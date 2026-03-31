// Amazon List Auto-Cart — Content Script
// Parses Amazon wishlist/registry pages and adds items to cart.
// Amazon Fresh items are always queued first.

(function () {
  'use strict';

  // In-memory store keyed by ASIN so we can look up items during cart-add
  // without needing to serialize DOM references.
  const itemStore = new Map();

  // ─── Message Router ──────────────────────────────────────────────────────────

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    switch (msg.action) {
      case 'ping':
        sendResponse({ ready: true, isListPage: isListPage() });
        break;

      case 'parseList':
        parseAndStoreItems().then(items => {
          sendResponse({ items });
        });
        return true; // async

      case 'addToCart':
        addItemsToCart(msg.asins).then(results => {
          sendResponse({ results });
        });
        return true; // async

      case 'scrollAll':
        scrollToLoadAll().then(() => {
          sendResponse({ done: true });
        });
        return true;
    }
    return true;
  });

  // ─── Page Detection ──────────────────────────────────────────────────────────

  function isListPage() {
    return /amazon\.com\/(hz\/wishlist|registry|gp\/registry)/.test(location.href);
  }

  // ─── Scroll to load lazy items ───────────────────────────────────────────────

  async function scrollToLoadAll() {
    let lastHeight = 0;
    for (let i = 0; i < 30; i++) {
      window.scrollTo(0, document.body.scrollHeight);
      await sleep(600);
      if (document.body.scrollHeight === lastHeight) break;
      lastHeight = document.body.scrollHeight;
    }
    window.scrollTo(0, 0);
    await sleep(400);
  }

  // ─── Parsing ─────────────────────────────────────────────────────────────────

  async function parseAndStoreItems() {
    itemStore.clear();

    // Amazon lazy-loads items — scroll to the bottom first to load all of them
    await scrollToLoadAll();

    const containers = gatherContainers();
    const items = [];

    for (const el of containers) {
      const item = extractItemData(el);
      if (!item || !item.asin) continue;
      itemStore.set(item.asin, { ...item, el });
      items.push(serializeItem(item));
    }

    // Fresh items first, then by delta descending
    items.sort((a, b) => {
      if (a.isFresh !== b.isFresh) return a.isFresh ? -1 : 1;
      return b.delta - a.delta;
    });

    return items;
  }

  function gatherContainers() {
    // Amazon uses different containers across wishlist / registry / shopping list pages
    const selectors = [
      'li[data-id]',
      'li[data-itemid]',
      'div[data-itemid]',
      '[data-item-prime-info]',
      '.g-item-sortable',
    ];
    for (const sel of selectors) {
      const nodes = Array.from(document.querySelectorAll(sel));
      if (nodes.length > 0) return nodes;
    }
    return [];
  }

  function extractItemData(el) {
    // ── ASIN ──────────────────────────────────────────────────────────────────
    const asin =
      el.dataset.asin ||
      el.querySelector('[data-asin]')?.dataset?.asin ||
      extractAsinFromUrl(el.querySelector('a[href*="/dp/"]')?.href || '');

    if (!asin) return null;

    // ── Item ID ───────────────────────────────────────────────────────────────
    const itemId = el.dataset.itemid || el.dataset.id || asin;

    // ── Name ──────────────────────────────────────────────────────────────────
    const nameEl =
      el.querySelector(`a[id^="itemName_"]`) ||
      el.querySelector(`span[id^="item-name-"]`) ||
      el.querySelector('.a-link-normal[title]') ||
      el.querySelector(`a[href*="/dp/${asin}"]`);
    const name = nameEl?.textContent?.trim() || nameEl?.title || 'Unknown item';

    // ── Quantities ────────────────────────────────────────────────────────────
    const neededEl =
      el.querySelector(`[id^="itemRequested_"]`) ||
      el.querySelector('[data-needed-quantity]') ||
      el.querySelector('.wl-item-option-quantity');

    const hasEl =
      el.querySelector(`[id^="itemPurchased_"]`) ||
      el.querySelector('[data-purchased-quantity]') ||
      el.querySelector('[id^="itemReceived_"]');

    const needed = parseQty(neededEl);
    const has    = parseQty(hasEl);
    const delta  = Math.max(0, needed - has);

    // ── Amazon Fresh? ─────────────────────────────────────────────────────────
    const isFresh = detectFresh(el);

    // ── Offer ID (used as fallback cart method) ────────────────────────────────
    const offerListingId =
      el.querySelector('[name="offerListingId"]')?.value ||
      el.querySelector('[data-offer-listing-id]')?.dataset?.offerListingId ||
      '';

    return { asin, itemId, name, needed, has, delta, isFresh, offerListingId };
  }

  function parseQty(el) {
    if (!el) return 0;
    const raw = el.textContent?.trim() || el.dataset?.neededQuantity || el.dataset?.purchasedQuantity || '0';
    return Math.max(0, parseInt(raw.replace(/\D/g, ''), 10) || 0);
  }

  function detectFresh(el) {
    const html = el.innerHTML;
    const text = el.textContent;
    return (
      /a-icon-fresh/i.test(html) ||
      /Amazon Fresh/i.test(text) ||
      /AmazonFresh/i.test(html) ||
      el.querySelector('[class*="fresh" i]') !== null ||
      el.querySelector('img[alt*="Fresh" i]') !== null ||
      el.querySelector('img[src*="fresh" i]') !== null
    );
  }

  function extractAsinFromUrl(url) {
    const m = url.match(/\/dp\/([A-Z0-9]{10})/i);
    return m ? m[1] : '';
  }

  function serializeItem(item) {
    // Strip DOM element before sending to popup
    const { el: _el, ...rest } = item;
    return rest;
  }

  // ─── Add to Cart ─────────────────────────────────────────────────────────────

  async function addItemsToCart(asins) {
    const results = [];

    for (const asin of asins) {
      const item = itemStore.get(asin);
      if (!item) {
        results.push({ asin, name: asin, success: false, error: 'Item not found in page' });
        continue;
      }
      if (item.delta <= 0) {
        results.push({ asin, name: item.name, success: false, error: 'No quantity needed' });
        continue;
      }

      const result = await addSingleItem(item);
      results.push({ asin, name: item.name, isFresh: item.isFresh, delta: item.delta, ...result });

      // Notify popup of per-item progress
      chrome.runtime.sendMessage({
        action: 'itemProgress',
        data: { asin, name: item.name, isFresh: item.isFresh, delta: item.delta, ...result },
      }).catch(() => {});

      await sleep(900); // avoid hammering Amazon
    }

    return results;
  }

  async function addSingleItem(item) {
    // ── Strategy 1: Dedicated cart-add URL (GET with session cookies) ──────────
    try {
      const cartUrl =
        `https://www.amazon.com/gp/aws/cart/add.html` +
        `?ASIN.1=${encodeURIComponent(item.asin)}` +
        `&Quantity.1=${item.delta}` +
        `&add=add`;

      const res = await fetch(cartUrl, {
        method: 'GET',
        credentials: 'include',
        redirect: 'follow',
      });

      // Amazon redirects to cart page on success
      if (res.ok || res.redirected) {
        return { success: true };
      }
    } catch (e) {
      console.warn('[AmazonCart] Cart URL strategy failed:', e.message);
    }

    // ── Strategy 2: Click the inline "Add to Cart" button on the list page ─────
    try {
      const el = item.el;
      if (el) {
        // Set quantity if there's an input
        const qtyInput = el.querySelector(
          'input[name^="itemRequestedQuantity"], select[name^="itemRequestedQuantity"], input[name="quantity"]'
        );
        if (qtyInput) {
          qtyInput.value = item.delta;
          qtyInput.dispatchEvent(new Event('change', { bubbles: true }));
          await sleep(300);
        }

        const btn = el.querySelector(
          'input[name="submit.addToCart"], input[value*="Add to Cart"], .a-button-input, [data-action="add-to-wishlist"]'
        );
        if (btn) {
          btn.click();
          await sleep(600);
          return { success: true };
        }
      }
    } catch (e) {
      console.warn('[AmazonCart] DOM click strategy failed:', e.message);
    }

    return { success: false, error: 'All add-to-cart strategies failed' };
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────────

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }
})();

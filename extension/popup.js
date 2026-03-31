// Amazon List Auto-Cart — Popup Controller

(function () {
  'use strict';

  // ─── State ────────────────────────────────────────────────────────────────────
  let currentTab = null;
  let parsedItems = [];    // full item list from content script
  let selectedAsins = new Set(); // ASINs the user wants to add

  // ─── DOM refs ─────────────────────────────────────────────────────────────────
  const states = {
    wrongPage: document.getElementById('state-wrong-page'),
    idle:      document.getElementById('state-idle'),
    scanning:  document.getElementById('state-scanning'),
    results:   document.getElementById('state-results'),
    adding:    document.getElementById('state-adding'),
    done:      document.getElementById('state-done'),
  };

  const el = {
    btnScan:      document.getElementById('btn-scan'),
    btnRescan:    document.getElementById('btn-rescan'),
    btnAddAll:    document.getElementById('btn-add-all'),
    btnRestart:   document.getElementById('btn-restart'),
    btnViewCart:  document.getElementById('btn-view-cart'),
    summaryText:  document.getElementById('summary-text'),
    itemList:     document.getElementById('item-list'),
    addingLabel:  document.getElementById('adding-label'),
    progressList: document.getElementById('progress-list'),
    finalList:    document.getElementById('final-list'),
    doneSummary:  document.getElementById('done-summary'),
    freshNote:    document.getElementById('fresh-note'),
  };

  // ─── Init ─────────────────────────────────────────────────────────────────────

  async function init() {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tabs[0];

    if (!currentTab) {
      showState('wrongPage');
      return;
    }

    // Ping content script to see if we're on a list page
    try {
      const response = await sendToContent({ action: 'ping' });
      if (response?.isListPage) {
        showState('idle');
      } else {
        showState('wrongPage');
      }
    } catch {
      showState('wrongPage');
    }
  }

  // ─── Event Handlers ───────────────────────────────────────────────────────────

  el.btnScan.addEventListener('click', () => scanList());
  el.btnRescan.addEventListener('click', () => scanList());
  el.btnAddAll.addEventListener('click', () => startAddToCart());
  el.btnRestart.addEventListener('click', () => {
    parsedItems = [];
    selectedAsins.clear();
    showState('idle');
  });

  // Listen for per-item progress from content script
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'itemProgress') {
      renderProgressRow(msg.data, el.progressList);
    }
  });

  // ─── Scan ─────────────────────────────────────────────────────────────────────

  async function scanList() {
    showState('scanning');
    try {
      const response = await sendToContent({ action: 'parseList' });
      parsedItems = response?.items || [];
      renderResults(parsedItems);
      showState('results');
    } catch (e) {
      alert('Could not parse the list. Make sure you are on an Amazon wishlist or registry page and try again.\n\n' + e.message);
      showState('idle');
    }
  }

  // ─── Render Results ───────────────────────────────────────────────────────────

  function renderResults(items) {
    selectedAsins.clear();
    el.itemList.innerHTML = '';

    const needsAdding = items.filter(i => i.delta > 0);
    const alreadyHas  = items.filter(i => i.delta <= 0);
    const hasFresh    = items.some(i => i.isFresh && i.delta > 0);

    // Pre-select all items that need adding
    needsAdding.forEach(i => selectedAsins.add(i.asin));

    el.summaryText.innerHTML =
      `<strong>${needsAdding.length}</strong> item${needsAdding.length !== 1 ? 's' : ''} to add` +
      (alreadyHas.length ? ` &middot; ${alreadyHas.length} already fulfilled` : '');

    el.freshNote.hidden = !hasFresh;

    const allItems = [...items]; // already sorted Fresh-first by content script

    for (const item of allItems) {
      const row = buildItemRow(item);
      el.itemList.appendChild(row);
    }

    updateAddButton();
  }

  function buildItemRow(item) {
    const row = document.createElement('div');
    row.className = 'item-row' + (item.delta <= 0 ? ' skip' : '');
    row.dataset.asin = item.asin;

    const checked = item.delta > 0 && selectedAsins.has(item.asin);

    row.innerHTML = `
      <div class="item-check">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="#131921" stroke-width="2.5">
          <polyline points="1.5,5 4,7.5 8.5,2"/>
        </svg>
      </div>
      <div class="item-info">
        <div class="item-name" title="${escHtml(item.name)}">${escHtml(item.name)}</div>
        <div class="item-meta">
          ${item.isFresh ? '<span class="tag fresh">Fresh</span>' : ''}
          <span>Needed: ${item.needed}</span>
          <span>Has: ${item.has}</span>
          ${item.delta <= 0 ? '<span class="tag zero">Fulfilled</span>' : ''}
        </div>
      </div>
      ${item.delta > 0 ? `<div class="item-qty">+${item.delta}</div>` : ''}
    `;

    if (!checked) row.classList.add('skip');

    // Toggle selection on click
    if (item.delta > 0) {
      row.addEventListener('click', () => toggleItem(item.asin, row));
    }

    return row;
  }

  function toggleItem(asin, row) {
    if (selectedAsins.has(asin)) {
      selectedAsins.delete(asin);
      row.classList.add('skip');
    } else {
      selectedAsins.add(asin);
      row.classList.remove('skip');
    }
    updateAddButton();
  }

  function updateAddButton() {
    const count = selectedAsins.size;
    el.btnAddAll.textContent = count > 0
      ? `Add ${count} Item${count !== 1 ? 's' : ''} to Cart`
      : 'No Items Selected';
    el.btnAddAll.disabled = count === 0;
  }

  // ─── Add to Cart ──────────────────────────────────────────────────────────────

  async function startAddToCart() {
    if (selectedAsins.size === 0) return;

    // Build ordered list: Fresh-first, matching selectedAsins
    const ordered = parsedItems
      .filter(i => selectedAsins.has(i.asin))
      .sort((a, b) => {
        if (a.isFresh !== b.isFresh) return a.isFresh ? -1 : 1;
        return 0;
      });

    // Render pending rows
    el.progressList.innerHTML = '';
    for (const item of ordered) {
      renderProgressRow({ ...item, pending: true }, el.progressList);
    }

    showState('adding');

    const results = await sendToContent({
      action: 'addToCart',
      asins: ordered.map(i => i.asin),
    });

    renderDone(results?.results || []);
  }

  function renderProgressRow(data, container) {
    // Update existing row if present, otherwise append
    let row = container.querySelector(`[data-asin="${data.asin}"]`);
    if (!row) {
      row = document.createElement('div');
      row.dataset.asin = data.asin;
      container.appendChild(row);
    }

    const isPending = data.pending;
    const isOk      = !isPending && data.success;
    const isFail    = !isPending && !data.success;

    row.className = 'progress-row ' + (isPending ? 'pending' : isOk ? 'ok' : 'fail');
    row.innerHTML = `
      <span class="progress-icon">${isPending ? '⏳' : isOk ? '✅' : '❌'}</span>
      <span class="progress-name" title="${escHtml(data.name)}">${escHtml(data.name)}</span>
      ${data.isFresh ? '<span class="tag fresh">Fresh</span>' : ''}
      ${data.delta ? `<span class="progress-qty">+${data.delta}</span>` : ''}
    `;
  }

  function renderDone(results) {
    const ok   = results.filter(r => r.success);
    const fail = results.filter(r => !r.success);

    el.doneSummary.className = 'notice ' + (fail.length === 0 ? 'ok' : ok.length > 0 ? 'warn' : 'error');
    el.doneSummary.innerHTML =
      fail.length === 0
        ? `<strong>All ${ok.length} item${ok.length !== 1 ? 's' : ''} added to cart!</strong>`
        : ok.length > 0
          ? `<strong>${ok.length} added, ${fail.length} failed.</strong><p>Failed items may be out of stock or unavailable.</p>`
          : `<strong>Could not add items to cart.</strong><p>You may need to add them manually.</p>`;

    el.finalList.innerHTML = '';
    for (const r of results) {
      renderProgressRow(r, el.finalList);
    }

    showState('done');
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────────

  function showState(name) {
    for (const [key, el] of Object.entries(states)) {
      el.hidden = key !== name;
    }
  }

  async function sendToContent(message) {
    return new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(currentTab.id, message, response => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ─── Boot ─────────────────────────────────────────────────────────────────────
  init();
})();

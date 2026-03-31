// Amazon List Auto-Cart — Service Worker (Background)
// Minimal: relays per-item progress from content script to the popup.

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'itemProgress') {
    // Forward progress updates to any open popup
    chrome.runtime.sendMessage(msg).catch(() => {});
  }
  sendResponse({});
  return true;
});

# Amazon List Auto-Cart — Extension

The browser extension source. Works on any Chromium-based browser (Chrome, Opera, Edge) via Manifest V3.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | Extension manifest (MV3), declares permissions and entry points |
| `content.js` | Injected into Amazon list pages — parses items, adds to cart |
| `background.js` | Service worker — relays per-item progress to the popup |
| `popup.html/css/js` | The popup UI shown when you click the toolbar icon |
| `icons/` | PNG icons (16, 48, 128 px) + `make-icons.html` generator |

## Load Manually in Chrome / Opera / Edge

1. Open extensions page:
   - Chrome → `chrome://extensions/`
   - Opera → `opera://extensions/`
   - Edge → `edge://extensions/`
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked**
4. Select **this folder** (the one containing `manifest.json`)

## Generate Icons

The PNG icons are not checked into git. Generate them with either method:

**Option A — HTML generator (no installs)**
Open `icons/make-icons.html` in your browser, click each **Download** button, save the files as `icons/icon16.png`, `icons/icon48.png`, `icons/icon128.png`.

**Option B — Python script**
```bash
# From the repo root:
pip install Pillow
python installer/generate_icons.py
```

## Permissions Used

| Permission | Why |
|---|---|
| `activeTab` | Read the current Amazon list page |
| `scripting` | Inject the content script on demand |
| `storage` | Reserved for future settings |
| `tabs` | Open the active tab from the popup |
| `*://*.amazon.com/*` | Access Amazon pages to parse lists and add to cart |

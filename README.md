# Amazon List Auto-Cart

A browser extension that parses your Amazon wishlist or registry, calculates how many of each item you still need (Needed − Has), and automatically adds them to your cart. **Amazon Fresh items are always queued first.**

Supports **Chrome**, **Opera**, **Edge**, and **Safari (macOS)**.

---

## Quick Install (Recommended)

Download the installer for your OS from the [**Releases page**](https://github.com/DranzerZERogue56/amazon-list-cart/releases/latest):

| OS | File |
|---|---|
| Windows | `AmazonListAutoCart-Installer.exe` |
| macOS | `AmazonListAutoCart-Installer-mac.zip` |

### Windows

1. Download `AmazonListAutoCart-Installer.exe`
2. Double-click to run it *(if Windows SmartScreen appears, click "More info" → "Run anyway")*
3. Check the browsers you want to install for
4. Click **Install Extension**
5. The installer opens your browser's Extensions page and copies the extension path to your clipboard
6. In the browser, toggle **Developer mode** (top-right)
7. Click **Load unpacked** → paste the path → click **Select Folder**
8. Done — the cart icon appears in your toolbar

### macOS

1. Download `AmazonListAutoCart-Installer-mac.zip`
2. Unzip it, then double-click `AmazonListAutoCart-Installer.app`
   *(if Gatekeeper blocks it: right-click → Open → Open)*
3. Follow the same steps 3–8 as Windows above
4. For **Safari**, see the [Safari section](#safari-macos) below

---

## Manual Install (No Installer)

1. Download `extension.zip` from the [Releases page](https://github.com/DranzerZERogue56/amazon-list-cart/releases/latest) and unzip it
   *— or —*
   Clone the repo and use the `extension/` folder directly
2. Open your browser's extensions page:
   - Chrome → `chrome://extensions/`
   - Opera → `opera://extensions/`
   - Edge → `edge://extensions/`
3. Enable **Developer mode** (toggle, top-right)
4. Click **Load unpacked**
5. Select the unzipped `extension/` folder
6. The extension is now installed

> **Icon note:** The extension needs PNG icons at `extension/icons/icon16.png`, `icon48.png`, `icon128.png`.
> Open `extension/icons/make-icons.html` in your browser, click each **Download** button, and save the files there.
> (Icons are auto-generated during CI releases — if you downloaded `extension.zip` from Releases, they're already included.)

---

## Safari (macOS)

Safari requires converting the Chromium extension into a native macOS app via Xcode.

**Requirements:** macOS, [Xcode](https://apps.apple.com/app/xcode/id497799835) (free from the App Store)

```bash
# From the repo root:
bash convert-to-safari.sh
```

Then:
1. Open the generated `.xcodeproj` in Xcode
2. Set your Apple Developer Team under **Signing & Capabilities**
3. Press **Run** (⌘R) — this builds and installs the host app
4. In Safari → **Settings** → **Extensions** → enable **Amazon List Auto-Cart**

---

## How to Use

1. Log in to Amazon in your browser
2. Navigate to any wishlist or registry
   *(URL looks like `amazon.com/hz/wishlist/ls/...` or `amazon.com/registry/...`)*
3. Click the **cart icon** in your browser toolbar
4. Click **Scan List** — the extension scrolls through all items and parses quantities
5. Review the item list:
   - Items tagged **Fresh** (green) will be added first
   - Each item shows **+N** (the quantity being added to cart)
   - Click any item to toggle it off
6. Click **Add N Items to Cart**
7. Watch the per-item progress log — each item is added with a short delay
8. Click **View Cart** when done

---

## Building from Source

**Requirements:** Python 3.9+, [PyInstaller](https://pyinstaller.org/)

```bash
# Clone
git clone https://github.com/DranzerZERogue56/amazon-list-cart.git
cd amazon-list-cart

# Generate icons
pip install Pillow
python installer/generate_icons.py

# Run installer directly (no .exe needed)
python installer/installer.py

# Build .exe (Windows) or .app (macOS)
pip install pyinstaller
pyinstaller --onefile --windowed --name "AmazonListAutoCart-Installer" installer/installer.py
# Output: dist/AmazonListAutoCart-Installer.exe  (or .app on macOS)
```

Releases are built automatically by [GitHub Actions](.github/workflows/build.yml) whenever a version tag (`v*`) is pushed.

---

## Project Structure

```
amazon-list-cart/
├── extension/              # The browser extension
│   ├── manifest.json       # Manifest V3
│   ├── content.js          # List parsing + cart logic
│   ├── background.js       # Progress event relay
│   ├── popup.html/css/js   # Extension popup UI
│   └── icons/              # PNG icons (generated) + make-icons.html
├── installer/
│   ├── installer.py        # GUI installer (tkinter, stdlib only)
│   └── generate_icons.py   # Pillow-based icon generator (used in CI)
├── .github/workflows/
│   └── build.yml           # Builds .exe, .app, extension.zip on release tags
└── convert-to-safari.sh    # Safari/Xcode conversion helper
```

---

## Browser Compatibility

| Browser | Platform | Support |
|---|---|---|
| Google Chrome | Windows, macOS, Linux | Full |
| Opera / Opera GX | Windows, macOS | Full |
| Microsoft Edge | Windows, macOS | Full |
| Safari | macOS only | Via Xcode conversion |

---

## Troubleshooting

**"Extension could not be loaded"** — Make sure you selected the `extension/` folder itself (containing `manifest.json`), not a parent folder.

**Items not detected** — Amazon occasionally updates their page layout. Try clicking **Re-scan** after the page fully loads. If the list is long, make sure you're viewing "All" items (not a filtered view).

**Cart add fails for some items** — The item may be out of stock, a Fresh item unavailable in your area, or sold by a third-party seller that requires selecting options first. These are flagged in the progress log — add them manually.

**Safari: "No developer account"** — A free Apple ID works for local installs (the app runs on your machine). Sign in with your Apple ID in Xcode under **Settings → Accounts**.

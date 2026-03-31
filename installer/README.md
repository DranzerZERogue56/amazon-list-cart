# Amazon List Auto-Cart — Installer

A single-file Python GUI installer that downloads the latest extension release from GitHub and walks you through enabling it in your browser(s).

## Run Without Building

```bash
# Requires Python 3.9+  (no third-party packages needed)
python installer.py
```

## Build a Standalone Executable

### Windows → `.exe`

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AmazonListAutoCart-Installer" installer.py
# Output: dist/AmazonListAutoCart-Installer.exe
```

### macOS → `.app`

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AmazonListAutoCart-Installer" installer.py
# Output: dist/AmazonListAutoCart-Installer.app
# Zip it for distribution:
cd dist && zip -r AmazonListAutoCart-Installer-mac.zip AmazonListAutoCart-Installer.app
```

> **Note:** Both commands should be run from the **repo root**, not from inside `installer/`.

## What the Installer Does

1. **Detects** your OS (Windows / macOS) and which browsers are installed
2. **Downloads** `extension.zip` from the latest GitHub release
   *(falls back to the `main` branch archive if no release exists yet)*
3. **Extracts** the extension to a local folder:
   - Windows: `%LOCALAPPDATA%\AmazonListAutoCart\extension\`
   - macOS: `~/Library/Application Support/AmazonListAutoCart/extension\`
4. **Copies** that path to your clipboard automatically
5. **Opens** the browser's Extensions page
6. **Shows** step-by-step instructions to click Load Unpacked and paste the path

## Generating Icons (CI Use)

`generate_icons.py` creates the three required PNG icons using Pillow.
It is run automatically by GitHub Actions before packaging the extension.

```bash
pip install Pillow
python installer/generate_icons.py
# Writes: extension/icons/icon16.png, icon48.png, icon128.png
```

## Updating the GitHub Repo Target

The installer downloads from `DranzerZERogue56/amazon-list-cart` by default.
If you fork the repo, update the `GITHUB_REPO` constant at the top of `installer.py`:

```python
GITHUB_REPO = "your-username/amazon-list-cart"
```

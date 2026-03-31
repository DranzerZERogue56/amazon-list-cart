#!/usr/bin/env bash
# Converts this Chrome/Opera MV3 extension to a Safari Web Extension (macOS only).
# Requirements: macOS, Xcode (with Command Line Tools), xcrun
#
# Usage (run from the extension root folder):
#   bash convert-to-safari.sh

set -euo pipefail

EXTENSION_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${EXTENSION_DIR}/../amazon-list-cart-safari"

echo "==> Checking for Xcode / xcrun..."
if ! command -v xcrun &>/dev/null; then
  echo "ERROR: xcrun not found. Install Xcode from the App Store and run:"
  echo "  xcode-select --install"
  exit 1
fi

echo "==> Converting extension..."
xcrun safari-web-extension-converter \
  --project-location "${OUTPUT_DIR}" \
  --app-name "AmazonListAutoCart" \
  --bundle-identifier "com.yourname.amazon-list-auto-cart" \
  --swift \
  "${EXTENSION_DIR}"

echo ""
echo "==> Done! Open the Xcode project at:"
echo "    ${OUTPUT_DIR}/AmazonListAutoCart/AmazonListAutoCart.xcodeproj"
echo ""
echo "Next steps:"
echo "  1. Open the .xcodeproj in Xcode"
echo "  2. Set your Team in Signing & Capabilities"
echo "  3. Build & Run — the app installs the Safari extension"
echo "  4. Enable it in Safari > Settings > Extensions"

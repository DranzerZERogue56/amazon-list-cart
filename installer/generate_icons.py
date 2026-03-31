"""
Generates icon16.png, icon48.png, icon128.png for the extension.
Requires Pillow:  pip install Pillow
Run from the repo root:  python installer/generate_icons.py
"""

import os
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Pillow is required: pip install Pillow")

ICONS_DIR = Path(__file__).parent.parent / "extension" / "icons"
SIZES     = [16, 48, 128]

# Colours
BG_DARK  = (19, 25, 33, 255)   # #131921
ORANGE   = (255, 153, 0, 255)  # #FF9900
GREEN    = (0, 166, 80, 255)   # #00A650
WHITE    = (255, 255, 255, 255)


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2 * radius, y0 + 2 * radius], fill=fill)
    draw.ellipse([x1 - 2 * radius, y0, x1, y0 + 2 * radius], fill=fill)
    draw.ellipse([x0, y1 - 2 * radius, x0 + 2 * radius, y1], fill=fill)
    draw.ellipse([x1 - 2 * radius, y1 - 2 * radius, x1, y1], fill=fill)


def make_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s    = size
    rad  = max(2, int(s * 0.15))

    # Background rounded square
    draw_rounded_rect(draw, (0, 0, s - 1, s - 1), rad, BG_DARK)

    lw = max(1, int(s * 0.065))

    # Cart handle  (small line top-left)
    hx0 = int(s * 0.08)
    hy0 = int(s * 0.15)
    hx1 = int(s * 0.24)
    draw.line([(hx0, hy0), (hx1, hy0)], fill=ORANGE, width=lw)

    # Cart body diagonal from handle to basket
    bx0 = hx1
    by0 = hy0
    bx1 = int(s * 0.30)
    by1 = int(s * 0.42)
    draw.line([(bx0, by0), (bx1, by1)], fill=ORANGE, width=lw)

    # Cart basket (trapezoid top line)
    basket_l = bx1
    basket_r = int(s * 0.84)
    basket_t = by1
    basket_b = int(s * 0.66)
    draw.line([(basket_l, basket_t), (basket_r, basket_t)], fill=ORANGE, width=lw)

    # Basket bottom (shorter)
    bottom_l = int(s * 0.34)
    bottom_r = int(s * 0.80)
    draw.line([(basket_l, basket_b), (bottom_l, basket_b)], fill=ORANGE, width=lw)
    draw.line([(basket_r, basket_b), (bottom_r, basket_b)], fill=ORANGE, width=lw)

    # Left & right sides of basket
    draw.line([(basket_l, basket_t), (bottom_l, basket_b)], fill=ORANGE, width=lw)
    draw.line([(basket_r, basket_t), (bottom_r, basket_b)], fill=ORANGE, width=lw)

    # Wheels
    wr = max(2, int(s * 0.065))
    cx1 = int(s * 0.36)
    cx2 = int(s * 0.76)
    cy  = basket_b + wr + lw
    draw.ellipse([cx1 - wr, cy - wr, cx1 + wr, cy + wr], fill=ORANGE)
    draw.ellipse([cx2 - wr, cy - wr, cx2 + wr, cy + wr], fill=ORANGE)

    # Green badge (bottom-right circle with checkmark)
    br   = max(3, int(s * 0.22))
    bcx  = s - br - 1
    bcy  = s - br - 1
    draw.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=GREEN)

    # Checkmark inside badge
    clw = max(1, int(br * 0.25))
    p1  = (bcx - int(br * 0.45), bcy)
    p2  = (bcx - int(br * 0.05), bcy + int(br * 0.45))
    p3  = (bcx + int(br * 0.50), bcy - int(br * 0.35))
    draw.line([p1, p2], fill=WHITE, width=clw)
    draw.line([p2, p3], fill=WHITE, width=clw)

    return img


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = ICONS_DIR / f"icon{size}.png"
        icon = make_icon(size)
        icon.save(path, "PNG")
        print(f"  Wrote {path}")
    print("Icons generated.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the Cluefolio brand mark.

A magnifier: the ring is the lens, the diagonal is the handle, the dot is the
clue being found. It reads at 48 px in a feed and at 512 px on a closing card.

Writes two transparent PNGs:
    brand/logo-mark-light.png   paper-coloured, for dark backgrounds
    brand/logo-mark-dark.png    ink-coloured, for paper backgrounds

Usage:
    python scripts/make_logo.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"

PAPER = (244, 239, 230)
INK = (21, 19, 15)
ACCENT = (140, 47, 30)

SIZE = 1024
SCALE = 4  # supersample, then downscale for clean edges


def draw_mark(colour: tuple[int, int, int]) -> Image.Image:
    s = SIZE * SCALE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Lens: a ring occupying the upper-left of the canvas.
    cx, cy = s * 0.42, s * 0.42
    r = s * 0.27
    width = int(s * 0.075)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*colour, 255), width=width)

    # Handle: a thick diagonal out of the lower-right of the ring.
    hx0, hy0 = cx + r * 0.72, cy + r * 0.72
    hx1, hy1 = s * 0.88, s * 0.88
    d.line([(hx0, hy0), (hx1, hy1)], fill=(*colour, 255), width=width)
    d.ellipse(
        [hx1 - width / 2, hy1 - width / 2, hx1 + width / 2, hy1 + width / 2],
        fill=(*colour, 255),
    )

    # The clue: a filled dot inside the lens, offset to imply search.
    dr = s * 0.085
    d.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=(*ACCENT, 255))

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> int:
    BRAND.mkdir(exist_ok=True)
    for name, colour in (("logo-mark-light.png", PAPER), ("logo-mark-dark.png", INK)):
        out = BRAND / name
        draw_mark(colour).save(out, "PNG")
        print(f"  OK  {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
    favicon = BRAND / "logo-mark.png"
    draw_mark(INK).save(favicon, "PNG")
    print(f"  OK  {favicon.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render Cluefolio carousel images from archival sources.

Usage:
    python scripts/render_post.py --slug first-post
    python scripts/render_post.py --slug first-post --only 01

Reads   content/<slug>/render-config.json
        content/<slug>/assets/manifest.json
Writes  content/<slug>/images/01-cover.jpg + interior jpgs

Design:
- 1080x1350 sRGB JPEG q92, progressive.
- Warm duotone grade that preserves archival character (never colorizes).
- Subtle film grain to unify scans of different quality.
- Cover lockup: wordmark rail, headline, accent rule, dateline.
- Interior: full bleed, top category tag, bottom credit strip.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent

W, H = 1080, 1350
JPEG_QUALITY = 92

FONT_DIR = Path("C:/Windows/Fonts")
GEORGIA = FONT_DIR / "georgia.ttf"
GEORGIA_BOLD = FONT_DIR / "georgiab.ttf"
GEORGIA_ITALIC = FONT_DIR / "georgiai.ttf"
SEGOE = FONT_DIR / "segoeui.ttf"
SEGOE_SEMI = FONT_DIR / "segoeuib.ttf"


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def crop_to_ratio(img: Image.Image, target_w: int, target_h: int, fx: float, fy: float, zoom: float) -> Image.Image:
    """Center-ish crop to the target aspect, then resize. fx/fy are 0..1 focal points."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_h = int(src_h / zoom)
        new_w = int(new_h * target_ratio)
    else:
        new_w = int(src_w / zoom)
        new_h = int(new_w / target_ratio)

    new_w = min(new_w, src_w)
    new_h = min(new_h, src_h)

    cx = fx * src_w
    cy = fy * src_h
    left = int(round(cx - new_w / 2))
    top = int(round(cy - new_h / 2))

    left = max(0, min(left, src_w - new_w))
    top = max(0, min(top, src_h - new_h))

    box = (left, top, left + new_w, top + new_h)
    cropped = img.crop(box)
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def apply_contrast(img: Image.Image, factor: float = 1.0) -> Image.Image:
    if abs(factor - 1.0) < 1e-6:
        return img
    from PIL import ImageEnhance

    return ImageEnhance.Contrast(img).enhance(factor)


def warm_duotone(img: Image.Image, strength: float = 0.55) -> Image.Image:
    """Map luminance onto a warm paper/ink ramp. Preserves detail; does not colorize."""
    gray = ImageOps.grayscale(img)
    arr = np.asarray(gray, dtype=np.float32) / 255.0

    # Gentle S-curve: lift mids slightly, protect highlights.
    arr = np.clip(arr, 0, 1)
    arr = arr ** 0.96

    shadow = np.array([26, 22, 17], dtype=np.float32) / 255.0
    highlight = np.array([246, 239, 226], dtype=np.float32) / 255.0

    ramp = shadow[None, None, :] + arr[:, :, None] * (highlight - shadow)[None, None, :]

    orig = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    out = orig * (1 - strength) + ramp * strength
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8), "RGB")


def add_grain(img: Image.Image, amount: float, seed: int = 7) -> Image.Image:
    if amount <= 0:
        return img
    rng = np.random.default_rng(seed)
    arr = np.asarray(img, dtype=np.float32)
    noise = rng.normal(0, 255 * amount, arr.shape[:2])[:, :, None]
    arr = np.clip(arr + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def vignette(img: Image.Image, strength: float = 0.30) -> Image.Image:
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    d = np.sqrt(((x - cx) / (w * 0.62)) ** 2 + ((y - cy) / (h * 0.62)) ** 2)
    mask = np.clip(1.0 - strength * np.clip(d - 0.55, 0, None) ** 1.5, 0, 1)
    arr = np.asarray(img, dtype=np.float32) * mask[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def gradient_scrim(img: Image.Image, start_frac: float = 0.42, max_alpha: int = 232) -> Image.Image:
    """Bottom gradient in ink for headline legibility."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    start = int(h * start_frac)
    for y in range(start, h):
        t = (y - start) / max(1, (h - start))
        alpha = int(max_alpha * (t ** 1.45))
        draw.line([(0, y), (w, y)], fill=(11, 10, 8, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def tracked_width(draw: ImageDraw.ImageDraw, text, font, tracking=0):
    if not text:
        return 0
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def fit_headline(draw, lines, max_width, start_size, min_size, font_path):
    size = start_size
    while size > min_size:
        font = load_font(font_path, size)
        widths = [draw.textlength(line, font=font) for line in lines]
        if max(widths) <= max_width:
            return font, size
        size -= 2
    return load_font(font_path, min_size), min_size


def wrap_to_width(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_cover(cfg, manifest, out_path: Path) -> None:
    palette = cfg["palette"]
    cover = cfg["cover"]
    paper = hex_rgb(palette["paper"])
    ink = hex_rgb(palette["ink"])
    muted = hex_rgb(palette["muted"])
    accent = hex_rgb(palette["accent"])

    asset = next(a for a in manifest["assets"] if a["id"] == cover["asset"])
    src_path = ROOT / "content" / cfg["slug"] / "assets" / (asset["id"] + Path(asset["file_url"]).suffix)
    if not src_path.exists():
        # fall back to any matching stem
        candidates = list(src_path.parent.glob(asset["id"] + ".*"))
        if not candidates:
            raise FileNotFoundError(src_path)
        src_path = candidates[0]

    src = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    crop = cover.get("crop", {})
    base = crop_to_ratio(src, W, H, crop.get("fx", 0.5), crop.get("fy", 0.5), crop.get("zoom", 1.0))
    base = warm_duotone(base, 0.62)
    base = add_grain(base, 0.018, seed=11)
    base = vignette(base, 0.34)
    base = gradient_scrim(base, start_frac=0.44, max_alpha=238)

    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Top rail
    margin = 64
    f_mark = load_font(SEGOE_SEMI, 25)
    f_cat = load_font(SEGOE_SEMI, 21)
    draw_tracked(draw, (margin, 58), cover["wordmark"], f_mark, paper, tracking=3.2)
    cat = cover["category"]
    cw = tracked_width(draw, cat, f_cat, tracking=2.6)
    cat_x = W - margin - cw
    draw.rectangle([cat_x - 16, 50, W - margin + 16, 92], fill=(*ink, 150))
    draw_tracked(draw, (cat_x, 62), cat, f_cat, (238, 230, 216), tracking=2.6)
    draw.line([(margin, 104), (W - margin, 104)], fill=(*paper, 70), width=1)

    # Headline block
    bottom_pad = 118
    dateline_font = load_font(GEORGIA_ITALIC, 34)
    dateline = cover["dateline"]
    dl_h = dateline_font.size + 6

    rule_gap = 26
    rule_h = 4
    head_lines = cover["headline"]
    head_font, head_size = fit_headline(draw, head_lines, W - margin * 2, 92, 58, GEORGIA_BOLD)
    line_h = int(head_size * 1.16)
    head_block_h = line_h * len(head_lines)

    total = head_block_h + rule_gap + rule_h + 24 + dl_h
    y0 = H - bottom_pad - total

    y = y0
    for line in head_lines:
        draw.text((margin, y), line, font=head_font, fill=paper)
        y += line_h

    y += rule_gap
    draw.rectangle([margin, y, margin + 132, y + rule_h], fill=accent)
    y += rule_h + 24

    draw.text((margin, y), dateline, font=dateline_font, fill=(226, 216, 200))

    # Disclosure badge for editorial reconstructions. Also covers the
    # generator watermark on the bottom-right of free AI renders.
    disclosure = cover.get("disclosure")
    if disclosure:
        f_disc = load_font(SEGOE_SEMI, 16)
        dw = tracked_width(draw, disclosure, f_disc, tracking=1.6)
        pad_x, pad_y = 12, 7
        bx1 = W - margin
        by1 = H - 34
        bx0 = bx1 - dw - pad_x * 2
        by0 = by1 - f_disc.size - pad_y * 2
        draw.rectangle([bx0, by0, bx1, by1], fill=(*ink, 200))
        draw_tracked(
            draw,
            (bx0 + pad_x, by0 + pad_y - 1),
            disclosure,
            f_disc,
            (238, 230, 216),
            tracking=1.6,
        )

    canvas.convert("RGB").save(out_path, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True, subsampling=1)


def render_interior(cfg, manifest, item, out_path: Path) -> None:
    palette = cfg["palette"]
    paper = hex_rgb(palette["paper"])
    muted = hex_rgb(palette["muted"])
    ink = hex_rgb(palette["ink"])
    accent = hex_rgb(palette["accent"])

    asset = next(a for a in manifest["assets"] if a["id"] == item["asset"])
    src_path = ROOT / "content" / cfg["slug"] / "assets" / (asset["id"] + Path(asset["file_url"]).suffix)
    if not src_path.exists():
        candidates = list(src_path.parent.glob(asset["id"] + ".*"))
        if not candidates:
            raise FileNotFoundError(src_path)
        src_path = candidates[0]

    src = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    crop = item.get("crop", {})
    base = crop_to_ratio(src, W, H, crop.get("fx", 0.5), crop.get("fy", 0.5), crop.get("zoom", 1.0))
    base = apply_contrast(base, item.get("contrast", 1.0))
    base = warm_duotone(base, 0.58)
    base = add_grain(base, item.get("grain", 0.02), seed=hash(item["out"]) % 10000)
    base = vignette(base, 0.22)

    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = 52
    f_cat = load_font(SEGOE_SEMI, 19)
    tag = "CLUEFOLIO  Â·  " + cfg["cover"]["category"]
    tw = tracked_width(draw, tag, f_cat, tracking=2.2)
    pad_x, pad_y = 16, 11
    draw.rectangle(
        [margin, margin, margin + tw + pad_x * 2, margin + f_cat.size + pad_y * 2],
        fill=(*ink, 168),
    )
    draw_tracked(draw, (margin + pad_x, margin + pad_y - 1), tag, f_cat, (238, 230, 216), tracking=2.2)

    # Credit strip
    strip_h = 118
    strip_top = H - strip_h
    draw.rectangle([0, strip_top, W, H], fill=(*paper, 246))
    draw.line([(0, strip_top), (W, strip_top)], fill=(*accent, 255), width=3)

    f_line = load_font(GEORGIA_ITALIC, 27)
    f_credit = load_font(SEGOE, 19)
    line_text = item.get("line", "")
    credit = asset.get("credit", "")

    line_y = strip_top + 20
    for wrapped in wrap_to_width(draw, line_text, f_line, W - margin * 2)[:1]:
        draw.text((margin, line_y), wrapped, font=f_line, fill=ink)

    credit_y = strip_top + 58
    for wrapped in wrap_to_width(draw, credit, f_credit, W - margin * 2)[:1]:
        draw.text((margin, credit_y), wrapped, font=f_credit, fill=muted)

    canvas.convert("RGB").save(out_path, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True, subsampling=1)


def paper_texture(canvas: Image.Image, amount: float = 0.012, seed: int = 3) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.asarray(canvas, dtype=np.float32)
    noise = rng.normal(0, 255 * amount, arr.shape[:2])[:, :, None]
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8), "RGB")


def render_photo_slide(cfg, manifest, item, out_path: Path) -> None:
    """Full-bleed archival photograph with a short overlay line, cover styling."""
    palette = cfg["palette"]
    paper = hex_rgb(palette["paper"])
    ink = hex_rgb(palette["ink"])
    accent = hex_rgb(palette["accent"])

    asset = next(a for a in manifest["assets"] if a["id"] == item["asset"])
    src_path = ROOT / "content" / cfg["slug"] / "assets" / (asset["id"] + Path(asset["file_url"]).suffix)
    if not src_path.exists():
        candidates = list(src_path.parent.glob(asset["id"] + ".*"))
        if not candidates:
            raise FileNotFoundError(src_path)
        src_path = candidates[0]

    src = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    crop = item.get("crop", {})
    base = crop_to_ratio(src, W, H, crop.get("fx", 0.5), crop.get("fy", 0.5), crop.get("zoom", 1.0))
    base = apply_contrast(base, item.get("contrast", 1.0))
    base = warm_duotone(base, 0.58)
    base = add_grain(base, item.get("grain", 0.018), seed=hash(out_path.name) % 10000)
    base = vignette(base, 0.30)
    base = gradient_scrim(base, start_frac=0.46, max_alpha=240)

    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = 64
    f_mark = load_font(SEGOE_SEMI, 25)
    f_cat = load_font(SEGOE_SEMI, 21)
    draw_tracked(draw, (margin, 58), cfg["cover"]["wordmark"], f_mark, paper, tracking=3.2)
    cat = cfg["cover"]["category"]
    cw = tracked_width(draw, cat, f_cat, tracking=2.6)
    cat_x = W - margin - cw
    draw.rectangle([cat_x - 16, 50, W - margin + 16, 92], fill=(*ink, 150))
    draw_tracked(draw, (cat_x, 62), cat, f_cat, (238, 230, 216), tracking=2.6)
    draw.line([(margin, 104), (W - margin, 104)], fill=(*paper, 70), width=1)

    headline = item["headline"]
    if isinstance(headline, str):
        headline = [headline]
    kicker = item.get("kicker", "")
    f_kick = load_font(GEORGIA_ITALIC, 32)

    bottom_pad = 118
    rule_gap = 22
    rule_h = 4
    head_font, head_size = fit_headline(draw, headline, W - margin * 2, 96, 52, GEORGIA_BOLD)
    line_h = int(head_size * 1.14)
    head_block_h = line_h * len(headline)
    kick_h = (f_kick.size + 8) if kicker else 0

    total = head_block_h + rule_gap + rule_h + (22 + kick_h if kicker else 0)
    y = H - bottom_pad - total

    for line in headline:
        draw.text((margin, y), line, font=head_font, fill=paper)
        y += line_h

    y += rule_gap
    draw.rectangle([margin, y, margin + 132, y + rule_h], fill=accent)
    y += rule_h + 22
    if kicker:
        draw.text((margin, y), kicker, font=f_kick, fill=(226, 216, 200))

    canvas.convert("RGB").save(out_path, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True, subsampling=1)


def render_plate(cfg, manifest, item, out_path: Path) -> None:
    """Editorial plate: paper background, optional photographic band, a stat or headline.

    `asset` is optional. Without it the slide is pure type, which is how a story
    with one great photograph still becomes a seven-slide carousel.
    """
    palette = cfg["palette"]
    paper = hex_rgb(palette["paper"])
    ink = hex_rgb(palette["ink"])
    muted = hex_rgb(palette["muted"])
    rule = hex_rgb(palette["rule"])
    accent = hex_rgb(palette["accent"])

    canvas = paper_texture(Image.new("RGB", (W, H), paper), 0.010)
    draw = ImageDraw.Draw(canvas)

    margin = 76
    f_tag = load_font(SEGOE_SEMI, 20)
    tag = "CLUEFOLIO  Â·  " + cfg["cover"]["category"]
    draw_tracked(draw, (margin, 62), tag, f_tag, muted, tracking=2.4)
    draw.line([(margin, 98), (W - margin, 98)], fill=rule, width=2)

    y = 156
    kicker = item.get("kicker")
    if kicker:
        f_kick = load_font(SEGOE_SEMI, 24)
        draw_tracked(draw, (margin, y), kicker.upper(), f_kick, accent, tracking=3.0)
        y += 58

    head_lines = wrap_to_width(draw, item.get("headline", ""), load_font(GEORGIA_BOLD, 60), W - margin * 2)
    f_head, head_size = fit_headline(draw, head_lines, W - margin * 2, 60, 40, GEORGIA_BOLD)
    head_lines = wrap_to_width(draw, item.get("headline", ""), f_head, W - margin * 2)
    lh = int(head_size * 1.14)
    for line in head_lines:
        draw.text((margin, y), line, font=f_head, fill=ink)
        y += lh

    band_item = item if item.get("asset") else None
    stat = item.get("stat")
    if stat:
        f_stat, stat_size = fit_headline(draw, [stat], W - margin * 2, 210, 110, GEORGIA_BOLD)
        y += 26
        draw.text((margin, y), stat, font=f_stat, fill=accent)
        y += int(stat_size * 0.98)
        if item.get("stat_label"):
            f_lab = load_font(SEGOE_SEMI, 26)
            draw_tracked(draw, (margin, y), item["stat_label"].upper(), f_lab, muted, tracking=2.6)
            y += 46

    if band_item:
        asset = next(a for a in manifest["assets"] if a["id"] == band_item["asset"])
        src_path = ROOT / "content" / cfg["slug"] / "assets" / (asset["id"] + Path(asset["file_url"]).suffix)
        if not src_path.exists():
            candidates = list(src_path.parent.glob(asset["id"] + ".*"))
            if not candidates:
                raise FileNotFoundError(src_path)
            src_path = candidates[0]

        src = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
        crop = band_item.get("crop", {})
        band_h = 460
        band = crop_to_ratio(src, W, band_h, crop.get("fx", 0.5), crop.get("fy", 0.5), crop.get("zoom", 1.0))
        band = apply_contrast(band, band_item.get("contrast", 1.0))
        band = warm_duotone(band, 0.52)
        band = add_grain(band, band_item.get("grain", 0.02), seed=23)

        y = max(y + 40, 460)
        canvas.paste(band, (0, y))
        draw.line([(0, y), (W, y)], fill=rule, width=1)
        draw.line([(0, y + band_h), (W, y + band_h)], fill=rule, width=1)
        y += band_h + 40

        f_cred = load_font(SEGOE, 19)
        for line in wrap_to_width(draw, asset.get("credit", ""), f_cred, W - margin * 2)[:1]:
            draw.text((margin, y), line, font=f_cred, fill=muted)
            y += 30
    else:
        y += 40
        draw.rectangle([margin, y, margin + 120, y + 4], fill=accent)
        y += 4 + 34

    f_body = load_font(GEORGIA, 31)
    body_lh = int(31 * 1.5)
    for line in wrap_to_width(draw, item.get("body", ""), f_body, W - margin * 2):
        draw.text((margin, y), line, font=f_body, fill=ink)
        y += body_lh

    draw.line([(margin, 1244), (W - margin, 1244)], fill=rule, width=2)
    draw_tracked(draw, (margin, 1266), "CLUEFOLIO", f_tag, muted, tracking=2.4)
    right = cfg.get("rail", "POST 001")
    rw = tracked_width(draw, right, f_tag, tracking=2.4)
    draw_tracked(draw, (W - margin - rw, 1266), right, f_tag, muted, tracking=2.4)

    canvas.save(out_path, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True, subsampling=1)


def render_cta(cfg, item, out_path: Path) -> None:
    """Closing card: wordmark, reason to follow, and the follow button."""
    palette = cfg["palette"]
    paper = hex_rgb(palette["paper"])
    ink = hex_rgb(palette["ink"])
    accent = hex_rgb(palette["accent"])
    muted = hex_rgb(palette["muted"])

    canvas = paper_texture(Image.new("RGB", (W, H), ink), 0.008, seed=5)
    draw = ImageDraw.Draw(canvas)

    # Brand logo. The primary asset is brand/logo.png (the studio mark, with a
    # black background knocked out). Fall back to the generated ring mark.
    logo_path = ROOT / "brand" / "logo.png"
    fallback_path = ROOT / "brand" / "logo-mark-light.png"
    headline_top = 420
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo_w = 480
        logo_h = round(logo.height * logo_w / logo.width)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        canvas.paste(logo, ((W - logo_w) // 2, 96), logo)
        headline_top = 96 + logo_h + 84
    elif fallback_path.exists():
        mark_size = 188
        mark = Image.open(fallback_path).convert("RGBA").resize((mark_size, mark_size), Image.LANCZOS)
        canvas.paste(mark, ((W - mark_size) // 2, 128), mark)
        f_mark = load_font(SEGOE_SEMI, 34)
        wordmark = "CLUEFOLIO"
        ww = tracked_width(draw, wordmark, f_mark, tracking=9.0)
        draw_tracked(draw, (W // 2 - ww / 2, 348), wordmark, f_mark, paper, tracking=9.0)
        headline_top = 420
    else:
        cx, cy, r = W // 2, 222, 62
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=accent, width=6)
        draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=paper)

    f_head = load_font(GEORGIA_BOLD, 62)
    headline = item.get("headline", "There's a story like this every day.")
    lines = wrap_to_width(draw, headline, f_head, W - 240)
    y = headline_top
    for line in lines[:4]:
        lw = draw.textlength(line, font=f_head)
        draw.text((W // 2 - lw / 2, y), line, font=f_head, fill=paper)
        y += int(62 * 1.18)

    y += 28
    f_sub = load_font(GEORGIA_ITALIC, 30)
    for line in wrap_to_width(draw, item.get("sub", ""), f_sub, W - 260)[:2]:
        lw = draw.textlength(line, font=f_sub)
        draw.text((W // 2 - lw / 2, y), line, font=f_sub, fill=(206, 196, 180))
        y += int(30 * 1.5)

    # Button sits on a fixed anchor so long copy can never push it off-canvas.
    label = item.get("button", "FOLLOW @CLUEFOLIO")
    f_btn = load_font(SEGOE_SEMI, 34)
    bw = tracked_width(draw, label, f_btn, tracking=2.6)
    pad_x, pad_y = 56, 30
    bx0 = (W - bw) / 2 - pad_x
    bx1 = (W + bw) / 2 + pad_x
    by0 = 990
    by1 = by0 + f_btn.size + pad_y * 2
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=(by1 - by0) / 2, fill=accent)
    draw_tracked(
        draw,
        ((W - bw) / 2, by0 + pad_y - 2),
        label,
        f_btn,
        paper,
        tracking=2.6,
    )

    handle = item.get("handle", "@cluefolio")
    f_handle = load_font(SEGOE_SEMI, 26)
    hw = tracked_width(draw, handle, f_handle, tracking=2.4)
    draw_tracked(draw, (W // 2 - hw / 2, 1140), handle, f_handle, muted, tracking=2.4)

    draw.line([(120, 1244), (W - 120, 1244)], fill=(*paper, 40), width=1)
    f_foot = load_font(SEGOE, 19)
    foot = item.get("footnote", "Authentic archival imagery. Sources in every caption.")
    fw = tracked_width(draw, foot, f_foot, tracking=1.4)
    draw_tracked(draw, (W // 2 - fw / 2, 1266), foot, f_foot, muted, tracking=1.4)

    canvas.save(out_path, "JPEG", quality=JPEG_QUALITY, progressive=True, optimize=True, subsampling=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--only", default=None, help="render only a matching output prefix, e.g. 01")
    args = ap.parse_args()

    post_dir = ROOT / "content" / args.slug
    cfg = json.loads((post_dir / "render-config.json").read_text(encoding="utf-8"))
    manifest = json.loads((post_dir / "assets" / "manifest.json").read_text(encoding="utf-8"))
    out_dir = post_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    jobs.append(("01-cover.jpg", lambda p: render_cover(cfg, manifest, p)))
    for item in cfg["interiors"]:
        if item.get("template") == "plate":
            jobs.append((item["out"], lambda p, it=item: render_plate(cfg, manifest, it, p)))
        elif item.get("template") == "photo":
            jobs.append((item["out"], lambda p, it=item: render_photo_slide(cfg, manifest, it, p)))
        else:
            jobs.append((item["out"], lambda p, it=item: render_interior(cfg, manifest, it, p)))

    cta = cfg.get("cta")
    if cta:
        out_name = cta.get("out") or f"{len(jobs) + 1:02d}-cta.jpg"
        jobs.append((out_name, lambda p: render_cta(cfg, cta, p)))

    made = 0
    for name, fn in jobs:
        if args.only and not name.startswith(args.only):
            continue
        out = out_dir / name
        fn(out)
        size = out.stat().st_size
        print(f"  OK  {name}  {size:,} bytes")
        made += 1

    print(f"\nRendered {made} image(s) to {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

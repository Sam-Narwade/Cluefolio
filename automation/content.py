"""Post selection, plan building, and pre-flight validation."""

from __future__ import annotations

import json
import urllib.parse
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from .config import ROOT

IG_CAPTION_LIMIT = 2200
FB_CAPTION_LIMIT = 63206
FB_HOUSE_TARGET = 2252
MAX_CAROUSEL = 10
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def today_et() -> str:
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def load_dashboard(root: Path = ROOT) -> dict:
    path = root / "content" / "dashboard.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: python scripts/build_dashboard_data.py")
    return json.loads(path.read_text(encoding="utf-8"))


def find_post(dashboard: dict, number_or_slug: str) -> dict | None:
    value = str(number_or_slug).strip().lower()
    for post in dashboard.get("posts", []):
        if post.get("number", "").lower() == value or post.get("slug", "").lower() == value:
            return post
    return None


def is_publishable(post: dict) -> bool:
    """A post may only publish itself once its pack is marked ready.

    Drafts and in-review packs must never be picked up by the scheduled run.
    """
    return str(post.get("status", "")).strip().lower() == "ready"


def select_due(posts: list[dict], on_date: str | None = None) -> dict | None:
    target = on_date or today_et()
    for post in posts:
        if post.get("date") == target and is_publishable(post):
            return post
    return None


def public_image_url(base_url: str, slug: str, filename: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/content/{urllib.parse.quote(slug)}/images/{urllib.parse.quote(filename)}"


def image_path(post: dict, filename: str, root: Path = ROOT) -> Path:
    return root / "content" / post["slug"] / "images" / filename


def build_plan(post: dict, base_url: str) -> dict:
    images = []
    for image in post.get("images", []):
        images.append({
            "file": image["file"],
            "url": public_image_url(base_url, post["slug"], image["file"]),
            "alt": image.get("alt") or post["captions"].get("alt_text", ""),
            "credit": image.get("credit", ""),
            "ai": bool(image.get("ai")),
        })

    ig_caption = post["captions"]["instagram"]
    fb_caption = post["captions"]["facebook"]
    return {
        "number": post["number"],
        "slug": post["slug"],
        "title": post["title"],
        "date": post["date"],
        "format": "carousel" if len(images) > 1 else "single",
        "images": images,
        "instagram_caption": ig_caption,
        "facebook_caption": fb_caption,
        "first_comment": post["captions"].get("first_comment", "").strip(),
        "ig_chars": len(ig_caption),
        "fb_chars": len(fb_caption),
        "alt_text": post["captions"].get("alt_text", ""),
    }


def validate_plan(post: dict, plan: dict, root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not plan["images"]:
        errors.append("Post has no images")
    if len(plan["images"]) > MAX_CAROUSEL:
        errors.append(f"Instagram carousel supports at most {MAX_CAROUSEL} images")

    if plan["ig_chars"] > IG_CAPTION_LIMIT:
        errors.append(f"Instagram caption is {plan['ig_chars']} characters (limit {IG_CAPTION_LIMIT})")
    if plan["fb_chars"] > FB_CAPTION_LIMIT:
        errors.append(f"Facebook caption is {plan['fb_chars']} characters (limit {FB_CAPTION_LIMIT})")
    elif plan["fb_chars"] > FB_HOUSE_TARGET:
        warnings.append(f"Facebook caption is above the house target of {FB_HOUSE_TARGET} characters")

    for image in plan["images"]:
        url = image["url"]
        if not url.startswith("https://"):
            errors.append(f"Image URL must be public HTTPS: {url}")
        if any(token in url for token in ("YOURUSER", "YOURREPO", "localhost", "127.0.0.1")):
            errors.append(f"Image URL still uses a placeholder or local host: {url}")

        path = image_path(post, image["file"], root)
        if not path.exists():
            errors.append(f"Missing image file: {path}")
            continue
        size = path.stat().st_size
        if size > MAX_IMAGE_BYTES:
            errors.append(f"{image['file']} is {size / 1024 / 1024:.1f} MB (limit 8 MB)")
        try:
            with Image.open(path) as opened:
                width, height = opened.size
        except Exception as exc:  # noqa: BLE001 - report the real file problem
            errors.append(f"{image['file']} is not a readable image: {exc}")
            continue
        if width < 320 or height < 320:
            errors.append(f"{image['file']} is too small: {width}x{height}")
        ratio = width / height
        if not 0.79 <= ratio <= 1.92:
            errors.append(f"{image['file']} has an unsupported aspect ratio: {width}x{height}")
        elif abs(ratio - 0.8) > 0.02:
            warnings.append(f"{image['file']} is not 4:5 ({width}x{height})")

        if not image.get("alt", "").strip():
            warnings.append(f"{image['file']} has no alt text")

    return errors, warnings

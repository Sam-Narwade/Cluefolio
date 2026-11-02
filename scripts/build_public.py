#!/usr/bin/env python3
"""Assemble the GitHub Pages artifact.

The public site lives at the Pages root. Post images are published under
/content/<slug>/images/ so the Meta Graph API can fetch stable HTTPS URLs.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"


def main() -> int:
    if not SITE.exists():
        print("site/ is missing. Run: python scripts/build_site.py")
        return 1

    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(SITE, PUBLIC)

    copied = 0
    for post_dir in sorted(CONTENT.iterdir()):
        images = post_dir / "images"
        if not images.is_dir():
            continue
        destination = PUBLIC / "content" / post_dir.name / "images"
        destination.mkdir(parents=True, exist_ok=True)
        for image in sorted(images.glob("*.jpg")):
            shutil.copy2(image, destination / image.name)
            copied += 1

    (PUBLIC / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built public/ with {copied} post images for GitHub Pages")
    print(f"  {PUBLIC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

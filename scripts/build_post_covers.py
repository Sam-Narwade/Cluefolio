#!/usr/bin/env python3
"""Build the cover package for every post in the season.

For each post this writes:

    content/<slug>/assets/manifest.json
    content/<slug>/assets/<asset>.jpg
    content/<slug>/render-config.json
    content/<slug>/images/01-cover.jpg

Run:

    python scripts/build_post_covers.py
    python scripts/build_post_covers.py --only hinderburg

The source images live in content/_sources/. Authentic archival photographs are
used wherever a usable, rights-clear image exists. Two posts use a disclosed
editorial reconstruction because the authentic record is either unusable at
1080px or still in copyright.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "content" / "_sources"

PALETTE = {
    "paper": "#F4EFE6",
    "ink": "#15130F",
    "muted": "#5B5348",
    "rule": "#B9AE9C",
    "accent": "#8C2F1E",
}

POSTS = [
    {
        "slug": "hinderburg",
        "number": "002",
        "source": "hindenburg.jpg",
        "asset_id": "hindenburg-cover",
        "asset_file": "hindenburg-cover.jpg",
        "title": "Hindenburg disaster at Lakehurst, 1937",
        "creator": "Unknown photographer, 1937",
        "source_url": "https://commons.wikimedia.org/wiki/File:Hindenburg_disaster.jpg",
        "license": "Public domain in the United States (published 1937; copyright not renewed)",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "The German airship Hindenburg, its tail engulfed in a huge ball of flame, hangs nose-up beside the Lakehurst mooring mast as tiny figures run below.",
        "headline": ["THE AIRSHIP", "FELL FROM THE SKY"],
        "category": "DISASTERS",
        "dateline": "Lakehurst, New Jersey  \u00b7  May 6, 1937",
        "crop": {"fx": 0.50, "fy": 0.46, "zoom": 1.04},
        "ai": False,
    },
    {
        "slug": "peshtigo-fire",
        "number": "003",
        "source": "peshtigo.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "Ruins of Peshtigo, Wisconsin, after the 1871 fire",
        "creator": "Unknown photographer, 1871",
        "source_url": "https://commons.wikimedia.org/wiki/File:The_ruins_of_Peshtigo_and_the_surrounding_landscape_after_1871_fire.jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A black-and-white photograph of the burned ruins of Peshtigo, Wisconsin, after the 1871 fire, with shattered trees, scattered debris, and a few figures in the distance.",
        "headline": ["THE FIRE THAT", "WAS FORGOTTEN"],
        "category": "DISASTERS",
        "dateline": "Peshtigo, Wisconsin  \u00b7  October 8, 1871",
        "crop": {"fx": 0.50, "fy": 0.54, "zoom": 1.00},
        "ai": False,
    },
    {
        "slug": "johnstown-flood",
        "number": "004",
        "source": "johnstown.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "A house torn from its foundation in the Johnstown Flood, 1889",
        "creator": "Unknown photographer, 1889",
        "source_url": "https://commons.wikimedia.org/wiki/File:Johnstown_Tree_in_House.jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A large wooden house stands tipped on its side amid flood debris in Johnstown, Pennsylvania, after the 1889 dam failure, with a massive tree trunk driven through its wall.",
        "headline": ["THE DAM", "NOBODY WOULD FIX"],
        "category": "ENGINEERING FAILURE",
        "dateline": "Johnstown, Pennsylvania  \u00b7  May 31, 1889",
        "crop": {"fx": 0.53, "fy": 0.50, "zoom": 1.02},
        "ai": False,
    },
    {
        "slug": "iroquois-theatre",
        "number": "005",
        "source": "iroquois.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "The Iroquois Theatre, Chicago, before the 1903 fire",
        "creator": "Unknown photographer, c. 1903",
        "source_url": "https://commons.wikimedia.org/wiki/File:IroquoisTheater.jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A black-and-white photograph of the Iroquois Theatre entrance in Chicago, with a striped canopy over the sidewalk and a crowd gathered outside.",
        "headline": ["THE DOORS THAT", "OPENED INWARD"],
        "category": "DISASTERS / SAFETY",
        "dateline": "Chicago, Illinois  \u00b7  December 30, 1903",
        "crop": {"fx": 0.50, "fy": 0.50, "zoom": 1.02},
        "ai": False,
    },
    {
        "slug": "monongah-mine",
        "number": "006",
        "source": "monongah-ai.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "Editorial reconstruction: Monongah mine entrance, 1907",
        "creator": "Cluefolio Studio (editorial reconstruction)",
        "source_url": "",
        "license": "Original work created for this project. Not a historical photograph. Disclosed as an editorial reconstruction.",
        "credit": "Editorial reconstruction by Cluefolio Studio. Not a historical photograph.",
        "alt": "An editorial reconstruction of a West Virginia coal mine entrance in winter 1907, with dark wooden tipples, smoke, and a narrow tramway between the buildings.",
        "headline": ["THE WORST MINE", "DISASTER IN AMERICA"],
        "category": "LABOR / DISASTERS",
        "dateline": "Monongah, West Virginia  \u00b7  December 6, 1907",
        "crop": {"fx": 0.50, "fy": 0.50, "zoom": 1.16},
        "ai": True,
        "disclosure": "AI RECONSTRUCTION",
    },
    {
        "slug": "halifax-explosion",
        "number": "007",
        "source": "halifax.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "The Halifax Explosion blast cloud, December 6, 1917",
        "creator": "Unknown photographer, 1917",
        "source_url": "https://commons.wikimedia.org/wiki/File:Halifax_Explosion_blast_cloud_restored.jpg",
        "license": "Public domain in Canada and the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A towering column of smoke rises over Halifax harbour after the 1917 munitions explosion, with a ship visible in the foreground.",
        "headline": ["THE BLAST THAT", "FLATTENED A CITY"],
        "category": "DISASTERS",
        "dateline": "Halifax, Nova Scotia  \u00b7  December 6, 1917",
        "crop": {"fx": 0.50, "fy": 0.42, "zoom": 1.00},
        "ai": False,
    },
    {
        "slug": "molasses-flood",
        "number": "008",
        "source": "molasses.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "Aftermath of the Great Molasses Flood, Boston, 1919",
        "creator": "Unknown photographer, 1919",
        "source_url": "https://commons.wikimedia.org/wiki/File:BostonMolassesDisaster.jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "An elevated view of the aftermath of the Great Molasses Flood in Boston's North End, showing collapsed buildings, wreckage, and crowds along the waterfront.",
        "headline": ["THE WAVE THAT", "CAME FROM A TANK"],
        "category": "ENGINEERING FAILURE",
        "dateline": "Boston, Massachusetts  \u00b7  January 15, 1919",
        "crop": {"fx": 0.46, "fy": 0.54, "zoom": 1.02},
        "ai": False,
    },
    {
        "slug": "radium-girls",
        "number": "009",
        "source": "radium.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "Workers painting watch dials with radium paint, c. 1922",
        "creator": "Unknown photographer, c. 1922",
        "source_url": "https://commons.wikimedia.org/wiki/File:All_women_or_girls_using_radium_paint_with_no_protection_or_warnings_in_1922,_from-_USRadiumGirls-Argonne1,ca1922-23-150dpi_(cropped).jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A row of young women in 1920s dresses sit at long worktables in a factory, painting watch dials with radium luminous paint.",
        "headline": ["THE WOMEN", "WHO GLOWED"],
        "category": "LABOR / SCIENCE",
        "dateline": "Orange, New Jersey  \u00b7  1922",
        "crop": {"fx": 0.50, "fy": 0.50, "zoom": 1.00},
        "ai": False,
    },
    {
        "slug": "cocoanut-grove",
        "number": "010",
        "source": "cocoanut-ai.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "Editorial reconstruction: Boston street after the Cocoanut Grove fire, 1942",
        "creator": "Cluefolio Studio (editorial reconstruction)",
        "source_url": "",
        "license": "Original work created for this project. Not a historical photograph. Disclosed as an editorial reconstruction.",
        "credit": "Editorial reconstruction by Cluefolio Studio. Not a historical photograph.",
        "alt": "An editorial reconstruction of a crowded Boston street at night in 1942, with smoke drifting between buildings and a crowd gathered outside a nightclub.",
        "headline": ["THE FIRE THAT", "CHANGED BURN CARE"],
        "category": "DISASTERS / MEDICINE",
        "dateline": "Boston, Massachusetts  \u00b7  November 28, 1942",
        "crop": {"fx": 0.50, "fy": 0.48, "zoom": 1.18},
        "ai": True,
        "disclosure": "AI RECONSTRUCTION",
    },
    {
        "slug": "hartford-circus-fire",
        "number": "011",
        "source": "hartford.jpg",
        "asset_id": "cover",
        "asset_file": "cover.jpg",
        "title": "The Hartford circus fire, July 6, 1944",
        "creator": "Unknown photographer, 1944",
        "source_url": "https://commons.wikimedia.org/wiki/File:Hartford_circus_fire.jpg",
        "license": "Public domain in the United States",
        "credit": "Photograph: public domain, via Wikimedia Commons",
        "alt": "A circus tent burns at the Hartford circus fire in 1944, with flames and black smoke rising above the canvas while people flee in the foreground.",
        "headline": ["THE TENT THAT", "BURNED IN MINUTES"],
        "category": "DISASTERS / SAFETY",
        "dateline": "Hartford, Connecticut  \u00b7  July 6, 1944",
        "crop": {"fx": 0.50, "fy": 0.44, "zoom": 1.04},
        "ai": False,
    },
]


def build_one(post: dict) -> None:
    slug = post["slug"]
    post_dir = ROOT / "content" / slug
    assets = post_dir / "assets"
    images = post_dir / "images"
    assets.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)

    src = SOURCES / post["source"]
    if not src.exists():
        raise FileNotFoundError(f"missing source image: {src}")

    dest = assets / post["asset_file"]
    shutil.copy2(src, dest)

    manifest = {
        "slug": slug,
        "assets": [
            {
                "id": post["asset_id"],
                "title": post["title"],
                "archive": "Wikimedia Commons" if not post["ai"] else "Cluefolio Studio",
                "source_url": post["source_url"],
                "file_url": post["source_url"] or f"content/_sources/{post['source']}",
                "creator": post["creator"],
                "date": "",
                "license": post["license"],
                "credit": post["credit"],
                "depicts": post["alt"],
                "role": "cover",
                "alt_text": post["alt"],
                "ai_generated": post["ai"],
            }
        ],
    }
    (assets / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    config = {
        "slug": slug,
        "rail": f"POST {post['number']}",
        "canvas": {"width": 1080, "height": 1350},
        "palette": PALETTE,
        "cover": {
            "asset": post["asset_id"],
            "wordmark": "CLUEFOLIO",
            "category": post["category"],
            "headline": post["headline"],
            "dateline": post["dateline"],
            "crop": post["crop"],
            "disclosure": post.get("disclosure", ""),
        },
        "interiors": [],
    }
    (post_dir / "render-config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_post.py"), "--slug", slug],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    print(f"  OK  {slug:24s} -> content/{slug}/images/01-cover.jpg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="build a single slug")
    args = ap.parse_args()

    made = 0
    for post in POSTS:
        if args.only and post["slug"] != args.only:
            continue
        build_one(post)
        made += 1
    print(f"\nBuilt {made} cover(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

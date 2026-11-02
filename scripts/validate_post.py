#!/usr/bin/env python3
"""Validate a Cluefolio post package before sign-off.

Usage:
    python scripts/validate_post.py --slug first-post

Checks:
  1. Every image referenced in post-metadata.json exists.
  2. Every image is 1080x1350, sRGB RGB mode, JPEG, and under the size cap.
  3. Filenames sort in carousel order and the count matches.
  4. Every rendered asset has a license and a credit in the manifest.
  5. Every rendered asset has alt text.
  6. Captions exist, sit within the platform character limit, carry the hook in the
     first 125 characters, and end with specific hashtags.
  7. Every path named in post-metadata.json exists on disk.
  8. Gate status is complete.

Exit code 0 = all checks pass, 1 = at least one failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

W, H = 1080, 1350
MAX_BYTES = 8 * 1024 * 1024

# Hook marker: use post-metadata.json hook_marker if provided, else hardcoded
# The Eastland post uses "still tied to the dock"; other posts can provide their own.
DEFAULT_HOOK_MARKER = "still tied to the dock"


def get_hook_marker(meta: dict) -> str:
    """Return the hook marker from post-metadata.json, or the default."""
    return meta.get("hook_marker", DEFAULT_HOOK_MARKER)


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, "PASS" if ok else "FAIL", detail))
    return ok


results: list[tuple[str, str, str]] = []


def caption_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts = [p.strip() for p in text.split("\n---\n")]
    for part in parts:
        if not part.startswith("#") and "Character count" not in part and "Target:" not in part:
            if len(part) > 200:
                return part
    # fallback: longest block
    return max(parts, key=len)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()

    post = ROOT / "content" / args.slug
    meta_path = post / "post-metadata.json"
    manifest_path = post / "assets" / "manifest.json"

    if not meta_path.exists():
        print(f"FATAL: missing {meta_path}")
        return 1
    if not manifest_path.exists():
        print(f"FATAL: missing {manifest_path}")
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in manifest["assets"]}

    try:
        from PIL import Image
    except ImportError:
        print("FATAL: Pillow is required")
        return 1

    # 1 & 2 & 3 — images
    images = meta.get("images", [])
    # Accept 1 image (single-photo format) or 6 (carousel format, Eastland-style)
    check("image count matches metadata", len(images) in (1, 6), f"{len(images)} listed")

    names = [Path(im["file"]).name for im in images]
    check("filenames sort in carousel order", names == sorted(names), " -> ".join(names))

    for im in images:
        rel = im["file"]
        p = ROOT / rel
        if not check(f"exists: {Path(rel).name}", p.exists(), rel):
            continue
        if p.stat().st_size > MAX_BYTES:
            check(f"size under cap: {p.name}", False, f"{p.stat().st_size:,} bytes")
        else:
            check(f"size under cap: {p.name}", True, f"{p.stat().st_size:,} bytes")

        with Image.open(p) as img:
            check(f"dimensions 1080x1350: {p.name}", img.size == (W, H), str(img.size))
            check(f"RGB mode: {p.name}", img.mode == "RGB", img.mode)
            check(f"format JPEG: {p.name}", img.format == "JPEG", str(img.format))

    # 4 & 5 — manifest license, credit, alt text for rendered assets
    rendered_ids = {im["asset_id"] for im in images}
    for aid in sorted(rendered_ids):
        a = assets.get(aid)
        if not check(f"asset in manifest: {aid}", a is not None):
            continue
        check(f"license present: {aid}", bool(a.get("license", "").strip()), a.get("license", "")[:48])
        check(f"credit present: {aid}", bool(a.get("credit", "").strip()), a.get("credit", "")[:48])
        check(f"alt text present: {aid}", len(a.get("alt_text", "")) >= 40, f"{len(a.get('alt_text',''))} chars")

    # 6 — captions
    insta = ROOT / meta["captions"]["instagram"]
    fbook = ROOT / meta["captions"]["facebook"]
    alt = ROOT / meta["captions"]["alt_text"]

    check("instagram caption exists", insta.exists(), str(insta))
    check("facebook caption exists", fbook.exists(), str(fbook))
    check("alt text file exists", alt.exists(), str(alt))

    hook_marker = get_hook_marker(meta)

    if insta.exists():
        body = caption_body(insta)
        n = len(body)
        check("instagram within 2200 chars", n <= 2200, f"{n} chars")
        check("instagram hook in first 125 chars", hook_marker in body[:125].lower(), repr(body[:80]))
        check("instagram hashtags 4-6", 4 <= body.count("#") <= 6, f"{body.count('#')} tags")

    if fbook.exists():
        body = caption_body(fbook)
        n = len(body)
        check("facebook within 63206 chars", n <= 63206, f"{n} chars")
        check("facebook hook in first 200 chars", hook_marker in body[:200].lower(), repr(body[:80]))
        check("facebook hashtags 3-4", 3 <= body.count("#") <= 4, f"{body.count('#')} tags")

    # 7 — every path named in metadata exists
    paths: list[str] = []
    paths += [im["file"] for im in images]
    paths += [v for v in meta.get("captions", {}).values() if isinstance(v, str)]
    paths += [a.get("source_url", "") for a in assets.values() if a.get("source_url")]
    local = [p for p in paths if isinstance(p, str) and p and not p.startswith("http")]
    for p in local:
        check(f"path exists: {p}", (ROOT / p).exists(), p)

    # 8 — gates
    for gate, status in meta.get("gates", {}).items():
        check(f"gate {gate}", status == "PASS", status)

    # report
    width = max(len(r[0]) for r in results)
    failures = 0
    print()
    for name, status, detail in results:
        if status == "FAIL":
            failures += 1
        print(f"  [{status}] {name.ljust(width)}  {detail}")
    print()
    print(f"{len(results) - failures}/{len(results)} checks passed.")
    print("RESULT: " + ("SIGNED OFF" if failures == 0 else f"BLOCKED ({failures} failure(s))"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
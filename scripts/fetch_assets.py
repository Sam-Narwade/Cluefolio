#!/usr/bin/env python3
"""Fetch archival assets listed in a post manifest.

Usage:
    python scripts/fetch_assets.py --slug first-post
    python scripts/fetch_assets.py --slug first-post --force

Reads   content/<slug>/assets/manifest.json
Writes  content/<slug>/assets/<id>.<ext>
        content/<slug>/assets/fetch-report.json

Design notes:
- One polite user agent, sequential requests, exponential backoff on 429/5xx.
- Never overwrites an existing file unless --force is passed (cache-friendly).
- Records SHA-256, byte size, and HTTP status for provenance.
- Refuses to fetch if the manifest entry lacks a license field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = (
    "CluefolioArchiveBot/1.0 (archival research; contact: studio@cluefolio.local) "
    "python-urllib"
)
TIMEOUT = 90
MAX_RETRIES = 5


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guess_ext(url: str, fallback: str = ".jpg") -> str:
    clean = url.split("?")[0].lower()
    for ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"):
        if clean.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return fallback


def download(url: str, dest: Path) -> tuple[int, int]:
    """Download url to dest. Returns (status, bytes). Raises on failure."""
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = resp.status
                data = resp.read()
            if not data:
                raise ValueError("empty response body")
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            return status, len(data)
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                wait = min(60, 2 ** attempt * 2)
                log(f"    HTTP {exc.code}; retry {attempt}/{MAX_RETRIES - 1} in {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < MAX_RETRIES:
                wait = min(30, 2 ** attempt)
                log(f"    {type(exc).__name__}; retry {attempt}/{MAX_RETRIES - 1} in {wait}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"download failed: {last_err}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    ap.add_argument("--only", default=None, help="fetch a single asset id")
    args = ap.parse_args()

    post_dir = ROOT / "content" / args.slug
    manifest_path = post_dir / "assets" / "manifest.json"
    if not manifest_path.exists():
        log(f"ERROR: manifest not found: {manifest_path}")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest.get("assets", manifest if isinstance(manifest, list) else [])
    if not assets:
        log("ERROR: manifest has no assets")
        return 1

    report = []
    failures = 0

    for entry in assets:
        aid = entry.get("id")
        if not aid:
            log("SKIP: manifest entry without id")
            continue
        if args.only and aid != args.only:
            continue

        license_text = (entry.get("license") or "").strip()
        if not license_text:
            log(f"REFUSE {aid}: manifest entry has no license field")
            report.append({"id": aid, "status": "refused", "reason": "missing license"})
            failures += 1
            continue

        url = entry.get("file_url") or entry.get("url")
        if not url:
            log(f"REFUSE {aid}: no file_url")
            report.append({"id": aid, "status": "refused", "reason": "missing file_url"})
            failures += 1
            continue

        ext = guess_ext(url)
        dest = post_dir / "assets" / f"{aid}{ext}"

        if dest.exists() and not args.force:
            log(f"CACHE  {aid}  {dest.name}  ({dest.stat().st_size:,} bytes)")
            report.append(
                {
                    "id": aid,
                    "status": "cached",
                    "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256(dest),
                    "source_url": url,
                    "license": license_text,
                }
            )
            continue

        log(f"GET    {aid}  {url}")
        try:
            status, nbytes = download(url, dest)
            digest = sha256(dest)
            log(f"  OK   {status}  {nbytes:,} bytes  sha256={digest[:16]}…")
            report.append(
                {
                    "id": aid,
                    "status": "downloaded",
                    "http_status": status,
                    "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": nbytes,
                    "sha256": digest,
                    "source_url": url,
                    "license": license_text,
                }
            )
            time.sleep(2)  # be polite between requests
        except Exception as exc:  # noqa: BLE001
            log(f"  FAIL {aid}: {exc}")
            report.append({"id": aid, "status": "failed", "reason": str(exc), "source_url": url})
            failures += 1

    out = post_dir / "assets" / "fetch-report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"\nReport: {out.relative_to(ROOT)}")
    log(f"Failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

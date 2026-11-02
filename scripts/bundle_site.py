#!/usr/bin/env python3
"""Bundle the built site into ONE self-contained HTML file.

No server, no relative paths, no external requests. Every stylesheet, script,
and photograph is embedded in the file itself, so it opens from a USB stick,
an email attachment, or a browser with networking disabled.

Usage:
    python scripts/bundle_site.py
Writes:
    site/cluefolio.html
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

PAGES = [
    ("home", "index.html"),
    ("post", "post-001.html"),
    ("calendar", "calendar.html"),
    ("agency", "agency.html"),
    ("brand", "brand.html"),
    ("process", "process.html"),
    ("resources", "resources.html"),
]

LINK_MAP = {
    "index.html": "#home",
    "post-001.html": "#post",
    "calendar.html": "#calendar",
    "agency.html": "#agency",
    "brand.html": "#brand",
    "process.html": "#process",
    "resources.html": "#resources",
}

NAV_ITEMS = [
    ("home", "Home"),
    ("post", "Post 001"),
    ("calendar", "Calendar"),
    ("agency", "Agency"),
    ("brand", "Brand"),
    ("process", "Process"),
    ("resources", "Resources"),
]

EXTRA_CSS = """
[data-page] { scroll-margin-top: 74px; }
[data-page] + [data-page] > section:first-child { border-top: 1px solid var(--rule); }
.nav-links a.active { color: var(--ink); border-bottom-color: var(--accent); }
"""


def data_uri(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def main() -> int:
    missing = [f for _, f in PAGES if not (SITE / f).exists()]
    if missing:
        print("Missing built pages:", ", ".join(missing))
        print("Run: python scripts/build_site.py")
        return 1

    css = (SITE / "assets" / "style.css").read_text(encoding="utf-8")
    js = (SITE / "assets" / "site.js").read_text(encoding="utf-8")

    # One data URI per unique image, computed once.
    cache: dict[str, str] = {}
    for img in (SITE / "assets" / "images").glob("*.jpg"):
        cache[img.name] = data_uri(img)
    print(f"Embedded {len(cache)} images")

    fragments: list[str] = []
    for page_id, filename in PAGES:
        html = (SITE / filename).read_text(encoding="utf-8")
        m = re.search(r"<main>(.*?)</main>", html, re.S)
        if not m:
            print(f"error: no <main> in {filename}")
            return 1
        body = m.group(1).strip()

        # The lightbox attribute repeats the same path; in the bundle that would
        # embed every photograph twice. The script falls back to img.src.
        body = re.sub(r'\s+data-full="assets/images/[^"]+"', "", body)

        for name, uri in cache.items():
            body = body.replace(f"assets/images/{name}", uri)

        for target, anchor in LINK_MAP.items():
            body = body.replace(f'href="{target}"', f'href="{anchor}"')

        body = body.replace(' aria-current="page"', "")
        fragments.append(f'<div data-page id="{page_id}">\n{body}\n</div>')

    nav = "".join(f'<a href="#{pid}" data-nav="{pid}">{label}</a>' for pid, label in NAV_ITEMS)

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cluefolio — Post 001 and Season One</title>
<meta name="description" content="The SS Eastland disaster, six archival images, the full production record, and the ten-post season calendar.">
<link rel="icon" href="data:,">
<style>
{css}
{EXTRA_CSS}
</style>
</head>
<body>
<nav class="nav">
  <div class="nav-inner">
    <a class="brand" href="#home">CLUEFOLIO<span>.</span></a>
    <div class="nav-links">{nav}</div>
  </div>
</nav>

<main>
{chr(10).join(fragments)}
</main>

<footer>
  <div class="wrap footer-grid">
    <p><strong>Cluefolio Studio</strong> — evidence-first, image-led history for Instagram and Facebook.
    Every claim traceable, every image credited, nothing published without a human.</p>
    <p class="small">Post 001 · October 2026 · Built locally. No AI imagery used. Total production cost: $0.
    This is a single-file copy: all styles, scripts, and photographs are embedded.</p>
  </div>
</footer>

<div class="lightbox" id="lightbox" role="dialog" aria-label="Image viewer">
  <button class="close" aria-label="Close">&times;</button>
  <img alt="">
</div>

<script>
{js}
(function () {{
  var links = document.querySelectorAll("[data-nav]");
  var pages = document.querySelectorAll("[data-page]");
  function mark() {{
    var y = window.scrollY + 120;
    var active = pages[0] ? pages[0].id : "";
    pages.forEach(function (p) {{ if (p.offsetTop <= y) active = p.id; }});
    links.forEach(function (a) {{
      a.classList.toggle("active", a.getAttribute("data-nav") === active);
    }});
  }}
  window.addEventListener("scroll", mark, {{ passive: true }});
  mark();
}})();
</script>
</body>
</html>
"""

    out = SITE / "cluefolio.html"
    out.write_text(doc, encoding="utf-8")
    size = out.stat().st_size
    print(f"Wrote {out.relative_to(ROOT)}  ({size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

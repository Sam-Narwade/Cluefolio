#!/usr/bin/env python3
"""Build the Cluefolio static site from the repository's markdown and JSON.

Usage:
    python scripts/build_site.py
    python scripts/build_site.py --serve     # build, then serve on :8000

Reads   AGENCY.md, brand/*.md, resources/*.md, content/first-post/*.md,
        content/first-post/post-metadata.json, content/first-post/assets/manifest.json,
        content/first-post/render-config.json, content/calendar.json
Writes  site/*.html, site/assets/images/*, site/assets/style.css, site/assets/site.js

No external services. No network. Output is a self-contained static site.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, BaseLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
POST = ROOT / "content" / "first-post"


# --------------------------------------------------------------------------
# Minimal markdown -> HTML (the subset these documents actually use)
# --------------------------------------------------------------------------

def _inline(s: str) -> str:
    s = html.escape(s, quote=False)

    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", stash, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\"'=])(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)

    for i, c in enumerate(codes):
        s = s.replace(f"\x00{i}\x00", f"<code>{c}</code>")
    return s


def _table_sep(line: str) -> bool:
    return bool(re.match(r"^\|[\s:\-|]+\|$", line.strip()))


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_html(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    para: list[str] = []
    in_list: str | None = None
    in_code = False
    code_buf: list[str] = []
    i = 0

    def flush_para() -> None:
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            close_list()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        if not stripped:
            flush_para()
            close_list()
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < len(lines) and _table_sep(lines[i + 1]):
            flush_para()
            close_list()
            header = _cells(stripped)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i].strip()))
                i += 1
            buf = ['<div class="table-wrap"><table><thead><tr>']
            buf += [f"<th>{_inline(c)}</th>" for c in header]
            buf.append("</tr></thead><tbody>")
            for row in rows:
                buf.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
            buf.append("</tbody></table></div>")
            out.append("".join(buf))
            continue

        # headings
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # hr
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush_para()
            close_list()
            out.append("<hr>")
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            flush_para()
            close_list()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + _inline(" ".join(buf)) + "</p></blockquote>")
            continue

        # list
        m_ul = re.match(r"^[-*+]\s+(.*)$", stripped)
        m_ol = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m_ul or m_ol:
            flush_para()
            kind = "ul" if m_ul else "ol"
            if in_list != kind:
                close_list()
                out.append(f"<{kind}>")
                in_list = kind
            item = m_ul.group(1) if m_ul else m_ol.group(1)
            out.append(f"<li>{_inline(item)}</li>")
            i += 1
            continue

        # metadata lines such as **Slug:** value should not merge into one paragraph
        if re.match(r"^\*\*[^*]{1,48}:\*\*\s", stripped):
            flush_para()
            close_list()
            out.append(f'<p class="meta-line">{_inline(stripped)}</p>')
            i += 1
            continue

        # paragraph text
        close_list()
        para.append(stripped)
        i += 1

    if in_code and code_buf:
        out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    flush_para()
    close_list()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Page shell
# --------------------------------------------------------------------------

env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html"]))
env.filters["md"] = md_to_html

BASE = env.from_string("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · Cluefolio Studio</title>
<meta name="description" content="{{ description }}">
<link rel="icon" href="data:,">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<nav class="nav">
  <div class="nav-inner">
    <a class="brand" href="index.html">CLUEFOLIO<span>.</span></a>
    <div class="nav-links">
      <a href="post-001.html"{% if page == 'post' %} aria-current="page"{% endif %}>Post 001</a>
      <a href="calendar.html"{% if page == 'calendar' %} aria-current="page"{% endif %}>Calendar</a>
      <a href="agency.html"{% if page == 'agency' %} aria-current="page"{% endif %}>Agency</a>
      <a href="brand.html"{% if page == 'brand' %} aria-current="page"{% endif %}>Brand</a>
      <a href="process.html"{% if page == 'process' %} aria-current="page"{% endif %}>Process</a>
      <a href="resources.html"{% if page == 'resources' %} aria-current="page"{% endif %}>Resources</a>
    </div>
  </div>
</nav>

<main>
{{ content|safe }}
</main>

<footer>
  <div class="wrap footer-grid">
    <p><strong>Cluefolio Studio</strong> — evidence-first, image-led history for Instagram and Facebook.
    Every claim traceable, every image credited, nothing published without a human.</p>
    <p class="small">Post 001 · October 2026 · Built locally. No AI imagery used. Total production cost: $0.</p>
  </div>
</footer>

<div class="lightbox" id="lightbox" role="dialog" aria-label="Image viewer">
  <button class="close" aria-label="Close">&times;</button>
  <img alt="">
</div>
<script src="assets/site.js"></script>
</body>
</html>
""")


def page(title: str, description: str, content: str, page_id: str) -> str:
    return BASE.render(title=title, description=description, content=content, page=page_id)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    img_dir = SITE / "assets" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    meta = json.loads(read(POST / "post-metadata.json"))
    manifest = json.loads(read(POST / "assets" / "manifest.json"))
    config = json.loads(read(POST / "render-config.json"))
    calendar = json.loads(read(ROOT / "content" / "calendar.json"))

    assets = {a["id"]: a for a in manifest["assets"]}

    # copy images
    for im in meta["images"]:
        src = ROOT / im["file"]
        shutil.copy2(src, img_dir / src.name)

    # caption lines keyed by output filename
    lines = {"01-cover.jpg": " · ".join(config["cover"]["headline"])}
    for item in config["interiors"]:
        if item.get("template") == "plate":
            lines[item["out"]] = item.get("headline", "")
        else:
            lines[item["out"]] = item.get("line", "")

    cards = []
    for im in meta["images"]:
        name = Path(im["file"]).name
        a = assets[im["asset_id"]]
        cards.append(
            {
                "n": im["position"],
                "file": name,
                "alt": a["alt_text"],
                "credit": a["credit"],
                "line": lines.get(name, ""),
                "role": im["role"],
            }
        )

    # ---------------- index ----------------
    tpl_index = env.from_string("""
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-figure">
      <img src="assets/images/01-cover.jpg" alt="A long passenger steamship lies completely on its side in a narrow city river, its dark hull exposed above the waterline.">
    </div>
    <div>
      <p class="eyebrow">Post 001 · {{ post_date }}</p>
      <h1>{{ title }}</h1>
      <p class="lede">{{ subtitle }}</p>
      <div class="hero-meta">
        <span class="tag accent">Disasters</span>
        <span class="tag">6 images</span>
        <span class="tag">4:5 · 1080×1350</span>
        <span class="tag">Viral score {{ score }}/40</span>
      </div>
      <div class="actions">
        <a class="btn" href="post-001.html">View the post</a>
        <a class="btn ghost" href="calendar.html">Season calendar</a>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">The story</p>
    <h2>844 people died on a ship that never went anywhere.</h2>
    <div class="prose">
      <p>On the morning of July 24, 1915, the excursion steamer <em>Eastland</em> was moored on the Chicago River, loading Western Electric employees and their families for a company picnic. More than 2,500 people came aboard. The gangplank was still down.</p>
      <p>Shortly after 7 a.m., the ship rolled onto its side. The river there is about twenty feet deep, and the hull came to rest about twenty feet from the wharf. That shallow, narrow gap is why hundreds climbed out alive — and why hundreds below deck had minutes, not hours.</p>
      <p>844 passengers and crew died. 590 were under 25. Twenty-two entire families were wiped out. A grand jury indicted the owners, the captain, the chief engineer, and federal inspectors. The cases ended without a conviction.</p>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Inside the studio</p>
    <h2>Everything the post was built from.</h2>
    <div class="grid-3" style="margin-top:36px">
      <a class="card" href="process.html" style="text-decoration:none">
        <span class="num">PROCESS</span>
        <h3>Research to sign-off</h3>
        <p>The brief, candidate scoring, timeline, source ledger, independent fact-check, rights record, outline, hook lab, visual plan, growth plan, standards clearance, and QA.</p>
      </a>
      <a class="card" href="agency.html" style="text-decoration:none">
        <span class="num">AGENCY</span>
        <h3>Eighteen roles, six gates</h3>
        <p>The charter, the roster, the pipeline, and the rules that stop a beautiful story from drifting off the facts.</p>
      </a>
      <a class="card" href="calendar.html" style="text-decoration:none">
        <span class="num">CALENDAR</span>
        <h3>Ten posts, one season</h3>
        <p>Weekly through January 2027. Post 001 is ready; the next nine are researched briefs, each with sources to verify and an honest note on imagery.</p>
      </a>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">The record</p>
    <h2>What the fact-check changed.</h2>
    <div class="prose">
      <p>Gate 2 exists because research drifts. In this post it caught two material errors before a single caption was written.</p>
      <ul>
        <li><strong>A fabricated defendant.</strong> The draft named a man who does not appear in any source connected to the case. Removed.</li>
        <li><strong>A false conviction claim.</strong> The widely repeated story that the chief engineer was convicted conflates a 1933 <em>civil</em> ruling with criminal guilt. The defendants were acquitted in February 1916 and no trial was ever held in Chicago. Corrected.</li>
      </ul>
      <p>An unsupported death-toll figure was also removed, and the rights audit caught a wrong Library of Congress identifier written from memory. The full trail is in the <a href="process.html">process record</a>.</p>
    </div>
  </div>
</section>
""")

    index_html = page(
        "Post 001 — The Ship That Never Left the Dock",
        "A steamship capsized while still tied to the dock, killing 844 people in twenty feet of water. Six archival images and the full production record.",
        tpl_index.render(
            post_date="October 21, 2026",
            title="The Ship That Never Left the Dock",
            subtitle="The SS Eastland disaster. Chicago, July 24, 1915. A ship that never left the wharf, and the 844 people who died anyway.",
            score=meta["viral_readiness"]["total"],
        ),
        "home",
    )
    (SITE / "index.html").write_text(index_html, encoding="utf-8")

    # ---------------- post ----------------
    tpl_post = env.from_string("""
<section style="padding-bottom:24px">
  <div class="wrap">
    <p class="eyebrow">Post 001 · {{ date }} · Disasters</p>
    <h1 style="max-width:16ch">The Ship That Never Left the Dock</h1>
    <p class="lede">The SS Eastland, Chicago, July 24, 1915. Six archival frames, in order.</p>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <p class="counter">Carousel · 6 frames · click any image to enlarge</p>
    <div class="carousel">
      {% for c in cards %}
      <figure>
        <img src="assets/images/{{ c.file }}" alt="{{ c.alt }}" data-full="assets/images/{{ c.file }}">
        <figcaption><strong>{{ "%02d"|format(c.n) }}</strong> — {{ c.line }}<br><span style="color:#8a8071">{{ c.credit }}</span></figcaption>
      </figure>
      {% endfor %}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Instagram caption</p>
    <h2>Platform copy</h2>
    <div class="prose">
      {{ instagram|md|safe }}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Facebook caption</p>
    <h2>The same story, told for Facebook</h2>
    <div class="prose">
      {{ facebook|md|safe }}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Accessibility</p>
    <h2>Alt text</h2>
    <div class="prose">
      {{ alt_text|md|safe }}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Package</p>
    <h2>The files and the numbers</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          <tr><td>Status</td><td>{{ status }}</td></tr>
          <tr><td>Images</td><td>6 × 1080×1350 JPEG, sRGB</td></tr>
          <tr><td>Instagram caption</td><td>{{ ig_chars }} characters · 5 hashtags</td></tr>
          <tr><td>Facebook caption</td><td>{{ fb_chars }} characters · 4 hashtags</td></tr>
          <tr><td>Viral Readiness</td><td>{{ score }} / 40 (publish floor 32, flagship 36)</td></tr>
          <tr><td>AI imagery</td><td>None. All six assets are authentic 1904–1915 documents.</td></tr>
          <tr><td>Rights</td><td>Public domain in the United States, or no known restrictions</td></tr>
          <tr><td>Cost</td><td>$0</td></tr>
          <tr><td>Recommended window</td><td>Tue/Wed 12:00–13:00 ET, or Sun 19:00–21:00 ET</td></tr>
        </tbody>
      </table>
    </div>
    <div class="actions">
      <a class="btn" href="process.html">Read the full process</a>
      <a class="btn ghost" href="calendar.html">Next posts</a>
    </div>
  </div>
</section>
""")

    insta = read(POST / "captions" / "instagram.md")
    fbook = read(POST / "captions" / "facebook.md")
    alt_text = read(POST / "captions" / "alt-text.md")

    def body_len(text: str) -> int:
        parts = [p.strip() for p in text.split("\n---\n")]
        for p in parts:
            if not p.startswith("#") and "Character count" not in p and "Target:" not in p and len(p) > 200:
                return len(p)
        return len(max(parts, key=len))

    def caption_display(text: str) -> str:
        """Return only the paste-ready caption plus the first comment, dropping internal notes."""
        text = re.split(r"\n## Notes\b", text)[0]
        parts = [p.strip() for p in text.split("\n---\n")]
        for p in parts:
            if len(p) > 200:
                return p
        return text

    def strip_title(text: str) -> str:
        lines = text.split("\n")
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        return "\n".join(lines).strip()

    alt_clean = strip_title(re.split(r"\n## Notes\b", alt_text)[0])

    post_html = page(
        "Post 001 — The Ship That Never Left the Dock",
        "The finished Eastland post: six archival images, Instagram and Facebook captions, alt text, and the package record.",
        tpl_post.render(
            date="October 21, 2026",
            cards=cards,
            instagram=caption_display(insta),
            facebook=caption_display(fbook),
            alt_text=alt_clean,
            status=meta["status"],
            ig_chars=f"{body_len(insta):,}",
            fb_chars=f"{body_len(fbook):,}",
            score=meta["viral_readiness"]["total"],
        ),
        "post",
    )
    (SITE / "post-001.html").write_text(post_html, encoding="utf-8")

    # ---------------- calendar ----------------
    tpl_cal = env.from_string("""
<section>
  <div class="wrap">
    <p class="eyebrow">Season One</p>
    <h1>Ten posts, one season.</h1>
    <p class="lede">Weekly through January 2027. Post 001 is finished. The rest are researched briefs — angles, sources to verify, and an honest note on what the imagery will support.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Schedule</p>
    <div class="calendar">
      {% for i in posts %}
      <div class="post-row">
        <div class="date"><strong>{{ i.number }}</strong>{{ i.display_date }}<br>{{ i.weekday }}</div>
        <div>
          <h3><a href="#brief-{{ i.number }}" style="text-decoration:none">{{ i.title }}</a></h3>
          <p>{{ i.angle }}</p>
        </div>
        <div class="cat">{{ i.category }}</div>
        <div class="status-cell">
          <span class="status {{ 'ready' if i.status == 'ready' else 'planned' }}">{{ i.status }}</span>
        </div>
      </div>
      {% endfor %}
    </div>
    <p class="small" style="margin-top:22px">Cadence: {{ cadence }}</p>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Briefs</p>
    <h2>What each post is for</h2>
    <p class="lede" style="margin-bottom:40px">A brief is not a script. It is a reason to spend research time, plus the specific questions that research has to answer.</p>
    {% for i in posts %}
    <article class="brief" id="brief-{{ i.number }}">
      <p class="eyebrow" style="margin-bottom:8px">Post {{ i.number }} · {{ i.category }}</p>
      <h3>{{ i.title }}</h3>
      <p class="sub">{{ i.weekday }}, {{ i.display_date }} · provisional score {{ i.provisional_score }}/40 · {{ i.status }}</p>
      <p class="angle">{{ i.angle }}</p>
      <dl>
        <dt>Why it earns a slot</dt><dd>{{ i.why }}</dd>
        <dt>Sources to verify</dt><dd>{{ i.sources|join('; ') }}</dd>
        <dt>Imagery outlook</dt><dd>{{ i.imagery }}</dd>
        <dt>Risks</dt><dd>{{ i.risks }}</dd>
      </dl>
    </article>
    {% endfor %}
    <p class="small">Provisional scores are estimates made before research. Every claim in a brief must pass the same Gate 2 audit that Post 001 did, and any of these can be killed at Gate 1 if the sources do not hold up.</p>
  </div>
</section>
""")

    cal_html = page(
        "Season Calendar — Ten Posts",
        "The Cluefolio editorial calendar: ten researched story briefs through January 2027.",
        tpl_cal.render(posts=calendar["posts"], cadence=calendar["cadence"]),
        "calendar",
    )
    (SITE / "calendar.html").write_text(cal_html, encoding="utf-8")

    # ---------------- agency ----------------
    tpl_doc = env.from_string("""
<section>
  <div class="wrap">
    <p class="eyebrow">{{ kicker }}</p>
    <h1>{{ heading }}</h1>
    <p class="lede">{{ lede }}</p>
  </div>
</section>
<section>
  <div class="wrap prose" style="max-width:860px">
    {{ body|md|safe }}
  </div>
</section>
""")

    agency_html = page(
        "Agency Operating Manual",
        "The Cluefolio charter: eighteen roles, eleven stages, six gates, and the rules that govern the work.",
        tpl_doc.render(
            kicker="The operating manual",
            heading="How the studio works.",
            lede="Eighteen roles, eleven stages, six gates, and one rule that matters more than the rest: nothing moves forward on vibes.",
            body=read(ROOT / "AGENCY.md"),
        ),
        "agency",
    )
    (SITE / "agency.html").write_text(agency_html, encoding="utf-8")

    # ---------------- brand ----------------
    brand_files = [
        ("Voice", "voice.md"),
        ("Visual identity", "visual-identity.md"),
        ("Platform specs", "platform-specs.md"),
        ("Hook rubric", "hook-rubric.md"),
        ("Editorial standards", "editorial-standards.md"),
    ]
    brand_body = "\n\n".join(read(ROOT / "brand" / f) for _, f in brand_files)
    brand_html = page(
        "Brand System",
        "Cluefolio's voice, visual identity, platform specifications, hook rubric, and editorial standards.",
        tpl_doc.render(
            kicker="Brand system",
            heading="Voice, look, and refusals.",
            lede="What we sound like, what we look like, and what we will not publish.",
            body=brand_body,
        ),
        "brand",
    )
    (SITE / "brand.html").write_text(brand_html, encoding="utf-8")

    # ---------------- resources ----------------
    resources_html = page(
        "Resource Register",
        "What tooling Cluefolio tested, adopted, rejected, and could not access — with reasons and costs.",
        tpl_doc.render(
            kicker="Resource register",
            heading="What we tested and what we refused.",
            lede="Four buckets: available, adopted, useful but inaccessible, and investigated then rejected.",
            body=read(ROOT / "resources" / "resource-register.md"),
        ),
        "resources",
    )
    (SITE / "resources.html").write_text(resources_html, encoding="utf-8")

    # ---------------- process ----------------
    docs = [
        ("brief", "Production brief", "00-brief.md"),
        ("candidates", "Candidate scoring (Gate 1)", "01-candidates.md"),
        ("research", "Research", "02-research.md"),
        ("ledger", "Source ledger", "03-source-ledger.md"),
        ("factcheck", "Independent fact-check (Gate 2)", "04-fact-check.md"),
        ("sourcing", "Visual sourcing and rights (Gate 3)", "05-sourcing.md"),
        ("outline", "Narrative outline (Gate 4)", "06-outline.md"),
        ("hooks", "Hook lab", "07-hooks.md"),
        ("visual", "Visual plan", "08-visual-plan.md"),
        ("growth", "Growth packaging", "10-growth.md"),
        ("community", "Community plan", "11-community.md"),
        ("standards", "Standards clearance (Gate 5)", "12-standards.md"),
        ("qa", "QA sign-off (Gate 6)", "13-qa.md"),
        ("postmortem", "Post-mortem (awaiting data)", "14-postmortem.md"),
        ("report", "Final delivery report", "FINAL-REPORT.md"),
    ]

    toc = "".join(f'<a href="#{d[0]}">{d[1]}</a>' for d in docs)
    body_parts = []
    for anchor, title, filename in docs:
        body_parts.append(f'<div class="doc" id="{anchor}">')
        body_parts.append(md_to_html(read(POST / filename)))
        body_parts.append("</div>")

    tpl_process = env.from_string("""
<section>
  <div class="wrap">
    <p class="eyebrow">Post 001 · the working record</p>
    <h1>How this post was made.</h1>
    <p class="lede">Every artifact, in pipeline order — including the two material errors the fact-check caught before writing began.</p>
  </div>
</section>
<section>
  <div class="wrap process-layout">
    <aside class="toc">{{ toc|safe }}</aside>
    <div class="prose">{{ body|safe }}</div>
  </div>
</section>
""")

    process_html = page(
        "Process Record — Post 001",
        "The full production record for the Eastland post: research, source ledger, fact-check, rights, outline, hooks, visuals, growth, standards, and QA.",
        tpl_process.render(toc=toc, body="".join(body_parts)),
        "process",
    )
    (SITE / "process.html").write_text(process_html, encoding="utf-8")

    print(f"Built {len(list(SITE.glob('*.html')))} pages into {SITE.relative_to(ROOT)}")
    for p in sorted(SITE.glob("*.html")):
        print(f"  {p.name}  {p.stat().st_size:,} bytes")


def _first_free_port(start: int, tries: int = 20) -> int:
    import socket

    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port in range {start}-{start + tries - 1}")


def _lan_address() -> str | None:
    """Best-effort local network address, for reaching the site from a phone."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # no packets sent; just picks the default route
            return s.getsockname()[0]
    except Exception:
        return None


def serve(port: int, open_browser: bool = True, lan: bool = False) -> int:
    import http.server
    import socket
    import socketserver
    import threading
    import traceback
    import webbrowser

    class Handler(http.server.SimpleHTTPRequestHandler):
        server_version = "Cluefolio/1.0"
        protocol_version = "HTTP/1.0"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SITE), **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store, max-age=0")
            super().end_headers()

        def list_directory(self, path):
            # No directory listings: send people to the index instead.
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return None

        def log_message(self, fmt, *args):
            sys.stderr.write("  %s\n" % (fmt % args))

    class V6Server(socketserver.ThreadingTCPServer):
        address_family = socket.AF_INET6
        daemon_threads = True
        allow_reuse_address = True

        def server_bind(self):
            # Keep IPv6 and IPv4 listeners independent so both can share the port.
            try:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except OSError:
                pass
            super().server_bind()

    class V4Server(socketserver.ThreadingTCPServer):
        address_family = socket.AF_INET
        daemon_threads = True
        allow_reuse_address = True

    if not (SITE / "index.html").exists():
        print(f"error: {SITE / 'index.html'} is missing. Run the build first.")
        return 1

    try:
        port = _first_free_port(port)
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 1

    # Localhost always. localhost resolves to ::1 as often as 127.0.0.1, so bind both.
    addresses = ["0.0.0.0", "::"] if lan else ["127.0.0.1", "::1"]

    servers = []
    for address in addresses:
        try:
            if ":" in address:
                srv = V6Server((address, port), Handler)
            else:
                srv = V4Server((address, port), Handler)
            servers.append((address, srv))
        except OSError as exc:
            print(f"  note: could not listen on {address}:{port} ({exc.strerror or exc})")

    if not servers:
        print(f"error: could not bind port {port} on any address.")
        print("Another program may be using it. Try: --port 8080")
        return 1

    print(f"\nServing {SITE}")
    print(f"  http://localhost:{port}/")
    print(f"  http://127.0.0.1:{port}/")
    if lan:
        ip = _lan_address()
        if ip:
            print(f"  http://{ip}:{port}/     (other devices on this network)")
        else:
            print("  (could not determine a LAN address)")
        print("\n  Bound to all interfaces. Anything on your network can read these files.")
    print("\n  Press Ctrl+C to stop.\n")

    threads = []
    for address, srv in servers:
        t = threading.Thread(target=srv.serve_forever, name=f"serve-{address}", daemon=True)
        t.start()
        threads.append(t)

    if open_browser:
        try:
            webbrowser.open(f"http://localhost:{port}/")
        except Exception:
            pass

    try:
        while any(t.is_alive() for t in threads):
            threads[0].join(timeout=0.5)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        for _, srv in servers:
            try:
                srv.shutdown()
                srv.server_close()
            except Exception:
                pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Cluefolio static site.")
    ap.add_argument("--serve", action="store_true", help="build, then serve locally")
    ap.add_argument("--port", type=int, default=8000, help="preferred port (default 8000)")
    ap.add_argument("--no-open", action="store_true", help="do not open a browser")
    ap.add_argument(
        "--lan",
        action="store_true",
        help="also accept connections from other devices on your network",
    )
    args = ap.parse_args()

    build()

    if args.serve:
        return serve(args.port, open_browser=not args.no_open, lan=args.lan)
    return 0


if __name__ == "__main__":
    sys.exit(main())


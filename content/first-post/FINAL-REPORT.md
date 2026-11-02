# FINAL REPORT — Cluefolio Studio, Post 001

**Delivered:** 2026-10-19
**Owner:** `agency-lead`
**Status:** READY FOR HUMAN PUBLISHING
**Total cost:** $0

---

## 1. What was built

A complete, self-contained content agency inside this repository, plus one finished,
publication-ready post.

**The agency** — 18 roles defined in `.opencode/agents/`, a 11-stage / 6-gate pipeline in
`AGENCY.md`, a 5-file brand system in `brand/`, 4 reusable templates in `templates/`, and 3
production scripts in `scripts/`.

**The post** — 6 images at 1080×1350, two platform-native captions, alt text for every image, a
source ledger with claim IDs, a rights record, a community plan, and QA reports.

**Every path below exists on disk.** Verified programmatically.

---

## 2. The story and the angle

**Post 001: "The Ship That Never Left the Dock"** — the SS *Eastland* disaster, Chicago,
July 24, 1915. Category: Disasters / Engineering failure.

**Angle:** A steamship capsized while still secured to its dock, killing 844 people in twenty feet
of water, twenty feet from shore — and no one was ever criminally convicted.

**Why this story:** it has an irreducible hook in one sentence, genuine engineering substance
(top-weight, stability, and a well-intentioned safety law that made a known flaw worse), an abundant
free public-domain visual archive, and it is far less known nationally than its scale warrants.

**Why not the others:** Triangle Shirtwaist (too familiar), Halifax (heavily covered), Molasses
Flood (thin visuals), Cocoanut Grove (held for a future post). Full scoring in
`01-candidates.md`.

---

## 3. The deliverable package

```
content/first-post/
  images/01-cover.jpg          1080x1350   381 KB
  images/02-upright.jpg        1080x1350   488 KB
  images/03-the-moment.jpg     1080x1350   496 KB
  images/04-the-hull.jpg       1080x1350   648 KB
  images/05-the-rescue.jpg     1080x1350   476 KB
  images/06-the-wreck.jpg      1080x1350   378 KB
  captions/instagram.md        1,801 chars, 5 hashtags
  captions/facebook.md         2,264 chars, 4 hashtags
  captions/alt-text.md         6 descriptions
  post-metadata.json           machine-readable summary
  assets/manifest.json         7 assets (6 used, 1 documented as rejected)
  render-config.json           crop points and copy
```

**Carousel order:** cover → the ship → the moment → the hull → the rescue → the closing plate.

---

## 4. How it was produced

The pipeline ran in order, and every gate passed:

| Gate | Decision | Decided by |
|---|---|---|
| G1 Greenlight | PASS — Eastland selected at 39/40 | `editorial-director` |
| G2 Factual lock | PASS after two material corrections | `fact-checker` (independent) |
| G3 Rights clearance | PASS — all public domain in the US | `visual-researcher` + `standards-editor` |
| G4 Story approval | PASS — 8-beat outline | `editorial-director` |
| G5 Clearance | CLEARED — no vetoes | `standards-editor` |
| G6 Sign-off | SIGNED OFF — 80/80 checks | `qa-lead` |

Two genuine parallel specialist runs were used: an independent fact-checker and a rights auditor,
each working from its own sources rather than the research notes.

**Revision rounds used:** 2 of a maximum 3.

---

## 5. Verification — what the fact-check caught

This is the most important section of the report, because G2 changed the post.

**Error 1 — a fabricated name.** The draft research named "Paul Steinbrecher" as a defendant whose
extradition was refused. No such person is connected to the case in any source. Removed.

**Error 2 — a false conviction claim.** The draft repeated the widely circulated story that chief
engineer Joseph Erickson was the only person convicted. This conflates a **1933 civil ruling** with
criminal guilt. In fact the defendants were found **not guilty in February 1916**, the court refused
extradition to Illinois, and no criminal trial was ever held in Chicago. Erickson had died in 1919.
Corrected, and the caption now states only what is certain.

**Also corrected:** an unsupported "812" death toll removed; the ship's transfer path to the Navy
corrected; the lifeboat law reframed as *one contributing factor*, not a cause.

**Deliberate omissions:** the *Titanic*/*Lusitania* comparison (true only in a narrow congressional
form that a caption cannot carry honestly) and the crew death count (sources give 2, 3, or 4).
**No direct quotations are used**, because none could be verified word-for-word with a stable
citation.

**Result:** every factual statement in both captions traces to a claim ID in `03-source-ledger.md`.

---

## 6. Rights and imagery

- **All six images are public domain in the United States** or carry a "no known restrictions on
  publication" statement from the holding institution.
- **No AI was used anywhere.** Every image is an authentic 1904–1915 document, so no AI disclosure
  is required.
- **Imagery was verified against catalog records, not filenames.** The rights audit corrected the
  panorama's archive identifiers (the correct ones are LCCN 2007661460 and LC-USZ62-126620), the
  Bain News Service creator credit, the two NARA catalog titles, and the postcard publisher.
- **Dignity:** the body-recovery postcard and the mourning-photograph frame were both sourced and
  deliberately rejected. No image of the dead is used.
- **Rights caveat recorded:** the 1915 postcard and the Satterfield drawing are public domain in the
  US only and may still be protected in life-plus-70 jurisdictions. Acceptable for a US audience and
  US platforms.

---

## 7. Quality assurance

`python scripts/validate_post.py --slug first-post` → **80/80 checks passed, SIGNED OFF.**

Every image was opened at full size and inspected. Six defects were found and fixed during
inspection, including an illegible cover tag, a period photograph carrying an *incorrect date* in
its own handwriting, and an inaccurate statement on the closing plate.

**Viral Readiness Score: 37/40.** Exceeds the 32 publish floor and the 36 flagship bar. The score
measures inputs we control, not a prediction of virality.

---

## 8. Cost and resources

**Total spend: $0.** No paid APIs, no subscriptions, no credits, no purchases. Free models only.

`resources/resource-register.md` records four buckets: what was already available and reusable, what
was verified and adopted (Wikimedia Commons, NARA, LoC, Pillow, numpy), what was useful but
inaccessible (Pollinations now returns HTTP 402; no image API keys; no discrete GPU for local
diffusion), and what was investigated and rejected — including paid generation, AI upscaling of
archival scans, scraping social platforms, and building a database the project does not need.

---

## 9. Known limits and honest caveats

1. **The post is not published.** Nothing was posted, scheduled, or boosted. A human must publish it.
2. **No performance data exists**, so `14-postmortem.md` is deliberately empty rather than estimated.
3. **Pre-1930 dating is the defensible public-domain basis** for the two NARA images, not federal
   authorship — both are fine in the US.
4. **Two images are US-only public domain** and would need review before use in other markets.
5. **Some archival scans are soft or coarse** (the fire-tug postcard; the rescue aerial). They are
   authentic and readable, but they are not high-fidelity photographs.
6. **The Facebook and Instagram captions share one narrative**, as required, but are written
   separately and are not copies of each other.

---

## 10. What to do next

**To publish:** upload `images/01`–`06` in order, paste `captions/instagram.md` and
`captions/facebook.md`, attach the matching alt text from `captions/alt-text.md` to each image, and
put the source list in the Instagram first comment. Recommended window: Tuesday or Wednesday,
12:00–13:00 ET, or Sunday 19:00–21:00 ET.

**To operate the agency for Post 002:** create `content/<slug>/`, write the brief from
`templates/brief.md`, run the pipeline, and do not start writing until G2 passes. The three scripts
and the templates are reusable unchanged.

**Immediate improvements this post proved necessary:**
- Verify every archive identifier against the holding institution. Never write one from memory.
- Decide on a candidate image at sourcing time. Do not carry an unused asset into the manifest
  as an afterthought.

---

HANDOFF
status: PASS
changed: `content/first-post/FINAL-REPORT.md`
open: publishing is a human action; post-mortem awaits real data
next: human publisher

# Visual Plan — The Ship That Never Left the Dock

**Slug:** `first-post`
**Owner:** `art-director`
**Gate:** post-G3, pre-render
**Date:** 2026-10-19

---

## 1. Image count and reason

**Six images.**

The story has a hook, four distinct turns (the known flaw, the law that made it worse, the roll,
the geometry of survival), and a resolution. Six frames let each turn have its own image without
repeating. The story does not need seven or more, and three would flatten the causal chain.

Format: 1080×1350, sRGB, JPEG q92.

---

## 2. Sequence

| # | File | Asset | Purpose — what it adds | Composition | Overlay | Alt ref |
|---|---|---|---|---|---|---|
| 01 | `01-cover.jpg` | `01-capsized-nara` | The hook. The ship already over, the dock right there. | Full bleed; hull diagonal running lower-left to upper-right; headline in the lower third on a scrim | Wordmark, `DISASTERS`, headline, dateline | `01-cover` |
| 02 | `02-upright.jpg` | `02-upright-nara` | Context. What the ship was before the morning. | Full bleed; bow-on, showing the height of the superstructure | Caption line, credit strip | `02-upright` |
| 03 | `03-the-moment.jpg` | `05-satterfield` | The only record of the actual roll. No photograph captures it. | Full bleed; period illustration, high contrast, figures and water | Caption line, credit strip | `03-the-moment` |
| 04 | `04-the-hull.jpg` | `04-firetug-postcard` | Scale. The hull at water level, seen from a boat. | Full bleed, low angle, hull filling the frame | Caption line, credit strip | `04-the-hull` |
| 05 | `05-the-rescue.jpg` | `03-rescue-loc` | Response. Crowds and boats; the human reaction and its size. | Full bleed, elevated view across the river to the crowded bank | Caption line, credit strip | `05-the-rescue` |
| 06 | `06-the-wreck.jpg` | `07-wreck-panorama` | Ending. The river and the city, wide and quiet. | Closing plate: paper ground, full-width photographic band, headline, short close, credit, post rail | `The river kept the evidence.` plus body | `06-the-wreck` |

Every frame adds something the others do not: the consequence, the ship, the moment, the scale, the
response, the aftermath.

---

## 3. Cover lockup

- Wordmark: `CLUEFOLIO` (top left)
- Category tag: `DISASTERS` (top right, on a dark plate for legibility against the sky)
- Headline: **THE SHIP THAT / NEVER LEFT THE DOCK** (Georgia Bold, auto-fit, max two lines)
- Dateline: `Chicago · July 24, 1915` (Georgia Italic)
- Accent rule: rust, 132×4 px, above the dateline

Legibility check: the headline holds at 200 px wide because the type is large, high contrast, and
sits on a gradient scrim rather than raw photograph.

---

## 4. Continuity notes

- One palette, one type system, one credit strip position across all six frames.
- Only image 01 carries the headline lockup. Images 02–05 carry a small `CLUEFOLIO · DISASTERS` tag
  top-left so any single frame is identifiable if screenshotted out of order.
- The closing plate deliberately breaks the full-bleed rule to read as an end card, not a
  seventh photograph. It returns to the paper ground established by the brand.

---

## 5. Rejections

| Asset | Reason |
|---|---|
| `06-mourners` (Chicago Tribune) | Coarse newspaper halftone. At the crop required for 4:5 the print screen is visible and the frame tightens on a grieving woman's face. Fails the quality bar and the dignity standard. |
| Body-recovery postcard | Excluded; never used. |
| Kenosha / righted-ship postcards | Only 475×381 and 478×373. Too small to render. |
| Modern tourist photograph of the site | Modern, low value, CC BY-SA obligation unnecessary. |
| 2013 Coast Guard ceremonial photograph | Not documentary. |
| Frank King cartoon | Commentary, not record. |

---

## 6. Render configuration

Crop focal points, grain amounts, and contrast are set per frame in
`content/first-post/render-config.json`. Rendered with:

```
python scripts/render_post.py --slug first-post
```

Quality rules applied: no upscale beyond 1.6×, no colorization, no generative fill, warm grade only.

---

HANDOFF
status: PASS
changed: `content/first-post/08-visual-plan.md`
open: none
next: `image-producer`

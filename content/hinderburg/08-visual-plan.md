# Visual Plan — The Airship That Fell From the Sky

**Slug:** `hinderburg`
**Owner:** `art-director`
**Gate:** post-G3, pre-render
**Date:** 2026-11-20

--- 

## 1. Image count and reason

**One primary photograph.**

The story has a hook, three distinct turns (the approach, the fire, the collapse), and a resolution. A single primary photograph lets the image do all the work without splitting attention. The caption carries the narrative. The format is 1080×1350, sRGB, JPEG q92.

The primary photograph will be the Sam Shere image: the Hindenburg coming in for a landing, moments before the fire engulfed it.

Format: 1080×1350, sRGB, JPEG q92.

--- 

## 2. Primary photograph

| # | File | Asset | Purpose — what it adds | Composition | Overlay | Alt ref |
|---|---|---|---|---|---|---|
| 01 | `01-cover.jpg` | `hindenburg-cover` | The hook. The Hindenburg coming in for a landing, moments before the fire. | Full bleed; the airship centered in the frame, moving lower-left to upper-right; headline in the lower third on a scrim | None; the image is strong on its own | `01-cover` |

Every frame adds something the others do not: the image carries the entire visual weight. The caption carries the narrative.

--- 

## 3. Cover lockup

- Wordmark: `CLUEFOLIO` (top left)
- Category tag: `DISASTERS` (top right, on a dark plate for legibility against the sky)
- Headline: **THE AIRSHIP / FELL FROM THE SKY** (Georgia Bold, auto-fit, max two lines)
- Dateline: `Lakehurst, New Jersey · May 6, 1915` → corrected to `Lakehurst, New Jersey · May 6, 1937` (Georgia Italic)
- Accent rule: rust, 132×4 px, above the dateline

Legibility check: the headline holds at 200 px wide because the type is large, high contrast, and sits on a gradient scrim rather than raw photograph.

--- 

## 4. Continuity notes

- One palette, one type system, one credit strip position across the single frame.
- The on-image text (the cover headline) is included in the caption, so it is not repeated in the alt text.
- The image is the sole visual element. No additional panels, collages, or supplementary images.

--- 

## 5. Render configuration

Crop focal points, grain amounts, and contrast are set per frame in
`content/hinderburg/render-config.json`. Rendered with:

```
python scripts/render_post.py --slug hinderburg
```

Quality rules applied: no upscale beyond 1.6×, no colorization, warm grade only.

--- 

HANDOFF
status: PASS
changed: `content/hinderburg/08-visual-plan.md`
open: none
next: `image-producer`
# Cluefolio Visual Identity

## The idea

An archival research desk, not a tabloid. Warm paper, dark ink, restrained type, and photographs
that are allowed to be photographs.

The grid should be recognizable before anyone reads the wordmark.

## Canvas

- **Primary:** 1080 × 1350 (4:5 portrait) — Instagram and Facebook feed.
- **Secondary:** 1080 × 1080 (1:1) — only if a platform crop demands it.
- **Story/Reel cover:** 1080 × 1920 — future use, not part of Post 001.
- **Color profile:** sRGB. **Format:** JPEG, quality 92, progressive.
- **Max file size:** 8 MB per image (Instagram feed limit is generous; stay well under).

## Palette

| Role | Hex | Use |
|---|---|---|
| Paper | `#F4EFE6` | Background, caption panels |
| Ink | `#15130F` | Headlines, body text |
| Muted ink | `#5B5348` | Secondary text, credits |
| Rule | `#B9AE9C` | Hairlines, dividers |
| Accent | `#8C2F1E` | Category tag, key numerals |
| Deep shadow | `#0B0A08` | Vignette, overlay scrim |

Never use pure white `#FFFFFF` for type on paper. Never use pure black `#000000` for text.

## Typography

- **Display:** Georgia Bold — headlines, numerals.
- **Secondary display:** Georgia Italic — pull quotes, datelines.
- **Text:** Segoe UI — captions, credits, labels.
- **Labels:** Segoe UI Semibold, letter-spaced 0.14em, uppercase, 22–26 px.

Rules:
- Headline max 2 lines on the cover, max 3 on interior.
- Never stretch or condense type. Never outline it.
- Minimum body size on-image: 28 px at 1080 wide.
- Minimum credit size: 20 px.

## Cover lockup (image 01)

Fixed positions, identical on every post:

```
┌──────────────────────────────┐
│  CLUEFOLIO        [CATEGORY] │  ← top rail, 72 px from edges
│                              │
│                              │
│         [photograph]         │
│                              │
│                              │
│  THE SHIP THAT               │  ← headline, Georgia Bold
│  NEVER LEFT THE DOCK         │
│  ────────────────            │  ← 3 px accent rule
│  Chicago, July 24, 1915      │  ← dateline, Georgia Italic
└──────────────────────────────┘
```

- Top rail: wordmark left, category tag right, both in muted ink.
- Headline sits in the lower third, on a soft gradient scrim for legibility.
- Accent rule is 120 px wide, 3 px tall.
- Never place the headline over a busy area without a scrim.

## Interior pages (02–06)

- Full-bleed photograph, slight warm grade, subtle grain.
- A 40 px paper-colored margin is **not** used; images bleed to the edge.
- A bottom credit strip: 96 px tall, paper background, 90% opacity, muted ink text.
- Optional short caption line above the credit strip (max 90 characters) in Georgia Italic.
- Page number bottom-right in Segoe UI, muted ink.

## Image treatment

- **Grade:** warm highlights, slightly lifted blacks, desaturated by 8–12%. Never crush detail.
- **Grain:** subtle, 2–4% opacity. Enough to unify scans of different quality.
- **Sharpening:** light unsharp mask after resize. Never over-sharpen archival scans.
- **Cropping:** crop for composition, never to distort. Never upscale beyond 1.6× original.
- **No fake colorization.** If an image is black and white, it stays black and white.
- **No AI fills, no generative expand, no invented detail.**

## Consistency across a carousel

- Same palette, same type, same credit strip position on every image.
- Image 1 is the only one with the headline lockup.
- Images 2–6 carry a small category tag in the top-left so a screenshot is still identifiable.

## Alt text

Every image gets alt text written for a screen-reader user, not for SEO. Describe what is visible
and what it shows, in one to three sentences. Do not begin with "Image of."

Example:
> A long passenger steamship lies completely on its side in a narrow city river, its hull exposed
> above the waterline. Small boats cluster alongside, and a few figures stand on the upturned hull.

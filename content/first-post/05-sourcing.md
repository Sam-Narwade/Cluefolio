# Visual Sourcing — The Ship That Never Left the Dock

**Slug:** `first-post`
**Owner:** `visual-researcher`
**Gate:** G3 — Rights clearance (pending `standards-editor`)
**Date:** 2026-10-19

---

## 1. Search strategy

We searched Wikimedia Commons, the Library of Congress, the National Archives catalog, and the
Newberry Library's Chicago collections for the *Eastland*.

We filtered for:
- Authentic period material (1915), not later tourist or modern photographs.
- Public-domain or no-known-restrictions status, recorded per item.
- Sufficient resolution to hold 1080 px wide without exceeding a 1.6× upscale.
- Dignity: no corpse, morgue, or body-recovery imagery.

A note on rate limits: the Commons API returns HTTP 429 under rapid automated requests. We used a
descriptive user agent, sequential requests with delays, and a local cache. NARA and the Library of
Congress were queried separately.

---

## 2. Adopted assets

| ID | Title | Archive | License | Role |
|---|---|---|---|---|
| `01-capsized-nara` | Photographic Exhibits of The Eastland (NAID 281841) | U.S. National Archives | Unrestricted / PD-US | Cover |
| `02-upright-nara` | Panoramic Photograph of The Eastland (NAID 281840) | U.S. National Archives | Unrestricted / PD-US | Before |
| `05-satterfield` | Capsizing of the SS Eastland, as witnessed by Satterfield | *The Tacoma Times*, July 27, 1915 | PD-US (pre-1931) | The moment |
| `04-firetug-postcard` | View of the Eastland taken from a fire tug | Max Rigot Selling Co., Chicago, 1915 | PD-US (pre-1931) | Scale |
| `03-rescue-loc` | Eastland disaster: rescue operations | LoC, Bain Collection, LCCN 2017658559, LC-USZ62-30114 | No known restrictions | Response |
| `07-wreck-panorama` | The wreck of the Eastland | LoC, LCCN 2007661460, LC-USZ62-126620, pan.6a04191 | No known restrictions | Closing plate |

Full metadata, credit lines, and alt text are in `assets/manifest.json`.

### Credit corrections applied after independent rights verification

- The panorama's archive identifier was initially recorded incorrectly. The correct identifiers are
  LCCN 2007661460, call number PAN US GEOG – Illinois no. 34, reproduction number LC-USZ62-126620.
- The rescue photograph is credited to the Bain News Service, not to the collection; the collection
  is named for George Grantham Bain.
- The two NARA items are catalogued as "Photographic Exhibits of The Eastland" and "Panoramic
  Photograph of The Eastland." The Commons filenames carry older captions, not the NARA titles.
- The fire-tug postcard's publisher is the Max Rigot Selling Company, Chicago.

### Rights caveat recorded

The two NARA items are tagged PD-USGov on Commons, but they were made by commercial photographers
and the defensible public-domain basis is pre-1930 publication, not federal authorship. Under either
basis they are free to reproduce in the United States. The 1915 postcard and the Satterfield drawing
are public domain in the United States only; both could still be protected in life-plus-70
jurisdictions. That is acceptable because our audience and platforms are US-based, and it is noted
here for the record.

---

## 3. Rejected assets

| Asset | Reason |
|---|---|
| `06-mourners` — Chicago Tribune photographs of mourners | Considered and dropped. The source is a coarse newspaper halftone; at the crop required for 4:5 it shows the print screen badly and frames a grieving woman too tightly. It fails the quality bar and risks being exploitative. The human cost is carried by the caption and by the rescue frame. |
| Eastland Postcard — "Recovering bodies from the hull" | Excluded on dignity grounds. Body-recovery imagery is never used. |
| `EastlandKenosha.jpg` | Only 475×381. Far too small for 1080 px. |
| "Eastland being righted" (port side) | Only 478×373. Too small. |
| CC BY-SA tourist photograph of the site | Modern, low value, and a share-alike obligation we do not need. |
| 2013 U.S. Coast Guard ceremonial photograph | Modern and non-documentary. |
| "Eastland disaster through the eyes of Frank King" | A cartoon commentary, not a documentary record. |
| Chicago Tribune front page scans | Text-dense and unreadable at 1080 px wide. |

---

## 4. Gaps and AI-reconstruction decision

The one moment no photograph captures is the capsizing itself — all surviving photographs are
after the ship was already over. The 1915 eyewitness newspaper illustration (Satterfield) fills that
gap with authentic period material.

**No AI reconstruction is required for this post, and none was used.** Every image is an authentic
1915 document. Therefore **no AI disclosure is needed** in the captions.

---

## 5. Verification notes

- Each image was opened and inspected at full size before adoption.
- The rescue photograph carries period handwriting across the top that includes an incorrect date
  ("1-24-15"). The final crop removes it so the image cannot be misread.
- The panorama carries a period caption and a photography-studio stamp. It is published in the
  United States in 1915 and is in the public domain.
- We do not upscale any source beyond 1.6×, and we never colorize.

---

HANDOFF
status: PASS
changed: `content/first-post/05-sourcing.md`, `content/first-post/assets/manifest.json`
open: final rights sign-off at G3
next: `standards-editor`, `art-director`

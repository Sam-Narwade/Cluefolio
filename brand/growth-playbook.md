# Cluefolio Growth Playbook

Image-first growth for @cluefolio (Instagram) and the Cluefolio Facebook Page.
Written to be executed by the automation pipeline, not admired.

---

## 1. Reality check

| Target | Honest assessment |
|---|---|
| 1,000,000 followers | Not achievable in 30 days. Requires crossover or paid amplification. |
| 100,000 followers | 12–24 months of consistent carousels plus 2–3 breakout posts. |
| 5,000 followers in 90 days | Achievable with 5 posts/week, strong covers, and a save-driven format. |
| 1,000 followers in 30 days | Achievable if two or three posts break out of the follow graph. |

Anyone promising 1M in a month is selling bots. Bought followers suppress reach:
the ratio of engaged to total followers is a distribution input, so a padded
audience makes every subsequent post perform worse.

## 2. Positioning

Not "history facts". That space is saturated with text-on-color garbage.

**Cluefolio is the account that makes you say "how did I never know this?" and
then shows you the photograph.**

Three commitments, applied to every post:

1. **One impossible fact in the first line.** No setup, no throat-clearing.
2. **Authentic imagery only.** The archive is the differentiator. No AI covers.
3. **A receipt.** Sources in the first comment, every time. This is the trust
   asset that makes saves and shares safe.

## 3. Format: the 7-slide carousel

Single images are the weakest format on the platform. Every post is a carousel.

| Slide | Job | Content |
|---|---|---|
| 1 | Stop the scroll | Best archival photo, headline ≤ 6 words, one number max |
| 2 | Establish stakes | Who, where, when — one sentence, big type |
| 3 | The mechanism | Why it happened. Diagram, map, or photo with a 2-line caption |
| 4 | The turn | The moment it became unavoidable |
| 5 | Human cost | Names, ages, families. Dignity rules apply — no victim imagery |
| 6 | The consequence | What changed in law, engineering, or safety |
| 7 | The hook home | Payoff line + "Save this" / "Follow for the next one" |

Rules:

- Slide 1 carries the entire post. If the cover does not work as a standalone
  image, the post fails regardless of the other six.
- Text on the cover: ≤ 6 words, one accent word, no paragraph.
- No slide is a wall of text. One idea per slide, ≤ 22 words.
- Slide 7 must give a reason to save: a list, a timeline, a "what changed", or
  a question worth arguing about in the comments.

## 4. Discovery and SEO

Instagram search is a real surface now, and the caption feeds it.

- **Keyword in the first 125 characters.** "The Eastland disaster" not "this
  forgotten tragedy".
- **Keywords in the alt text**, written as description, not keyword soup.
- **Keywords as on-image text** on slide 1 — the OCR pass reads it.
- **3–5 hashtags, not 30.** Two niche (`#EastlandDisaster`, `#ChicagoHistory`),
  one topic (`#MaritimeHistory`), one broad (`#HistoryFacts`). More dilutes.
- **Location tag** on every post. Free local discovery, and history is
  inherently place-bound.
- **Caption length:** 150–250 words. Long enough to satisfy a read, short enough
  to finish.

## 5. Cadence and timing

Five posts per week. Six is better. Fewer than three is invisible.

| Slot | ET | Rationale |
|---|---|---|
| Primary | 11:30 | Lunch scroll, US East |
| Secondary | 19:30 | Evening scroll, US East + Europe waking |

Current workflow runs Wednesday only. It must move to **daily** so the calendar
is the single source of truth and any ready post publishes on its date.

## 6. Community

- Reply to every comment within the first 60 minutes. Comment velocity in the
  first hour is a ranking input.
- Every caption ends with a question that has a real answer, not "what do you
  think?".
- Pin the source comment. It is the account's credibility marker.
- Never argue with a correction. Thank, verify, and post a correction in the
  same thread.

## 7. Measurement

Weekly, from the Graph API, per post:

| Metric | Kill threshold | Scale threshold |
|---|---|---|
| Reach | < 1.5x follower count | > 5x follower count |
| Saves | < 1% of reach | > 3% of reach |
| Shares | < 0.3% of reach | > 1.5% of reach |
| Follows per post | < 0.05% of reach | > 0.5% of reach |

Kill rule: a format that misses twice in a row is retired for a month.
Scale rule: a post that beats the scale threshold gets its structure cloned —
same slide count, same hook shape, new story.

## 8. Guardrails

Never, at any volume:

- Bought followers, engagement pods, follow/unfollow automation, mass DMs.
- Auto-commenting on strangers' posts.
- Multi-account operations to evade limits.
- Posting a pack that is not marked `ready` in the dashboard.

These are the exact behaviours that get accounts actioned, and the reach loss
from a single enforcement event is larger than any growth they produce.

## 9. The 30-day plan

| Week | Output | Focus |
|---|---|---|
| 1 | 5 posts, 7 slides each | Cover quality. Test three headline shapes. |
| 2 | 5 posts | Slide-7 save mechanics. Timeline and "what changed" plates. |
| 3 | 5 posts | Keyword and alt-text discipline. Measure search reach. |
| 4 | 5 posts | Clone the best performer's structure twice. |

Twenty posts. At five per week, that is one month of autonomous publishing,
with a weekly approval click on the `production` gate.

## 10. Content spec

Every pack pushed to `content/<slug>/` must contain:

- `post-metadata.json` with `status: "ready"` only when the pack is publishable.
- `images/` with **7 finished slides**, named `01-cover.jpg` … `07-close.jpg`.
- Caption with the keyword inside the first 125 characters.
- Alt text describing each slide for screen readers.
- Source ledger referenced by the pinned comment.
- No AI-generated imagery. If unavoidable, the disclosure field must be set and
  the image must carry the label.

#!/usr/bin/env python3
"""Build the dashboard data file from the curated post packs.

Usage:
    python scripts/build_dashboard_data.py

Writes:
    content/dashboard.json   full dashboard payload
    content/calendar.json    compatibility calendar for the static site
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard_content import PLAYBOOK, POSTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

PIPELINE_STAGES = [
    {"id": "brief", "label": "Brief", "owner": "agency-lead / editorial-director"},
    {"id": "research", "label": "Research", "owner": "research-journalist"},
    {"id": "factcheck", "label": "Fact-check", "owner": "fact-checker"},
    {"id": "visuals", "label": "Visuals", "owner": "visual-researcher / art-director"},
    {"id": "story", "label": "Story + hooks", "owner": "story-editor / hook-doctor"},
    {"id": "render", "label": "Render", "owner": "image-producer"},
    {"id": "copy", "label": "Copy", "owner": "social-copywriter"},
    {"id": "growth", "label": "Growth", "owner": "growth-strategist"},
    {"id": "standards", "label": "Standards", "owner": "standards-editor"},
    {"id": "qa", "label": "QA", "owner": "qa-lead"},
    {"id": "publish", "label": "Ready", "owner": "human publisher"},
]

BRIEFS = {
    "first-post": {
        "why": "The strongest single story in the slate: an impossible fact in one sentence, real engineering substance, and an abundant free visual archive.",
        "imagery": "Excellent. Six authentic public-domain frames; renderer complete.",
        "risks": "None outstanding. Two common false claims were removed at Gate 2.",
    },
    "hinderburg": {
        "why": "An iconic public-domain photograph, a hook that fits in one sentence, and a cause that is still genuinely unresolved.",
        "imagery": "Excellent. Authentic 1937 photograph of the airship in flames.",
        "risks": "Death toll must distinguish 35 on board from 36 total. Cause must stay qualified.",
    },
    "peshtigo-fire": {
        "why": "The Chicago comparison is a built-in hook and a genuine historical injustice. The purest 'I never knew this' story on the slate.",
        "imagery": "Weak. Surviving photographs are scarce and low-resolution. Consider a second visual pass or a text-forward plate.",
        "risks": "Death toll is an estimate and ranges widely. Must be presented as an estimate, never a precise figure.",
    },
    "johnstown-flood": {
        "why": "Class, negligence, and documented warnings ignored. The clearest accountability story available, and the imagery is strong.",
        "imagery": "Strong. Widely held period photographs, public domain.",
        "risks": "The club's responsibility is documented but the legal outcome needs precision. Avoid a simple morality play.",
    },
    "iroquois-theatre": {
        "why": "A direct safety-failure story with a physical mechanism a reader can picture, and Chicago continuity with Post 001.",
        "imagery": "Strong. Period photographs, postcards, and architectural images.",
        "risks": "Graphic subject. No imagery of victims. Verify each specific exit failure before naming it.",
    },
    "monongah-mine": {
        "why": "Labor history with a concrete policy consequence, and a death toll that is still argued over.",
        "imagery": "Moderate. Period photographs exist but are low-resolution or graphic. Cover is a disclosed reconstruction.",
        "risks": "Death toll varies from 362 to over 500. Child labor is central and needs care. Dignity review required.",
    },
    "halifax-explosion": {
        "why": "Enormous scale, a clear chain of events, a strong human-response beat, and a warm US-Canada payoff.",
        "imagery": "Strong. Period photographs are public domain in Canada and the US.",
        "risks": "Non-US story; needs a clear reason for a US audience. Verify the death toll and the Turtle Grove story.",
    },
    "molasses-flood": {
        "why": "The hook is irresistible and the underlying failure, a tank built too thin and never properly tested, is genuinely instructive.",
        "imagery": "Strong. Period photographs widely held.",
        "risks": "Tone is the whole risk. It reads as trivia if handled lightly. Verify the claimed wave speed and the toll.",
    },
    "radium-girls": {
        "why": "Human, scientific, and legally consequential. It broadens the season beyond disasters into science and labor.",
        "imagery": "Moderate. The factory photograph is authentic but soft. Portraits are limited and rights vary.",
        "risks": "Portrait rights need per-item verification. Avoid lurid medical detail. Verify names, dates, and legal outcomes.",
    },
    "cocoanut-grove": {
        "why": "Held from the Post 001 shortlist. A double payoff: the disaster and the medical legacy that came out of it.",
        "imagery": "Weak for rights. The best period photographs are still in copyright. Cover is a disclosed reconstruction.",
        "risks": "Graphic subject; no victim imagery. Verify the toll and the specific medical claims, which are often overstated.",
    },
    "hartford-circus-fire": {
        "why": "Devastating and largely forgotten, with a clear materials-failure mechanism and a direct line to modern flame-retardant rules.",
        "imagery": "Strong. The period photograph is public domain and visually powerful.",
        "risks": "The highest emotional content on the slate, involving children. Dignity review is mandatory. Verify the tent treatment claim.",
    },
}


def enrich(post: dict) -> dict:
    p = dict(post)
    p["ig_chars"] = len(p["captions"]["instagram"])
    p["fb_chars"] = len(p["captions"]["facebook"])
    p["ig_tags"] = len(p["hashtags"]["instagram"])
    p["fb_tags"] = len(p["hashtags"]["facebook"])
    p["keyword_count"] = 1 + len(p["keywords"]["secondary"]) + len(p["keywords"]["long_tail"])
    p["story_words"] = len(" ".join(p["story"]).split())
    p["gates_passed"] = sum(1 for v in p["pipeline"]["gates"].values() if v == "PASS")
    p["gates_total"] = len(p["pipeline"]["gates"])
    return p


def build() -> dict:
    posts = [enrich(p) for p in POSTS]
    posts.sort(key=lambda p: p["number"])

    total_images = sum(p["image_count"] for p in posts)
    total_words = sum(p["story_words"] for p in posts)
    ready = [p for p in posts if p["status"] == "ready"]
    drafts = [p for p in posts if p["status"] != "ready"]
    avg_score = round(statistics.mean(p["viral_readiness"]["total"] for p in posts), 1)

    calendar_posts = []
    for p in posts:
        b = BRIEFS.get(p["slug"], {})
        calendar_posts.append({
            "number": p["number"],
            "slug": p["slug"],
            "title": p["title"],
            "category": p["category"],
            "date": p["date"],
            "display_date": p["display_date"],
            "weekday": p["weekday"],
            "status": p["status"],
            "angle": p["angle"],
            "why": b.get("why", p["angle"]),
            "sources": p["sources"],
            "imagery": b.get("imagery", ""),
            "risks": b.get("risks", p["review_notes"]),
            "provisional_score": p["viral_readiness"]["total"],
        })

    dashboard = {
        "meta": {
            "studio": "Cluefolio Studio",
            "season": "Season One - American Disasters & Engineering Failures",
            "generated": "2026-11-02",
            "cadence": "Weekly on Wednesdays, 12:00-13:00 ET. Holiday pause Dec 23 and Dec 30.",
            "total_posts": len(posts),
            "ready": len(ready),
            "draft": len(drafts),
            "total_images": total_images,
            "total_story_words": total_words,
            "avg_viral_score": avg_score,
            "ready_numbers": [p["number"] for p in ready],
            "next_post": ready[1]["number"] if len(ready) > 1 else (drafts[0]["number"] if drafts else ""),
        },
        "posts": posts,
        "calendar": {
            "season": "Season One - American Disasters & Engineering Failures",
            "note": "Eleven posts through January 2027. Posts 001-002 are ready. Posts 003-011 are drafts until Gate 2.",
            "cadence": "Weekly on Wednesdays, 12:00-13:00 ET. Dec 23 and Dec 30 skipped for the holidays.",
            "posts": calendar_posts,
        },
        "pipeline_stages": PIPELINE_STAGES,
        "playbook": PLAYBOOK,
    }
    return dashboard


def main() -> int:
    dashboard = build()
    out = ROOT / "content" / "dashboard.json"
    out.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} bytes)")
    print(f"  posts: {dashboard['meta']['total_posts']}")
    print(f"  ready: {dashboard['meta']['ready']}  draft: {dashboard['meta']['draft']}")
    print(f"  images: {dashboard['meta']['total_images']}")
    print(f"  avg viral score: {dashboard['meta']['avg_viral_score']}")

    cal_out = ROOT / "content" / "calendar.json"
    cal_out.write_text(
        json.dumps(dashboard["calendar"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {cal_out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

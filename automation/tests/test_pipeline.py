from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.content import (
    build_plan,
    find_post,
    load_dashboard,
    public_image_url,
    select_due,
    validate_plan,
)
from automation.publish import main as publish_main
from automation.publisher import publish_facebook, publish_instagram


class FakeGraph:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.items = 0
        self.photos = 0

    def post(self, path: str, params: dict | None = None) -> dict:
        payload = dict(params or {})
        self.calls.append(("POST", path, payload))
        if path.endswith("/media"):
            if payload.get("media_type") == "CAROUSEL":
                return {"id": "carousel-container"}
            if payload.get("is_carousel_item") == "true":
                self.items += 1
                return {"id": f"item-{self.items}"}
            return {"id": "container"}
        if path.endswith("/media_publish"):
            return {"id": "media-1"}
        if path.endswith("/photos"):
            self.photos += 1
            return {"id": f"photo-{self.photos}"}
        if path.endswith("/feed"):
            return {"id": "post-1"}
        if path.endswith("/comments"):
            return {"id": "comment-1"}
        return {"id": "ok"}

    def get(self, path: str, params: dict | None = None) -> dict:
        return {"permalink": "https://example.com/p"}


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_dashboard()
        cls.post = find_post(cls.data, "001")
        cls.base = "https://example.github.io/Cluefolio"

    def test_find_post_by_number_and_slug(self) -> None:
        self.assertEqual(find_post(self.data, "001")["title"], self.post["title"])
        self.assertEqual(find_post(self.data, "first-post")["number"], "001")
        self.assertIsNone(find_post(self.data, "999"))

    def test_select_due(self) -> None:
        posts = [
            {"number": "001", "date": "2026-10-21", "status": "ready"},
            {"number": "002", "date": "2026-10-28", "status": "ready"},
            {"number": "003", "date": "2026-11-04", "status": "draft"},
        ]
        self.assertEqual(select_due(posts, "2026-10-28")["number"], "002")
        self.assertIsNone(select_due(posts, "2026-11-01"))
        self.assertIsNone(select_due(posts, "2026-11-04"))

    def test_public_url(self) -> None:
        self.assertEqual(
            public_image_url("https://u.github.io/repo/", "first-post", "01-cover.jpg"),
            "https://u.github.io/repo/content/first-post/images/01-cover.jpg",
        )

    def test_plan_is_carousel_with_six_images(self) -> None:
        plan = build_plan(self.post, self.base)
        self.assertEqual(plan["format"], "carousel")
        self.assertEqual(len(plan["images"]), 6)
        self.assertTrue(plan["images"][0]["url"].startswith("https://example.github.io/"))
        self.assertEqual(plan["ig_chars"], 1774)

    def test_validation_passes_for_shipped_post(self) -> None:
        plan = build_plan(self.post, self.base)
        errors, warnings = validate_plan(self.post, plan)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_validation_rejects_placeholder_host(self) -> None:
        plan = build_plan(self.post, "https://YOURUSER.github.io/Cluefolio")
        errors, _ = validate_plan(self.post, plan)
        self.assertTrue(any("placeholder" in e for e in errors))

    def test_instagram_carousel_payload(self) -> None:
        graph = FakeGraph()
        plan = build_plan(self.post, self.base)
        result = publish_instagram(graph, "ig-1", plan)

        self.assertEqual(result["media_id"], "media-1")
        media_calls = [c for c in graph.calls if c[1].endswith("/media")]
        item_calls = [c for c in media_calls if c[2].get("is_carousel_item") == "true"]
        parent_calls = [c for c in media_calls if c[2].get("media_type") == "CAROUSEL"]
        self.assertEqual(len(item_calls), 6)
        self.assertEqual(len(parent_calls), 1)
        self.assertEqual(parent_calls[0][2]["children"], "item-1,item-2,item-3,item-4,item-5,item-6")
        self.assertIn("Eastland", parent_calls[0][2]["caption"])

    def test_facebook_carousel_payload(self) -> None:
        graph = FakeGraph()
        plan = build_plan(self.post, self.base)
        result = publish_facebook(graph, "page-1", plan)

        self.assertEqual(result["post_id"], "post-1")
        photo_calls = [c for c in graph.calls if c[1].endswith("/photos")]
        feed_calls = [c for c in graph.calls if c[1].endswith("/feed")]
        self.assertEqual(len(photo_calls), 6)
        self.assertEqual(len(feed_calls), 1)
        attached = json.loads(feed_calls[0][2]["attached_media"])
        self.assertEqual(len(attached), 6)
        self.assertEqual(attached[0], {"media_fbid": "photo-1"})

    def test_single_image_post(self) -> None:
        post = find_post(self.data, "002")
        plan = build_plan(post, self.base)
        self.assertEqual(plan["format"], "single")

        graph = FakeGraph()
        publish_instagram(graph, "ig-1", plan)
        self.assertEqual(sum(1 for c in graph.calls if c[1].endswith("/media")), 1)
        self.assertEqual(sum(1 for c in graph.calls if c[1].endswith("/media_publish")), 1)


class PublishCliTests(unittest.TestCase):
    ENV = {
        "META_PAGE_ID": "page-1",
        "META_IG_USER_ID": "ig-1",
        "META_PAGE_ACCESS_TOKEN": "test-token",
        "PUBLIC_BASE_URL": "https://example.github.io/Cluefolio",
        "META_GRAPH_VERSION": "v23.0",
    }

    def test_full_publish_writes_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "published.json"
            report = Path(temp) / "last-run.json"
            with patch.dict(os.environ, self.ENV, clear=False), \
                 patch("automation.publish.GraphClient", return_value=FakeGraph()):
                code = publish_main([
                    "--post", "002",
                    "--ledger", str(ledger),
                    "--report", str(report),
                    "--no-notify",
                ])

            self.assertEqual(code, 0)
            data = json.loads(ledger.read_text(encoding="utf-8"))
            entry = data["published"]["002"]
            self.assertEqual(entry["status"], "published")
            self.assertEqual(entry["instagram"]["media_id"], "media-1")
            self.assertEqual(entry["facebook"]["post_id"], "post-1")
            self.assertEqual(entry["first_comment"]["instagram"]["comment_id"], "comment-1")
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["ok"], True)

    def test_partial_run_resumes_at_facebook(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "published.json"
            report = Path(temp) / "last-run.json"
            ledger.write_text(json.dumps({
                "version": 1,
                "published": {
                    "002": {
                        "number": "002",
                        "status": "partial",
                        "instagram": {"media_id": "media-existing", "permalink": None},
                    },
                },
            }), encoding="utf-8")

            graph = FakeGraph()
            with patch.dict(os.environ, self.ENV, clear=False), \
                 patch("automation.publish.GraphClient", return_value=graph):
                code = publish_main([
                    "--post", "002",
                    "--ledger", str(ledger),
                    "--report", str(report),
                    "--no-notify",
                ])

            self.assertEqual(code, 0)
            self.assertFalse(any(c[1].endswith("/media") for c in graph.calls))
            self.assertTrue(any(c[1].endswith("/feed") for c in graph.calls))
            entry = json.loads(ledger.read_text(encoding="utf-8"))["published"]["002"]
            self.assertEqual(entry["instagram"]["media_id"], "media-existing")
            self.assertEqual(entry["status"], "published")


if __name__ == "__main__":
    unittest.main()

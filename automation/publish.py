"""Publish an approved Cluefolio post to Instagram and Facebook.

Examples:
    python -m automation.publish --post 001 --dry-run
    python -m automation.publish --due
    python -m automation.publish --post 002 --force

The default mode publishes the post whose date matches today in America/New_York.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ledger as ledger_store
from . import notify
from .config import DEFAULT_LEDGER, DEFAULT_REPORT, ConfigError, Settings, load_dotenv
from .content import build_plan, find_post, load_dashboard, select_due, today_et, validate_plan
from .graph import GraphClient, GraphError
from .publisher import publish_comment, publish_facebook, publish_instagram


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.no_dotenv:
        load_dotenv()

    try:
        settings = Settings.from_env(require_credentials=not args.dry_run)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    base_url = (args.base_url or settings.public_base_url).rstrip("/")
    try:
        dashboard = load_dashboard()
    except Exception as exc:  # noqa: BLE001
        print(f"Could not load dashboard data: {exc}")
        return 2

    post, reason = _select_post(dashboard, args)
    if not post:
        print(reason)
        return 0

    ledger_path = Path(args.ledger)
    report_path = Path(args.report)
    ledger = ledger_store.load(ledger_path)

    if ledger_store.is_published(ledger, post["number"]) and not args.force:
        print(f"Post {post['number']} is already published according to {ledger_path}. Use --force to override.")
        return 0

    plan = build_plan(post, base_url)
    errors, warnings = validate_plan(post, plan)
    report = {
        "post": post["number"],
        "title": post["title"],
        "date": post["date"],
        "dry_run": bool(args.dry_run),
        "base_url": base_url,
        "plan": plan,
        "warnings": warnings,
        "errors": errors,
    }

    _print_plan(plan, warnings)
    if errors:
        print("\nPre-flight failed:")
        for error in errors:
            print(f"  - {error}")
        _write_report(report_path, report)
        return 2

    if args.dry_run:
        print("\nDry run complete. No API calls were made.")
        _write_report(report_path, report)
        return 0

    graph = GraphClient(settings.graph_base, settings.token)
    entry = ledger_store.entry_for(ledger, post["number"])
    if args.force:
        entry.clear()
    entry.update({
        "number": post["number"],
        "title": post["title"],
        "date": post["date"],
        "status": "publishing",
        "started_at": ledger_store.now_iso(),
    })
    ledger_store.save(ledger_path, ledger)

    try:
        if not entry.get("instagram"):
            print("  Instagram: creating media container and publishing...")
            entry["instagram"] = publish_instagram(graph, settings.ig_user_id, plan)
            entry["status"] = "partial"
            ledger_store.save(ledger_path, ledger)
            print(f"  Instagram: published {entry['instagram']['media_id']}")

        if not entry.get("facebook"):
            print("  Facebook: uploading photos and publishing...")
            entry["facebook"] = publish_facebook(
                graph, settings.page_id, plan, include_alt=settings.fb_alt_text
            )
            entry["status"] = "partial"
            ledger_store.save(ledger_path, ledger)
            print(f"  Facebook: published {entry['facebook']['post_id']}")

        if plan["first_comment"] and not args.skip_comments and not entry.get("first_comment"):
            print("  First comment: pinning the source ledger...")
            comments = {}
            try:
                comments["instagram"] = publish_comment(
                    graph, entry["instagram"]["media_id"], plan["first_comment"]
                )
            except GraphError as exc:
                comments["instagram_error"] = str(exc)
            try:
                comments["facebook"] = publish_comment(
                    graph, entry["facebook"]["post_id"], plan["first_comment"]
                )
            except GraphError as exc:
                comments["facebook_error"] = str(exc)
            entry["first_comment"] = comments
            if comments.get("instagram_error") or comments.get("facebook_error"):
                entry["comment_warning"] = "One or both first comments failed; pin manually."
        ledger_store.save(ledger_path, ledger)

        entry["status"] = "published"
        entry["published_at"] = ledger_store.now_iso()
        ledger_store.save(ledger_path, ledger)

        report["result"] = entry
        report["ok"] = True
        _write_report(report_path, report)
        _notify(args, f"Published Post {post['number']} - {post['title']}\n"
                      f"Instagram: {entry['instagram'].get('permalink') or entry['instagram']['media_id']}\n"
                      f"Facebook: {entry['facebook'].get('permalink') or entry['facebook']['post_id']}")
        print(f"\nPublished Post {post['number']} - {post['title']}")
        if entry.get("comment_warning"):
            print("  warning: one or both first comments failed; pin manually.")
        return 0

    except Exception as exc:  # noqa: BLE001 - record any failure in the ledger and report
        entry["status"] = "failed"
        entry["error"] = str(exc)
        entry["failed_at"] = ledger_store.now_iso()
        ledger_store.save(ledger_path, ledger)

        report["ok"] = False
        report["error"] = str(exc)
        _write_report(report_path, report)
        _notify(args, f"Publish FAILED for Post {post['number']} - {post['title']}: {exc}")
        print(f"\nPublish failed: {exc}")
        if entry.get("instagram"):
            print("  Instagram already published; a rerun will resume at Facebook.")
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish a Cluefolio post to Instagram and Facebook.")
    parser.add_argument("--post", help="Post number or slug (e.g. 001 or first-post)")
    parser.add_argument("--date", help="Publish the post scheduled for YYYY-MM-DD")
    parser.add_argument("--due", action="store_true", help="Publish the post due today (default)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan; no API calls")
    parser.add_argument("--force", action="store_true", help="Republish even if the ledger says published")
    parser.add_argument("--skip-comments", action="store_true", help="Do not publish the first comment")
    parser.add_argument("--no-notify", action="store_true", help="Skip the Discord notification")
    parser.add_argument("--no-dotenv", action="store_true", help="Do not read the local .env file")
    parser.add_argument("--base-url", help="Override PUBLIC_BASE_URL for the public image host")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="Path to the idempotency ledger")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Path to the last-run JSON report")
    return parser


def _select_post(dashboard: dict, args: argparse.Namespace) -> tuple[dict | None, str]:
    posts = dashboard.get("posts", [])
    if args.post:
        post = find_post(dashboard, args.post)
        if not post:
            return None, f"Post not found: {args.post}"
        return post, ""
    on_date = args.date or today_et()
    post = select_due(posts, on_date)
    if not post:
        return None, f"No post scheduled for {on_date} (America/New_York). Nothing to do."
    return post, ""


def _print_plan(plan: dict, warnings: list[str]) -> None:
    print(f"Post {plan['number']} - {plan['title']}")
    print(f"  Date       : {plan['date']}")
    print(f"  Format     : {plan['format']} ({len(plan['images'])} image{'s' if len(plan['images']) != 1 else ''})")
    print(f"  Instagram  : {plan['ig_chars']:,} characters")
    print(f"  Facebook   : {plan['fb_chars']:,} characters")
    print(f"  First image: {plan['images'][0]['url'] if plan['images'] else 'none'}")
    if warnings:
        print("  Warnings:")
        for warning in warnings:
            print(f"    - {warning}")


def _write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _notify(args: argparse.Namespace, message: str) -> None:
    if not args.no_notify:
        notify.send(message)


if __name__ == "__main__":
    sys.exit(main())

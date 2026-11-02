"""Check Meta credentials, page linkage, and public image hosting."""

from __future__ import annotations

import argparse
import sys
import urllib.request

from .config import ConfigError, Settings, load_dotenv
from .content import build_plan, find_post, load_dashboard
from .graph import GraphClient, GraphError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the Cluefolio publishing setup.")
    parser.add_argument("--post", help="Post number used for the public image check")
    parser.add_argument("--skip-url", action="store_true", help="Skip the public image URL check")
    args = parser.parse_args(argv)

    load_dotenv()
    try:
        settings = Settings.from_env(require_credentials=True)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    graph = GraphClient(settings.graph_base, settings.token)
    try:
        page = graph.get(settings.page_id, {
            "fields": "id,name,instagram_business_account{id,username}",
        })
        print(f"Page       : {page.get('name')} ({page.get('id')})")

        linked = (page.get("instagram_business_account") or {})
        ig_id = settings.ig_user_id or linked.get("id")
        if not ig_id:
            print("Instagram  : no business account linked to this Page")
            return 1
        ig = graph.get(ig_id, {"fields": "id,username,followers_count,media_count"})
        print(f"Instagram  : @{ig.get('username')} ({ig.get('id')})")
        print(f"Audience   : {ig.get('followers_count', 0):,} followers | {ig.get('media_count', 0):,} posts")
        if linked.get("id") and linked.get("id") != settings.ig_user_id:
            print(f"Warning    : META_IG_USER_ID is {settings.ig_user_id}, Page links {linked.get('id')}")
    except GraphError as exc:
        print(f"Meta check failed: {exc}")
        return 1

    if not args.skip_url:
        try:
            dashboard = load_dashboard()
            post = find_post(dashboard, args.post) if args.post else dashboard["posts"][0]
            if not post:
                print(f"Image check: post not found: {args.post}")
                return 1
            plan = build_plan(post, settings.public_base_url)
            url = plan["images"][0]["url"]
            request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "CluefolioDoctor/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                content_type = response.headers.get("Content-Type", "")
                status = response.status
            print(f"Image URL  : {status} {content_type} {url}")
            if status != 200 or not content_type.startswith("image/"):
                print("Image check failed: the public URL must return an image.")
                return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Image check failed: {exc}")
            print("Confirm GitHub Pages is deployed and PUBLIC_BASE_URL points at it.")
            return 1

    print("\nAll checks passed. Dry-run next: python -m automation.publish --post <number> --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

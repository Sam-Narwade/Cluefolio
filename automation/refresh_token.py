"""Exchange a short-lived Meta token for a long-lived Page token.

Run locally, then update the META_PAGE_ACCESS_TOKEN repository secret.
Never commit the output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from .config import ConfigError, Settings, load_dotenv
from .graph import GraphClient, GraphError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh the Meta Page access token.")
    parser.add_argument("--user-token", default=os.getenv("META_USER_TOKEN", ""))
    parser.add_argument("--app-id", default=os.getenv("META_APP_ID", ""))
    parser.add_argument("--app-secret", default=os.getenv("META_APP_SECRET", ""))
    parser.add_argument("--page-id", default=os.getenv("META_PAGE_ID", ""))
    parser.add_argument("--write", type=Path, help="Optional file to write the new tokens to")
    args = parser.parse_args(argv)

    load_dotenv()
    args.user_token = args.user_token or os.getenv("META_USER_TOKEN", "")
    args.app_id = args.app_id or os.getenv("META_APP_ID", "")
    args.app_secret = args.app_secret or os.getenv("META_APP_SECRET", "")
    args.page_id = args.page_id or os.getenv("META_PAGE_ID", "")

    missing = [
        name for name, value in (
            ("user token", args.user_token),
            ("app id", args.app_id),
            ("app secret", args.app_secret),
            ("page id", args.page_id),
        ) if not value
    ]
    if missing:
        print("Missing: " + ", ".join(missing))
        print("Set META_USER_TOKEN, META_APP_ID, META_APP_SECRET, and META_PAGE_ID.")
        return 2

    try:
        settings = Settings.from_env(require_credentials=False)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    try:
        long_lived = _exchange_user_token(
            settings.graph_version, args.app_id, args.app_secret, args.user_token
        )
        graph = GraphClient(settings.graph_base, long_lived)
        page = graph.get(args.page_id, {"fields": "id,name,access_token"})
    except (GraphError, OSError, ValueError) as exc:
        print(f"Token refresh failed: {exc}")
        return 1

    page_token = page.get("access_token")
    if not page_token:
        print("No Page access token returned. Confirm the user manages this Page and granted pages_show_list.")
        return 1

    print(f"Page: {page.get('name')} ({page.get('id')})")
    print("\nLong-lived user token (keep private):")
    print(long_lived)
    print("\nPage access token (set META_PAGE_ACCESS_TOKEN):")
    print(page_token)

    if args.write:
        args.write.write_text(
            "# Generated locally. Do not commit.\n"
            f"META_USER_TOKEN={long_lived}\n"
            f"META_PAGE_ACCESS_TOKEN={page_token}\n",
            encoding="utf-8",
        )
        try:
            args.write.chmod(0o600)
        except OSError:
            pass
        print(f"\nWrote {args.write}. Add it to .gitignore and delete it after updating GitHub Secrets.")
    return 0


def _exchange_user_token(version: str, app_id: str, app_secret: str, user_token: str) -> str:
    query = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": user_token,
    })
    url = f"https://graph.facebook.com/{version}/oauth/access_token?{query}"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", "replace"))
    token = payload.get("access_token")
    if not token:
        raise ValueError(f"No access_token in response: {payload}")
    return token


if __name__ == "__main__":
    sys.exit(main())

"""Optional Discord webhook notifications. Never raises."""

from __future__ import annotations

import json
import os
import urllib.request


def send(message: str) -> None:
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps({"content": message[:1900]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10):
            pass
    except Exception as exc:  # noqa: BLE001 - notifications must never break publishing
        print(f"  warning: Discord notification failed: {exc}")

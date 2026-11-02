"""JSON ledger so a rerun never double-posts."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "published": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ledger is not a JSON object: {path}")
    data.setdefault("version", 1)
    data.setdefault("published", {})
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".ledger-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def entry_for(ledger: dict, number: str) -> dict:
    return ledger.setdefault("published", {}).setdefault(number, {})


def is_published(ledger: dict, number: str) -> bool:
    entry = ledger.get("published", {}).get(number) or {}
    return entry.get("status") == "published"

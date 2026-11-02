"""Configuration and .env loading (standard library only)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "automation" / "state"
DEFAULT_LEDGER = STATE_DIR / "published.json"
DEFAULT_REPORT = STATE_DIR / "last-run.json"


class ConfigError(RuntimeError):
    pass


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env without overwriting real env vars."""
    path = path or (ROOT / ".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    page_id: str
    ig_user_id: str
    token: str
    public_base_url: str
    graph_version: str = "v23.0"
    fb_alt_text: bool = True

    @property
    def graph_base(self) -> str:
        return f"https://graph.facebook.com/{self.graph_version}"

    @classmethod
    def from_env(cls, require_credentials: bool = True) -> "Settings":
        version = os.getenv("META_GRAPH_VERSION", "v23.0").strip()
        if not re.fullmatch(r"v\d+\.\d+", version):
            raise ConfigError(f"META_GRAPH_VERSION must look like v23.0, got {version!r}")

        base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
        if not base:
            if require_credentials:
                raise ConfigError("PUBLIC_BASE_URL is not set")
            base = "https://YOURUSER.github.io/Cluefolio"

        settings = cls(
            page_id=os.getenv("META_PAGE_ID", "").strip(),
            ig_user_id=os.getenv("META_IG_USER_ID", "").strip(),
            token=os.getenv("META_PAGE_ACCESS_TOKEN", "").strip(),
            public_base_url=base,
            graph_version=version,
            fb_alt_text=os.getenv("META_FB_ALT_TEXT", "true").strip().lower() not in ("0", "false", "no"),
        )

        if require_credentials:
            missing = [
                name for name, value in (
                    ("META_PAGE_ID", settings.page_id),
                    ("META_IG_USER_ID", settings.ig_user_id),
                    ("META_PAGE_ACCESS_TOKEN", settings.token),
                ) if not value
            ]
            if missing:
                raise ConfigError("Missing required environment variables: " + ", ".join(missing))
        return settings

"""Small, dependency-free Meta Graph API client with retries."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

RETRYABLE_HTTP = {429, 500, 502, 503, 504}
RETRYABLE_CODES = {1, 2, 4, 17, 32, 341, 613}


class GraphError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None,
                 code: int | None = None, subcode: int | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.subcode = subcode


class GraphClient:
    """Minimal Graph API client.

    The access token is sent in the request body for POSTs so it never appears
    in a URL or in an exception message.
    """

    def __init__(self, base: str, token: str, timeout: int = 90, max_attempts: int = 4):
        self.base = base.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.max_attempts = max_attempts

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params)

    def post(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", path, params)

    def _request(self, method: str, path: str, params: dict[str, Any] | None) -> dict[str, Any]:
        payload = {k: v for k, v in (params or {}).items() if v is not None}
        payload["access_token"] = self.token
        url = f"{self.base}/{path.lstrip('/')}"

        if method == "GET":
            request = urllib.request.Request(
                f"{url}?{urllib.parse.urlencode(payload, doseq=True)}",
                headers={"Accept": "application/json"},
                method="GET",
            )
        else:
            request = urllib.request.Request(
                url,
                data=urllib.parse.urlencode(payload, doseq=True).encode("utf-8"),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )

        last_error: GraphError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = response.read().decode("utf-8", "replace")
                    return json.loads(body) if body.strip() else {}
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "replace")
                error = _parse_error(body)
                status = exc.code
                code = _as_int(error.get("code"))
                subcode = _as_int(error.get("error_subcode"))
                message = error.get("message") or f"Graph API HTTP {status}"

                if code == 190:
                    message = "Access token is invalid or expired. Refresh META_PAGE_ACCESS_TOKEN."
                elif code == 10 or code == 200:
                    message = "Permission denied. Check app review, page role, and token scopes."

                last_error = GraphError(message, status=status, code=code, subcode=subcode)
                if not _retryable(status, code) or attempt == self.max_attempts:
                    raise last_error from None
            except urllib.error.URLError as exc:
                last_error = GraphError(f"Network error: {exc.reason}")
                if attempt == self.max_attempts:
                    raise last_error from None

            time.sleep(min(30, 2 ** (attempt - 1)))

        raise last_error or GraphError("Graph API request failed")


def _parse_error(body: str) -> dict[str, Any]:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return {"message": body[:400]}
    error = parsed.get("error")
    return error if isinstance(error, dict) else {"message": str(parsed)[:400]}


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _retryable(status: int, code: int | None) -> bool:
    return status in RETRYABLE_HTTP or (code is not None and code in RETRYABLE_CODES)

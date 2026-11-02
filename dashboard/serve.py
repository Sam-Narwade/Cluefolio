#!/usr/bin/env python3
"""Local server for the Cluefolio Studio OS dashboard.

Serves the project root so the dashboard can read /content/dashboard.json and
the rendered covers under /content/<slug>/images/. Binds to localhost only.

Usage:
    python dashboard/serve.py                # http://127.0.0.1:8080/dashboard/
    python dashboard/serve.py --port 8090
    python dashboard/serve.py --no-browser
"""

from __future__ import annotations

import argparse
import http.server
import os
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/dashboard"):
            self.send_response(302)
            self.send_header("Location", "/dashboard/")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        print("  " + (fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Cluefolio dashboard locally.")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser window")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}/dashboard/"

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        print(f"Could not bind 127.0.0.1:{args.port} - {exc}")
        print("Another process is probably using that port. Try: python dashboard/serve.py --port 8090")
        return 1

    print()
    print("  CLUEFOLIO STUDIO OS")
    print(f"  Dashboard : {url}")
    print(f"  Static site: http://127.0.0.1:{args.port}/site/index.html")
    print(f"  Data       : http://127.0.0.1:{args.port}/content/dashboard.json")
    print("  Serving   : " + str(ROOT))
    print("  Stop      : Ctrl+C")
    print()

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

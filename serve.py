#!/usr/bin/env python3
"""GHF demo server: static site + server-side Anthropic proxy.

The browser calls POST /api/chat; this server forwards it to the Anthropic API
with the key from the ANTHROPIC_API_KEY environment variable, so the key never
appears in any file or in client-side code.

Run:  ANTHROPIC_API_KEY=sk-ant-...  python3 serve.py
"""
import http.server
import json
import os
import socketserver
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "docs")
PORT = int(os.environ.get("PORT", "4173"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE, **kwargs)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            self._json(503, {"error": {"message": "Server has no ANTHROPIC_API_KEY. Restart with: ANTHROPIC_API_KEY=sk-ant-... python3 serve.py"}})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                # stream SSE chunks straight through
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except BrokenPipeError:
                        break
        except urllib.error.HTTPError as e:
            self._raw(e.code, e.read())
        except Exception as e:  # noqa: BLE001 — surface anything to the widget
            self._json(502, {"error": {"message": str(e)}})

    def _raw(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status, obj):
        self._raw(status, json.dumps(obj).encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as srv:
        has_key = "yes" if os.environ.get("ANTHROPIC_API_KEY") else "NO — chat will be disabled"
        print(f"GHF site on http://localhost:{PORT}  (API key present: {has_key})")
        srv.serve_forever()

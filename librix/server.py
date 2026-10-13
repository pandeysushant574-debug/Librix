"""HTTP server (standard library only): serves the frontend files and the JSON API on one port."""
import json
import mimetypes
import sqlite3
import sys
import traceback
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from . import config, logger
from .db import get_db
from .helpers import ApiError
from .request import Request
from .router import dispatch
from .security import sessions

MAX_BODY = 2 * 1024 * 1024

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Librix"
    sys_version = ""

    # ------------------------------------------------------------------ plumbing
    def log_message(self, fmt, *args):  # quieter, one clean line per request
        sys.stderr.write(f"  {self.command:<6} {self.path}  ->  {args[1] if len(args) > 1 else ''}\n")

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, MAX_BODY))
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, UnicodeDecodeError):
            return {}

    def _send(self, status, body: bytes, content_type, extra_headers=(), head_only=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _send_json(self, status, payload, cookies=(), head_only=False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = [("Cache-Control", "no-store")] + [("Set-Cookie", c) for c in cookies]
        self._send(status, body, "application/json; charset=utf-8", headers, head_only)

    # ------------------------------------------------------------------ routing
    def _handle(self):
        parts = urlsplit(self.path)
        path = unquote(parts.path)
        body = self._read_body() if self.command in ("POST", "PUT", "PATCH", "DELETE") else {}
        head_only = self.command == "HEAD"

        if self.command == "OPTIONS":
            self._send(HTTPStatus.NO_CONTENT, b"", "text/plain", [("Allow", "GET, POST, PUT, DELETE, OPTIONS")])
            return

        if path == "/api" or path.startswith("/api/"):
            self._handle_api(path, parts.query, body, head_only)
        elif self.command in ("GET", "HEAD"):
            self._serve_static(path, head_only)
        else:
            self._send_json(405, {"success": False, "message": "Method not allowed.", "errors": None})

    def _handle_api(self, path, query_string, body, head_only):
        cookie = SimpleCookie(self.headers.get("Cookie") or "")
        cookies = {k: v.value for k, v in cookie.items()}
        query = {k: v[0] for k, v in parse_qs(query_string, keep_blank_values=True).items()}
        method = "GET" if self.command == "HEAD" else self.command
        segments = [s for s in path.split("/") if s]

        db = get_db()
        with db.lock:  # one API request at a time keeps SQLite transactions simple and safe
            session = sessions.get(cookies.get(config.SESSION_COOKIE))
            req = Request(method, path, query, body, session, cookies)
            try:
                result = dispatch(req, segments)
                if getattr(result, "root", False):
                    self._send_json(200, {"success": True, "message": "Library Management System API", "status": "OK"}, head_only=head_only)
                else:
                    self._send_json(result.status, {"success": True, "message": result.message, "data": result.data},
                                    result.cookies, head_only)
            except ApiError as exc:
                self._send_json(exc.status, {"success": False, "message": exc.message, "errors": exc.errors}, head_only=head_only)
            except Exception as exc:  # noqa: BLE001  - ErrorMiddleware equivalent
                traceback.print_exc()
                logger.log("System", "DATABASE_ERROR" if isinstance(exc, sqlite3.Error) else "SYSTEM_ERROR", "ERROR",
                           str(exc), "FAILED", f"{type(exc).__name__}")
                self._send_json(500, {"success": False, "message": "An unexpected server error occurred. It has been logged.",
                                      "errors": None}, head_only=head_only)

    def _serve_static(self, path, head_only):
        if path in ("", "/"):
            path = "/index.html"
        root = config.FRONTEND_DIR.resolve()
        target = (root / path.lstrip("/")).resolve()
        if root not in target.parents and target != root:
            return self._send(403, b"Forbidden", "text/plain; charset=utf-8", head_only=head_only)
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            page = b"<!doctype html><meta charset=utf-8><title>Not found</title><body style='font-family:sans-serif;padding:40px'><h2>404 - page not found</h2><a href='/'>Back to Librix</a>"
            return self._send(404, page, "text/html; charset=utf-8", head_only=head_only)
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype, [("Cache-Control", "no-cache")], head_only)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = _handle


class LibrixServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(host=None, port=None) -> LibrixServer:
    return LibrixServer((host or config.HOST, port if port is not None else config.PORT), Handler)

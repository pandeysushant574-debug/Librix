"""
Librix automated tests (standard library `unittest` - nothing to install).
Run:   python -m unittest discover -s tests -v
Covers validators, fine calculation, password hashing and the full HTTP API
(login, roles, books, members, issue/return/fine flow, quality modules).
"""
import http.cookiejar
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from librix import config  # noqa: E402
from librix.db import init_db  # noqa: E402
from librix.security import hash_password, verify_password  # noqa: E402
from librix.server import make_server  # noqa: E402
from librix.services.fines import FineService  # noqa: E402
from librix.validators import BookValidator, IssueValidator, MemberValidator  # noqa: E402


class ValidatorTests(unittest.TestCase):
    def test_book_valid(self):
        self.assertEqual(BookValidator.validate({"title": "T", "author": "A", "quantity": 5}), [])

    def test_book_blank_title(self):
        self.assertIn("Title is required.", BookValidator.validate({"title": "", "author": "A", "quantity": 1}))

    def test_book_quantity_boundaries(self):
        ok = lambda q: not BookValidator.validate({"title": "T", "author": "A", "quantity": q})  # noqa: E731
        self.assertFalse(ok(-1))
        self.assertTrue(ok(0))
        self.assertTrue(ok(9999))
        self.assertFalse(ok(10000))

    def test_title_length_boundaries(self):
        ok = lambda n: not BookValidator.validate({"title": "A" * n, "author": "A", "quantity": 1})  # noqa: E731
        self.assertTrue(ok(255))
        self.assertFalse(ok(256))

    def test_available_cannot_exceed_total(self):
        self.assertTrue(BookValidator.validate({"title": "T", "author": "A", "quantity": 2, "available_qty": 5}))

    def test_member_code_format(self):
        base = {"name": "N", "membership_date": "2026-01-01"}
        self.assertEqual(MemberValidator.validate({**base, "member_code": "MEM-0001"}), [])
        self.assertTrue(MemberValidator.validate({**base, "member_code": "BAD"}))

    def test_issue_due_before_issue(self):
        errs = IssueValidator.validate({"book_id": 1, "member_id": 1, "issue_date": "2026-09-10", "due_date": "2026-09-01"})
        self.assertIn("Due date must be on or after the issue date.", errs)


class FineAndSecurityTests(unittest.TestCase):
    def test_fine_three_days_late(self):
        self.assertEqual(FineService.calculate("2026-08-27", "2026-08-30")["amount"], 15.0)

    def test_no_fine_when_on_time(self):
        self.assertEqual(FineService.calculate("2026-08-27", "2026-08-27")["amount"], 0.0)

    def test_password_hash_roundtrip(self):
        h = hash_password("Secret@1")
        self.assertTrue(verify_password("Secret@1", h))
        self.assertFalse(verify_password("secret@1", h))
        self.assertNotEqual(h, hash_password("Secret@1"))  # salted


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        init_db(os.path.join(cls.tmp.name, "test.db"))
        cls.server = make_server("127.0.0.1", 0)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def client(self, username=None, password=None):
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        def call(method, path, body=None):
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(self.base + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"} if data else {})
            try:
                with opener.open(req) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        if username:
            status, _ = call("POST", "/api/auth/login", {"username": username, "password": password})
            assert status == 200, "login failed in test setup"
        return call

    def test_requires_login(self):
        self.assertEqual(self.client()("GET", "/api/books")[0], 401)

    def test_bad_login(self):
        status, body = self.client()("POST", "/api/auth/login", {"username": "admin", "password": "nope"})
        self.assertEqual(status, 401)
        self.assertEqual(body["message"], "Invalid username or password.")

    def test_roles(self):
        assistant = self.client("assistant", "Assistant@123")
        self.assertEqual(assistant("POST", "/api/books", {"title": "x", "author": "y", "quantity": 1})[0], 403)
        librarian = self.client("librarian", "Librarian@123")
        self.assertEqual(librarian("GET", "/api/users")[0], 403)
        self.assertEqual(self.client("admin", "Admin@123")("GET", "/api/users")[0], 200)

    def test_book_crud_and_search(self):
        c = self.client("admin", "Admin@123")
        status, body = c("POST", "/api/books", {"title": "Search Me Please", "author": "Z", "quantity": 3, "isbn": "T-1"})
        self.assertEqual(status, 201)
        self.assertEqual(body["data"]["available_qty"], 3)
        self.assertEqual(c("POST", "/api/books", {"title": "Dup", "author": "Z", "quantity": 1, "isbn": "T-1"})[0], 409)
        self.assertEqual(len(c("GET", "/api/books?q=search%20me")[1]["data"]), 1)
        self.assertEqual(c("DELETE", f"/api/books/{body['data']['book_id']}")[0], 200)

    def test_issue_return_fine_flow(self):
        c = self.client("admin", "Admin@123")
        before = c("GET", "/api/books/4")[1]["data"]["available_qty"]
        status, body = c("POST", "/api/issues", {"book_id": 4, "member_id": 1, "issue_date": "2026-09-01", "due_date": "2026-09-08"})
        self.assertEqual(status, 201)
        self.assertEqual(c("GET", "/api/books/4")[1]["data"]["available_qty"], before - 1)
        status, ret = c("POST", "/api/returns", {"issue_id": body["data"]["issue_id"], "return_date": "2026-09-11"})
        self.assertEqual((status, ret["data"]["fine_amount"]), (200, "15.00"))
        self.assertEqual(c("GET", "/api/books/4")[1]["data"]["available_qty"], before)
        self.assertEqual(c("POST", "/api/returns", {"issue_id": body["data"]["issue_id"], "return_date": "2026-09-11"})[0], 409)

    def test_cannot_issue_unavailable_book(self):
        c = self.client("admin", "Admin@123")
        status, body = c("POST", "/api/issues", {"book_id": 5, "member_id": 1, "issue_date": "2026-09-01", "due_date": "2026-09-08"})
        self.assertEqual(status, 409)
        self.assertIn("not available", body["message"])

    def test_quality_modules(self):
        c = self.client("admin", "Admin@123")
        results = c("POST", "/api/tests/run-all")[1]["data"]
        self.assertEqual(len(results), 12)
        self.assertTrue(all(r["status"] == "PASS" for r in results), results)
        boundary = c("POST", "/api/boundary-tests/run")[1]["data"]
        self.assertTrue(all(r["status"] == "PASS" for r in boundary), boundary)
        self.assertEqual(c("POST", "/api/boundary-tests/run")[0], 200)  # no duplicate-code crash on re-run

    def test_bug_workflow(self):
        c = self.client("admin", "Admin@123")
        _, body = c("POST", "/api/bugs", {"module": "M", "title": "t", "description": "d", "severity": "Low",
                                          "priority": "Low", "reported_date": "2026-10-01"})
        bug_id = body["data"]["bug_id"]
        self.assertEqual(c("PUT", f"/api/bugs/{bug_id}", {"status": "Closed"})[0], 409)  # Open -> Closed not allowed
        for step in ("In Progress", "Fixed", "Retest", "Closed"):
            self.assertEqual(c("PUT", f"/api/bugs/{bug_id}", {"status": step})[0], 200)

    def test_dashboard_and_frontend(self):
        self.assertEqual(self.client("admin", "Admin@123")("GET", "/api/reports/dashboard")[0], 200)
        with urllib.request.urlopen(self.base + "/login.html") as r:
            self.assertEqual(r.status, 200)

    def test_path_traversal_blocked(self):
        for path in ("/../app.py", "/%2e%2e/app.py"):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(self.base + path)
            self.assertIn(ctx.exception.code, (403, 404))


if __name__ == "__main__":
    unittest.main(verbosity=2)

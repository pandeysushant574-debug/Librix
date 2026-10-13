"""
API router - the single entry point for every /api/* request.
Architecture:  browser fetch() -> router -> Controller -> Service -> SQLite
The frontend never talks to the database directly.
"""
from .controllers.admin import ReportController, UserController
from .controllers.auth import AuthController
from .controllers.books import BookController
from .controllers.issues import FineController, IssueController
from .controllers.members import MemberController
from .controllers.quality import BoundaryController, BugController, LogController, TestController
from .helpers import ApiError, to_int
from .request import RootResult


def dispatch(req, segments):
    """Map (method, /api/<resource>/<sub1>/<sub2>) onto a controller action. Returns a Result."""
    if segments and segments[0] == "api":
        segments = segments[1:]
    resource = segments[0] if len(segments) > 0 else ""
    sub1 = segments[1] if len(segments) > 1 else None
    sub2 = segments[2] if len(segments) > 2 else None
    m = req.method
    not_found = ApiError("Not found.", 404)

    if resource == "auth":
        c = AuthController()
        if sub1 == "login" and m == "POST":
            return c.login(req)
        if sub1 == "logout" and m == "POST":
            return c.logout(req)
        if sub1 == "me" and m == "GET":
            return c.me(req)
        raise not_found

    if resource == "books":
        c = BookController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "GET":
            return c.show(req, to_int(sub1))
        if m == "POST" and sub1 is None:
            return c.store(req)
        if m == "PUT" and sub1 is not None:
            return c.update(req, to_int(sub1))
        if m == "DELETE" and sub1 is not None:
            return c.destroy(req, to_int(sub1))
        raise not_found

    if resource == "members":
        c = MemberController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "GET":
            return c.show(req, to_int(sub1))
        if m == "POST" and sub1 is None:
            return c.store(req)
        if m == "PUT" and sub1 is not None:
            return c.update(req, to_int(sub1))
        if m == "DELETE" and sub1 is not None:
            return c.destroy(req, to_int(sub1))
        raise not_found

    if resource == "issues":
        c = IssueController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub1 is None:
            return c.store(req)
        raise not_found

    if resource == "returns":
        if m == "POST":
            return IssueController().return_book(req)
        raise not_found

    if resource == "fines":
        c = FineController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub2 == "pay":
            return c.pay(req, to_int(sub1))
        raise not_found

    if resource == "tests":
        c = TestController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub1 is None:
            return c.store(req)
        if m == "POST" and sub1 == "run-all":
            return c.run_all(req)
        if m == "POST" and sub1 == "run" and sub2 is not None:
            return c.run(req, to_int(sub2))
        if m == "PUT" and sub1 is not None:
            return c.update(req, to_int(sub1))
        if m == "DELETE" and sub1 is not None:
            return c.destroy(req, to_int(sub1))
        raise not_found

    if resource == "bugs":
        c = BugController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub1 is None:
            return c.store(req)
        if m == "PUT" and sub1 is not None:
            return c.update(req, to_int(sub1))
        if m == "DELETE" and sub1 is not None:
            return c.destroy(req, to_int(sub1))
        raise not_found

    if resource == "boundary-tests":
        c = BoundaryController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub1 == "run":
            return c.run_all(req)
        raise not_found

    if resource == "logs":
        if m == "GET":
            return LogController().index(req)
        raise not_found

    if resource == "reports":
        c = ReportController()
        if m == "GET":
            action = {"dashboard": c.dashboard, "testing": c.testing, "bugs": c.bugs, "library": c.library,
                      "issues": c.issues, "fines": c.fines, "system-logs": c.system_logs}.get(sub1)
            if action:
                return action(req)
        raise not_found

    if resource == "users":
        c = UserController()
        if m == "GET" and sub1 is None:
            return c.index(req)
        if m == "POST" and sub1 is None:
            return c.store(req)
        if m == "PUT" and sub1 is not None and sub2 == "status":
            return c.update_status(req, to_int(sub1))
        raise not_found

    if resource == "":
        return RootResult()
    raise not_found

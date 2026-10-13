"""Controllers for the Quality (Q16) modules: unit tests, bugs, boundary tests, logs."""
from ..helpers import ApiError, ServiceError
from ..request import success
from ..services.boundary import BoundaryService
from ..services.bugs import BugService
from ..services.logs import LogService
from ..services.testcases import TestService
from ..validators import BugValidator, TestValidator

EDITORS = ("Admin", "Librarian")


class TestController:
    __test__ = False

    def __init__(self):
        self.service = TestService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all())

    def store(self, req):
        session = req.require_role(*EDITORS)
        errors = TestValidator.validate(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        return success(self.service.create(req.body, session["user_id"]), "Test case created.", 201)

    def update(self, req, test_id):
        req.require_role(*EDITORS)
        errors = TestValidator.validate(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.update(test_id, req.body), "Test case updated.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404) from exc

    def destroy(self, req, test_id):
        req.require_role(*EDITORS)
        self.service.delete(test_id)
        return success([], "Test case deleted.")

    def run(self, req, test_id):
        session = req.require_role(*EDITORS)
        try:
            return success(self.service.run(test_id, session["user_id"], session["username"]), "Test executed.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404) from exc

    def run_all(self, req):
        session = req.require_role(*EDITORS)
        return success(self.service.run_all(session["user_id"], session["username"]), "All tests executed.")


class BugController:
    def __init__(self):
        self.service = BugService()

    def index(self, req):
        req.require_auth()
        if "counters" in req.query:
            return success(self.service.counters())
        return success(self.service.all(req.filters("status", "severity", "module")))

    def store(self, req):
        session = req.require_role(*EDITORS)
        errors = BugValidator.validate(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        return success(self.service.create(req.body, session["user_id"], session["username"]), "Bug logged.", 201)

    def update(self, req, bug_id):
        session = req.require_role(*EDITORS)
        try:
            return success(self.service.update(bug_id, req.body, session["user_id"], session["username"]), "Bug updated.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404 if "not found" in str(exc).lower() else 409) from exc

    def destroy(self, req, bug_id):
        req.require_role("Admin")
        self.service.delete(bug_id)
        return success([], "Bug deleted.")


class BoundaryController:
    def __init__(self):
        self.service = BoundaryService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all())

    def run_all(self, req):
        session = req.require_role(*EDITORS)
        return success(self.service.run_all(session["user_id"], session["username"]), "Boundary tests executed.")


class LogController:
    def __init__(self):
        self.service = LogService()

    def index(self, req):
        req.require_auth()
        if "counters" in req.query:
            return success(self.service.counters())
        if "audit" in req.query:
            return success(self.service.audit_logs())
        return success(self.service.all(req.filters("level", "module", "q")))

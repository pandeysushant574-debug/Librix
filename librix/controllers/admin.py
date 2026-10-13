from ..helpers import ApiError, ServiceError, is_empty
from ..request import success
from ..services.reports import ReportService
from ..services.users import UserService


class ReportController:
    def __init__(self):
        self.service = ReportService()

    def dashboard(self, req):
        req.require_auth()
        return success(self.service.dashboard())

    def testing(self, req):
        req.require_auth()
        return success(self.service.testing_report())

    def bugs(self, req):
        req.require_auth()
        return success(self.service.bug_report())

    def library(self, req):
        req.require_auth()
        return success(self.service.library_report())

    def issues(self, req):
        req.require_auth()
        return success(self.service.issue_report())

    def fines(self, req):
        req.require_auth()
        return success(self.service.fine_report())

    def system_logs(self, req):
        req.require_auth()
        return success(self.service.system_log_report())


class UserController:
    def __init__(self):
        self.service = UserService()

    def index(self, req):
        req.require_role("Admin")
        return success(self.service.all())

    def store(self, req):
        session = req.require_role("Admin")
        b = req.body
        if any(is_empty(b.get(k)) for k in ("name", "username", "password", "role")):
            raise ApiError("Name, username, password and role are required.", 422)
        try:
            return success(self.service.create(b, session["user_id"], session["username"]), "User created.", 201)
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc

    def update_status(self, req, user_id):
        session = req.require_role("Admin")
        if is_empty(req.body.get("status")):
            raise ApiError("Status is required.", 422)
        try:
            return success(self.service.update_status(user_id, req.body["status"], session["user_id"], session["username"]), "User status updated.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404 if "not found" in str(exc).lower() else 422) from exc

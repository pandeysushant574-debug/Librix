from ..helpers import ApiError, ServiceError
from ..request import success
from ..services.fines import FineService
from ..services.issues import IssueService
from ..validators import IssueValidator

ALL_ROLES = ("Admin", "Librarian", "Assistant")


class IssueController:
    def __init__(self):
        self.service = IssueService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all(req.filters("status", "member_id")))

    def store(self, req):
        session = req.require_role(*ALL_ROLES)
        errors = IssueValidator.validate(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.issue_book(req.body, session["user_id"], session["username"]), "Book issued.", 201)
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc

    def return_book(self, req):
        session = req.require_role(*ALL_ROLES)
        errors = IssueValidator.validate_return(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.return_book(req.body, session["user_id"], session["username"]), "Book returned.")
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc


class FineController:
    def __init__(self):
        self.service = FineService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all(req.filters("status")))

    def pay(self, req, fine_id):
        session = req.require_role("Admin", "Librarian")
        try:
            return success(self.service.pay(fine_id, session["user_id"], session["username"]), "Fine marked as paid.")
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc

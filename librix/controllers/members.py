from ..helpers import ApiError, ServiceError
from ..request import success
from ..services.members import MemberService
from ..validators import MemberValidator

WRITE_ROLES = ("Admin", "Librarian")


class MemberController:
    def __init__(self):
        self.service = MemberService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all(req.filters("q", "status")))

    def show(self, req, member_id):
        req.require_auth()
        member = self.service.find(member_id)
        if not member:
            raise ApiError("Member not found.", 404)
        return success(member)

    def store(self, req):
        session = req.require_role(*WRITE_ROLES)
        errors = MemberValidator.validate(req.body)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.create(req.body, session["user_id"], session["username"]), "Member created.", 201)
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc

    def update(self, req, member_id):
        session = req.require_role(*WRITE_ROLES)
        try:
            return success(self.service.update(member_id, req.body, session["user_id"], session["username"]), "Member updated.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404) from exc

    def destroy(self, req, member_id):
        session = req.require_role(*WRITE_ROLES)
        try:
            self.service.delete(member_id, session["user_id"], session["username"])
            return success([], "Member removed.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404 if "not found" in str(exc).lower() else 409) from exc

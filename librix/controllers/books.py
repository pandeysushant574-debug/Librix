from .. import logger
from ..helpers import ApiError, ServiceError
from ..request import success
from ..services.books import BookService
from ..validators import BookValidator

WRITE_ROLES = ("Admin", "Librarian")


class BookController:
    def __init__(self):
        self.service = BookService()

    def index(self, req):
        req.require_auth()
        return success(self.service.all(req.filters("q", "category", "status")))

    def show(self, req, book_id):
        req.require_auth()
        book = self.service.find(book_id)
        if not book:
            raise ApiError("Book not found.", 404)
        return success(book)

    def store(self, req):
        session = req.require_role(*WRITE_ROLES)
        errors = BookValidator.validate(req.body)
        if errors:
            logger.warning("Books", "VALIDATION_FAILED", "Book creation validation failed", session["user_id"], session["username"])
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.create(req.body, session["user_id"], session["username"]), "Book created.", 201)
        except ServiceError as exc:
            raise ApiError(str(exc), 409) from exc

    def update(self, req, book_id):
        session = req.require_role(*WRITE_ROLES)
        errors = BookValidator.validate(req.body, True)
        if errors:
            raise ApiError("Validation failed.", 422, errors)
        try:
            return success(self.service.update(book_id, req.body, session["user_id"], session["username"]), "Book updated.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404 if "not found" in str(exc).lower() else 409) from exc

    def destroy(self, req, book_id):
        session = req.require_role(*WRITE_ROLES)
        try:
            self.service.delete(book_id, session["user_id"], session["username"])
            return success([], "Book deleted.")
        except ServiceError as exc:
            raise ApiError(str(exc), 404 if "not found" in str(exc).lower() else 409) from exc

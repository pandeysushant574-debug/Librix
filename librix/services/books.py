import sqlite3

from .. import logger
from ..db import get_db
from ..helpers import ServiceError, text, to_int


def _isbn(value):
    return text(value) or None


class BookService:
    def all(self, filters=None) -> list:
        filters = filters or {}
        sql = "SELECT * FROM books WHERE 1=1"
        params = []
        if filters.get("q"):
            sql += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)"
            like = f"%{filters['q']}%"
            params += [like, like, like]
        if filters.get("category"):
            sql += " AND category = ?"
            params.append(filters["category"])
        if filters.get("status"):
            sql += " AND status = ?"
            params.append(filters["status"])
        sql += " ORDER BY title COLLATE NOCASE ASC"
        return get_db().query(sql, params)

    def find(self, book_id: int):
        return get_db().one("SELECT * FROM books WHERE book_id = ?", (book_id,))

    def create(self, data: dict, user_id, username) -> dict:
        db = get_db()
        quantity = to_int(data["quantity"])
        available = to_int(data["available_qty"]) if data.get("available_qty") not in (None, "") else quantity
        try:
            book_id = db.insert(
                "INSERT INTO books (isbn, title, author, category, publisher, edition, year_published, quantity, "
                "available_qty, reorder_level, shelf_location, status, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_isbn(data.get("isbn")), text(data["title"]), text(data["author"]), data.get("category"),
                 data.get("publisher"), data.get("edition"), data.get("year_published") or None, quantity, available,
                 data["reorder_level"] if data.get("reorder_level") not in (None, "") else 2,
                 data.get("shelf_location"), data.get("status") or "Available", text(data.get("description")) or None),
            )
        except sqlite3.IntegrityError as exc:
            raise ServiceError(self._friendly(exc)) from exc
        book = self.find(book_id)
        logger.audit("CREATE_BOOK", "Book", book_id, None, book, user_id, username)
        logger.info("Books", "BOOK_CREATED", f'Book "{book["title"]}" created', user_id, username, "SUCCESS", f"book_id={book_id}")
        return book

    def update(self, book_id: int, data: dict, user_id, username) -> dict:
        db = get_db()
        existing = self.find(book_id)
        if not existing:
            raise ServiceError("Book not found.")
        quantity = to_int(data["quantity"]) if "quantity" in data else existing["quantity"]
        available = to_int(data["available_qty"]) if "available_qty" in data else existing["available_qty"]
        pick = lambda key: data[key] if key in data and data[key] is not None else existing[key]  # noqa: E731
        try:
            db.execute(
                "UPDATE books SET isbn=?, title=?, author=?, category=?, publisher=?, edition=?, year_published=?, "
                "quantity=?, available_qty=?, reorder_level=?, shelf_location=?, status=?, description=? WHERE book_id=?",
                (_isbn(data["isbn"]) if "isbn" in data else existing["isbn"],
                 text(data["title"]) if data.get("title") is not None else existing["title"],
                 text(data["author"]) if data.get("author") is not None else existing["author"],
                 pick("category"), pick("publisher"), pick("edition"), pick("year_published"),
                 quantity, available, pick("reorder_level"), pick("shelf_location"), pick("status"),
                 (text(data["description"]) or None) if "description" in data else existing["description"], book_id),
            )
        except sqlite3.IntegrityError as exc:
            raise ServiceError(self._friendly(exc)) from exc
        updated = self.find(book_id)
        logger.audit("UPDATE_BOOK", "Book", book_id, existing, updated, user_id, username)
        logger.info("Books", "BOOK_UPDATED", f'Book "{updated["title"]}" updated', user_id, username, "SUCCESS", f"book_id={book_id}")
        return updated

    def delete(self, book_id: int, user_id, username) -> None:
        existing = self.find(book_id)
        if not existing:
            raise ServiceError("Book not found.")
        try:
            get_db().execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        except sqlite3.IntegrityError as exc:
            raise ServiceError("This book has issue records and cannot be deleted. Mark it Inactive instead.") from exc
        logger.audit("DELETE_BOOK", "Book", book_id, existing, None, user_id, username)
        logger.info("Books", "BOOK_DELETED", f'Book "{existing["title"]}" deleted', user_id, username, "SUCCESS", f"book_id={book_id}")

    @staticmethod
    def _friendly(exc: sqlite3.IntegrityError) -> str:
        msg = str(exc)
        if "books.isbn" in msg:
            return "A book with this ISBN already exists."
        if "CHECK" in msg:
            return "Quantity values are inconsistent (available cannot exceed total)."
        return "Could not save the book: " + msg

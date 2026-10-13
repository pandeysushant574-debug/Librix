from .. import logger
from ..db import get_db
from ..helpers import ServiceError, money, to_int
from .fines import FineService


def _present(row):
    if row:
        row["fine_amount"] = money(row["fine_amount"])
    return row


class IssueService:
    def all(self, filters=None) -> list:
        filters = filters or {}
        sql = ("SELECT i.*, b.title AS book_title, m.name AS member_name, m.member_code FROM issues i "
               "JOIN books b ON b.book_id = i.book_id JOIN members m ON m.member_id = i.member_id WHERE 1=1")
        params = []
        if filters.get("status"):
            sql += " AND i.status = ?"
            params.append(filters["status"])
        if filters.get("member_id"):
            sql += " AND i.member_id = ?"
            params.append(filters["member_id"])
        sql += " ORDER BY i.issue_date DESC, i.issue_id DESC"
        return [_present(r) for r in get_db().query(sql, params)]

    def find(self, issue_id: int):
        return _present(get_db().one("SELECT * FROM issues WHERE issue_id = ?", (issue_id,)))

    def issue_book(self, data: dict, issued_by: int, username) -> dict:
        db = get_db()
        try:
            with db.transaction():
                book_id = to_int(data["book_id"])
                member_id = to_int(data["member_id"])
                qty = to_int(data["quantity"]) if data.get("quantity") is not None else 1

                member = db.one("SELECT * FROM members WHERE member_id = ?", (member_id,))
                if not member:
                    raise ServiceError("Member not found.")
                if member["status"] != "Active":
                    raise ServiceError("Member is not active.")

                book = db.one("SELECT * FROM books WHERE book_id = ?", (book_id,))
                if not book:
                    raise ServiceError("Book not found.")
                if book["available_qty"] < qty or qty <= 0:
                    raise ServiceError("Book is not available in the requested quantity.")
                if data["due_date"] < data["issue_date"]:
                    raise ServiceError("Due date must be on or after the issue date.")

                issue_id = db.insert(
                    "INSERT INTO issues (book_id, member_id, issued_by, issue_date, due_date, quantity, status) "
                    "VALUES (?,?,?,?,?,?, 'Issued')",
                    (book_id, member_id, issued_by, data["issue_date"], data["due_date"], qty),
                )
                db.execute("UPDATE books SET available_qty = ? WHERE book_id = ?", (book["available_qty"] - qty, book_id))

                logger.audit("BOOK_ISSUED", "Issue", issue_id, None,
                             {"book_id": book_id, "member_id": member_id, "quantity": qty}, issued_by, username)
                logger.info("Issues", "BOOK_ISSUED", f'Book "{book["title"]}" issued to member {member["member_code"]}',
                            issued_by, username, "SUCCESS", f"issue_id={issue_id}")
            return self.find(issue_id)
        except Exception as exc:
            logger.error("Issues", "BOOK_ISSUED", str(exc), issued_by, username)
            raise

    def return_book(self, data: dict, received_by: int, username) -> dict:
        db = get_db()
        try:
            with db.transaction():
                issue_id = to_int(data["issue_id"])
                issue = db.one("SELECT * FROM issues WHERE issue_id = ?", (issue_id,))
                if not issue:
                    raise ServiceError("Issue not found.")
                if issue["status"] == "Returned":
                    raise ServiceError("This issue has already been returned.")

                return_date = data["return_date"]
                if return_date < issue["issue_date"]:
                    raise ServiceError("Return date cannot be before the issue date.")

                fine = FineService.calculate(issue["due_date"], return_date)

                db.execute("UPDATE issues SET status = 'Returned', return_date = ?, fine_amount = ? WHERE issue_id = ?",
                           (return_date, fine["amount"], issue_id))
                db.insert(
                    "INSERT INTO returns (issue_id, received_by, return_date, condition_status, fine_amount, remarks) "
                    "VALUES (?,?,?,?,?,?)",
                    (issue_id, received_by, return_date, data.get("condition_status") or "Good", fine["amount"], data.get("remarks")),
                )
                book = db.one("SELECT * FROM books WHERE book_id = ?", (issue["book_id"],))
                db.execute("UPDATE books SET available_qty = MIN(quantity, available_qty + ?) WHERE book_id = ?",
                           (issue["quantity"], issue["book_id"]))

                if fine["amount"] > 0:
                    db.insert(
                        "INSERT INTO fines (issue_id, member_id, days_late, rate_per_day, amount, status) VALUES (?,?,?,?,?, 'Unpaid')",
                        (issue_id, issue["member_id"], fine["days_late"], fine["rate_per_day"], fine["amount"]),
                    )
                    logger.info("Fines", "FINE_CREATED", f"Fine of {fine['amount']} created for issue #{issue_id}", received_by, username)

                logger.audit("BOOK_RETURNED", "Issue", issue_id, {"status": "Issued"}, {"status": "Returned"}, received_by, username)
                logger.info("Issues", "BOOK_RETURNED", f'Book "{book["title"]}" returned', received_by, username, "SUCCESS", f"issue_id={issue_id}")
            return self.find(issue_id)
        except Exception as exc:
            logger.error("Issues", "BOOK_RETURNED", str(exc), received_by, username)
            raise

from datetime import date

from .. import logger
from ..db import get_db
from ..helpers import ServiceError, money

RATE_PER_DAY = 5.00
NORMAL_MAX = 250.00  # 50 days' worth, used by the boundary tests


def _present(row):
    if row:
        row["rate_per_day"] = money(row["rate_per_day"])
        row["amount"] = money(row["amount"])
    return row


class FineService:
    RATE_PER_DAY = RATE_PER_DAY
    NORMAL_MAX = NORMAL_MAX

    @staticmethod
    def calculate(due_date: str, return_date: str, rate: float = RATE_PER_DAY) -> dict:
        due = date.fromisoformat(due_date)
        ret = date.fromisoformat(return_date)
        days_late = max(0, (ret - due).days)
        return {"days_late": days_late, "rate_per_day": rate, "amount": round(days_late * rate, 2)}

    def all(self, filters=None) -> list:
        filters = filters or {}
        sql = ("SELECT f.*, m.name AS member_name, m.member_code, i.book_id FROM fines f "
               "JOIN members m ON m.member_id = f.member_id JOIN issues i ON i.issue_id = f.issue_id WHERE 1=1")
        params = []
        if filters.get("status"):
            sql += " AND f.status = ?"
            params.append(filters["status"])
        sql += " ORDER BY f.created_at DESC, f.fine_id DESC"
        return [_present(r) for r in get_db().query(sql, params)]

    def pay(self, fine_id: int, user_id, username) -> dict:
        db = get_db()
        fine = db.one("SELECT * FROM fines WHERE fine_id = ?", (fine_id,))
        if not fine:
            raise ServiceError("Fine not found.")
        if fine["status"] == "Paid":
            raise ServiceError("Fine already paid.")
        db.execute("UPDATE fines SET status = 'Paid', paid_at = datetime('now','localtime') WHERE fine_id = ?", (fine_id,))
        logger.info("Fines", "FINE_PAID", f"Fine #{fine_id} marked as paid", user_id, username)
        return _present(db.one("SELECT * FROM fines WHERE fine_id = ?", (fine_id,)))

import sqlite3

from .. import logger
from ..db import get_db
from ..helpers import ServiceError, text


class MemberService:
    def all(self, filters=None) -> list:
        filters = filters or {}
        sql = "SELECT * FROM members WHERE 1=1"
        params = []
        if filters.get("q"):
            sql += " AND (name LIKE ? OR member_code LIKE ? OR email LIKE ?)"
            like = f"%{filters['q']}%"
            params += [like, like, like]
        if filters.get("status"):
            sql += " AND status = ?"
            params.append(filters["status"])
        sql += " ORDER BY name COLLATE NOCASE ASC"
        return get_db().query(sql, params)

    def find(self, member_id: int):
        return get_db().one("SELECT * FROM members WHERE member_id = ?", (member_id,))

    def find_by_code(self, code: str):
        return get_db().one("SELECT * FROM members WHERE member_code = ?", (code,))

    def create(self, data: dict, user_id, username) -> dict:
        db = get_db()
        code = text(data["member_code"])
        if self.find_by_code(code):
            raise ServiceError("Member code already exists.")
        member_id = db.insert(
            "INSERT INTO members (member_code, name, email, phone, address, membership_date, expiry_date, status) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (code, text(data["name"]), data.get("email"), data.get("phone"), data.get("address"),
             data["membership_date"], data.get("expiry_date") or None, data.get("status") or "Active"),
        )
        member = self.find(member_id)
        logger.audit("CREATE_MEMBER", "Member", member_id, None, member, user_id, username)
        logger.info("Members", "MEMBER_CREATED", f'Member "{member["name"]}" created', user_id, username, "SUCCESS", f"member_id={member_id}")
        return member

    def update(self, member_id: int, data: dict, user_id, username) -> dict:
        existing = self.find(member_id)
        if not existing:
            raise ServiceError("Member not found.")
        pick = lambda key: data[key] if key in data and data[key] is not None else existing[key]  # noqa: E731
        get_db().execute(
            "UPDATE members SET name=?, email=?, phone=?, address=?, membership_date=?, expiry_date=?, status=? WHERE member_id=?",
            (text(data["name"]) if data.get("name") is not None else existing["name"], pick("email"), pick("phone"),
             pick("address"), pick("membership_date"), pick("expiry_date"), pick("status"), member_id),
        )
        updated = self.find(member_id)
        logger.audit("UPDATE_MEMBER", "Member", member_id, existing, updated, user_id, username)
        action = "MEMBER_DEACTIVATED" if (updated["status"] == "Inactive" and existing["status"] != "Inactive") else "MEMBER_UPDATED"
        logger.info("Members", action, f'Member "{updated["name"]}" updated', user_id, username, "SUCCESS", f"member_id={member_id}")
        return updated

    def delete(self, member_id: int, user_id, username) -> None:
        existing = self.find(member_id)
        if not existing:
            raise ServiceError("Member not found.")
        try:
            get_db().execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        except sqlite3.IntegrityError as exc:
            raise ServiceError("This member has issue records and cannot be deleted. Mark them Inactive instead.") from exc
        logger.audit("DELETE_MEMBER", "Member", member_id, existing, None, user_id, username)
        logger.info("Members", "MEMBER_DEACTIVATED", f'Member "{existing["name"]}" removed', user_id, username, "SUCCESS", f"member_id={member_id}")

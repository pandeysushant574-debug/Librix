import sqlite3

from .. import logger
from ..db import get_db
from ..helpers import ServiceError
from ..security import hash_password

PUBLIC_COLS = "user_id, name, username, role, status, email, phone, created_at"
ROLES = ["Admin", "Librarian", "Assistant"]
STATUSES = ["Active", "Inactive"]


class UserService:
    def all(self) -> list:
        return get_db().query(f"SELECT {PUBLIC_COLS} FROM users ORDER BY user_id")

    def find(self, user_id: int) -> dict:
        row = get_db().one(f"SELECT {PUBLIC_COLS} FROM users WHERE user_id = ?", (user_id,))
        if not row:
            raise ServiceError("User not found.")
        return row

    def create(self, data: dict, user_id, username) -> dict:
        db = get_db()
        if db.one("SELECT user_id FROM users WHERE username = ?", (data["username"],)):
            raise ServiceError("Username already exists.")
        if data["role"] not in ROLES:
            raise ServiceError("Role must be one of: " + ", ".join(ROLES) + ".")
        status = data.get("status") or "Active"
        if status not in STATUSES:
            raise ServiceError("Status must be Active or Inactive.")
        try:
            new_id = db.insert(
                "INSERT INTO users (name, username, password_hash, role, status, email, phone) VALUES (?,?,?,?,?,?,?)",
                (data["name"], data["username"], hash_password(str(data["password"])), data["role"], status,
                 data.get("email"), data.get("phone")),
            )
        except sqlite3.IntegrityError as exc:
            raise ServiceError("Username already exists.") from exc
        logger.info("Admin", "USER_CREATED", f'User "{data["username"]}" created with role {data["role"]}', user_id, username)
        return self.find(new_id)

    def update_status(self, target_id: int, status: str, user_id, username) -> dict:
        if status not in STATUSES:
            raise ServiceError("Status must be Active or Inactive.")
        self.find(target_id)
        get_db().execute("UPDATE users SET status = ? WHERE user_id = ?", (status, target_id))
        logger.info("Admin", "USER_UPDATED", f"User #{target_id} status set to {status}", user_id, username)
        return self.find(target_id)

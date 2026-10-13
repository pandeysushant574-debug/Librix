from .. import logger
from ..db import get_db
from ..helpers import ServiceError
from ..security import verify_password


class AuthService:
    def login(self, username: str, password: str) -> dict:
        db = get_db()
        user = db.one("SELECT * FROM users WHERE username = ? LIMIT 1", (username,))
        if not user or user["status"] != "Active" or not verify_password(password, user["password_hash"]):
            logger.warning("Auth", "LOGIN_FAILED", f'Invalid credentials for username "{username}"')
            raise ServiceError("Invalid username or password.")
        logger.info("Auth", "LOGIN_SUCCESS", f"User {username} logged in", user["user_id"], username)
        return {"user_id": user["user_id"], "name": user["name"], "username": user["username"], "role": user["role"]}

    def logout(self, session) -> None:
        username = session.get("username") if session else None
        user_id = session.get("user_id") if session else None
        logger.info("Auth", "LOGOUT", f"User {username or 'unknown'} logged out", user_id, username)

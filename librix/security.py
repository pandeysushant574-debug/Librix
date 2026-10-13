"""Password hashing (PBKDF2-SHA256, standard library) and server-side sessions."""
import hashlib
import hmac
import os
import secrets
import threading
import time

from . import config

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


class SessionStore:
    """In-memory sessions: token -> {user_id, username, role, name}. Cleared when the server restarts."""

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def create(self, user: dict) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._data[token] = {**user, "_seen": time.time()}
        return token

    def get(self, token):
        if not token:
            return None
        with self._lock:
            sess = self._data.get(token)
            if not sess:
                return None
            if time.time() - sess["_seen"] > config.SESSION_TTL_SECONDS:
                del self._data[token]
                return None
            sess["_seen"] = time.time()
            return {k: v for k, v in sess.items() if not k.startswith("_")}

    def destroy(self, token):
        with self._lock:
            self._data.pop(token, None)


sessions = SessionStore()

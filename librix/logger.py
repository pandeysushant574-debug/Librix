"""system_logs and audit_logs writers. Logging must never break the request that triggered it."""
import json
import sys

from .db import get_db


def log(module, action, level, message, result=None, details=None, user_id=None, username=None):
    try:
        get_db().execute(
            "INSERT INTO system_logs (user_id, username, module, action, level, message, result, details) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, module, action, level.upper(), message, result, details),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Logger.log failed: {exc}", file=sys.stderr)


def info(module, action, message, user_id=None, username=None, result="SUCCESS", details=None):
    log(module, action, "INFO", message, result, details, user_id, username)


def warning(module, action, message, user_id=None, username=None, details=None):
    log(module, action, "WARNING", message, "WARNING", details, user_id, username)


def error(module, action, message, user_id=None, username=None, details=None):
    log(module, action, "ERROR", message, "FAILED", details, user_id, username)


def debug(module, action, message, user_id=None, username=None, details=None):
    log(module, action, "DEBUG", message, "SUCCESS", details, user_id, username)


def audit(action, entity_type, entity_id, old_value, new_value, user_id=None, username=None):
    """WHO / WHAT / OLD VALUE / NEW VALUE / WHEN."""
    try:
        enc = lambda v: None if v is None else json.dumps(v, separators=(",", ":"), default=str)  # noqa: E731
        get_db().execute(
            "INSERT INTO audit_logs (user_id, username, action, entity_type, entity_id, old_value, new_value) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, action, entity_type, entity_id, enc(old_value), enc(new_value)),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Audit.record failed: {exc}", file=sys.stderr)

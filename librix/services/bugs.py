from .. import logger
from ..db import get_db
from ..helpers import ServiceError, next_code, today
from ..validators import BugValidator


class BugService:
    def all(self, filters=None) -> list:
        filters = filters or {}
        sql = "SELECT * FROM bug_logs WHERE 1=1"
        params = []
        for key in ("status", "severity", "module"):
            if filters.get(key):
                sql += f" AND {key} = ?"
                params.append(filters[key])
        sql += " ORDER BY reported_date DESC, bug_id DESC"
        return get_db().query(sql, params)

    def counters(self) -> dict:
        row = get_db().one(
            "SELECT COUNT(*) AS total, SUM(status='Open') AS open_count, SUM(severity='Critical') AS critical_count, "
            "SUM(priority='High') AS high_priority_count, SUM(status='Fixed') AS fixed_count, "
            "SUM(status='Retest') AS retest_count, SUM(status='Closed') AS closed_count FROM bug_logs"
        )
        return {k: int(v or 0) for k, v in row.items()}

    def find(self, bug_id: int) -> dict:
        row = get_db().one("SELECT * FROM bug_logs WHERE bug_id = ?", (bug_id,))
        if not row:
            raise ServiceError("Bug not found.")
        return row

    def create(self, data: dict, user_id, username) -> dict:
        db = get_db()
        code = next_code(db, "bug_logs", "bug_code", "BUG")
        bug_id = db.insert(
            "INSERT INTO bug_logs (bug_code, reported_date, module, title, description, severity, priority, status, assigned_to, reported_by) "
            "VALUES (?,?,?,?,?,?,?, 'Open', ?, ?)",
            (code, data["reported_date"], data["module"], data["title"], data["description"], data["severity"],
             data["priority"], data.get("assigned_to") or None, user_id),
        )
        logger.info("Bugs", "BUG_CREATED", f"Bug {code} reported: {data['title']}", user_id, username)
        return self.find(bug_id)

    def update(self, bug_id: int, data: dict, user_id, username) -> dict:
        db = get_db()
        existing = self.find(bug_id)

        new_status = data.get("status") if data.get("status") is not None else existing["status"]
        if new_status != existing["status"]:
            if not BugValidator.is_valid_status(new_status):
                raise ServiceError("Invalid status.")
            if not BugValidator.can_transition(existing["status"], new_status):
                raise ServiceError(f"Cannot move bug from '{existing['status']}' to '{new_status}'.")

        closed_date = existing["closed_date"]
        if new_status == "Closed" and existing["status"] != "Closed":
            closed_date = data.get("closed_date") or today()
        if new_status != "Closed":
            closed_date = None

        pick = lambda key: data[key] if key in data and data[key] is not None else existing[key]  # noqa: E731
        db.execute(
            "UPDATE bug_logs SET module=?, title=?, description=?, severity=?, priority=?, status=?, assigned_to=?, "
            "root_cause=?, fix_action=?, retest_result=?, closed_date=? WHERE bug_id=?",
            (pick("module"), pick("title"), pick("description"), pick("severity"), pick("priority"), new_status,
             pick("assigned_to") or None, pick("root_cause"), pick("fix_action"), pick("retest_result"), closed_date, bug_id),
        )

        if new_status != existing["status"]:
            action = {"Fixed": "BUG_FIXED", "Retest": "BUG_RETESTED", "Closed": "BUG_CLOSED"}.get(new_status, "BUG_UPDATED")
            logger.info("Bugs", action, f"{existing['bug_code']}: {existing['status']} -> {new_status}", user_id, username)
        else:
            logger.info("Bugs", "BUG_UPDATED", f"{existing['bug_code']} updated", user_id, username)
        return self.find(bug_id)

    def delete(self, bug_id: int) -> None:
        get_db().execute("DELETE FROM bug_logs WHERE bug_id = ?", (bug_id,))

from ..db import get_db


class LogService:
    def all(self, filters=None, limit: int = 200) -> list:
        filters = filters or {}
        sql = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        if filters.get("level"):
            sql += " AND level = ?"
            params.append(filters["level"])
        if filters.get("module"):
            sql += " AND module = ?"
            params.append(filters["module"])
        if filters.get("q"):
            sql += " AND (message LIKE ? OR action LIKE ?)"
            like = f"%{filters['q']}%"
            params += [like, like]
        sql += f" ORDER BY timestamp DESC, log_id DESC LIMIT {int(limit)}"
        return get_db().query(sql, params)

    def counters(self) -> dict:
        row = get_db().one(
            "SELECT SUM(date(timestamp) = date('now','localtime')) AS today, SUM(level='WARNING') AS warnings, "
            "SUM(level='ERROR') AS errors, SUM(level='DEBUG') AS debug FROM system_logs"
        )
        return {k: int(v or 0) for k, v in row.items()}

    def audit_logs(self, limit: int = 200) -> list:
        return get_db().query(f"SELECT * FROM audit_logs ORDER BY timestamp DESC, audit_id DESC LIMIT {int(limit)}")

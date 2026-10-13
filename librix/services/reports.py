from ..db import get_db
from ..helpers import money

LATEST_RESULTS = "result_id IN (SELECT MAX(result_id) FROM test_results GROUP BY test_case_id)"


def _ints(row: dict) -> dict:
    return {k: int(v or 0) for k, v in row.items()}


class ReportService:
    def dashboard(self) -> dict:
        db = get_db()
        books = db.one("SELECT COUNT(*) AS total, SUM(available_qty) AS available, SUM(quantity - available_qty) AS issued FROM books")
        members = db.one("SELECT COUNT(*) AS active FROM members WHERE status = 'Active'")
        tests = db.one(f"SELECT COUNT(*) AS total, SUM(status='PASS') AS passed, SUM(status='FAIL') AS failed FROM test_results tr WHERE {LATEST_RESULTS}")
        bugs = db.one("SELECT SUM(status='Open') AS open_count, SUM(severity='Critical') AS critical, SUM(status='Fixed') AS fixed, SUM(status='Closed') AS closed FROM bug_logs")
        logs = db.one("SELECT SUM(date(timestamp) = date('now','localtime')) AS today, SUM(level='WARNING') AS warnings, SUM(level='ERROR') AS errors FROM system_logs")

        recent_issues = db.query(
            "SELECT i.issue_id, b.title, m.name AS member_name, i.issue_date, i.status FROM issues i "
            "JOIN books b ON b.book_id=i.book_id JOIN members m ON m.member_id=i.member_id ORDER BY i.issue_id DESC LIMIT 5")
        recent_failed = db.query(
            "SELECT tr.result_id, tc.test_code, tc.title, tr.executed_at FROM test_results tr "
            "JOIN test_cases tc ON tc.test_case_id = tr.test_case_id WHERE tr.status IN ('FAIL','ERROR') "
            "ORDER BY tr.executed_at DESC, tr.result_id DESC LIMIT 5")
        recent_bugs = db.query("SELECT bug_id, bug_code, title, severity, status FROM bug_logs ORDER BY bug_id DESC LIMIT 5")
        recent_errors = db.query(
            "SELECT log_id, module, action, message, timestamp FROM system_logs WHERE level='ERROR' "
            "ORDER BY timestamp DESC, log_id DESC LIMIT 5")

        total = int(tests["total"] or 0)
        passed = int(tests["passed"] or 0)
        pass_rate = round(passed / total * 100, 1) if total > 0 else 0
        return {
            "books": {"total": int(books["total"] or 0), "available": int(books["available"] or 0), "issued": int(books["issued"] or 0)},
            "members": {"active": int(members["active"] or 0)},
            "testing": {"total": total, "passed": passed, "failed": int(tests["failed"] or 0), "pass_rate": pass_rate},
            "bugs": _ints(bugs),
            "logs": _ints(logs),
            "recent": {"issues": recent_issues, "failed_tests": recent_failed, "bugs": recent_bugs, "errors": recent_errors},
        }

    def testing_report(self) -> dict:
        db = get_db()
        unit = db.one(f"SELECT COUNT(*) AS total, SUM(status='PASS') AS passed, SUM(status='FAIL') AS failed FROM test_results tr WHERE {LATEST_RESULTS}")
        boundary = db.one("SELECT COUNT(*) AS total, SUM(status='PASS') AS passed, SUM(status='FAIL') AS failed FROM boundary_tests")
        unit_total, boundary_total = int(unit["total"] or 0), int(boundary["total"] or 0)
        return {
            "unit": {"total": unit_total, "passed": int(unit["passed"] or 0), "failed": int(unit["failed"] or 0),
                     "pass_rate": round(int(unit["passed"] or 0) / unit_total * 100, 1) if unit_total else 0},
            "boundary": {"total": boundary_total, "passed": int(boundary["passed"] or 0), "failed": int(boundary["failed"] or 0),
                         "coverage": round(boundary_total / 6 * 100, 1) if boundary_total else 0},  # 6 fields in the spec matrix
        }

    def bug_report(self) -> dict:
        row = get_db().one("SELECT COUNT(*) AS total, SUM(severity='Critical') AS critical, SUM(status='Open') AS open_count, "
                           "SUM(status='Fixed') AS fixed, SUM(status='Closed') AS closed FROM bug_logs")
        return _ints(row)

    def library_report(self) -> list:
        return get_db().query("SELECT book_id, title, author, category, quantity, available_qty, status FROM books ORDER BY title COLLATE NOCASE")

    def issue_report(self) -> list:
        rows = get_db().query(
            "SELECT i.issue_id, b.title, m.name AS member_name, i.issue_date, i.due_date, i.return_date, i.status, i.fine_amount "
            "FROM issues i JOIN books b ON b.book_id=i.book_id JOIN members m ON m.member_id=i.member_id "
            "ORDER BY i.issue_date DESC, i.issue_id DESC")
        for r in rows:
            r["fine_amount"] = money(r["fine_amount"])
        return rows

    def fine_report(self) -> list:
        rows = get_db().query(
            "SELECT f.fine_id, m.name AS member_name, f.days_late, f.rate_per_day, f.amount, f.status, f.created_at "
            "FROM fines f JOIN members m ON m.member_id=f.member_id ORDER BY f.created_at DESC, f.fine_id DESC")
        for r in rows:
            r["rate_per_day"] = money(r["rate_per_day"])
            r["amount"] = money(r["amount"])
        return rows

    def system_log_report(self) -> list:
        return get_db().query("SELECT level, COUNT(*) AS count FROM system_logs GROUP BY level")

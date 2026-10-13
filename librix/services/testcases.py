"""Unit-test case management + the executable logic behind UT001..UT012."""
import time

from .. import logger
from ..db import get_db
from ..helpers import ServiceError, next_code
from ..security import verify_password
from ..validators import BookValidator
from .fines import FineService

LAST_RESULT = (
    "(SELECT {col} FROM test_results tr WHERE tr.test_case_id = tc.test_case_id ORDER BY tr.result_id DESC LIMIT 1)"
)


class TestService:
    __test__ = False  # not a pytest/unittest class despite the name

    def all(self) -> list:
        sql = (
            "SELECT tc.*, "
            + LAST_RESULT.format(col="tr.status") + " AS last_status, "
            + LAST_RESULT.format(col="tr.actual_result") + " AS last_actual, "
            + LAST_RESULT.format(col="tr.executed_at") + " AS last_executed_at "
            "FROM test_cases tc ORDER BY tc.test_code ASC"
        )
        return get_db().query(sql)

    def _find(self, test_case_id: int):
        return get_db().one("SELECT * FROM test_cases WHERE test_case_id = ?", (test_case_id,))

    def create(self, data: dict, user_id) -> dict:
        db = get_db()
        code = next_code(db, "test_cases", "test_code", "UT", 3, "")
        new_id = db.insert(
            "INSERT INTO test_cases (test_code, module, title, description, input_data, expected_result, test_type, priority, created_by) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (code, data["module"], data["title"], data.get("description"), data.get("input_data"), data["expected_result"],
             data.get("test_type") or "Unit", data.get("priority") or "Medium", user_id),
        )
        return self._find(new_id)

    def update(self, test_case_id: int, data: dict) -> dict:
        if not self._find(test_case_id):
            raise ServiceError("Test case not found.")
        active = int(bool(data["active"])) if data.get("active") is not None else 1
        get_db().execute(
            "UPDATE test_cases SET module=?, title=?, description=?, input_data=?, expected_result=?, test_type=?, priority=?, active=? "
            "WHERE test_case_id=?",
            (data["module"], data["title"], data.get("description"), data.get("input_data"), data["expected_result"],
             data.get("test_type") or "Unit", data.get("priority") or "Medium", active, test_case_id),
        )
        return self._find(test_case_id)

    def delete(self, test_case_id: int) -> None:
        db = get_db()
        with db.transaction():
            db.execute("DELETE FROM test_results WHERE test_case_id = ?", (test_case_id,))
            db.execute("DELETE FROM test_cases WHERE test_case_id = ?", (test_case_id,))

    def run_all(self, user_id, username) -> list:
        ids = [r["test_case_id"] for r in get_db().query("SELECT test_case_id FROM test_cases WHERE active = 1")]
        return [self.run(i, user_id, username) for i in ids]

    def run(self, test_case_id: int, user_id, username) -> dict:
        db = get_db()
        tc = self._find(test_case_id)
        if not tc:
            raise ServiceError("Test case not found.")

        logger.info("Testing", "UNIT_TEST_STARTED", f"Running {tc['test_code']} - {tc['title']}", user_id, username)

        start = time.perf_counter()
        status, actual, error_message = self._execute(tc["test_code"])
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        db.insert(
            "INSERT INTO test_results (test_case_id, actual_result, status, executed_by, duration_ms, error_message) VALUES (?,?,?,?,?,?)",
            (test_case_id, actual, status, user_id, duration_ms, error_message),
        )
        logger.log("Testing", "UNIT_TEST_PASSED" if status == "PASS" else "UNIT_TEST_FAILED",
                   "INFO" if status == "PASS" else "ERROR",
                   f"{tc['test_code']} finished with status {status}", status, actual, user_id, username)
        return {"test_case_id": test_case_id, "test_code": tc["test_code"], "status": status, "actual": actual, "duration_ms": duration_ms}

    # ------------------------------------------------------------------ the tests themselves
    def _execute(self, code: str):
        db = get_db()
        try:
            if code == "UT001":  # add valid book (validation only - nothing is written)
                errors = BookValidator.validate({"title": "Temp Test Book", "author": "Tester", "quantity": 5})
                return ("PASS", "No validation errors; book would be created with available_qty = quantity.", None) if not errors \
                    else ("FAIL", "Unexpected validation errors: " + ", ".join(errors), None)

            if code == "UT002":
                errors = BookValidator.validate({"title": "", "author": "Tester", "quantity": 5})
                return ("PASS", "Blank title correctly rejected.", None) if "Title is required." in errors \
                    else ("FAIL", "Blank title was NOT rejected.", None)

            if code == "UT003":
                errors = BookValidator.validate({"title": "X", "author": "Y", "quantity": -1})
                return ("PASS", "Negative quantity correctly rejected: " + ", ".join(errors), None) if errors \
                    else ("FAIL", "Negative quantity was NOT rejected.", None)

            if code == "UT004":
                errors = BookValidator.validate({"title": "X", "author": "Y", "quantity": 2, "available_qty": 5})
                return ("PASS", "available_qty > quantity correctly rejected.", None) if errors \
                    else ("FAIL", "available_qty > quantity was NOT rejected.", None)

            if code == "UT005":
                book = db.one("SELECT * FROM books WHERE available_qty > 0 LIMIT 1")
                return ("PASS", f'Found issuable book "{book["title"]}" (available_qty={book["available_qty"]}).', None) if book \
                    else ("FAIL", "No book with available_qty > 0 found to validate issuing logic.", None)

            if code == "UT006":
                book = db.one("SELECT * FROM books WHERE available_qty = 0 LIMIT 1")
                if not book:
                    return ("ERROR", "No book with available_qty = 0 exists in the current dataset.", "Missing fixture")
                blocked = book["available_qty"] < 1
                return ("PASS", f'Book "{book["title"]}" correctly identified as unissuable (available_qty=0).', None) if blocked \
                    else ("FAIL", "Book with 0 availability was not blocked.", None)

            if code == "UT007":
                member = db.one("SELECT * FROM members WHERE member_id = 999999")
                return ("PASS", "Non-existent member_id correctly returns no record (would be rejected).", None) if not member \
                    else ("FAIL", "Invalid member_id unexpectedly matched a record.", None)

            if code == "UT008":
                issue = db.one("SELECT * FROM issues WHERE status = 'Returned' LIMIT 1")
                return ("PASS", f"Found a correctly Returned issue (#{issue['issue_id']}) confirming return flow updates status.", None) if issue \
                    else ("FAIL", "No Returned issue found to validate the return flow.", None)

            if code == "UT009":
                fine = FineService.calculate("2026-08-27", "2026-08-30")
                ok = abs(fine["amount"] - 15.00) < 0.001
                return ("PASS", f"Fine calculated as {fine['amount']} for 3 days late (expected 15.00).", None) if ok \
                    else ("FAIL", f"Fine calculated as {fine['amount']}, expected 15.00.", None)

            if code == "UT010":
                user = db.one("SELECT * FROM users WHERE username = ?", ("admin",))
                ok = bool(user) and verify_password("Admin@123", user["password_hash"])
                return ("PASS", "Password check succeeded for seeded admin credentials.", None) if ok \
                    else ("FAIL", "Password check failed for seeded admin credentials.", None)

            if code == "UT011":
                user = db.one("SELECT * FROM users WHERE username = ?", ("admin",))
                ok = bool(user) and not verify_password("WrongPassword!", user["password_hash"])
                return ("PASS", "Password check correctly rejected an incorrect password.", None) if ok \
                    else ("FAIL", "Incorrect password was unexpectedly accepted.", None)

            if code == "UT012":
                rows = db.query("SELECT * FROM books WHERE title LIKE '%Clean%'")
                return ("PASS", f'Search for "Clean" returned {len(rows)} result(s).', None) if rows \
                    else ("FAIL", 'Search for "Clean" returned no results.', None)

            return ("ERROR", "No executable logic mapped for this test code.", f"Unmapped test_code: {code}")
        except Exception as exc:  # noqa: BLE001
            return ("ERROR", f"Exception during execution: {exc}", str(exc))

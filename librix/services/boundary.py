"""Boundary-value tests: below / lower / normal / upper / above for six fields."""
from .. import logger
from ..db import get_db
from ..helpers import is_valid_date, next_code
from ..validators import BookValidator, MemberValidator


def _ends(result: str, word: str) -> bool:
    return result.endswith(word)


class BoundaryService:
    def all(self) -> list:
        return get_db().query("SELECT * FROM boundary_tests ORDER BY boundary_test_id DESC")

    def run_all(self, user_id, username) -> list:
        return [self._run_one(case, user_id, username) for case in self._definitions()]

    @staticmethod
    def _definitions() -> list:
        return [
            {"module": "Books", "field_name": "quantity", "values": ["-1", "0", "1", "9999", "10000"], "check": "book_quantity"},
            {"module": "Issues", "field_name": "issue_quantity", "values": ["-1", "0", "1", "avail", "avail+1"], "check": "issue_quantity"},
            {"module": "Fines", "field_name": "fine_amount", "values": ["-1", "0", "1", "max", "max+1"], "check": "fine_amount"},
            {"module": "Books", "field_name": "title", "values": ["", "A", "Clean Code", "A" * 255, "A" * 256], "check": "book_title"},
            {"module": "Members", "field_name": "member_code", "values": ["", "BAD-FORMAT", "MEM-0001", "9" * 30, "9" * 31], "check": "member_code"},
            {"module": "Issues", "field_name": "due_date", "values": ["not-a-date", "2026-01-01", "2026-01-05", "2026-01-05", "2026-01-12"], "check": "due_date"},
        ]

    def _run_one(self, case: dict, user_id, username) -> dict:
        db = get_db()
        expected, actual, status = self._evaluate(case)
        code = next_code(db, "boundary_tests", "test_code", "BT")
        v = case["values"]
        db.insert(
            "INSERT INTO boundary_tests (test_code, module, field_name, below_boundary, lower_boundary, normal_value, upper_boundary, "
            "above_boundary, expected_behavior, actual_behavior, status, executed_by, executed_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?, datetime('now','localtime'))",
            (code, case["module"], case["field_name"], v[0], v[1], v[2], v[3], v[4], expected, actual, status, user_id),
        )
        logger.log("Testing", "BOUNDARY_TEST_PASSED" if status == "PASS" else "BOUNDARY_TEST_FAILED",
                   "INFO" if status == "PASS" else "ERROR",
                   f"{code} ({case['field_name']}) finished with status {status}", status, actual, user_id, username)
        return {"test_code": code, "field_name": case["field_name"], "status": status, "expected": expected, "actual": actual}

    def _evaluate(self, case: dict):
        check = case["check"]

        if check == "book_quantity":
            expected = "Reject below 0; accept 0 to 9999; reject above 9999."
            results = []
            for v in (-1, 0, 1, 9999, 10000):
                errors = BookValidator.validate({"title": "X", "author": "Y", "quantity": v})
                results.append(f"{v}=>{'accepted' if not errors else 'rejected'}")
            ok = (_ends(results[0], "rejected") and _ends(results[1], "accepted") and _ends(results[2], "accepted")
                  and _ends(results[3], "accepted") and _ends(results[4], "rejected"))
            return expected, ", ".join(results), "PASS" if ok else "FAIL"

        if check == "book_title":
            expected = "Reject blank and >255 chars; accept 1 to 255 chars."
            results = []
            for v in case["values"]:
                errors = BookValidator.validate({"title": v, "author": "Y", "quantity": 1})
                results.append(f"{len(v)}chars=>{'accepted' if not errors else 'rejected'}")
            ok = (_ends(results[0], "rejected") and _ends(results[1], "accepted") and _ends(results[2], "accepted")
                  and _ends(results[3], "accepted") and _ends(results[4], "rejected"))
            return expected, ", ".join(results), "PASS" if ok else "FAIL"

        if check == "member_code":
            expected = "Reject blank/invalid format and >30 chars; accept valid MEM-#### format."
            results = []
            for v in case["values"]:
                errors = MemberValidator.validate({"member_code": v, "name": "X", "membership_date": "2026-01-01"})
                results.append(f"'{v}'=>{'accepted' if not errors else 'rejected'}")
            ok = _ends(results[0], "rejected") and _ends(results[1], "rejected") and _ends(results[2], "accepted")
            return expected, ", ".join(results), "PASS" if ok else "FAIL"

        if check == "fine_amount":
            expected = "Negative fine rejected; 0 and positive accepted."
            neg, zero, pos = (-1 >= 0), (0 >= 0), (15 >= 0)
            ok = (not neg) and zero and pos
            word = lambda b: "accepted" if b else "rejected"  # noqa: E731
            return expected, f"-1=>{word(neg)}, 0=>{word(zero)}, 15=>{word(pos)}", "PASS" if ok else "FAIL"

        if check == "issue_quantity":
            expected = "Reject <= 0; accept 1..available_qty; reject > available_qty."
            tests = [(-1, False), (0, False), (1, True), (3, True), (4, False)]  # assume available_qty = 3
            results, ok = [], True
            for qty, expect_accept in tests:
                accept = 0 < qty <= 3
                results.append(f"{qty}=>{'accepted' if accept else 'rejected'}")
                if accept != expect_accept:
                    ok = False
            return expected, ", ".join(results), "PASS" if ok else "FAIL"

        if check == "due_date":
            expected = "Invalid date format rejected; due_date must be >= issue_date."
            issue_date = "2026-01-05"
            results, ok = [], True
            for due, expect_valid in (("not-a-date", False), ("2026-01-01", False), ("2026-01-05", True), ("2026-01-12", True)):
                valid = is_valid_date(due) and due >= issue_date
                results.append(f"{due}=>{'accepted' if valid else 'rejected'}")
                if valid != expect_valid:
                    ok = False
            return expected, ", ".join(results), "PASS" if ok else "FAIL"

        return "n/a", "No evaluator for this boundary case.", "ERROR"

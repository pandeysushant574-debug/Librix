"""Input validators. They return a list of error strings (empty list == valid)."""
import re

from .helpers import is_numeric, is_valid_date, text, to_int, is_empty


class BookValidator:
    TITLE_MAX_LEN = 255
    QTY_MIN = 0
    QTY_MAX = 9999

    @classmethod
    def validate(cls, data: dict, is_update: bool = False) -> list:
        errors = []

        title = text(data.get("title"))
        if title == "":
            errors.append("Title is required.")
        elif len(title) > cls.TITLE_MAX_LEN:
            errors.append(f"Title must be at most {cls.TITLE_MAX_LEN} characters.")

        if text(data.get("author")) == "":
            errors.append("Author is required.")

        if "quantity" not in data or not is_numeric(data["quantity"]):
            errors.append("Quantity is required and must be numeric.")
        elif to_int(data["quantity"]) < cls.QTY_MIN or to_int(data["quantity"]) > cls.QTY_MAX:
            errors.append(f"Quantity must be between {cls.QTY_MIN} and {cls.QTY_MAX}.")

        if "available_qty" in data:
            if not is_numeric(data["available_qty"]) or to_int(data["available_qty"]) < 0:
                errors.append("Available quantity must be a non-negative number.")
            elif is_numeric(data.get("quantity")) and to_int(data["available_qty"]) > to_int(data["quantity"]):
                errors.append("Available quantity cannot exceed total quantity.")

        if "reorder_level" in data and data["reorder_level"] not in ("", None):
            if not is_numeric(data["reorder_level"]) or to_int(data["reorder_level"]) < 0:
                errors.append("Reorder level must be a non-negative number.")

        return errors


class MemberValidator:
    CODE_MAX_LEN = 30
    CODE_PATTERN = re.compile(r"^MEM-\d{4,}$")
    _EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")

    @classmethod
    def validate(cls, data: dict) -> list:
        errors = []

        code = text(data.get("member_code"))
        if code == "":
            errors.append("Member code is required.")
        elif len(code) > cls.CODE_MAX_LEN:
            errors.append(f"Member code must be at most {cls.CODE_MAX_LEN} characters.")
        elif not cls.CODE_PATTERN.match(code):
            errors.append("Member code must match the format MEM-0001.")

        if text(data.get("name")) == "":
            errors.append("Name is required.")

        email = text(data.get("email"))
        if email != "" and not cls._EMAIL.match(email):
            errors.append("Email address is invalid.")

        membership_date = data.get("membership_date") or ""
        if membership_date == "":
            errors.append("Membership date is required.")
        elif not is_valid_date(membership_date):
            errors.append("Membership date must be a valid date (YYYY-MM-DD).")

        return errors


class IssueValidator:
    @staticmethod
    def validate(data: dict) -> list:
        errors = []
        if is_empty(data.get("book_id")) or not is_numeric(data.get("book_id")):
            errors.append("A valid book is required.")
        if is_empty(data.get("member_id")) or not is_numeric(data.get("member_id")):
            errors.append("A valid member is required.")
        if not is_empty(data.get("quantity")) and to_int(data["quantity"]) <= 0:
            errors.append("Issue quantity must be greater than 0.")
        if is_empty(data.get("issue_date")) or not is_valid_date(data.get("issue_date")):
            errors.append("A valid issue date is required.")
        if is_empty(data.get("due_date")) or not is_valid_date(data.get("due_date")):
            errors.append("A valid due date is required.")
        if (not is_empty(data.get("issue_date")) and not is_empty(data.get("due_date"))
                and is_valid_date(data["issue_date"]) and is_valid_date(data["due_date"])):
            if data["due_date"] < data["issue_date"]:
                errors.append("Due date must be on or after the issue date.")
        return errors

    @staticmethod
    def validate_return(data: dict) -> list:
        errors = []
        if is_empty(data.get("issue_id")) or not is_numeric(data.get("issue_id")):
            errors.append("A valid issue is required.")
        if is_empty(data.get("return_date")) or not is_valid_date(data.get("return_date")):
            errors.append("A valid return date is required.")
        return errors


class TestValidator:
    __test__ = False
    ALLOWED_TYPES = ["Unit", "Functional", "Regression"]

    @classmethod
    def validate(cls, data: dict) -> list:
        errors = []
        if text(data.get("module")) == "":
            errors.append("Module is required.")
        if text(data.get("title")) == "":
            errors.append("Title is required.")
        if text(data.get("expected_result")) == "":
            errors.append("Expected result is required.")
        if not is_empty(data.get("test_type")) and data["test_type"] not in cls.ALLOWED_TYPES:
            errors.append("Invalid test type.")
        return errors


class BugValidator:
    SEVERITIES = ["Critical", "High", "Medium", "Low"]
    PRIORITIES = ["High", "Medium", "Low"]
    STATUSES = ["Open", "In Progress", "Fixed", "Retest", "Closed"]
    ALLOWED_TRANSITIONS = {
        "Open": ["In Progress"],
        "In Progress": ["Fixed"],
        "Fixed": ["Retest"],
        "Retest": ["Closed", "In Progress"],
        "Closed": [],
    }

    @classmethod
    def validate(cls, data: dict) -> list:
        errors = []
        if text(data.get("module")) == "":
            errors.append("Module is required.")
        if text(data.get("title")) == "":
            errors.append("Title is required.")
        if text(data.get("description")) == "":
            errors.append("Description is required.")
        if is_empty(data.get("severity")) or data["severity"] not in cls.SEVERITIES:
            errors.append("A valid severity is required.")
        if is_empty(data.get("priority")) or data["priority"] not in cls.PRIORITIES:
            errors.append("A valid priority is required.")
        if is_empty(data.get("reported_date")) or not is_valid_date(data.get("reported_date")):
            errors.append("A valid reported date is required.")
        return errors

    @classmethod
    def can_transition(cls, current: str, new: str) -> bool:
        if current == new:
            return True
        return new in cls.ALLOWED_TRANSITIONS.get(current, [])

    @classmethod
    def is_valid_status(cls, status: str) -> bool:
        return status in cls.STATUSES

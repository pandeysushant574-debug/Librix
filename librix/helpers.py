"""Small shared helpers: API errors, PHP-compatible value semantics, code generation, dates."""
import re
from datetime import date, datetime


class ApiError(Exception):
    """Raised anywhere in controllers/services to produce a JSON error response."""

    def __init__(self, message: str, status: int = 400, errors=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors


class ServiceError(Exception):
    """A business-rule failure raised by services (controllers translate it to a 404/409)."""


# --------------------------------------------------------------------------
# Value helpers. The original backend relied on PHP's loose typing; these keep
# the exact same validation behaviour for strings/numbers coming from JSON.
# --------------------------------------------------------------------------
_NUMERIC_RE = re.compile(r"^\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?\s*$")


def is_numeric(v) -> bool:
    if isinstance(v, bool) or v is None:
        return False
    if isinstance(v, (int, float)):
        return v == v and v not in (float("inf"), float("-inf"))
    return isinstance(v, str) and bool(_NUMERIC_RE.match(v))


def to_int(v) -> int:
    """PHP-style (int) cast: '5' -> 5, '5.9' -> 5, None/'' -> 0."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        m = re.match(r"^\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", v)
        return int(float(m.group(0))) if m else 0
    return 0


def is_empty(v) -> bool:
    """PHP empty(): None, '', '0', 0, 0.0, False, [] and {} are all 'empty'."""
    return v is None or v is False or v == 0 or v == "" or v == "0" or v == [] or v == {}


def text(v) -> str:
    """trim() that tolerates None / numbers."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else ""
    return str(v).strip()


def is_valid_date(value) -> bool:
    if not value or not isinstance(value, str):
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d") == value
    except ValueError:
        return False


def today() -> str:
    return date.today().isoformat()


def money(value) -> str:
    """DECIMAL(10,2) columns are returned as '15.00' strings, exactly like the MySQL/PDO build did."""
    return f"{float(value or 0):.2f}"


def next_code(db, table: str, column: str, prefix: str, pad: int = 3, sep: str = "-") -> str:
    """Next sequential code, e.g. BUG-006, or UT013 with sep=''. Uses the highest NUMBER among
    codes shaped like PREFIX-123 / PREFIX123 so unrelated seeded codes can't cause duplicates."""
    pattern = re.compile("^" + re.escape(prefix) + r"-?(\d+)$")
    highest = 0
    for row in db.query(f"SELECT {column} AS c FROM {table}"):
        m = pattern.match(str(row["c"]))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"{prefix}{sep}{str(highest + 1).zfill(pad)}"

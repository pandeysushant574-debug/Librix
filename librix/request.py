"""Request / Result objects shared by the router and the controllers."""
from .helpers import ApiError, is_empty


class Result:
    """A successful API response (always rendered as {"success": true, "message", "data"})."""

    def __init__(self, data=None, message: str = "OK", status: int = 200, cookies=None):
        self.data = [] if data is None else data
        self.message = message
        self.status = status
        self.cookies = cookies or []  # list of raw Set-Cookie header values


class RootResult(Result):
    """GET /api -> the friendly 'API is up' message."""
    root = True

    def __init__(self):
        super().__init__([], "Library Management System API")


def success(data=None, message: str = "OK", status: int = 200) -> Result:
    return Result(data, message, status)


class Request:
    def __init__(self, method, path, query, body, session, cookies):
        self.method = method
        self.path = path
        self.query = query          # dict[str, str] (first value of every key)
        self.body = body            # dict (decoded JSON object, {} when absent/invalid)
        self.session = session      # dict | None
        self.cookies = cookies      # dict[str, str]

    # --- middleware equivalents -------------------------------------------------
    def require_auth(self) -> dict:
        """AuthMiddleware::check()"""
        if not self.session:
            raise ApiError("Unauthorized. Please log in.", 401)
        return self.session

    def require_role(self, *roles) -> dict:
        """AuthMiddleware::check() + RoleMiddleware::allow()"""
        session = self.require_auth()
        role = session.get("role")
        if not role or role not in roles:
            raise ApiError(f"Forbidden. Your role ({role or 'none'}) cannot access this resource.", 403)
        return session

    def filters(self, *keys) -> dict:
        """Query-string filters with empty values dropped (PHP array_filter)."""
        return {k: self.query[k] for k in keys if k in self.query and not is_empty(self.query[k])}

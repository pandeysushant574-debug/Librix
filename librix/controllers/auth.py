from .. import config
from ..helpers import ApiError, ServiceError, text
from ..request import Result, success
from ..security import sessions
from ..services.auth import AuthService


class AuthController:
    def login(self, req) -> Result:
        username = text(req.body.get("username"))
        password = str(req.body.get("password") or "")
        if username == "" or password == "":
            raise ApiError("Username and password are required.", 422)
        try:
            user = AuthService().login(username, password)
        except ServiceError as exc:
            raise ApiError(str(exc), 401) from exc
        token = sessions.create(user)
        result = success(user, "Login successful.")
        result.cookies.append(f"{config.SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax")
        return result

    def logout(self, req) -> Result:
        AuthService().logout(req.session)
        sessions.destroy(req.cookies.get(config.SESSION_COOKIE))
        result = success([], "Logged out.")
        result.cookies.append(f"{config.SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
        return result

    def me(self, req) -> Result:
        if not req.session:
            raise ApiError("Not authenticated.", 401)
        s = req.session
        return success({"user_id": s["user_id"], "username": s["username"], "role": s["role"], "name": s["name"]})

"""Auth-service bridge for cross-service session validation."""

from dataclasses import dataclass

from flask import current_app


class AuthServiceUnavailable(RuntimeError):
    """Raised when the auth service validation endpoint cannot be reached."""


@dataclass(frozen=True)
class AuthenticatedSession:
    user_id: str
    rol: str


def validate_session_token(token: str | None) -> AuthenticatedSession | None:
    if not token:
        return None

    auth_app = current_app.config.get("AUTH_SERVICE_APP")
    if auth_app is None:
        raise AuthServiceUnavailable("AUTH_SERVICE_APP is not configured")

    client = auth_app.test_client()
    client.set_cookie(current_app.config["SESSION_COOKIE_NAME"], token)
    response = client.post("/internal/v1/sessions/validate")

    if response.status_code == 401:
        return None
    if response.status_code != 200:
        raise AuthServiceUnavailable(f"Auth validation failed with {response.status_code}")

    payload = response.get_json() or {}
    return AuthenticatedSession(user_id=payload["user_id"], rol=payload["rol"])

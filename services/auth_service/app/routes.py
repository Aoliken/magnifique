"""HTTP routes for the extracted auth service."""

from flask import Blueprint, current_app, jsonify, make_response, request

from app import db
from app.models import AuthSession, Usuario

auth_api_bp = Blueprint("auth_api", __name__)


def _session_cookie_name() -> str:
    return current_app.config["SESSION_COOKIE_NAME"]


def _read_session() -> AuthSession | None:
    token = request.cookies.get(_session_cookie_name())
    if not token:
        return None

    session = AuthSession.query.filter_by(token=token).first()
    if not session or not session.is_active():
        return None
    return session


def _expire_cookie(response):
    response.set_cookie(
        _session_cookie_name(),
        "",
        expires=0,
        httponly=True,
        path=current_app.config["SESSION_COOKIE_PATH"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        secure=current_app.config["SESSION_COOKIE_SECURE"],
    )
    return response


@auth_api_bp.post("/api/v1/auth/login")
def login():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    user = Usuario.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid_credentials"}), 401

    lifetime = current_app.config["AUTH_SESSION_LIFETIME_SECONDS"]
    session = AuthSession.issue(user_id=user.id, lifetime_seconds=lifetime)
    db.session.add(session)
    db.session.commit()

    response = make_response("", 204)
    response.set_cookie(
        _session_cookie_name(),
        session.token,
        max_age=lifetime,
        httponly=True,
        path=current_app.config["SESSION_COOKIE_PATH"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        secure=current_app.config["SESSION_COOKIE_SECURE"],
    )
    return response


@auth_api_bp.get("/api/v1/auth/session")
def get_session():
    session = _read_session()
    if not session:
        return jsonify({"error": "authentication_required"}), 401

    user = db.session.get(Usuario, session.user_id)
    if not user:
        return jsonify({"error": "authentication_required"}), 401

    return jsonify(
        {
            "user": {
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
            }
        }
    )


@auth_api_bp.post("/api/v1/auth/logout")
def logout():
    session = _read_session()
    if session:
        db.session.delete(session)
        db.session.commit()

    return _expire_cookie(make_response("", 204))


@auth_api_bp.post("/internal/v1/sessions/validate")
def validate_session():
    session = _read_session()
    if not session:
        return jsonify({"error": "authentication_required"}), 401

    user = db.session.get(Usuario, session.user_id)
    if not user:
        return jsonify({"error": "authentication_required"}), 401

    return jsonify({"user_id": user.id, "rol": user.rol})

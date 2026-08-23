"""Auth service Flask application factory."""

from flask import Flask

from app import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="auth-service-secret",
        SQLALCHEMY_DATABASE_URI="sqlite:///magnifique.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_NAME="magnifique_session",
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_PATH="/",
        SESSION_COOKIE_SECURE=False,
        AUTH_SESSION_LIFETIME_SECONDS=1800,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.models import AuthSession, Usuario  # noqa: F401
    from services.auth_service.app.routes import auth_api_bp

    app.register_blueprint(auth_api_bp)
    return app

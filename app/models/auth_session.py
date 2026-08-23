"""Server-side session authority shared by the extracted auth service."""

import secrets
import uuid
from datetime import timedelta

from app import db
from app.models._timestamps import utc_now


class AuthSession(db.Model):
    __tablename__ = "auth_session"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("usuario.id"), nullable=False, index=True)
    token = db.Column(db.String(128), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    expires_at = db.Column(db.DateTime, nullable=False)

    @classmethod
    def issue(cls, *, user_id: str, lifetime_seconds: int) -> "AuthSession":
        return cls(
            user_id=user_id,
            token=secrets.token_urlsafe(32),
            expires_at=utc_now() + timedelta(seconds=lifetime_seconds),
        )

    def is_active(self) -> bool:
        return self.expires_at > utc_now()

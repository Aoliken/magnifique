"""
Hotel Magnifique — Model: Configuracion (player preferences)

Persists per-player language, display currency and difficulty so the
"Opciones" menu survives across sessions.
"""
import uuid
from app import db
from app.models._timestamps import utc_now
from app.utils.preferences import (
    DEFAULT_CURRENCY,
    DEFAULT_DIFFICULTY,
    DEFAULT_LANGUAGE,
)


class Configuracion(db.Model):
    __tablename__ = 'configuracion'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = db.Column(
        db.String(36), db.ForeignKey('usuario.id'), nullable=False, unique=True, index=True
    )
    idioma = db.Column(db.String(10), nullable=False, default=DEFAULT_LANGUAGE)
    moneda = db.Column(db.String(10), nullable=False, default=DEFAULT_CURRENCY)
    dificultad = db.Column(db.String(10), nullable=False, default=DEFAULT_DIFFICULTY)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # ── Relaciones ─────────────────────────────────────
    usuario = db.relationship('Usuario', back_populates='configuracion')

    def __repr__(self):
        return f'<Configuracion {self.usuario_id} {self.idioma}/{self.moneda}/{self.dificultad}>'
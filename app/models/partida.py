"""
Hotel Magnifique — Model: Partida
"""
import uuid
from datetime import datetime
from app import db


class Partida(db.Model):
    __tablename__ = 'partida'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = db.Column(db.String(36), db.ForeignKey('usuario.id'), nullable=False, index=True)
    dia_actual = db.Column(db.Integer, nullable=False, default=1)  # 1-31
    capital = db.Column(db.Numeric(10, 2), nullable=False, default=5000.00)
    reputacion = db.Column(db.Numeric(3, 1), nullable=False, default=3.0)  # 1.0-10.0
    ganancia_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    ingreso_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    gasto_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    grado_final = db.Column(db.String(10), nullable=True)  # A|B|C|D|F|S|💸

    # ── Relaciones ─────────────────────────────────────
    usuario = db.relationship('Usuario', back_populates='partidas')
    dias = db.relationship('Dia', back_populates='partida', lazy='dynamic', order_by='Dia.numero')
    ajustes = db.relationship('Ajuste', back_populates='partida', lazy='dynamic')

    def __repr__(self):
        return f'<Partida {self.id} día {self.dia_actual}>'
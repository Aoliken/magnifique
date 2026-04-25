"""
Hotel Magnifique — Model: Resultado
"""
import uuid
from app import db


class Resultado(db.Model):
    __tablename__ = 'resultado'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dia_id = db.Column(db.String(36), db.ForeignKey('dia.id'), nullable=False, index=True)
    habitaciones_ocupadas = db.Column(db.Integer, nullable=False)
    ocupacion_pct = db.Column(db.Numeric(3, 2), nullable=False)
    ingreso = db.Column(db.Numeric(10, 2), nullable=False)
    gasto = db.Column(db.Numeric(10, 2), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False)
    reputacion = db.Column(db.Numeric(3, 1), nullable=False)
    reputacion_cambio = db.Column(db.Numeric(3, 2), nullable=False)
    demanda_base = db.Column(db.Numeric(3, 2), nullable=False)
    precio_optimo = db.Column(db.Numeric(5, 2), nullable=False)

    # ── Relaciones ─────────────────────────────────────
    dia = db.relationship('Dia', back_populates='resultado')

    def __repr__(self):
        return f'<Resultado {self.dia_id} hab={self.habitaciones_ocupadas}>'
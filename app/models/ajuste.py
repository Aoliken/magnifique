"""
Hotel Magnifique — Model: Ajuste
"""
import uuid
from datetime import datetime
from app import db


class Ajuste(db.Model):
    __tablename__ = 'ajuste'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partida_id = db.Column(db.String(36), db.ForeignKey('partida.id'), nullable=False, index=True)
    parametro = db.Column(db.String(50), nullable=False)  # inflacion|demanda_base|...
    valor_base = db.Column(db.Numeric(10, 4), nullable=False)
    valor_actual = db.Column(db.Numeric(10, 4), nullable=False)
    motivo = db.Column(db.String(50), nullable=False)  # inflation|evento|manual
    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ── Relaciones ─────────────────────────────────────
    partida = db.relationship('Partida', back_populates='ajustes')

    def __repr__(self):
        return f'<Ajuste {self.parametro} {self.valor_base}→{self.valor_actual}>'
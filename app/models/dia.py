"""
Hotel Magnifique — Model: Dia
"""
import uuid
from datetime import datetime
from app import db


class Dia(db.Model):
    __tablename__ = 'dia'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partida_id = db.Column(db.String(36), db.ForeignKey('partida.id'), nullable=False, index=True)
    numero = db.Column(db.Integer, nullable=False)  # 1-31
    temporada = db.Column(db.String(20), nullable=False)  # Primavera|Verano|Otoño|Invierno
    evento = db.Column(db.String(50), nullable=False)  # Normal|Congreso|Feria|...
    factor_temporada = db.Column(db.Numeric(3, 2), nullable=False)
    factor_evento = db.Column(db.Numeric(3, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ── Relaciones ─────────────────────────────────────
    partida = db.relationship('Partida', back_populates='dias')
    decision = db.relationship('Decision', back_populates='dia', uselist=False)
    resultado = db.relationship('Resultado', back_populates='dia', uselist=False)

    def __repr__(self):
        return f'<Dia {self.numero} ({self.temporada})>'
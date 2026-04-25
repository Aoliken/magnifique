"""
Hotel Magnifique — Model: Decision
"""
import uuid
from app import db


class Decision(db.Model):
    __tablename__ = 'decision'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dia_id = db.Column(db.String(36), db.ForeignKey('dia.id'), nullable=False, index=True)
    precio = db.Column(db.Integer, nullable=False)
    personal = db.Column(db.Integer, nullable=False)  # 1-12 empleados
    marketing = db.Column(db.Integer, nullable=False)  # $0-500
    desayuno = db.Column(db.Boolean, nullable=False, default=False)
    piscina = db.Column(db.Boolean, nullable=False, default=False)
    spa = db.Column(db.Boolean, nullable=False, default=False)

    # ── Relaciones ─────────────────────────────────────
    dia = db.relationship('Dia', back_populates='decision')

    def __repr__(self):
        return f'<Decision día {self.dia_id} precio=${self.precio}>'
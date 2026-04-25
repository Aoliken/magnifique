"""
Hotel Magnifique — Model: Usuario
"""
import uuid
import bcrypt
from app import db, login_manager
from flask_login import UserMixin
from app.models._timestamps import utc_now


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(60), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario')  # 'usuario' | 'admin'
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    last_login = db.Column(db.DateTime, nullable=True)

    # ── Relaciones ──────────────────────────────���──────
    partidas = db.relationship('Partida', back_populates='usuario', lazy='dynamic')

    # ── Métodos ─────────────────────────────────────
    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def is_admin(self) -> bool:
        return self.rol == 'admin'

    def __repr__(self):
        return f'<Usuario {self.email}>'


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(Usuario, user_id)

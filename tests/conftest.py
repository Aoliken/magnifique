"""
Hotel Magnifique — Test Configuration (pytest fixtures)
"""
import pytest
from decimal import Decimal
from app import create_app, db
from app.models import Usuario, Partida, Dia, Decision, Resultado


@pytest.fixture
def app():
    """Crea app en modo test."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    with app.app_context():
        db.create_all()
        db.session.remove()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def usuario(app):
    """Usuario de prueba."""
    u = Usuario(email='test@test.com', nombre='Test User', rol='usuario')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def partida(app, usuario):
    """Partida de prueba."""
    p = Partida(
        usuario_id=usuario.id,
        dia_actual=1,
        capital=Decimal('5000'),
        reputacion=Decimal('3.0'),
        activa=True,
    )
    db.session.add(p)
    db.session.commit()
    return p

"""Tests for full-game translations (play, results, end, navbar)."""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Configuracion, Partida, Usuario


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    usuario = Usuario(email="player@test.com", nombre="Player One", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def login(client, email="player@test.com", password="password123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def set_config(user, *, idioma="es", moneda="usd", dificultad="media"):
    config = Configuracion(usuario_id=user.id, idioma=idioma, moneda=moneda, dificultad=dificultad)
    db.session.add(config)
    db.session.commit()
    return config


def create_active_game(user, *, day=1, capital="5000.00", reputation="3.0"):
    partida = Partida(
        usuario_id=user.id,
        dia_actual=day,
        capital=Decimal(capital),
        reputacion=Decimal(reputation),
        activa=True,
    )
    db.session.add(partida)
    db.session.commit()
    return partida


class TestPlayTranslation:
    def test_play_defaults_to_spanish(self, client, user):
        create_active_game(user)
        login(client)

        response = client.get("/game/play")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'lang="es"' in html
        assert "Pronóstico del Día" in html
        assert "Tus Decisiones de Hoy" in html
        assert "Precio/noche" in html
        assert "Abrir el Hotel — Día 1" in html
        assert "Día Siguiente →" in html
        assert "Cerrar sesión" in html

    def test_play_renders_english_and_currency(self, client, user):
        create_active_game(user, day=3)
        set_config(user, idioma="en", moneda="eur")
        login(client)

        response = client.get("/game/play")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'lang="en"' in html
        assert "Daily Forecast" in html
        assert "Your Decisions Today" in html
        assert "Price/night" in html
        assert "Open the Hotel — Day 3" in html
        assert "Next Day →" in html
        assert "Staff (€130/person)" in html
        assert "€5,000" in html  # capital del navbar
        assert "Log out" in html
        # La localización numérica del cliente sigue al idioma
        assert 'const LOCALE = "en-US"' in html

    def test_play_yesterday_profit_uses_currency_and_sign(self, client, user):
        from app.models import Dia, Decision, Resultado

        create_active_game(user, day=5, capital="6200.00")
        dia_prev = Dia(
            partida_id=Partida.query.filter_by(usuario_id=user.id, activa=True).first().id,
            numero=4,
            temporada="Verano",
            evento="Normal",
            factor_temporada=Decimal("1.0"),
            factor_evento=Decimal("1.0"),
        )
        db.session.add(dia_prev)
        db.session.flush()
        db.session.add(Decision(dia_id=dia_prev.id, precio=120, personal=4, marketing=100))
        db.session.add(
            Resultado(
                dia_id=dia_prev.id,
                habitaciones_ocupadas=10,
                ocupacion_pct=Decimal("50.00"),
                ingreso=Decimal("900.00"),
                gasto=Decimal("600.00"),
                balance=Decimal("300.00"),
                reputacion=Decimal("3.0"),
                reputacion_cambio=Decimal("0.10"),
                demanda_base=Decimal("1.0"),
                precio_optimo=Decimal("120.0"),
            )
        )
        db.session.commit()
        set_config(user, idioma="en", moneda="usd")
        login(client)

        response = client.get("/game/play")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        # Jinja escapa el apóstrofe; la entidad es la forma correcta en HTML
        assert "Yesterday&#39;s profit" in html
        assert "+$300" in html


class TestEndTranslation:
    def test_final_results_renders_spanish_by_default(self, client, user):
        partida = Partida(
            usuario_id=user.id,
            dia_actual=30,
            capital=Decimal("7000.00"),
            reputacion=Decimal("4.2"),
            ganancia_total=Decimal("2000.00"),
            ingreso_total=Decimal("10000.00"),
            gasto_total=Decimal("8000.00"),
            activa=False,
            grado_final="A",
        )
        db.session.add(partida)
        db.session.commit()
        login(client)

        response = client.get("/game/final-results")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "¡Temporada Completada!" in html
        assert "Capital final" in html
        assert "Jugar de Nuevo" in html

    def test_final_results_renders_english(self, client, user):
        partida = Partida(
            usuario_id=user.id,
            dia_actual=30,
            capital=Decimal("7000.00"),
            reputacion=Decimal("4.2"),
            ganancia_total=Decimal("2000.00"),
            ingreso_total=Decimal("10000.00"),
            gasto_total=Decimal("8000.00"),
            activa=False,
            grado_final="A",
        )
        db.session.add(partida)
        db.session.commit()
        set_config(user, idioma="en", moneda="eur")
        login(client)

        response = client.get("/game/final-results")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Season Complete!" in html
        assert "Final capital" in html
        assert "Total profit" in html
        assert "Days played" in html
        assert "Play Again" in html
        assert "€7,000" in html
        assert 'lang="en"' in html


class TestInvalidOptionsFlash:
    def test_invalid_options_flash_in_spanish(self, app, client, user):
        set_config(user, idioma="es")
        login(client)

        response = client.post(
            "/game/options",
            data={"idioma": "klingon", "moneda": "usd", "dificultad": "media"},
            follow_redirects=True,
        )

        assert "Valores de opciones inválidos." in response.get_data(as_text=True)

    def test_invalid_options_flash_in_english(self, app, client, user):
        set_config(user, idioma="en")
        login(client)

        response = client.post(
            "/game/options",
            data={"idioma": "klingon", "moneda": "usd", "dificultad": "media"},
            follow_redirects=True,
        )

        assert "Invalid option values." in response.get_data(as_text=True)
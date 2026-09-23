"""Tests for the post-login main menu: start/continue, options, tutorial, ranking."""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Configuracion, Partida, Usuario
from app.utils.preferences import money


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


@pytest.fixture
def second_user(app):
    usuario = Usuario(email="rival@test.com", nombre="Rival Two", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def login(client, email="player@test.com", password="password123", follow_redirects=False):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=follow_redirects,
    )


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


class TestMenu:
    def test_menu_renders_all_six_actions_when_no_active_game(self, client, user):
        login(client)

        response = client.get("/game/menu")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        for label in [
            "Comenzar juego",
            "Continuar partida",
            "Tutorial",
            "Opciones",
            "Ranking de jugadores",
            "Salir",
        ]:
            assert label in html
        # Sin partida: Continuar no debe ser un enlace jugable
        assert 'title="You don' not in html  # tr es es por defecto
        assert "No tenés una partida pendiente por terminar." in html

    def test_menu_with_active_game_shows_continue_and_day(self, client, user):
        create_active_game(user, day=7, capital="6200.00", reputation="3.4")
        login(client)

        response = client.get("/game/menu")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Partida en curso" in html
        assert "Día 7 de 30" in html
        assert "$6,200" in html  # moneda por defecto usd
        assert "/game/play" in html

    def test_menu_form_new_game_archives_active_when_forced(self, client, user):
        current = create_active_game(user, day=12)
        login(client)

        response = client.post("/game/new", data={"force": "1"}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/game/play")

        db.session.refresh(current)
        assert current.activa is False

        fresh = Partida.query.filter_by(usuario_id=user.id, activa=True).first()
        assert fresh is not None
        assert fresh.id != current.id
        assert fresh.dia_actual == 1

    def test_menu_new_game_without_force_reuses_active_game(self, app, client, user):
        current = create_active_game(user, day=5)
        login(client)

        response = client.post("/game/new", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/game/play")
        assert Partida.query.filter_by(usuario_id=user.id).count() == 1
        db.session.refresh(current)
        assert current.activa is True

    def test_play_redirects_to_menu_when_no_active_game(self, client, user):
        login(client)

        response = client.get("/game/play", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/game/menu")

    def test_new_game_snapshots_difficulty_from_options(self, app, client, user):
        login(client)
        client.post(
            "/game/options",
            data={"idioma": "en", "moneda": "eur", "dificultad": "dificil"},
        )

        client.post("/game/new", follow_redirects=False)

        fresh = Partida.query.filter_by(usuario_id=user.id, activa=True).first()
        assert fresh is not None
        assert fresh.dificultad == "dificil"


class TestOptions:
    def test_options_creates_defaults_on_first_access(self, app, client, user):
        login(client)

        response = client.get("/game/options")

        assert response.status_code == 200
        config = Configuracion.query.filter_by(usuario_id=user.id).first()
        assert config is not None
        assert config.idioma == "es"
        assert config.moneda == "usd"
        assert config.dificultad == "media"
        html = response.get_data(as_text=True)
        assert "Español" in html
        assert "US Dollar ($)" in html
        assert "Media" in html

    def test_options_save_valid_values(self, app, client, user):
        login(client)

        response = client.post(
            "/game/options",
            data={"idioma": "en", "moneda": "eur", "dificultad": "facil"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        config = Configuracion.query.filter_by(usuario_id=user.id).first()
        assert config.idioma == "en"
        assert config.moneda == "eur"
        assert config.dificultad == "facil"
        assert "Options saved." in response.get_data(as_text=True)

    def test_options_reject_invalid_values(self, app, client, user):
        login(client)
        config = Configuracion(usuario_id=user.id)
        db.session.add(config)
        db.session.commit()

        response = client.post(
            "/game/options",
            data={"idioma": "klingon", "moneda": "usd", "dificultad": "media"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/game/options")
        db.session.refresh(config)
        assert config.idioma == "es"
        assert config.moneda == "usd"
        assert config.dificultad == "media"

    def test_money_formatter_uses_currency(self):
        assert money(5000, "usd") == "$5,000"
        assert money(5000, "eur") == "€5,000"
        assert money(5000, "ars") == "ARS$5,000"
        assert money(1234.5, "usd") == "$1,234"


class TestTutorial:
    def test_tutorial_page_embeds_manual(self, client, user):
        login(client)

        response = client.get("/game/tutorial")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Tutorial" in html
        assert "/game/manual" in html

    def test_manual_file_is_served(self, client, user):
        login(client)

        response = client.get("/game/manual")

        assert response.status_code == 200
        assert b"Manual del Jugador" in response.data


class TestRanking:
    def test_ranking_lists_best_player_per_user(self, app, client, user, second_user):
        partida_winner = Partida(
            usuario_id=user.id,
            dia_actual=30,
            capital=Decimal("9000.00"),
            reputacion=Decimal("4.7"),
            ganancia_total=Decimal("4000.00"),
            ingreso_total=Decimal("12000.00"),
            gasto_total=Decimal("8000.00"),
            activa=False,
            grado_final="S",
        )
        partida_loser = Partida(
            usuario_id=user.id,
            dia_actual=30,
            capital=Decimal("5200.00"),
            reputacion=Decimal("3.0"),
            ganancia_total=Decimal("200.00"),
            ingreso_total=Decimal("6000.00"),
            gasto_total=Decimal("5800.00"),
            activa=False,
            grado_final="C",
        )
        partida_rival = Partida(
            usuario_id=second_user.id,
            dia_actual=30,
            capital=Decimal("7000.00"),
            reputacion=Decimal("4.1"),
            ganancia_total=Decimal("2000.00"),
            ingreso_total=Decimal("9000.00"),
            gasto_total=Decimal("7000.00"),
            activa=False,
            grado_final="A",
        )
        db.session.add_all([partida_winner, partida_loser, partida_rival])
        db.session.commit()

        login(client)

        response = client.get("/game/ranking")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Player One" in html
        assert "Rival Two" in html
        # El jugador aparece una sola vez y su mejor partida gana
        assert html.index("Player One") < html.index("Rival Two")
        assert "$4,000" in html
        assert "$200" not in html

    def test_ranking_shows_empty_state(self, client, user):
        login(client)

        response = client.get("/game/ranking")

        assert response.status_code == 200
        assert "Todavía no hay partidas terminadas." in response.get_data(as_text=True)
"""Regression tests for app startup and core game flow."""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Dia, Decision, Partida, Resultado, Usuario


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


def test_create_app_uses_local_fallbacks_when_env_is_incomplete(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "   ")
    monkeypatch.setenv("DATABASE_URL", "")
    for key in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]:
        monkeypatch.setenv(key, "")

    app = create_app({"TESTING": True})

    assert app.config["SECRET_KEY"]
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///")


def test_root_redirects_anonymous_users_to_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_root_redirects_logged_in_users_with_active_game_to_menu(app, client, user):
    create_active_game(user)
    login(client)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game/menu")


def test_root_redirects_logged_in_users_without_active_game_to_menu(client, user):
    login(client)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game/menu")


def test_login_redirects_to_menu_screen_when_user_has_no_active_game(client, user):
    response = login(client, follow_redirects=True)

    assert response.status_code == 200
    assert b"Comenzar juego" in response.data


def test_run_day_updates_decision_columns_and_advances_day(app, client, user):
    partida = create_active_game(user)

    dia = Dia(
        partida_id=partida.id,
        numero=1,
        temporada="Primavera 🌸",
        evento="Día Normal ☁️",
        factor_temporada=Decimal("0.62"),
        factor_evento=Decimal("1.00"),
    )
    db.session.add(dia)
    db.session.commit()

    login(client)

    response = client.post(
        "/game/day",
        data={
            "precio": "175",
            "personal": "6",
            "marketing": "150",
            "desayuno": "1",
            "spa": "1",
        },
    )

    assert response.status_code == 200

    db.session.refresh(partida)
    decision = Decision.query.filter_by(dia_id=dia.id).first()

    assert decision.precio == 175
    assert decision.personal == 6
    assert decision.marketing == 150
    assert decision.desayuno is True
    assert decision.spa is True
    assert partida.dia_actual == 2


def test_new_game_reuses_existing_active_game_instead_of_creating_a_duplicate(app, client, user):
    create_active_game(user)
    login(client)

    response = client.post("/game/new", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game/play")
    assert Partida.query.filter_by(usuario_id=user.id).count() == 1


def test_new_game_creates_a_day_one_save_when_user_has_no_active_game(client, user):
    login(client)

    response = client.post("/game/new", follow_redirects=False)

    partida = Partida.query.filter_by(usuario_id=user.id, activa=True).first()

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game/play")
    assert partida is not None
    assert partida.dia_actual == 1


def test_play_bootstraps_missing_current_day_and_shows_previous_results(app, client, user):
    partida = create_active_game(user, day=2)

    prev_dia = Dia(
        partida_id=partida.id,
        numero=1,
        temporada="Primavera 🌸",
        evento="Día Normal ☁️",
        factor_temporada=Decimal("0.62"),
        factor_evento=Decimal("1.00"),
    )
    db.session.add(prev_dia)
    db.session.commit()

    db.session.add(
        Resultado(
            dia_id=prev_dia.id,
            habitaciones_ocupadas=12,
            ocupacion_pct=Decimal("0.60"),
            ingreso=Decimal("2400.00"),
            gasto=Decimal("1700.00"),
            balance=Decimal("700.00"),
            reputacion=Decimal("3.2"),
            reputacion_cambio=Decimal("0.20"),
            demanda_base=Decimal("0.62"),
            precio_optimo=Decimal("120.00"),
        )
    )
    db.session.commit()

    login(client)

    response = client.get("/game/play")

    assert response.status_code == 200
    assert b"12/20" in response.data

    dia_actual = Dia.query.filter_by(partida_id=partida.id, numero=2).first()
    decision = Decision.query.filter_by(dia_id=dia_actual.id).first()

    assert dia_actual is not None
    assert decision is not None
    assert decision.precio == 120
    assert decision.personal == 4
    assert decision.marketing == 100


def test_run_day_returns_400_when_user_has_no_active_game(client, user):
    login(client)

    response = client.post("/game/day", data={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Sin partida activa"}


def test_run_day_returns_404_when_current_day_is_missing(app, client, user):
    create_active_game(user)
    login(client)

    response = client.post("/game/day", data={})

    assert response.status_code == 404
    assert response.get_json() == {"error": "Día no encontrado"}


def test_game_over_response_exposes_final_results_and_page_renders(app, client, user):
    partida = create_active_game(user, day=30, capital="5000.00", reputation="4.6")

    dia = Dia(
        partida_id=partida.id,
        numero=30,
        temporada="Verano ☀️",
        evento="Congreso 🎤",
        factor_temporada=Decimal("0.95"),
        factor_evento=Decimal("1.30"),
    )
    db.session.add(dia)
    db.session.commit()

    login(client)

    response = client.post(
        "/game/day",
        data={
            "precio": "190",
            "personal": "8",
            "marketing": "200",
            "desayuno": "1",
            "piscina": "1",
            "spa": "1",
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["game_over"] is True
    assert payload["next_day"] is None
    assert payload["final_results_url"].endswith("/game/final-results")

    db.session.refresh(partida)

    assert partida.activa is False
    assert partida.grado_final in {"S", "A", "B", "C", "D", "💸"}

    final_results = client.get(payload["final_results_url"])

    assert final_results.status_code == 200
    assert b"Temporada Completada" in final_results.data
    assert partida.grado_final.encode() in final_results.data


def test_final_results_page_restarts_game_via_post_form_not_get_link(app, client, user):
    partida = Partida(
        usuario_id=user.id,
        dia_actual=30,
        capital=Decimal("6400.00"),
        reputacion=Decimal("4.4"),
        activa=False,
        grado_final="A",
    )
    db.session.add(partida)
    db.session.commit()

    login(client)

    response = client.get("/game/final-results")

    assert response.status_code == 200
    assert b'<form method="POST" action="/game/new">' in response.data
    assert b'href="/game/new"' not in response.data


def test_finished_game_can_start_a_new_run_via_post_endpoint(app, client, user):
    finished_game = Partida(
        usuario_id=user.id,
        dia_actual=30,
        capital=Decimal("6400.00"),
        reputacion=Decimal("4.4"),
        activa=False,
        grado_final="A",
    )
    db.session.add(finished_game)
    db.session.commit()

    login(client)

    response = client.post("/game/new", follow_redirects=False)

    active_game = Partida.query.filter_by(usuario_id=user.id, activa=True).first()

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game/play")
    assert Partida.query.filter_by(usuario_id=user.id).count() == 2
    assert active_game is not None
    assert active_game.id != finished_game.id
    assert active_game.dia_actual == 1

"""Phase 1 contract coverage for the Flask microservices slice."""

import json
from pathlib import Path

from app import create_app as create_monolith_app, db
from app.models import Decision, Dia, Partida, Usuario
from services.auth_service.app import create_app as create_auth_service_app
from services.game_service.app import create_app as create_game_service_app


def _create_user(email: str = "contract@test.com") -> Usuario:
    usuario = Usuario(email=email, nombre="Contract User", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _sqlite_uri(tmp_path, filename: str) -> str:
    return f"sqlite:///{tmp_path / filename}"


def test_public_urls_remain_stable_during_phase1_cutover():
    app = create_monolith_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        client = app.test_client()

        root_response = client.get("/", follow_redirects=False)
        login_page = client.get("/auth/login")
        protected_page = client.get("/game/play", follow_redirects=False)

        assert root_response.status_code == 302
        assert root_response.headers["Location"].endswith("/auth/login")
        assert login_page.status_code == 200
        assert protected_page.status_code == 302
        assert protected_page.headers["Location"].endswith("/auth/login?next=%2Fgame%2Fplay")

        db.session.remove()
        db.drop_all()


def test_auth_service_login_sets_http_only_session_cookie():
    app = create_auth_service_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        _create_user()
        client = app.test_client()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "contract@test.com", "password": "password123"},
        )

        cookie = response.headers["Set-Cookie"]

        assert response.status_code == 204
        assert "magnifique_session=" in cookie
        assert "HttpOnly" in cookie
        assert "Path=/" in cookie
        assert "SameSite=Lax" in cookie

        db.session.remove()
        db.drop_all()


def test_auth_service_session_endpoint_returns_authenticated_user():
    app = create_auth_service_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        _create_user(email="session@test.com")
        client = app.test_client()

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "session@test.com", "password": "password123"},
        )
        cookie = login_response.headers["Set-Cookie"].split(";", 1)[0]
        token_value = cookie.split("=", 1)[1]
        client.set_cookie("magnifique_session", token_value)

        response = client.get("/api/v1/auth/session")

        assert response.status_code == 200
        assert response.get_json() == {
            "user": {
                "email": "session@test.com",
                "nombre": "Contract User",
                "rol": "usuario",
            }
        }

        db.session.remove()
        db.drop_all()


def test_game_service_current_game_contract_returns_authenticated_state(tmp_path):
    contract = json.loads(
        (Path(__file__).resolve().parents[2] / "shared" / "contracts" / "http" / "game_current.json").read_text(
            encoding="utf-8"
        )
    )
    database_uri = _sqlite_uri(tmp_path, "game_contract.db")
    auth_app = create_auth_service_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": database_uri,
        }
    )
    game_app = create_game_service_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": database_uri,
            "AUTH_SERVICE_APP": auth_app,
        }
    )

    with auth_app.app_context():
        db.create_all()
        user = _create_user(email="game-contract@test.com")
        partida = Partida(usuario_id=user.id, dia_actual=1, activa=True)
        db.session.add(partida)
        db.session.commit()
        dia = Dia(
            partida_id=partida.id,
            numero=1,
            temporada="Primavera 🌸",
            evento="Día Normal ☁️",
            factor_temporada=0.62,
            factor_evento=1.00,
        )
        db.session.add(dia)
        db.session.commit()
        db.session.add(Decision(dia_id=dia.id, precio=120, personal=4, marketing=100))
        db.session.commit()

    auth_client = auth_app.test_client()
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "game-contract@test.com", "password": "password123"},
    )
    token_value = login_response.headers["Set-Cookie"].split(";", 1)[0].split("=", 1)[1]

    game_client = game_app.test_client()
    game_client.set_cookie("magnifique_session", token_value)

    response = game_client.get(contract["request"]["path"])

    assert response.status_code == contract["response"]["status"]
    assert response.get_json() == contract["response"]["body"]

"""Integration coverage for cross-service session validation in phase 1."""

from app import db
from app.models import Decision, Dia, Partida, Resultado, Usuario
from services.auth_service.app import create_app as create_auth_service_app
from services.game_service.app import create_app as create_game_service_app


def _sqlite_uri(tmp_path, filename: str) -> str:
    return f"sqlite:///{tmp_path / filename}"


def _create_user(email: str = "integration@test.com") -> Usuario:
    usuario = Usuario(email=email, nombre="Integration User", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def test_game_service_rejects_missing_or_forged_cookie_without_writing_game_state(tmp_path):
    database_uri = _sqlite_uri(tmp_path, "phase1_session_fk_invalid.db")
    auth_app = create_auth_service_app(
        {"TESTING": True, "SECRET_KEY": "test-secret", "SQLALCHEMY_DATABASE_URI": database_uri}
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
        user = _create_user()
        db.session.add(Partida(usuario_id=user.id, dia_actual=1, activa=True))
        db.session.commit()

    client = game_app.test_client()

    missing_cookie = client.get("/api/v1/games/current")
    client.set_cookie("magnifique_session", "forged-token")
    forged_cookie = client.get("/api/v1/games/current")

    assert missing_cookie.status_code == 401
    assert forged_cookie.status_code == 401

    with game_app.app_context():
        assert Dia.query.count() == 0
        assert Decision.query.count() == 0
        assert Resultado.query.count() == 0


def test_game_service_fails_closed_when_auth_validation_is_unavailable(tmp_path):
    database_uri = _sqlite_uri(tmp_path, "phase1_session_fk_outage.db")
    auth_app = create_auth_service_app(
        {"TESTING": True, "SECRET_KEY": "test-secret", "SQLALCHEMY_DATABASE_URI": database_uri}
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
        user = _create_user(email="outage@test.com")
        db.session.add(Partida(usuario_id=user.id, dia_actual=1, activa=True))
        db.session.commit()

    client = game_app.test_client()
    client.set_cookie("magnifique_session", "any-token")
    game_app.config["AUTH_SERVICE_APP"] = None

    response = client.get("/api/v1/games/current")

    assert response.status_code == 503

    with game_app.app_context():
        assert Dia.query.count() == 0
        assert Decision.query.count() == 0
        assert Resultado.query.count() == 0


def test_game_service_keeps_usuario_reads_only_and_preserves_temporary_fk(tmp_path):
    database_uri = _sqlite_uri(tmp_path, "phase1_session_fk_valid.db")
    auth_app = create_auth_service_app(
        {"TESTING": True, "SECRET_KEY": "test-secret", "SQLALCHEMY_DATABASE_URI": database_uri}
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
        user = _create_user(email="fk@test.com")
        user_id = user.id

    auth_client = auth_app.test_client()
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "fk@test.com", "password": "password123"},
    )
    token_value = login_response.headers["Set-Cookie"].split(";", 1)[0].split("=", 1)[1]

    game_client = game_app.test_client()
    game_client.set_cookie("magnifique_session", token_value)

    create_response = game_client.post("/api/v1/games")
    run_response = game_client.post(
        "/api/v1/days/current/run",
        json={"precio": 175, "personal": 6, "marketing": 150, "desayuno": True, "spa": True},
    )

    assert create_response.status_code == 201
    assert run_response.status_code == 200

    with game_app.app_context():
        partida = Partida.query.one()

        assert Usuario.query.count() == 1
        assert partida.usuario_id == user_id
        assert partida.usuario.id == user_id
        assert Dia.query.count() == 1
        assert Decision.query.count() == 1
        assert Resultado.query.count() == 1

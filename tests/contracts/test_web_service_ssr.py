"""Contract coverage for the incremental web-service SSR slice."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from urllib import error, request

from app import create_app as create_monolith_app, db
from app.models import Usuario


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_SERVICE_ROOT = PROJECT_ROOT / "services" / "web_service"
WEB_SERVICE_SERVER = WEB_SERVICE_ROOT / "src" / "server.js"
OWNER_HEADER = "X-Magnifique-Web-Service"
OWNER_VALUE = "web-service"


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _fetch(url: str):
    opener = request.build_opener(_NoRedirect)
    try:
        return opener.open(url, timeout=5)
    except error.HTTPError as exc:
        return exc


def _create_user(email: str = "compat@test.com") -> Usuario:
    usuario = Usuario(email=email, nombre="Compat User", rol="usuario")
    usuario.set_password("password123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


@contextmanager
def _started_web_service():
    port = _free_port()
    process = subprocess.Popen(
        ["node", str(WEB_SERVICE_SERVER)],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                response = _fetch(f"http://127.0.0.1:{port}/auth/login")
            except OSError:
                time.sleep(0.1)
                continue
            response.read()
            break
        else:
            stdout, stderr = process.communicate(timeout=1)
            raise AssertionError(f"web-service failed to boot\nstdout:\n{stdout}\nstderr:\n{stderr}")

        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_web_service_owns_incremental_public_routes_with_stable_urls():
    with _started_web_service() as base_url:
        root_response = _fetch(f"{base_url}/")
        login_response = _fetch(f"{base_url}/auth/login")
        register_response = _fetch(f"{base_url}/auth/register")
        no_game_response = _fetch(f"{base_url}/game/no-game")

        assert root_response.status == 302
        assert root_response.headers["Location"].endswith("/auth/login")
        assert root_response.headers[OWNER_HEADER] == OWNER_VALUE

        assert login_response.status == 200
        assert login_response.headers[OWNER_HEADER] == OWNER_VALUE
        assert "Acceso al Hotel" in login_response.read().decode("utf-8")

        assert register_response.status == 200
        assert register_response.headers[OWNER_HEADER] == OWNER_VALUE
        assert "Registro de Huésped" in register_response.read().decode("utf-8")

        assert no_game_response.status == 200
        assert no_game_response.headers[OWNER_HEADER] == OWNER_VALUE
        assert "Nueva partida" in no_game_response.read().decode("utf-8")


def test_flask_routes_handoff_ssr_pages_to_web_service_owner():
    with _started_web_service() as base_url:
        app = create_monolith_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "WEB_SERVICE_BASE_URL": base_url,
            }
        )

        with app.app_context():
            db.create_all()
            user = _create_user()
            client = app.test_client()

            login_response = client.get("/auth/login")
            register_response = client.get("/auth/register")
            root_response = client.get("/", follow_redirects=False)

            client.post(
                "/auth/login",
                data={"email": user.email, "password": "password123"},
            )

            no_game_response = client.get("/game/no-game")

            assert login_response.status_code == 200
            assert login_response.headers[OWNER_HEADER] == OWNER_VALUE
            assert "Acceso al Hotel" in login_response.get_data(as_text=True)

            assert register_response.status_code == 200
            assert register_response.headers[OWNER_HEADER] == OWNER_VALUE
            assert "Registro de Huésped" in register_response.get_data(as_text=True)

            assert root_response.status_code == 302
            assert root_response.headers["Location"].endswith("/auth/login")
            assert root_response.headers[OWNER_HEADER] == OWNER_VALUE

            assert no_game_response.status_code == 200
            assert no_game_response.headers[OWNER_HEADER] == OWNER_VALUE
            assert "Nueva partida" in no_game_response.get_data(as_text=True)

            db.session.remove()
            db.drop_all()

"""
Hotel Magnifique — Flask Application Factory
"""
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# ── Instancia global de SQLAlchemy ──────────────────────────────
# Definida ANTES de cualquier import que use db
db = SQLAlchemy()
login_manager = LoginManager()


DEFAULT_SECRET_KEY = 'dev-secret-key-cambiar-en-produccion'
DEFAULT_SQLITE_URI = 'sqlite:///magnifique.db'


def _is_set(value: str | None) -> bool:
    return bool(value and value.strip() and not value.strip().startswith('#'))


def _resolve_secret_key() -> str:
    secret_key = os.getenv('SECRET_KEY')
    return secret_key if _is_set(secret_key) else DEFAULT_SECRET_KEY


def _resolve_database_uri() -> str:
    database_url = os.getenv('DATABASE_URL')
    if _is_set(database_url):
        return database_url

    db_parts = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'name': os.getenv('DB_NAME'),
    }
    if all(_is_set(value) for value in db_parts.values()):
        return (
            f"postgresql://{db_parts['user']}:{db_parts['password']}"
            f"@{db_parts['host']}:{db_parts['port']}/{db_parts['name']}"
        )

    return DEFAULT_SQLITE_URI


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────
    app.config['SECRET_KEY'] = _resolve_secret_key()
    app.config['SQLALCHEMY_DATABASE_URI'] = _resolve_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 24h base, se ajusta por User-Agent

    if test_config:
        app.config.update(test_config)

    # ── Inicializar extensiones ──────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # ── Importar modelos (después de db.init_app) ─────
    # Se importan aquí para que Alembic los detecte
    from app.models import Usuario, Partida, Dia, Decision, Resultado, Ajuste

    # ── Blueprints ────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.game import game_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)

    @app.get('/')
    def index():
        if not current_user.is_authenticated:
            from app.routes.auth import _proxy_web_service

            proxied = _proxy_web_service('/')
            if proxied is not None:
                return proxied

        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        from app.models import Partida

        partida_activa = Partida.query.filter_by(
            usuario_id=current_user.id, activa=True
        ).first()
        if partida_activa:
            return redirect(url_for('game.play'))

        return redirect(url_for('game.no_game'))

    # ── CLI commands ─────────────────────────────────────
    @app.cli.command('init-db')
    def init_db():
        """Crea todas las tablas (útil para desarrollo)."""
        with app.app_context():
            db.create_all()
        print('✓ Tablas creadas')

    return app

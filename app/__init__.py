"""
Hotel Magnifique — Flask Application Factory
"""
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# ── Instancia global de SQLAlchemy ──────────────────────────────
# Definida ANTES de cualquier import que use db
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 24h base, se ajusta por User-Agent

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

    # ── CLI commands ─────────────────────────────────────
    @app.cli.command('init-db')
    def init_db():
        """Crea todas las tablas (útil para desarrollo)."""
        with app.app_context():
            db.create_all()
        print('✓ Tablas creadas')

    return app
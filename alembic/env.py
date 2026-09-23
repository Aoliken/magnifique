from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
import os

# ── Cargar .env ──────────────────────────────────────
load_dotenv()

# ── Construir DATABASE_URL desde .env ──────────────────────────────
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hotel_magnifique')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

sqlalchemy_url = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# this is the Alembic Config object
config = context.config

# ── OVERRIDE: forzar la URL desde .env en vez de alembic.ini ────
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (sin conexión DB)."""
    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations en 'online' mode (con conexión DB real)."""
    from sqlalchemy import engine_from_config
    from sqlalchemy import pool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Obtener metadata DENTRO del app context ─────────────────────────
# Flask-SQLAlchemy 3.x requiere que db.Model.metadata se acceda
# mientras el app context está activo.
# Se ejecuta al final de env.py para que las funciones ya estén definidas.
from app import create_app, db as _db

app = create_app()
with app.app_context():
    # _db.Model.metadata se resuelve correctamente DENTRO del context
    target_metadata = _db.Model.metadata
    # Importar todos los modelos explícitamente para asegurar que se registran
    from app.models import Usuario, Partida, Dia, Decision, Resultado, Ajuste, Configuracion
    # Tables registradas:
    print("Tables en metadata:", list(target_metadata.tables.keys()))

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
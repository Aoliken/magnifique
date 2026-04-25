# Skill Registry — Hotel Magnifique

## Project Conventions

- **Stack**: Python 3.12 + Miniconda, Flask, PostgreSQL, SQLAlchemy, Alembic
- **Frontend**: HTML/JS existente migrado a plantillas Flask + Bootstrap
- **Testing**: pytest (pending installation via requirements.txt)
- **Pattern**: 4 agentes lógicos (Auth, Simulation, Data, Template)

## Compact Rules

### Backend Flask
- Rutas en `app/routes/`, templates en `app/templates/`, estáticos en `app/static/`
- Modelos SQLAlchemy en `app/models/`
- Configuración via `app/config.py` leyendo `.env` con python-dotenv

### Database Migrations (Alembic)
- Inicializar: `alembic init migrations`
- Migración: `alembic revision --autogenerate -m "description"`
- Aplicar: `alembic upgrade head`

### Simulation Engine
- Lógica central en `app/engine/simulation.py` (extraer de hotel-magnifique.html JS)
- Constantes: `app/engine/constants.py`
- Eventos: `app/engine/events.py`
- Temporadas: `app/engine/seasons.py`

## User Skills (auto-resolved)

No hay user skills definidos aún para este proyecto.
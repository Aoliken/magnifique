"""configuracion and partida.dificultad

Revision ID: 5f4e3d2c1b0a
Revises: c8a812dc9d9f
Create Date: 2026-09-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f4e3d2c1b0a"
down_revision: Union[str, None] = "c8a812dc9d9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "configuracion",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("idioma", sa.String(length=10), nullable=False),
        sa.Column("moneda", sa.String(length=10), nullable=False),
        sa.Column("dificultad", sa.String(length=10), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )
    op.create_index(op.f("ix_configuracion_usuario_id"), "configuracion", ["usuario_id"], unique=True)

    op.add_column(
        "partida",
        sa.Column("dificultad", sa.String(length=10), nullable=False, server_default="media"),
    )


def downgrade() -> None:
    op.drop_column("partida", "dificultad")
    op.drop_index(op.f("ix_configuracion_usuario_id"), table_name="configuracion")
    op.drop_table("configuracion")
"""auth_session

Revision ID: c8a812dc9d9f
Revises: 6efc9f58613a
Create Date: 2026-08-22 14:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8a812dc9d9f"
down_revision: Union[str, None] = "6efc9f58613a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_session",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_auth_session_token"), "auth_session", ["token"], unique=True)
    op.create_index(op.f("ix_auth_session_user_id"), "auth_session", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_session_user_id"), table_name="auth_session")
    op.drop_index(op.f("ix_auth_session_token"), table_name="auth_session")
    op.drop_table("auth_session")

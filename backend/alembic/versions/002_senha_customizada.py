"""add senha_customizada to usuarios

Revision ID: 002_senha_customizada
Revises: 001_initial_schema
Create Date: 2026-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_senha_customizada"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _coluna_existe(nome: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if "usuarios" not in inspector.get_table_names():
        return False
    return nome in {c["name"] for c in inspector.get_columns("usuarios")}


def upgrade() -> None:
    if _coluna_existe("senha_customizada"):
        return
    with op.batch_alter_table("usuarios") as batch:
        batch.add_column(
            sa.Column(
                "senha_customizada",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    if not _coluna_existe("senha_customizada"):
        return
    with op.batch_alter_table("usuarios") as batch:
        batch.drop_column("senha_customizada")

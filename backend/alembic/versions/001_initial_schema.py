"""create initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("perfil", sa.String(length=50), nullable=False, server_default="secretaria"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ativo"),
        sa.Column("data_criacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_id"), "usuarios", ["id"], unique=False)
    op.create_index(op.f("ix_usuarios_username"), "usuarios", ["username"], unique=True)

    op.create_table(
        "alunos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome_completo", sa.String(length=255), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("cpf", sa.String(length=20), nullable=False),
        sa.Column("telefone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("endereco", sa.String(length=255), nullable=True),
        sa.Column("numero", sa.String(length=20), nullable=True),
        sa.Column("bairro", sa.String(length=100), nullable=True),
        sa.Column("cidade", sa.String(length=100), nullable=True),
        sa.Column("estado", sa.String(length=10), nullable=True),
        sa.Column("cep", sa.String(length=20), nullable=True),
        sa.Column("rg", sa.String(length=30), nullable=True),
        sa.Column("situacao", sa.String(length=20), nullable=False, server_default="ativo"),
        sa.Column("data_cadastro", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alunos_id"), "alunos", ["id"], unique=False)
    op.create_index(op.f("ix_alunos_nome_completo"), "alunos", ["nome_completo"], unique=False)
    op.create_index(op.f("ix_alunos_cpf"), "alunos", ["cpf"], unique=True)

    op.create_table(
        "responsaveis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome_completo", sa.String(length=255), nullable=False),
        sa.Column("cpf", sa.String(length=20), nullable=False),
        sa.Column("telefone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("endereco", sa.String(length=255), nullable=True),
        sa.Column("numero", sa.String(length=20), nullable=True),
        sa.Column("bairro", sa.String(length=100), nullable=True),
        sa.Column("cidade", sa.String(length=100), nullable=True),
        sa.Column("estado", sa.String(length=10), nullable=True),
        sa.Column("cep", sa.String(length=20), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_responsaveis_id"), "responsaveis", ["id"], unique=False)
    op.create_index(op.f("ix_responsaveis_nome_completo"), "responsaveis", ["nome_completo"], unique=False)
    op.create_index(op.f("ix_responsaveis_cpf"), "responsaveis", ["cpf"], unique=True)

    op.create_table(
        "turmas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("turno", sa.String(length=30), nullable=False),
        sa.Column("ano_letivo", sa.String(length=10), nullable=False),
        sa.Column("capacidade_maxima", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("sala", sa.String(length=50), nullable=True),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("situacao", sa.String(length=20), nullable=False, server_default="ativa"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_turmas_id"), "turmas", ["id"], unique=False)
    op.create_index(op.f("ix_turmas_nome"), "turmas", ["nome"], unique=False)
    op.create_index(op.f("ix_turmas_ano_letivo"), "turmas", ["ano_letivo"], unique=False)

    op.create_table(
        "aluno_responsavel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aluno_id", sa.Integer(), nullable=False),
        sa.Column("responsavel_id", sa.Integer(), nullable=False),
        sa.Column("grau_parentesco", sa.String(length=100), nullable=True),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["aluno_id"], ["alunos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responsavel_id"], ["responsaveis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aluno_responsavel_id"), "aluno_responsavel", ["id"], unique=False)
    op.create_index(op.f("ix_aluno_responsavel_aluno_id"), "aluno_responsavel", ["aluno_id"], unique=False)
    op.create_index(op.f("ix_aluno_responsavel_responsavel_id"), "aluno_responsavel", ["responsavel_id"], unique=False)

    op.create_table(
        "matriculas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aluno_id", sa.Integer(), nullable=False),
        sa.Column("turma_id", sa.Integer(), nullable=False),
        sa.Column("data_matricula", sa.Date(), nullable=False),
        sa.Column("ano_letivo", sa.String(length=10), nullable=False),
        sa.Column("situacao", sa.String(length=20), nullable=False, server_default="ativa"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["aluno_id"], ["alunos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turma_id"], ["turmas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matriculas_id"), "matriculas", ["id"], unique=False)
    op.create_index(op.f("ix_matriculas_aluno_id"), "matriculas", ["aluno_id"], unique=False)
    op.create_index(op.f("ix_matriculas_turma_id"), "matriculas", ["turma_id"], unique=False)
    op.create_index(op.f("ix_matriculas_ano_letivo"), "matriculas", ["ano_letivo"], unique=False)


def downgrade() -> None:
    op.drop_table("matriculas")
    op.drop_table("aluno_responsavel")
    op.drop_table("turmas")
    op.drop_table("responsaveis")
    op.drop_table("alunos")
    op.drop_table("usuarios")

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Garante que a raiz do backend esteja no caminho de importacao
_backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from app.database import Base, settings
from app.models import usuario, aluno, responsavel, aluno_responsavel, turma, matricula  # noqa: F401

config = context.config

# Sobrescreve a URL com a do .env / variável de ambiente
db_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    _rel = db_url[len("sqlite:///"):]
    if not os.path.isabs(_rel):
        _rel = os.path.join(_backend_root, _rel).replace("\\", "/")
        db_url = "sqlite:///" + _rel
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Reusa a engine do aplicativo, ja com a URL do SQLite resolvida (caminho absoluto)
    from app.database import engine as app_engine

    connectable = app_engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

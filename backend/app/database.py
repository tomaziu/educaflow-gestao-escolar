from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base


_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite:///"):
    _relativo = _db_url[len("sqlite:///"):]
    if not os.path.isabs(_relativo):
        _aqui = os.path.dirname(os.path.abspath(__file__))          # backend/app
        _backend = os.path.dirname(_aqui)                            # backend
        _projeto = os.path.dirname(_backend)                         # raiz do projeto
        _relativo = os.path.join(_projeto, _relativo).replace("\\", "/")
        _db_url = "sqlite:///" + _relativo

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if _db_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_diretorio_dados() -> str:
    _aqui = os.path.dirname(os.path.abspath(__file__))           # backend/app
    _backend = os.path.dirname(_aqui)                            # backend
    _projeto = os.path.dirname(_backend)                         # raiz do projeto
    pasta_dados = os.path.join(_projeto, "data")
    os.makedirs(pasta_dados, exist_ok=True)
    return pasta_dados

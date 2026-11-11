from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings

_aqui = os.path.dirname(os.path.abspath(__file__))           # backend/app/core
_app = os.path.dirname(_aqui)                                # backend/app
_backend = os.path.dirname(_app)                             # backend
_projeto = os.path.dirname(_backend)                         # raiz do projeto
_ENV_FILE = os.path.join(_projeto, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "EducaFlow"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./data/educaflow.db"

    SECRET_KEY: str = "educaflow-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str | None = None

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8-sig"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

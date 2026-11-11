from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(senha: str) -> str:
    # bcrypt considera apenas os primeiros 72 bytes; truncamos para evitar erro
    return pwd_context.hash(senha[:72])


def verify_password(senha_plana: str, hash_armazenado: str) -> bool:
    return pwd_context.verify(senha_plana[:72], hash_armazenado)


def criar_token_acesso(dados: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    para_codificar = dados.copy()
    expira = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    para_codificar.update({"exp": expira})
    return jwt.encode(para_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

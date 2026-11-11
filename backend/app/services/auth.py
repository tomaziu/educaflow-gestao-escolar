from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.session import obter_sessao
from app.database import SessionLocal, get_db
from app.models.usuario import Usuario


def get_db_session() -> Session:
    return SessionLocal()


def obter_usuario_por_username(db: Session, username: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.username == username).first()


def autenticar_usuario(db: Session, username: str, senha: str) -> Optional[Usuario]:
    from app.core.security import verify_password

    usuario = obter_usuario_por_username(db, username)
    if not usuario:
        return None
    if not verify_password(senha, usuario.senha_hash):
        return None
    if usuario.status != "ativo":
        return None
    return usuario


def usuario_id_da_sessao(request: Request) -> Optional[int]:
    session_id = request.cookies.get("educaflow_session")
    sessao = obter_sessao(session_id)
    if not sessao:
        return None
    return sessao["user_id"]


def usuario_atual(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    user_id = usuario_id_da_sessao(request)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None or usuario.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def requer_admin(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if usuario.perfil != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return usuario


def verificar_csrf(request: Request) -> None:
    if request.method.upper() in ("GET", "HEAD", "OPTIONS"):
        return
    session_id = request.cookies.get("educaflow_session")
    sessao = obter_sessao(session_id) if session_id else None
    if not sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Entre novamente.",
        )
    token = request.headers.get("X-CSRF-Token")
    if not token or token != sessao["csrf"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token CSRF inválido.",
        )

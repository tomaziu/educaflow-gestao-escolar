from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.session import nova_sessao, obter_sessao, remover_sessao
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioLogin, UsuarioOut
from app.services.auth import (
    autenticar_usuario,
    obter_usuario_por_username,
    requer_admin,
    usuario_atual,
    verificar_csrf,
)
from app.core.security import hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _usuario_dados(usuario: Usuario, csrf_token: str | None = None) -> dict:
    perfil = usuario.perfil or "secretaria"
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "username": usuario.username,
        "perfil": perfil,
        "tipo": "administrador" if perfil == "administrador" else "secretaria",
        "perfil_label": "Administrador" if perfil == "administrador" else "Secretária escolar",
    }


def _definir_cookies(resposta: Response, session_id: str) -> None:
    resposta.set_cookie(
        key="educaflow_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 7,
    )


def _limpar_cookies(resposta: Response) -> None:
    resposta.delete_cookie(key="educaflow_session", path="/")
    resposta.delete_cookie(key="educaflow_csrf", path="/")


def _ler_credenciais(dados: UsuarioLogin) -> tuple[str, str]:
    identificador = (dados.identificador or "").strip()
    senha = dados.senha or ""
    return identificador, senha


@router.post("/login")
async def login(
    dados: UsuarioLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    identificador, senha = _ler_credenciais(dados)
    usuario = autenticar_usuario(db, identificador, senha)
    if not usuario:
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "Usuário ou senha inválidos.", "code": "invalid_credentials"}},
        )
    if usuario.status != "ativo":
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "Usuário inativo.", "code": "user_inactive"}},
        )
    session_id, csrf = nova_sessao(usuario.id)
    _definir_cookies(response, session_id)
    return {
        "data": {
            "csrfToken": csrf,
            "usuario": _usuario_dados(usuario, csrf),
        }
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("educaflow_session")
    remover_sessao(session_id)
    _limpar_cookies(response)
    return {"data": {"ok": True}}


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("educaflow_session")
    sessao = obter_sessao(session_id) if session_id else None
    user_id = sessao["user_id"] if sessao else None
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "Não autenticado.", "code": "not_authenticated"}},
        )
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario or usuario.status != "ativo":
        resposta = JSONResponse(
            status_code=401,
            content={"error": {"message": "Sessão inválida.", "code": "invalid_session"}},
        )
        _limpar_cookies(resposta)
        return resposta
    csrf = sessao["csrf"]
    return {
        "data": {
            "csrfToken": csrf,
            "usuario": _usuario_dados(usuario, csrf),
        }
    }


@router.post("/registro")
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requer_admin),
    __: None = Depends(verificar_csrf),
):
    if obter_usuario_por_username(db, dados.username):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Usuário já existe.", "code": "username_exists"}},
        )
    usuario = Usuario(
        nome=dados.nome,
        username=dados.username,
        senha_hash=hash_password(dados.senha),
        perfil=dados.perfil or "secretaria",
        status=dados.status or "ativo",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"data": UsuarioOut.model_validate(usuario)}

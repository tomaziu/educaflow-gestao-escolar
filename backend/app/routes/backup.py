from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, criar_diretorio_dados
from app.core.config import settings
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual, verificar_csrf

router = APIRouter(prefix="/api/backup", tags=["backup"])

PASTA_BACKUPS = "backups"


def _caminho_banco() -> str:
    if settings.DATABASE_URL.startswith("sqlite:///"):
        return settings.DATABASE_URL.replace("sqlite:///", "", 1)
    return settings.DATABASE_URL


def _garantir_pasta_backups(projeto_dir: str) -> str:
    pasta = os.path.join(projeto_dir, PASTA_BACKUPS)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _projeto_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # backend/app/routes -> backend -> projeto
    return os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))


@router.post("/criar")
def criar_backup(
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    projeto_dir = _projeto_dir()
    caminho_banco = _caminho_banco()
    # resolver caminho relativo ao projeto
    if not os.path.isabs(caminho_banco):
        caminho_banco = os.path.join(projeto_dir, caminho_banco)
    if not os.path.exists(caminho_banco):
        return JSONResponse(status_code=404, content={"error": {"message": "Banco de dados não encontrado.", "code": "not_found"}})
    pasta = _garantir_pasta_backups(projeto_dir)
    nome = f"educaflow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    destino = os.path.join(pasta, nome)
    shutil.copy2(caminho_banco, destino)
    return {"data": {"arquivo": nome, "caminho": destino, "criado_em": datetime.now().isoformat()}}


@router.get("/listar")
def listar_backups(_: UsuarioOut = Depends(usuario_atual)):
    projeto_dir = _projeto_dir()
    pasta = os.path.join(projeto_dir, PASTA_BACKUPS)
    if not os.path.exists(pasta):
        return {"data": []}
    arquivos = []
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith(".db"):
            caminho = os.path.join(pasta, nome)
            arquivos.append({
                "arquivo": nome,
                "tamanho": os.path.getsize(caminho),
                "criado_em": datetime.fromtimestamp(os.path.getctime(caminho)).isoformat(),
            })
    return {"data": arquivos}


@router.post("/restaurar")
def restaurar_backup(
    corpo: dict,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    nome = corpo.get("arquivo")
    if not nome:
        return JSONResponse(status_code=400, content={"error": {"message": "Informe o arquivo de backup.", "code": "invalido"}})
    projeto_dir = _projeto_dir()
    pasta = os.path.join(projeto_dir, PASTA_BACKUPS)
    origem = os.path.join(pasta, nome)
    if not os.path.exists(origem):
        return JSONResponse(status_code=404, content={"error": {"message": "Backup não encontrado.", "code": "not_found"}})
    caminho_banco = _caminho_banco()
    if not os.path.isabs(caminho_banco):
        caminho_banco = os.path.join(projeto_dir, caminho_banco)
    # preserva o banco atual antes de restaurar
    if os.path.exists(caminho_banco):
        shutil.copy2(caminho_banco, caminho_banco + ".pre-restore")
    shutil.copy2(origem, caminho_banco)
    return {"data": {"ok": True, "restaurado": nome}}

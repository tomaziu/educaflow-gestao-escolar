from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from pathlib import Path

from app.core.config import settings
from app.database import engine, Base, criar_diretorio_dados
from app.models import usuario, aluno, responsavel, aluno_responsavel, turma, matricula  # noqa: F401

from app.routes import auth, alunos, responsaveis, turmas, matriculas, relatorios, backup  # noqa: F401

app = FastAPI(title="EducaFlow", version="1.0.0")

# Rotas da API
app.include_router(auth.router)
app.include_router(alunos.router)
app.include_router(responsaveis.router)
app.include_router(turmas.router)
app.include_router(matriculas.router)
app.include_router(relatorios.router)
app.include_router(backup.router)


@app.on_event("startup")
def iniciar():
    criar_diretorio_dados()
    Base.metadata.create_all(bind=engine)


@app.get("/")
def raiz():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/status")
def status():
    return {"nome": settings.APP_NAME, "status": "online", "documentacao": "/docs"}


# Front-end estático
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"

if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/{caminho:path}")
def frontend(caminho: str):
    arquivo = FRONTEND_DIR / caminho
    if arquivo.exists() and arquivo.is_file():
        return FileResponse(str(arquivo))
    return FileResponse(str(FRONTEND_DIR / "index.html"))

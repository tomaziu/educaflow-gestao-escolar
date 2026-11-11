"""
Script de seed/inicializacao do EducaFlow.
- Carrega o .env
- Cria as tabelas (idempotente)
- Cria o usuario administrador inicial, se ainda nao existir
- Imprime as credenciais iniciais no terminal
"""
from __future__ import annotations

import os
import secrets
import string
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent          # backend/
PROJETO_DIR = BASE_DIR.parent                       # raiz do projeto
os.chdir(str(BASE_DIR))

load_dotenv(PROJETO_DIR / ".env", override=False, encoding="utf-8-sig")

import sys  # noqa: E402

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import engine, Base, SessionLocal  # noqa: E402
import app.models  # noqa: F401  (garante que os modelos estejam registrados)
from app.models.usuario import Usuario  # noqa: E402
from app.core.security import hash_password, verify_password  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Criar tabelas (idempotente)
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)


def _garantir_coluna_senha_customizada() -> None:
    """Garante a coluna senha_customizada em bancos criados antes da migracao 002."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "usuarios" not in insp.get_table_names():
        return
    if "senha_customizada" in {c["name"] for c in insp.get_columns("usuarios")}:
        return
    with engine.begin() as conexao:
        conexao.execute(text("ALTER TABLE usuarios ADD COLUMN senha_customizada BOOLEAN NOT NULL DEFAULT 0"))
    print("[EducaFlow] Coluna senha_customizada adicionada a tabela usuarios.")


_garantir_coluna_senha_customizada()

# ---------------------------------------------------------------------------
# 2. Criar administrador inicial
# ---------------------------------------------------------------------------
db = SessionLocal()
try:
    username = os.getenv("ADMIN_USERNAME", "admin")
    senha = os.getenv("ADMIN_PASSWORD")
    gerada = False
    senha_explicita = bool(senha)
    if not senha:
        alfabeto = string.ascii_letters + string.digits + "!@#$%&*"
        senha = "".join(secrets.choice(alfabeto) for _ in range(16))
        gerada = True

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        usuario = Usuario(
            nome="Administrador",
            username=username,
            senha_hash=hash_password(senha),
            perfil="administrador",
            status="ativo",
        )
        db.add(usuario)
        db.commit()
        print(f"[EducaFlow] Usuario administrador criado: {username}")
        print(f"[EducaFlow] Login: {username}")
        print(f"[EducaFlow] Senha: {senha}")
    else:
        # Só sincroniza com o .env se a senha ainda não foi trocada pelo usuário
        if senha_explicita and not usuario.senha_customizada and not verify_password(senha, usuario.senha_hash):
            usuario.senha_hash = hash_password(senha)
            db.commit()
            print(f"[EducaFlow] Senha do administrador sincronizada com o arquivo .env.")
            print(f"[EducaFlow] Login: {username}")
            print(f"[EducaFlow] Senha: {senha}")
        else:
            print(f"[EducaFlow] Usuario administrador ja existe: {username}")
            if usuario.senha_customizada:
                print("[EducaFlow] A senha foi alterada pelo usuario e nao e sobrescrita pelo .env.")

    if gerada:
        print("[EducaFlow] ATENCAO: senha gerada automaticamente. Alteracao no primeiro acesso e recomendada.")
finally:
    db.close()

print("[EducaFlow] Banco de dados pronto.")

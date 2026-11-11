from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic.functional_validators import BeforeValidator


def _vazio_para_none(valor):
    if valor is None:
        return None
    if isinstance(valor, str) and valor.strip() == "":
        return None
    return valor


def _nao_vazio(valor):
    if valor is None:
        raise ValueError("campo obrigatório não pode ser vazio")
    if isinstance(valor, str) and valor.strip() == "":
        raise ValueError("campo obrigatório não pode ser vazio")
    return valor


StrOuNone = Annotated[str | None, BeforeValidator(_vazio_para_none)]
NaoVazio = Annotated[str, BeforeValidator(_nao_vazio)]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioBase(BaseModel):
    nome: NaoVazio = Field(..., max_length=200)
    username: NaoVazio = Field(..., max_length=100)
    perfil: str = Field(default="secretaria", max_length=50)
    status: str = Field(default="ativo", max_length=20)


class UsuarioCreate(UsuarioBase):
    senha: NaoVazio = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nome: StrOuNone = None
    username: StrOuNone = None
    senha: StrOuNone = None
    perfil: StrOuNone = None
    status: StrOuNone = None


class UsuarioOut(UsuarioBase):
    id: int

    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    identificador: NaoVazio
    senha: NaoVazio


class SenhaTroca(BaseModel):
    senha_atual: NaoVazio = Field(..., min_length=1)
    nova_senha: NaoVazio = Field(..., min_length=6, max_length=72)
    confirmacao: NaoVazio = Field(..., min_length=1)


class SenhaRedefinicao(BaseModel):
    nova_senha: NaoVazio = Field(..., min_length=6, max_length=72)
    confirmacao: NaoVazio = Field(..., min_length=1)


class UsuarioMe(BaseModel):
    id: int
    nome: str
    username: str
    perfil: str
    tipo: str
    perfil_label: str
    csrf_token: str | None = None

    class Config:
        from_attributes = True


class Paginated(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    total_pages: int

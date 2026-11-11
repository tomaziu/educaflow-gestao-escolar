from __future__ import annotations

from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic.functional_validators import BeforeValidator

from app.schemas.usuario import UsuarioOut


def _only_digits(valor):
    if valor is None:
        return None
    s = str(valor)
    if s.strip() == "":
        return None
    return "".join(ch for ch in s if ch.isdigit())


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


def _int_ou_none_str(valor):
    if valor is None:
        return None
    if isinstance(valor, str) and valor.strip() == "":
        return None
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


StrOuNone = Annotated[str | None, BeforeValidator(_vazio_para_none)]
NaoVazio = Annotated[str, BeforeValidator(_nao_vazio)]
IntOuNone = Annotated[int | None, BeforeValidator(_int_ou_none_str)]


class ResponsavelBase(BaseModel):
    nome_completo: NaoVazio = Field(..., max_length=255)
    cpf: NaoVazio = Field(..., max_length=20)
    telefone: StrOuNone = None
    email: StrOuNone = None
    endereco: StrOuNone = None
    numero: StrOuNone = None
    bairro: StrOuNone = None
    cidade: StrOuNone = None
    estado: StrOuNone = None
    cep: StrOuNone = None

    @field_validator("cpf", mode="before")
    @classmethod
    def normalizar_cpf(cls, v):
        return _only_digits(v)


class ResponsavelCreate(ResponsavelBase):
    aluno_id: IntOuNone = None


class ResponsavelUpdate(BaseModel):
    nome_completo: StrOuNone = None
    cpf: StrOuNone = None
    telefone: StrOuNone = None
    email: StrOuNone = None
    endereco: StrOuNone = None
    numero: StrOuNone = None
    bairro: StrOuNone = None
    cidade: StrOuNone = None
    estado: StrOuNone = None
    cep: StrOuNone = None
    aluno_id: IntOuNone = None

    @field_validator("cpf", mode="before")
    @classmethod
    def normalizar_cpf(cls, v):
        return _only_digits(v)


class AlunoResumo(BaseModel):
    id: int
    nome: str

    class Config:
        from_attributes = True


class ResponsavelOut(BaseModel):
    id: int
    nome_completo: str
    cpf: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    alunos: List[AlunoResumo] = []
    total_alunos: int = 0

    class Config:
        from_attributes = True

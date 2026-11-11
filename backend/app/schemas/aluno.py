from __future__ import annotations

from datetime import date
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


def _int_ou_none_str(valor):
    if valor is None:
        return None
    if isinstance(valor, str) and valor.strip() == "":
        return None
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


def _int_ou_padrao_str(valor):
    if valor is None:
        return 30
    if isinstance(valor, str) and valor.strip() == "":
        return 30
    try:
        return int(valor)
    except (ValueError, TypeError):
        return 30


def _nao_vazio(valor):
    if valor is None:
        raise ValueError("campo obrigatório não pode ser vazio")
    if isinstance(valor, str) and valor.strip() == "":
        raise ValueError("campo obrigatório não pode ser vazio")
    return valor


StrOuNone = Annotated[str | None, BeforeValidator(_vazio_para_none)]
IntOuNone = Annotated[int | None, BeforeValidator(_int_ou_none_str)]
IntOuPadrao = Annotated[int, BeforeValidator(_int_ou_padrao_str)]
NaoVazio = Annotated[str, BeforeValidator(_nao_vazio)]


class AlunoBase(BaseModel):
    nome_completo: NaoVazio = Field(..., max_length=255)
    data_nascimento: Optional[date] = None
    cpf: NaoVazio = Field(..., max_length=20)
    telefone: StrOuNone = None
    email: StrOuNone = None
    endereco: StrOuNone = None
    numero: StrOuNone = None
    bairro: StrOuNone = None
    cidade: StrOuNone = None
    estado: StrOuNone = None
    cep: StrOuNone = None
    rg: StrOuNone = None
    situacao: StrOuNone = "ativo"

    @field_validator("data_nascimento", mode="before")
    @classmethod
    def _data_vazia_para_none(cls, v):
        return _vazio_para_none(v)

    @field_validator("cpf", mode="before")
    @classmethod
    def normalizar_cpf(cls, v):
        return _only_digits(v)


class AlunoCreate(AlunoBase):
    responsavel_id: IntOuNone = None
    turma_id: IntOuNone = None


class AlunoUpdate(BaseModel):
    nome_completo: StrOuNone = None
    data_nascimento: Optional[date] = None
    cpf: StrOuNone = None
    telefone: StrOuNone = None
    email: StrOuNone = None
    endereco: StrOuNone = None
    numero: StrOuNone = None
    bairro: StrOuNone = None
    cidade: StrOuNone = None
    estado: StrOuNone = None
    cep: StrOuNone = None
    rg: StrOuNone = None
    situacao: StrOuNone = None
    responsavel_id: IntOuNone = None
    turma_id: IntOuNone = None

    @field_validator("data_nascimento", mode="before")
    @classmethod
    def _data_vazia_para_none(cls, v):
        return _vazio_para_none(v)

    @field_validator("cpf", mode="before")
    @classmethod
    def normalizar_cpf(cls, v):
        return _only_digits(v)


class ResponsavelResumo(BaseModel):
    id: int
    nome: str
    principal: bool = False

    class Config:
        from_attributes = True


class MatriculaResumo(BaseModel):
    id: int
    ano_letivo: str
    turma: str
    situacao: str

    class Config:
        from_attributes = True


class AlunoOut(BaseModel):
    id: int
    nome_completo: str
    data_nascimento: Optional[date] = None
    cpf: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    rg: Optional[str] = None
    situacao: str
    responsaveis: List[ResponsavelResumo] = []
    matriculas: List[MatriculaResumo] = []

    class Config:
        from_attributes = True

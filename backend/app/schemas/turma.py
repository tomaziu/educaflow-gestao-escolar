from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator
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


def _int_ou_padrao_str(valor):
    if valor is None:
        return "30"
    if isinstance(valor, str) and valor.strip() == "":
        return "30"
    try:
        return str(int(valor))
    except (ValueError, TypeError):
        return "30"


StrOuNone = Annotated[str | None, BeforeValidator(_vazio_para_none)]
NaoVazio = Annotated[str, BeforeValidator(_nao_vazio)]


def _capacidade(valor) -> Optional[int]:
    if valor is None:
        return None
    if isinstance(valor, str) and valor.strip() == "":
        return None
    try:
        numero = int(valor)
    except (ValueError, TypeError):
        return None
    return numero if numero > 0 else None


Capacidade = Annotated[Optional[int], BeforeValidator(_capacidade)]


class TurmaBase(BaseModel):
    nome: NaoVazio = Field(..., max_length=100)
    turno: NaoVazio = Field(..., max_length=30)
    ano_letivo: NaoVazio = Field(..., max_length=10)
    capacidade_maxima: Capacidade = None
    cap_maxima: str = Field("30", max_length=10)
    sala: StrOuNone = None
    descricao: StrOuNone = None
    situacao: StrOuNone = "ativa"

    @field_validator("nome", "turno", "ano_letivo", mode="before")
    @classmethod
    def _str_obrigatorio_nao_vazio(cls, v):
        if v is None:
            raise ValueError("campo obrigatório não pode ser vazio")
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("campo obrigatório não pode ser vazio")
        return v

    @field_validator("cap_maxima", mode="before")
    @classmethod
    def _cap_maxima(cls, v):
        if v is None:
            return "30"
        if isinstance(v, str) and v.strip() == "":
            return "30"
        try:
            return str(int(v))
        except (ValueError, TypeError):
            return "30"

    @field_validator("sala", "descricao", mode="before")
    @classmethod
    def _str_vazio_para_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class TurmaCreate(TurmaBase):
    pass


class TurmaUpdate(BaseModel):
    nome: StrOuNone = None
    turno: StrOuNone = None
    ano_letivo: StrOuNone = None
    capacidade_maxima: Capacidade = None
    cap_maxima: str = Field("30", max_length=10)
    sala: StrOuNone = None
    descricao: StrOuNone = None
    situacao: StrOuNone = None

    @field_validator("cap_maxima", mode="before")
    @classmethod
    def _cap_maxima(cls, v):
        if v is None:
            return "30"
        if isinstance(v, str) and v.strip() == "":
            return "30"
        try:
            return str(int(v))
        except (ValueError, TypeError):
            return "30"

    @field_validator("sala", "descricao", mode="before")
    @classmethod
    def _str_vazio_para_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class TurmaOut(BaseModel):
    id: int
    nome: str
    turno: str
    ano_letivo: str
    capacidade_maxima: int
    sala: Optional[str] = None
    descricao: Optional[str] = None
    situacao: str
    matriculados: int = 0
    vagas_disponiveis: int = 0

    class Config:
        from_attributes = True


class TurmaResumo(BaseModel):
    total_ativas: int
    vagas_disponiveis: int
    turnos: int
    turnos_nomes: str

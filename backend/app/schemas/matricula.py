from __future__ import annotations

from datetime import date
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic.functional_validators import BeforeValidator


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


def _nao_vazio(valor):
    if valor is None:
        raise ValueError("campo obrigatório não pode ser vazio")
    if isinstance(valor, str) and valor.strip() == "":
        raise ValueError("campo obrigatório não pode ser vazio")
    return valor


StrOuNone = Annotated[str | None, BeforeValidator(_vazio_para_none)]
IntOuNone = Annotated[int | None, BeforeValidator(_int_ou_none_str)]
NaoVazio = Annotated[str, BeforeValidator(_nao_vazio)]


class MatriculaBase(BaseModel):
    aluno_id: IntOuNone = None
    turma_id: IntOuNone = None
    data_matricula: Optional[date] = None
    ano_letivo: StrOuNone = None
    situacao: StrOuNone = "ativa"

    @field_validator("data_matricula", mode="before")
    @classmethod
    def _data_vazia_para_none(cls, v):
        return _vazio_para_none(v)

    @field_validator("ano_letivo", "situacao", mode="before")
    @classmethod
    def _str_vazio_para_none(cls, v):
        return _vazio_para_none(v)


class MatriculaCreate(MatriculaBase):
    pass


class MatriculaUpdate(MatriculaBase):
    pass


class MatriculaOut(BaseModel):
    id: int
    aluno_id: Optional[int] = None
    aluno: Optional[str] = None
    aluno_cpf: Optional[str] = None
    turma_id: Optional[int] = None
    turma: Optional[str] = None
    turno: Optional[str] = None
    ano_letivo: Optional[str] = None
    data_matricula: Optional[date] = None
    data_matricula_br: Optional[str] = None
    situacao: Optional[str] = None
    responsaveis: Optional[str] = None

    class Config:
        from_attributes = True


class MatriculaResumo(BaseModel):
    total: int
    ativas: int
    pendentes: int
    canceladas: int
    percentual_confirmadas: float
    anos: list[int]
    ano: int | None = None

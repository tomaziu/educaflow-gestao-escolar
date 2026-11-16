from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RelatorioOpcoes(BaseModel):
    anos: list[int]
    turmas: list[dict]
    situacoes: list[str]


class RelatorioDados(BaseModel):
    titulo: str
    subtitulo: str
    gerado_em: str
    filtros_aplicados: Optional[str] = None
    colunas: list[dict]
    linhas: list[list]
    total: int
    truncado: bool = False

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Turma(Base):
    __tablename__ = "turmas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    turno: Mapped[str] = mapped_column(String(30), nullable=False)
    ano_letivo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    capacidade_maxima: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sala: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    situacao: Mapped[str] = mapped_column(String(20), default="ativa", nullable=False)

    matriculas: Mapped[list["Matricula"]] = relationship(
        "Matricula", back_populates="turma", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Turma(id={self.id}, nome={self.nome})>"

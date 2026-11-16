from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Matricula(Base):
    __tablename__ = "matriculas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    turma_id: Mapped[int] = mapped_column(
        ForeignKey("turmas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    data_matricula: Mapped[date] = mapped_column(Date, nullable=False)
    ano_letivo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    situacao: Mapped[str] = mapped_column(String(20), default="ativa", nullable=False)

    aluno: Mapped["Aluno"] = relationship("Aluno", back_populates="matriculas")
    turma: Mapped["Turma"] = relationship("Turma", back_populates="matriculas")

    def __repr__(self) -> str:
        return f"<Matricula(id={self.id}, aluno={self.aluno_id}, turma={self.turma_id})>"

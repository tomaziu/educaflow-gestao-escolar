from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Aluno(Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome_completo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cpf: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cep: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    rg: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    situacao: Mapped[str] = mapped_column(String(20), default="ativo", nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    responsaveis: Mapped[list["AlunoResponsavel"]] = relationship(
        "AlunoResponsavel", back_populates="aluno", cascade="all, delete-orphan"
    )
    matriculas: Mapped[list["Matricula"]] = relationship(
        "Matricula", back_populates="aluno", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Aluno(id={self.id}, nome={self.nome_completo})>"

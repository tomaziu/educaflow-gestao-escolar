from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Responsavel(Base):
    __tablename__ = "responsaveis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome_completo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cep: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    alunos: Mapped[list["AlunoResponsavel"]] = relationship(
        "AlunoResponsavel", back_populates="responsavel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Responsavel(id={self.id}, nome={self.nome_completo})>"

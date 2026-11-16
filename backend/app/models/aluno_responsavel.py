from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AlunoResponsavel(Base):
    __tablename__ = "aluno_responsavel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    responsavel_id: Mapped[int] = mapped_column(
        ForeignKey("responsaveis.id", ondelete="CASCADE"), index=True, nullable=False
    )
    grau_parentesco: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    principal: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        # evita duplicidade de vinculo aluno-responsavel
        {"sqlite_autoincrement": True},
    )

    aluno: Mapped["Aluno"] = relationship("Aluno", back_populates="responsaveis")
    responsavel: Mapped["Responsavel"] = relationship("Responsavel", back_populates="alunos")

    def __repr__(self) -> str:
        return f"<AlunoResponsavel(aluno={self.aluno_id}, responsavel={self.responsavel_id})>"

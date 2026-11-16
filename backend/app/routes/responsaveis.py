from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, or_

from app.database import get_db
from app.models.responsavel import Responsavel
from app.models.aluno_responsavel import AlunoResponsavel
from app.models.aluno import Aluno
from app.schemas.responsavel import ResponsavelCreate, ResponsavelUpdate, ResponsavelOut
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual, verificar_csrf

router = APIRouter(prefix="/api/responsaveis", tags=["responsaveis"])


def _para_saida(responsavel: Responsavel) -> dict:
    vinculos = responsavel.alunos or []
    alunos_nomes = []
    for v in vinculos:
        a = v.aluno
        if a:
            alunos_nomes.append(a.nome_completo)
    return {
        "id": responsavel.id,
        "nome_completo": responsavel.nome_completo,
        "cpf": responsavel.cpf,
        "telefone": responsavel.telefone,
        "email": responsavel.email,
        "endereco": responsavel.endereco,
        "numero": responsavel.numero,
        "bairro": responsavel.bairro,
        "cidade": responsavel.cidade,
        "estado": responsavel.estado,
        "cep": responsavel.cep,
        "alunos": ", ".join(alunos_nomes) if alunos_nomes else "—",
        "total_alunos": len([a for a in (responsavel.alunos or []) if a]),
    }


@router.get("")
def listar_responsaveis(
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=500),
    q: Optional[str] = Query(None),
):
    query = db.query(Responsavel).options(selectinload(Responsavel.alunos).joinedload(AlunoResponsavel.aluno))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Responsavel.nome_completo.ilike(like), Responsavel.cpf.ilike(like)))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    return {
        "data": {
            "items": [_para_saida(r) for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    }


@router.get("/{responsavel_id}")
def obter_responsavel(responsavel_id: int, db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    responsavel = (
        db.query(Responsavel)
        .options(selectinload(Responsavel.alunos).joinedload(AlunoResponsavel.aluno))
        .filter(Responsavel.id == responsavel_id)
        .first()
    )
    if not responsavel:
        return JSONResponse(status_code=404, content={"error": {"message": "Responsável não encontrado.", "code": "not_found"}})
    return {"data": _para_saida(responsavel)}


def _vincular_aluno(db: Session, responsavel: Responsavel, aluno_id: Optional[int]) -> None:
    if not aluno_id:
        return
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return
    existente = (
        db.query(AlunoResponsavel)
        .filter(
            AlunoResponsavel.responsavel_id == responsavel.id,
            AlunoResponsavel.aluno_id == aluno_id,
        )
        .first()
    )
    if existente:
        return
    db.add(
        AlunoResponsavel(
            aluno_id=aluno_id,
            responsavel_id=responsavel.id,
            principal=not db.query(AlunoResponsavel)
            .filter(AlunoResponsavel.aluno_id == aluno_id)
            .first(),
        )
    )


@router.post("")
def criar_responsavel(
    dados: ResponsavelCreate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    existente = db.query(Responsavel).filter(Responsavel.cpf == dados.cpf).first()
    if existente:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Já existe um responsável com este CPF.", "code": "cpf_duplicado", "field": "cpf"}},
        )
    dados_dict = dados.model_dump(exclude_unset=True)
    aluno_id = dados_dict.pop("aluno_id", None)
    responsavel = Responsavel(**dados_dict)
    db.add(responsavel)
    db.commit()
    db.refresh(responsavel)
    _vincular_aluno(db, responsavel, aluno_id)
    db.commit()
    db.refresh(responsavel)
    return {"data": _para_saida(responsavel)}


@router.put("/{responsavel_id}")
def atualizar_responsavel(
    responsavel_id: int,
    dados: ResponsavelUpdate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    responsavel = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
    if not responsavel:
        return JSONResponse(status_code=404, content={"error": {"message": "Responsável não encontrado.", "code": "not_found"}})
    if dados.cpf and dados.cpf != responsavel.cpf:
        existente = db.query(Responsavel).filter(Responsavel.cpf == dados.cpf).first()
        if existente:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": "CPF já cadastrado para outro responsável.", "code": "cpf_duplicado", "field": "cpf"}},
            )
    valores = dados.model_dump(exclude_unset=True)
    aluno_id = valores.pop("aluno_id", None)
    for campo, valor in valores.items():
        setattr(responsavel, campo, valor)
    db.commit()
    db.refresh(responsavel)
    _vincular_aluno(db, responsavel, aluno_id)
    db.commit()
    db.refresh(responsavel)
    return {"data": _para_saida(responsavel)}


@router.delete("/{responsavel_id}")
def excluir_responsavel(
    responsavel_id: int,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    responsavel = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
    if not responsavel:
        return JSONResponse(status_code=404, content={"error": {"message": "Responsável não encontrado.", "code": "not_found"}})
    db.delete(responsavel)
    db.commit()
    return {"data": {"ok": True}}

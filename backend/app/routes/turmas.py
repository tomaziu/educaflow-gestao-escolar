from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, or_

from app.database import get_db
from app.models.turma import Turma
from app.models.matricula import Matricula
from app.schemas.turma import TurmaCreate, TurmaUpdate, TurmaOut, TurmaResumo
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual, verificar_csrf

router = APIRouter(prefix="/api/turmas", tags=["turmas"])


def _contar_matriculados(db: Session, turma_id: int) -> int:
    return (
        db.query(func.count(Matricula.id))
        .filter(Matricula.turma_id == turma_id, Matricula.situacao.in_(["ativa", "pendente"]))
        .scalar()
        or 0
    )


def _para_saida(turma: Turma, db: Session) -> dict:
    matriculados = _contar_matriculados(db, turma.id)
    return {
        "id": turma.id,
        "nome": turma.nome,
        "turno": turma.turno,
        "ano_letivo": turma.ano_letivo,
        "capacidade_maxima": turma.capacidade_maxima,
        "sala": turma.sala,
        "descricao": turma.descricao,
        "situacao": turma.situacao,
        "matriculados": matriculados,
        "vagas_disponiveis": max(0, turma.capacidade_maxima - matriculados),
    }


@router.get("")
def listar_turmas(
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=500),
    q: Optional[str] = Query(None),
    ano: Optional[str] = Query(None),
    situacao: Optional[str] = Query(None),
    turno: Optional[str] = Query(None),
    todas: Optional[str] = Query(None),
):
    query = db.query(Turma)
    if q:
        like = f"%{q}%"
        query = query.filter(Turma.nome.ilike(like))
    if ano:
        query = query.filter(Turma.ano_letivo == ano)
    if situacao:
        query = query.filter(Turma.situacao == situacao)
    if turno:
        query = query.filter(Turma.turno == turno)

    total = query.count()
    if todas and todas.lower() in ("1", "true", "sim"):
        items = query.all()
        total_pages = 1
        page_out = 1
        per_page_out = len(items)
    else:
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        page_out = page
        per_page_out = per_page

    return {
        "data": {
            "items": [_para_saida(t, db) for t in items],
            "total": total,
            "page": page_out,
            "per_page": per_page_out,
            "total_pages": total_pages,
        }
    }


@router.get("/resumo")
def resumo_turmas(db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    turmas = db.query(Turma).all()
    ativas = [t for t in turmas if t.situacao == "ativa"]
    vagas = 0
    turnos_nomes = []
    for t in ativas:
        vagas += max(0, t.capacidade_maxima - _contar_matriculados(db, t.id))
        if t.turno not in turnos_nomes:
            turnos_nomes.append(t.turno)
    return {
        "data": TurmaResumo(
            total_ativas=len(ativas),
            vagas_disponiveis=vagas,
            turnos=len(turnos_nomes),
            turnos_nomes=", ".join(turnos_nomes) if turnos_nomes else "Matutino, vespertino e integral",
        ).model_dump()
    }


@router.get("/{turma_id}")
def obter_turma(turma_id: int, db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        return JSONResponse(status_code=404, content={"error": {"message": "Turma não encontrada.", "code": "not_found"}})
    return {"data": _para_saida(turma, db)}


def _capacidade(dados_dict: dict) -> int:
    capacidade = dados_dict.pop("capacidade_maxima", None)
    legado = dados_dict.pop("cap_maxima", None)
    if capacidade is None and legado not in (None, ""):
        try:
            capacidade = int(legado)
        except (TypeError, ValueError):
            capacidade = None
    if capacidade is None:
        return 30
    return max(1, int(capacidade))


@router.post("")
def criar_turma(
    dados: TurmaCreate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    dados_dict = dados.model_dump(exclude_unset=True)
    dados_dict["capacidade_maxima"] = _capacidade(dados_dict)
    turma = Turma(**dados_dict)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return {"data": _para_saida(turma, db)}


@router.put("/{turma_id}")
def atualizar_turma(
    turma_id: int,
    dados: TurmaUpdate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        return JSONResponse(status_code=404, content={"error": {"message": "Turma não encontrada.", "code": "not_found"}})
    dados_dict = dados.model_dump(exclude_unset=True)
    if "capacidade_maxima" in dados_dict or "cap_maxima" in dados_dict:
        dados_dict["capacidade_maxima"] = _capacidade(dados_dict)
    for campo, valor in dados_dict.items():
        setattr(turma, campo, valor)
    db.commit()
    db.refresh(turma)
    return {"data": _para_saida(turma, db)}


@router.patch("/{turma_id}/situacao")
def alterar_situacao_turma(
    turma_id: int,
    corpo: dict,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        return JSONResponse(status_code=404, content={"error": {"message": "Turma não encontrada.", "code": "not_found"}})
    novo = corpo.get("situacao")
    if novo not in ("ativa", "inativa"):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Situação inválida.", "code": "situacao_invalida"}},
        )
    turma.situacao = novo
    db.commit()
    return {"data": {"situacao": turma.situacao}}


@router.delete("/{turma_id}")
def excluir_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        return JSONResponse(status_code=404, content={"error": {"message": "Turma não encontrada.", "code": "not_found"}})
    db.delete(turma)
    db.commit()
    return {"data": {"ok": True}}

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import or_, func

from app.database import get_db
from app.models.matricula import Matricula
from app.models.aluno import Aluno
from app.models.turma import Turma
from app.models.aluno_responsavel import AlunoResponsavel
from app.schemas.matricula import MatriculaCreate, MatriculaUpdate, MatriculaOut
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual, verificar_csrf

router = APIRouter(prefix="/api/matriculas", tags=["matriculas"])


def _data_br(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    return d.strftime("%d/%m/%Y")


def _para_saida(matricula: Matricula, db: Session) -> dict:
    aluno = matricula.aluno
    turma = matricula.turma
    responsaveis = []
    if aluno:
        for v in (aluno.responsaveis or []):
            r = v.responsavel
            if r:
                responsaveis.append(r.nome_completo)
    return {
        "id": matricula.id,
        "aluno_id": matricula.aluno_id,
        "aluno": aluno.nome_completo if aluno else "",
        "aluno_cpf": aluno.cpf if aluno else "",
        "turma_id": matricula.turma_id,
        "turma": turma.nome if turma else "",
        "turno": turma.turno if turma else "",
        "ano_letivo": matricula.ano_letivo,
        "data_matricula": matricula.data_matricula,
        "data_matricula_br": _data_br(matricula.data_matricula),
        "situacao": matricula.situacao,
        "responsaveis": ", ".join(responsaveis) if responsaveis else "",
    }


@router.get("")
def listar_matriculas(
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=500),
    q: Optional[str] = Query(None),
    ano: Optional[str] = Query(None),
    turma_id: Optional[int] = Query(None),
    situacao: Optional[str] = Query(None),
):
    query = db.query(Matricula).options(
        selectinload(Matricula.aluno),
        selectinload(Matricula.turma),
        selectinload(Matricula.aluno).selectinload(Aluno.responsaveis).joinedload(AlunoResponsavel.responsavel),
    )
    if q:
        like = f"%{q}%"
        query = query.join(Aluno, Aluno.id == Matricula.aluno_id).filter(
            or_(Aluno.nome_completo.ilike(like), Aluno.cpf.ilike(like))
        )
    if ano:
        query = query.filter(Matricula.ano_letivo == ano)
    if turma_id:
        query = query.filter(Matricula.turma_id == turma_id)
    if situacao:
        query = query.filter(Matricula.situacao == situacao)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    return {
        "data": {
            "items": [_para_saida(m, db) for m in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    }


@router.get("/resumo")
def resumo_matriculas(db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    ano_atual = date.today().year
    todas = db.query(Matricula).all()
    total = len(todas)
    ativas = len([m for m in todas if m.situacao == "ativa"])
    pendentes = len([m for m in todas if m.situacao == "pendente"])
    canceladas = len([m for m in todas if m.situacao == "cancelada"])
    percentual = round((ativas / total * 100) if total else 0, 1)
    anos = sorted({m.ano_letivo for m in todas})
    return {
        "data": {
            "total": total,
            "ativas": ativas,
            "pendentes": pendentes,
            "canceladas": canceladas,
            "percentual_confirmadas": percentual,
            "anos": anos,
            "ano": str(ano_atual),
        }
    }


@router.get("/{matricula_id}")
def obter_matricula(matricula_id: int, db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    matricula = (
        db.query(Matricula)
        .options(
            selectinload(Matricula.aluno).selectinload(Aluno.responsaveis).joinedload(AlunoResponsavel.responsavel),
            selectinload(Matricula.turma),
        )
        .filter(Matricula.id == matricula_id)
        .first()
    )
    if not matricula:
        return JSONResponse(status_code=404, content={"error": {"message": "Matrícula não encontrada.", "code": "not_found"}})
    return {"data": _para_saida(matricula, db)}


@router.post("")
def criar_matricula(
    dados: MatriculaCreate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    aluno_id = int(dados.aluno_id) if dados.aluno_id not in (None, "") else None
    turma_id = int(dados.turma_id) if dados.turma_id not in (None, "") else None
    if not aluno_id:
        return JSONResponse(status_code=400, content={"error": {"message": "Aluno é obrigatório.", "code": "aluno_obrigatorio", "field": "aluno_id"}})
    if not turma_id:
        return JSONResponse(status_code=400, content={"error": {"message": "Turma é obrigatória.", "code": "turma_obrigatoria", "field": "turma_id"}})
    if not dados.ano_letivo:
        return JSONResponse(status_code=400, content={"error": {"message": "Ano letivo é obrigatório.", "code": "ano_letivo_obrigatorio", "field": "ano_letivo"}})

    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return JSONResponse(status_code=404, content={"error": {"message": "Aluno não encontrado.", "code": "not_found"}})
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        return JSONResponse(status_code=404, content={"error": {"message": "Turma não encontrada.", "code": "not_found"}})

    ano = dados.ano_letivo or turma.ano_letivo

    # impede matrícula duplicada do mesmo aluno no mesmo ano letivo (ativa ou pendente)
    existente = (
        db.query(Matricula)
        .filter(
            Matricula.aluno_id == aluno_id,
            Matricula.ano_letivo == ano,
            Matricula.situacao.in_(["ativa", "pendente"]),
        )
        .first()
    )
    if existente:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Este aluno já possui matrícula neste ano letivo.", "code": "matricula_duplicada"}},
        )

    # respeita capacidade da turma
    ocupadas = (
        db.query(func.count(Matricula.id))
        .filter(Matricula.turma_id == turma_id, Matricula.situacao.in_(["ativa", "pendente"]))
        .scalar()
        or 0
    )
    if ocupadas >= turma.capacidade_maxima:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "A turma já atingiu a capacidade máxima.", "code": "capacidade_esgotada"}},
        )

    matricula = Matricula(
        aluno_id=aluno_id,
        turma_id=turma_id,
        data_matricula=dados.data_matricula or date.today(),
        ano_letivo=ano,
        situacao=dados.situacao or "ativa",
    )
    db.add(matricula)
    db.commit()
    db.refresh(matricula)
    db.refresh(matricula, attribute_names=["aluno", "turma"])
    return {"data": _para_saida(matricula, db)}


@router.put("/{matricula_id}")
def atualizar_matricula(
    matricula_id: int,
    dados: MatriculaUpdate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if not matricula:
        return JSONResponse(status_code=404, content={"error": {"message": "Matrícula não encontrada.", "code": "not_found"}})
    valores = dados.model_dump(exclude_unset=True)
    if "aluno_id" in valores and valores["aluno_id"] not in (None, ""):
        matricula.aluno_id = int(valores["aluno_id"])
    if "turma_id" in valores and valores["turma_id"] not in (None, ""):
        matricula.turma_id = int(valores["turma_id"])
    if "data_matricula" in valores:
        matricula.data_matricula = valores["data_matricula"]
    if "ano_letivo" in valores and valores["ano_letivo"] is not None:
        matricula.ano_letivo = valores["ano_letivo"]
    if "situacao" in valores and valores["situacao"] is not None:
        matricula.situacao = valores["situacao"]
    db.commit()
    db.refresh(matricula)
    db.refresh(matricula, attribute_names=["aluno", "turma"])
    return {"data": _para_saida(matricula, db)}


@router.post("/{matricula_id}/cancelar")
def cancelar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if not matricula:
        return JSONResponse(status_code=404, content={"error": {"message": "Matrícula não encontrada.", "code": "not_found"}})
    matricula.situacao = "cancelada"
    db.commit()
    return {"data": {"situacao": matricula.situacao}}


@router.delete("/{matricula_id}")
def excluir_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if not matricula:
        return JSONResponse(status_code=404, content={"error": {"message": "Matrícula não encontrada.", "code": "not_found"}})
    db.delete(matricula)
    db.commit()
    return {"data": {"ok": True}}

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_

from app.database import get_db
from app.models.aluno import Aluno
from app.models.turma import Turma
from app.models.matricula import Matricula
from app.models.responsavel import Responsavel
from app.models.aluno_responsavel import AlunoResponsavel
from app.schemas.aluno import AlunoCreate, AlunoUpdate, AlunoOut
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual, verificar_csrf

router = APIRouter(prefix="/api/alunos", tags=["alunos"])


def _data_br(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    return d.strftime("%d/%m/%Y")


def _para_saida(aluno: Aluno) -> dict:
    responsaveis = [
        {
            "id": r.responsavel_id,
            "nome": r.responsavel.nome_completo if r.responsavel else "",
            "principal": bool(r.principal),
        }
        for r in (aluno.responsaveis or [])
    ]
    matriculas = [
        {
            "id": m.id,
            "ano_letivo": m.ano_letivo,
            "turma": m.turma.nome if m.turma else "",
            "situacao": m.situacao,
        }
        for m in (aluno.matriculas or [])
    ]
    responsavel_nome = ""
    for vinculo in responsaveis:
        if vinculo["principal"]:
            responsavel_nome = vinculo["nome"]
            break
    if not responsavel_nome and responsaveis:
        responsavel_nome = responsaveis[0]["nome"]
    turma_nome = ""
    for matricula in matriculas:
        if matricula["situacao"] in ("ativa", "pendente"):
            turma_nome = matricula["turma"]
            break
    if not turma_nome and matriculas:
        turma_nome = matriculas[0]["turma"]
    nascimento_br = _data_br(aluno.data_nascimento)

    return {
        "id": aluno.id,
        "nome_completo": aluno.nome_completo,
        "data_nascimento": aluno.data_nascimento,
        "data_nascimento_br": nascimento_br,
        "nascimento_br": nascimento_br,
        "cpf": aluno.cpf,
        "telefone": aluno.telefone,
        "email": aluno.email,
        "endereco": aluno.endereco,
        "numero": aluno.numero,
        "bairro": aluno.bairro,
        "cidade": aluno.cidade,
        "estado": aluno.estado,
        "cep": aluno.cep,
        "rg": aluno.rg,
        "situacao": aluno.situacao,
        "turma": turma_nome,
        "responsavel": responsavel_nome,
        "responsaveis": responsaveis,
        "matriculas": matriculas,
    }


@router.get("")
def listar_alunos(
    request: Request,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=500),
    q: Optional[str] = Query(None),
    turma_id: Optional[int] = Query(None),
    situacao: Optional[str] = Query(None),
):
    query = db.query(Aluno).options(
        selectinload(Aluno.responsaveis).joinedload(AlunoResponsavel.responsavel),
        selectinload(Aluno.matriculas).joinedload(Matricula.turma),
    )
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Aluno.nome_completo.ilike(like), Aluno.cpf.ilike(like)))
    if turma_id:
        query = query.join(Matricula, Matricula.aluno_id == Aluno.id).filter(
            Matricula.turma_id == turma_id
        )
    if situacao:
        query = query.filter(Aluno.situacao == situacao)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    return {
        "data": {
            "items": [_para_saida(a) for a in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    }


@router.get("/{aluno_id}")
def obter_aluno(aluno_id: int, db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    aluno = (
        db.query(Aluno)
        .options(
            selectinload(Aluno.responsaveis).joinedload(AlunoResponsavel.responsavel),
            selectinload(Aluno.matriculas).joinedload(Matricula.turma),
        )
        .filter(Aluno.id == aluno_id)
        .first()
    )
    if not aluno:
        return JSONResponse(status_code=404, content={"error": {"message": "Aluno não encontrado.", "code": "not_found"}})
    return {"data": _para_saida(aluno)}


@router.post("")
def criar_aluno(
    dados: AlunoCreate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    existente = db.query(Aluno).filter(Aluno.cpf == dados.cpf).first()
    if existente:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Já existe um aluno com este CPF.", "code": "cpf_duplicado", "field": "cpf"}},
        )
    dados_dict = dados.model_dump(exclude_unset=True)
    responsavel_id = dados_dict.pop("responsavel_id", None)
    turma_id = dados_dict.pop("turma_id", None)
    # Converter IDs de string para int
    responsavel_id = int(responsavel_id) if responsavel_id not in (None, "") else None
    turma_id = int(turma_id) if turma_id not in (None, "") else None
    aluno = Aluno(**dados_dict)
    db.add(aluno)
    db.commit()
    db.refresh(aluno)

    # Vincular responsável, se informado
    if responsavel_id:
        resp = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
        if resp:
            db.add(AlunoResponsavel(aluno_id=aluno.id, responsavel_id=responsavel_id, principal=True))

    # Matrícula imediata na turma, se informada
    if turma_id:
        from datetime import date
        turma = db.query(Turma).filter(Turma.id == turma_id).first()
        if turma:
            ocupadas = (
                db.query(func.count(Matricula.id))
                .filter(Matricula.turma_id == turma_id, Matricula.situacao.in_(["ativa", "pendente"]))
                .scalar()
                or 0
            )
            if ocupadas < turma.capacidade_maxima:
                ja_existe = db.query(Matricula).filter(
                    Matricula.aluno_id == aluno.id,
                    Matricula.ano_letivo == turma.ano_letivo,
                    Matricula.situacao.in_(["ativa", "pendente"]),
                ).first()
                if not ja_existe:
                    db.add(Matricula(
                        aluno_id=aluno.id,
                        turma_id=turma_id,
                        data_matricula=date.today(),
                        ano_letivo=turma.ano_letivo,
                        situacao="ativa",
                    ))

    db.commit()
    db.refresh(aluno)
    return {"data": _para_saida(aluno)}


@router.put("/{aluno_id}")
def atualizar_aluno(
    aluno_id: int,
    dados: AlunoUpdate,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return JSONResponse(status_code=404, content={"error": {"message": "Aluno não encontrado.", "code": "not_found"}})
    if dados.cpf and dados.cpf != aluno.cpf:
        existente = db.query(Aluno).filter(Aluno.cpf == dados.cpf).first()
        if existente:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": "CPF já cadastrado para outro aluno.", "code": "cpf_duplicado", "field": "cpf"}},
            )
    dados_dict = dados.model_dump(exclude_unset=True)
    responsavel_id = dados_dict.pop("responsavel_id", None)
    turma_id = dados_dict.pop("turma_id", None)
    responsavel_id = int(responsavel_id) if responsavel_id not in (None, "") else None
    turma_id = int(turma_id) if turma_id not in (None, "") else None
    for campo, valor in dados_dict.items():
        setattr(aluno, campo, valor)

    # Atualizar vínculo responsável principal
    if responsavel_id is not None:
        # remove vínculo principal antigo
        db.query(AlunoResponsavel).filter(
            AlunoResponsavel.aluno_id == aluno.id,
            AlunoResponsavel.principal == True,
        ).delete()
        resp = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
        if resp:
            existente = db.query(AlunoResponsavel).filter(
                AlunoResponsavel.aluno_id == aluno.id,
                AlunoResponsavel.responsavel_id == responsavel_id,
            ).first()
            if not existente:
                db.add(AlunoResponsavel(aluno_id=aluno.id, responsavel_id=responsavel_id, principal=True))

    # Atualizar matrícula na turma
    if turma_id is not None:
        from datetime import date
        turma = db.query(Turma).filter(Turma.id == turma_id).first()
        if turma:
            ocupadas = (
                db.query(func.count(Matricula.id))
                .filter(Matricula.turma_id == turma_id, Matricula.situacao.in_(["ativa", "pendente"]))
                .scalar()
                or 0
            )
            if ocupadas < turma.capacidade_maxima:
                ja_existe = db.query(Matricula).filter(
                    Matricula.aluno_id == aluno.id,
                    Matricula.ano_letivo == turma.ano_letivo,
                    Matricula.situacao.in_(["ativa", "pendente"]),
                ).first()
                if not ja_existe:
                    db.add(Matricula(
                        aluno_id=aluno.id,
                        turma_id=turma_id,
                        data_matricula=date.today(),
                        ano_letivo=turma.ano_letivo,
                        situacao="ativa",
                    ))

    db.commit()
    db.refresh(aluno)
    return {"data": _para_saida(aluno)}


@router.patch("/{aluno_id}/situacao")
def alterar_situacao_aluno(
    aluno_id: int,
    corpo: dict,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return JSONResponse(status_code=404, content={"error": {"message": "Aluno não encontrado.", "code": "not_found"}})
    novo = corpo.get("situacao")
    if novo not in ("ativo", "inativo"):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Situação inválida.", "code": "situacao_invalida"}},
        )
    aluno.situacao = novo
    db.commit()
    return {"data": {"situacao": aluno.situacao}}


@router.delete("/{aluno_id}")
def excluir_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    __: None = Depends(verificar_csrf),
):
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return JSONResponse(status_code=404, content={"error": {"message": "Aluno não encontrado.", "code": "not_found"}})
    db.delete(aluno)
    db.commit()
    return {"data": {"ok": True}}

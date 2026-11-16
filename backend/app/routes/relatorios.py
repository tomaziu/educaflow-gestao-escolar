from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from collections import Counter

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, or_

from app.database import get_db
from app.models.aluno import Aluno
from app.models.responsavel import Responsavel
from app.models.turma import Turma
from app.models.matricula import Matricula
from app.models.aluno_responsavel import AlunoResponsavel
from app.schemas.usuario import UsuarioOut
from app.services.auth import usuario_atual
from app.utils.export import gerar_csv, gerar_pdf, gerar_xlsx

router = APIRouter(prefix="/api", tags=["relatorios"])

MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _mes_anterior(ano: int, mes: int, quantidade: int) -> tuple[int, int]:
    total = (ano * 12 + (mes - 1)) - quantidade
    return total // 12, (total % 12) + 1


def _linha(colunas: list[dict], valores: list) -> dict:
    return {coluna["key"]: valor for coluna, valor in zip(colunas, valores)}


def _data_br(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    return d.strftime("%d/%m/%Y")


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    meses: int = Query(6, ge=1, le=24),
):
    alunos = db.query(Aluno).all()
    responsaveis = db.query(Responsavel).all()
    turmas = db.query(Turma).all()
    matriculas = db.query(Matricula).all()

    alunos_ativos = len([a for a in alunos if a.situacao == "ativo"])
    alunos_inativos = len([a for a in alunos if a.situacao == "inativo"])
    turmas_ativas = len([t for t in turmas if t.situacao == "ativa"])

    capacidade_total = sum(t.capacidade_maxima for t in turmas)
    vagas_disponiveis = 0
    matriculadas = 0
    for t in turmas:
        ocup = len([m for m in matriculas if m.turma_id == t.id and m.situacao in ("ativa", "pendente")])
        matriculadas += ocup
        vagas_disponiveis += max(0, t.capacidade_maxima - ocup)
    ocupacao_percentual = round((matriculadas / capacidade_total * 100) if capacidade_total else 0, 1)

    totais = {
        "alunos": len(alunos),
        "responsaveis": len(responsaveis),
        "turmas": len(turmas),
        "matriculas": len(matriculas),
        "alunos_ativos": alunos_ativos,
        "alunos_inativos": alunos_inativos,
        "vagas_disponiveis": vagas_disponiveis,
        "capacidade_total": capacidade_total,
        "ocupacao_percentual": ocupacao_percentual,
    }

    indicadores = [
        {"chave": "alunos", "rotulo": "Total de alunos", "valor": len(alunos), "nota": str(len(alunos)), "variacao": None},
        {"chave": "responsaveis", "rotulo": "Total de responsáveis", "valor": len(responsaveis), "nota": str(len(responsaveis)), "variacao": None},
        {"chave": "turmas", "rotulo": "Total de turmas", "valor": len(turmas), "nota": str(len(turmas)), "variacao": None},
        {"chave": "matriculas", "rotulo": "Total de matrículas", "valor": len(matriculas), "nota": str(len(matriculas)), "variacao": None},
    ]

    # série de matrículas por mês (últimos N meses)
    hoje = date.today()
    serie = []
    for i in range(meses - 1, -1, -1):
        ano_ref, mes_ref = _mes_anterior(hoje.year, hoje.month, i)
        mes_label = f"{MESES_ABREV[mes_ref - 1]}/{str(ano_ref)[2:]}"
        inicio = date(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            fim = date(ano_ref + 1, 1, 1)
        else:
            fim = date(ano_ref, mes_ref + 1, 1)
        novas = len([m for m in matriculas if m.situacao == "ativa" and inicio <= m.data_matricula < fim])
        rematriculas = len([m for m in matriculas if m.situacao == "pendente" and inicio <= m.data_matricula < fim])
        serie.append({"rotulo": mes_label, "novas": novas, "rematriculas": rematriculas})

    # etapas (situação dos alunos)
    contagem_situacao = Counter(a.situacao for a in alunos)
    total_alunos = len(alunos)
    etapas = []
    labels = {"ativo": "Ativos", "inativo": "Inativos"}
    for sit, qtd in contagem_situacao.items():
        etapas.append({
            "rotulo": labels.get(sit, sit.title()),
            "quantidade": qtd,
            "percentual": round((qtd / total_alunos * 100) if total_alunos else 0, 1),
        })

    # atividades recentes (sintetizadas a partir dos registros)
    atividades = []
    for m in sorted(matriculas, key=lambda x: x.data_matricula, reverse=True)[:8]:
        atividades.append({
            "acao": "criar",
            "descricao": f"Matrícula de {m.aluno.nome_completo if m.aluno else ''} na turma {m.turma.nome if m.turma else ''}",
            "quando": _data_br(m.data_matricula),
            "usuario": "",
        })
    for a in sorted(alunos, key=lambda x: x.data_cadastro, reverse=True)[:4]:
        atividades.append({
            "acao": "criar",
            "descricao": f"Cadastro de aluno {a.nome_completo}",
            "quando": _data_br(a.data_cadastro.date()) if hasattr(a.data_cadastro, "date") else str(a.data_cadastro)[:10],
            "usuario": "",
        })
    atividades = sorted(atividades, key=lambda x: x["quando"] or "", reverse=True)[:8]

    return {
        "data": {
            "totais": totais,
            "indicadores": indicadores,
            "serie_matriculas": serie,
            "etapas": etapas,
            "atividades": atividades,
        }
    }


@router.get("/relatorios/opcoes")
def relatorio_opcoes(db: Session = Depends(get_db), _: UsuarioOut = Depends(usuario_atual)):
    anos = sorted({m.ano_letivo for m in db.query(Matricula).all()}) or [str(date.today().year)]
    anos_int = [int(a) for a in anos]
    turmas = [{"id": t.id, "nome": t.nome} for t in db.query(Turma).all()]
    return {
        "data": {
            "anos": anos_int,
            "turmas": turmas,
            "situacoes": ["ativa", "pendente", "cancelada"],
        }
    }


def _aplicar_filtros(query, modelo, filtros: dict):
    if filtros.get("ano"):
        query = query.filter(modelo.ano_letivo == filtros["ano"])
    if filtros.get("turma_id"):
        query = query.filter(modelo.turma_id == int(filtros["turma_id"]))
    if filtros.get("situacao"):
        query = query.filter(modelo.situacao == filtros["situacao"])
    if filtros.get("nome"):
        like = f"%{filtros['nome']}%"
        query = query.filter(modelo.nome_completo.ilike(like) if hasattr(modelo, "nome_completo") else modelo.nome.ilike(like))
    return query


@router.get("/relatorios/{tipo}")
def relatorio(
    tipo: str,
    db: Session = Depends(get_db),
    _: UsuarioOut = Depends(usuario_atual),
    format: Optional[str] = Query("json"),
    ano: Optional[str] = Query(None),
    turma_id: Optional[str] = Query(None),
    situacao: Optional[str] = Query(None),
    nome: Optional[str] = Query(None),
):
    filtros = {"ano": ano, "turma_id": turma_id, "situacao": situacao, "nome": nome}
    filtros = {k: v for k, v in filtros.items() if v}

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados_filtros = ""
    if filtros:
        partes = []
        if ano: partes.append(f"Ano: {ano}")
        if turma_id: partes.append(f"Turma: {turma_id}")
        if situacao: partes.append(f"Situação: {situacao}")
        if nome: partes.append(f"Nome: {nome}")
        dados_filtros = " | ".join(partes)

    linhas = []
    colunas = []
    titulo = ""
    subtitulo = ""
    total = 0

    if tipo == "alunos":
        query = db.query(Aluno)
        if filtros.get("nome"):
            like = f"%{filtros['nome']}%"
            query = query.filter(Aluno.nome_completo.ilike(like))
        if filtros.get("situacao"):
            query = query.filter(Aluno.situacao == filtros["situacao"])
        if filtros.get("ano") or filtros.get("turma_id"):
            query = query.join(Matricula, Matricula.aluno_id == Aluno.id)
            if filtros.get("ano"):
                query = query.filter(Matricula.ano_letivo == filtros["ano"])
            if filtros.get("turma_id"):
                query = query.filter(Matricula.turma_id == int(filtros["turma_id"]))
        items = query.order_by(Aluno.nome_completo).all()
        colunas = [{"key": "nome_completo", "label": "Nome completo"}, {"key": "nascimento", "label": "Nascimento"},
                   {"key": "cpf", "label": "CPF"}, {"key": "telefone", "label": "Telefone"},
                   {"key": "email", "label": "E-mail"}, {"key": "situacao", "label": "Situação"}]
        for a in items:
            linhas.append(_linha(colunas, [a.nome_completo, _data_br(a.data_nascimento), a.cpf or "—", a.telefone or "—", a.email or "—", a.situacao.title()]))
        titulo = "Relatório de Alunos"
        subtitulo = "Lista completa de estudantes cadastrados"
        total = len(items)

    elif tipo == "alunos-por-turma":
        query = db.query(Turma)
        query = _aplicar_filtros(query, Turma, {k: v for k, v in filtros.items() if k in ("ano", "situacao")})
        items = query.order_by(Turma.nome).all()
        colunas = [{"key": "nome", "label": "Turma"}, {"key": "turno", "label": "Turno"},
                   {"key": "ano_letivo", "label": "Ano"}, {"key": "matriculados", "label": "Alunos"},
                   {"key": "vagas", "label": "Vagas"}]
        from sqlalchemy import func as _func
        for t in items:
            ocup = len([m for m in db.query(Matricula).all() if m.turma_id == t.id and m.situacao in ("ativa", "pendente")])
            linhas.append(_linha(colunas, [t.nome, t.turno, t.ano_letivo, str(ocup), str(max(0, t.capacidade_maxima - ocup))]))
        titulo = "Alunos por Turma"
        subtitulo = "Distribuição de estudantes por turma"
        total = len(items)

    elif tipo == "situacao-matriculas":
        cont = Counter(m.situacao for m in db.query(Matricula).all())
        labels = {"ativa": "Ativa", "pendente": "Pendente", "cancelada": "Cancelada"}
        colunas = [{"key": "situacao", "label": "Situação"}, {"key": "quantidade", "label": "Quantidade"}]
        for sit, qtd in cont.items():
            linhas.append(_linha(colunas, [labels.get(sit, sit.title()), str(qtd)]))
        total = sum(cont.values())
        titulo = "Situação das Matrículas"
        subtitulo = "Matrículas ativas, pendentes e canceladas"

    elif tipo == "responsaveis":
        query = db.query(Responsavel)
        if filtros.get("nome"):
            like = f"%{filtros['nome']}%"
            query = query.filter(Responsavel.nome_completo.ilike(like))
        items = query.order_by(Responsavel.nome_completo).all()
        # alunos vinculados
        vinculos = {}
        for v in db.query(AlunoResponsavel).all():
            vinculos.setdefault(v.responsavel_id, []).append(v.aluno_id)
        alunos_map = {a.id: a.nome_completo for a in db.query(Aluno).all()}
        colunas = [{"key": "nome", "label": "Responsável"}, {"key": "cpf", "label": "CPF"},
                   {"key": "telefone", "label": "Telefone"}, {"key": "email", "label": "E-mail"},
                   {"key": "alunos", "label": "Alunos vinculados"}]
        for r in items:
            nomes = [alunos_map.get(aid, "") for aid in vinculos.get(r.id, [])]
            linhas.append(_linha(colunas, [r.nome_completo, r.cpf, r.telefone or "—", r.email or "—", ", ".join(nomes) or "—"]))
        titulo = "Responsáveis"
        subtitulo = "Relação de responsáveis e alunos vinculados"
        total = len(items)

    elif tipo == "matriculas":
        query = db.query(Matricula).options(selectinload(Matricula.aluno), selectinload(Matricula.turma))
        query = _aplicar_filtros(query, Matricula, {k: v for k, v in filtros.items() if k in ("ano", "turma_id", "situacao")})
        if filtros.get("nome"):
            like = f"%{filtros['nome']}%"
            query = query.join(Aluno, Aluno.id == Matricula.aluno_id).filter(Aluno.nome_completo.ilike(like))
        items = query.order_by(Matricula.data_matricula.desc()).all()
        colunas = [{"key": "aluno", "label": "Aluno"}, {"key": "turma", "label": "Turma"},
                   {"key": "ano_letivo", "label": "Ano"}, {"key": "data", "label": "Data"},
                   {"key": "situacao", "label": "Situação"}]
        for m in items:
            linhas.append(_linha(colunas, [m.aluno.nome_completo if m.aluno else "", m.turma.nome if m.turma else "",
                           m.ano_letivo, _data_br(m.data_matricula), m.situacao.title()]))
        titulo = "Matrículas Realizadas"
        subtitulo = "Histórico de matrículas por ano letivo"
        total = len(items)

    elif tipo == "historico-matriculas":
        items = db.query(Matricula).options(selectinload(Matricula.aluno), selectinload(Matricula.turma)).order_by(Matricula.data_matricula.desc()).all()
        colunas = [{"key": "aluno", "label": "Aluno"}, {"key": "turma", "label": "Turma"},
                   {"key": "ano_letivo", "label": "Ano"}, {"key": "data", "label": "Data"},
                   {"key": "evento", "label": "Evento"}]
        for m in items:
            evento = {"ativa": "Matrícula criada", "pendente": "Matrícula pendente", "cancelada": "Matrícula cancelada"}.get(m.situacao, m.situacao)
            linhas.append(_linha(colunas, [m.aluno.nome_completo if m.aluno else "", m.turma.nome if m.turma else "",
                           m.ano_letivo, _data_br(m.data_matricula), evento]))
        total = len(items)
        titulo = "Histórico de Matrículas"
        subtitulo = "Eventos de criação, transferência e cancelamento"

    else:
        return JSONResponse(status_code=404, content={"error": {"message": "Tipo de relatório inválido.", "code": "not_found"}})

    payload = {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "gerado_em": agora,
        "filtros_aplicados": dados_filtros or None,
        "colunas": colunas,
        "linhas": linhas,
        "total": total,
        "truncado": False,
    }

    if format in ("pdf", "excel", "xlsx", "csv"):
        if format == "pdf":
            conteudo = gerar_pdf(
                titulo,
                subtitulo,
                colunas,
                linhas,
                observacoes=f"Gerado em {agora}" + (f" | {dados_filtros}" if dados_filtros else ""),
            )
            return Response(
                content=conteudo,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="educaflow-{tipo}.pdf"'},
            )
        if format in ("excel", "xlsx"):
            conteudo = gerar_xlsx(titulo, colunas, linhas)
            return Response(
                content=conteudo,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="educaflow-{tipo}.xlsx"'},
            )
        conteudo = gerar_csv(colunas, linhas)
        return Response(
            content=conteudo,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="educaflow-{tipo}.csv"'},
        )

    return {"data": payload}

"""Script para popular o banco de dados com dados de exemplo."""

import sys
from datetime import date, datetime
from pathlib import Path

# Adiciona o diretório backend ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.aluno import Aluno
from app.models.responsavel import Responsavel
from app.models.turma import Turma
from app.models.matricula import Matricula
from app.models.aluno_responsavel import AlunoResponsavel


def popular_banco():
    db: Session = SessionLocal()
    try:
        # Verifica se já existem dados suficientes
        turma_count = db.query(Turma).count()
        aluno_count = db.query(Aluno).count()

        if turma_count >= 4 and aluno_count >= 8:
            print("Banco já contém dados suficientes. Pulando popularização.")
            return

        print(f"Banco atual: {turma_count} turmas, {aluno_count} alunos")
        print("Adicionando novos dados...")
        db.commit()

        # --- TURMAS --- (apenas as que não existem)
        turmas_data = [
            {"nome": "1º Ano A", "turno": "Manhã", "ano_letivo": "2026", "capacidade_maxima": 30, "sala": "Sala 101"},
            {"nome": "1º Ano B", "turno": "Tarde", "ano_letivo": "2026", "capacidade_maxima": 30, "sala": "Sala 102"},
            {"nome": "2º Ano A", "turno": "Manhã", "ano_letivo": "2026", "capacidade_maxima": 30, "sala": "Sala 201"},
            {"nome": "3º Ano A", "turno": "Noite", "ano_letivo": "2026", "capacidade_maxima": 35, "sala": "Sala 301"},
        ]
        turmas = []
        for t in turmas_data:
            turma_existente = db.query(Turma).filter_by(nome=t["nome"], ano_letivo=t["ano_letivo"]).first()
            if not turma_existente:
                turma = Turma(**t)
                db.add(turma)
                turmas.append(turma)
        db.flush()
        print(f"✓ {len(turmas)} novas turmas criadas")

        # --- RESPONSÁVEIS ---
        responsaveis_data = [
            {"nome_completo": "Maria Silva Santos", "cpf": "123.456.789-00", "telefone": "(11) 99999-1111", "email": "maria.santos@email.com", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "José Carlos Oliveira", "cpf": "234.567.890-11", "telefone": "(11) 98888-2222", "email": "jose.oliveira@email.com", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Ana Paula Ferreira", "cpf": "345.678.901-22", "telefone": "(11) 97777-3333", "email": "ana.ferreira@email.com", "cidade": "Guarulhos", "estado": "SP"},
            {"nome_completo": "Roberto Almeida Costa", "cpf": "456.789.012-33", "telefone": "(11) 96666-4444", "email": "roberto.costa@email.com", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Lucia Mendes Souza", "cpf": "567.890.123-44", "telefone": "(11) 95555-5555", "email": "lucia.souza@email.com", "cidade": "Osasco", "estado": "SP"},
        ]
        responsaveis = []
        for r in responsaveis_data:
            # Verifica se o responsável já existe pelo CPF
            resp_existente = db.query(Responsavel).filter_by(cpf=r["cpf"]).first()
            if not resp_existente:
                responsavel = Responsavel(**r)
                db.add(responsavel)
                responsaveis.append(responsavel)
            else:
                responsaveis.append(resp_existente)
        db.flush()
        print(f"✓ {len(responsaveis)} responsáveis (apenas novos criados)")

        # --- ALUNOS ---
        alunos_data = [
            {"nome_completo": "Pedro Henrique Silva", "data_nascimento": date(2015, 3, 15), "cpf": "111.222.333-44", "telefone": "(11) 91111-1111", "situacao": "ativo", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Ana Clara Oliveira", "data_nascimento": date(2014, 7, 22), "cpf": "222.333.444-55", "telefone": "(11) 92222-2222", "situacao": "ativo", "bairro": "Jardim Europa", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Lucas Miguel Ferreira", "data_nascimento": date(2015, 1, 10), "cpf": "333.444.555-66", "telefone": "(11) 93333-3333", "situacao": "ativo", "bairro": "Vila Mariana", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Maria Eduarda Santos", "data_nascimento": date(2014, 11, 5), "cpf": "444.555.666-77", "telefone": "(11) 94444-4444", "situacao": "ativo", "bairro": "Pinheiros", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "João Pedro Almeida", "data_nascimento": date(2013, 9, 18), "cpf": "555.666.777-88", "telefone": "(11) 95555-5555", "situacao": "ativo", "bairro": "Itaim Bibi", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Sofia Beatriz Costa", "data_nascimento": date(2015, 6, 30), "cpf": "666.777.888-99", "telefone": "(11) 96666-6666", "situacao": "ativo", "bairro": "Morumbi", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Gabriel Nunes Souza", "data_nascimento": date(2014, 4, 12), "cpf": "777.888.999-00", "telefone": "(11) 97777-7777", "situacao": "ativo", "bairro": "Liberdade", "cidade": "São Paulo", "estado": "SP"},
            {"nome_completo": "Valentina Ramos Lima", "data_nascimento": date(2013, 12, 25), "cpf": "888.999.000-11", "telefone": "(11) 98888-8888", "situacao": "ativo", "bairro": "Brás", "cidade": "São Paulo", "estado": "SP"},
        ]
        alunos = []
        for a in alunos_data:
            # Verifica se o aluno já existe pelo CPF
            aluno_existente = db.query(Aluno).filter_by(cpf=a["cpf"]).first()
            if not aluno_existente:
                aluno = Aluno(**a)
                db.add(aluno)
                alunos.append(aluno)
            else:
                alunos.append(aluno_existente)
        db.flush()
        print(f"✓ {len(alunos)} alunos processados")

        # --- VÍNCULOS ALUNO x RESPONSÁVEL ---
        # Busca os IDs reais dos alunos já existentes pelo CPF
        aluno_pedro = db.query(Aluno).filter_by(cpf="111.222.333-44").first()
        aluno_ana = db.query(Aluno).filter_by(cpf="222.333.444-55").first()
        aluno_lucas = db.query(Aluno).filter_by(cpf="333.444.555-66").first()
        aluno_maria_edu = db.query(Aluno).filter_by(cpf="444.555.666-77").first()
        aluno_joao = db.query(Aluno).filter_by(cpf="555.666.777-88").first()
        aluno_sofia = db.query(Aluno).filter_by(cpf="666.777.888-99").first()
        aluno_gabriel = db.query(Aluno).filter_by(cpf="777.888.999-00").first()
        aluno_valentina = db.query(Aluno).filter_by(cpf="888.999.000-11").first()

        # Busca os IDs reais dos responsáveis já existentes pelo CPF
        resp_maria = db.query(Responsavel).filter_by(cpf="123.456.789-00").first()
        resp_jose = db.query(Responsavel).filter_by(cpf="234.567.890-11").first()
        resp_ana_paula = db.query(Responsavel).filter_by(cpf="345.678.901-22").first()
        resp_roberto = db.query(Responsavel).filter_by(cpf="456.789.012-33").first()
        resp_lucia = db.query(Responsavel).filter_by(cpf="567.890.123-44").first()

        # Busca os IDs reais das turmas
        turma_1ano_a = db.query(Turma).filter_by(nome="1º Ano A", ano_letivo="2026").first()
        turma_1ano_b = db.query(Turma).filter_by(nome="1º Ano B", ano_letivo="2026").first()
        turma_2ano_a = db.query(Turma).filter_by(nome="2º Ano A", ano_letivo="2026").first()
        turma_3ano_a = db.query(Turma).filter_by(nome="3º Ano A", ano_letivo="2026").first()

        # Vínculos aluno-responsável (apenas se não existirem)
        vinculos = [
            (aluno_pedro.id, resp_maria.id, "Mãe", True),
            (aluno_pedro.id, resp_jose.id, "Pai", False),
            (aluno_ana.id, resp_ana_paula.id, "Mãe", True),
            (aluno_lucas.id, resp_roberto.id, "Pai", True),
            (aluno_maria_edu.id, resp_lucia.id, "Mãe", True),
            (aluno_joao.id, resp_maria.id, "Avó", True),
            (aluno_sofia.id, resp_jose.id, "Mãe", True),
            (aluno_gabriel.id, resp_ana_paula.id, "Pai", True),
            (aluno_valentina.id, resp_roberto.id, "Mãe", True),
        ]
        for aluno_id, resp_id, grau, principal in vinculos:
            if aluno_id and resp_id:
                verificacao = db.query(AlunoResponsavel).filter_by(aluno_id=aluno_id, responsavel_id=resp_id).first()
                if not verificacao:
                    vinculo = AlunoResponsavel(aluno_id=aluno_id, responsavel_id=resp_id, grau_parentesco=grau, principal=principal)
                    db.add(vinculo)
        print(f"✓ Vínculos aluno-responsável criados")

        # --- MATRÍCULAS ---
        matriculas_lista = [
            (aluno_pedro.id, turma_1ano_a.id, date(2026, 2, 1), "2026"),
            (aluno_ana.id, turma_1ano_a.id, date(2026, 2, 1), "2026"),
            (aluno_lucas.id, turma_1ano_b.id, date(2026, 2, 1), "2026"),
            (aluno_maria_edu.id, turma_1ano_b.id, date(2026, 2, 1), "2026"),
            (aluno_joao.id, turma_2ano_a.id, date(2026, 2, 1), "2026"),
            (aluno_sofia.id, turma_2ano_a.id, date(2026, 2, 1), "2026"),
            (aluno_gabriel.id, turma_3ano_a.id, date(2026, 2, 1), "2026"),
            (aluno_valentina.id, turma_3ano_a.id, date(2026, 2, 1), "2026"),
        ]
        for aluno_id, turma_id, data_mat, ano in matriculas_lista:
            if aluno_id and turma_id:
                verificacao = db.query(Matricula).filter_by(aluno_id=aluno_id, turma_id=turma_id, ano_letivo=ano).first()
                if not verificacao:
                    matricula = Matricula(aluno_id=aluno_id, turma_id=turma_id, data_matricula=data_mat, ano_letivo=ano)
                    db.add(matricula)
        print("✓ Matrículas criadas")

        db.commit()

        # Contagem final
        total_turmas = db.query(Turma).count()
        total_alunos = db.query(Aluno).count()
        total_responsaveis = db.query(Responsavel).count()
        total_matriculas = db.query(Matricula).count()
        total_vinculos = db.query(AlunoResponsavel).count()

        print("\n✅ Banco de dados populado com sucesso!")
        print(f"   Turmas: {total_turmas}")
        print(f"   Alunos: {total_alunos}")
        print(f"   Responsáveis: {total_responsaveis}")
        print(f"   Matrículas: {total_matriculas}")
        print(f"   Vínculos aluno-responsável: {total_vinculos}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular banco: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    popular_banco()

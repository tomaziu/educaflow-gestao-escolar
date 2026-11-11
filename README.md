# EducaFlow — Gestão Escolar

Sistema completo de cadastro e gestão escolar (alunos, responsáveis, turmas e matrículas)
com back-end em **Python + FastAPI**, banco de dados **SQLite** e automação de instalação
por scripts **PowerShell** para Windows.

---

## Sumário

1. [Apresentação](#1-apresentação)
2. [Requisitos](#2-requisitos)
3. [Instalação](#3-instalação)
4. [Como iniciar e encerrar](#4-como-iniciar-e-encerrar)
5. [Manual de utilização](#5-manual-de-utilização)
6. [Banco de dados](#6-banco-de-dados)
7. [Backup e restauração](#7-backup-e-restauração)
8. [Solução de problemas](#8-solução-de-problemas)
9. [Manutenção](#9-manutenção)
10. [Tecnologias](#10-tecnologias)

---

## 1. Apresentação

### O que é o EducaFlow
O EducaFlow é uma plataforma de gestão escolar desenvolvida para instituições de ensino
cadastrarem e gerenciarem alunos, responsáveis, turmas e matrículas de forma simples,
rápida e sem necessidade de conhecimentos técnicos.

### Problema que resolve
Escolas e unidades de ensino frequentemente dependem de planilhas ou controles manuais para
gerenciar seus estudantes, o que dificulta a consulta, gera duplicidade de dados e dificulta
a geração de relatórios. O EducaFlow centraliza essas informações em um único sistema local,
com busca, edição, exclusão, relatórios e exportação.

### Principais funcionalidades
- Login e controle de acesso com níveis de perfil (administrador / secretária)
- Dashboard com totais reais (alunos, responsáveis, turmas, matrículas) e gráficos
- Cadastro completo de alunos (nome, nascimento, CPF, telefone, e-mail, endereço, situação)
- Cadastro completo de responsáveis, com vínculo de vários responsáveis por aluno e vice-versa
- Cadastro de turmas (nome, série, turno, ano letivo, capacidade e sala)
- Matrículas de alunos em turmas, com controle de capacidade e prevenção de duplicidade
- Relatórios de alunos, por turma, por situação de matrícula e responsáveis
- Filtros, paginação, busca e impressão dos relatórios
- Exportação de relatórios (CSV/Excel)
- Backup e restauração do banco de dados

### Tecnologias utilizadas
- **Python 3.11+**
- **FastAPI** (API REST)
- **Uvicorn** (servidor)
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (migrações de banco de dados)
- **Pydantic** (validação de dados)
- **passlib / bcrypt** (hash seguro de senhas)
- **python-jose** (suporte a token JWT)
- **SQLite** (banco de dados local, sem servidor externo)
- **HTML5, CSS3 e JavaScript** (front-end existente preservado)

---

## 2. Requisitos

### Sistemas operacionais compatíveis
- Windows 10 64 bits
- Windows 11 64 bits

### Requisitos mínimos do computador
- Processador: 1 GHz ou superior
- Memória RAM: 2 GB (recomendado 4 GB)
- Espaço em disco: cerca de 500 MB (incluindo o Python e as bibliotecas)
- Conexão com a internet apenas para a primeira instalação (download do Python e das bibliotecas, se necessário)

### Dependências instaladas automaticamente
O instalador (`setup.ps1`) baixa e configura sozinho:
- Python (caso não esteja instalado)
- Ambiente virtual (`.venv`)
- Todas as bibliotecas listadas em `requirements.txt` (FastAPI, Uvicorn, SQLAlchemy, Alembic, etc.)

Não é necessário instalar nada manualmente.

---

## 3. Instalação

Siga os passos abaixo. Não é necessário saber programar.

### 1. Baixar o projeto
Baixe a pasta do projeto EducaFlow (por exemplo, como um arquivo ZIP) para o seu computador.

### 2. Extrair a pasta
Extraia o conteúdo do ZIP em uma pasta de sua escolha, por exemplo:
```
C:\EducaFlow
```
Você pode colocar a pasta em qualquer local (Área de Trabalho, Documentos, etc.).

### 3. Abrir a pasta
Abra a pasta extraída no Explorador de Arquivos. Você deverá ver os itens:
- `backend/` (código do servidor)
- `frontend/` (telas do sistema)
- `data/` (banco de dados, criado na instalação)
- `scripts/` (arquivos de instalação e inicialização)
- `setup.ps1`, `start.ps1`, `stop.ps1`
- `requirements.txt`
- `.env.example`
- `README.md`

### 4. Executar o `setup.ps1`
1. Dê um duplo clique no arquivo `setup.ps1` (dentro da pasta `scripts/`).
2. Se o Windows exibir um aviso dizendo que "não é possível executar o script", veja o item
   **"Permitir a execução do script"** abaixo.
3. O instalador irá:
   - Verificar se o Windows é compatível
   - Verificar se o Python está instalado (e instalar automaticamente, se necessário)
   - Criar o ambiente virtual (`.venv`)
   - Instalar todas as dependências
   - Preparar o banco de dados SQLite (`data/educaflow.db`)
   - Criar as tabelas automaticamente
   - Criar o usuário administrador inicial
4. Ao final, será exibida a mensagem **INSTALAÇÃO CONCLUÍDA!** com as credenciais do
   administrador (usuário e senha).

> **Importante:** anote a senha do administrador exibida no terminal. Ela é mostrada apenas
> durante a instalação. Recomendamos alterá-la no primeiro acesso.

### 5. Permitir a execução do script (caso o Windows bloqueie)
Se o Windows impedir a execução do `setup.ps1`, abra o PowerShell como administrador e execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Depois tente executar o `setup.ps1` novamente.

### 6. Confirmar que a instalação terminou
O terminal deve mostrar a mensagem:
```
INSTALAÇÃO CONCLUÍDA!

Execute start.ps1 para iniciar o sistema.
```
E os arquivos `data/educaflow.db` e `.env` devem ter sido criados na raiz do projeto.

### 7. Erros mais comuns na instalação
Veja a seção [8. Solução de problemas](#8-solução-de-problemas).

---

## 4. Como iniciar e encerrar

### Iniciar o sistema
1. Dê um duplo clique em `start.ps1` (dentro da pasta `scripts/`).
2. O servidor será iniciado e o navegador será aberto automaticamente.
3. Acesse o sistema pelo endereço:
   ```
   http://127.0.0.1:8000
   ```
4. Faça login com o usuário e senha do administrador (criados na instalação).

O servidor permanecerá em execução até que você o encerre.

### Se a porta 8000 estiver ocupada
O `start.ps1` detecta isso e tenta usar a porta alternativa **8001**. Nesse caso, acesse:
```
http://127.0.0.1:8001
```

### Encerrar o servidor
1. Execute `stop.ps1` (dentro da pasta `scripts/`), ou
2. Pressione `Ctrl+C` na janela do terminal onde o servidor está rodando.

O banco de dados **não é apagado nem corrompido** ao encerrar. Todos os dados são preservados.

### Iniciar novamente em outro dia
Basta executar `start.ps1` novamente. O banco de dados e todos os registros continuam intactos.

---

## 5. Manual de utilização

### Login
- Acesse `http://127.0.0.1:8000` (ou a porta indicada pelo `start.ps1`).
- Informe o usuário e a senha do administrador.
- Clique em **Entrar no sistema**.
- Caso esqueça a senha, solicite ao administrador da unidade.

### Dashboard
Após o login, você verá o painel principal com:
- Total de alunos cadastrados
- Total de responsáveis
- Total de turmas
- Total de matrículas
- Alunos ativos e inativos
- Gráfico de matrículas ao longo dos meses
- Distribuição de alunos por situação
- Atividades recentes
- Acessos rápidos (cadastrar aluno, responsável e turma)

Todos os números vêm do banco de dados real (não são fictícios).

### Cadastro de alunos
1. No menu lateral, clique em **Alunos**.
2. Clique em **+ Novo aluno**.
3. Preencha os campos obrigatórios (nome completo, nascimento, CPF, etc.).
4. No campo **Data de nascimento**, clique no botão do calendário (▦) e escolha a data
   no painel de meses/dias. Também é possível digitar a data no formato `dd/mm/aaaa`.
5. Você pode vincular um responsável e fazer a matrícula imediata em uma turma.
6. Clique em **Salvar**.
- O CPF é validado para não ser duplicado.
- Use a busca para encontrar alunos por nome ou CPF.
- Clique nos ícones de cada linha para visualizar, editar, ativar/desativar ou excluir.

### Cadastro de responsáveis
1. No menu, clique em **Responsáveis**.
2. Clique em **+ Novo responsável**.
3. Preencha os dados e, opcionalmente, vincule a um aluno.
4. Um responsável pode estar associado a vários alunos, e um aluno pode ter vários responsáveis.

### Cadastro de turmas
1. No menu, clique em **Turmas**.
2. Clique em **+ Nova turma**.
3. Informe nome, turno, ano letivo, capacidade máxima, sala e descrição.
4. O sistema controla a quantidade de vagas disponíveis com base nas matrículas.

### Matrículas
1. No menu, clique em **Matrículas**.
2. Clique em **+ Nova matrícula**.
3. Selecione o aluno, a turma, o ano letivo, a data (pelo calendário ou digitando `dd/mm/aaaa`) e a situação.
4. O sistema impede:
   - Matrícula duplicada do mesmo aluno no mesmo ano letivo
   - Ultrapassar a capacidade máxima da turma
5. Você pode consultar, editar ou cancelar matrículas.

### Relatórios
1. No menu, clique em **Relatórios**.
2. Escolha o tipo de relatório (alunos, alunos por turma, situação das matrículas, responsáveis, matrículas, histórico).
3. Aplique filtros (ano letivo, turma, situação, nome) se desejar.
4. Use os botões para:
   - **Exportar PDF** (arquivo `.pdf` pronto para impressão)
   - **Exportar Excel** (arquivo `.xlsx` que abre no Excel)
   - **Imprimir** (usa a impressão do navegador)
Todos os relatórios utilizam dados reais do banco de dados.

### Backup e restauração
O sistema permite criar backups manuais do banco de dados (`data/educaflow.db`) e restaurá-los
quando necessário. Veja a seção [7. Backup e restauração](#7-backup-e-restauração).

---

## 6. Banco de dados

### Onde fica armazenado
O banco de dados é um arquivo SQLite localizado em:
```
data/educaflow.db
```
dentro da pasta do projeto.

### Como é criado automaticamente
Na primeira execução do `setup.ps1`, o instalador cria a pasta `data/`, o arquivo do banco,
executa as migrações do Alembic (criando todas as tabelas e relacionamentos) e cria o
usuário administrador inicial. Não é necessário executar nenhum comando SQL manualmente.

### Tabelas e relacionamentos
- **usuários**: administradores e secretárias do sistema
- **alunos**: estudantes cadastrados
- **responsáveis**: pais/responsáveis
- **aluno_responsável**: vínculo muitos-para-muitos entre alunos e responsáveis
- **turmas**: turmas da instituição
- **matrículas**: matrículas de alunos em turmas

### Como as tabelas são gerenciadas
As tabelas são gerenciadas pelo SQLAlchemy (ORM) e pelo Alembic (migrações). Sempre que o
sistema é iniciado, o `start.ps1` aplica as migrações pendentes automaticamente, sem apagar
os dados existentes.

### Como realizar backup
Veja a seção [7. Backup e restauração](#7-backup-e-restauração).

### Como restaurar dados
Veja a seção [7. Backup e restauração](#7-backup-e-restauração).

### Como atualizar a estrutura sem perder registros
Basta executar o `start.ps1` novamente: ele aplica as migrações pendentes e preserva todos
os registros já cadastrados.

---

## 7. Backup e restauração

O EducaFlow armazena tudo em um único arquivo (`data/educaflow.db`), o que torna o backup
simples: basta copiar esse arquivo.

### Backup manual (pelo sistema)
1. Faça login como administrador.
2. No sistema, use a função de backup (disponível na área administrativa) ou copie manualmente
   o arquivo `data/educaflow.db` para uma pasta de backups.
3. Os backups são armazenados na pasta `backups/` dentro do projeto.

### Restaurar um backup
1. Encerre o servidor (`stop.ps1`).
2. Copie o arquivo de backup de volta para `data/educaflow.db` (substituindo o atual).
   É recomendado preservar o banco atual antes (renomeie-o, por exemplo,
   `educaflow.db.antes-da-restauracao`).
3. Inicie o servidor novamente (`start.ps1`).

### Backup automático periódico
O sistema pode ser configurado para fazer backups automáticos em uma pasta específica. Consulte
o administrador do sistema para ativar essa opção.

---

## 8. Solução de problemas

| Problema | Solução |
|----------|---------|
| **Python não encontrado** | O `setup.ps1` tenta instalar o Python automaticamente via `winget`. Se falhar, instale o Python 3.11+ em https://www.python.org e execute o instalador novamente. |
| **Falha ao instalar dependências** | Verifique sua conexão com a internet e execute o `setup.ps1` novamente. |
| **Erro ao iniciar o servidor** | Confirme que a instalação foi concluída (`setup.ps1` executado com sucesso). |
| **Porta 8000 ocupada** | O `start.ps1` avisa e tenta a porta 8001. Acesse `http://127.0.0.1:8001`. |
| **Falha na conexão com o banco** | Verifique se o arquivo `data/educaflow.db` existe e se o `.env` está na raiz do projeto. |
| **Erro ao fazer login** | Use o usuário e senha exibidos durante a instalação. Se esqueceu a senha, solicite ao administrador. |
| **Permissão do PowerShell** | Execute, como administrador: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **O sistema não abre no navegador** | Confirme que o servidor está rodando (janela do terminal aberta) e acesse manualmente o endereço indicado. |

---

## 9. Manutenção

### Atualizar o sistema
1. Baixe a nova versão do projeto.
2. Substitua os arquivos da pasta existente (mantendo a pasta `data/` para preservar seus dados).
3. Execute `start.ps1` novamente para aplicar eventuais migrações.

### Instalar novas dependências
As dependências são gerenciadas pelo `requirements.txt`. Se precisar adicionar uma nova biblioteca,
execute (na pasta do projeto, com o ambiente virtual ativado):
```powershell
.\.venv\Scripts\python.exe -m pip install <nome-da-biblioteca>
```

### Preservar os dados
Nunca apague ou mova a pasta `data/` ou o arquivo `.env` sem fazer backup. Eles contêm
todo o banco de dados e as configurações do sistema.

---

## 10. Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Back-end | Python 3, FastAPI, Uvicorn |
| ORM / Banco | SQLAlchemy 2.0, SQLite |
| Migrações | Alembic |
| Validação | Pydantic |
| Segurança | passlib / bcrypt (senhas em hash), python-jose |
| Front-end | HTML5, CSS3, JavaScript (preservado do protótipo) |
| Instalação | PowerShell (`setup.ps1`, `start.ps1`, `stop.ps1`) |

---

## Suporte

Em caso de dúvidas, entre em contato com a coordenação da unidade de ensino ou com o
responsável pela instalação do sistema.

---

*EducaFlow — Gestão escolar simples e eficiente. © 2026*

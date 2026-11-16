@echo off
REM =============================================================================
REM EducaFlow - Instalador (setup.bat)
REM Executa este script para preparar o sistema automaticamente no Windows.
REM =============================================================================

title EducaFlow - Instalador

REM Obter diretorio do script
set "SCRIPT_DIR=%~dp0"
set "PROJ_DIR=%SCRIPT_DIR%.."

set "BACKEND=%PROJ_DIR%\backend"
set "VENV=%PROJ_DIR%\.venv"
set "VENV_PYTHON=%VENV%\Scripts\python.exe"
set "ENV_FILE=%PROJ_DIR%\.env"
set "REQ_BACKEND=%BACKEND%\requirements.txt"
set "DATA_DIR=%PROJ_DIR%\data"
set "BACKUP_DIR=%PROJ_DIR%\backups"

set ETAPA=0
set TOTAL_ETAPAS=10

echo.
echo ========================================
echo      EDUCAFLOW - INSTALADOR            
echo ========================================
echo.

REM Verificar Windows
call :escrever_etapa "Verificando ambiente (SO Windows)"

ver | findstr /i "Windows" >nul
if errorlevel 1 (
    echo ERRO: Este instalador suporta apenas Windows 10/11 64 bits.
    exit /b 1
)

REM Verificar Python
call :escrever_etapa "Verificando Python"

where python >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado. Tentando instalar automaticamente via winget...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo ERRO: winget nao esta disponivel para instalacao automatica.
        echo Instale o Python 3.11+ em https://www.python.org
        exit /b 1
    )
    winget install --id Python.Python.3.14 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
)

echo Python encontrado.
echo.

REM Verificar pip
call :escrever_etapa "Verificando pip"
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip nao encontrado. Tentando garantir o pip...
    python -m ensurepip --upgrade >nul 2>&1
)
echo pip disponivel.
echo.

REM Criar ambiente virtual
call :escrever_etapa "Criando ambiente virtual"
if exist "%VENV_PYTHON%" (
    echo Ambiente virtual .venv ja existe.
) else (
    python -m venv "%VENV%"
    if not exist "%VENV_PYTHON%" (
        echo ERRO: Falha ao criar o ambiente virtual.
        exit /b 1
    )
    echo Ambiente virtual criado com sucesso.
)
echo.

REM Instalar dependencias
call :escrever_etapa "Instalando dependencias"
echo Atualizando pip...
"%VENV_PYTHON%" -m pip install --upgrade pip >nul 2>&1
echo Instalando dependencias...
"%VENV_PYTHON%" -m pip install -r "%REQ_BACKEND%"
if errorlevel 1 (
    echo ERRO: Falha ao instalar as dependencias.
    exit /b 1
)
echo Dependencias instaladas com sucesso.
echo.

REM Verificar bibliotecas
call :escrever_etapa "Verificando bibliotecas"
"%VENV_PYTHON%" -c "import fastapi, sqlalchemy, alembic, jose, passlib, dotenv; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo ERRO: Verificacao de bibliotecas falhou.
    exit /b 1
)
echo Bibliotecas verificadas com sucesso.
echo.

REM Preparar diretorios
call :escrever_etapa "Preparando configuracoes"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
echo Diretorios de dados preparados.
echo.

REM Criar .env
if exist "%ENV_FILE%" (
    echo Arquivo .env ja existe. Mantendo configuracoes atuais.
    echo.
    goto :preparar_banco
)

call :escrever_etapa "Configurando banco de dados"
echo Criando arquivo .env...

REM Gerar chave secreta e senha aleatorias (usar PowerShell para gerar)
for /f "delims=" %%a in ('powershell -NoProfile -Command "Add-Type -AssemblyName System.Web; ([System.Web.Security.Membership]::GenerateUniqueKey(48))" 2^>nul') do set SECRET_KEY=%%a
for /f "delims=" %%a in ('powershell -NoProfile -Command "([char[]](33..126) | Get-Random -Count 16) -join ''" 2^>nul') do set ADMIN_PASS=%%a

(
    echo # EducaFlow - Variaveis de ambiente geradas pelo instalador
    echo DATABASE_URL=sqlite:///%DATA_DIR%/educaflow.db
    echo SECRET_KEY=%SECRET_KEY%
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=10080
    echo.
    echo ADMIN_USERNAME=admin
    echo ADMIN_PASSWORD=%ADMIN_PASS%
) > "%ENV_FILE%"

echo ========================================
echo  CREDENCIAIS DO ADMINISTRADOR INICIAL  
echo ========================================
echo  Usuario : admin
echo  Senha   : %ADMIN_PASS%
echo ========================================
echo  Anote a senha. Ela so eh exibida agora.
echo  Alteracao no primeiro acesso e recomendada.
echo.

goto :preparar_banco

REM Preparar banco
:preparar_banco
call :escrever_etapa "Configurando banco de dados"
echo Preparando banco de dados SQLite...
"%VENV_PYTHON%" "%BACKEND%\seed.py"
if errorlevel 1 (
    echo ERRO: Falha ao preparar o banco de dados.
    exit /b 1
)

echo Sincronizando migracoes (Alembic)...
"%VENV%\Scripts\alembic.exe" stamp head >nul 2>&1
if errorlevel 1 (
    echo ERRO: Falha ao sincronizar migracoes.
    exit /b 1
)

echo Banco de dados e migracoes prontos.
echo.

REM Verificar instalacao final
call :escrever_etapa "Finalizando instalacao"

set FALHOU=0
if exist "%VENV_PYTHON%" (
    echo   [OK] Ambiente virtual
) else (
    echo   [FALHOU] Ambiente virtual
    set FALHOU=1
)
if exist "%REQ_BACKEND%" (
    echo   [OK] Dependencias
) else (
    echo   [FALHOU] Dependencias
    set FALHOU=1
)
if exist "%ENV_FILE%" (
    echo   [OK] Configuracao (.env)
) else (
    echo   [FALHOU] Configuracao (.env)
    set FALHOU=1
)
if exist "%DATA_DIR%\educaflow.db" (
    echo   [OK] Banco de dados
) else (
    echo   [FALHOU] Banco de dados
    set FALHOU=1
)

if "%FALHOU%"=="1" (
    echo.
    echo ERRO: A instalacao nao foi concluida corretamente.
    exit /b 1
)

echo Todas as verificacoes passaram.
echo.

echo ========================================
echo  INSTALACAO CONCLUIDA COM SUCESSO!    
echo ========================================
echo.
echo Execute start.bat para iniciar o sistema.
echo Sistema disponivel em: http://127.0.0.1:8000
echo.

exit /b 0

REM Funcao para escrever etapa
:escrever_etapa
set /a ETAPA+=1
echo.
echo [%ETAPA%/%TOTAL_ETAPAS%] %~1
echo.
exit /b 0
@echo off
setlocal enabledelayedexpansion
REM =============================================================================
REM EducaFlow - Inicializador (start.bat)
REM Inicia o servidor FastAPI (Uvicorn) e abre o navegador.
REM =============================================================================

title EducaFlow - Servidor

REM Obter diretorio do script
set "SCRIPT_DIR=%~dp0"
for %%A in ("%SCRIPT_DIR%..\") do set "PROJ_DIR=%%~fA"

set "BACKEND=%PROJ_DIR%\backend"
set "VENV_PYTHON=%PROJ_DIR%\.venv\Scripts\python.exe"
set "ENV_FILE=%PROJ_DIR%\.env"
set "PID_FILE=%PROJ_DIR%\data\server.pid"
set "LOG_FILE=%PROJ_DIR%\data\server.log"
set "ERR_LOG_FILE=%PROJ_DIR%\data\server.error.log"
set "PORT=8000"
set "URL=http://127.0.0.1:!PORT!"

echo.
echo ========================================
echo        EDUCAFLOW - INICIADOR
echo ========================================
echo.

REM Verificar instalacao
if not exist "%VENV_PYTHON%" (
    echo ERRO: Ambiente virtual nao encontrado em "%VENV_PYTHON%".
    echo Execute setup.bat primeiro.
    exit /b 1
)
if not exist "%PROJ_DIR%\.env" (
    echo ERRO: Arquivo .env nao encontrado em "%PROJ_DIR%\.env".
    echo Execute setup.bat primeiro.
    exit /b 1
)
echo Instalacao confirmada.

REM Verificar se porta esta ocupida (usa netstat)
:CHECK_PORT
netstat -ano 2>nul | findstr /r ":!PORT![^0-9]" >nul
if errorlevel 1 goto PORT_FREE

echo ATENCAO: a porta !PORT! esta ocupada.
if !PORT!==8000 (
    set "PORT=8001"
    set "URL=http://127.0.0.1:!PORT!"
    echo Usando porta alternativa: !PORT!
    goto CHECK_PORT
)
echo ERRO: As portas 8000 e 8001 estao ocupadas. Libere uma delas e execute novamente.
exit /b 1

:PORT_FREE

REM Matar processo antigo se PID file existir
if exist "%PID_FILE%" (
    set /p OLD_PID=<%PID_FILE%
    if defined OLD_PID taskkill /F /PID %OLD_PID% >nul 2>&1
    del "%PID_FILE%" 2>nul
)

REM Aplicar migracoes (Alembic)
echo Aplicando migracoes pendentes - Alembic
pushd "%BACKEND%"
"%PROJ_DIR%\.venv\Scripts\alembic.exe" stamp head >nul 2>&1
if errorlevel 1 (
    echo ERRO: Falha ao aplicar as migracoes - Alembic
    popd
    exit /b 1
)
popd
echo Estrutura do banco verificada.

REM Garantir usuario administrador
echo Garantindo usuario administrador...
"%VENV_PYTHON%" "%BACKEND%\seed.py" >nul 2>&1
if errorlevel 1 (
    echo ERRO: Falha ao garantir o usuario administrador
    exit /b 1
)
echo Administrador verificado.

REM Iniciar servidor
echo Iniciando o servidor FastAPI - Uvicorn
if not exist "%PROJ_DIR%\data" mkdir "%PROJ_DIR%\data" >nul 2>&1
del "%LOG_FILE%" "%ERR_LOG_FILE%" 2>nul

REM Iniciar o servidor uvicorn em background
pushd "%BACKEND%"
start "EducaFlow-Uvicorn" /B "%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port !PORT! >"%LOG_FILE%" 2>"%ERR_LOG_FILE%"
popd

REM Aguardar um momento para o processo iniciar
ping -n 4 127.0.0.1 >nul

REM ------------------------------------------------------------
REM Aguardar servidor ficar online
REM ------------------------------------------------------------
echo Aguardando o servidor ficar disponivel em !URL! ...
set "ONLINE=0"
set "TRY=0"

:WAIT_LOOP
set /a TRY+=1
if %TRY% gtr 30 goto WAIT_END

REM Tentar acessar /status via curl ou powershell
curl -s -m 2 "!URL!/status" >nul 2>&1
if not errorlevel 1 (
    set "ONLINE=1"
    goto SERVER_ONLINE
)

ping -n 2 127.0.0.1 >nul
goto WAIT_LOOP

:WAIT_END
echo FALHA AO INICIAR O SERVIDOR (timeout apos 30s).
type "%LOG_FILE%" 2>nul
type "%ERR_LOG_FILE%" 2>nul
echo Verifique o log em: %LOG_FILE%
exit /b 1

:SERVER_ONLINE
echo Servidor online em !URL!

REM Obter PID do processo via wmic
set "SERVER_PID="
for /f "tokens=2 delims==" %%i in ('wmic process where "Name='python.exe' and CommandLine like '%%uvicorn%%'" get ProcessId /value 2^>nul') do (
    if not defined SERVER_PID set "SERVER_PID=%%i"
)

if defined SERVER_PID (
    echo %SERVER_PID% > "%PID_FILE%"
    echo Servidor iniciado (PID %SERVER_PID%).
) else (
    echo AVISO: Nao foi possivel obter o PID do servidor automaticamente.
)

REM Abrir navegador
start "" "!URL!"
echo Navegador aberto em !URL!

echo.
echo ========================================
echo   EDUCAFLOW ONLINE
echo ========================================
echo   Acesse o sistema em: !URL!
echo   Tela de login:       !URL!
echo   Documentacao API:    !URL!/docs
echo ========================================
echo.

echo O servidor esta rodando. Pressione Ctrl+C ou execute stop.bat para encerrar.
echo.

REM Manter o script ativo enquanto o servidor esta online
:WAIT_SERVER
ping -n 3 127.0.0.1 >nul
curl -s -m 1 "!URL!/status" >nul 2>&1
if errorlevel 1 (
    echo Servidor encerrado ou nao disponivel.
    exit /b 0
)
goto WAIT_SERVER
@echo off
setlocal enabledelayedexpansion
REM =============================================================================
REM EducaFlow - Encerrador (stop.bat)
REM Encerra o servidor Uvicorn de forma segura, sem apagar o banco de dados.
REM =============================================================================

title EducaFlow - Encerrador

REM Obter diretorio do script
set "SCRIPT_DIR=%~dp0"
for %%A in ("%SCRIPT_DIR%..\") do set "PROJ_DIR=%%~fA"

set "PID_FILE=%PROJ_DIR%\data\server.pid"

echo.
echo ========================================
echo      EDUCAFLOW - ENCERRADOR            
echo ========================================
echo.

REM ------------------------------------------------------------
REM Encerrar pelo PID file (preferencial)
REM ------------------------------------------------------------
if exist "%PID_FILE%" (
    REM Ler PID do arquivo
    set "OLD_PID="
    for /f "tokens=1" %%l in (%PID_FILE%) do if not "%%l"=="" set "OLD_PID=%%l"
    
    if defined OLD_PID (
        taskkill /F /PID %OLD_PID% >nul 2>&1
        echo Servidor (PID %OLD_PID%) encerrado com sucesso.
        del "%PID_FILE%" 2>nul
    ) else (
        del "%PID_FILE%" 2>nul
    )
) else (
    echo Nenhum arquivo de PID encontrado.
)

REM ------------------------------------------------------------
REM Fallback: encerrar processos python com uvicorn
REM ------------------------------------------------------------
echo Verificando processos...

powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*' } | Select-Object -ExpandProperty Id | ForEach-Object { taskkill /F /PID $_ >nul 2>&1; Write-Host 'Processo encerrado (PID' $_ ')' }"

echo.
echo O banco de dados (data\educaflow.db) nao foi modificado e seus dados estao preservados.
echo Execute start.bat para iniciar o sistema novamente.
echo.

exit /b 0
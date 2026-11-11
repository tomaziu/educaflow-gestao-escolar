# =============================================================================
# EducaFlow - Encerrador (stop.ps1)
# Encerra o servidor Uvicorn de forma segura, sem apagar o banco de dados.
# =============================================================================

$ErrorActionPreference = "Continue"
$host.UI.RawUI.WindowTitle = "EducaFlow - Encerrador"

$raiz = Split-Path -Parent $MyInvocation.MyCommand.Definition   # pasta scripts/
$projetoDir = Split-Path -Parent $raiz                          # raiz do projeto
$pidFile = Join-Path $projetoDir "data\server.pid"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       EDUCAFLOW - ENCERRADOR           " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function EncerrarPid() {
    if (-not (Test-Path $pidFile)) {
        Write-Host "Nenhum arquivo de PID do servidor encontrado." -ForegroundColor Yellow
        return $false
    }
    $pidServidor = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $pidServidor) {
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        Write-Host "PID invalido. Arquivo removido." -ForegroundColor Yellow
        return $false
    }
    try {
        Stop-Process -Id $pidServidor -Force -ErrorAction Stop
        Write-Host "Servidor (PID $pidServidor) encerrado com sucesso." -ForegroundColor Green
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return $true
    } catch {
        Write-Host "Nao foi possivel encerrar o PID $pidServidor (processo pode ja estar encerrado)." -ForegroundColor Yellow
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return $false
    }
}

function EncerrarPorNome() {
    # Fallback: encerra processos python que estejam rodando o uvicorn da app
    $processos = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*app.main:app*"
    }
    $encerrados = 0
    foreach ($p in $processos) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Host "Processo uvicorn encerrado (PID $($p.ProcessId))." -ForegroundColor Green
            $encerrados++
        } catch {
            # ignora
        }
    }
    return $encerrados
}

$encerrado = EncerrarPid
if (-not $encerrado) {
    $n = EncerrarPorNome
    if ($n -gt 0) {
        $encerrado = $true
    } else {
        Write-Host "Nenhum servidor do EducaFlow em execucao foi encontrado." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "O banco de dados (data/educaflow.db) nao foi modificado e seus dados estao preservados."
Write-Host "Execute start.ps1 para iniciar o sistema novamente."
Write-Host ""

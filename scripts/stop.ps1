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
    $pid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if (-not $pid) {
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        Write-Host "PID invalido. Arquivo removido." -ForegroundColor Yellow
        return $false
    }
    try {
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Write-Host "Servidor (PID $pid) encerrado com sucesso." -ForegroundColor Green
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return $true
    } catch {
        Write-Host "Nao foi possivel encerrar o PID $pid (processo pode ja estar encerrado)." -ForegroundColor Yellow
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return $false
    }
}

function EncerrarPorNome() {
    # Fallback: tenta encerrar processos python que estejam rodando o uvicorn da app
    $processos = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -and $_.Path -like "*python*"
    }
    $encerrados = 0
    foreach ($p in $processos) {
        try {
            $cmdline = (Get-Process -Id $p.Id).CommandLine 2>$null
            if ($cmdline -like "*uvicorn*app.main:app*") {
                Stop-Process -Id $p.Id -Force -ErrorAction Stop
                Write-Host "Processo uvicorn encerrado (PID $($p.Id))." -ForegroundColor Green
                $encerrados++
            }
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

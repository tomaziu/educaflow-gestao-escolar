# =============================================================================
# EducaFlow - Inicializador (start.ps1)
# Inicia o servidor FastAPI (Uvicorn) e abre o navegador.
# =============================================================================

$ErrorActionPreference = "Stop"
$host.UI.RawUI.WindowTitle = "EducaFlow - Servidor"

$raiz = Split-Path -Parent $MyInvocation.MyCommand.Definition   # pasta scripts/
$projetoDir = Split-Path -Parent $raiz                          # raiz do projeto
$backend = Join-Path $projetoDir "backend"
$venvPython = Join-Path $projetoDir ".venv\Scripts\python.exe"
$envFile = Join-Path $projetoDir ".env"
$pidFile = Join-Path $projetoDir "data\server.pid"
$porta = 8000
$url = "http://127.0.0.1:$porta"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       EDUCAFLOW - INICIADOR            " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function VerificarInstalacao() {
    if (-not (Test-Path $venvPython)) {
        Write-Error "Ambiente virtual nao encontrado. Execute setup.ps1 primeiro." -CategoryOperationStopped
    }
    if (-not (Test-Path $envFile)) {
        Write-Error "Arquivo .env nao encontrado. Execute setup.ps1 primeiro." -CategoryOperationStopped
    }
    Write-Host "Instalacao confirmada." -ForegroundColor Green
}

function PortaOcupada([int]$p) {
    try {
        $con = Test-NetConnection -ComputerName 127.0.0.1 -Port $p -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return [bool]$con
    } catch {
        return $false
    }
}

function AplicarMigrações() {
    Write-Host "Aplicando migracoes pendentes (Alembic)..." -ForegroundColor Yellow
    $alembicExe = Join-Path $projetoDir ".venv\Scripts\alembic.exe"
    Push-Location $backend
    $ep = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $alembicExe upgrade head > $null 2>&1
    $ErrorActionPreference = $ep
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao aplicar as migracoes (Alembic)." -Category OperationStopped
    }
    Write-Host "Estrutura do banco verificada." -ForegroundColor Green
}

function GarantirAdministrador() {
    Write-Host "Garantindo usuario administrador..." -ForegroundColor Yellow
    & $venvPython "$backend\seed.py" 2>&1 | Out-Null
    Write-Host "Administrador verificado." -ForegroundColor Green
}

function IniciarServidor() {
    Write-Host "Iniciando o servidor FastAPI (Uvicorn)..." -ForegroundColor Yellow
    Push-Location $backend
    $processo = Start-Process $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $porta -PassThru -WindowStyle Hidden
    Pop-Location

    # Salva o PID para o stop.ps1
    $processo.Id | Out-File -FilePath $pidFile -Encoding UTF8

    Write-Host "Servidor iniciado (PID $($processo.Id))." -ForegroundColor Green
    return $processo
}

function AguardarServidor([int]$segundos = 30) {
    Write-Host "Aguardando o servidor ficar disponível em $url ..." -ForegroundColor Yellow
    $inicio = Get-Date
    while ((Get-Date) - $inicio -lt (New-TimeSpan -Seconds $segundos)) {
        try {
            $resposta = Invoke-RestMethod -Uri "$url/" -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($resposta) {
                Write-Host "Servidor online em $url" -ForegroundColor Green
                return $true
            }
        } catch {
            # ainda nao esta pronto
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

function AbrirNavegador() {
    try {
        Start-Process $url
        Write-Host "Navegador aberto em $url" -ForegroundColor Green
    } catch {
        Write-Host "Nao foi possivel abrir o navegador automaticamente. Acesse manualmente: $url" -ForegroundColor Yellow
    }
}

try {
    VerificarInstalacao

    if (Test-Path $pidFile) {
        $pidAntigo = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($pidAntigo) {
            try { Stop-Process -Id $pidAntigo -Force -ErrorAction Stop } catch { }
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    }

    if (PortaOcupada $porta) {
        Write-Host "ATENCAO: a porta $porta esta ocupada." -ForegroundColor Yellow
        $portaAlt = 8001
        if (PortaOcupada $portaAlt) {
            Write-Error "As portas 8000 e 8001 estao ocupadas. Libere uma delas e execute novamente." -CategoryOperationStopped
        }
        Write-Host "Usando porta alternativa: $portaAlt" -ForegroundColor Yellow
        $porta = $portaAlt
        $url = "http://127.0.0.1:$porta"
    }

    AplicarMigrações
    GarantirAdministrador
    $proc = IniciarServidor
    $online = AguardarServidor
    if ($online) {
        AbrirNavegador
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  EDUCAFLOW ONLINE                     " -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  Acesse o sistema em: $url" -ForegroundColor Green
        Write-Host "  Tela de login:       $url" -ForegroundColor Green
        Write-Host "  Documentacao API:    $url/docs" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "O servidor pode estar demorando para iniciar. Acesse manualmente: $url" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "O servidor esta rodando. Pressione Ctrl+C ou execute stop.ps1 para encerrar."
    Write-Host "Para encerrar pressionando Ctrl+C neste terminal, o processo sera interrompido."
    Write-Host ""

    # Mantem o script vinculado ao processo do servidor para nao sair imediatamente
    try {
        Wait-Process -Id $proc.Id
    } catch {
        # processo finalizado
    }
} catch {
    Write-Host ""
    Write-Host "ERRO AO INICIAR O SERVIDOR: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}

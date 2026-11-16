# =============================================================================
# EducaFlow - Instalador (setup.ps1)
# Executa este script para preparar o sistema automaticamente no Windows.
# =============================================================================

$ErrorActionPreference = "Stop"
$host.UI.RawUI.WindowTitle = "EducaFlow - Instalador"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       EDUCAFLOW - INSTALADOR           " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$raiz = Split-Path -Parent $MyInvocation.MyCommand.Definition   # pasta scripts/
$projetoDir = Split-Path -Parent $raiz                          # raiz do projeto
$backend = Join-Path $projetoDir "backend"
$venv = Join-Path $projetoDir ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
$envFile = Join-Path $projetoDir ".env"
$reqBackend = Join-Path $backend "requirements.txt"

function EscreverEtapa([int]$atual, [int]$total, [string]$texto) {
    $pct = [math]::Round(($atual / $total) * 100)
    Write-Host ""
    Write-Host "[$atual/$total] $texto" -ForegroundColor Yellow
}

function VerificarWindows() {
    if ([environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        Write-Error "Este instalador suporta apenas Windows (Windows 10/11 64 bits)." -Category OperationStopped
    }
}

function VerificarPython() {
    $script:pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not $script:pythonExe) {
        Write-Host "Python nao encontrado. Tentando instalar automaticamente via winget..." -ForegroundColor Yellow
        winget install --id Python.Python.3.14 --silent --accept-package-agreements --accept-source-agreements 2>$null | Out-Null
        # Atualiza o PATH para enxergar o Python recem-instalado
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $script:pythonExe = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $script:pythonExe) {
        Write-Error "Nao foi possível instalar o Python automaticamente. Instale o Python 3.11+ em https://www.python.org e execute este instalador novamente." -Category OperationStopped
    }
    Write-Host "Python encontrado: $($script:pythonExe.Source)" -ForegroundColor Green
    Write-Host "Versao: $(& $script:pythonExe --version 2>&1)" -ForegroundColor Green
}

function VerificarPip() {
    $pipDisponível = & $script:pythonExe -m pip --version 2>$null
    if (-not $pipDisponível) {
        Write-Host "pip nao encontrado. Tentando garantir o pip..." -ForegroundColor Yellow
        & $script:pythonExe -m ensurepip --upgrade 2>$null | Out-Null
    }
    Write-Host "pip disponível." -ForegroundColor Green
}

function CriarAmbienteVirtual() {
    if (-not (Test-Path $venvPython)) {
        Write-Host "Criando ambiente virtual .venv..." -ForegroundColor Yellow
        & $script:pythonExe -m venv $venv
        if (-not (Test-Path $venvPython)) {
            Write-Error "Falha ao criar o ambiente virtual." -Category OperationStopped
        }
    } else {
        Write-Host "Ambiente virtual .venv ja existe." -ForegroundColor Green
    }
}

function InstalarDependencias() {
    Write-Host "Verificando o pip dentro do ambiente virtual..." -ForegroundColor Yellow
    try {
        & $venvPython -m pip install --upgrade pip 2>$null | Out-Null
    } catch {
        # nao bloqueia a instalacao por causa do pip
    }
    Write-Host "  Pip verificado." -ForegroundColor Green

    Write-Host "Instalando dependencias no ambiente virtual (pode demorar alguns minutos)..." -ForegroundColor Yellow
    & $venvPython -m pip install --only-binary :all: -r $reqBackend
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao instalar as dependencias. Verifique sua conexao com a internet." -Category OperationStopped
    }
    Write-Host "Dependencias instaladas com sucesso." -ForegroundColor Green
}

function VerificarBibliotecas() {
    $resultado = & $venvPython -c "import fastapi, sqlalchemy, alembic, jose, passlib, dotenv; print('BIBLIOTECAS_OK')" 2>&1
    if ($LASTEXITCODE -ne 0 -or $resultado -notlike "*BIBLIOTECAS_OK*") {
        Write-Error "Verificacao de bibliotecas falhou: $resultado" -Category OperationStopped
    }
    Write-Host "Bibliotecas verificadas com sucesso." -ForegroundColor Green
}

function PrepararDiretorios() {
    $dataDir = Join-Path $projetoDir "data"
    $backupDir = Join-Path $projetoDir "backups"
    if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir -Force | Out-Null }
    if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir -Force | Out-Null }
    Write-Host "Diretórios de dados preparados." -ForegroundColor Green
}

function CriarEnv() {
    if (Test-Path $envFile) {
        Write-Host "Arquivo .env ja existe. Mantendo configuracoes atuais." -ForegroundColor Green
        return
    }

    Write-Host "Criando arquivo de configuracao .env..." -ForegroundColor Yellow
    $chave = -join ((33..126) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $senhaAdmin = -join ((33..126) | Get-Random -Count 16 | ForEach-Object { [char]$_ })
    $caminhoDb = (Join-Path $projetoDir "data\educaflow.db").Replace("\", "/")

    $conteudo = @"
# EducaFlow - Variáveis de ambiente geradas pelo instalador
DATABASE_URL=sqlite:///$caminhoDb
SECRET_KEY=$chave
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

ADMIN_USERNAME=admin
ADMIN_PASSWORD=$senhaAdmin
"@
    # Grava sem BOM UTF-8 para que o pydantic-settings/dotenv leiam as variaveis corretamente
    [System.IO.File]::WriteAllText($envFile, $conteudo, (New-Object System.Text.UTF8Encoding($false)))

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  CREDENCIAIS DO ADMINISTRADOR INICIAL   " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Usuario : admin" -ForegroundColor Cyan
    Write-Host "  Senha   : $senhaAdmin" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Anote a senha acima. Ela so eh exibida agora." -ForegroundColor Yellow
    Write-Host "  Alteracao no primeiro acesso e recomendada." -ForegroundColor Yellow
    Write-Host ""
}

function PrepararBanco() {
    Write-Host "Preparando banco de dados SQLite e tabelas..." -ForegroundColor Yellow
    & $venvPython "$backend\seed.py" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao preparar o banco de dados." -Category OperationStopped
    }

    # Marca o Alembic como aplicado (head) pois as tabelas ja foram criadas pelo seed
    Write-Host "Sincronizando controle de migracoes (Alembic)..." -ForegroundColor Yellow
    $alembic = Join-Path $venv "Scripts\alembic.exe"
    Push-Location $backend
    $ep = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $alembic stamp head > $null 2>&1
    $ErrorActionPreference = $ep
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao sincronizar as migracoes (Alembic)." -Category OperationStopped
    }
    Write-Host "Banco de dados e migracoes prontos." -ForegroundColor Green
}

function VerificarInstalacao() {
    Write-Host "Executando verificacoes finais..." -ForegroundColor Yellow
    $caminhoBanco = Join-Path $projetoDir "data\educaflow.db"
    $todosOk = $true

    function EscreverCheck([string]$nome, [bool]$ok) {
        if ($ok) { $cor = "Green"; $estado = "OK" } else { $cor = "Red"; $estado = "FALHOU" }
        Write-Host "  [$estado] $nome" -ForegroundColor $cor
        if (-not $ok) { $script:verificarFalhou = $true }
    }

    $script:verificarFalhou = $false

    $check1 = Test-Path $script:pythonExe.Source
    EscreverCheck "Python" $check1

    $check2 = Test-Path $venvPython
    EscreverCheck "Ambiente virtual" $check2

    $check3 = Test-Path $reqBackend
    EscreverCheck "Dependencias" $check3

    $check4 = Test-Path $envFile
    EscreverCheck "Configuracao (.env)" $check4

    $check5 = Test-Path $caminhoBanco
    EscreverCheck "Banco de dados" $check5

    if ($script:verificarFalhou) {
        Write-Error "A instalacao nao foi concluída corretamente." -Category OperationStopped
    }
    Write-Host "Todas as verificacoes passaram." -ForegroundColor Green
}

# =============================================================================
# Execucao
# =============================================================================
$totalEtapas = 10

try {
    VerificarWindows
    EscreverEtapa 1 $totalEtapas "Verificando ambiente (SO Windows)"
    EscreverEtapa 2 $totalEtapas "Verificando Python"
    VerificarPython
    EscreverEtapa 3 $totalEtapas "Verificando pip"
    VerificarPip
    EscreverEtapa 4 $totalEtapas "Criando ambiente virtual"
    CriarAmbienteVirtual
    EscreverEtapa 5 $totalEtapas "Instalando dependencias"
    InstalarDependencias
    EscreverEtapa 6 $totalEtapas "Verificando bibliotecas"
    VerificarBibliotecas
    EscreverEtapa 7 $totalEtapas "Preparando configuracoes"
    PrepararDiretorios
    CriarEnv
    EscreverEtapa 8 $totalEtapas "Configurando banco de dados"
    PrepararBanco
    EscreverEtapa 9 $totalEtapas "Criando tabelas"
    Write-Host "  Tabelas criadas automaticamente pelo script de seed." -ForegroundColor Green
    EscreverEtapa 10 $totalEtapas "Finalizando instalacao"
    VerificarInstalacao

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  INSTALACAO CONCLUÍDA COM SUCESSO!     " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Execute start.ps1 para iniciar o sistema."
    Write-Host "O sistema sera disponibilizado em: http://127.0.0.1:8000"
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "ERRO DURANTE A INSTALACAO: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}





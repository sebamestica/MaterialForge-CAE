# =========================================================================
# MATERIALFORGE - STARTUP SCRIPT (Windows PowerShell)
# =========================================================================

$ErrorActionPreference = "Stop"
Clear-Host

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  >>> INICIANDO ENTORNO DE TRABAJO MATERIALFORGE <<<" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Validar entorno virtual de Python
$venvPath = Join-Path (Get-Location) ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[-] ERROR: No se encontro el entorno virtual .venv." -ForegroundColor Red
    Write-Host "    Asegurate de estar en el directorio raiz del proyecto." -ForegroundColor Yellow
    exit 1
}

# 2. Validar dependencias del frontend
$frontendPath = Join-Path (Get-Location) "frontend"
if (-not (Test-Path $frontendPath)) {
    Write-Host "[-] ERROR: No se encontro la carpeta /frontend." -ForegroundColor Red
    exit 1
}

$currentDir = (Get-Location).Path

# 3. Validar y arrancar Ollama Server si no está activo
Write-Host "[+] Verificando Ollama Server..." -ForegroundColor Green
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -ErrorAction SilentlyContinue
} catch {
    $ollamaCheck = $null
}

if ($null -eq $ollamaCheck) {
    Write-Host "[*] Ollama no detectado. Iniciando Ollama..." -ForegroundColor Yellow
    $ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaPath) {
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
    } else {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    }
    # Esperar a que Ollama responda
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 1
        try {
            $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -ErrorAction SilentlyContinue
        } catch {
            $ollamaCheck = $null
        }
        if ($null -ne $ollamaCheck) {
            Write-Host "[OK] ¡Ollama está activo!" -ForegroundColor Green
            break
        }
    }
} else {
    Write-Host "[OK] Ollama ya está activo y en ejecución." -ForegroundColor Green
}

# 4. Validar y construir la base de datos si falta
$dbPath = Join-Path (Get-Location) "data\processed\training_table.parquet"
if (-not (Test-Path $dbPath)) {
    Write-Host "[*] Base de datos no encontrada. Iniciando pipeline de escaneo e ingesta..." -ForegroundColor Yellow
    & '.\.venv\Scripts\python.exe' -m backend.src.data.dataset_scanner
    Write-Host "[OK] Base de datos consolidada exitosamente." -ForegroundColor Green
}

# 5. Lanzar Backend FastAPI en una nueva ventana
Write-Host "[+] Lanzando API del Backend en puerto 8000..." -ForegroundColor Green
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "
    Set-Location '$currentDir';
    Write-Host '========================================================' -ForegroundColor Green;
    Write-Host '   FASTAPI BACKEND - SERVIDOR DE PREDICCION Y CAD       ' -ForegroundColor Green;
    Write-Host '========================================================' -ForegroundColor Green;
    & '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
"

# 6. Lanzar Frontend Next.js en una nueva ventana
Write-Host "[+] Lanzando Servidor de Desarrollo del Frontend en puerto 3000..." -ForegroundColor Green
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "
    Set-Location '$frontendPath';
    Write-Host '========================================================' -ForegroundColor Cyan;
    Write-Host '   NEXT.JS FRONTEND - MATERIALFORGE WORKSPACE           ' -ForegroundColor Cyan;
    Write-Host '========================================================' -ForegroundColor Cyan;
    npm run dev
"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  [OK] ¡Servidores iniciados exitosamente!" -ForegroundColor Green
Write-Host "  -> Backend API: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "  -> Frontend App: http://localhost:3000" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Write-Host "No cierres las ventanas de terminal secundarias que se han abierto." -ForegroundColor Gray

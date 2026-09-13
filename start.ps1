# NeedNow AI - Local Development Startup Script (PowerShell)
# Usage: .\start.ps1

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   🚀 Starting NeedNow AI Development Servers      " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

# 1. Backend Setup
Write-Host "`n[Backend] Setting up FastAPI environment..." -ForegroundColor Yellow

$VenvActivate = $null
if (Test-Path "$BackendDir\venv\Scripts\Activate.ps1") {
    $VenvActivate = "$BackendDir\venv\Scripts\Activate.ps1"
} elseif (Test-Path "$BackendDir\.venv\Scripts\Activate.ps1") {
    $VenvActivate = "$BackendDir\.venv\Scripts\Activate.ps1"
}

if ($VenvActivate) {
    Write-Host "[Backend] Activating virtual environment: $VenvActivate" -ForegroundColor Green
} else {
    Write-Host "[Backend] Warning: Virtual environment not found in backend\venv or backend\.venv." -ForegroundColor Yellow
}

if (-not (Test-Path "$BackendDir\.env") -and (Test-Path "$BackendDir\.env.example")) {
    Write-Host "[Backend] .env missing. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "$BackendDir\.env.example" "$BackendDir\.env"
}

# 2. Frontend Setup
Write-Host "`n[Frontend] Setting up Next.js environment..." -ForegroundColor Yellow
if (-not (Test-Path "$FrontendDir\.env.local")) {
    Write-Host "[Frontend] Creating default .env.local..." -ForegroundColor Yellow
    "NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -Encoding ascii "$FrontendDir\.env.local"
}

# 3. Start Backend & Frontend in separate windows
Write-Host "`n[Servers] Launching Backend and Frontend terminals..." -ForegroundColor Green

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$BackendDir'; if (Test-Path 'venv\Scripts\Activate.ps1') { . 'venv\Scripts\Activate.ps1' } elseif (Test-Path '.venv\Scripts\Activate.ps1') { . '.venv\Scripts\Activate.ps1' }; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FrontendDir'; npm run dev"

Write-Host "`n====================================================" -ForegroundColor Green
Write-Host "   ✨ NeedNow AI is up and running!                " -ForegroundColor Green
Write-Host "   • Frontend: http://localhost:3000              " -ForegroundColor Green
Write-Host "   • Backend:  http://localhost:8000              " -ForegroundColor Green
Write-Host "   • API Docs: http://localhost:8000/docs         " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

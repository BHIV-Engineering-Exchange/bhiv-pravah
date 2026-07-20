# Quick script to start backend services in PowerShell
# Usage: .\START_BACKEND.ps1

Write-Host ""
Write-Host "Starting BHIV HR Backend Services..." -ForegroundColor Green
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"

if (-not (Test-Path $backendDir)) {
    Write-Host "ERROR: Backend directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $backendDir

# Check if venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Pop-Location
    exit 1
}

# Activate venv and run services
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Green
Write-Host "  Gateway:    http://localhost:8000" -ForegroundColor Gray
Write-Host "  Agent:      http://localhost:9000" -ForegroundColor Gray
Write-Host "  LangGraph:  http://localhost:9001" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

python run_services.py

Pop-Location


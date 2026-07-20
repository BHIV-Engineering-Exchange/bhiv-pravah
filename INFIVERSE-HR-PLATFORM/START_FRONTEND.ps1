# Quick script to start frontend in PowerShell
# Usage: .\START_FRONTEND.ps1

Write-Host ""
Write-Host "Starting BHIV HR Frontend..." -ForegroundColor Green
Write-Host ""

$frontendDir = Join-Path $PSScriptRoot "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "ERROR: Frontend directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Green
Write-Host "  URL: http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

npm run dev

Pop-Location


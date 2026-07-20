# BHIV HR Platform - Complete Project Runner
# This script starts both backend and frontend services
# =====================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BHIV HR Platform - Starting All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

# Check if directories exist
if (-not (Test-Path $backendDir)) {
    Write-Host "ERROR: Backend directory not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $frontendDir)) {
    Write-Host "ERROR: Frontend directory not found!" -ForegroundColor Red
    exit 1
}

# Check if venv exists
$venvPath = Join-Path $backendDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Backend virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Function to start backend services
function Start-Backend {
    Write-Host ""
    Write-Host "🚀 Starting Backend Services..." -ForegroundColor Green
    Write-Host "   Gateway:    http://localhost:8000" -ForegroundColor Gray
    Write-Host "   Agent:      http://localhost:9000" -ForegroundColor Gray
    Write-Host "   LangGraph:  http://localhost:9001" -ForegroundColor Gray
    Write-Host ""
    
    Push-Location $backendDir
    & .\venv\Scripts\python.exe run_services.py
    Pop-Location
}

# Function to start frontend
function Start-Frontend {
    Write-Host ""
    Write-Host "🎨 Starting Frontend..." -ForegroundColor Green
    Write-Host "   URL: http://localhost:3000" -ForegroundColor Gray
    Write-Host ""
    
    Push-Location $frontendDir
    npm run dev
    Pop-Location
}

# Ask user which services to start
Write-Host "Select services to start:" -ForegroundColor Yellow
Write-Host "  1. Backend only" -ForegroundColor White
Write-Host "  2. Frontend only" -ForegroundColor White
Write-Host "  3. Both (Backend + Frontend)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter choice (1-3, default: 3)"

if ([string]::IsNullOrWhiteSpace($choice)) {
    $choice = "3"
}

switch ($choice) {
    "1" {
        Start-Backend
    }
    "2" {
        Start-Frontend
    }
    "3" {
        # Start backend in background job
        Write-Host "Starting backend in background..." -ForegroundColor Yellow
        $backendJob = Start-Job -ScriptBlock {
            param($dir)
            Set-Location $dir
            & .\venv\Scripts\python.exe run_services.py
        } -ArgumentList $backendDir
        
        # Wait a bit for backend to start
        Start-Sleep -Seconds 5
        
        # Start frontend in foreground
        Start-Frontend
        
        # Clean up backend job when frontend exits
        Stop-Job $backendJob
        Remove-Job $backendJob
    }
    default {
        Write-Host "Invalid choice. Starting both services..." -ForegroundColor Yellow
        Start-Backend
    }
}

Write-Host ""
Write-Host "Services stopped." -ForegroundColor Yellow


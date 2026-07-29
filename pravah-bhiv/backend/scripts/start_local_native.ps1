$BackendDir = "C:\Users\black\OneDrive\Desktop\Pravah\pravah-bhiv\backend"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "    PRAVAH NATIVE STARTUP SCRIPT (WINDOWS LOCAL)       " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Start Redis in Docker
Write-Host "`n[1/7] Starting Redis Event Bus via Docker Compose..." -ForegroundColor Yellow
Set-Location $BackendDir
docker compose -f docker-compose.yml --env-file environments/prod.env --profile prod up -d redis

Write-Host "Waiting 3 seconds for Redis to initialize..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

# Helper function to open a new terminal window, set all environment variables, and run a command
function Start-ServiceWindow {
    param(
        [string]$Title, 
        [string]$Command
    )
    
    # We must escape the $ variables with a backtick (`) so they evaluate in the NEW window, not the current one.
    $EnvSetup = "cd $BackendDir; .\venv\Scripts\activate; `$env:PYTHONPATH='$BackendDir'; `$env:ENVIRONMENT='prod'; `$env:REDIS_HOST='127.0.0.1'; `$env:LINEAGE_SIGNING_KEY='local-dummy-key'; `$env:SSPL_SECRET_KEY='local-dummy-key';"
    
    $FullCommand = "$EnvSetup `$host.UI.RawUI.WindowTitle = '$Title'; clear; Write-Host '--- $Title ---' -ForegroundColor Green; Write-Host 'Press CTRL+C to stop this service.`n' -ForegroundColor DarkGray; $Command"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $FullCommand
}

# 2. Control Plane
Write-Host "[2/7] Launching Control Plane (Port 7000)..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Control Plane (7000)" -Command "python wsgi.py"
Start-Sleep -Seconds 2

# 3. Decision Brain
Write-Host "[3/7] Launching Decision Brain (Port 8000)..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Decision Brain (8000)" -Command "uvicorn control_plane.backend.app.main:app --host 0.0.0.0 --port 8000 --log-level info"
Start-Sleep -Seconds 2

# 4. Observer Server
Write-Host "[4/7] Launching Observer Server (Port 8600)..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Observer (8600)" -Command "uvicorn observer_server:app --host 0.0.0.0 --port 8600 --log-level info"
Start-Sleep -Seconds 2

# 5. Deploy Agent
Write-Host "[5/7] Launching Multi-Deploy Agent..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Deploy Agent 1" -Command "`$env:WORKER_ID='1'; python -m control_plane.agents.multi_deploy_agent --env prod --workers 1"

# 6. Queue Monitor
Write-Host "[6/7] Launching Queue Monitor..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Queue Monitor" -Command "python -m monitoring.queue_monitor --continuous --cycles 0"

# 7. Health Monitor
Write-Host "[7/7] Launching Health Monitor..." -ForegroundColor Yellow
Start-ServiceWindow -Title "PRAVAH Health Monitor" -Command "python -m monitoring.infra_health_monitor --env prod --continuous"

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "  All services launched successfully in new windows!   " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

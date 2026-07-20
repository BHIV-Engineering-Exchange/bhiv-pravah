@echo off
REM ============================================================
REM start_gurukul_services.bat
REM Gurukul 24x7 Deterministic Service Orchestrator (Windows)
REM
REM Starts all services in the correct dependency order:
REM   1. Database verification
REM   2. Vaani Voice Engine (Port 8008)
REM   3. Gurukul Backend API (Port 3000)
REM   4. Watchdog Supervisor
REM
REM Usage: start_gurukul_services.bat
REM ============================================================

echo ====================================================
echo  Gurukul 24x7 Infrastructure Orchestrator (Windows)
echo  Started at: %date% %time%
echo ====================================================
echo.

set SCRIPT_DIR=%~dp0
set VAANI_DIR=%SCRIPT_DIR%..\vaani-engine

REM Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

REM ── Step 1: Database Verification ─────────────────────────
echo [1/4] Checking Database Connectivity...
cd /d "%SCRIPT_DIR%"
python -c "from app.core.database import engine; from sqlalchemy import text; conn = engine.connect(); conn.execute(text('SELECT 1')); print('    OK: SQL database is reachable'); conn.close()" 2>nul || echo     ! SQL database check skipped
echo.

REM ── Step 2: Start Vaani Voice Engine ──────────────────────
echo [2/4] Starting Vaani Sovereign Voice Engine (Port 8008)...
cd /d "%VAANI_DIR%"
start "Vaani Engine" /MIN cmd /c "python voice_service_api.py > "%SCRIPT_DIR%logs\vaani.log" 2>&1"
echo     Vaani Engine starting in background...
echo     Waiting 30 seconds for model to load...
timeout /t 30 /nobreak >nul
echo.

REM ── Step 3: Start Gurukul Backend ─────────────────────────
echo [3/4] Starting Gurukul Backend API (Port 3000)...
cd /d "%SCRIPT_DIR%"
start "Gurukul Backend" /MIN cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 > logs\backend.log 2>&1"
echo     Backend starting in background...
echo     Waiting 10 seconds for startup...
timeout /t 10 /nobreak >nul
echo.

REM ── Step 4: Start Watchdog Supervisor ─────────────────────
echo [4/4] Starting Uptime Watchdog...
cd /d "%SCRIPT_DIR%"
start "Gurukul Watchdog" /MIN cmd /c "python watchdog_runner.py > logs\watchdog.log 2>&1"
echo     Watchdog starting in background...
echo.

REM ── Summary ───────────────────────────────────────────────
echo ====================================================
echo  All Gurukul services are STARTING
echo.
echo  Services:
echo    Backend:  http://localhost:3000
echo    Vaani:    http://localhost:8008
echo    Watchdog: Running in background
echo.
echo  Health:     http://localhost:3000/system/health
echo  API Docs:   http://localhost:3000/docs
echo  Logs:       %SCRIPT_DIR%logs\
echo ====================================================

pause

@echo off
echo.
echo === Gurukul Service Launcher ===
echo.
echo Choose launch mode:
echo   [1] Supervised Mode  (Python Orchestrator - auto-restarts crashed services)
echo   [2] Manual Mode      (Individual windows - original behaviour)
echo.
set /p CHOICE=Enter 1 or 2: 
echo.

if "%CHOICE%"=="1" goto :SUPERVISED
if "%CHOICE%"=="2" goto :MANUAL
echo Invalid choice. Defaulting to Manual Mode.
goto :MANUAL

:SUPERVISED
echo Starting in SUPERVISED mode via service_orchestrator.py...
echo Services will auto-restart on crash. Press Ctrl+C to stop all.
echo.
cd /d %~dp0backend
python scripts/service_orchestrator.py --poll 30
goto :EOF

:MANUAL
echo Starting in MANUAL mode (individual CMD windows)...
echo.

REM Start Gurukul Backend
start "Gurukul Backend" cmd /k "cd /d %~dp0backend && echo Gurukul Backend starting on http://localhost:3000 && uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload"

REM Wait a bit
timeout /t 1 /nobreak >nul

REM Start EMS Backend
start "EMS Backend" cmd /k "cd /d %~dp0EMS-System && echo EMS Backend starting on http://localhost:8000 && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a bit
timeout /t 1 /nobreak >nul

REM Start Vaani Engine
start "Vaani Engine" cmd /k "cd /d %~dp0vaani-engine && echo Vaani Engine starting on http://localhost:8008 && python voice_service_api.py"

REM Wait a bit
timeout /t 1 /nobreak >nul

REM Start Gurukul Frontend
start "Gurukul Frontend" cmd /k "cd /d %~dp0Frontend && echo Gurukul Frontend starting on http://localhost:5173 && npm run dev"

REM Wait a bit
timeout /t 1 /nobreak >nul

REM Start EMS Frontend
start "EMS Frontend" cmd /k "cd /d %~dp0EMS-System\frontend && echo EMS Frontend starting on http://localhost:3001 && npm run dev"

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start Bucket Consumer (integrated mode - uses same backend for karma)
start "Bucket Consumer" cmd /k "cd /d %~dp0backend && echo Bucket Consumer starting (integrated mode)... && python scripts/start_bucket_consumer.py"

echo.
echo All services are starting in separate windows!
echo.
echo Service URLs:
echo   - Gurukul Backend:  http://localhost:3000 (includes Karma Tracker)
echo   - EMS Backend:      http://localhost:8000
echo   - Vaani Engine:     http://localhost:8008
echo   - Gurukul Frontend: http://localhost:5173
echo   - EMS Frontend:     http://localhost:3001
echo   - Bucket Consumer:  Processing PRANA packets (integrated mode)
echo.
pause


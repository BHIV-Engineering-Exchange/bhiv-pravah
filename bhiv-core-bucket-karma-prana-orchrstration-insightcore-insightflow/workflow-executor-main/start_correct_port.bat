@echo off
echo ========================================
echo Starting Workflow Executor on Port 8003
echo ========================================
echo.
echo Port Allocation:
echo - Karma:    8000
echo - Bucket:   8001
echo - Core:     8002
echo - Workflow: 8003
echo.
echo Starting service...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

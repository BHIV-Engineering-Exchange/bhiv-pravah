@echo off
echo Starting InsightFlow Dashboard...
echo.

echo [1/2] Starting Backend Server...
cd backend
start "InsightFlow Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Frontend Development Server...
cd ..\frontend
start "InsightFlow Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   InsightFlow Dashboard Starting...
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause > nul
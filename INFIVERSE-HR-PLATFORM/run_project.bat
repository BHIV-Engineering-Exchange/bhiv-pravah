@echo off
REM ========================================
REM BHIV HR Platform - Complete Project Runner
REM This script starts both backend and frontend services
REM ========================================

echo.
echo ========================================
echo BHIV HR Platform - Starting All Services
echo ========================================
echo.

REM Check if backend venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Backend virtual environment not found!
    echo Please run: cd backend ^&^& setup_venv.bat
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo ERROR: Frontend dependencies not found!
    echo Please run: cd frontend ^&^& npm install
    pause
    exit /b 1
)

echo.
echo Select services to start:
echo   1. Backend only
echo   2. Frontend only
echo   3. Both (Backend + Frontend) - Recommended
echo.
set /p choice="Enter choice (1-3, default: 3): "

if "%choice%"=="" set choice=3

if "%choice%"=="1" (
    echo.
    echo Starting Backend Services...
    echo   Gateway:    http://localhost:8000
    echo   Agent:      http://localhost:9000
    echo   LangGraph:  http://localhost:9001
    echo.
    cd backend
    call run_with_venv.bat
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo Starting Frontend...
    echo   URL: http://localhost:3000
    echo.
    cd frontend
    npm run dev
    goto :end
)

if "%choice%"=="3" (
    echo.
    echo Starting Backend Services in new window...
    start "BHIV Backend Services" cmd /k "cd backend && call run_with_venv.bat"
    timeout /t 5 /nobreak >nul
    echo.
    echo Starting Frontend...
    echo   URL: http://localhost:3000
    echo.
    cd frontend
    npm run dev
    goto :end
)

echo Invalid choice. Exiting.
pause
exit /b 1

:end
echo.
echo Services stopped.
pause


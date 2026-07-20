@echo off
echo ========================================
echo Real-Time Micro-Bridge - Quick Start
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js v18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [1/5] Checking Node.js version...
node --version
echo.

REM Backend setup
echo [2/5] Setting up backend...
cd backend
if not exist node_modules (
    echo Installing backend dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Backend npm install failed!
        pause
        exit /b 1
    )
)

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Starting backend server...
start "Backend Server" cmd /k "npm start"
timeout /t 3 /nobreak >nul
cd ..

REM Frontend setup
echo [3/5] Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Frontend npm install failed!
        pause
        exit /b 1
    )
)

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo [4/5] Starting frontend server...
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo [5/5] System Ready!
echo ========================================
echo Backend:  http://localhost:3000
echo Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to open dashboard in browser...
pause >nul
start http://localhost:5173

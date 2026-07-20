@echo off
echo ========================================
echo BHIV HR Platform - Local Deployment
echo ========================================
echo.

cd /d "%~dp0\.."

echo [1/5] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)
echo ✓ Docker is available

echo.
echo [2/5] Stopping existing containers...
docker-compose -f deployment\docker\docker-compose.production.yml down --remove-orphans >nul 2>&1
echo ✓ Cleaned up existing containers

echo.
echo [3/5] Building and starting services...
docker-compose -f deployment\docker\docker-compose.production.yml up -d --build
if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo.
echo [4/5] Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo.
echo [5/5] Checking service health...
echo Testing Gateway...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠ WARNING: Gateway service may still be starting...
) else (
    echo ✓ Gateway: HEALTHY
)

echo Testing AI Agent...
curl -s http://localhost:9000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠ WARNING: Agent service may still be starting...
) else (
    echo ✓ Agent: HEALTHY
)

echo.
echo ========================================
echo 🚀 BHIV HR Platform is now running!
echo ========================================
echo.
echo 📊 Service URLs:
echo   • Gateway API:    http://localhost:8000/docs
echo   • AI Agent:       http://localhost:9000/docs
echo   • HR Portal:      http://localhost:8501
echo   • Client Portal:  http://localhost:8502
echo   • Database:       localhost:5432
echo.
echo 🔧 Management Commands:
echo   • View logs:      docker-compose -f deployment\docker\docker-compose.production.yml logs -f
echo   • Stop services:  docker-compose -f deployment\docker\docker-compose.production.yml down
echo   • Restart:        docker-compose -f deployment\docker\docker-compose.production.yml restart
echo.
echo 🧪 Quick Test:
echo   curl http://localhost:8000/health
echo   curl http://localhost:9000/health
echo.
pause
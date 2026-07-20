@echo off
REM Docker setup script for ARTHA application (Windows)

echo 🐳 Setting up ARTHA Docker environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist backend\.env (
    echo 📝 Creating backend\.env file from template...
    copy backend\.env.example backend\.env
    echo ⚠️  Please update backend\.env with your configuration before running the application.
)

REM Build and start development environment
echo 🚀 Starting development environment...
docker-compose -f docker-compose.dev.yml up --build -d

echo ✅ ARTHA development environment is ready!
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:5000
echo 🗄️  MongoDB: Cloud Atlas (configured in .env)
echo.
echo 📋 Useful commands:
echo   docker-compose -f docker-compose.dev.yml logs -f    # View logs
echo   docker-compose -f docker-compose.dev.yml down       # Stop services
echo   docker-compose -f docker-compose.dev.yml restart    # Restart services
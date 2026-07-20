@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting ARTHA deployment...

set SEED_DB=false
:parse_args
if "%~1"=="--seed" (
    set SEED_DB=true
    shift
    goto parse_args
)
if not "%~1"=="" (
    shift
    goto parse_args
)

REM Check if .env.production exists
if not exist .env.production (
    echo ❌ Error: .env.production not found
    echo Please create .env.production from .env.production.example
    exit /b 1
)

REM Check if backend/.env.production exists
if not exist backend\.env.production (
    echo ❌ Error: backend/.env.production not found
    echo Please create backend/.env.production from backend/.env.production.example
    exit /b 1
)

echo 📦 Building Docker images...
docker-compose -f docker-compose.prod.yml build --no-cache

echo 🛑 Stopping existing containers...
docker-compose -f docker-compose.prod.yml down

echo 🚀 Starting containers...
docker-compose -f docker-compose.prod.yml up -d

echo ⏳ Waiting for services to be healthy...
timeout /t 15 /nobreak > nul

echo Checking MongoDB...
docker exec artha-mongo-prod mongosh --eval "db.adminCommand('ping')" > nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ MongoDB is healthy
) else (
    echo ✗ MongoDB is not responding
    exit /b 1
)

echo Initializing MongoDB replica set...
docker exec artha-mongo-prod mongosh --eval "rs.initiate()" > nul 2>&1

timeout /t 5 /nobreak > nul

echo Checking Redis...
docker exec artha-redis-prod redis-cli ping > nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Redis is healthy
) else (
    echo ✗ Redis is not responding
    exit /b 1
)

echo Checking backend...
timeout /t 10 /nobreak > nul
curl -f http://localhost:5000/ready > nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Backend is healthy
) else (
    echo ✗ Backend is not responding
    docker logs artha-backend-prod --tail 50
    exit /b 1
)

echo Creating database indexes...
docker exec artha-backend-prod npm run create-indexes

if "%SEED_DB%"=="true" (
    echo Seeding database...
    docker exec artha-backend-prod npm run seed
)

echo Checking frontend...
curl -f http://localhost/health > nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Frontend is healthy
) else (
    echo ✗ Frontend is not responding
    docker logs artha-frontend-prod --tail 50
    exit /b 1
)

echo ✅ Deployment completed successfully!
echo.
echo Services:
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost
echo   Health:   http://localhost:5000/health/detailed
echo.
echo To view logs:
echo   docker-compose -f docker-compose.prod.yml logs -f
@echo off
echo ========================================
echo Restarting BHIV Bucket with Core Integration
echo ========================================
echo.

echo Finding Bucket process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo Waiting for port to be released...
timeout /t 2 /nobreak >nul

echo Starting Bucket with Core integration endpoints...
cd BHIV_Central_Depository-main
start "BHIV Bucket" cmd /k "python main.py"

echo.
echo Waiting for Bucket to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Testing Core integration endpoints...
echo ========================================
curl -s http://localhost:8000/health | python -m json.tool

echo.
echo ========================================
echo Bucket restarted! Run test_integration.py to verify.
echo ========================================
pause

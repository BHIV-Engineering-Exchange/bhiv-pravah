@echo off
echo ========================================
echo Day 13 - E2E Pipeline Test Runner
echo ========================================
echo.

echo [1/3] Checking if backend is running...
curl -s http://localhost:3000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Backend not running!
    echo Please start backend first: node index.js
    exit /b 1
)
echo     Backend is running

echo.
echo [2/3] Checking if Python engine is running...
timeout /t 2 /nobreak >nul
echo     Assuming engine is running...

echo.
echo [3/3] Running E2E Pipeline Test...
echo.
node tests\test_e2e_pipeline.js

echo.
echo ========================================
echo Test Complete
echo ========================================
pause

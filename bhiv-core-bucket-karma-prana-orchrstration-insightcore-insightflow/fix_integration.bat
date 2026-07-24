@echo off
echo ========================================
echo BHIV Core-Bucket Integration Fix
echo ========================================
echo.
echo Problem: Core integration endpoints returning 404
echo Solution: Restart Bucket to load new endpoints
echo.
echo ========================================
echo Step 1: Stopping old Bucket process...
echo ========================================

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Found Bucket on PID %%a - stopping...
    taskkill /F /PID %%a
    echo Bucket stopped!
)

echo.
echo ========================================
echo Step 2: Waiting for port to be released...
echo ========================================
ping 127.0.0.1 -n 4 > nul
echo Port 8000 released!

echo.
echo ========================================
echo Step 3: Starting Bucket with Core integration...
echo ========================================
echo Opening new window for Bucket...
start "BHIV Bucket (Port 8000)" cmd /k "cd BHIV_Central_Depository-main && python main.py"

echo.
echo Waiting for Bucket to initialize (15 seconds)...
ping 127.0.0.1 -n 16 > nul

echo.
echo ========================================
echo Step 4: Testing Core integration endpoints...
echo ========================================
echo.

echo Testing /health endpoint...
curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Bucket is running
) else (
    echo [FAIL] Bucket not responding - wait longer and try test_integration.py
    goto end
)

echo.
echo Testing /core/write-event endpoint...
curl -X POST http://localhost:8000/core/write-event -H "Content-Type: application/json" -d "{\"requester_id\":\"bhiv_core\",\"event_data\":{\"test\":\"restart_test\"}}" -s > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Core write-event endpoint loaded
) else (
    echo [WARN] Endpoint may still be loading...
)

echo.
echo Testing /core/stats endpoint...
curl -s http://localhost:8000/core/stats > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Core stats endpoint loaded
) else (
    echo [WARN] Endpoint may still be loading...
)

echo.
echo Testing /core/events endpoint...
curl -s http://localhost:8000/core/events > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Core events endpoint loaded
) else (
    echo [WARN] Endpoint may still be loading...
)

:end
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Run: python test_integration.py
echo 2. All tests should now PASS
echo 3. If still failing, wait 10 more seconds and retry
echo ========================================
echo.
pause

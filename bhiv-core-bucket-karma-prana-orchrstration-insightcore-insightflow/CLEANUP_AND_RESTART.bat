@echo off
echo ========================================
echo CLEANUP AND RESTART ALL SERVICES
echo ========================================
echo.

echo [1/4] Killing all processes on ports 8000-8003...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8003" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
echo Done!
echo.

timeout /t 3 /nobreak >nul

echo [2/4] Verifying ports are free...
netstat -ano | findstr ":8000 :8001 :8002 :8003" | findstr "LISTENING"
if %errorlevel% equ 0 (
    echo WARNING: Some ports still in use. Wait 10 seconds and try again.
    timeout /t 10 /nobreak >nul
) else (
    echo All ports are free!
)
echo.

echo ========================================
echo READY TO START SERVICES
echo ========================================
echo.
echo Start services in this order:
echo.
echo Terminal 1: cd karma_chain_v2-main ^&^& python main.py
echo Terminal 2: cd BHIV_Central_Depository-main ^&^& python main.py
echo Terminal 3: cd v1-BHIV_CORE-main ^&^& python mcp_bridge.py
echo Terminal 4: cd workflow-executor-main ^&^& python main.py
echo.
echo Press any key to exit...
pause >nul

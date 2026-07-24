@echo off
echo ========================================
echo Starting 7-Pillar BHIV System
echo ========================================
echo.

echo [1/7] Starting Karma (8000)...
start "Karma" cmd /k "cd /d karma_chain_v2-main && python main.py"
timeout /t 12 /nobreak >nul

echo [2/7] Starting Bucket (8001)...
start "Bucket" cmd /k "cd /d BHIV_Central_Depository-main && python main.py"
timeout /t 12 /nobreak >nul

echo [3/7] Starting Insight Core (8005)...
start "Insight" cmd /k "cd /d insightcore-bridgev4x-main && python insight_service.py"
timeout /t 10 /nobreak >nul

echo [4/7] Starting Core (8002)...
start "Core" cmd /k "cd /d v1-BHIV_CORE-main && python mcp_bridge.py"
timeout /t 12 /nobreak >nul

echo [5/7] Starting Workflow (8003)...
start "Workflow" cmd /k "cd /d workflow-executor-main && python main.py"
timeout /t 10 /nobreak >nul

echo [6/7] Starting UAO (8004)...
start "UAO" cmd /k "cd /d Unified Action Orchestration && python action_orchestrator.py"
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Ports:
echo   Karma:    8000
echo   Bucket:   8001
echo   Core:     8002
echo   Workflow: 8003
echo   UAO:      8004
echo   Insight:  8005
echo.
echo Run verification:
echo   python verify_all_services.py
echo.
echo Run complete flow test:
echo   python test_complete_insight_flow.py
echo.
pause

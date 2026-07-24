@echo off
echo Starting Workflow Executor on port 8003...
echo.
echo Port Allocation:
echo   - Karma: 8000
echo   - Bucket: 8001
echo   - Core: 8002
echo   - Workflow Executor: 8003
echo.
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

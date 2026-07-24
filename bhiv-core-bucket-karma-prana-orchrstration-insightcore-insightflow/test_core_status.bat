@echo off
echo ========================================
echo Testing Core Integration Status
echo ========================================
echo.

echo Checking Bucket health with core_integration status...
curl -s http://localhost:8000/health | python -m json.tool

echo.
echo ========================================
echo Running full integration test...
echo ========================================
python test_integration.py

echo.
pause

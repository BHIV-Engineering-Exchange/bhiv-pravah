@echo off
echo ========================================
echo RESTARTING BHIV CENTRAL DEPOSITORY
echo ========================================
echo.
echo This will restart the server to load updated agent code.
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting server...
python main.py

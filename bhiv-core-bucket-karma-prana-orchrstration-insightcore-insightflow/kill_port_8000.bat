@echo off
echo Killing process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Found process %%a using port 8000
    taskkill /f /pid %%a
)
echo Port 8000 should now be free
pause
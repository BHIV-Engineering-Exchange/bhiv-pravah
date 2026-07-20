@echo off
echo ============================================
echo   STARTING ADMIN CHATBOT SYSTEM
echo ============================================
echo.

echo Step 1: Installing server dependencies...
cd /d "%~dp0server"
call npm install groq-sdk
echo.

echo Step 2: Installing client dependencies...
cd /d "%~dp0client"
call npm install @radix-ui/react-scroll-area
echo.

echo ============================================
echo   DEPENDENCIES INSTALLED!
echo ============================================
echo.
echo Now starting the servers...
echo.
echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0server && npm start"
timeout /t 3 /nobreak >nul

echo Starting Frontend Client...
start "Frontend Client" cmd /k "cd /d %~dp0client && npm run dev"

echo.
echo ============================================
echo   SERVERS STARTING!
echo ============================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Check the new terminal windows for status.
echo Press any key to exit this window...
pause >nul


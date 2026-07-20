@echo off
ECHO ========================================
ECHO Employee Activity Agent - Setup
ECHO ========================================
ECHO.

REM Check if Node.js is installed
where node >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Node.js is not installed!
    ECHO Please install Node.js from https://nodejs.org/
    ECHO.
    PAUSE
    EXIT /B 1
)

ECHO [1/5] Node.js found: 
node --version
ECHO.

ECHO [2/5] Checking npm...
npm --version
ECHO.

REM Check if .env file exists
IF NOT EXIST .env (
    ECHO [3/5] Creating .env file from template...
    copy .env.example .env
    ECHO.
    ECHO [!] IMPORTANT: Edit .env file and set your backend URL
    ECHO     Open .env and update AGENT_API_BASE_URL
    ECHO.
) ELSE (
    ECHO [3/5] .env file already exists
    ECHO.
)

ECHO [4/5] Installing dependencies...
ECHO This may take a few minutes...
ECHO.
call npm install

IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERROR] Failed to install dependencies!
    ECHO.
    ECHO Common fixes:
    ECHO - Run as Administrator
    ECHO - Install Windows Build Tools: npm install --global windows-build-tools
    ECHO - Restart your computer and try again
    ECHO.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO [5/5] Setup complete!
ECHO.
ECHO ========================================
ECHO Next Steps:
ECHO ========================================
ECHO 1. Edit .env file with your backend URL
ECHO 2. Run the app: npm start
ECHO 3. Build for distribution: npm run build:win
ECHO.
ECHO ========================================
ECHO.
PAUSE

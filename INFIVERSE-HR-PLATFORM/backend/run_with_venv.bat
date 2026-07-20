@echo off
REM ========================================
REM BHIV HR Platform - Run Services with Virtual Environment
REM ========================================
REM This script activates venv and runs all backend services
REM Usage: run_with_venv.bat
REM ========================================

echo.
echo ========================================
echo BHIV HR Platform - Starting Backend Services
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Running setup first...
    echo.
    call setup_venv.bat
    if errorlevel 1 (
        echo.
        echo Setup failed! Please check the error above.
        pause
        exit /b 1
    )
    echo.
)

REM Verify venv exists after setup
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo ERROR: Virtual environment still not found after setup!
    echo Please run setup_venv.bat manually and check for errors.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)

echo Starting services...
python run_services.py

pause

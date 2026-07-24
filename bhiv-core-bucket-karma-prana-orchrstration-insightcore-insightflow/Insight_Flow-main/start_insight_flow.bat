@echo off
echo Starting Insight Flow Backend (Port 8007)...
cd /d "c:\Users\Ashmit Pandey\Desktop\Core-Bucket_KarmaIntegratedPart-main\Insight_Flow-main\backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\fastapi" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start server on port 8007
echo Starting Insight Flow on port 8007...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload

@echo off
echo ========================================
echo Starting Insight Flow Backend (Port 8007)
echo ========================================
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload

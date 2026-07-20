@echo off
echo Starting AI Agent Logistics System...
echo =====================================

REM Set encoding for Unicode support
set PYTHONIOENCODING=utf-8
set STREAMLIT_SERVER_HEADLESS=true

REM Kill any existing processes
echo Cleaning up existing processes...
taskkill /f /im streamlit.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
timeout /t 2 >nul

REM Start API server in background
echo Starting API server on port 8000...
start "API Server" cmd /c "set PYTHONIOENCODING=utf-8 && uvicorn api_app:app --host 0.0.0.0 --port 8000"

REM Wait for API to start
timeout /t 3 >nul

REM Start CRM Dashboard
echo Starting CRM Dashboard on port 8502...
start "CRM Dashboard" cmd /c "set PYTHONIOENCODING=utf-8 && set STREAMLIT_SERVER_HEADLESS=true && streamlit run crm_dashboard.py --server.port=8502"

REM Start Main Dashboard
echo Starting Main Dashboard on port 8503...
start "Main Dashboard" cmd /c "set PYTHONIOENCODING=utf-8 && set STREAMLIT_SERVER_HEADLESS=true && streamlit run dashboard_app.py --server.port=8503"

REM Start Product Catalog Dashboard
echo Starting Product Catalog Dashboard on port 8505...
start "Product Catalog" cmd /c "set PYTHONIOENCODING=utf-8 && set STREAMLIT_SERVER_HEADLESS=true && streamlit run product_catalog_dashboard.py --server.port=8505"

echo.
echo =====================================
echo AI Agent Logistics System Started!
echo =====================================
echo.
echo 🌐 API Server:        http://localhost:8000
echo 📊 CRM Dashboard:     http://localhost:8502
echo 📦 Main Dashboard:    http://localhost:8503
echo 🛍️  Product Catalog:   http://localhost:8505
echo 📖 API Docs:          http://localhost:8000/docs
echo.
echo Press any key to exit (services will continue running)...
pause >nul
@echo off
echo ========================================
echo Starting Insight Flow Bridge (Standalone Mode)
echo Port: 8006
echo ========================================
echo.
echo This runs the bridge WITHOUT requiring the full backend.
echo For full features, use start_insight_flow_fixed.bat first.
echo.
cd /d "%~dp0"
python insight_flow_bridge_standalone.py

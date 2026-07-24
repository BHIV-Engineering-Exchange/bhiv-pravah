@echo off
REM endpoint_tests.bat - Windows batch file for endpoint verification

echo === InsightFlow Endpoint Tests ===
echo.

echo Starting server in background...
start /B uvicorn app.main:app --reload
timeout /t 5 /nobreak > nul

echo.
echo Testing Route Agent Endpoint...
curl -X POST http://localhost:8000/api/v1/routing/route-agent ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_type\": \"nlp\", \"context\": {\"text\": \"test\"}, \"confidence_threshold\": 0.5}"
echo.

echo Testing Dashboard Endpoints...
echo Performance metrics:
curl "http://localhost:8000/dashboard/metrics/performance?hours=24"
echo.

echo Accuracy metrics:
curl http://localhost:8000/dashboard/metrics/accuracy
echo.

echo Agent metrics:
curl http://localhost:8000/dashboard/metrics/agents
echo.

echo Testing Public Routing Endpoints...
echo Recent decisions:
curl "http://localhost:8000/api/routing/decisions?limit=5"
echo.

echo Statistics:
curl http://localhost:8000/api/routing/statistics
echo.

echo Testing Health Endpoints...
echo Health check:
curl http://localhost:8000/health
echo.

echo API version:
curl http://localhost:8000/api/version
echo.

echo === Endpoint Tests Complete ===
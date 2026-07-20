
# Gurukul Backend Run Script
# ---------------------------
# Activates the backend with the new modular architecture.
# Make sure .env is configured with SUPABASE_URL if using DB features.

Write-Host "Starting Gurukul Backend (v2 Refactored)..." -ForegroundColor Cyan
Write-Host "Command: python -m app.main" -ForegroundColor Gray

$env:PYTHONPATH = "."
python -m app.main

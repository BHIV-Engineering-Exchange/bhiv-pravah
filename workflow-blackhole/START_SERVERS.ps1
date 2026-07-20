# Admin Chatbot Startup Script
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   STARTING ADMIN CHATBOT SYSTEM" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot

# Start Backend Server
Write-Host "Starting Backend Server on port 5000..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\server'; npm start" -PassThru
Start-Sleep -Seconds 5

# Start Frontend Client
Write-Host "Starting Frontend Client on port 5173..." -ForegroundColor Green
$frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\client'; npm run dev" -PassThru
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   SERVERS STARTED!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Backend PID: $($backendJob.Id)" -ForegroundColor White
Write-Host "✅ Frontend PID: $($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "To stop servers, close the terminal windows or press Ctrl+C in each." -ForegroundColor Gray
Write-Host ""


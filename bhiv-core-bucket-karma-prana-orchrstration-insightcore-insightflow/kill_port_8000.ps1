# Kill all processes on port 8000
Write-Host "Killing all processes on port 8000..." -ForegroundColor Yellow

$processes = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($pid in $processes) {
        Write-Host "Killing process $pid..." -ForegroundColor Red
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Done! Port 8000 should be free now." -ForegroundColor Green
} else {
    Write-Host "No processes found on port 8000." -ForegroundColor Green
}

# Wait a moment
Start-Sleep -Seconds 2

# Verify
Write-Host "`nVerifying port 8000 is free..." -ForegroundColor Yellow
$check = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($check) {
    Write-Host "WARNING: Port 8000 still in use!" -ForegroundColor Red
    $check | Format-Table
} else {
    Write-Host "SUCCESS: Port 8000 is free!" -ForegroundColor Green
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

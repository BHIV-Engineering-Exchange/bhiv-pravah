# Run this after 60 seconds of Electron tracking

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          VERIFICATION SCRIPT                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

cd c:\Users\A\workflow-blackhole\server

Write-Host "Checking TODAY's activity for vinayak tiwari..." -ForegroundColor Yellow
node check-today-activity.js

Write-Host "`n" -ForegroundColor White
Write-Host "Checking detailed activity records..." -ForegroundColor Yellow
node check-activity-details.js

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          TEST RESULT                                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "✓ If you see mouse/keyboard events above = SUCCESS!" -ForegroundColor Green
Write-Host "✗ If all values are 'N/A' or undefined = FAILED" -ForegroundColor Red
Write-Host "`nNext step:" -ForegroundColor Cyan
Write-Host "  SUCCESS → Run: git add . && git commit -m 'Fixed activity tracking' && git push upstream main" -ForegroundColor Green
Write-Host "  FAILED  → Share the output for debugging" -ForegroundColor Red
Write-Host ""

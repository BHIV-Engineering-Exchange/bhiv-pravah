# Real-time Activity Monitor for Vinayak Tiwari
# Run this while testing to see live data updates

$userId = "681dc8122ae66516796d4854"  # vinayak tiwari
$lastCount = 0

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     REAL-TIME ACTIVITY MONITOR (Vinayak Tiwari)       ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
Write-Host "Monitoring database for new activity records..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

while ($true) {
    $result = node -e "
        const mongoose = require('mongoose');
        require('dotenv').config();
        mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/workflow')
          .then(async () => {
            const EmployeeActivity = require('./models/EmployeeActivity');
            const today = new Date();
            today.setHours(0,0,0,0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            const count = await EmployeeActivity.countDocuments({
              employee: '$userId',
              timestamp: { \$gte: today, \$lt: tomorrow }
            });
            
            const latest = await EmployeeActivity.findOne({
              employee: '$userId',
              timestamp: { \$gte: today, \$lt: tomorrow }
            }).sort({ timestamp: -1 }).lean();
            
            console.log(JSON.stringify({ count, latest }));
            process.exit(0);
          })
          .catch(() => process.exit(1));
    " 2>$null
    
    if ($result) {
        $data = $result | ConvertFrom-Json
        
        if ($data.count -gt $lastCount) {
            $timestamp = Get-Date -Format "HH:mm:ss"
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
            Write-Host "✓ NEW RECORD! " -NoNewline -ForegroundColor Green
            Write-Host "Total today: $($data.count) | " -NoNewline -ForegroundColor Cyan
            
            if ($data.latest) {
                $mouse = if ($data.latest.mouseEvents) { $data.latest.mouseEvents } elseif ($data.latest.mouse_activity_score) { $data.latest.mouse_activity_score } else { "N/A" }
                $keyboard = if ($data.latest.keyboardEvents) { $data.latest.keyboardEvents } elseif ($data.latest.keystroke_count) { $data.latest.keystroke_count } else { "N/A" }
                
                Write-Host "Mouse: $mouse | Keyboard: $keyboard" -ForegroundColor Yellow
            }
            
            $lastCount = $data.count
        } else {
            $timestamp = Get-Date -Format "HH:mm:ss"
            Write-Host "[$timestamp] Waiting... (Total: $($data.count))" -ForegroundColor DarkGray
        }
    }
    
    Start-Sleep -Seconds 5
}

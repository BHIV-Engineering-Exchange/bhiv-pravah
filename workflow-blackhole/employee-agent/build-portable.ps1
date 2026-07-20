# Build Portable Electron App (No Signing Required)

Write-Host "Building Employee Activity Agent Portable..." -ForegroundColor Cyan

# Clean dist folder
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}
New-Item -ItemType Directory -Path "dist" -Force | Out-Null
New-Item -ItemType Directory -Path "dist\portable" -Force | Out-Null

# Copy app files
Write-Host "Copying application files..." -ForegroundColor Yellow
Copy-Item "src" -Destination "dist\portable\src" -Recurse
Copy-Item "package.json" -Destination "dist\portable\"
Copy-Item "assets" -Destination "dist\portable\assets" -Recurse -ErrorAction SilentlyContinue
if (Test-Path ".env") {
    Copy-Item ".env" -Destination "dist\portable\"
    Write-Host "  ✓ Copied .env file" -ForegroundColor Green
} elseif (Test-Path ".env.example") {
    Copy-Item ".env.example" -Destination "dist\portable\.env"
    Write-Host "  ✓ Copied .env.example as .env (please configure)" -ForegroundColor Yellow
}

# Install dependencies in portable folder
Write-Host "Installing dependencies in portable folder..." -ForegroundColor Yellow
Push-Location "dist\portable"
npm install --production --no-optional
Pop-Location

# Copy Electron executable from node_modules
Write-Host "Copying Electron executable..." -ForegroundColor Yellow
$electronPath = "node_modules\electron\dist"
if (Test-Path $electronPath) {
    Copy-Item "$electronPath\*" -Destination "dist\portable\" -Recurse
}

# Create launcher batch file
Write-Host "Creating launcher..." -ForegroundColor Yellow
$launcherContent = @"
@echo off
echo Starting Employee Activity Agent...
"%~dp0electron.exe" "%~dp0src\main.js"
"@
$launcherContent | Out-File -FilePath "dist\portable\EmployeeActivityAgent.bat" -Encoding ASCII

# Also create a PowerShell launcher for better error handling
$psLauncherContent = @"
`$ErrorActionPreference = 'Stop'
`$scriptPath = Split-Path -Parent `$MyInvocation.MyCommand.Path
Set-Location `$scriptPath
Write-Host "Starting Employee Activity Agent..." -ForegroundColor Cyan
Write-Host "App Directory: `$scriptPath" -ForegroundColor Gray
if (-not (Test-Path "`$scriptPath\package.json")) {
    Write-Host "ERROR: package.json not found!" -ForegroundColor Red
    Write-Host "Please ensure all files were extracted properly." -ForegroundColor Yellow
    pause
    exit 1
}
& "`$scriptPath\electron.exe" "`$scriptPath"
if (`$LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Electron exited with code `$LASTEXITCODE" -ForegroundColor Red
    pause
}
"@
$psLauncherContent | Out-File -FilePath "dist\portable\EmployeeActivityAgent.ps1" -Encoding UTF8

# Create README
$readmeContent = @"
# Employee Activity Agent - Portable

## Initial Setup (IMPORTANT!)
1. Open `.env` file in a text editor (Notepad)
2. Update AGENT_API_BASE_URL with your backend server URL:
   - For localhost: http://127.0.0.1:5001
   - For production: https://your-backend-url.onrender.com
3. Save the file

## How to Run
1. Double-click `EmployeeActivityAgent.bat` (or `EmployeeActivityAgent.ps1`)
2. The agent will start and appear in the system tray
3. Login with your employee credentials
4. The agent will automatically track activity when you start your workday from the dashboard

## Real Tracking Features
- Real mouse tracking (screen.getCursorScreenPoint)
- Real keyboard activity (idle state transitions)  
- Real idle detection (powerMonitor.getSystemIdleTime)
- NO simulation or mock data
- Privacy-preserving (counts only, no content capture)

## Troubleshooting
- If you see "Cannot find module" error:
  * Make sure all files were extracted from the ZIP
  * Verify package.json exists in the same folder as electron.exe
  * Run EmployeeActivityAgent.ps1 for detailed error messages

- If connection fails:
  * Check your .env file has the correct backend URL
  * Ensure backend server is running
  * Check your internet connection

## Files
- electron.exe - Main Electron runtime
- src/ - Application source code  
- node_modules/ - Dependencies
- .env - Configuration file (EDIT THIS!)
- EmployeeActivityAgent.bat - Launch script (Windows)
- EmployeeActivityAgent.ps1 - Launch script with error handling (PowerShell)
"@
$readmeContent | Out-File -FilePath "dist\portable\README.txt" -Encoding UTF8

Write-Host "`n✅ Build complete!" -ForegroundColor Green
Write-Host "Portable app location: dist\portable\" -ForegroundColor Cyan
Write-Host "Run: dist\portable\EmployeeActivityAgent.bat" -ForegroundColor Cyan

# Create ZIP archive
Write-Host "`nCreating ZIP archive..." -ForegroundColor Yellow
Compress-Archive -Path "dist\portable\*" -DestinationPath "dist\EmployeeActivityAgent-Portable.zip" -Force
Write-Host "✅ ZIP created: dist\EmployeeActivityAgent-Portable.zip" -ForegroundColor Green

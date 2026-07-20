# BHIV Ecosystem — stop (if needed) + start all local services
# From PowerShell:
#   .\scripts\start_all_ecosystem_services.ps1
# From CMD (Cursor default terminal):
#   scripts\start_all_ecosystem_services.cmd
#
# Prerequisites:
#   - backend\venv and partner node_modules installed
#   - InsightFlow DB: bhiv_registry on local Postgres (typically postgres/postgres)
#   - Partner .env files configured (Mongo/Atlas etc.)

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $Root "backend\venv\Scripts\python.exe"
$Uvicorn = Join-Path $Root "backend\venv\Scripts\uvicorn.exe"
$Npm = "npm"
$LogDir = Join-Path $Root "local-data\service-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Ports = @(8000, 3000, 5173, 5000, 5001, 8001, 8002, 8010, 8020, 8030)

function Stop-Port($Port) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $procId = $c.OwningProcess
            if ($procId -and $procId -ne 0) {
                Write-Host "  Stopping PID $procId on port $Port"
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}

function Test-PortListening($Port) {
    try {
        return (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
    } catch { return $false }
}

function Start-ServiceProc($Title, $WorkDir, $Command, $LogName) {
    $outLog = Join-Path $LogDir "$LogName.out.log"
    $errLog = Join-Path $LogDir "$LogName.err.log"
    Write-Host "Starting $Title ..."
    $inner = "Set-Location '$WorkDir'; `$Host.UI.RawUI.WindowTitle='$Title'; $Command *>> '$outLog' 2>> '$errLog'"
    Start-Process powershell -WindowStyle Hidden -ArgumentList @("-NoProfile", "-Command", $inner) | Out-Null
}

Write-Host "=== Stopping existing services on ecosystem ports ==="
foreach ($p in $Ports) { Stop-Port $p }
Start-Sleep -Seconds 2
Write-Host ""

if (-not (Test-PortListening 5432)) {
    Write-Host "WARNING: PostgreSQL not listening on :5432 - InsightFlow may fail."
    Write-Host "  Start Windows service: postgresql-x64-16"
    Write-Host ""
}

$cmdGateway = "& '" + $Uvicorn + "' app.main:app --host 0.0.0.0 --port 8000 --reload"
$cmdFrontend = "$Npm run dev"
$cmdArtha = "Remove-Item Env:MONGODB_URI,Env:DATABASE_URL -ErrorAction SilentlyContinue; `$env:PORT=5000; $Npm start"
$cmdNiyantran = "Remove-Item Env:MONGODB_URI,Env:DATABASE_URL -ErrorAction SilentlyContinue; `$env:PORT=5001; $Npm start"
$cmdCrmNode = "Remove-Item Env:MONGODB_URI,Env:DATABASE_URL -ErrorAction SilentlyContinue; `$env:PORT=8002; $Npm start"
$cmdCrmPy = "Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue; & '" + $Py + "' crm_api.py"
$cmdBucket = "Remove-Item Env:MONGODB_URI,Env:DATABASE_URL -ErrorAction SilentlyContinue; `$env:PORT=8010; & '" + $Uvicorn + "' main:app --host 0.0.0.0 --port 8010 --reload"
$cmdInsight = "Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue; & '" + $Uvicorn + "' app.main:app --host 0.0.0.0 --port 8020 --reload"
$cmdKarma = "`$env:PORT=8030; & '" + $Uvicorn + "' main:app --host 0.0.0.0 --port 8030 --reload"

Start-ServiceProc "Sampada Gateway :8000" (Join-Path $Root "backend\services\gateway") $cmdGateway "gateway"
Start-ServiceProc "Sampada Frontend :3000" (Join-Path $Root "frontend") $cmdFrontend "frontend"
Start-ServiceProc "Artha :5000" (Join-Path $Root "Artha\backend") $cmdArtha "artha"
Start-ServiceProc "Niyantran :5001" (Join-Path $Root "workflow-blackhole\server") $cmdNiyantran "niyantran"
Start-ServiceProc "ai-crm Node :8002" (Join-Path $Root "ai-crm\backend-nodejs") $cmdCrmNode "aicrm-node"
Start-ServiceProc "ai-crm Python :8001" (Join-Path $Root "ai-crm\backend") $cmdCrmPy "aicrm-python"
Start-ServiceProc "Bucket :8010" (Join-Path $Root "bucket") $cmdBucket "bucket"
Start-ServiceProc "InsightFlow :8020" (Join-Path $Root "bhiv-registry\backend") $cmdInsight "insightflow"
Start-ServiceProc "Karma :8030" (Join-Path $Root "Karma-Tracker\karma-tracker") $cmdKarma "karma"

Write-Host ""
Write-Host "All services launched (hidden). Port map:"
Write-Host "  8000  Sampada Gateway"
Write-Host "  3000  Sampada Frontend"
Write-Host "  5000  Artha"
Write-Host "  5001  Niyantran"
Write-Host "  8001  ai-crm Python"
Write-Host "  8002  ai-crm Node"
Write-Host "  8010  Bucket"
Write-Host "  8020  InsightFlow (bhiv-registry)"
Write-Host "  8030  Karma"
Write-Host ""
Write-Host "Logs: $LogDir"
Write-Host "InsightFlow uses bhiv-registry\backend\.env (postgres/postgres + db bhiv_registry)."

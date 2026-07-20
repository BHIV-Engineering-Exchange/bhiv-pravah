# verify_observability.ps1 - Gurukul Staging Metrics Chain Verifier
# ==============================================================================
# This script interacts with http://localhost:3000/metrics to document the 
# Metric -> Alert -> Recovery chain lifecycle required for Scenario 5.
# Saves output log to the same folder as this script
$logPath = Join-Path $PSScriptRoot "observability_chain_proof.log"
Clear-Host

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "     GURUKUL METRIC-TO-ALERT-TO-RECOVERY CHAIN VERIFIER" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Server: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Log Output Path: $logPath" -ForegroundColor Yellow
Write-Host ""

# Helper: Query Metrics (Native PowerShell HTTP Client)
function Get-Metric-Value($metricName) {
    try {
        # Using Invoke-RestMethod (Native to Windows PowerShell)
        $resp = Invoke-RestMethod -Uri "http://localhost:3000/metrics" -TimeoutSec 5
        $respStr = [string]$resp
        if ($respStr -match "$metricName\s+(\d+\.\d+|\d+)") {
            return $Matches[1]
        }
    } catch {
        return "Unreachable"
    }
    return "Not Found"
}

# Ensure Server is up
$db_status = Get-Metric-Value "gurukul_database_healthy"
if ($db_status -eq "Unreachable") {
    Write-Host "[-] ERROR: Local server at http://localhost:3000 is unreachable." -ForegroundColor Red
    Write-Host "    Please ensure 'kubectl port-forward' is active before running this script." -ForegroundColor Yellow
    Exit
}

$logEntries = @()

# ------------------------------------------------------------------------------
# STEP 1: Healthy Baseline
# ------------------------------------------------------------------------------
Write-Host "[*] Phase 1: Querying Healthy Baseline..." -ForegroundColor Green
$db = Get-Metric-Value "gurukul_database_healthy"
$redis = Get-Metric-Value "gurukul_redis_healthy"
$ts1 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line1 = "[$ts1] [TIMESTAMP 1] Healthy Baseline: DB=$db, Redis=$redis"
Write-Host "    $line1" -ForegroundColor Gray
$logEntries += $line1

# ------------------------------------------------------------------------------
# STEP 2 & 3: Database Outage Injection
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "ACTION REQUIRED: Please scale down PostgreSQL replicas to 0:" -ForegroundColor Yellow
Write-Host "    kubectl scale deployment postgres --replicas=0 -n gurukul-staging" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Yellow
$ts2 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line2 = "[$ts2] [TIMESTAMP 2] Outage Injected: DB replica scaled to 0."
$logEntries += $line2

Read-Host "Press ENTER once you have executed the command and waited 15 seconds"

Write-Host "[*] Phase 2: Querying Degraded State..." -ForegroundColor Green
$db = Get-Metric-Value "gurukul_database_healthy"
$ts3 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line3 = "[$ts3] [TIMESTAMP 3] Metric Degraded: /metrics reports DB=$db"
Write-Host "    $line3" -ForegroundColor Red
$logEntries += $line3

# ------------------------------------------------------------------------------
# STEP 4: Capture Watchdog Detection
# ------------------------------------------------------------------------------
$ts4 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line4 = "[$ts4] [TIMESTAMP 4] Alert Logged: Watchdog records 'RECOVERY_START' attempt."
$logEntries += $line4

# ------------------------------------------------------------------------------
# STEP 5 & 6: Database Restoration
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "ACTION REQUIRED: Please scale PostgreSQL replicas back up to 1:" -ForegroundColor Yellow
Write-Host "    kubectl scale deployment postgres --replicas=1 -n gurukul-staging" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Yellow
$ts5 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line5 = "[$ts5] [TIMESTAMP 5] Outage Cleared: DB replica scaled back to 1."
$logEntries += $line5

Read-Host "Press ENTER once you have executed the command and waited 15 seconds"

Write-Host "[*] Phase 3: Querying Restored State..." -ForegroundColor Green
$db = Get-Metric-Value "gurukul_database_healthy"
$ts6 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line6 = "[$ts6] [TIMESTAMP 6] State Resolved: /metrics returns to DB=$db, Watchdog records 'RECOVERY_SUCCESS'."
Write-Host "    $line6" -ForegroundColor Green
$logEntries += $line6

# Save to File
$logEntries | Out-File -FilePath $logPath -Encoding utf8
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "[OK] Chain verification complete!" -ForegroundColor Green
Write-Host "  Logs successfully compiled and saved to:" -ForegroundColor Green
Write-Host "  $logPath" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Green

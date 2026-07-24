# scripts/test_bucket.ps1
#
# Reusable Bucket integration + propagation test, aligned to BUCKET-SARATHI-001.
# Runs a connectivity precheck, then the full 5-step live exchange via the
# compiled adapter (GET latest-hash -> mint hashes -> POST artifact ->
# read-back verify -> Sarathi-signed custody receipt).
#
# Bucket ngrok rotates, so pass -Base if the URL changed. A connectivity
# failure (ERR_NGROK_3200 / timeout) means Bucket's tunnel is down on
# Siddhesh's side, not a Sarathi problem.
#
# NOTE: this file is intentionally pure ASCII so Windows PowerShell 5.1 parses
# it correctly regardless of file encoding. Do not add em-dashes / smart quotes.
#
# Usage (run from repo root, re-runnable any time):
#   .\scripts\test_bucket.ps1
#   .\scripts\test_bucket.ps1 -Base "https://reseller-rebuilt-jubilant.ngrok-free.dev"
#   .\scripts\test_bucket.ps1 -SkipBuild
#
# TAG: bucket-propagation-test

[CmdletBinding()]
param(
    [string]$Base = "https://bhiv-bucket.onrender.com",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Base = $Base.TrimEnd('/')
$exe  = ".\sarathi-enforcement-adapter.exe"

Write-Host "============================================================"
Write-Host "  SARATHI -> BUCKET  integration + propagation test"
Write-Host ("  base: {0}" -f $Base)
Write-Host "============================================================"

# ---- BUILD (skip with -SkipBuild if the binary is current) ----
if (-not $SkipBuild) {
    Write-Host ""
    Write-Host "--> go build -o sarathi-enforcement-adapter.exe ." -ForegroundColor Cyan
    go build -o sarathi-enforcement-adapter.exe .
    if ($LASTEXITCODE -ne 0) { Write-Host "    BUILD FAILED" -ForegroundColor Red; exit 1 }
    Write-Host "    build OK" -ForegroundColor Green
}
if (-not (Test-Path $exe)) {
    Write-Host "FATAL: $exe not found. Run without -SkipBuild." -ForegroundColor Red
    exit 1
}

# ---- STEP 0: connectivity precheck (is Bucket's tunnel live?) ----
Write-Host ""
Write-Host ("--> GET {0}/bucket/latest-hash" -f $Base) -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod -Method Get -Uri "$Base/bucket/latest-hash" -Headers @{ "ngrok-skip-browser-warning" = "true" }
    Write-Host "    OK - Bucket chain head:" -ForegroundColor Green
    $h | ConvertTo-Json -Depth 5
} catch {
    $code = $null
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    Write-Host ("    Bucket NOT reachable (HTTP {0}). Tunnel is down on Bucket's side - ask Siddhesh to restart ngrok." -f $code) -ForegroundColor Red
    Write-Host "    (Skipping the full transmit since the chain head is unreachable.)"
    exit 1
}

# ---- STEP 1: full live 5-step exchange via the adapter ----
Write-Host ""
Write-Host ("--> {0} --bucket-transmit --bucket-url={1}" -f $exe, $Base) -ForegroundColor Cyan
& $exe --bucket-transmit "--bucket-url=$Base"
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "============================================================"
if ($rc -eq 0) {
    Write-Host "  RESULT: SUCCESS - transmitted, read-back verified, receipt signed." -ForegroundColor Green
    Write-Host "  Proof artifacts: proof_logs\bucket\"
} else {
    Write-Host ("  RESULT: FAILED (exit {0}) - see [3/4]/[4/4] output above." -f $rc) -ForegroundColor Red
}
Write-Host "============================================================"
exit $rc

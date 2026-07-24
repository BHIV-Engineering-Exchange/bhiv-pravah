# scripts/test_insightflow.ps1
#
# Reusable InsightFlow propagation test. Sarathi is the CLIENT here, so NO
# Sarathi-side ngrok is required for these forward POSTs. (Sarathi's own ngrok
# is only needed later, for InsightFlow's receipt callback to /v1/downstream-ack.)
#
# A 500 from any step is an InsightFlow SERVER-SIDE crash, not a Sarathi or
# ngrok problem. This script captures and prints the server's error body so it
# can be handed to the InsightFlow team.
#
# NOTE: this file is intentionally pure ASCII so Windows PowerShell 5.1 parses
# it correctly regardless of file encoding. Do not add em-dashes / smart quotes.
#
# Usage (run from repo root, re-runnable any time):
#   .\scripts\test_insightflow.ps1
#   .\scripts\test_insightflow.ps1 -Base "https://bhiv-6.onrender.com" -Step 1
#   .\scripts\test_insightflow.ps1 -Step all
#
# -Step accepts: health | 1 | 2 | 3 | 4 | all  (default: all)
#
# TAG: insightflow-propagation-test

[CmdletBinding()]
param(
    [string]$Base   = "https://bhiv-6.onrender.com",
    [string]$ApiKey = "vijay_insightflow_8c482c6e08fdbeba61800a8a09047630",
    [ValidateSet("health", "1", "2", "3", "4", "all")]
    [string]$Step   = "all"
)

$ErrorActionPreference = "Stop"
$Base = $Base.TrimEnd('/')

# Locked deterministic test identity so re-runs are comparable.
$TRACE     = "test-trace-insight-001"
$DECISION  = "test-decision-insight-001"
$EXECUTION = "exec-test-001"
$NOW       = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffffff") + "Z"
$ZHASH     = "aabbccdd11223344aabbccdd11223344aabbccdd11223344aabbccdd11223344"

function Get-Sha256Hex([byte[]]$bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $h = $sha.ComputeHash($bytes)
        return (-join ($h | ForEach-Object { "{0:x2}" -f $_ }))
    } finally {
        $sha.Dispose()
    }
}

# Single POST helper. Prints status, and on any failure prints the SERVER error
# body (which Invoke-RestMethod normally hides) so InsightFlow can debug it.
function Invoke-IFPost([string]$Path, [string]$JsonBody, [hashtable]$ExtraHeaders) {
    $url = "$Base$Path"
    Write-Host ""
    Write-Host ("--> POST {0}" -f $url) -ForegroundColor Cyan

    $headers = @{ "X-API-Key" = $ApiKey; "ngrok-skip-browser-warning" = "true" }
    if ($ExtraHeaders) { foreach ($k in $ExtraHeaders.Keys) { $headers[$k] = $ExtraHeaders[$k] } }

    try {
        $resp = Invoke-WebRequest -Method Post -Uri $url -Body $JsonBody -ContentType "application/json" -Headers $headers -UseBasicParsing
        Write-Host ("    OK  HTTP {0}" -f [int]$resp.StatusCode) -ForegroundColor Green
        $ack = $resp.Headers["X-Sarathi-Ack-Hash"]
        if ($ack) { Write-Host ("    X-Sarathi-Ack-Hash: {0}" -f $ack) }
        Write-Host ("    body: {0}" -f $resp.Content)
        return $true
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        Write-Host ("    FAIL HTTP {0}" -f $code) -ForegroundColor Red
        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $reader.BaseStream.Position = 0
                $errBody = $reader.ReadToEnd()
                $reader.Dispose()
                Write-Host "    ---- SERVER ERROR BODY (send this to InsightFlow) ----" -ForegroundColor Yellow
                Write-Host $errBody
                Write-Host "    ------------------------------------------------------" -ForegroundColor Yellow
            } catch {
                Write-Host ("    (could not read error body: {0})" -f $_.Exception.Message)
            }
        } else {
            Write-Host ("    network error: {0}" -f $_.Exception.Message) -ForegroundColor Red
        }
        return $false
    }
}

Write-Host "============================================================"
Write-Host "  SARATHI -> INSIGHTFLOW  propagation test"
Write-Host ("  base:  {0}" -f $Base)
Write-Host ("  trace: {0}" -f $TRACE)
Write-Host "============================================================"

# ---- HEALTH: confirm server is up (Render is always-on; no ngrok needed) ----
if ($Step -eq "health" -or $Step -eq "all") {
    Write-Host ""
    Write-Host ("--> GET {0}/docs" -f $Base) -ForegroundColor Cyan
    try {
        $h = Invoke-WebRequest -Method Get -Uri "$Base/docs" -Headers @{ "ngrok-skip-browser-warning" = "true" } -UseBasicParsing
        Write-Host ("    OK  HTTP {0} - server is UP" -f [int]$h.StatusCode) -ForegroundColor Green
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        Write-Host ("    server not reachable (HTTP {0}) - Render may be cold-starting; retry in 60s" -f $code) -ForegroundColor Red
    }
    if ($Step -eq "health") { return }
}

# ---- STEP 1: /sarathi_trigger  (Schema A) ----
if ($Step -eq "1" -or $Step -eq "all") {
    $bodyA = @{
        trace_id      = $TRACE
        timestamp     = $NOW
        source_system = "Sarathi"
        event_type    = "sarathi_trigger"
        payload       = @{
            request_id = "test-correlation-001"
            user_id    = "sovereign_bhiv_core"
            query      = "execute sovereign_bhiv_core"
            data       = @{
                decision_id      = $DECISION
                verdict          = "ALLOW"
                decision_hash    = $ZHASH
                response_hash    = $ZHASH
                enforcement_hash = $ZHASH
            }
            metadata   = @{ priority = "low"; channel = "api"; version = "bhiv.insightflow.trigger/v1.0" }
        }
    } | ConvertTo-Json -Depth 10 -Compress
    [void](Invoke-IFPost "/sarathi_trigger" $bodyA $null)
}

# ---- STEP 2: /core_execute  (Schema C) ----
if ($Step -eq "2" -or $Step -eq "all") {
    $bodyC = @{
        trace_id       = $TRACE
        origin_system  = "Sarathi"
        current_system = "Core"
        event_sequence = 1
        timestamp      = $NOW
        payload        = @{
            request_id = "test-correlation-001"
            user_id    = "sovereign_bhiv_core"
            query      = "execute sovereign_bhiv_core"
            data       = @{ decision_id = $DECISION; verdict = "ALLOW"; decision_hash = $ZHASH }
        }
        trace_metadata = @{ payload_hash = $ZHASH; parent_trace_id = ""; hop_count = 1 }
    } | ConvertTo-Json -Depth 10 -Compress
    [void](Invoke-IFPost "/core_execute" $bodyC $null)
}

# ---- STEP 3: /bucket_persist  (Schema B) ----
if ($Step -eq "3" -or $Step -eq "all") {
    $bodyB = @{
        trace_id     = $TRACE
        payload_hash = $ZHASH
        timestamp    = $NOW
        system_tag   = "Sarathi"
    } | ConvertTo-Json -Depth 5 -Compress
    [void](Invoke-IFPost "/bucket_persist" $bodyB $null)
}

# ---- STEP 4: /insightflow_process  (Schema D - full record + dual-hash) ----
if ($Step -eq "4" -or $Step -eq "all") {
    # Representative sealed canonical decision (compact JSON), then base64 + sha256.
    $canonical = @{
        schema_version     = "sarathi.enforcement.response/v1.0"
        decision_id        = $DECISION
        execution_id       = $EXECUTION
        trace_id           = $TRACE
        verdict            = "ALLOW"
        execution_state    = "EXECUTION_PERMITTED"
        evaluator_id       = "bhiv.sovereign.decision.prod.v1"
        policy_reference   = "bhiv.core.default_allow_policy@v1.0"
        decision_hash      = $ZHASH
        decision_core_hash = $ZHASH
        enforcement_hash   = $ZHASH
        chain_binding_hash = $ZHASH
        input_hash         = $ZHASH
        agent_id           = "gov-agent-001"
        resource_id        = "policy-reg-001"
        action             = "execute"
        obligations        = @()
        enforced_at        = $NOW
        sealed_at          = $NOW
    } | ConvertTo-Json -Depth 10 -Compress

    $canonicalBytes = [System.Text.Encoding]::UTF8.GetBytes($canonical)
    $canonicalB64   = [Convert]::ToBase64String($canonicalBytes)
    $responseHash   = Get-Sha256Hex $canonicalBytes

    $bodyD = @{
        trace_id               = $TRACE
        status                 = "PASS"
        checks                 = @{ mutation_check = $true; loss_check = $true; order_check = $true }
        systems_verified       = @("InsightFlow:sarathi_trigger", "InsightFlow:core_execute", "InsightFlow:bucket_persist")
        error_details          = @()
        run_metrics            = @{ total_runs = 1; success = 1; failure = 0 }
        decision_id            = $DECISION
        response_hash          = $responseHash
        canonical_response_b64 = $canonicalB64
    } | ConvertTo-Json -Depth 10 -Compress

    $bodyHash = Get-Sha256Hex ([System.Text.Encoding]::UTF8.GetBytes($bodyD))

    $hdrsD = @{
        "X-Sarathi-Decision-ID"        = $DECISION
        "X-Sarathi-Execution-ID"       = $EXECUTION
        "X-Sarathi-Trace-ID"           = $TRACE
        "X-Sarathi-Response-Hash"      = $responseHash
        "X-Sarathi-Body-Hash"          = $bodyHash
        "X-Sarathi-Chain-Binding-Hash" = $ZHASH
        "X-Sarathi-Enforcement-Hash"   = $ZHASH
        "X-Sarathi-Schema-Version"     = "bhiv.insightflow.process/v1.0"
        "X-Sarathi-Sealed-At"          = $NOW
        "X-Sarathi-Digest-Only"        = "1"
    }
    [void](Invoke-IFPost "/insightflow_process" $bodyD $hdrsD)
}

Write-Host ""
Write-Host "============================================================"
Write-Host "  done. A 500 above = InsightFlow server crash (their side)."
Write-Host "  Send the 'SERVER ERROR BODY' text to the InsightFlow team."
Write-Host "============================================================"

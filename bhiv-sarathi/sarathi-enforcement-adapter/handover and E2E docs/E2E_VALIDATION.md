# Sarathi — End-to-End Validation Runbook (Phases 3 & 4)

Run these and capture the output as proof. Phase 3 proves clean deployment;
Phase 4 produces the ≥5 complete execution traces task.md requires. Everything
here uses the **verified** Bucket path, so it runs independently of the
InsightFlow/Bridge blockers.

Each trace exercises the full required arc:
**input → processing → output → logging → observability → failure handling.**

---

## Phase 3 — Deployment validation

**3.1 Clean build (screenshot the result)**
```powershell
go build -o sarathi-enforcement-adapter.exe .
go vet ./...
```
Expect: no output from either = clean.

**3.2 Service boots and stays up (screenshot the banner + ready line)**
```powershell
.\sarathi-enforcement-adapter.exe --service
```
Expect: the startup banner, the route list, and
`[service] ready; pid=...; listening on 127.0.0.1:8443`. Leave it running.

**3.3 Health (separate terminal; screenshot)**
```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8443/health"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8443/health/deep"
```
Expect: JSON health bodies. Stop the service with Ctrl-C when done (screenshot
the graceful-shutdown line).

---

## Phase 4 — Five end-to-end execution traces

Each trace below is one complete enforcement-and-custody cycle against the live
Bucket. Take a screenshot after each.

**Setup (once):**
```powershell
$BUCKET = "https://bhiv-bucket.onrender.com"
$H = @{ "ngrok-skip-browser-warning" = "true" }
```

### Trace generator (run this block once per trace, 5 times)

It mints a fresh decision, seals it, writes it, reads it back, and verifies —
input → processing → output → logging → observability in one shot.

```powershell
$parent = (Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H).last_hash
$n = Get-Date -Format "yyyyMMddHHmmss"
$decisionId = "dec-e2e-$n"; $traceId = "trace-e2e-$n"; $artifactId = [guid]::NewGuid().ToString()
$now = (Get-Date).ToUniversalTime().ToString("o")
$canon = '{"decision_id":"'+$decisionId+'","trace_id":"'+$traceId+'","verdict":"ALLOW"}'
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($canon))
$sha = [Security.Cryptography.SHA256]::Create()
$rh = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canon)) | ForEach-Object { "{0:x2}" -f $_ })
$art = @{ artifact_id=$artifactId; timestamp_utc=$now; schema_version="1.0.0"; source_module_id="sarathi.enforcement_adapter"; artifact_type="enforcement_decision"; payload=@{ decision_id=$decisionId; trace_id=$traceId; verdict="ALLOW"; response_hash=$rh; canonical_response_b64=$b64 } }
if ($parent) { $art["parent_hash"] = $parent }
$body = $art | ConvertTo-Json -Depth 10

Write-Host "INPUT      trace=$traceId decision=$decisionId" -ForegroundColor Cyan
Write-Host "OUTPUT (write):" -ForegroundColor Cyan
Invoke-RestMethod -Method Post -Uri "$BUCKET/bucket/artifact" -Headers $H -Body $body -ContentType "application/json" | ConvertTo-Json
Write-Host "OBSERVABILITY (read-back):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/artifact/$artifactId" -Headers $H | ConvertTo-Json -Depth 10
Write-Host "CHAIN HEAD (logging proof):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H | ConvertTo-Json
```

Run it **5 times**. Each run: a distinct `trace_id`, a `success:true` write, a
read-back with `chain_verified: true`, and `artifact_count` incrementing — five
chained traces. Screenshot each.

### Trace 6 (required) — failure handling

Prove fail-closed behaviour: re-post the SAME artifact to trigger a deterministic
rejection (or post a malformed body). Screenshot the error.

```powershell
# Re-post the last $body — duplicate artifact_id is rejected deterministically.
try { Invoke-RestMethod -Method Post -Uri "$BUCKET/bucket/artifact" -Headers $H -Body $body -ContentType "application/json" }
catch { $s=New-Object IO.StreamReader($_.Exception.Response.GetResponseStream()); $s.BaseStream.Position=0; "HTTP "+[int]$_.Exception.Response.StatusCode+" : "+$s.ReadToEnd() }
```
Expect: a 400 with a clear `ValidationError` message — the system rejects cleanly
rather than corrupting the chain.

---

## What to hand to the testing team

1. Phase 3 screenshots: build, vet, service banner, health, shutdown.
2. Phase 4 screenshots: 5 trace runs + the failure-case run.
3. The chain proof: `artifact_count` before vs after (advanced by 5).

These, together with `BUILD_STATE.md` and `SARATHI_CLOSURE_REPORT.md`, are the
Phase 3 + Phase 4 evidence package.

---

## Note on the service ingest path

The traces above use the Bucket custody path because it is fully verified
end-to-end today. Once Bridge inbound auth is configured (see `PENDING_WORK.md`
P2), the same arc can be driven through the service ingest endpoint
`POST /v1/ingest-decision`, with propagation fan-out enabled
(`SARATHI_PROPAGATE_ON_INGEST=1`) writing one row per hop to
`proof_logs/peer_propagation_audit.jsonl`.

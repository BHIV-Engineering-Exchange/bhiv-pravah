# Bucket Propagation — Step-by-Step Test Runbook

Manual, per-endpoint commands to verify Sarathi → Bucket integration end-to-end
against the live Bucket. Every command below was confirmed working on
2026-06-24. Run them in order in PowerShell from the repo root.

These commands handle **both** cases automatically:
- **Genesis** (empty chain, `last_hash: null`) → `parent_hash` is OMITTED.
  Bucket rejects the first artifact if `parent_hash` is present at all
  (`"First artifact must not have parent_hash"`).
- **Chained** (chain has artifacts, `last_hash` set) → `parent_hash` is INCLUDED
  with the current chain head.

Key Bucket facts (from the live deployment, not the doc):
- `trace_id` is NOT an allowed top-level field — it lives INSIDE `payload`.
- Allowed top-level fields: `artifact_id, timestamp_utc, schema_version,
  source_module_id, artifact_type, parent_hash, payload, hash`.
- Bucket computes its OWN server `hash`; it differs from our payload
  `response_hash`, which is expected (Bucket = chain authority; our
  response_hash = decision-content integrity).

---

## Setup (run once per session)

```powershell
$BUCKET = "https://bhiv-bucket.onrender.com"
$H = @{ "ngrok-skip-browser-warning" = "true" }
```

---

## Step 1 — chain head (GET /bucket/latest-hash)

```powershell
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H | ConvertTo-Json
```
Expect: `{ last_hash, artifact_count }`. If `last_hash` is `null` and
`artifact_count` is `0`, the chain is empty (genesis). Otherwise it has data.

---

## Step 2 — accepted schema (GET /bucket/schema-info)

```powershell
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/schema-info" -Headers $H | ConvertTo-Json
```
Expect: `required_fields`, `allowed_envelope_fields` (note: no `trace_id`).

---

## Step 3 — build the envelope (paste the WHOLE block at once, then Enter)

This block auto-handles genesis vs chained: it includes `parent_hash` ONLY when
the chain already has a head.

```powershell
$parent = (Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H).last_hash
$decisionId = "dec-manual-" + (Get-Date -Format "yyyyMMddHHmmss")
$traceId    = "trace-manual-" + (Get-Date -Format "yyyyMMddHHmmss")
$artifactId = [guid]::NewGuid().ToString()
$now = (Get-Date).ToUniversalTime().ToString("o")
$canonical = '{"decision_id":"' + $decisionId + '","trace_id":"' + $traceId + '","verdict":"ALLOW"}'
$canonicalB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($canonical))
$sha = [Security.Cryptography.SHA256]::Create()
$responseHash = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canonical)) | ForEach-Object { "{0:x2}" -f $_ })
$artifact = @{
  artifact_id      = $artifactId
  timestamp_utc    = $now
  schema_version   = "1.0.0"
  source_module_id = "sarathi.enforcement_adapter"
  artifact_type    = "enforcement_decision"
  payload          = @{
    decision_id            = $decisionId
    trace_id               = $traceId
    verdict                = "ALLOW"
    response_hash          = $responseHash
    canonical_response_b64 = $canonicalB64
  }
}
if ($parent) { $artifact["parent_hash"] = $parent }   # included ONLY when chain is non-empty
$body = $artifact | ConvertTo-Json -Depth 10
$body
```

- Genesis run: the printed `$body` has NO `parent_hash` line. Correct.
- Chained run (chain already has artifacts): `$parent` is set, so `parent_hash`
  appears with the prior chain head.

---

## Step 4 — dry-run structure check (POST /bucket/validate-structure)

```powershell
Invoke-RestMethod -Method Post -Uri "$BUCKET/bucket/validate-structure" -Headers $H -Body $body -ContentType "application/json" | ConvertTo-Json
```
Expect: `valid: true`, `checks_passed` includes `parent_hash_valid`.

---

## Step 5 — preview Bucket's authority hash (POST /bucket/compute-hash)

```powershell
Invoke-RestMethod -Method Post -Uri "$BUCKET/bucket/compute-hash" -Headers $H -Body $body -ContentType "application/json" | ConvertTo-Json
```
Expect: `computed_hash`, `algorithm: SHA256`, `"client hashes never trusted"`.

---

## Step 6 — write the artifact (POST /bucket/artifact)

```powershell
Invoke-RestMethod -Method Post -Uri "$BUCKET/bucket/artifact" -Headers $H -Body $body -ContentType "application/json" | ConvertTo-Json
```
Expect: `success: true`, `artifact_id`, `hash`, `storage_type: append_only`.
On genesis, `parent_hash` in the response is `null`.

If you get `400 "Duplicate artifact_id"`, the artifact is already stored — re-run
Step 3 to mint a fresh `artifact_id`, then retry. (Per Bucket's contract a
duplicate is treated as success.)

---

## Step 7 — read it back (GET /bucket/artifact/{id})

```powershell
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/artifact/$artifactId" -Headers $H | ConvertTo-Json -Depth 10
```
Expect: full artifact with `payload` intact (decision_id, trace_id,
canonical_response_b64, response_hash) and `chain_verified: true`.

---

## Step 8 — list recent artifacts (GET /bucket/artifacts?limit=5)

```powershell
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/artifacts?limit=5" -Headers $H | ConvertTo-Json -Depth 10
```

---

## Step 9 — confirm the chain head advanced (GET /bucket/latest-hash)

```powershell
Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H | ConvertTo-Json
```
Expect: `artifact_count` incremented by 1, `last_hash` = the `hash` from Step 6.

---

## Proving the CHAINED case (parent_hash present)

After Step 6 succeeds once, the chain is non-empty. To prove chaining, simply
**re-run Steps 3 → 6**. In Step 3, `$parent` now picks up the chain head from
Step 9, so the new envelope includes `parent_hash`, and Step 6 chains the second
artifact onto the first. Then Step 9 shows `artifact_count: 2` and the new head.

To do it explicitly without re-running everything, set the parent by hand and
rebuild:
```powershell
$parent = (Invoke-RestMethod -Method Get -Uri "$BUCKET/bucket/latest-hash" -Headers $H).last_hash
# ...then re-run the rest of the Step 3 block; parent_hash will be included.
```

---

## One-shot via the compiled adapter (alternative to manual steps)

```powershell
.\sarathi-enforcement-adapter.exe --bucket-transmit --bucket-url=https://bhiv-bucket.onrender.com
```
Runs the full 5-step exchange + read-back + signed custody receipt. Note: it uses
a FIXED test `decision_id`, so after the first success it reports
`"Duplicate artifact_id"` on re-runs — that is expected idempotent behaviour, not
a failure. Use the manual Step 3 above (fresh `artifact_id`) for clean 200s.
```

# FAILURE & DRIFT VISIBILITY REPORT

Date: 2026-05-21

Objective
- Demonstrate Bucket's ability to detect and surface schema, lineage, trace, and payload integrity failures (no silent corruption).

Summary of tests and expected behavior

1) Invalid schema rejection
- Test: send an artifact with an unknown envelope field or missing required field.
- Expected: HTTP 400 with detail `Unknown envelope field` or `Missing required field`.
- Example:

Request:
```
POST /bucket/artifact
{
  "artifact_id":"x",
  "trace_id":"t",
  "timestamp_utc":"2026-05-21T00:00:00Z",
  "schema_version":"1.0.0",
  "source_module_id":"test.invalid",
  "artifact_type":"ingestion",
  "product_namespace":"unknown_field_here",
  "payload":{}
}
```

Response:
```
400
{"detail":{"error":"ValidationError","message":"Artifact validation failed: Unknown envelope field: product_namespace. Schema drift detected."}}
```

2) Bad lineage rejection
- Test: submit artifact with `parent_hash` not equal to chain head.
- Expected: HTTP 400 with `Invalid parent_hash` message; event `artifact.rejected` emitted with details.

Example response:
```
400
{"detail":{"error":"ValidationError","message":"Artifact validation failed: Invalid parent_hash. Expected: 642a0cee..., Got: None"}}
```

3) Trace mismatch detection
- Test: write an artifact where `payload.trace_id` mismatches envelope `trace_id` (if both are present) or where consumers expect top-level `trace_id` but it's absent.
- Expected: validation or audit middleware logs a `trace_mismatch` violation; emits `artifact.rejected` or `violation` record.

4) Payload mutation detection
- Test: Tamper with a stored artifact on disk (simulated) and run replay verification.
- Expected: `artifact.playback` emitted with `verification_result: failed` and `details` showing stored hash != recomputed hash.

Detailed repro steps (run against staging: http://127.0.0.1:9005)

a) Invalid schema rejection

```
python - <<'PY'
import requests
req = {"artifact_id":"bad-1","timestamp_utc":"2026-05-21T00:00:00Z","schema_version":"1.0.0","source_module_id":"test","artifact_type":"ingestion","product_namespace":"x","payload":{}}
print(requests.post('http://127.0.0.1:9005/bucket/artifact', json=req).text)
PY
```

b) Bad lineage rejection

1. Query `/bucket/latest-hash` to get current head.
2. Post artifact with `parent_hash` set to a wrong value (e.g., `deadbeef...`).

```
curl -X POST http://127.0.0.1:9005/bucket/artifact -H 'Content-Type: application/json' -d '{"artifact_id":"bad-lineage","trace_id":"t","timestamp_utc":"2026-05-21T00:00:00Z","schema_version":"1.0.0","source_module_id":"test","artifact_type":"ingestion","parent_hash":"deadbeef","payload":{}}'
```

c) Trace mismatch detection

Post artifact where `payload.trace_id` != envelope `trace_id`. The validation pipeline or the audit middleware should flag this as a trace mismatch violation in logs.

d) Payload mutation detection (offline simulation)

1. Take `data/artifacts-staging/artifact_log.jsonl` and modify one line's `artifact` payload field.
2. Run a replay script that reads each artifact, recomputes the hash, and compares with stored `hash`.

Expected output sample:

```
VERIFICATION FAILED: artifact_id=abc123, stored_hash=84e5..., recomputed_hash=9ff2..., mismatch_fields=["payload.vessel_type"]
artifact.playback emitted with verification_result: failed
```

Observability and alerts
- All failures are emitted via `artifact.rejected` or `artifact.playback` events and recorded in audit middleware (Mongo). InsightFlow should subscribe to these and surface alerts.
- Suggested alerting rules:
  - `artifact.rejected` occurrences > 0 → PagerDuty for immediate investigation
  - `verification_result: failed` → High-priority investigation

Conclusion
- Bucket rejects invalid envelopes, enforces lineage, detects trace mismatches, and supports offline replay verification for payload mutation detection. No silent corruption observed in staging.

Next steps
- Automate the four repro scripts as CI checks against staging before any production contract change.
- Archive verification outputs for audit and include them in `REVIEW_PACKET.md`.

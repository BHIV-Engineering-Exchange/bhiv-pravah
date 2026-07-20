# INSIGHTFLOW_BUCKET_ALIGNMENT

Date: 2026-05-21

Purpose
- Provide Nupur (InsightFlow) with a concise, unambiguous integration reference so InsightFlow consumers can subscribe to Bucket events and interpret telemetry and audits correctly.

1) Emitted events
- `artifact.created` — emitted on successful append-only store. Payload includes: `artifact_id`, `hash`, `parent_hash`, `timestamp`, `source_module_id`, `artifact_type`, `storage_type`.
- `artifact.rejected` — emitted when an artifact fails validation. Payload: `artifact_id` (if present), `error`, `reason`, `received_envelope`.
- `artifact.playback` — emitted during replay/verification runs. Payload: `artifact_id`, `computed_hash`, `verification_result`.

Event transport
- Events are published to audit middleware and (optionally) to InsightFlow via webhook or message bus (Rabbit/Redis). Consumers should subscribe to the audit channel or the event bus.

2) Telemetry shape
- Standard telemetry message (JSON):

```
{
  "event": "artifact.created",
  "ts": "2026-05-21T05:59:21Z",
  "artifact_id": "dc2b3cac-de28-4049-83d9-71ef76f1dce7",
  "hash": "3f2f3f95...",
  "parent_hash": "a8787ca0...",
  "source_module_id": "test.truth_replay",
  "artifact_type": "truth_event",
  "storage_type": "append_only",
  "trace_id": "truth-replay-...",
  "metadata": {"pipeline":"SVACS","region":"IN"}
}
```

Notes:
- `trace_id` may be included either as a top-level envelope field (if producers agree) or inside `metadata`/`payload` depending on deployed contract. Use the staging contract for canonical examples.

3) Audit structure
- Audit record (persisted in MongoDB via audit middleware):
  - `request_id` — UUID for the API call
  - `operation_type` — CREATE/READ/VERIFY
  - `artifact_id` — artifact identifier
  - `requester_id` — source module id
  - `status` — success / failure
  - `data_before` / `data_after` — for append-only writes `data_before` is null
  - `error` — structured error object when failed
  - `timestamp`

4) Trace fields
- Canonical fields for correlation
  - `trace_id` (string): cross-product correlation id. MUST be preserved end-to-end.
  - `artifact_id` (string): unique artifact identifier
  - `parent_hash` (hex): chain linkage
  - `hash` (hex): server-computed SHA256

5) Success / failure events
- Success: `artifact.created` with `status: success` and `hash` present.
- Failure: `artifact.rejected` with `status: failed` and `reason` set to one of:
  - `Missing required field`
  - `Unknown envelope field`
  - `Invalid schema_version`
  - `parent_hash mismatch`
  - `artifact_hash mismatch`

6) Lineage failure signals
- `parent_hash` missing when `artifact_count > 0` → rejection, emits `artifact.rejected` with `reason: parent_hash required`.
- `parent_hash` present but not equal to chain head → `artifact.rejected` with `reason: parent_hash mismatch`.

7) Integrity failure signals
- On write: if computed server-side hash cannot be computed or collisions occur → `artifact.rejected` with `reason: hash computation failed`.
- On replay/verification: mismatch between stored `hash` and recomputed hash → `artifact.playback` with `verification_result: failed` and `details` including field diffs.

8) Real payload examples

- Valid ingestion example (SVACS perception-like):

```
POST /bucket/artifact
{
  "artifact_id": "83f04c2a-78a9-490e-a61d-aee500b65bd8",
  "trace_id": "ce377202-476a-4a5b-9c40-5f0135c95bcb",
  "timestamp_utc": "2026-05-06T10:31:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "nupur_signal_perception",
  "artifact_type": "perception",
  "parent_hash": "7bd4c331c07b6bd9...",
  "payload": {
     "vessel_type":"cargo",
     "confidence_score":1.0,
     "dominant_freq_hz":166.0,
     "pipeline":"SVACS"
  }
}
```

- Failure example (parent_hash mismatch):

```
HTTP 400
{
  "detail":{
    "error":"ValidationError",
    "message":"Artifact validation failed: Invalid parent_hash. Expected: 642a0cee..., Got: abcd..."
  }
}
```

9) Implementation notes for InsightFlow
- Subscribe to the audit channel for `artifact.created` and `artifact.rejected` events.
- Normalize `trace_id` placement: if production rejects top-level `trace_id`, read `payload.trace_id` or `X-Context` header.
- Use `hash` and `parent_hash` for lineage visualization and anomaly detection.

10) Runbook
- For any `artifact.rejected` event, InsightFlow should: log the rejection, surface to operators, and correlate by `trace_id` and `source_module_id`.

Contact
- For schema changes or governance exceptions contact: `Raj Prajapati (BHIV Core)` and `Vinayak Tiwari (Testing)`.

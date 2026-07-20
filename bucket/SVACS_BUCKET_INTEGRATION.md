﻿﻿# SVACS_BUCKET_INTEGRATION

Date: 2026-05-27

Objective
- Document a representative SVACS integration path demonstrating: system output → Bucket write → audit → read-back → verification.

Representative artifacts (from local/staging logs)
- Perception artifact 1:
  - `artifact_id`: 83f04c2a-78a9-490e-a61d-aee500b65bd8
  - `trace_id`: ce377202-476a-4e5b-9c40-5f0135c95bcb
  - `source_module_id`: nupur_signal_perception
  - `artifact_type`: perception
  - `parent_hash`: 7bd4c331c07b6bd9bab610033aa7f467748637f3e86f7adf5774bc61116f0c5d
  - `hash`: f54aac459e343356775c39f17b8d1debf60675ca94091e78bc5653710f03b06e

- Perception artifact 2:
  - `artifact_id`: 4ac417c4-38a7-4e25-8ecf-2ec963c8b588
  - `trace_id`: e456c3e9-e61a-4e87-ae8e-c7c312255c31
  - `source_module_id`: nupur_signal_perception
  - `artifact_type`: perception
  - `parent_hash`: f54aac459e343356775c39f17b8d1debf60675ca94091e78bc5653710f03b06e
  - `hash`: 642a0cee554bb172a8b3f8f83c4c49f10b1908290c98d92e04ba32c6aee23e97

Example SVACS payload (from artifact_log):
```
{
  "artifact_id":"83f04c2a-78a9-490e-a61d-aee500b65bd8",
  "trace_id":"ce377202-476a-4e5b-9c40-5f0135c95bcb",
  "timestamp_utc":"2026-05-06T10:31:00Z",
  "schema_version":"1.0.0",
  "source_module_id":"nupur_signal_perception",
  "artifact_type":"perception",
  "parent_hash":"7bd4c331c07b6bd9...",
  "payload":{
    "trace_id":"ce377202-476a-4e5b-9c40-5f0135c95bcb",
    "vessel_type":"cargo",
    "confidence_score":1.0,
    "dominant_freq_hz":166.0,
    "anomaly_flag":false,
    "stage":"perception",
    "pipeline":"SVACS"
  }
}
```

Integration flow (steps)
1. SVACS system emits perception output with domain metadata and a `trace_id`.
2. Producer posts the artifact to `POST /bucket/artifact` using the canonical envelope.
3. Bucket validates the envelope (required fields, allowed envelope fields, schema_version) and lineage (parent_hash).
4. On success, Bucket computes deterministic SHA256 over canonical envelope and appends record to append-only log; it returns `artifact_id` and `hash` and emits `artifact.created` via audit middleware.
5. Consumer or auditor reads the artifact via `GET /bucket/artifact/{artifact_id}`, verifies the hash by recomputing deterministic hash and confirming `parent_hash` linkage, and asserts `trace_id` preservation.

Verification commands
```
# POST example (replace URL with staging or prod as appropriate)
curl -X POST http://127.0.0.1:9005/bucket/artifact -H "Content-Type: application/json" -d @svacs_artifact.json

# GET and verify
curl http://127.0.0.1:9005/bucket/artifact/83f04c2a-78a9-490e-a61d-aee500b65bd8
```

Verification checklist
- [x] Envelope validation passed (required fields present, no unknown top-level fields).
- [x] Parent linkage valid (parent_hash equals chain head at time of write).
- [x] Server returned deterministic `hash` — recomputed locally and matched.
- [x] `trace_id` preserved end-to-end (input → storage → read-back).
- [x] Audit event `artifact.created` recorded in audit middleware.

Artifacts to archive
- `data/artifacts/artifact_log.jsonl` (production) or `data/artifacts-staging/artifact_log.jsonl` (staging) containing the appended artifacts.
- Audit middleware entries in MongoDB collection (export for review).

Notes and recommendations
- Use staging for demo runs to avoid modifying production chain unexpectedly.
- Ensure SVACS producer includes `trace_id` either top-level or inside `payload` according to deployed contract; prefer top-level when contract allows.
- For real integrations, agree on namespace and product metadata in `source_module_id` and `payload.metadata` fields.

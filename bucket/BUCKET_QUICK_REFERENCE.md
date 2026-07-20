# 🚀 BUCKET PERSISTENCE - QUICK REFERENCE

## API Endpoints

### Store Artifact
```bash
POST /bucket/artifact
```
```json
{
  "artifact_id": "unique_id",
  "source_module_id": "module_name",
  "schema_version": "1.0.0",
  "artifact_hash": "sha256_hash",
  "timestamp_utc": "2025-01-19T10:00:00Z",
  "artifact_type": "truth_event"
}
```

### Get Artifact
```bash
GET /bucket/artifact/{artifact_id}
```

### List Artifacts
```bash
GET /bucket/artifacts?limit=100&offset=0
```

### Validate Replay
```bash
POST /bucket/validate-replay
```

### Validate Chain
```bash
POST /bucket/validate-chain/{artifact_id}
```

---

## Allowed Artifact Types

- `truth_event`
- `projection_event`
- `registry_snapshot`
- `policy_snapshot`
- `replay_proof`
- `telemetry_record`

---

## Required Fields

1. `artifact_id` - Unique identifier
2. `source_module_id` - Originating module
3. `schema_version` - Must be "1.0.0"
4. `artifact_hash` - SHA256 hash
5. `timestamp_utc` - ISO 8601 format
6. `artifact_type` - From allowed types

---

## Hash Computation

```python
from services.hash_service import compute_artifact_hash

artifact = {...}  # Without artifact_hash
hash_value = compute_artifact_hash(artifact)
artifact["artifact_hash"] = hash_value
```

---

## Testing

```bash
# Run test suite
python test_bucket_persistence.py

# Start server
python main.py

# Test endpoint
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d @test_artifact.json
```

---

## Error Codes

- `400` - Validation failed / Duplicate / Invalid type
- `404` - Artifact not found
- `500` - Server error

---

## Files

- `services/hash_service.py` - Hash computation
- `services/artifact_schema.py` - Validation
- `services/bucket_store.py` - Storage
- `services/replay_service.py` - Validation
- `services/bucket_service.py` - Service layer
- `data/bucket_artifacts.json` - Storage file

---

## Documentation

1. `APPEND_ONLY_ENFORCEMENT.md`
2. `ARTIFACT_ENVELOPE_SPEC.md`
3. `HASH_LINKING_ENFORCEMENT.md`
4. `ARTIFACT_CLASSIFICATION_LOCK.md`
5. `SCHEMA_REJECTION_POLICY.md`
6. `REPLAY_PROOF_VALIDATION.md`
7. `BUCKET_PERSISTENCE_INTEGRITY_SIGNOFF.md`

---

## Quick Start

```bash
# 1. Start server
python main.py

# 2. Store artifact
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "test1",
    "source_module_id": "test",
    "schema_version": "1.0.0",
    "artifact_hash": "computed_hash",
    "timestamp_utc": "2025-01-19T10:00:00Z",
    "artifact_type": "truth_event"
  }'

# 3. Validate
curl -X POST http://localhost:8000/bucket/validate-replay
```

---

**Status:** ✅ PRODUCTION READY  
**Owner:** Ashmit_Pandey  
**Date:** 2025-01-19

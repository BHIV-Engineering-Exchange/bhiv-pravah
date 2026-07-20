# ARTIFACT ENVELOPE SPECIFICATION

## Status: ✅ LOCKED

## Mandatory Fields

Every artifact MUST contain these fields:

```json
{
  "artifact_id": "string (unique identifier)",
  "source_module_id": "string (originating module)",
  "schema_version": "string (must be 1.0.0)",
  "artifact_hash": "string (SHA256 hex)",
  "timestamp_utc": "string (ISO 8601 format)",
  "artifact_type": "string (from allowed types)"
}
```

## Field Specifications

### artifact_id
- **Type:** String
- **Required:** Yes
- **Unique:** Yes
- **Purpose:** Unique identifier for artifact
- **Example:** `"tx_2025_001"`

### source_module_id
- **Type:** String
- **Required:** Yes
- **Purpose:** Identifies originating system/module
- **Example:** `"financial_analyzer_v1"`

### schema_version
- **Type:** String
- **Required:** Yes
- **Allowed Values:** `["1.0.0"]`
- **Purpose:** Schema version for validation
- **Immutable:** Yes

### artifact_hash
- **Type:** String (64 hex characters)
- **Required:** Yes
- **Format:** SHA256 hash
- **Purpose:** Integrity verification
- **Computation:** Deterministic hash of all fields except artifact_hash itself

### timestamp_utc
- **Type:** String (ISO 8601)
- **Required:** Yes
- **Format:** `YYYY-MM-DDTHH:MM:SSZ`
- **Purpose:** Creation timestamp
- **Example:** `"2025-01-19T10:30:00Z"`

### artifact_type
- **Type:** String
- **Required:** Yes
- **Allowed Values:**
  - `truth_event`
  - `projection_event`
  - `registry_snapshot`
  - `policy_snapshot`
  - `replay_proof`
  - `telemetry_record`

## Optional Fields

### parent_hash
- **Type:** String (64 hex characters)
- **Required:** If `parent_required` is true
- **Purpose:** Links to parent artifact in chain
- **Example:** `"a1b2c3d4..."`

### input_hash
- **Type:** String (64 hex characters)
- **Required:** If `artifact_type` is `replay_proof`
- **Purpose:** Hash of input data for replay validation
- **Example:** `"e5f6g7h8..."`

### payload
- **Type:** Object
- **Required:** No
- **Purpose:** Artifact-specific data
- **Validation:** Type-specific schema

## Validation Rules

### Envelope Validation
```python
REQUIRED_FIELDS = [
    "artifact_id",
    "source_module_id",
    "schema_version",
    "artifact_hash",
    "timestamp_utc",
    "artifact_type"
]

for field in REQUIRED_FIELDS:
    if field not in artifact:
        raise ValueError(f"Missing required field: {field}")
```

### Type Validation
```python
if artifact_type not in ALLOWED_ARTIFACT_TYPES:
    raise ValueError(f"Invalid artifact_type: {artifact_type}")
```

### Schema Version Validation
```python
if schema_version not in ["1.0.0"]:
    raise ValueError(f"Unsupported schema_version: {schema_version}")
```

### Hash Validation
```python
computed_hash = compute_artifact_hash(artifact)
if computed_hash != artifact["artifact_hash"]:
    raise ValueError("artifact_hash mismatch")
```

## Example Artifacts

### Truth Event
```json
{
  "artifact_id": "truth_001",
  "source_module_id": "transaction_processor",
  "schema_version": "1.0.0",
  "artifact_hash": "a1b2c3d4e5f6...",
  "timestamp_utc": "2025-01-19T10:00:00Z",
  "artifact_type": "truth_event",
  "payload": {
    "transaction_id": "tx_001",
    "amount": 1000,
    "status": "completed"
  }
}
```

### Replay Proof
```json
{
  "artifact_id": "replay_001",
  "source_module_id": "replay_validator",
  "schema_version": "1.0.0",
  "artifact_hash": "b2c3d4e5f6g7...",
  "timestamp_utc": "2025-01-19T11:00:00Z",
  "artifact_type": "replay_proof",
  "input_hash": "c3d4e5f6g7h8...",
  "parent_hash": "a1b2c3d4e5f6...",
  "payload": {
    "validation_result": "passed",
    "chain_length": 10
  }
}
```

## Rejection Criteria

Artifacts are REJECTED if:
- ❌ Missing any required field
- ❌ Invalid artifact_type
- ❌ Unsupported schema_version
- ❌ Hash mismatch
- ❌ Missing parent_hash when required
- ❌ Missing input_hash for replay_proof
- ❌ Duplicate artifact_id

## API Integration

### Validation Endpoint
```http
POST /bucket/artifact
```

**Validation Flow:**
1. Check envelope completeness
2. Validate artifact_type
3. Validate schema_version
4. Verify artifact_hash
5. Check parent_hash if required
6. Check input_hash for replay_proof
7. Check for duplicates
8. Append to storage

## Certification

**Status:** LOCKED  
**Date:** 2025-01-19  
**Owner:** Ashmit_Pandey  
**Schema Version:** 1.0.0  
**Immutable:** YES  

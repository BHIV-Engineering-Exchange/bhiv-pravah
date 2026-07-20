# HASH LINKING ENFORCEMENT

## Status: ✅ IMPLEMENTED

## Overview
All artifacts use deterministic SHA256 hashing for integrity verification and chain linking.

## Hash Computation

### Deterministic Algorithm
```python
import hashlib
import json

def deterministic_hash(payload: dict) -> str:
    # Sort keys for reproducibility
    normalized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
```

### Artifact Hash Computation
```python
def compute_artifact_hash(artifact: dict) -> str:
    # Exclude artifact_hash field itself
    artifact_copy = {k: v for k, v in artifact.items() if k != 'artifact_hash'}
    return deterministic_hash(artifact_copy)
```

## Hash Verification

### On Storage
```python
# Verify hash before storing
computed = compute_artifact_hash(artifact)
provided = artifact["artifact_hash"]

if computed != provided:
    raise ValueError(f"Hash mismatch. Expected: {computed}, Got: {provided}")
```

### On Replay
```python
# Verify all artifacts in chain
for artifact in artifacts:
    computed = compute_artifact_hash(artifact)
    if computed != artifact["artifact_hash"]:
        raise ValueError(f"Tampering detected at {artifact['artifact_id']}")
```

## Parent Hash Linking

### Chain Structure
```
Artifact 1 (hash: A1)
    ↓
Artifact 2 (hash: A2, parent_hash: A1)
    ↓
Artifact 3 (hash: A3, parent_hash: A2)
```

### Parent Validation
```python
if artifact.get("parent_hash"):
    parent = find_artifact_by_hash(artifact["parent_hash"])
    if not parent:
        raise ValueError(f"Broken parent chain at {artifact['artifact_id']}")
```

## Input Hash (Replay Proof)

### Purpose
For `replay_proof` artifacts, `input_hash` captures the hash of input data used to generate the proof.

### Requirement
```python
if artifact["artifact_type"] == "replay_proof":
    if not artifact.get("input_hash"):
        raise ValueError("replay_proof requires input_hash")
```

### Example
```json
{
  "artifact_type": "replay_proof",
  "input_hash": "hash_of_input_data",
  "artifact_hash": "hash_of_entire_artifact",
  "parent_hash": "hash_of_previous_artifact"
}
```

## Hash Properties

### Deterministic
- Same input → Same hash
- Sorted keys ensure reproducibility
- No randomness or timestamps in hash

### Collision-Resistant
- SHA256 provides 256-bit security
- Practically impossible to find collisions

### Tamper-Evident
- Any modification changes hash
- Broken chains detected immediately

## API Endpoints

### Validate Replay
```http
POST /bucket/validate-replay
```

**Response:**
```json
{
  "valid": true,
  "message": "Replay validation passed - chain integrity verified"
}
```

**Or:**
```json
{
  "valid": false,
  "errors": [
    "Tampering detected at index 5, artifact_id: tx_005",
    "Broken parent chain at artifact_id: tx_010"
  ]
}
```

### Validate Chain
```http
POST /bucket/validate-chain/{artifact_id}
```

**Response:**
```json
{
  "valid": true,
  "artifact_id": "tx_010",
  "message": "Chain validation passed"
}
```

## Testing

### Test Hash Computation
```python
artifact = {
    "artifact_id": "test1",
    "source_module_id": "test_module",
    "schema_version": "1.0.0",
    "timestamp_utc": "2025-01-19T10:00:00Z",
    "artifact_type": "truth_event"
}

hash1 = compute_artifact_hash(artifact)
hash2 = compute_artifact_hash(artifact)

assert hash1 == hash2  # Deterministic
```

### Test Chain Validation
```bash
# Store artifacts with parent links
curl -X POST http://localhost:8000/bucket/artifact -d '{
  "artifact_id": "a1",
  "artifact_hash": "computed_hash_a1",
  ...
}'

curl -X POST http://localhost:8000/bucket/artifact -d '{
  "artifact_id": "a2",
  "parent_hash": "computed_hash_a1",
  "artifact_hash": "computed_hash_a2",
  ...
}'

# Validate chain
curl -X POST http://localhost:8000/bucket/validate-chain/a2
```

## Guarantees

✅ **Deterministic**: Same artifact → Same hash  
✅ **Tamper-Evident**: Modification detected  
✅ **Chain Integrity**: Parent links verified  
✅ **Replay Validation**: Full chain replayable  

## Certification

**Status:** PRODUCTION_READY  
**Date:** 2025-01-19  
**Algorithm:** SHA256  
**Determinism:** GUARANTEED  
**Owner:** Ashmit_Pandey  

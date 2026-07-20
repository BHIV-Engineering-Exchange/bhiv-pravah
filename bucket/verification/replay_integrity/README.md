# Replay Integrity Verification

## Purpose
This directory contains test artifacts demonstrating:
1. **Hash chain validation**
2. **Tampering detection**
3. **Deterministic replay**
4. **Schema rejection**
5. **Type classification enforcement**

## Test Artifacts

### Valid Artifacts (Chain)

#### 1. `artifact_001_truth_event.json`
- **Type:** truth_event
- **Purpose:** Root artifact (no parent)
- **Status:** ✅ Valid

#### 2. `artifact_002_projection_event.json`
- **Type:** projection_event
- **Parent:** artifact_001
- **Purpose:** Derived projection with parent link
- **Status:** ✅ Valid

#### 3. `artifact_003_replay_proof.json`
- **Type:** replay_proof
- **Parent:** artifact_002
- **Input Hash:** Present
- **Purpose:** Validation proof with input_hash
- **Status:** ✅ Valid

### Invalid Artifacts (Rejection Examples)

#### 4. `artifact_004_tampered_example.json`
- **Issue:** Payload modified but hash not recomputed
- **Detection:** Hash mismatch during validation
- **Status:** ❌ Tampering detected

#### 5. `artifact_005_invalid_schema.json`
- **Issue:** schema_version = "0.9.0" (not allowed)
- **Detection:** Schema version validation
- **Status:** ❌ Rejected

#### 6. `artifact_006_invalid_type.json`
- **Issue:** artifact_type = "custom_event" (not allowed)
- **Detection:** Type classification validation
- **Status:** ❌ Rejected

## Running Validation

### Load Test Artifacts
```python
import json
from pathlib import Path

artifacts_dir = Path("verification/replay_integrity/test_artifacts")
for artifact_file in artifacts_dir.glob("*.json"):
    with artifact_file.open() as f:
        artifact = json.load(f)
        print(f"Loaded: {artifact['artifact_id']}")
```

### Validate Chain
```bash
# Store valid artifacts
curl -X POST http://localhost:8000/bucket/artifact \
  -d @verification/replay_integrity/test_artifacts/artifact_001_truth_event.json

curl -X POST http://localhost:8000/bucket/artifact \
  -d @verification/replay_integrity/test_artifacts/artifact_002_projection_event.json

curl -X POST http://localhost:8000/bucket/artifact \
  -d @verification/replay_integrity/test_artifacts/artifact_003_replay_proof.json

# Validate replay
curl -X POST http://localhost:8000/bucket/validate-replay
```

### Test Rejections
```bash
# Test invalid schema
curl -X POST http://localhost:8000/bucket/artifact \
  -d @verification/replay_integrity/test_artifacts/artifact_005_invalid_schema.json
# Expected: 400 Unsupported schema_version

# Test invalid type
curl -X POST http://localhost:8000/bucket/artifact \
  -d @verification/replay_integrity/test_artifacts/artifact_006_invalid_type.json
# Expected: 400 Invalid artifact_type
```

## Validation Results

### Expected Outcomes

| Artifact | Expected Result | Reason |
|----------|----------------|--------|
| artifact_001 | ✅ Accepted | Valid truth_event |
| artifact_002 | ✅ Accepted | Valid projection with parent |
| artifact_003 | ✅ Accepted | Valid replay_proof with input_hash |
| artifact_004 | ❌ Rejected | Hash mismatch (tampering) |
| artifact_005 | ❌ Rejected | Invalid schema version |
| artifact_006 | ❌ Rejected | Invalid artifact type |

## Hash Chain Structure

```
artifact_001 (truth_event)
    hash: e3b0c44...
    parent: none
    ↓
artifact_002 (projection_event)
    hash: d4735e3...
    parent_hash: e3b0c44... (links to artifact_001)
    ↓
artifact_003 (replay_proof)
    hash: 4e07408...
    parent_hash: d4735e3... (links to artifact_002)
    input_hash: 5feceb6... (validation input)
```

## Tampering Detection

The tampered artifact (004) demonstrates:
1. Original hash stored: `ORIGINAL_HASH_BEFORE_TAMPERING`
2. Payload modified: `amount: 9999999`
3. Hash NOT recomputed
4. Validation detects mismatch
5. Artifact rejected or flagged

## Certification

**Status:** ✅ VERIFIED  
**Date:** 2025-01-19  
**Artifacts:** 6 test cases  
**Coverage:**
- ✅ Valid chain (3 artifacts)
- ✅ Tampering detection (1 artifact)
- ✅ Schema rejection (1 artifact)
- ✅ Type rejection (1 artifact)

**Owner:** Ashmit_Pandey

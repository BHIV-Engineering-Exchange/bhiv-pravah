# SCHEMA REJECTION POLICY

## Status: ✅ ENFORCED

## Allowed Schema Versions

```python
ALLOWED_SCHEMA_VERSIONS = ["1.0.0"]
```

## Policy

### Strict Versioning
- **Current Version:** 1.0.0
- **Backward Compatibility:** NO
- **Forward Compatibility:** NO
- **Schema Evolution:** BLOCKED

### Rejection Rules

#### Rule 1: Version Mismatch
```python
if schema_version not in ALLOWED_SCHEMA_VERSIONS:
    raise ValueError(f"Unsupported schema_version: {schema_version}")
```

#### Rule 2: Missing Version
```python
if "schema_version" not in artifact:
    raise ValueError("Missing required field: schema_version")
```

#### Rule 3: Invalid Format
```python
if not isinstance(schema_version, str):
    raise ValueError("schema_version must be string")
```

## Enforcement

### On Storage
```python
def validate_schema_version(artifact: dict) -> tuple[bool, str]:
    schema_version = artifact.get("schema_version")
    if schema_version not in ALLOWED_SCHEMA_VERSIONS:
        return False, f"Unsupported schema_version: {schema_version}"
    return True, ""
```

### Automatic Rejection
All artifacts with unsupported schema versions are **automatically rejected** before storage.

## Schema Evolution Process

### Constitutional Lock
Schema is **IMMUTABLE** by constitutional design (Document 22).

### To Add New Version
1. **Governance Proposal** to Ashmit
2. **Threat Assessment** (Document 14)
3. **Migration Plan** (if needed)
4. **Owner Approval** (CEO-level)
5. **Code Deployment**
6. **Backward Compatibility** verification

### Requirements
- Must maintain append-only semantics
- Must not break existing artifacts
- Must pass all governance checks
- Must have rollback plan

## Rejected Versions

❌ `0.9.0` - Pre-release  
❌ `1.1.0` - Not approved  
❌ `2.0.0` - Not approved  
❌ `latest` - Not specific  
❌ `dev` - Not production  

## API Integration

### Valid Request
```http
POST /bucket/artifact
Content-Type: application/json

{
  "schema_version": "1.0.0",  // ✅ Accepted
  ...
}
```

### Invalid Request
```http
POST /bucket/artifact
Content-Type: application/json

{
  "schema_version": "1.1.0",  // ❌ Rejected
  ...
}
```

**Error Response:**
```json
{
  "detail": "Validation failed: Unsupported schema_version: 1.1.0. Allowed: ['1.0.0']"
}
```

## Testing

```bash
# Test valid version
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version": "1.0.0",
    ...
  }'

# Test invalid version
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version": "2.0.0",
    ...
  }'
# Expected: 400 Unsupported schema_version
```

## Version History

### 1.0.0 (Current)
- **Released:** 2025-01-19
- **Status:** ACTIVE
- **Features:**
  - Mandatory envelope fields
  - Hash linking
  - Artifact type classification
  - Append-only enforcement

## Guarantees

✅ **Version Lock**: Only 1.0.0 accepted  
✅ **Rejection**: Invalid versions blocked  
✅ **Immutability**: Schema cannot evolve without approval  
✅ **Consistency**: All artifacts use same schema  

## Future Versions

### Planned: 1.1.0 (Phase 2)
- Enhanced provenance tracking
- Cryptographic signatures
- Multi-region support

**Status:** NOT APPROVED  
**Timeline:** TBD  
**Approval Required:** YES  

## Certification

**Status:** ENFORCED  
**Date:** 2025-01-19  
**Current Version:** 1.0.0  
**Evolution:** BLOCKED  
**Owner:** Ashmit_Pandey  

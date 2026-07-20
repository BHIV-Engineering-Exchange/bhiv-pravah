# ARTIFACT CLASSIFICATION LOCK

## Status: ✅ LOCKED

## Allowed Artifact Types

The Bucket accepts **ONLY** these artifact types:

```python
ALLOWED_ARTIFACT_TYPES = [
    "truth_event",
    "projection_event",
    "registry_snapshot",
    "policy_snapshot",
    "replay_proof",
    "telemetry_record"
]
```

## Type Definitions

### truth_event
**Purpose:** Immutable facts from source systems  
**Example:** Transaction completed, user registered  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  

### projection_event
**Purpose:** Derived views from truth events  
**Example:** Daily summary, aggregated metrics  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  

### registry_snapshot
**Purpose:** Point-in-time registry state  
**Example:** Agent registry at timestamp  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  

### policy_snapshot
**Purpose:** Governance policy at timestamp  
**Example:** Artifact admission rules  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  

### replay_proof
**Purpose:** Validation of replay integrity  
**Example:** Chain validation result  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  
**Special:** Requires `input_hash` field  

### telemetry_record
**Purpose:** System metrics and monitoring  
**Example:** Performance metrics, health checks  
**Mutability:** IMMUTABLE  
**Operations:** CREATE, READ  

## Enforcement

### Validation
```python
def validate_artifact_type(artifact: dict) -> tuple[bool, str]:
    artifact_type = artifact.get("artifact_type")
    if artifact_type not in ALLOWED_ARTIFACT_TYPES:
        return False, f"Invalid artifact_type: {artifact_type}"
    return True, ""
```

### Rejection
```python
# Automatic rejection of unknown types
if artifact_type not in ALLOWED_ARTIFACT_TYPES:
    raise ValueError(f"Invalid artifact_type: {artifact_type}. Allowed: {ALLOWED_ARTIFACT_TYPES}")
```

## Adding New Types

### Process
1. **Proposal** to Ashmit (Owner)
2. **Governance Review** (7 days)
3. **Threat Assessment** (Document 14)
4. **Schema Definition**
5. **Owner Approval**
6. **Code Update** (requires restart)

### Requirements
- Must fit Bucket purpose
- Must be immutable
- Must have clear schema
- Must pass threat model
- Must have retention policy

## Rejected Types

These types are **PERMANENTLY REJECTED**:

❌ `user_data` - PII not allowed  
❌ `model_weights` - Too large  
❌ `video_file` - Wrong storage  
❌ `mutable_state` - Violates append-only  
❌ `business_logic` - Code not allowed  

## API Integration

### Store Artifact
```http
POST /bucket/artifact
Content-Type: application/json

{
  "artifact_type": "truth_event",  // Must be in allowed list
  ...
}
```

**Error Response:**
```json
{
  "detail": "Invalid artifact_type: custom_type. Allowed: ['truth_event', ...]"
}
```

## Testing

```bash
# Test valid type
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "truth_event",
    ...
  }'

# Test invalid type
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "custom_type",
    ...
  }'
# Expected: 400 Invalid artifact_type
```

## Type-Specific Rules

### replay_proof
```python
if artifact_type == "replay_proof":
    if not artifact.get("input_hash"):
        raise ValueError("replay_proof requires input_hash")
```

### Chained Types
```python
if artifact.get("parent_required"):
    if not artifact.get("parent_hash"):
        raise ValueError("Missing parent_hash for chained artifact")
```

## Guarantees

✅ **Type Safety**: Only allowed types accepted  
✅ **Immutability**: All types are immutable  
✅ **Schema Enforcement**: Type-specific validation  
✅ **Rejection**: Unknown types blocked  

## Certification

**Status:** LOCKED  
**Date:** 2025-01-19  
**Total Types:** 6  
**Expansion:** Requires owner approval  
**Owner:** Ashmit_Pandey  

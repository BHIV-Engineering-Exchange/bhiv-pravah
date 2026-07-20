# Append-Only Log Storage Architecture

**Document Version:** 1.0.0  
**Last Updated:** 2025-01-20  
**Status:** PRODUCTION ACTIVE

---

## 🎯 Core Philosophy

> **"Bucket is MEMORY, not DECISION"**

Bucket is a **permanent evidence locker**, not a processing system.

### What Bucket Does
✅ Accepts artifacts  
✅ Verifies structural correctness  
✅ Stores immutably  
✅ Allows replay of history  

### What Bucket NEVER Does
❌ Analyzes data  
❌ Derives meaning  
❌ Applies business logic  
❌ Triggers actions  
❌ Interprets results  
❌ Modifies artifacts  

---

## 🏗️ Architecture Overview

### Storage Model: Append-Only JSONL Log

```
artifact_log.jsonl
├── artifact_1 (line 1)
├── artifact_2 (line 2)
├── artifact_3 (line 3)
└── artifact_4 (line 4)
```

Each line is a complete, independent artifact.

### Key Files

```
data/artifacts/
├── artifact_log.jsonl      # Main append-only log
├── artifact_index.json      # Fast lookup index
└── chain_state.json         # Current chain state
```

---

## 🔒 Immutability Guarantees

### 1. Append-Only Writes

**Rule:** Once written, artifacts are NEVER modified.

```python
# ✅ ALLOWED
append_artifact(new_artifact)

# ❌ FORBIDDEN
update_artifact(artifact_id, changes)
delete_artifact(artifact_id)
modify_artifact(artifact_id, field, value)
```

### 2. Duplicate Prevention

**Rule:** Each `artifact_id` can only be stored once.

```python
# First write
store_artifact({"artifact_id": "A001", ...})  # ✅ Success

# Duplicate attempt
store_artifact({"artifact_id": "A001", ...})  # ❌ Rejected
```

### 3. Atomic Writes

**Rule:** Each artifact write is atomic and durable.

```python
# Write process
1. Validate structure
2. Compute hash
3. Append to log
4. fsync() to disk  # Force physical write
5. Update index
6. Update chain state
```

If any step fails, the entire operation is rolled back.

---

## 🔗 Hash Chain Architecture

### Chain Structure

```
Artifact 1
├── hash: H1
└── parent_hash: null (first artifact)

Artifact 2
├── hash: H2
└── parent_hash: H1

Artifact 3
├── hash: H3
└── parent_hash: H2
```

### Tamper Detection

If someone modifies Artifact 2:
```
Artifact 2 (modified)
├── hash: H2' (changed)
└── parent_hash: H1

Artifact 3
├── hash: H3
└── parent_hash: H2 (expects original hash)
```

**Result:** Chain breaks immediately. Tampering detected.

### Parent Validation Rules

| Artifact Position | Parent Hash Rule |
|------------------|------------------|
| First artifact | `parent_hash` must be `null` |
| All others | `parent_hash` must equal previous artifact's `hash` |

**Orphan Prevention:** If parent doesn't exist → artifact rejected.

---

## 🔐 Hash Authority Policy

### ❌ NEVER Trust Client Hashes

**Problem:**
```json
{
  "payload": "malicious_data",
  "hash": "trusted_looking_hash"
}
```

A malicious client could send fake hashes.

### ✅ Server Computes All Hashes

**Correct Flow:**
```
1. Client sends artifact (no hash)
2. Server validates structure
3. Server computes SHA256 hash
4. Server stores artifact with hash
5. Server returns hash to client
```

### Deterministic Hashing

**Hash Input (sorted):**
```json
{
  "artifact_id": "...",
  "artifact_type": "...",
  "parent_hash": "...",
  "payload": {...},
  "schema_version": "...",
  "source_module_id": "...",
  "timestamp_utc": "..."
}
```

**Serialization:** `json.dumps(hash_input, sort_keys=True, separators=(',', ':'))`

**Hash:** `SHA256(serialized_bytes)`

**Guarantee:** Same artifact → same hash everywhere.

---

## 📋 Artifact Structure

### Required Metadata Fields

```json
{
  "artifact_id": "unique_identifier",
  "timestamp_utc": "2025-01-20T10:30:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "aiaic_satellite_analysis",
  "artifact_type": "crop_yield_analysis",
  "parent_hash": "previous_artifact_hash",
  "payload": {
    "domain_specific_data": "..."
  },
  "hash": "computed_by_server"
}
```

### Allowed Envelope Fields

Only these fields are permitted:
- `artifact_id`
- `timestamp_utc`
- `schema_version`
- `source_module_id`
- `artifact_type`
- `parent_hash`
- `payload`
- `hash`

**Unknown fields → Rejected** (prevents schema drift)

---

## 🚫 Domain-Agnostic Validation

### What Bucket Validates

✅ **Structure** (metadata fields present)  
✅ **Size** (payload within limits)  
✅ **Schema version** (matches current version)  
✅ **Parent chain** (hash links valid)  
✅ **Envelope fields** (no unknown fields)  

### What Bucket NEVER Validates

❌ **Payload content** (domain-specific)  
❌ **Business logic** (belongs to analysis systems)  
❌ **Data meaning** (interpretation forbidden)  

### Example: Allowed vs Forbidden

```json
// ✅ ALLOWED (domain-agnostic)
{
  "artifact_type": "crop_yield_analysis",
  "payload": {
    "analysis_output": {...}
  }
}

// ❌ FORBIDDEN (contains decision)
{
  "artifact_type": "crop_yield_analysis",
  "payload": {
    "crop_yield_is_bad": true  // ← This is a DECISION
  }
}
```

**Why?** Bucket must remain domain-neutral. Decisions belong to analysis layers.

---

## 🔄 Deterministic Replay

### Replay Ordering

Artifacts are replayed in this order:
1. **Primary:** `timestamp_utc` (ascending)
2. **Secondary:** `parent_hash` chain

**Guarantee:** Every system replaying the log produces identical results.

### Replay Process

```python
1. Read artifact_log.jsonl line by line
2. For each artifact:
   a. Verify hash
   b. Verify parent chain
   c. Reconstruct state
3. Final state = complete system history
```

### Replay Validation

```python
def validate_replay():
    previous_hash = None
    for artifact in read_log():
        # Verify hash
        assert artifact.hash == compute_hash(artifact)
        
        # Verify parent chain
        if not first_artifact:
            assert artifact.parent_hash == previous_hash
        
        previous_hash = artifact.hash
```

---

## 📏 Size Limits

### Payload Size Limit

**Default:** 16 MB per artifact

**Rationale:**
- Prevents memory exhaustion
- Protects disk space
- Ensures reasonable processing time

**Configuration:**
```python
MAX_PAYLOAD_SIZE = 16 * 1024 * 1024  # 16MB
```

**Enforcement:**
```python
payload_size = len(json.dumps(payload).encode('utf-8'))
if payload_size > MAX_PAYLOAD_SIZE:
    raise ValueError("Payload too large")
```

---

## 🛡️ Security Properties

### 1. Tamper-Evident

Any modification breaks the hash chain immediately.

### 2. Append-Only

History cannot be rewritten or deleted.

### 3. Deterministic

Same input → same hash → same replay result.

### 4. Auditable

Complete history preserved forever.

### 5. Domain-Neutral

No interpretation = no bias = no corruption.

---

## 📊 Storage Statistics

### Available Metrics

```python
{
  "artifact_count": 1234,
  "last_hash": "abc123...",
  "log_file_size_bytes": 52428800,
  "log_file_size_mb": 50.0,
  "storage_path": "data/artifacts",
  "schema_version": "1.0.0",
  "max_payload_size_mb": 16.0
}
```

---

## 🔍 Validation Checks

### On Artifact Ingestion

| Check | Purpose |
|-------|---------|
| Required fields present | Metadata discipline |
| No unknown fields | Prevent schema drift |
| Schema version valid | Version compatibility |
| Payload size within limit | Resource protection |
| Parent hash exists | Chain integrity |
| No duplicate artifact_id | Uniqueness guarantee |

### On Chain Validation

| Check | Purpose |
|-------|---------|
| Hash correctness | Tamper detection |
| Parent chain valid | Integrity verification |
| No orphan artifacts | Completeness guarantee |
| Deterministic ordering | Replay consistency |

---

## 🎯 Use Cases

### 1. AIAIC Satellite Analysis

```json
{
  "artifact_id": "aiaic_sat_001",
  "artifact_type": "satellite_analysis",
  "source_module_id": "aiaic_processor",
  "payload": {
    "satellite_image_analysis": {...},
    "crop_health_metrics": {...}
  }
}
```

### 2. Marine Sensor Telemetry

```json
{
  "artifact_id": "marine_sensor_001",
  "artifact_type": "sensor_telemetry",
  "source_module_id": "marine_iot_gateway",
  "payload": {
    "temperature": 23.5,
    "salinity": 35.2,
    "ph_level": 8.1
  }
}
```

### 3. AI Model Predictions

```json
{
  "artifact_id": "ai_prediction_001",
  "artifact_type": "model_prediction",
  "source_module_id": "ml_inference_engine",
  "payload": {
    "prediction_output": {...},
    "confidence_scores": {...}
  }
}
```

---

## ✅ Definition of Done

Implementation is complete when Bucket guarantees:

1. ✅ **Immutability** - Artifacts cannot be modified
2. ✅ **Deterministic hashes** - Same artifact → same hash everywhere
3. ✅ **Chain integrity** - Artifacts form verifiable history
4. ✅ **Replayability** - System state can be reconstructed
5. ✅ **Schema discipline** - Artifacts follow strict rules
6. ✅ **Domain neutrality** - Bucket never interprets data

---

## 📚 Related Documents

- `CHAIN_INTEGRITY_ENFORCEMENT.md` - Hash chain details
- `HASH_AUTHORITY_POLICY.md` - Server-side hashing
- `DOMAIN_INGESTION_READINESS.md` - Validation rules
- `REPLAY_PROOF_VALIDATION.md` - Replay mechanics

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-20 | Initial append-only architecture |

---

**Bucket Owner:** Ashmit Pandey  
**Certification:** PRODUCTION READY  
**Review Cycle:** 6 months

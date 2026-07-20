# BHIV Bucket — Movement Documentation

**Document ID:** BUCKET-MOV-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** VERIFIED (codebase + live proof artifacts)  
**Component:** BHIV Bucket — Append-Only Evidence Substrate

---

## 1. Purpose

This document describes the **movement of data through BHIV Bucket**: what enters the system, what processing occurs, and what is produced. All content is derived from directly verifiable sources in this repository — source code, contract definitions, and documented live proof runs.

Bucket is defined canonically in `ROLE.md` as:

> *Bucket is the BHIV append-only evidence substrate.*

Bucket is **memory, not decision**. It stores artifacts exactly as received. It does not interpret payload content, execute workflows, or trigger downstream actions.

---

## 2. Movement Summary

| Stage | Description |
|-------|-------------|
| **Input** | Artifact envelope submitted via HTTP POST (metadata + payload) |
| **Processing** | Structure validation, lineage verification, server-side hash computation, append-only storage, audit capture |
| **Output** | Immutable stored artifact with hash-chain linkage and API acknowledgment |

---

## 3. Input

### 3.1 What Enters Bucket

An **artifact envelope** — a structured JSON record containing metadata fields and an opaque `payload`. The payload is domain-specific (e.g., SVACS perception data, transaction events) and is stored without interpretation.

### 3.2 Entry Points

| Endpoint | Method | Purpose | Source |
|----------|--------|---------|--------|
| `/bucket/artifact` | POST | Direct artifact write | `main.py` |
| `/bucket/artifacts/write` | POST | Core contract write (strict boundary) | `main.py` |
| `/bucket/latest-hash` | GET | Chain head lookup before write | `main.py` |

### 3.3 Required Envelope Fields

Defined in `services/append_only_storage.py`:

| Field | Required | Description |
|-------|----------|-------------|
| `artifact_id` | Yes | Unique identifier; duplicates rejected |
| `trace_id` | Yes | Cross-system trace identifier; stored unchanged |
| `timestamp_utc` | Yes | ISO 8601 UTC timestamp |
| `schema_version` | Yes | Must be `"1.0.0"` |
| `source_module_id` | Yes | Originating module (e.g., `svacs.perception`) |
| `artifact_type` | Yes | Artifact classification (e.g., `perception`) |
| `payload` | Yes | Domain data; Bucket does not interpret content |
| `parent_hash` | Conditional | Required for all artifacts after the first in the chain; must match current chain head |

**Allowed envelope fields** (no others permitted — schema drift is rejected):

`artifact_id`, `trace_id`, `timestamp_utc`, `schema_version`, `source_module_id`, `artifact_type`, `parent_hash`, `payload`, `hash`

Client-provided `hash` values are ignored. The server computes the authoritative hash.

### 3.4 Contract Write Request (Core Integration)

For `POST /bucket/artifacts/write`, the request body wraps the envelope:

```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "unique-id",
    "trace_id": "trace-001",
    "timestamp_utc": "2026-06-09T06:53:03Z",
    "schema_version": "1.0.0",
    "source_module_id": "svacs.perception",
    "artifact_type": "perception",
    "parent_hash": "84e57104a73b2fa1c02657518444135ec6a763e546f4eaeb77f94a13d732e489",
    "payload": { }
  }
}
```

### 3.5 Example Input (Live Proof)

Source: `SVACS_BUCKET_LIVE_PROOF.md` — executed 2026-06-09 UTC.

```json
{
  "artifact_id": "03d80b5b-6dd3-42c5-a401-92be64a59656",
  "trace_id": "svacs-tantra-1780987983",
  "timestamp_utc": "2026-06-09T06:53:03Z",
  "schema_version": "1.0.0",
  "source_module_id": "svacs.perception",
  "artifact_type": "perception",
  "parent_hash": "84e57104a73b2fa1c02657518444135ec6a763e546f4eaeb77f94a13d732e489",
  "payload": {
    "trace_id": "svacs-tantra-1780987983",
    "vessel_type": "cargo",
    "confidence_score": 0.9418,
    "dominant_freq_hz": 166.0,
    "anomaly_flag": false,
    "stage": "perception",
    "pipeline": "SVACS",
    "producer": "svacs_team_representative",
    "tantra_phase": "phase1_live_proof"
  }
}
```

---

## 4. Processing

### 4.1 Processing Pipeline

When an artifact enters Bucket, the following steps execute in order. No step interprets or modifies payload semantics.

```
HTTP Request Received
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Integration Gate (contract endpoint only)            │
│    Validate requester_id and integration_id             │
├─────────────────────────────────────────────────────────┤
│ 2. Structure Validation                                 │
│    • Required metadata fields present                     │
│    • No unknown envelope fields                           │
│    • schema_version == "1.0.0"                           │
│    • Payload size ≤ 16 MB                                │
├─────────────────────────────────────────────────────────┤
│ 3. Lineage Validation                                   │
│    • First artifact: parent_hash must be absent/null    │
│    • Subsequent artifacts: parent_hash must match       │
│      current chain head (chain_state.json)              │
├─────────────────────────────────────────────────────────┤
│ 4. Duplicate Check                                      │
│    • Reject if artifact_id already exists in index      │
├─────────────────────────────────────────────────────────┤
│ 5. Server-Side Hash Computation                         │
│    • SHA256 over canonical JSON (sort_keys, no spaces)   │
│    • Fields: artifact_id, trace_id, timestamp_utc,      │
│      schema_version, source_module_id, artifact_type,   │
│      parent_hash, payload                                │
├─────────────────────────────────────────────────────────┤
│ 6. Append-Only Persistence                              │
│    • Write record to artifact_log.jsonl                 │
│    • fsync() to disk (atomic, durable)                   │
├─────────────────────────────────────────────────────────┤
│ 7. Index & Chain State Update                           │
│    • Update artifact_index.json (artifact_id → position)│
│    • Update chain_state.json (last_hash, artifact_count)│
├─────────────────────────────────────────────────────────┤
│ 8. Audit Capture                                        │
│    • Log CREATE operation to audit trail                │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   API Response Returned
```

Implementation: `services/append_only_storage.py` → `store_artifact()`

### 4.2 What Bucket Does

| Action | Verified In |
|--------|-------------|
| Accepts artifact envelopes | `append_only_storage.py` |
| Validates structural correctness | `validate_artifact_structure()` |
| Validates hash-chain lineage | `validate_artifact_structure()` |
| Computes server-authoritative SHA256 | `compute_hash()` |
| Stores immutably (append-only) | `store_artifact()` |
| Preserves trace_id unchanged | `SVACS_BUCKET_LIVE_PROOF.md` |
| Logs operations to audit trail | `middleware/audit_middleware.py` |

### 4.3 What Bucket Does NOT Do

| Excluded Action | Reference |
|-----------------|-----------|
| Analyze or interpret payload content | `ROLE.md`, `docs/APPEND_LOG_STORAGE.md` |
| Apply business logic | `docs/APPEND_LOG_STORAGE.md` |
| Modify, enrich, or normalize data | `append_only_storage.py` |
| Execute agents or workflows | `ROLE.md` |
| Trigger actions in other systems | `ROLE.md` |
| Delete or update stored artifacts | `docs/APPEND_LOG_STORAGE.md` |

### 4.4 Rejection Conditions

| Condition | HTTP Status | Example |
|-----------|-------------|---------|
| Missing required field | 400 | `"Missing required field: trace_id"` |
| Unknown envelope field | 400 | `"Unknown envelope field: extra_field. Schema drift detected."` |
| Invalid schema version | 400 | `"Invalid schema version: 2.0.0. Expected: 1.0.0"` |
| Payload exceeds size limit | 400 | `"Payload size exceeds limit"` |
| Invalid parent_hash | 400 | `"Invalid parent_hash. Expected: {hash}, Got: {value}"` |
| Duplicate artifact_id | 400 | `"Duplicate artifact_id: {id}"` |

---

## 5. Output

### 5.1 Immediate API Response (Write Acknowledgment)

On successful write, Bucket returns:

```json
{
  "success": true,
  "artifact_id": "03d80b5b-6dd3-42c5-a401-92be64a59656",
  "hash": "7ef3d6bdf6f72f3cbf88580f369b65b44dfcb989d2e18ec6ad7be4c6e34a59f2",
  "parent_hash": "84e57104a73b2fa1c02657518444135ec6a763e546f4eaeb77f94a13d732e489",
  "timestamp": "2026-06-09T06:53:03Z",
  "storage_type": "append_only",
  "message": "Artifact stored successfully in append-only log"
}
```

Contract endpoint (`POST /bucket/artifacts/write`) returns equivalent fields wrapped in a success envelope with `request_id`.

### 5.2 Persistent Stored Artifact

The immutable record is written to the append-only log:

| File | Purpose |
|------|---------|
| `data/artifacts/artifact_log.jsonl` | Primary append-only log (one JSON record per line) |
| `data/artifacts/artifact_index.json` | Fast lookup index (artifact_id → file position) |
| `data/artifacts/chain_state.json` | Current chain head (`last_hash`, `artifact_count`) |

Each log line contains the artifact envelope and the server-computed hash:

```json
{
  "artifact": {
    "artifact_id": "03d80b5b-6dd3-42c5-a401-92be64a59656",
    "trace_id": "svacs-tantra-1780987983",
    "timestamp_utc": "2026-06-09T06:53:03Z",
    "schema_version": "1.0.0",
    "source_module_id": "svacs.perception",
    "artifact_type": "perception",
    "parent_hash": "84e57104a73b2fa1c02657518444135ec6a763e546f4eaeb77f94a13d732e489",
    "payload": { }
  },
  "hash": "7ef3d6bdf6f72f3cbf88580f369b65b44dfcb989d2e18ec6ad7be4c6e34a59f2"
}
```

### 5.3 Read-Back Output

Retrieved via `GET /bucket/artifact/{artifact_id}` or `POST /bucket/artifacts/read`:

```json
{
  "artifact": {
    "artifact_id": "03d80b5b-6dd3-42c5-a401-92be64a59656",
    "trace_id": "svacs-tantra-1780987983",
    "timestamp_utc": "2026-06-09T06:53:03Z",
    "schema_version": "1.0.0",
    "source_module_id": "svacs.perception",
    "artifact_type": "perception",
    "parent_hash": "84e57104a73b2fa1c02657518444135ec6a763e546f4eaeb77f94a13d732e489",
    "payload": {
      "trace_id": "svacs-tantra-1780987983",
      "vessel_type": "cargo",
      "confidence_score": 0.9418,
      "pipeline": "SVACS"
    }
  },
  "storage_type": "append_only",
  "chain_verified": true
}
```

Payload content is returned unchanged from write to read-back.

---

## 6. End-to-End Movement Flow

### 6.1 System Context

```
  SVACS ──write──►                    ◄──write── NICAI
                    BHIV Bucket
  Core  ──write──►                    ◄──read──── InsightFlow
                    (memory / truth anchor)
```

Producers write. Consumers read. Bucket stores.

### 6.2 Write Movement

```
Producer                    Bucket                         Storage
   │                          │                               │
   │  POST /bucket/artifact   │                               │
   │  (artifact envelope)     │                               │
   │ ────────────────────────►│                               │
   │                          │  Validate structure           │
   │                          │  Validate lineage             │
   │                          │  Compute SHA256               │
   │                          │ ─────────────────────────────►│ artifact_log.jsonl
   │                          │                               │ artifact_index.json
   │                          │                               │ chain_state.json
   │                          │  Log audit entry              │
   │                          │ ─────────────────────────────►│ audit.log
   │  { artifact_id, hash,    │                               │
   │    parent_hash, ... }    │                               │
   │ ◄────────────────────────│                               │
```

### 6.3 Read Movement

```
Consumer                    Bucket                         Storage
   │                          │                               │
   │  GET /bucket/artifact/id │                               │
   │ ────────────────────────►│                               │
   │                          │  Lookup index                 │
   │                          │ ◄─────────────────────────────│ artifact_log.jsonl
   │  { artifact,             │                               │
   │    chain_verified: true }│                               │
   │ ◄────────────────────────│                               │
```

---

## 7. Supplementary Evidence

### 7.1 Screenshot

**Not available in repository.** No screenshot files are checked into the codebase.

When the server is running, interactive API documentation is available at:

```
GET /docs
```

### 7.2 Logs

| Log Type | Location | Content |
|----------|----------|---------|
| Application log | `utils/logger` output | Artifact append events, validation failures |
| Audit log | `data/audit.log` (file fallback) or MongoDB `audit_logs` | CREATE/READ with artifact_id, requester_id, status |
| Storage log | `data/artifacts/artifact_log.jsonl` | One immutable record per artifact |

Example application log message (from `append_only_storage.py`):

```
Artifact {artifact_id} stored successfully with hash {computed_hash}
```

Example audit entry fields (from `middleware/audit_middleware.py`):

```
timestamp, operation_type, artifact_id, requester_id, integration_id,
status, data_after, immutable: true
```

### 7.3 Runtime Output

**Live proof execution** — SVACS Phase 1, 2026-06-09 UTC.

| Field | Value |
|-------|-------|
| Execution timestamp | `2026-06-09T06:53:03.341041+00:00` |
| Target | `http://127.0.0.1:8005` |
| Proof script | `scripts/svacs_phase1_proof.py` |
| Machine-readable proof | `data/svacs_phase1_proof.json` |
| Human-readable report | `SVACS_BUCKET_LIVE_PROOF.md` |

**Verification results:**

| Check | Result | Evidence |
|-------|--------|----------|
| Hash proof | PASS | Server hash matches locally recomputed SHA256 |
| Trace proof | PASS | `trace_id` unchanged: write → storage → read-back |
| Lineage proof | PASS | `parent_hash` links to correct chain head |
| Failure visibility | PASS | Broken lineage rejected with HTTP 400 |

**Failure case runtime output** (broken lineage injection):

```json
{
  "detail": {
    "error": "ValidationError",
    "message": "Artifact validation failed: Invalid parent_hash. Expected: 7ef3d6bdf6f72f3cbf88580f369b65b44dfcb989d2e18ec6ad7be4c6e34a59f2, Got: INVALID_HASH_INTENTIONAL",
    "artifact_id": "0bb66039-4a54-4a10-94e1-5a07f6997d08"
  }
}
```

**Chain state after write:**

| Field | Value |
|-------|-------|
| artifact_count | 5 |
| last_hash | `7ef3d6bdf6f72f3cbf88580f369b65b44dfcb989d2e18ec6ad7be4c6e34a59f2` |

---

## 8. Related Read Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/bucket/artifact/{artifact_id}` | GET | Retrieve single artifact |
| `/bucket/artifacts` | GET | List artifacts (supports `trace_id` filter) |
| `/bucket/artifacts/read` | POST | Contract read endpoint |
| `/bucket/artifacts/query` | POST | Contract query endpoint |
| `/bucket/latest-hash` | GET | Current chain head |
| `/bucket/validate-replay` | POST | Full chain integrity validation |

---

## 9. Source References

| Reference | Path | Relevance |
|-----------|------|-----------|
| Canonical role definition | `ROLE.md` | What Bucket is and is not |
| Storage architecture | `docs/APPEND_LOG_STORAGE.md` | Immutability guarantees |
| Core implementation | `services/append_only_storage.py` | Write/read/validate logic |
| HTTP endpoints | `main.py` (lines ~2463–3111) | API surface |
| Core contract | `docs/constitutional/BHIV_CORE_BUCKET_CONTRACT.md` | Integration boundary |
| Live proof report | `SVACS_BUCKET_LIVE_PROOF.md` | End-to-end runtime evidence |
| Machine-readable proof | `data/svacs_phase1_proof.json` | Verifiable test output |
| Proof script | `scripts/svacs_phase1_proof.py` | Repeatable execution |

---

## 10. Document Control

| Field | Value |
|-------|-------|
| Prepared for | Movement documentation exercise |
| Verification method | Code review + live proof artifact cross-reference |
| Scope | Bucket artifact write/read movement only |
| Exclusions | Agent basket orchestration, governance endpoints, frontend UI |

---

*End of document.*

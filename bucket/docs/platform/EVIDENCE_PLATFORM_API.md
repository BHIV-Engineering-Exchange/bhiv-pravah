# Evidence Platform API Reference

**Document ID:** BUCKET-API-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** CANONICAL  
**Owner:** Siddhesh Narkar — Bucket Custodian  
**Base URL:** `https://<bucket-host>` (e.g. port 8000 local, production via Render/ngrok)

---

## 1. API Design Principles

| Principle | Implementation |
|-----------|----------------|
| Stability | Path-stable `/bucket/*` endpoints; additive response fields only |
| Server hash authority | Client `hash` always ignored |
| Constitutional discipline | No product-specific endpoints |
| Versioning | `schema_version` in envelope; API v1 implicit |
| Error visibility | All rejections return explicit messages |

### Versioning Strategy

| Layer | Version | Breaking Change Policy |
|-------|---------|------------------------|
| Envelope | `schema_version: "1.0.0"` | New versions require governance approval |
| HTTP paths | v1 (stable) | Additive only; no path removal |
| Response fields | v1 | New fields additive; existing fields never removed |

---

## 2. Artifact Persistence

### 2.1 `POST /bucket/artifact`

**Purpose:** Primary artifact write endpoint for all ecosystem producers.

**Authentication:** Open in v1; producer identity via `source_module_id`.

**Request:**
```json
{
  "artifact_id": "string (required, unique)",
  "trace_id": "string (required)",
  "timestamp_utc": "ISO8601 (required)",
  "schema_version": "1.0.0 (required)",
  "source_module_id": "string (required)",
  "artifact_type": "string (required)",
  "parent_hash": "string (required after genesis)",
  "payload": "object (required)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "artifact_id": "string",
  "hash": "string (server SHA-256)",
  "parent_hash": "string | null",
  "timestamp": "ISO8601",
  "storage_type": "append_only",
  "message": "Artifact stored successfully in append-only log"
}
```

**Error Responses:**

| Status | Cause | Body |
|--------|-------|------|
| 400 | Validation failure | `{ "detail": { "error": "ValidationError", "message": "...", "artifact_id": "..." } }` |
| 500 | Storage failure | `{ "detail": "..." }` |

**Security:** Client-provided `hash` stripped. Payload size max 16 MB.

---

### 2.2 `POST /bucket/artifacts/write`

**Purpose:** Core-privileged contract write with strict boundary enforcement.

**Authentication:** `integration_id` must match Core patterns (`bhiv_core`, `core_*`, etc.).

**Request:**
```json
{
  "requester_id": "string (required)",
  "integration_id": "string (required — Core only)",
  "artifact": {
    "artifact_id": "string",
    "trace_id": "string",
    "timestamp_utc": "ISO8601",
    "schema_version": "1.0.0",
    "source_module_id": "string",
    "artifact_type": "string",
    "parent_hash": "string | null",
    "payload": {}
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "request_id": "string",
  "data": {
    "artifact_id": "string",
    "hash": "string",
    "parent_hash": "string | null",
    "timestamp_utc": "ISO8601",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

**Error Responses:**

| Status | Cause |
|--------|-------|
| 400 | `integration_boundary_violation`, validation error |
| 500 | `internal_server_error` |

---

## 3. Artifact Retrieval

### 3.1 `GET /bucket/artifact/{artifact_id}`

**Purpose:** Retrieve single artifact by ID.

**Request:** Path parameter `artifact_id`.

**Success Response (200):**
```json
{
  "artifact": { "...envelope..." },
  "storage_type": "append_only",
  "chain_verified": true
}
```

**Error Responses:**

| Status | Cause |
|--------|-------|
| 404 | Artifact not found |
| 500 | Server error |

**Note:** `chain_verified` is a response flag; full chain validation requires `POST /bucket/validate-replay`.

---

### 3.2 `POST /bucket/artifacts/read`

**Purpose:** Core-privileged deterministic read.

**Request:**
```json
{
  "requester_id": "string",
  "integration_id": "string (Core only)",
  "artifact_id": "string"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "request_id": "string",
  "data": {
    "artifact": { "...envelope..." },
    "storage_type": "append_only",
    "chain_verified": true
  }
}
```

**Error:** 404 `artifact_not_found`, 400 `integration_boundary_violation`

---

## 4. Evidence Lookup

### 4.1 `GET /bucket/artifacts`

**Purpose:** List artifacts with optional trace filter.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 100 | Max 1000 |
| `offset` | int | 0 | Skip count |
| `trace_id` | string | null | Filter by trace |

**Success Response (200):**
```json
{
  "artifacts": [ "...envelope objects..." ],
  "count": 10,
  "total": 100,
  "offset": 0,
  "limit": 100,
  "storage_type": "append_only"
}
```

With `trace_id`:
```json
{
  "artifacts": [ "..." ],
  "count": 3,
  "total": 3,
  "trace_id": "string",
  "storage_type": "append_only"
}
```

---

### 4.2 `POST /bucket/artifacts/query`

**Purpose:** Core-privileged filtered query with pagination.

**Request:**
```json
{
  "requester_id": "string",
  "integration_id": "string (Core only)",
  "limit": 100,
  "offset": 0,
  "artifact_type": "string (optional)",
  "source_module_id": "string (optional)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "request_id": "string",
  "data": {
    "artifacts": [ "..." ],
    "count": 10,
    "total": 100,
    "offset": 0,
    "limit": 100,
    "storage_type": "append_only"
  }
}
```

---

## 5. Replay Validation

### 5.1 `POST /bucket/validate-replay`

**Purpose:** Full chain integrity validation — scans entire log, verifies hashes and lineage.

**Request:** No body required.

**Success Response (200):**
```json
{
  "valid": true,
  "artifact_count": 7,
  "last_hash": "string",
  "storage_type": "append_only",
  "message": "Chain integrity validation PASSED - no tampering detected",
  "legacy_storage_valid": true,
  "legacy_errors": []
}
```

**Failure Response (200 with valid=false):**
```json
{
  "valid": false,
  "errors": [ "Line N: Hash mismatch for ..." ],
  "artifact_count": 7,
  "last_hash": "string",
  "storage_type": "append_only",
  "message": "Chain integrity validation FAILED - tampering detected",
  "severity": "CRITICAL"
}
```

---

### 5.2 `POST /bucket/validate-chain/{artifact_id}`

**Purpose:** Validate chain from specific artifact backward (legacy storage path).

**Note:** Operates on legacy `data/bucket_artifacts.json`, not append-only log. Prefer `validate-replay` for production.

---

## 6. Provenance Queries

### 6.1 `POST /bucket/audit/read`

**Purpose:** Query audit trail records.

**Request:**
```json
{
  "requester_id": "string",
  "integration_id": "string (Core only)",
  "limit": 100,
  "artifact_id": "string (optional)",
  "operation_type": "string (optional)",
  "status": "string (optional)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "request_id": "string",
  "data": {
    "entries": [
      {
        "timestamp": "ISO8601",
        "operation_type": "CREATE",
        "artifact_id": "string",
        "requester_id": "string",
        "status": "success"
      }
    ],
    "count": 10
  }
}
```

---

## 7. Trace Queries

Trace correlation uses `GET /bucket/artifacts?trace_id={id}`.

**W3C Trace Context alignment:** Bucket stores `trace_id` as provided. Producers should use UUID format consistent with OpenTelemetry trace IDs where applicable.

**No dedicated `/bucket/trace/{id}` endpoint in v1** — use artifacts list with `trace_id` filter.

---

## 8. Registry Queries

### 8.1 `GET /bucket/schema-info`

**Purpose:** Discover envelope contract requirements.

**Response (200):**
```json
{
  "schema_version": "1.0.0",
  "required_fields": [ "artifact_id", "trace_id", "..." ],
  "allowed_envelope_fields": [ "..." ],
  "max_payload_size_bytes": 16777216,
  "max_payload_size_mb": 16
}
```

### 8.2 `GET /bucket/chain-state`

**Response (200):**
```json
{
  "last_hash": "string | null",
  "artifact_count": 0,
  "storage_type": "append_only"
}
```

### 8.3 `GET /bucket/latest-hash`

**Purpose:** Fetch chain head before write.

**Response (200):**
```json
{
  "last_hash": "string | null",
  "artifact_count": 7
}
```

### 8.4 `GET /bucket/storage-stats`

**Response (200):**
```json
{
  "artifact_count": 7,
  "last_hash": "string",
  "log_file_size_bytes": 12345,
  "log_file_size_mb": 0.01,
  "storage_path": "data/artifacts",
  "schema_version": "1.0.0",
  "max_payload_size_mb": 16
}
```

### 8.5 `GET /bucket/certification`

**Purpose:** Platform certification metadata.

---

## 9. Integrity Verification

### 9.1 `POST /bucket/compute-hash`

**Purpose:** Preview server hash without storing.

**Request:** Full artifact envelope (same as write).

**Response (200):**
```json
{
  "artifact_id": "string",
  "computed_hash": "string",
  "algorithm": "SHA256",
  "deterministic": true,
  "message": "Hash computed by server (client hashes never trusted)"
}
```

### 9.2 `POST /bucket/validate-structure`

**Purpose:** Dry-run structure validation without storing.

**Request:** Full artifact envelope.

**Success Response (200):**
```json
{
  "valid": true,
  "artifact_id": "string",
  "message": "Artifact structure is valid"
}
```

**Failure Response (200 with valid=false):**
```json
{
  "valid": false,
  "error": "Missing required field: trace_id",
  "artifact_id": "string"
}
```

---

## 10. Batch Retrieval

**Status:** PLANNED — Not implemented in v1.

**Current workaround:** Use paginated query:

```
GET /bucket/artifacts?limit=100&offset=0
POST /bucket/artifacts/query { "limit": 100, "offset": 0, ... }
```

**Design target (v1.1):**
```
POST /bucket/artifacts/batch-read
{ "artifact_ids": ["id1", "id2", ...] }  // max 100 per config/scale_limits.py
```

`ScaleLimits.MAX_BATCH_SIZE = 500` defined but endpoint not yet implemented.

---

## 11. Search Capabilities

**Status:** LIMITED in v1.

| Capability | Status | Endpoint |
|------------|--------|----------|
| Filter by `trace_id` | ✅ Implemented | `GET /bucket/artifacts?trace_id=` |
| Filter by `artifact_type` | ✅ Implemented | `POST /bucket/artifacts/query` |
| Filter by `source_module_id` | ✅ Implemented | `POST /bucket/artifacts/query` |
| Full-text payload search | ❌ Not implemented | — |
| Time-range search | ❌ Not implemented | — |

---

## 12. Platform Health

### `GET /health`

**Purpose:** Service and dependency health check.

**Response (200):**
```json
{
  "status": "healthy | degraded | unhealthy",
  "append_only_storage": { "status": "active", "artifact_count": 7 },
  "services": { "mongodb": "connected", "redis": "connected" }
}
```

---

## 13. Security Expectations

| Concern | v1 Behavior | Recommendation |
|---------|-------------|----------------|
| Authentication | Open write/read endpoints | Network-level ACL in production |
| Authorization | Core contract endpoints check `integration_id` | Producers use direct write path |
| Hash authority | Server-only | Never trust client hash |
| Payload size | 16 MB max | Enforce at producer |
| Audit | All contract ops logged | Monitor `audit/read` |
| TLS | Deployment responsibility | Required in production |
| CORS | `allow_origins: *` | Restrict in production |

---

## 14. Error Handling Summary

| Code | Meaning | Producer Action |
|------|---------|-----------------|
| 200 | Success (including `valid: false` on validate endpoints) | Process response |
| 400 | Validation / boundary violation | Fix request, check schema-info |
| 404 | Not found | Verify artifact_id, retry read |
| 500 | Server error | Retry with backoff |

All 400 errors on write should be treated as **visible rejections** — never silent failures.

---

## 15. API Quick Reference

| Method | Path | Category | Access |
|--------|------|----------|--------|
| POST | `/bucket/artifact` | Persist | All producers |
| POST | `/bucket/artifacts/write` | Persist | Core only |
| GET | `/bucket/artifact/{id}` | Retrieve | Open |
| POST | `/bucket/artifacts/read` | Retrieve | Core only |
| GET | `/bucket/artifacts` | Lookup | Open |
| POST | `/bucket/artifacts/query` | Lookup | Core only |
| POST | `/bucket/validate-replay` | Integrity | Open |
| POST | `/bucket/compute-hash` | Integrity | Open |
| POST | `/bucket/validate-structure` | Integrity | Open |
| GET | `/bucket/latest-hash` | Registry | Open |
| GET | `/bucket/chain-state` | Registry | Open |
| GET | `/bucket/schema-info` | Registry | Open |
| GET | `/bucket/storage-stats` | Registry | Open |
| POST | `/bucket/audit/read` | Provenance | Core only |
| GET | `/health` | Platform | Open |
| GET | `/docs` | Platform | Open (Swagger UI) |

---

## 16. Related Documents

| Document | Purpose |
|----------|---------|
| `BUCKET_PLATFORM_ARCHITECTURE.md` | Architecture |
| `EVIDENCE_REGISTRY_SPEC.md` | Registry model |
| `ECOSYSTEM_PRODUCER_PACK.md` | Producer contracts |
| `docs/HASH_AUTHORITY_POLICY.md` | Hash policy |

---

*End of EVIDENCE_PLATFORM_API.md*

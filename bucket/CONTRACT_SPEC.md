# CONTRACT_SPEC

## Scope
This is the Core-facing API contract for BHIV Bucket integration readiness.

Rules preserved:
- Append-only storage behavior is unchanged.
- Bucket remains memory-only (no execution logic).
- Contract validation enforced at API boundary.
- Only Core integration is allowed on contract endpoints.

Base URL:
- `http://localhost:8000`

---

## 1) Endpoint: `/bucket/artifacts/write`
Method:
- `POST`

Request JSON:
```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "artifact-001",
    "timestamp_utc": "2026-04-14T10:00:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "analysis_report",
    "parent_hash": null,
    "payload": {
      "summary": "deterministic output"
    }
  }
}
```

Success Response JSON:
```json
{
  "success": true,
  "request_id": "uuid",
  "timestamp": "2026-04-14T10:00:01.000000Z",
  "data": {
    "artifact_id": "artifact-001",
    "hash": "sha256hex",
    "parent_hash": null,
    "timestamp_utc": "2026-04-14T10:00:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

Validation rules:
- `integration_id` must be Core-only (`core`, `bhiv_core`, `bhiv-core`, or core-prefixed).
- Unknown fields are rejected at all request object levels.
- Envelope fields required:
  - `artifact_id`, `timestamp_utc`, `schema_version`, `source_module_id`, `artifact_type`.
- `schema_version` must match current storage schema (`1.0.0`).
- Payload size must be <= 16 MB.
- Lineage rule:
  - first artifact must not include non-null `parent_hash`.
  - subsequent artifacts must have `parent_hash` equal to current chain `last_hash`.
- Client-supplied `hash` is ignored; server computes authoritative hash.

Rejection conditions:
- Invalid/unknown fields -> 422.
- Non-Core integration -> 400.
- Oversized payload -> 400.
- Invalid lineage -> 400.
- Schema drift / structure mismatch -> 400.
- Unexpected internal failure -> 500.

---

## 2) Endpoint: `/bucket/artifacts/read`
Method:
- `POST`

Request JSON:
```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact_id": "artifact-001"
}
```

Success Response JSON:
```json
{
  "success": true,
  "request_id": "uuid",
  "timestamp": "2026-04-14T10:00:02.000000Z",
  "data": {
    "artifact": {
      "artifact_id": "artifact-001",
      "timestamp_utc": "2026-04-14T10:00:00Z",
      "schema_version": "1.0.0",
      "source_module_id": "core_pipeline",
      "artifact_type": "analysis_report",
      "parent_hash": null,
      "payload": {"summary": "deterministic output"},
      "hash": "sha256hex"
    },
    "storage_type": "append_only",
    "chain_verified": true
  }
}
```

Validation rules:
- Core-only integration enforcement.
- Unknown fields rejected.
- `artifact_id` is required.

Rejection conditions:
- Invalid/unknown fields -> 422.
- Non-Core integration -> 400.
- Artifact not found -> 404.
- Unexpected internal failure -> 500.

---

## 3) Endpoint: `/bucket/artifacts/query`
Method:
- `POST`

Request JSON:
```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "limit": 50,
  "offset": 0,
  "artifact_type": "analysis_report",
  "source_module_id": "core_pipeline"
}
```

Success Response JSON:
```json
{
  "success": true,
  "request_id": "uuid",
  "timestamp": "2026-04-14T10:00:03.000000Z",
  "data": {
    "artifacts": [],
    "count": 0,
    "total": 0,
    "limit": 50,
    "offset": 0,
    "filters": {
      "artifact_type": "analysis_report",
      "source_module_id": "core_pipeline"
    },
    "storage_type": "append_only"
  }
}
```

Validation rules:
- Core-only integration enforcement.
- Unknown fields rejected.
- `limit` range: 1 to 1000.
- `offset` minimum: 0.
- Filtering is deterministic and metadata-only.

Rejection conditions:
- Invalid/unknown fields -> 422.
- Non-Core integration -> 400.
- Unexpected internal failure -> 500.

---

## 4) Endpoint: `/bucket/audit/read`
Method:
- `POST`

Request JSON:
```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "limit": 100,
  "artifact_id": "artifact-001",
  "operation_type": "CREATE",
  "status": "success"
}
```

Success Response JSON:
```json
{
  "success": true,
  "request_id": "uuid",
  "timestamp": "2026-04-14T10:00:04.000000Z",
  "data": {
    "records": [],
    "count": 0,
    "limit": 100,
    "filters": {
      "artifact_id": "artifact-001",
      "operation_type": "CREATE",
      "status": "success"
    }
  }
}
```

Validation rules:
- Core-only integration enforcement.
- Unknown fields rejected.
- `limit` range: 1 to 1000.
- Filters are optional and exact-match.

Rejection conditions:
- Invalid/unknown fields -> 422.
- Non-Core integration -> 400.
- Unexpected internal failure -> 500.

---

## Standard Error Response (All Contract Endpoints)
```json
{
  "success": false,
  "error": "string",
  "request_id": "uuid",
  "timestamp": "ISO8601"
}
```

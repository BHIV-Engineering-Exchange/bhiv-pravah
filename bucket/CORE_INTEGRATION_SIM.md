# CORE_INTEGRATION_SIM

## Goal
Simulate how BHIV Core should call Bucket through standardized contract APIs.

## Flow
1. Core writes artifact.
2. Core reads artifact by ID.
3. Core queries artifacts by metadata.
4. Core reads audit records for observability.

---

## Step 1: Write Artifact
Request:
```json
POST /bucket/artifacts/write
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "core-flow-001",
    "timestamp_utc": "2026-04-14T12:00:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": null,
    "payload": {
      "event": "core_to_bucket_write",
      "version": "v1"
    }
  }
}
```

Sample response:
```json
{
  "success": true,
  "request_id": "8d8ab8ef-bde1-4f10-b216-cc2f34d5a300",
  "timestamp": "2026-04-14T12:00:00.234000Z",
  "data": {
    "artifact_id": "core-flow-001",
    "hash": "abc123...",
    "parent_hash": null,
    "timestamp_utc": "2026-04-14T12:00:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

---

## Step 2: Read Artifact
Request:
```json
POST /bucket/artifacts/read
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact_id": "core-flow-001"
}
```

Sample response:
```json
{
  "success": true,
  "request_id": "48dc31d7-2e87-4c0f-9c7b-79842adcbf8f",
  "timestamp": "2026-04-14T12:00:01.145000Z",
  "data": {
    "artifact": {
      "artifact_id": "core-flow-001",
      "timestamp_utc": "2026-04-14T12:00:00Z",
      "schema_version": "1.0.0",
      "source_module_id": "core_pipeline",
      "artifact_type": "integration_event",
      "parent_hash": null,
      "payload": {
        "event": "core_to_bucket_write",
        "version": "v1"
      },
      "hash": "abc123..."
    },
    "storage_type": "append_only",
    "chain_verified": true
  }
}
```

---

## Step 3: Query Artifacts
Request:
```json
POST /bucket/artifacts/query
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "limit": 10,
  "offset": 0,
  "artifact_type": "integration_event",
  "source_module_id": "core_pipeline"
}
```

Sample response:
```json
{
  "success": true,
  "request_id": "634f0905-4cc3-4a95-a12e-f1462eac5b58",
  "timestamp": "2026-04-14T12:00:01.901000Z",
  "data": {
    "artifacts": [],
    "count": 0,
    "total": 0,
    "limit": 10,
    "offset": 0,
    "filters": {
      "artifact_type": "integration_event",
      "source_module_id": "core_pipeline"
    },
    "storage_type": "append_only"
  }
}
```

---

## Step 4: Read Audit
Request:
```json
POST /bucket/audit/read
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "limit": 25,
  "artifact_id": "core-flow-001",
  "operation_type": "CREATE",
  "status": "success"
}
```

Sample response:
```json
{
  "success": true,
  "request_id": "70fecfdf-c9db-4e7a-855f-b89f1be5a6e8",
  "timestamp": "2026-04-14T12:00:02.300000Z",
  "data": {
    "records": [],
    "count": 0,
    "limit": 25,
    "filters": {
      "artifact_id": "core-flow-001",
      "operation_type": "CREATE",
      "status": "success"
    }
  }
}
```

## End-to-End Explanation
- Core sends validated requests to contract endpoints.
- Boundary validation enforces schema + Core-only integration.
- Bucket persists artifacts via append-only storage with server-computed hash.
- Bucket returns deterministic response envelopes with `request_id` and timestamp.
- Audit trail records success/rejection/failure events.

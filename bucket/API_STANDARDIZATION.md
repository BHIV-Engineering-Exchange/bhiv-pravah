# API_STANDARDIZATION

## Objective
Standardize Core-facing Bucket APIs with strict schema validation, deterministic response shapes, and enforceable rejection behavior.

## Implemented Standardization

### 1) Contract endpoint set
- `POST /bucket/artifacts/write`
- `POST /bucket/artifacts/read`
- `POST /bucket/artifacts/query`
- `POST /bucket/audit/read`

### 2) Strict schema validation
- Pydantic models define every request schema.
- Unknown fields are rejected with `extra="forbid"`.
- Typed constraints enforce limits (`limit`, `offset`, etc).

### 3) Boundary enforcement
- `integration_id` is validated as Core-only.
- Non-Core integrations are blocked at boundary.

### 4) Deterministic error format
All contract endpoint errors return:
```json
{
  "success": false,
  "error": "string",
  "request_id": "string",
  "timestamp": "ISO8601"
}
```

### 5) Deterministic success format
All contract endpoint success responses return:
```json
{
  "success": true,
  "request_id": "string",
  "timestamp": "ISO8601",
  "data": {}
}
```

## Validation/Rejection Matrix
- Unknown field -> `422`
- Type/schema violation -> `422`
- Integration boundary violation -> `400`
- Payload too large -> `400`
- Invalid lineage -> `400`
- Artifact not found (read) -> `404`
- Internal unexpected failure -> `500`

## Implementation Notes
- Append-only storage internals were not changed.
- Hash authority remains server-computed.
- Legacy endpoints are preserved for backward compatibility.
- Contract endpoints are the canonical Core integration boundary.

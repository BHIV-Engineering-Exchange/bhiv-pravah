# VALIDATION_RULES

## Enforced Rejection Rules (Contract Endpoints)

Applies to:
- `POST /bucket/artifacts/write`
- `POST /bucket/artifacts/read`
- `POST /bucket/artifacts/query`
- `POST /bucket/audit/read`

## Rule 1: Invalid Schema
Detection:
- Missing required fields
- Wrong field types
- Invalid numeric bounds (`limit`, `offset`)

Result:
- HTTP `422`
- Standard error response:
```json
{
  "success": false,
  "error": "body -> field: <reason>",
  "request_id": "uuid",
  "timestamp": "ISO8601"
}
```

## Rule 2: Unknown Fields
Detection:
- Any field not declared in contract request models.

Mechanism:
- Pydantic `extra="forbid"`.

Result:
- HTTP `422`
- Standard error response.

## Rule 3: Oversized Payload
Applies:
- `/bucket/artifacts/write` (`artifact.payload`).

Mechanism:
- Serialized payload byte size check.
- Max allowed: `16 * 1024 * 1024` bytes.

Result:
- HTTP `400`
- Error: `Payload size <n> exceeds limit <max>`.

## Rule 4: Invalid Lineage
Applies:
- `/bucket/artifacts/write`.

Mechanism:
- If chain empty: `parent_hash` must be null.
- If chain non-empty: `parent_hash` must equal current chain `last_hash`.

Result:
- HTTP `400`
- Error code semantics: `invalid_lineage`.

## Rule 5: Integration Boundary Violation
Mechanism:
- `integration_id` must be Core-only (`core`, `bhiv_core`, `bhiv-core`, or Core-prefixed).

Result:
- HTTP `400`
- Error: `Integration boundary violation: only Core integration is allowed`.

## Rule 6: Not Found
Applies:
- `/bucket/artifacts/read`.

Result:
- HTTP `404`
- Error: `artifact_not_found`.

## Rule 7: Internal Failure
Result:
- HTTP `500`
- Error: `internal_server_error`.

## Determinism Requirements
- Server computes and owns hash values.
- Bucket does not execute payloads.
- Validation occurs before write.
- Rejections are deterministic and logged.

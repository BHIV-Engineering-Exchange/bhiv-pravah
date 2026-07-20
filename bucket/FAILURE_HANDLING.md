# FAILURE_HANDLING

## Failure Handling Plan

## Case A: Invalid Request Schema
Example:
- Missing required `artifact` in write request.
Expected:
- HTTP `422`
- Standard error envelope.

## Case B: Unknown Field Rejection
Example:
- Add `unexpected_field` to request body.
Expected:
- HTTP `422`
- Field-level validation message.

## Case C: Integration Boundary Violation
Example:
- `integration_id = "external_system"`.
Expected:
- HTTP `400`
- Error indicates Core-only boundary.

## Case D: Oversized Payload
Example:
- Payload > 16MB.
Expected:
- HTTP `400`
- Explicit payload-size rejection.

## Case E: Invalid Lineage
Example:
- Non-matching `parent_hash`.
Expected:
- HTTP `400`
- Invalid lineage rejection.

## Case F: Read Missing Artifact
Example:
- Unknown `artifact_id`.
Expected:
- HTTP `404`
- `artifact_not_found`.

## Case G: Internal Failure
Example:
- Unhandled runtime exception in endpoint.
Expected:
- HTTP `500`
- `internal_server_error`.

## Partial Write Safety
- Validation occurs before append-only write.
- Storage write is append-only and fsync-backed.
- If validation fails, write does not occur.
- If storage write fails, endpoint returns failure response.

## Suggested curl checks
```bash
curl -X POST http://localhost:8000/bucket/artifacts/write -H "Content-Type: application/json" -d "{}"
curl -X POST http://localhost:8000/bucket/artifacts/read -H "Content-Type: application/json" -d '{"requester_id":"core","integration_id":"bhiv_core","artifact_id":"missing"}'
```

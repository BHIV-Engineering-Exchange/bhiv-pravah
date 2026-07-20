# Sarathi Approval Integration Spec

## Scope
This document describes the live approval-related runtime surfaces already present in the repository and how SETU should integrate with them without introducing a new approval system or hidden authority.

The repository contains two relevant approval surfaces:

1. SETU execution ingress for approval intents: [backend/setu/routes.py](backend/setu/routes.py)
2. Business approval mutation for procurement: [backend/customer_portal_api.py](backend/customer_portal_api.py)

The trace and tenant continuity gate for SETU is enforced by [backend/setu/trace_continuity_middleware.py](backend/setu/trace_continuity_middleware.py) and [backend/setu/trace_continuity.py](backend/setu/trace_continuity.py).

## Endpoint URLs

### SETU runtime ingress
- `POST /setu/route`
- `GET /setu/lineage/{trace_id}`
- `GET /setu/telemetry/{trace_id}`

These routes are defined by [backend/setu/routes.py](backend/setu/routes.py) with an `APIRouter(prefix="/setu")`.

### Business approval mutation currently implemented in the repo
- `PUT /admin/procurement/{procurement_id}/approve`

This endpoint is implemented in [backend/customer_portal_api.py](backend/customer_portal_api.py) and is the repository’s concrete approval action that marks procurement as approved and creates a purchase order.

## Authentication Method

### SETU routes
- Authentication is JWT Bearer auth via `get_current_user` from [backend/auth_system.py](backend/auth_system.py).
- The dependency extracts `Authorization: Bearer <token>` using FastAPI `HTTPBearer`.

### Business approval mutation
- The same `get_current_user` dependency is used.
- The current route does not add an additional role-check dependency; it is authenticated but not separately role-gated in code.

## Authorization Middleware

The repository does not define a separate approval authorization middleware for the procurement approval endpoint.

What is actually present:
- `get_current_user` in [backend/auth_system.py](backend/auth_system.py) performs JWT validation and returns the authenticated user.
- `TraceContinuityMiddleware` in [backend/setu/trace_continuity_middleware.py](backend/setu/trace_continuity_middleware.py) validates SETU execution contracts on `/setu/*` POST/PUT/PATCH requests, but it is a continuity gate, not a role-based auth layer.

## Request Contract

### Accepted SETU request body shapes
The SETU validator accepts any of these payload forms:
- raw execution object
- `{ "execution": { ... } }`
- `{ "execution_contract": { ... } }`

This behavior is implemented by `extract_execution` in [backend/setu/trace_continuity.py](backend/setu/trace_continuity.py) and mirrored in [backend/setu/trace_continuity_middleware.py](backend/setu/trace_continuity_middleware.py).

### Required fields
The live SETU execution contract requires these fields:
- `execution_id`
- `trace_id`
- `source_system`
- `actor`
- `intent_type`
- `target_system`
- `parameters`
- `priority`
- `timestamp`
- `schema_version`
- `tenant_id`

These are enforced in [backend/setu/trace_continuity.py](backend/setu/trace_continuity.py) and in the JSON schema at [contracts/execution/execution_contract_v1.json](contracts/execution/execution_contract_v1.json).

### Contract shape used for approval intent
The repository’s runtime proof uses this approval intent shape:
- `intent_type`: `approve_order`
- `target_system.system_id`: `sarathi`
- `priority`: `3`
- `schema_version`: `1.0`
- `governance.gated_bridge.status`: `approved`

The concrete example is captured in [end_to_end_trace.json](end_to_end_trace.json).

## Response Contract

### Success response from `POST /setu/route`
When the routed execution passes continuity and governance checks, the router returns:

```json
{
  "ok": true,
  "mode": "observe_only",
  "routing": { "ok": true, "sarathi_payload": "generated", "bhiv_envelope": "generated" },
  "lineage_events": [],
  "telemetry_events": []
}
```

The real route response shape is defined in [backend/setu/routes.py](backend/setu/routes.py). The proof payload values are recorded in [SOVEREIGN_ROUTING_PROOF.md](SOVEREIGN_ROUTING_PROOF.md).

### Rejection response from `POST /setu/route`
If governance blocks the request, the route returns HTTP `403` with:

```json
{
  "ok": false,
  "mode": "blocked",
  "reason": "gated_bridge_not_approved",
  "details": "pending",
  "telemetry_event": { ... },
  "lineage_event": { ... }
}
```

If the execution contract is invalid, the route returns HTTP `400`.

### Error response from trace continuity middleware
The middleware returns JSON in this shape for validation failures:

```json
{
  "success": false,
  "error": "<code>",
  "message": "<human readable message>",
  "details": { ... }
}
```

This is the actual payload emitted by [backend/setu/trace_continuity.py](backend/setu/trace_continuity.py) and [backend/setu/trace_continuity_middleware.py](backend/setu/trace_continuity_middleware.py).

### Business approval mutation response
The procurement approval endpoint returns:

```json
{
  "success": true,
  "procurement_id": "<id>",
  "purchase_order_id": "<po_id>",
  "message": "Procurement approved and PO sent to supplier"
}
```

That is the live response in [backend/customer_portal_api.py](backend/customer_portal_api.py).

## Trace Propagation Rules

1. `trace_id` is immutable across the execution chain.
2. `tenant_id` must remain constant across lineage.
3. `trace_lineage.root_trace_id`, when present, must equal `trace_id`.
4. `trace_lineage.parent_execution_id` must point to a prior execution with the same `trace_id` and `tenant_id`.
5. `lineage_hash` must match the deterministic hash computed from `execution_id`, `trace_id`, `tenant_id`, `root_trace_id`, `parent_trace_id`, and `parent_execution_id`.
6. SETU response headers are stamped on successful continuity validation:
   - `X-SETU-Execution-Id`
   - `X-SETU-Trace-Id`
   - `X-SETU-Tenant-Id`
   - `X-SETU-Lineage-Hash`
7. The route layer also exposes `req.getSetuTraceHeaders()` and sets `X-SETU-*` headers on the response in [backend/setu/trace_continuity.py](backend/setu/trace_continuity.py) and [backend/setu/trace_continuity_middleware.py](backend/setu/trace_continuity_middleware.py).

## Runtime Proof

### Approval request example
Source: [end_to_end_trace.json](end_to_end_trace.json)

```json
{
  "execution_contract": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "source_system": "tantra",
    "actor": {
      "actor_id": "user_4721",
      "actor_type": "user"
    },
    "intent_type": "approve_order",
    "target_system": {
      "system_id": "sarathi",
      "system_type": "routing"
    },
    "parameters": {
      "order_id": "ORD_44821",
      "approval_level": "ops"
    },
    "priority": 3,
    "timestamp": "2026-05-29T12:00:02Z",
    "schema_version": "1.0",
    "tenant_id": "tenant_sampada_001",
    "trace_lineage": {
      "root_trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
      "lineage_hash": "2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88"
    },
    "provenance": {
      "recorded_by": "setu",
      "recorded_at": "2026-05-29T12:00:02Z"
    },
    "replay": {
      "idempotency_key": "idem_44821_ops",
      "sequence": 1,
      "determinism_fingerprint": "f8de74a1f0a9d27d6f3f5cf532b85e90"
    },
    "governance": {
      "gated_bridge": {
        "status": "approved",
        "attestation_id": "att_8811",
        "checked_at": "2026-05-29T12:00:06Z",
        "policy_id": "gov_exec_v1",
        "policy_version": "1.0"
      }
    }
  }
}
```

### Approval success example
Source: [SOVEREIGN_ROUTING_PROOF.md](SOVEREIGN_ROUTING_PROOF.md)

```json
{
  "ok": true,
  "sarathi_payload": "generated",
  "bhiv_envelope": "generated",
  "governance": {
    "gated_bridge": {
      "status": "approved",
      "attestation_id": "att_8811"
    }
  }
}
```

The associated trace evidence is also present in [TELEMETRY_PROOF.md](TELEMETRY_PROOF.md).

### Approval rejection example
Source: [TRACE_CONTINUITY_PROOF.md](TRACE_CONTINUITY_PROOF.md) and [SOVEREIGN_ROUTING_PROOF.md](SOVEREIGN_ROUTING_PROOF.md)

```json
{
  "success": false,
  "error": "trace_id_regenerated",
  "message": "Trace ID regeneration detected",
  "details": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "expected_trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "received_trace_id": "trace_9999_bad"
  }
}
```

```json
{
  "ok": false,
  "reason": "gated_bridge_not_approved",
  "details": "pending"
}
```

### Logs showing trace continuity
Source: [TRACE_CONTINUITY_PROOF.md](TRACE_CONTINUITY_PROOF.md) and [end_to_end_trace.json](end_to_end_trace.json)

```json
{"event":"trace_continuity_ok","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","lineage_hash":"2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88","timestamp":"2026-05-29T12:00:03Z"}
{"event":"trace_continuity_ok","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","lineage_hash":"2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88","timestamp":"2026-05-29T12:00:08Z","downstream":"sarathi"}
```

The end-to-end trace also shows lineage events recorded under the same `execution_id`, `trace_id`, and `tenant_id` across the approval chain.

## Integration Notes

- The SETU ingress is observe-only at the router level; it does not introduce a new approval authority.
- Governance rejection is emitted as telemetry and lineage events instead of silently mutating state.
- If SETU is mounted into the host app, it must preserve the `TraceContinuityMiddleware` on `/setu/*` mutation paths so trace and tenant checks run before business logic.
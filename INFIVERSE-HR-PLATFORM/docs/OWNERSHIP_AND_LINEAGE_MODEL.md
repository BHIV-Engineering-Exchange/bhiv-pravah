# Ownership and Lineage Model

**Owner**: Rishabh Yadav

## Lineage Envelope (required on cross-system signals)

| Field | Description |
|-------|-------------|
| origin_system | System that originated the signal |
| owning_system | Authoritative data owner |
| schema_version | Contract version |
| trace_id | End-to-end trace |
| correlation_id | Request/flow correlation |
| trust_classification | canonical \| derived \| observed \| challenged |
| visibility_scope | platform \| tenant \| org \| department \| restricted |

## Implementation

- Module: `backend/services/gateway/app/lineage_envelope.py`
- Attached to: workforce entities, policy evaluations, decisions, SETU signals, audit logs

## Propagation

- Gateway `X-Correlation-ID` middleware sets `request.state.correlation_id`
- Workforce governance routes pass correlation ID into all write operations
- Audit logs store `trace_id` and `correlation_id` at top level

## Example

```json
{
  "lineage": {
    "origin_system": "niyantran",
    "owning_system": "niyantran",
    "schema_version": "1.0.0",
    "trace_id": "trace-abc",
    "correlation_id": "cid-abc",
    "trust_classification": "observed",
    "visibility_scope": "tenant"
  }
}
```

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Missing required envelope fields at construction | 422 | Pydantic validation error on `LineageEnvelope` | No |
| Mismatched `owning_system` vs signal type | 200 | Defaults applied via `OWNERSHIP_BY_TYPE`; no hard error | No |
| Invalid `trust_classification` value | 422 | Pydantic validation error | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| Lineage envelope attachment | N/A (metadata) | Every workforce/governance write via `attach_lineage` or `LineageEnvelope.from_request` | Yes |
| `visibility_scope` on event | tenant / platform | Set on every lineage envelope | Yes |

No standalone audit action — lineage is embedded in workforce and governance audit entries.

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 1,
  "events": [
    {
      "action": "organization_create",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00",
      "lineage": {
        "origin_system": "gateway",
        "owning_system": "sampada",
        "schema_version": "1.0.0",
        "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
        "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
        "trust_classification": "canonical",
        "visibility_scope": "tenant"
      }
    }
  ]
}
```

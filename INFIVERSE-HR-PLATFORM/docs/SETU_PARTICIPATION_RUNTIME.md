# SETU Participation Runtime

**Owner**: Rishabh Yadav

## Participation Contracts

| Signal Type | Owning System | Schema Reference |
|-------------|---------------|------------------|
| niyantran_telemetry | niyantran | `docs/schemas/execution_telemetry.json` |
| artha_payroll_visibility | artha | `docs/schemas/payroll_visibility.json` |
| crm_participation | crm | SETU convergence map |
| setu_aggregation | setu | SETU convergence map |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/setu/signals/{signal_type}` | Ingest participation signal |
| GET | `/v1/setu/signals` | List signals (scoped) |
| GET | `/v1/setu/trace/{trace_id}` | Trace continuity across signals + audits |

## Required Metadata

- ownership metadata (via LineageEnvelope)
- source_declaration
- correlation_id
- lineage references
- trace continuity (shared trace_id)

## Sample Niyantran Telemetry Ingest

```json
{
  "payload": { "event": "task_completed", "task_id": "t-001" },
  "workforce_ref_id": "wf-abc123",
  "source_declaration": "Niyantran execution telemetry",
  "origin_system": "niyantran",
  "trust_classification": "observed"
}
```

## Storage

MongoDB collection: `setu_signals`

Evidence: `evidence/workforce_runtime/setu_signal_proof.json`

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Unknown `signal_type` in path | 422 | signal_type must be one of: [...] | No |
| Missing required ingest body fields | 422 | FastAPI validation error | No |
| Trace ID with no matching signals | 200 | signal_count: 0 (empty continuity, not error) | No |
| Caller lacks workforce role | 403 | Workforce APIs require client, recruiter, or admin role | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `setu_signal_niyantran_telemetry` | ingested | After niyantran signal insert | Yes |
| `setu_signal_artha_payroll_visibility` | ingested | After artha signal insert | Yes |
| `setu_signal_crm_participation` | ingested | After CRM signal insert | Yes |
| `setu_signal_setu_aggregation` | ingested | After SETU aggregation signal insert | Yes |

Ownership is always derived from `OWNERSHIP_BY_TYPE` when not explicitly supplied.

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 3,
  "events": [
    {
      "action": "setu_signal_niyantran_telemetry",
      "outcome": "ingested",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00",
      "signal_id": "sig-f25fd8f6c7bb"
    },
    {
      "action": "setu_signal_artha_payroll_visibility",
      "outcome": "ingested",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "95348dd7-3d50-41ef-90c7-0a17652055a3",
      "created_at": "2026-06-08T06:50:44.000000+00:00",
      "signal_id": "sig-0edf86a54492"
    },
    {
      "action": "setu_trace_continuity",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00",
      "signal_count": 1
    }
  ]
}
```

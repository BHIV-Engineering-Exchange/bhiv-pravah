# Decision Ledger Model

**Owner**: Rishabh Yadav

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| decision_id | string | Unique decision identifier |
| owner | string | Decision owner (human/system) |
| scope | string | Tenant/org scope |
| rationale | string | Why the decision was made |
| inputs | object | Input context |
| timestamp | datetime | When recorded |
| dependencies | string[] | Related decision IDs |
| status | string | active, superseded |
| supersedes | string | Prior decision_id replaced |
| trace_references | string[] | Correlation/trace IDs |

## Storage

MongoDB collection: `decisions` (append-only; supersession via `supersedes` link)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/decisions` | Record decision |
| GET | `/v1/decisions` | List decisions (scoped) |
| GET | `/v1/decisions/{id}` | Get decision |
| GET | `/v1/decisions/replay` | Reconstruct chain |

## Replay Reconstruction

1. **supersedes_chain**: Start at `decision_id`, follow `supersedes` backward
2. **correlation_timeline**: All decisions sharing `correlation_id` sorted by timestamp

## Sample Entries

```json
{
  "decision_id": "dec-a1b2c3",
  "owner": "Rishabh Yadav",
  "scope": "TECH001",
  "rationale": "Visibility challenge upheld — scope corrected",
  "status": "active",
  "trace_references": ["cid-uuid-1"]
}
```

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| `supersedes` references missing decision | 404 | Prior decision not found | No |
| Decision lookup by ID not found | 404 | Decision not found | No |
| Missing required fields (`owner`, `rationale`) | 422 | FastAPI validation error | No |
| Replay with unknown correlation_id | 200 | Empty decisions list (not an error) | No |
| Review not found when recording from review | 404 | Review not found | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `decision_record` | recorded | After decision document insert | Yes |

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 2,
  "events": [
    {
      "action": "decision_record",
      "outcome": "recorded",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00",
      "decision_id": "dec-abc123",
      "supersedes": null
    },
    {
      "action": "decision_record",
      "outcome": "recorded",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00",
      "decision_id": "dec-def456",
      "supersedes": "dec-abc123"
    }
  ]
}
```

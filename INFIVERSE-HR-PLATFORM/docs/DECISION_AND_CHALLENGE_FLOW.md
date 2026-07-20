# Decision and Challenge Flow

**Owner**: Rishabh Yadav

## Challenge Lifecycle

```
open → under_review → resolved | rejected
```

| Status | Meaning |
|--------|---------|
| open | Challenge filed against policy evaluation |
| under_review | Review assigned |
| resolved | Review upheld challenge |
| rejected | Review rejected challenge |

## Review Lifecycle

```
assigned → completed
```

## Override Lifecycle

```
proposed → applied | rejected
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/governance/challenges` | Create challenge |
| GET | `/v1/governance/challenges` | List challenges |
| POST | `/v1/governance/reviews` | Assign review |
| POST | `/v1/governance/reviews/{id}/complete` | Complete review |
| POST | `/v1/governance/overrides` | Record workflow override |
| POST | `/v1/governance/overrides/{id}/apply` | Apply override |
| POST | `/v1/governance/reviews/{id}/decision` | Record decision from review |

## Sample Challenge

```json
{
  "policy_key": "visibility_policy",
  "evaluation_id": "peval-abc123",
  "reason": "Scope boundary appears incorrect for department view"
}
```

## Collections

- `challenges` — challenge records
- `reviews` — review assignments and outcomes
- `workflow_overrides` — override proposals and applied state

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Challenge ID not found | 404 | Challenge not found | No |
| Review assigned to closed challenge | 409 | Challenge not open for review | No |
| Review ID not found on complete | 404 | Review not found | No |
| Override ID not found on apply | 404 | Override not found | No |
| Missing required challenge body fields | 422 | FastAPI validation error | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `challenge_create` | open | After challenge insert | Yes |
| `review_assign` | assigned | After review insert and challenge status update | Yes |
| `workflow_override_record` | proposed | After workflow override insert | Yes |

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 3,
  "events": [
    {
      "action": "challenge_create",
      "outcome": "open",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00"
    },
    {
      "action": "review_assign",
      "outcome": "assigned",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:44.000000+00:00"
    },
    {
      "action": "workflow_override_record",
      "outcome": "proposed",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00"
    }
  ]
}
```

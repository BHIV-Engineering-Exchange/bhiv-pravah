# Policy Engine Runtime

**Owner**: Rishabh Yadav

## Components

| Component | Collection | Purpose |
|-----------|------------|---------|
| Policy Registry | `policy_registry` | Tenant policy index |
| Policy Definitions | `policy_definitions` | Versioned rules |
| Policy Evaluation | `policy_evaluations` | Evaluation results |
| Policy Override | `policy_overrides` | Explicit overrides |
| Policy Audit | `audit_logs` | `policy_evaluate`, `policy_override` events |

## Example Policies (seeded)

1. **leave_policy** — tenure-based leave observation
2. **visibility_policy** — scope-match visibility
3. **growth_policy** — derived growth signal bounds
4. **approval_policy** — explicit approval required
5. **retention_policy** — retention boundaries

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/policies/seed` | Seed example policies for tenant |
| GET | `/v1/policies/definitions` | List policy definitions |
| POST | `/v1/policies/definitions` | Create policy definition |
| POST | `/v1/policies/evaluate` | Evaluate policy against context |
| POST | `/v1/policies/overrides` | Record policy override |

## Sample Evaluate Request

```json
{
  "policy_key": "leave_policy",
  "context": { "tenure_days": 120 },
  "employee_id": "<employee_id>",
  "organization_id": "<org_id>"
}
```

## Sample Evaluate Response

```json
{
  "evaluation_id": "peval-abc123",
  "policy_key": "leave_policy",
  "result": { "decision": "allow", "effect": "observe", "rationale": "policy=leave_policy" },
  "correlation_id": "<uuid>"
}
```

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Unknown `policy_key` at evaluate | 404 | Policy definition not found | No |
| Missing required evaluate body fields | 422 | FastAPI validation error | No |
| Caller lacks workforce role (non-client/recruiter/admin) | 403 | Workforce APIs require client, recruiter, or admin role | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `policy_evaluate` | allow / deny / observe (from evaluation result) | After successful policy evaluation insert | Yes |
| `policy_override` | recorded | After policy override document insert | Yes |

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 3,
  "events": [
    {
      "action": "policy_seed",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00"
    },
    {
      "action": "policy_evaluate",
      "outcome": "allow",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:44.000000+00:00"
    },
    {
      "action": "policy_override",
      "outcome": "recorded",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00"
    }
  ]
}
```

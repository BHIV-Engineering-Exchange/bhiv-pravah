# Workforce Lifecycle API

**Owner**: Rishabh Yadav

## Lifecycle States

`draft` → `onboarding` → `active` → (`role_change_pending` | `transfer_pending` | `offboarding_prep` | `inactive`) → `offboarded`

## Endpoints

| Method | Path | Action |
|--------|------|--------|
| POST | `/v1/workforce/employees/{id}/lifecycle/onboard` | Start onboarding |
| POST | `/v1/workforce/employees/{id}/lifecycle/onboard-complete` | Complete onboarding → active |
| POST | `/v1/workforce/employees/{id}/lifecycle/role-move` | Role movement (requires `new_role`) |
| POST | `/v1/workforce/employees/{id}/lifecycle/department-transfer` | Transfer (requires `new_department_id`) |
| PATCH | `/v1/workforce/employees/{id}/lifecycle/status` | Status change (requires `target_state`) |
| POST | `/v1/workforce/employees/{id}/lifecycle/offboard-prepare` | Offboarding preparation |

## Sample Payload — Role Move

```json
{
  "new_role": "senior_analyst",
  "reason": "Promotion after review"
}
```

## Failure Cases

| Case | HTTP | Detail |
|------|------|--------|
| Invalid transition | 409 | e.g. draft → active without onboarding |
| Employee not found | 404 | Wrong ID or cross-tenant access |
| Department not found | 404 | Invalid `new_department_id` |
| Missing required field | 422 | e.g. role-move without `new_role` |
| Unauthorized role | 403 | candidate role blocked |

## Audit Logging

Every transition writes `governance` event to `audit_logs` with `prior_state`, `new_state`, `correlation_id`.

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Invalid lifecycle transition (e.g. `active` → `draft`) | 409 | Invalid transition from {prior} to {new} | No |
| Employee not found for transition | 404 | Employee not found | No |
| Onboarding from invalid state | 409 | Onboarding only allowed from draft or inactive | No |
| Missing `new_role` on role movement | 422 | new_role is required | No |
| Missing `new_department_id` on transfer | 422 | new_department_id is required | No |
| Department not found on transfer | 404 | Department not found | No |
| Missing `target_state` on status change | 422 | Valid target_state is required | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `employee_onboard` | success | Valid draft/inactive → onboarding transition | Yes |
| `employee_role_move` | success | Role change applied | Yes |
| `employee_department_transfer` | success | Department transfer applied | Yes |
| `employee_status_change` | success | Lifecycle state change applied | Yes |
| `employee_offboard_prepare` | success | Offboarding preparation applied | Yes |

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 3,
  "events": [
    {
      "action": "employee_onboard",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00"
    },
    {
      "action": "employee_status_change",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:44.000000+00:00"
    },
    {
      "action": "employee_status_change",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00"
    }
  ]
}
```

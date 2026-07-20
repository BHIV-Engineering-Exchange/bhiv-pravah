# Federated Workforce Runtime

**Owner**: Rishabh Yadav | **Status**: Runtime live in gateway

## Overview

Live workforce identity and organization hierarchy runtime for Sampada. Recruitment entities (`candidates`, `jobs`) remain separate from workforce entities (`employees`, `organizations`).

## MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `organizations` | Top-level org units with tenant isolation |
| `divisions` | Divisions under organizations |
| `units` | Units under divisions |
| `departments` | Departments with team structures |
| `employees` | Federated workforce records |

## Entity Schemas

### Organization
- `name`, `code`, `parent_organization_id`, `default_roles`, `status`, `tenant_id`, `lineage`

### Division
- `organization_id`, `name`, `code`, `status`, `tenant_id`, `lineage`

### Unit
- `division_id`, `name`, `code`, `status`, `tenant_id`, `lineage`

### Department
- `organization_id`, `unit_id`, `name`, `code`, `teams[]`, `default_roles[]`, `status`, `tenant_id`, `lineage`

### Employee
- `workforce_ref_id`, `organization_id`, `department_id`, `unit_id`
- `workforce_type`: contractor | employee | consultant | advisor | intern | vendor_workforce
- `role`, `inherited_roles[]`, `lifecycle_state`, `display_name`, `email`
- `local_system_id`, `source_system`, `tenant_id`, `lineage`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/workforce/organizations` | Create organization |
| GET | `/v1/workforce/organizations` | List organizations (scoped) |
| GET | `/v1/workforce/organizations/{id}` | Get organization |
| GET | `/v1/workforce/organizations/{id}/hierarchy` | Full hierarchy tree |
| POST | `/v1/workforce/divisions` | Create division |
| GET | `/v1/workforce/divisions` | List divisions |
| POST | `/v1/workforce/units` | Create unit |
| GET | `/v1/workforce/units` | List units |
| POST | `/v1/workforce/departments` | Create department |
| GET | `/v1/workforce/departments` | List departments |
| POST | `/v1/workforce/employees` | Create employee |
| GET | `/v1/workforce/employees` | List employees |
| GET | `/v1/workforce/employees/{id}` | Get employee |
| GET | `/v1/workforce/trace-replay` | Workforce audit trace replay |

## Sample Payload — Create Employee

```json
{
  "organization_id": "<org_id>",
  "department_id": "<dept_id>",
  "workforce_type": "contractor",
  "role": "analyst",
  "display_name": "A. Sharma",
  "lifecycle_state": "draft"
}
```

## Trace / Replay Proof

1. Create org → division → department → employee (note `X-Correlation-ID` header).
2. `GET /v1/workforce/trace-replay?correlation_id=<cid>`
3. Verify audit events: `organization_create`, `employee_create`, etc.

Evidence: `evidence/workforce_runtime/api_proof_workforce.json`

---

### Failure Cases

| Scenario | HTTP Status | Error Detail | Audit Event Written |
|----------|-------------|--------------|---------------------|
| Invalid `workforce_type` on employee create | 422 | workforce_type must be one of: [...] | No |
| Invalid `lifecycle_state` on employee create | 422 | lifecycle_state must be one of: [...] | No |
| Organization not found (missing or cross-tenant) | 404 | Organization not found | No |
| Department not found on employee create | 404 | Department not found | No |
| Caller lacks workforce role | 403 | Workforce APIs require client, recruiter, or admin role | No |
| Cross-tenant org read / hierarchy | 404 | Organization not found | No |

---

### Audit Events

| Action | Outcome Values | When Fired | Correlation ID Propagated |
|--------|---------------|------------|--------------------------|
| `organization_create` | success | After organization insert | Yes |
| `division_create` | success | After division insert | Yes |
| `department_create` | success | After department insert | Yes |
| `employee_create` | success | After employee insert | Yes |

---

### Replay Example

```json
{
  "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
  "event_count": 3,
  "events": [
    {
      "action": "organization_create",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:43.132018+00:00"
    },
    {
      "action": "division_create",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:44.000000+00:00"
    },
    {
      "action": "employee_create",
      "outcome": "success",
      "correlation_id": "9a83b441-e387-4e26-aeb2-2616e86d2762",
      "trace_id": "f6f72b52-57ed-4ddf-a5c1-43379364c180",
      "created_at": "2026-06-08T06:50:45.000000+00:00"
    }
  ]
}
```

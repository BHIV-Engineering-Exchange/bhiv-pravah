# Central Control API Contract Freeze

Status: active (verified localhost 2026-06-03; Render production 2026-06-06 — 33/33 comprehensive evaluation)
Owner: Rishabh Yadav
Support Builder: Shashank
**Updated:** 2026-06-06

## Scope

This contract freeze defines the live API surfaces used by central control so frontend wiring does not rely on mock sources.

## Approved Endpoints

- `GET /metrics/dashboard` (Gateway `:8000`)
  - Auth required (`Bearer` token or service API key)
  - Allowed roles: `client`, `recruiter`, `admin`
  - Response buckets:
    - `performance_summary`
    - `business_metrics`
    - `system_metrics`
  - Correlation header: `X-Correlation-ID`

- `GET /v1/candidates/stats` (Gateway `:8000`)
  - Auth required (`Bearer` token or service API key)
  - Allowed roles: `client`, `recruiter`, `admin`
  - Core fields:
    - `total_candidates`
    - `active_jobs`
    - `recent_matches`
    - `pending_interviews`
    - `new_candidates_this_week`
    - `total_feedback_submissions`
  - Correlation header: `X-Correlation-ID`

- `GET /health` (Agent `:9000`)
  - Read-only health probe
  - Used for service readiness only

- `GET /health` (LangGraph `:9001`)
  - Read-only health probe
  - Used for service readiness only

- `POST /v1/control-center/audit-events` (Gateway `:8000`)
  - Auth required (`Bearer` token or service API key)
  - Allowed roles: `client`, `recruiter`, `admin`
  - Stores control-center access, refresh, and fallback audit records

- `GET /v1/control-center/audit-replay` (Gateway `:8000`)
  - Auth required (`Bearer` token or service API key)
  - Query: optional `correlation_id`, `limit` (default 20)
  - Response: `events[]` (`ts`, `service`, `op`, `correlation_id`, `status`), `count`, `source`, `replay_mode`, `policy_scope`

- `GET /v1/control-center/dashboard-aggregates` (Gateway `:8000`)
  - Auth required (`Bearer` token or service API key)
  - Response: `hiring_funnel[]`, `department_load[]`, `policy_scope`, `generated_at`, `data_source`

- `GET /health` (Gateway `:8000`)
  - No auth required (used by `checkApiHealth` on load/refresh)

## Live wiring verification (2026-06-03)

Verified on localhost: Gateway `:8000`, Agent `:9000`, LangGraph `:9001` up; E2E suite `backend/tests/e2e/control_center/run_control_center_e2e.py` — **8 passed, 2 skipped** (JWT role-matrix tests skipped without `JWT_SECRET_KEY` / `CANDIDATE_JWT_SECRET_KEY`).

| Frontend (`api.ts`) | HTTP | Gateway path | Verified | Notes |
|---------------------|------|--------------|----------|-------|
| `checkApiHealth` | GET | `/health` | Y | No Bearer required; `ControlCenter` load step 1 |
| `fetchGatewayMetricsDashboard` | GET | `/metrics/dashboard` | Y | Bearer via axios interceptor; 401 without auth |
| `fetchGatewayCandidateStats` | GET | `/v1/candidates/stats` | Y | Scoped stats; `assert_control_center_access` |
| `fetchControlCenterDashboardAggregates` | GET | `/v1/control-center/dashboard-aggregates` | Y | Funnel + department load in UI |
| `fetchControlCenterAuditReplay` | GET | `/v1/control-center/audit-replay` | Y | Replay zone; optional `correlation_id` query |
| `postControlCenterAuditEvent` | POST | `/v1/control-center/audit-events` | Y | `control_center_view` + `control_center_refresh` |
| `fetchServiceHealth` | GET | Agent `/health` (`VITE_AGENT_SERVICE_URL`, default `:9000`) | Y | Direct axios; optional Bearer |
| `fetchServiceHealth` | GET | LangGraph `/health` (`VITE_LANGGRAPH_SERVICE_URL`, default `:9001`) | Y | Direct axios; optional Bearer |

UI gate: `VITE_ENABLE_CONTROL_CENTER=true` and roles `client` \| `recruiter` \| `admin` (`ControlCenter.tsx`). Gateway base: `VITE_API_BASE_URL` (default `http://localhost:8000`).

**Production (Vercel):** `VITE_API_BASE_URL`, `VITE_AGENT_SERVICE_URL`, `VITE_LANGGRAPH_SERVICE_URL` (not `VITE_LANGGRAPH_URL`), `VITE_ENABLE_CONTROL_CENTER=true`, `VITE_API_KEY`. See `frontend/VERCEL_DEPLOYMENT.md`.

**UI behavior:** parallel fetch on load/refresh; 30s silent background refresh (`CONTROL_CENTER_REFRESH_MS`).

Not called from UI (E2E only): `GET /v1/control-center/audit-events`.

## Governance visibility endpoints (Control Center panel)

Read-only endpoints used when `VITE_ENABLE_GOVERNANCE=true` (`ControlCenter.tsx` governance zone). All require Bearer auth; roles `client`, `recruiter`, `admin`. Verified live 2026-06-06.

| Frontend (`api.ts`) | HTTP | Gateway path | Verified | Notes |
|---------------------|------|--------------|----------|-------|
| `fetchWorkforceOrganizations` | GET | `/v1/workforce/organizations` | Y | Returns `items[]`, `policy_scope` |
| `fetchPolicyDefinitions` | GET | `/v1/policies/definitions` | Y | Returns `items[]`, `policy_scope` |
| `fetchGovernanceChallenges` | GET | `/v1/governance/challenges` | Y | Returns `items[]`, `policy_scope` |
| `fetchGovernanceDecisions` | GET | `/v1/decisions` | Y | Returns `items[]`, `policy_scope` |
| `fetchSetuSignals` | GET | `/v1/setu/signals` | Y | Returns `items[]`; `policy_scope` not yet in response body |
| `fetchWorkforceTraceReplay` | GET | `/v1/workforce/trace-replay` | Y | Returns `events[]`, `event_count` |

Write/mutation governance endpoints (`POST /v1/governance/*`, `POST /v1/policies/*`, `POST /v1/decisions`) are implemented on the gateway but are **not** invoked from the read-only control center UI. See `backend/services/gateway/routes/workforce_governance_routes.py`.

## Role-based access (verified live 2026-06-06)

| Role | `GET /metrics/dashboard` | `GET /v1/candidates/stats` | `GET /v1/governance/challenges` | Expected scope |
|------|--------------------------|----------------------------|-----------------------------------|----------------|
| API key | 200 | 200 | 200 | `platform_admin` |
| `admin` JWT | 200 | 200 | 200 | `platform` |
| `client` JWT | 200 | 200 | 200 | `client` |
| `recruiter` JWT | 200 | 200 | 200 | `recruiter` |
| `candidate` JWT | 403 | 403 | 403 | denied |

## Mock Surface Replacement Inventory

Replaced or bounded in central control:

- Static KPI cards -> live Gateway metrics and candidate stats mapping
- Service status badges -> live Agent/LangGraph health checks
- Funnel visualization -> `GET /v1/control-center/dashboard-aggregates` (`hiring_funnel`)
- Department load bars -> same aggregates endpoint (`department_load`)
- Replay/trace panel -> `GET /v1/control-center/audit-replay` (Mongo `audit_logs`, scoped)

## Security and Governance Notes

- Control center stays read-only.
- No execution or mutation workflows are introduced.
- Unauthorized role access returns `403` and UI fails closed.
- Correlation IDs are propagated for traceability.


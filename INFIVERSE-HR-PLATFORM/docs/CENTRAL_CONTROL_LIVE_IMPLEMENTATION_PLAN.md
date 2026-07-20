# Central Control Live Implementation Plan

> **Archive note (2026-06-03):** Implementation is **complete** per [CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md](CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md). This document is retained as historical scope and design rationale. For current API surfaces and verification, use [CENTRAL_CONTROL_API_CONTRACT_FREEZE.md](CENTRAL_CONTROL_API_CONTRACT_FREEZE.md) and [CONTROL_CENTER_E2E_TEST_FRAMEWORK.md](CONTROL_CENTER_E2E_TEST_FRAMEWORK.md).

**Owner**: Rishabh Yadav
**Support Builder**: Shashank
**Scope**: Task19 live central control wiring
**Status**: Complete — see execution checklist (production health verified; prod UI smoke open)

## 1. Goal

Replace the Control Center's static mock intelligence with authenticated live reads from the backend services while keeping the dashboard advisory, provenance-aware, and bounded by the governance documents.

The control center must remain read-only. It may observe, explain, and surface signals, but it must not infer execution authority.

## 2. Architectural Boundary

Live integration must stay inside these service boundaries:

- Gateway on `:8000` for aggregation, metrics, and protected API access
- Agent on `:9000` for AI service health and operational state
- LangGraph on `:9001` for workflow engine health and orchestration state

The frontend must not bypass the gateway for business data when a gateway route exists. Direct service calls are limited to health and readiness checks where no gateway equivalent is exposed.

## 3. Implementation Strategy

### Phase A - Live data wiring

- Replace hardcoded KPI arrays in the central control page with API-driven data models.
- Use the gateway metrics endpoint as the primary live data source.
- Add authenticated service health calls for Agent and LangGraph.
- Preserve the current command-center UX structure so the live implementation drops into the existing boundary.

### Phase A1 - Explicit card mapping

- Map gateway performance fields to fixed cards such as Avg Response Time, P95 Response Time, Error Rate, Total Requests, and Requests Per Minute.
- Map gateway candidate-stats fields to fixed cards such as Total Candidates, Active Jobs, Pending Interviews, Recent Matches, Applications Today, and New Candidates This Week.
- Map system metrics to fixed cards such as CPU Usage, Memory Usage, Disk Usage, Active Connections, and Current Active Users.
- Replay zone uses live `GET /v1/control-center/audit-replay` (Mongo `audit_logs`, scoped); advisory-only semantics retained.

### Phase B - Protection and gating

- Keep the control center behind authenticated role checks.
- Ensure every live request carries the current bearer token where applicable.
- Fail closed on unauthorized responses.
- Display a visible fallback state instead of silently fabricating values.

### Phase C - Explainability and provenance

- Label each dashboard zone with the source of its data.
- Surface last refresh time and partial-failure state.
- Keep replay and audit material visibly separated from live service metrics.

### Phase D - Audit and trace readiness (complete)

- Live audit write/read/replay: `POST/GET /v1/control-center/audit-events`, `GET /v1/control-center/audit-replay`.
- Frontend emits `control_center_view` / `control_center_refresh`; replay panel reads scoped audit logs only.

## 4. Technical Requirements

### Frontend

- Add environment support for the LangGraph base URL.
- Use a typed API helper for gateway metrics and service health calls.
- Poll live data on a bounded interval.
- Keep the control center read-only.

### API layer

- Reuse the gateway axios client for gateway metrics.
- Use auth-aware direct requests for service health endpoints.
- Normalize service health responses to a shared shape.
- Surface transport failures without crashing the dashboard.

### Data model

- Gateway metrics should expose performance, business, and system buckets.
- Service health should expose `status`, `service`, `version`, `timestamp`, and `environment` where available.
- Fallback states should identify the missing source.

## 5. Security Requirements

- Require signed-in access to the control center.
- Restrict the control center to the approved roles from the ownership matrix.
- Include bearer auth on gateway reads.
- Keep direct service calls narrow and read-only.
- Do not expose secrets, tokens, or mutable control actions in the dashboard.
- Log and display partial failures rather than masking them.

## 6. Governance Alignment

### Command center governance

- Separate observation, assessment, recommendation, decision, and execution visually.
- Keep executive summaries explicitly labeled as derived signals.
- Show source visibility and calculation context for live metrics.

### Policy governance

- Tag every visible live metric with its source bucket.
- Keep policy-sensitive metrics scoped to authorized roles only.
- Do not imply that the dashboard has approval authority.

### Human safety

- Avoid surveillance-style individual scoring.
- Keep workforce metrics aggregated where the safety model requires it.
- Preserve reviewability and challenge paths in the UI language.

## 7. Integration Points

| Service | Port | Purpose | Integration Method |
|---|---:|---|---|
| Gateway | 8000 | Protected metrics and business aggregation | `/metrics/dashboard`, `/health` |
| Agent | 9000 | AI service readiness | `/health` |
| LangGraph | 9001 | Workflow engine readiness | `/health` |

## 8. Execution Checklist

### API protection

- [x] Verify the control center is accessible only after auth loads.
- [x] Verify bearer tokens are attached to gateway requests.
- [x] Verify direct service calls are limited to health checks.
- [x] Verify 401 and 403 conditions fail closed (E2E + manual).

### Live data integration

- [x] Replace static KPI arrays with gateway metrics data.
- [x] Add live Agent status cards.
- [x] Add live LangGraph status cards.
- [x] Show last refresh time; 30s silent background refresh.
- [x] Surface partial-failure fallback states.
- [x] Replace the generic bucket extraction with explicit named cards for performance, hiring, workforce, growth, and org visibility.

### Governance compliance

- [x] Keep observation, assessment, recommendation, decision, and execution separated.
- [x] Show source labels for every live metric bucket.
- [x] Keep the replay panel clearly bounded as evidence, not authority.
- [x] Avoid any control action that mutates backend state.

### Audit and traceability

- [x] Preserve correlation-aware labels where the backend already provides them.
- [x] Record refresh and fallback states visibly.
- [x] Live audit-log endpoints integrated (see contract freeze).

## 9. Testing Plan

- [x] Typecheck the frontend after the API helper changes.
- [x] Validate the control center renders with a valid token.
- [x] Validate the control center shows fallback states when Agent or LangGraph are unavailable.
- [x] Validate unauthorized users are blocked (governance pytest + E2E when JWT set).
- [x] Validate the gateway metrics endpoint populates live values.
- [x] Validate the dashboard refresh re-fetches live data (manual + E2E pipeline).
- [ ] Production UI smoke on Vercel (checklist §F).

## 10. Deployment Steps

1. [x] Set `VITE_LANGGRAPH_SERVICE_URL` (and agent/gateway URLs) in local and Vercel — **not** `VITE_LANGGRAPH_URL`.
2. [x] Deploy API helpers and control center behind `VITE_ENABLE_CONTROL_CENTER=true`.
3. [x] Render backend health verified (2026-06-03).
4. [ ] Complete production UI smoke and prod JWT matrix (checklist §F).
5. [x] Localhost/E2E confirms read-only traffic patterns on control-center routes.

## 11. Exit Criteria

The central control implementation is complete when:

- The control center reads live data from the backend instead of static mock arrays.
- Gateway, Agent, and LangGraph are represented with live status.
- The dashboard remains read-only and role-gated.
- Live metrics and live audit replay are clearly separated (replay is advisory, from `audit_logs`).
- The control center can be refreshed without reintroducing mock data.

## 12. Known Follow-Up

- Production UI smoke and prod JWT role matrix on Render gateway.
- Extend policy-scope patterns beyond control-center routes platform-wide.
- If gateway metrics response shapes change, keep the frontend mapping layer tolerant.
- Any new privileged action surface must be reviewed against the ownership matrix before release.
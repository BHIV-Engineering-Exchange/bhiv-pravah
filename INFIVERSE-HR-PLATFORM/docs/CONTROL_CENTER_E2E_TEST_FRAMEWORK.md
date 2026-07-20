# Control Center E2E Test Framework

**Updated:** 2026-06-06

End-to-end validation of the Control Center data-flow pipeline on **localhost**: environment preflight → baseline capture → pipeline actions (audit + stats refresh) → final capture → state comparison → role matrix and routing checks.

Production deployment (Render + Vercel) is documented in `frontend/VERCEL_DEPLOYMENT.md` and `docs/CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md` §F. For production API + RBAC + governance reads, use `run_comprehensive_evaluation.py` (see below). Manual UI smoke is still required.

**Latest production run (2026-06-06):** `run_comprehensive_evaluation.py` — **33/33 passed**.

## Prerequisites

| Service | Default URL |
|---------|-------------|
| Gateway | `http://localhost:8000` |
| Agent (optional health) | `http://localhost:9000` |
| LangGraph (optional health) | `http://localhost:9001` |
| Frontend | Optional — API tests do not require Vite |

Start gateway (and Mongo if you want direct `audit_logs` counts):

```bash
# Example — use your project's usual start commands
cd backend/services/gateway && uvicorn app.main:app --port 8000
```

## Required environment variables

| Variable | Purpose |
|----------|---------|
| `API_KEY_SECRET` (or `API_KEY`) | Bearer token for admin/platform E2E calls |
| `GATEWAY_URL` | Default `http://localhost:8000` |

## Optional environment variables

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Mint client/admin JWT for role matrix |
| `CANDIDATE_JWT_SECRET_KEY` | Mint candidate/recruiter JWT (403 tests) |
| `MONGODB_URI` / `MONGO_URI` | Direct `audit_logs` count for integrity |
| `AGENT_URL` | Default `http://localhost:9000` |
| `LANGGRAPH_URL` | Default `http://localhost:9001` |
| `E2E_CLIENT_ID` / `E2E_CLIENT_PASSWORD` | Optional client JWT tests — **no default**; archived `TECH001`/`demo123` is not valid on production |
| `E2E_HTTP_TIMEOUT` | Request timeout seconds (default 30) |
| `E2E_RESULTS_DIR` | JSON report directory |

### Frontend (documented, not required for API E2E)

- `VITE_API_BASE_URL` — gateway base URL in dev (default `http://localhost:8000`)
- `VITE_ENABLE_CONTROL_CENTER=true` — enables `/control` UI
- `VITE_AGENT_SERVICE_URL` / `VITE_LANGGRAPH_SERVICE_URL` — direct `/health` probes from UI (defaults `:9000` / `:9001`)

## Live wiring verification (2026-06-03)

| UI function (`api.ts`) | Method | Path | Verified | Notes |
|------------------------|--------|------|----------|-------|
| `checkApiHealth` | GET | `/health` | Y | Gateway; no auth |
| `fetchGatewayMetricsDashboard` | GET | `/metrics/dashboard` | Y | E2E `api_key_metrics_dashboard` |
| `fetchGatewayCandidateStats` | GET | `/v1/candidates/stats` | Y | E2E + pipeline refresh |
| `fetchControlCenterDashboardAggregates` | GET | `/v1/control-center/dashboard-aggregates` | Y | Funnel/dept load |
| `fetchControlCenterAuditReplay` | GET | `/v1/control-center/audit-replay` | Y | Replay zone |
| `postControlCenterAuditEvent` | POST | `/v1/control-center/audit-events` | Y | View + refresh audit |
| `fetchServiceHealth` | GET | `{agent}/health`, `{langgraph}/health` | Y | Optional Bearer |

**Last run:** localhost — Gateway/Agent/LangGraph health 200; E2E **8 passed, 2 skipped** (~8s). Skips: `test_role_matrix_*` without JWT env. Report: `backend/tests/e2e/control_center/results/control_center_e2e_report.json`.

**Doc gap fixed:** use `VITE_AGENT_SERVICE_URL` / `VITE_LANGGRAPH_SERVICE_URL` (not `VITE_AGENT_URL`).

## Production comprehensive evaluation

From repository **`backend/`** directory (loads `backend/.env` automatically; requires `API_KEY_SECRET`, optional JWT secrets for RBAC):

```bash
python tests/e2e/control_center/run_comprehensive_evaluation.py
```

Covers: Render health, control center core, governance visibility reads, JWT role matrix (admin/client/recruiter/candidate), client vs recruiter scope isolation, Vercel bundle wiring.

Report: `backend/tests/e2e/control_center/results/control_center_comprehensive_evaluation_report.json`

Lighter smoke (API key only): `python tests/e2e/control_center/run_production_smoke.py`

## One-command run (localhost)

From repository **`backend/`** directory:

```bash
python tests/e2e/control_center/run_control_center_e2e.py
```

Equivalent pytest invocation:

```bash
cd backend
set API_KEY_SECRET=your-key-here
python -m pytest tests/e2e/control_center/test_control_center_e2e.py -v -m e2e
```

## Offline tests (no services)

```bash
cd backend
python -m pytest tests/e2e/control_center/test_control_center_offline.py tests/gateway/test_control_center_governance.py -v
```

## Package layout

```
backend/tests/e2e/control_center/
  conftest.py                 # fixtures, session JSON report
  test_control_center_e2e.py  # live localhost suite
  test_control_center_offline.py
  run_control_center_e2e.py   # runner script
  framework/
    config.py                 # E2EConfig.from_env()
    env_check.py              # preflight + service probe
    auth_helpers.py           # API key / JWT mint / client login
    state_capture.py          # baseline & final snapshots
    state_compare.py          # deltas & integrity rules
    pipeline_runner.py        # audit view + refresh proxy pipeline
    reporter.py               # per-test timing + JSON/console summary
  results/
    control_center_e2e_report.json   # written after session
```

## Endpoints validated (aligned with `frontend/src/services/api.ts`)

### Control center core

| Method | Path |
|--------|------|
| GET | `/metrics/dashboard` |
| GET | `/v1/candidates/stats` |
| POST | `/v1/control-center/audit-events` |
| GET | `/v1/control-center/audit-events` |
| GET | `/v1/control-center/audit-replay` |
| GET | `/v1/control-center/dashboard-aggregates` |
| GET | `/health` (gateway, agent, langgraph) |

### Governance visibility (when `VITE_ENABLE_GOVERNANCE=true`)

| Method | Path |
|--------|------|
| GET | `/v1/workforce/organizations` |
| GET | `/v1/policies/definitions` |
| GET | `/v1/governance/challenges` |
| GET | `/v1/decisions` |
| GET | `/v1/setu/signals` |
| GET | `/v1/workforce/trace-replay` |

## Pipeline model

When no safe destructive ingestion path is configured, the suite uses a **documented proxy pipeline**:

1. Capture baseline (stats, aggregates, audit replay/events, metrics dashboard).
2. POST `control_center_view` and `control_center_refresh` audit events with a shared `correlation_id`.
3. Re-read `/v1/candidates/stats`.
4. Capture final state and compare (audit count non-decreasing, stats not dropped, metrics keys present).

## Sample console output

```
Running: python -m pytest tests/e2e/control_center/test_control_center_e2e.py -v -m e2e --tb=short
...
========================================================================
CONTROL CENTER E2E — SUMMARY
========================================================================
Gateway: http://localhost:8000
Duration: 4521 ms
  [PASS] env_preflight (12 ms) — Environment OK for live E2E.
  [PASS] health_gateway (45 ms) — http://localhost:8000/health -> up
  [SKIP] health_agent (8 ms) — service down: ...
  [PASS] baseline_pipeline_final_compare (2100 ms) — audit_delta={'baseline': 5, 'final': 7, 'delta': 2}
------------------------------------------------------------------------
Total: 12 | Passed: 10 | Failed: 0 | Skipped: 2
========================================================================

Report written: backend/tests/e2e/control_center/results/control_center_e2e_report.json
```

## JSON report

`control_center_e2e_report.json` includes per-test `duration_ms`, pass/fail/skip, `compare_result`, and `pipeline` metadata.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Preflight fails on `API_KEY_SECRET` | Export the same key the gateway uses |
| All E2E skipped | Gateway not on :8000 — start gateway |
| Role JWT tests skipped | Set `JWT_SECRET_KEY` / `CANDIDATE_JWT_SECRET_KEY` |
| Mongo assertions missing | Set `MONGODB_URI` or rely on API audit counts only |

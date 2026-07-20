# Task19 Acceptance Test Pack

Executable checks for runtime governance hardening. Run from repository root.

**Last verified:** 2026-06-03 (localhost E2E: 8 passed, 2 skipped without JWT env; Render `/health` 200)

## 0. Control Center E2E suite (localhost pipeline)

Full data-flow validation (baseline → pipeline → final → compare) with JSON report:

```bash
cd backend
# export API_KEY_SECRET=...  (and optional JWT/MONGODB_URI)
python tests/e2e/control_center/run_control_center_e2e.py
```

See **`docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md`** for environment variables, offline vs live runs, and expected output.

Offline helpers only:

```bash
cd backend
python -m pytest tests/e2e/control_center/test_control_center_offline.py tests/gateway/test_control_center_governance.py -v
```

## 1. Unit tests (policy scope + audit mapping)

```bash
cd backend
python -m pytest tests/gateway/test_control_center_governance.py -v
```

**Covers:** scope resolution, role gate, audit trace mapping, scoped empty stats.

## 2. Gateway compile check

```bash
python -m py_compile services/gateway/app/main.py services/gateway/app/control_center_governance.py
```

## 3. Authz — control center endpoints (manual, staging or production)

Use a JWT for `client`, `recruiter`, or `admin` and gateway URL (`VITE_API_BASE_URL` / Render gateway).

| Check | Command | Expected |
|-------|---------|----------|
| Metrics dashboard allowed | `curl -H "Authorization: Bearer $TOKEN" $GATEWAY/metrics/dashboard` | 200 + `policy_scope` |
| Candidate denied (candidate role) | Bearer candidate token → `/metrics/dashboard` | 403 |
| Audit replay live | `curl -H "Authorization: Bearer $TOKEN" $GATEWAY/v1/control-center/audit-replay` | 200, `source: audit_logs` |
| Dashboard aggregates | `curl -H "Authorization: Bearer $TOKEN" $GATEWAY/v1/control-center/dashboard-aggregates` | 200, `hiring_funnel` array |
| Correlation header | `-i` on any above | `X-Correlation-ID` present |

## 4. Scope isolation

1. Log in as **client A**, open Command Center (`/control`), note scoped stats and **Data scope** label.
2. Log in as **client B**, confirm different `policy_scope.scope_label` and stats (when data exists).
3. Admin sees `scope: platform` in `policy_scope`.

## 5. Governance separation (UI)

1. Set `VITE_ENABLE_CONTROL_CENTER=true` on frontend (Vercel).
2. Open `/control` as client/recruiter/admin — governance stage strip visible; no execute actions.
3. Replay zone shows advisory note; events from `audit_logs` only (not seeded defaults).
4. Confirm **Auto-refresh every 30s** (background) after initial load.

## 6. Traceability

1. Refresh control center → `control_center_refresh` audit row in MongoDB `audit_logs`.
2. Agent/LangGraph `/health` returns `correlation_id` when `X-Correlation-ID` sent.

## 7. LangGraph RL retrain protection

```bash
curl -X POST $LANGGRAPH/rl/retrain
# Expected: 401/403 without API key
curl -X POST -H "Authorization: Bearer $API_KEY" $LANGGRAPH/rl/retrain
# Expected: 200 or business validation response
```

## 8. Frontend lint

```bash
cd frontend && npm run lint
```

## 9. Production smoke (Render + Vercel)

**Frontend env (Vercel)** — names must match `frontend/src/services/api.ts` / `vite-env.d.ts`:

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Render gateway |
| `VITE_AGENT_SERVICE_URL` | Render agent |
| `VITE_LANGGRAPH_SERVICE_URL` | Render langgraph (**not** `VITE_LANGGRAPH_URL`) |
| `VITE_ENABLE_CONTROL_CENTER` | `true` |
| `VITE_API_KEY` | Service API key for health probes |

**Checks:**

1. `curl $GATEWAY/health` and agent/langgraph `/health` → 200.
2. Log in on Vercel app → `/control` → service cards show Render URLs (not localhost).
3. Optional: JWT role matrix on production gateway (candidate 403) — requires real prod accounts; legacy `TECH001`/`demo123` is **archived**.

**Automated (from `backend/`):**

```bash
set GATEWAY_URL=https://bhiv-hr-gateway-l0xp.onrender.com
set API_KEY_SECRET=<your-render-gateway-key>
python tests/e2e/control_center/run_production_smoke.py
```

Report: `backend/tests/e2e/control_center/results/control_center_production_smoke_report.json`

See `frontend/VERCEL_DEPLOYMENT.md` and `docs/CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md` §F.

## Evidence artifacts

- `docs/TASK19_REQUIREMENT_EVIDENCE_MATRIX.md`
- `REVIEW_PACKET.md` (runtime section)
- `CONTRIBUTION_LOG.md` (Task19 entries)
- `docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md`
- `docs/CENTRAL_CONTROL_API_CONTRACT_FREEZE.md`

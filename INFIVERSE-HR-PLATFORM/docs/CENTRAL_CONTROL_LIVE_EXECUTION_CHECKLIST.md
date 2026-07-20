# Central Control Live Execution Checklist

Status: live on Render + Vercel; comprehensive production API evaluation complete (2026-06-06, 33/33); manual UI login sign-off pending
Date: 2026-06-06

## A) Technical Requirements

- [x] Removed mock/static production data path in central control KPI cards.
- [x] Added typed API adapters for gateway dashboard metrics and candidate stats with metadata.
- [x] Added bounded polling + manual refresh path.
- [x] Added source and refresh metadata display in UI.
- [x] Added partial-failure surface without fabricated fallback values.

## B) API Security and Protection

- [x] Protected control-center route in frontend with authenticated `ProtectedRoute`.
- [x] Restricted control-center visibility to command-center roles (`client`, `recruiter`, `admin`).
- [x] Enforced backend auth and role checks on `GET /metrics/dashboard`.
- [x] Enforced backend auth and role checks on `GET /v1/candidates/stats`.
- [x] Kept direct service calls read-only to `/health` probes.

## C) Governance Compliance

- [x] Added visible governance-stage separation (observe, assess, recommend, decision, execute).
- [x] Preserved advisory-only semantics in command center language.
- [x] Tagged source and metric type context in card sublabels.
- [x] Wired replay section to live scoped audit API (`GET /v1/control-center/audit-replay`); advisory-only semantics retained.
- [x] Preserved read-only dashboard boundary (no mutating controls added).

## D) Human Safety Compliance

- [x] No individual-level coercive ranking introduced.
- [x] Kept growth and org visuals aggregated.
- [x] Added clear explainability context for metrics source and type.
- [x] Preserved challenge/review-oriented language and bounded authority statements.

## E) Traceability and Audit Logging

- [x] Added correlation ID propagation middleware on gateway responses.
- [x] Added control-center audit ingestion endpoint: `POST /v1/control-center/audit-events`.
- [x] Added audit read/replay endpoints: `GET /v1/control-center/audit-events`, `GET /v1/control-center/audit-replay`.
- [x] Added backend-driven aggregates: `GET /v1/control-center/dashboard-aggregates`.
- [x] Added frontend audit event emission for view and refresh outcomes.
- [x] Added correlation ID display in dashboard for replay/investigation support.

## F) Verification

- [x] Frontend typecheck passed (`npm run lint` in `frontend`).
- [x] Gateway syntax validation passed (`python -m py_compile backend/services/gateway/app/main.py`).
- [x] Localhost live wiring (2026-06-03): all Control Center UI paths return 200 with platform API key; health on `:8000`, `:9000`, `:9001`.
- [x] E2E runner: `cd backend && set API_KEY_SECRET=... && python tests/e2e/control_center/run_control_center_e2e.py` — 8 passed, 2 skipped (JWT secrets unset).
- [x] Offline + governance unit tests: `test_control_center_offline.py`, `test_control_center_governance.py` — 10 passed.
- [x] Render production health (2026-06-03): gateway, agent, langgraph `/health` → 200.
- [x] Production API smoke (2026-06-03): `python tests/e2e/control_center/run_production_smoke.py` — 15/15 with explicit `GATEWAY_URL` (health, metrics, stats, aggregates, audit read/write, 401 unauthenticated).
- [x] Vercel deploy fetch: `infiverse-hr.vercel.app` + `sampada.blackholeinfiverse.com` → 200; JS bundles contain Render gateway/agent hosts.
- [ ] Production UI smoke (manual): log in on Vercel → `/control` → confirm service cards show Render URLs (automated bundle check passed).
- [ ] JWT role matrix on production (manual): use real client/recruiter/admin accounts — archived `TECH001`/`demo123`).
- [x] Production audit write canary: `POST /v1/control-center/audit-events` with `production_smoke_test` → 200.
- [x] Comprehensive production evaluation (2026-06-06): `python tests/e2e/control_center/run_comprehensive_evaluation.py` — **33/33 passed** (health, core CC, governance reads, RBAC matrix, scope isolation, Vercel bundles). Report:`.
- [x] Production RBAC JWT matrix (2026-06-06): admin/client/recruiter → 200 with correct scopes; candidate → 403 (minted JWTs with gateway secrets).
- [ ] Production scoped-data isolation with real tenant accounts (requires `E2E_CLIENT_ID` / `E2E_CLIENT_PASSWORD`).

### Live wiring verification (2026-06-06)

See `docs/CENTRAL_CONTROL_API_CONTRACT_FREEZE.md` (table: UI function → method/path → verified) and `docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md` (E2E command + endpoint list).

Frontend env names (must match `frontend/src/services/api.ts` / `vite-env.d.ts`):

- `VITE_API_BASE_URL`, `VITE_AGENT_SERVICE_URL`, `VITE_LANGGRAPH_SERVICE_URL`, `VITE_ENABLE_CONTROL_CENTER=true`

## G) Rollout Steps

- [x] Production backend on Render — health endpoints verified (2026-06-03).
- [x] Production frontend on Vercel — env vars documented (`VITE_LANGGRAPH_SERVICE_URL`, not `VITE_LANGGRAPH_URL`).
- [x] Localhost role matrix + E2E (API key path; JWT tests when secrets set).
- [x] Production API + Vercel bundle smoke (script + report JSON).
- [ ] Production UI login walkthrough (manual sign-off).
- [ ] Production JWT matrix with real tenant accounts.


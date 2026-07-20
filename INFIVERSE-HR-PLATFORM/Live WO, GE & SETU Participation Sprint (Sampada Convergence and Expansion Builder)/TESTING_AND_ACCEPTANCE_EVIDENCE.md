# Testing & Acceptance Evidence (Live WO/GE/SETU Sprint · Phase 8)

**Workflow position:** Step 8 of 11 (after Control Center; before live deployment re-verification)  
**Date:** 2026-06-27 (initial) · updated 2026-07-04 (local functional)  
**Gateway base URL:** in-process FastAPI (Phases 1–8) · `http://127.0.0.1:8000` (local) · `https://bhiv-hr-gateway-l0xp.onrender.com` (live)  
**Environment:** local in-process + local multi-service + deployed Render gateway  
**Status:** `complete` — gateway tests pass; post-deploy smoke pass (2026-07-03); local functional pass 3/4 partners (2026-07-04)  
**Raw capture:** `evidence/live_workforce_governance_setu/test_results/`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Purpose

Phase 8 consolidates **automated test results** and the **acceptance checklist** across all prior phases. It answers: "Did the full suite still pass after gap fixes, and do live deployments remain healthy?"

---

## Prerequisites

| Step | Must be complete |
|---|---|
| Steps 1–7 | All phase evidence docs populated with real IDs (no `TBD`) |
| Step 0 | Gap fixes applied; `compileall` success |
| Steps 9–11 | Optional for initial Phase 8; required for final acceptance after deploy |

---

## Execution method (how to reproduce)

### A. Local gateway test suite (Step 8 core)

```powershell
cd INFIVERSE-HR-PLATFORM
python -m compileall backend/services/gateway
python -m pytest -q backend/tests/gateway/
```

**Expected:** compile success; **35 passed** (gateway suite, 2026-07-02 re-run).

**Outputs:**

| File | Content |
|---|---|
| `test_results/pytest_final.txt` | Full suite result (29 passed initial + additive tests) |
| `test_results/pytest_after_gapfix.txt` | Post–Gap Fix #1 regression (24 passed) |
| `test_results/compileall_final.txt` | Compile check |

### B. Live gateway auth probe (Step 9 prerequisite)

```powershell
python evidence/live_workforce_governance_setu/harness/auth_probe.py
```

**Expected:** health 200; `API_KEY_SECRET` → 200; `GATEWAY_SECRET_KEY` → 401.

### C. Post-deploy smoke (Step 11)

```powershell
python evidence/live_workforce_governance_setu/harness/post_deploy_smoke.py
python evidence/live_workforce_governance_setu/harness/run_partner_capture.py
```

**Expected:** all backend health checks pass; four partner dispatches → HTTP 200 + `sig-…` ids.

---

## Acceptance checklist (Definition of Done)

| # | Validation area | Evidence source | Status |
|---|---|---|---|
| 1 | Workforce lifecycle | `LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md` | Met — 13-event replay |
| 2 | Hierarchy traversal | `ORG_HIERARCHY_VALIDATION.md` | Met — incl. multi-org addendum |
| 3 | Governance replay | `GOVERNANCE_REPLAY_EVIDENCE.md` | Met — 3 scenarios + consolidated packet |
| 4 | Policy replay | `POLICY_REPLAY_VALIDATION.md` | Met — re-evaluations prove stable definitions |
| 5 | SETU participation | `SETU_PARTICIPATION_EVIDENCE.md` | Met — local + live + partner Tier 2 |
| 6 | Ownership propagation | `LINEAGE_PROPAGATION_EVIDENCE.md` | Met — 7/7 fields × 3 samples |
| 7 | Lineage propagation | `LINEAGE_PROPAGATION_EVIDENCE.md` | Met — 1 signal + 14 audits on one cid |
| 8 | Decision replay | `GOVERNANCE_REPLAY_EVIDENCE.md` | Met — 2-link supersedes chain (Leave) |
| 9 | Control Center reads | `CONTROL_CENTER_EVIDENCE.md` | Met — 38 events / 14 filtered / replay 14 |
| 10 | Gateway unit tests | `test_results/pytest_final.txt` | Met — 35 passed |
| 11 | No Sampada contract change | `EXECUTION_LOG.md` §Partner closeout | Met — empty diff on SETU routes |
| 12 | Evidence bundle complete | `evidence/live_workforce_governance_setu/SUMMARY.md` | Met |

---

## Test results summary

| Run | Command | Result | Date |
|---|---|---|---|
| After gap fix | `pytest` (4 gateway files) | **24 passed**, 5 warnings | 2026-06-27 |
| Full suite | `pytest` (+ additive Live WO tests) | **29 passed**, 6 warnings | 2026-06-27 |
| Gateway re-run | `pytest -q backend/tests/gateway/` | **35 passed**, 8 warnings | 2026-07-02 |
| Compile | `compileall backend/services/gateway` | exit 0 | 2026-06-27, 2026-07-02 |
| Control Center e2e | `run_comprehensive_evaluation.py` | 32/33 passed (health_agent timeout) | 2026-07-02 |

---

## Post-deploy verification (Step 11 — 2026-07-03)

After all four partner repos + Sampada deployed to Render/Vercel with env verified.

### Live service health

| Service | Endpoint | Result |
|---|---|---|
| Sampada gateway | `GET /health` | **200** — v4.2.0 |
| Artha backend | `GET /health` | **200** — API running |
| ai-crm backend | `POST /api/auth/login` | **401** — server reachable |
| Niyantran backend | `POST /api/auth/login` | **400** — server reachable |

### Live frontends (Vercel)

| App | URL | Result |
|---|---|---|
| Artha | `https://ai-artha.vercel.app` | **200** |
| ai-crm | `https://ai-crm-sigma-five.vercel.app` | **200** |
| Niyantran | `https://blackhole-workflow.vercel.app` | **200** |
| Sampada | `https://infiverse-hr.vercel.app` | **200** |

### Fresh partner SETU capture (re-confirm after deploy)

**Bundle:** `evidence/live_workforce_governance_setu/partner_live/20260703T100843Z/`

| Partner | New signal_id | HTTP |
|---|---|---|
| Artha | `sig-43d05ebea091` | 200 |
| CRM | `sig-b83c10ba250c` | 200 |
| Logistics | `sig-077b665909d2` | 200 |
| Niyantran | `sig-89a4b9062553` | 200 |

**Shared correlation_id:** `3d0a7d1a-1be8-4267-af5b-8d239ea25049`

### Git / deploy alignment (2026-07-03)

| Repo | `main` pushed | SETU on `main` |
|---|---|---|
| ai-crm | Yes (`5633c13`) | `sampada_dispatcher.py` |
| Artha (origin + AI-Artha) | Yes (`04608e5`) | `sampadaAdapter.js` |
| workflow-blackhole | Yes (`fbcfa73`) | `setuDispatcher.js` |

---

## Live URL verification (2026-07-04 — user-provided production domains)

All URLs supplied by owner verified against live Render + `*.blackholeinfiverse.com` frontends.

### Live service health (backends)

| Service | URL | Result |
|---|---|---|
| Sampada gateway | `https://bhiv-hr-gateway-l0xp.onrender.com/health` | **200** — v4.2.0 |
| Sampada agent | `https://bhiv-hr-agent-cato.onrender.com/health` | **200** — v3.0.0 |
| Sampada LangGraph | `https://bhiv-hr-langgraph-luy9.onrender.com/health` | **200** |
| Artha backend | `https://ai-artha.onrender.com/health` | **200** |
| ai-crm backend | `https://ai-crm-4nje.onrender.com/api/auth/login` | **401** — reachable |
| Niyantran backend | `https://blackholeworkflow.onrender.com/api/auth/login` | **400** — reachable (no `/health` route) |

### Live frontends (custom domains)

| App | URL | Result | Bundle API target |
|---|---|---|---|
| Sampada | `https://sampada.blackholeinfiverse.com/` | **200** | Gateway + Agent + LangGraph ✓ |
| Artha | `https://artha.blackholeinfiverse.com/` | **200** | `ai-artha.onrender.com/api/v1` ✓ |
| SETU/CRM | `https://setu.blackholeinfiverse.com/` | **200** | `ai-crm-4nje.onrender.com` ✓ *(stale `ai-artha.vercel.app` ref in bundle — fix env + redeploy)* |
| Niyantran | `https://niyantran.blackholeinfiverse.com/login` | **200** | `blackholeworkflow.onrender.com/api` ✓ |

### Fresh partner SETU capture (2026-07-04)

**Bundle:** `evidence/live_workforce_governance_setu/partner_live/20260704T071016Z/`

| Partner | signal_id | HTTP |
|---|---|---|
| Artha | `sig-5527bab3a3c9` | 200 |
| CRM | `sig-8ac9e1885a97` | 200 |
| Logistics | `sig-fff4f754415a` | 200 |
| Niyantran | `sig-99fcca8ba98a` | 200 |

**Shared correlation_id:** `3d0a7d1a-1be8-4267-af5b-8d239ea25049`

### Open config actions (from live scan)

1. Redeploy SETU frontend — remove stale `ai-artha.vercel.app` from build bundle
2. Confirm partner Render env: `SETU_ENABLED`, `SETU_BASE_URL`, `SETU_API_KEY` for Tier-1 auto-dispatch
3. Add Niyantran `/api/health` (optional; login probe sufficient today)
4. Rotate `API_KEY_SECRET` after capture sessions

---

## Local multi-service functional test (2026-07-04)

**Harness:** `evidence/live_workforce_governance_setu/harness/start_local_gateway.py`, `local_auth_probe.py`, `local_partner_functional_test.py`, `local_control_center_probe.py`  
**Capture:** `evidence/live_workforce_governance_setu/local_functional/20260704T064800Z/local_partner_dispatch.json`  
**Correlation ID:** `local-functional-test-20260704`

### Services started (local)

| Service | Port | Status |
|---|---|---|
| Sampada gateway | 8000 | Running — health 200, v4.2.0 |
| Artha backend | 5000 | Running — `/health` 200 |
| ai-crm Node | 8001 *(override; `.env` default 8000 conflicts with gateway)* | Running |
| Niyantran | 5001 *(override; `.env` default 5000 conflicts with Artha)* | Running |

### Startup issues

| Issue | Resolution |
|---|---|
| Missing `backend/venv` | Created venv; installed `requirements.txt` |
| Missing ai-crm `node_modules` | `npm install` in `ai-crm/backend-nodejs/` |
| Port conflicts (8000 / 5000) | Override via `$env:PORT` for ai-crm and Niyantran |
| Gateway auth 401 without `.env` in process | Restart via `start_local_gateway.py` |

### Features verified (local)

| Feature | Result |
|---|---|
| `GET /health` | Pass |
| SETU auth (`API_KEY_SECRET` 200; `GATEWAY_SECRET_KEY` 401) | Pass |
| `GET /v1/setu/signals`, `GET /v1/setu/trace/{id}` | Pass |
| Control Center reads (audit-events, audit-replay, dashboard-aggregates) | Pass |
| Artha SETU dispatch (`artha_payroll_visibility`) | Pass — `sig-09b6bf7aa810` |
| CRM SETU dispatch (`crm_participation`) | Pass — `sig-0757dc6c045b` |
| Logistics SETU dispatch (`crm_participation` + `subsystem: logistics`) | Pass — `sig-7aac0fb6efaf` |
| Niyantran SETU dispatch (`niyantran_telemetry`) | **Fail** — empty `ExecutionEvent` collection in local Mongo |
| Live `auth_probe.py` + `post_deploy_smoke.py` | Pass (re-run same session) |
| `pytest -q backend/tests/gateway/` | 31 passed, 2 failed (missing `pytest-asyncio` in fresh venv) |

### Local blockers (unchanged from sprint)

- Niyantran local Tier-2 capture needs seeded `ExecutionEvent` data (live dispatch works: `sig-89a4b9062553`).
- Tier 1 business-route → dispatcher path not exercised; ai-crm Node does not auto-wire Python SETU dispatcher.

---

## Known limitations

- Control Center **UI screenshot** not captured — backend read endpoints only (`CONTROL_CENTER_EVIDENCE.md`).
- Tier 2 partner path only — Tier 1 full business-route dispatch not exercised.
- ai-crm Render runs Node `backend-nodejs`; Python SETU dispatcher requires separate service or Node port for live auto-dispatch from CRM UI.
- Policy **conflict resolution** not a present runtime capability — not fabricated.

---

## Cross-references

- Master workflow: `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder).md`
- Running log: `EXECUTION_LOG.md`
- Evidence index: `evidence/live_workforce_governance_setu/SUMMARY.md`
- Review packet: `REVIEW_PACKET.md`
- Deployment runbook: `PARTNER_SETU_LIVE_RUNBOOK.md`

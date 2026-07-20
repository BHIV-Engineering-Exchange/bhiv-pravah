# SETU Review Packet

**Repository root:** `ai-crm/`  
**Last updated:** 2026-07-04 (Phase II Post-Handover Audit)  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`  
**Ownership decision:** Accepted with Conditions — see `SETU_OWNER_ACCEPTANCE_REPORT.md` in the audit bundle.

This packet is the index for reviewing SETU. It was rewritten after the Phase II audit to point at the **live Python implementation** and flag outdated references.

---

## 1. Start here

| Priority | Document | Purpose |
|---|---|---|
| 1 | `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/README.md` | Audit bundle index |
| 2 | `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_GAP_REGISTER.md` | 22 prioritized gaps (6 Critical) |
| 3 | `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_OWNER_ACCEPTANCE_REPORT.md` | Conditions + 30-day plan |

---

## 2. Entry point — execution contract

| Item | Path | Audit status |
|---|---|---|
| Contract spec | `ai-crm/contracts/execution/EXECUTION_CONTRACT_SPEC.md` | Verified — aligns with `TraceContinuityValidator.REQUIRED_FIELDS` |
| JSON schema | `ai-crm/contracts/execution/execution_contract_v1.json` | Documentation only — not imported at runtime |

---

## 3. Core execution flow (live — Python)

**Canonical runtime path.** Wired in `ai-crm/backend/api_app.py` (lines 235–303).

| Responsibility | Live module (`ai-crm/backend/setu/`) | State |
|---|---|---|
| Router (20 routes, `/setu`) | `routes.py` | Wired |
| Trace continuity | `trace_continuity.py` | Wired |
| Trace middleware | `trace_continuity_middleware.py` | Wired — **over-scoped (F5)** blocks 6 POST endpoints |
| Sovereign routing | `sovereign_routing_adapter.py` | **Broken (F1)** — mis-init at `api_app.py:253` |
| Lineage / Bucket | `bucket_lineage_adapter.py` | Wired — persists to Mongo via `mongo_store.py` |
| Telemetry | `telemetry_layer.py` | Wired |
| Signal ingest | `signal_ingestion.py` | Wired — blocked by F5 on POST |
| Niyantran visibility | `niyantran_integration_adapter.py` | Wired — blocked by F5 on POST |
| Contract validation | `contract_validation.py` | Wired — blocked by F5 on POST |
| Persistence | `mongo_store.py` | Wired — requires `pymongo`/`motor` (F2) |
| Sampada outbound | `sampada_dispatcher.py` | Wired — env-gated (`SAMPADA_SETU_ENABLED`) |

**Startup chain (verified):**  
`uvicorn api_app:app` → `api_app.py` SETU init → `setu_router` mounted at startup.

**Deploy paths:**

| Mechanism | Command | SETU reachable? |
|---|---|---|
| Docker / local scripts | `uvicorn api_app:app` | Yes (if Mongo + deps OK) |
| `ai-crm/backend/Procfile` | `python start_server.py` | **No** — file missing (F3) |
| `ai-crm/backend/railway.json` | `python start_server.py` | **No** — file missing (F3) |

Do **not** use `ai-crm/backend/main.py` for SETU — it is a separate inventory API.

---

## 4. Deprecated — JavaScript prototype (orphaned)

These paths appeared in the original review packet but are **not** on the live runtime path (zero importers — F6):

| Module | Path | Replacement |
|---|---|---|
| Trace continuity | `ai-crm/middleware/traceContinuityValidator.js` | `ai-crm/backend/setu/trace_continuity.py` |
| Sovereign routing | `ai-crm/integration/sovereign_routing_adapter.js` | `ai-crm/backend/setu/sovereign_routing_adapter.py` |
| Lineage | `ai-crm/integration/bucket_lineage_adapter.js` | `ai-crm/backend/setu/bucket_lineage_adapter.py` |
| Telemetry | `ai-crm/integration/telemetry_layer.js` | `ai-crm/backend/setu/telemetry_layer.py` |

JS modules use in-memory storage only. Treat as historical prototype; do not extend.

---

## 5. Proof documents — what to trust

| # | Document | Use for | Audit note |
|---|---|---|---|
| 1 | `ai-crm/replay_demo.json` | Example execution chain | Static fixture — not runtime-generated (F12) |
| 2 | `ai-crm/replay_proof.md` | Replay narrative | Partially verified — regenerate from Mongo after fixes |
| 3 | `ai-crm/end_to_end_trace.json` | Full trace example | Static fixture |
| 4 | `ai-crm/TRACE_CONTINUITY_PROOF.md` | Immutability rules | **Verified** — matches Python validator behavior |
| 5 | `ai-crm/SOVEREIGN_ROUTING_PROOF.md` | Sarathi / BHIV shapes | Code verified — `/setu/route` broken at runtime (F1) |
| 6 | `ai-crm/TELEMETRY_PROOF.md` | Event field requirements | **Verified** (code) — log excerpts unverifiable without live run |
| 7 | `ai-crm/LINEAGE_EMISSION_PROOF.md` | Append-only lineage | **Verified** (code) — JSON artifact is static |
| 8 | `ai-crm/DEPENDENCY_GRAPH_PROOF.md` | Blockage propagation | Code exists but **unwired** (F7) |
| 9 | `ai-crm/SETU_FLOW_PROOF.md` | 7-phase implementation map | Partially verified — deployment section overstated |
| 10 | `ai-crm/contracts/execution/EXECUTION_CONTRACT_SPEC.md` | Tenant isolation + contract fields | **Verified** |
| 11 | `ai-crm/TRACE_CONTINUITY_PROOF.md` + spec | Tenant isolation proof | **Verified** (code) |
| 12 | Failure cases | `TRACE_CONTINUITY_PROOF.md`, `SOVEREIGN_ROUTING_PROOF.md` | Error codes align with Python implementations |

---

## 6. Convergence gaps

See `ai-crm/CONVERGENCE_GAPS.md` — **partially outdated** after audit:

| Original claim | Current status (2026-07-04) |
|---|---|
| Runtime wiring not applied | **Contradicted** — wiring exists in `api_app.py`; POST paths broken (F1, F5) |
| Durable storage not configured | **Contradicted** — `MongoSetuStore` + `MONGODB_URL`; clean install fails without deps (F2) |
| Gated Bridge contract-only | **Verified** — local schema validation only (GAP-012) |

Full backlog: `SETU_GAP_REGISTER.md` in the audit bundle.

---

## 7. Critical blockers (fix first)

| Gap | Issue | File |
|---|---|---|
| GAP-001 / F3 | Missing `start_server.py` | `ai-crm/backend/Procfile`, `railway.json` |
| GAP-002 / F1 | `SovereignRoutingAdapter(setu_store)` TypeError | `ai-crm/backend/api_app.py:253` |
| GAP-003 / F5 | Middleware blocks non-execution POSTs | `trace_continuity_middleware.py` |
| GAP-004 / F2 | `pymongo`/`motor` missing from requirements | `ai-crm/backend/requirements.txt` |
| GAP-005 / F4 | Credentials in `backend/.env` | Rotate immediately |
| GAP-006 / F10 | Zero SETU tests | Add `backend/tests/test_setu_*.py` |

---

## 8. Suggested review order

1. Read audit bundle `README.md` and `SETU_OWNER_ACCEPTANCE_REPORT.md`
2. Trace live wiring: `api_app.py` → `backend/setu/routes.py`
3. Validate contract spec against `trace_continuity.py`
4. Cross-check proof docs in §5 against Python modules (not JS)
5. Work through `SETU_GAP_REGISTER.md` sequenced backlog (Phase A first)

---

*Supersedes the 2026-03 handover index that listed JS modules as the core execution flow.*

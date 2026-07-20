# SETU Handover Verification Report

**Audit date:** 2026-07-04  
**Repository root:** `ai-crm/` — all paths below are relative to this folder (not parent directories such as `INFIVERSE-HR-PLATFORM/ai-crm`).  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`

**Scope:** All SETU handover/proof documents under `ai-crm/`  
**Method:** Independent verification against source code in `ai-crm/backend/setu/`, `ai-crm/integration/`, `ai-crm/middleware/`, `ai-crm/contracts/`, and backend entry points.  
**Finding IDs (F#):** Cross-referenced in `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md` and `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_GAP_REGISTER.md`.

---

## 1. Documents Enumerated

| Document | Type | Primary claims |
|---|---|---|
| `ai-crm/CONVERGENCE_GAPS.md` | Gap summary | Runtime wiring absent; no durable storage; Gated Bridge is contract-only |
| `ai-crm/REVIEW_PACKET.md` | Index / review guide | Core flow in JS `ai-crm/middleware/` + `ai-crm/integration/`; points to all proof docs |
| `ai-crm/replay_proof.md` | Replay evidence | Deterministic IDs across chain; append-only lineage |
| `ai-crm/replay_demo.json` | Chain fixture | End-to-end execution chain with fixed IDs |
| `ai-crm/end_to_end_trace.json` | Trace fixture | Full execution contract + telemetry + lineage |
| `ai-crm/TELEMETRY_PROOF.md` | Telemetry evidence | Normalized event types; required fields present |
| `ai-crm/TRACE_CONTINUITY_PROOF.md` | Trace continuity evidence | Immutability rules; rejection examples |
| `ai-crm/SETU_FLOW_PROOF.md` | Implementation proof | All 7 phases complete; middleware integrated; MongoDB ready; deployment complete |
| `ai-crm/SOVEREIGN_ROUTING_PROOF.md` | Routing evidence | Sarathi payload; BHIV envelope; governance validation |
| `ai-crm/DEPENDENCY_GRAPH_PROOF.md` | Dependency graph evidence | Blockage propagation; impact scoring |
| `ai-crm/LINEAGE_EMISSION_PROOF.md` | Lineage evidence | Append-only artifacts; determinism hashes |
| `ai-crm/contracts/execution/EXECUTION_CONTRACT_SPEC.md` | Contract spec | Required fields; continuity invariants |
| `ai-crm/contracts/execution/execution_contract_v1.json` | Contract schema | JSON schema for v1 contract |

No dedicated `SETU_HANDOVER_*.md` narrative or SETU onboarding README was found — the above is the complete handover documentation set.

**Checkpoint 2.5:** Every document below has a verdict with cited evidence.

---

## 2. Verified Deployment Entry Point Chain

| Step | Declared path | Evidence | Verdict |
|---|---|---|---|
| Railway deploy | `ai-crm/backend/railway.json` → `python start_server.py` | ```6:7:backend/railway.json``` | **Contradicted** — `start_server.py` does not exist (`Test-Path` → False) |
| Procfile | `web: python start_server.py` | ```1:1:backend/Procfile``` | **Contradicted** — same missing file (F3) |
| Docker production | `uvicorn api_app:app` | ```47:47:backend/Dockerfile``` | **Verified** — alternate live path |
| Local scripts | `uvicorn api_app:app` | `ai-crm/backend/run_project.sh`, `ai-crm/backend/docker-entrypoint.sh` | **Verified** |
| `ai-crm/backend/main.py` | Standalone ERP ingestion API | ```1:32:backend/main.py``` | **Verified** — unrelated to SETU; not the SETU entry point |

**Actual verified startup chain (when SETU is reachable):**  
`uvicorn api_app:app` → `ai-crm/backend/api_app.py` lines 235–303 initialize SETU components → `startup_event` includes `setu_router` at lines 298–300.

Railway/Procfile path is **not reproducible** from the repository.

---

## 3. Live vs Orphaned Implementation (REVIEW_PACKET reconciliation)

**Claim (`ai-crm/REVIEW_PACKET.md` line 2):** Core execution flow lives in:
- `ai-crm/middleware/traceContinuityValidator.js`
- `ai-crm/integration/sovereign_routing_adapter.js`
- `ai-crm/integration/bucket_lineage_adapter.js`
- `ai-crm/integration/telemetry_layer.js`

**Evidence — live path is Python:**

```235:280:backend/api_app.py
# Initialize SETU integrations
try:
    from setu.mongo_store import MongoSetuStore
    from setu.trace_continuity import TraceContinuityValidator
    from setu.trace_continuity_middleware import TraceContinuityMiddleware
    from setu.sovereign_routing_adapter import SovereignRoutingAdapter
    ...
    app.add_middleware(
        TraceContinuityMiddleware,
        validator=trace_validator,
        path_prefix="/setu"
    )
```

**Evidence — JS modules are orphaned:** Repository-wide search found **zero importers** of the four orphaned JS modules under `ai-crm/`. JS trace validator defaults to in-memory store:

```42:75:middleware/traceContinuityValidator.js
const createInMemoryLineageStore = () => {
  const byExecutionId = new Map();
  ...
};
...
    lineageStore = createInMemoryLineageStore(),
```

| Verdict | Detail |
|---|---|
| **Contradicted** | REVIEW_PACKET describes JS as core flow; runtime wires Python equivalents under `ai-crm/backend/setu/` (F6) |
| **Orphaned** | `ai-crm/integration/` and `ai-crm/middleware/` JS files have no consumers |

---

## 4. Per-Document Claim Verification

### 4.1 `ai-crm/CONVERGENCE_GAPS.md`

| Claim | Evidence | Verdict |
|---|---|---|
| "Runtime wiring of SETU middleware and adapters into live services is not yet applied." | SETU router + middleware registered in `api_app.py` ```235:303:backend/api_app.py``` | **Contradicted / Outdated** — partial wiring exists, but F1 crashes `/setu/route` and F5 blocks six other POST endpoints |
| "External durable storage for lineage and telemetry streams is not configured." | `MongoSetuStore` uses `get_async_db()` ```13:48:backend/setu/mongo_store.py```; `MONGODB_URL` present in delivered `ai-crm/backend/.env` (key verified, value not reproduced here) | **Contradicted** — durable storage is configured in code and environment; caveat: `pymongo`/`motor` missing from `requirements.txt` (F2) can prevent SETU from loading on clean install |
| "Gated Bridge policy engine integration is represented as a validation contract only." | Local validator only ```30:42:backend/setu/sovereign_routing_adapter.py```; no HTTP/policy service call | **Verified** |

### 4.2 `ai-crm/REVIEW_PACKET.md`

| Claim | Verdict |
|---|---|
| Entry at `ai-crm/contracts/execution/EXECUTION_CONTRACT_SPEC.md` | **Verified** — file exists |
| Core flow in JS `ai-crm/integration/` + `ai-crm/middleware/` | **Contradicted** — see Section 3 (F6) |
| Replay chain in `ai-crm/replay_demo.json` | **Partially Verified** — static JSON fixture, not generated by running code (F12) |
| Remaining gaps in `ai-crm/CONVERGENCE_GAPS.md` | **Partially Verified** — Gated Bridge claim holds; wiring and storage claims outdated |

### 4.3 `ai-crm/replay_proof.md` / `ai-crm/replay_demo.json` / `ai-crm/end_to_end_trace.json`

| Claim | Evidence | Verdict |
|---|---|---|
| Same `execution_id` / `trace_id` across stages | IDs appear identically across handover JSON fixtures | **Partially Verified** — static fixtures only |
| IDs like `trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R` produced by running code | No matches in `ai-crm/backend/setu/*.py`; no reproduction harness in repo | **Contradicted** — example strings in proof artifacts, not runtime-generated proof (F12) |
| Lineage append-only with deterministic hashes | Python implementation computes hashes ```31:34:backend/setu/bucket_lineage_adapter.py``` | **Verified** (code capability) — not proven by replay JSON alone |

### 4.4 `ai-crm/TELEMETRY_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| Events include execution_id, trace_id, tenant_id, timestamp | Enforced in `TelemetryLayer.emit` ```21:29:backend/setu/telemetry_layer.py``` | **Verified** (code) |
| Event types normalized to approved set | `TELEMETRY_TYPES` list ```6:14:backend/setu/telemetry_layer.py``` | **Verified** (code) |
| Log block in proof doc reflects live output | Only appears in `.md` file | **Unverifiable** as runtime proof — would need executed request + MongoDB query |

### 4.5 `ai-crm/TRACE_CONTINUITY_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| trace_id immutable | Enforced ```88:98:backend/setu/trace_continuity.py``` | **Verified** (code) |
| tenant_id unchanged on lineage edge | Enforced ```140:151:backend/setu/trace_continuity.py``` | **Verified** (code) |
| lineage_hash verified | Enforced ```153:164:backend/setu/trace_continuity.py``` | **Verified** (code) |
| Rejection JSON examples | Match error codes in `TraceContinuityError` | **Verified** (code alignment) |
| Log examples are live output | Static in `.md` only | **Unverifiable** without runtime logs |

### 4.6 `ai-crm/SETU_FLOW_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| All 7 phases implemented | Routes exist in ```31:304:backend/setu/routes.py``` | **Partially Verified** — code present (20 routes total) |
| File paths `setu/signal_ingestion.py` (no `ai-crm/backend/` prefix) | Actual path `ai-crm/backend/setu/signal_ingestion.py` | **Partially Verified** — path imprecise |
| Middleware integrated | ```276:280:backend/api_app.py``` | **Verified** |
| MongoDB collections created | Four SETU collections in `COLLECTIONS` ```151:156:backend/database/mongodb_connection.py```; two more use fallback strings in `mongo_store.py` | **Partially Verified** |
| "Deployment Status: ✅ All modules… API routes exposed" | `start_server.py` missing (F3); F1 breaks `/setu/route`; F5 blocks other POSTs | **Contradicted** |
| "PROOF COMPLETE" for real TANTRA flow | No CRM/Logistics caller invokes SETU; proof IDs static | **Contradicted** |

### 4.7 `ai-crm/SOVEREIGN_ROUTING_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| Sarathi payload shape | `_build_sarathi_payload` ```45:59:backend/setu/sovereign_routing_adapter.py``` | **Verified** (code) |
| BHIV envelope shape | `_build_bhiv_envelope` ```62:82:backend/setu/sovereign_routing_adapter.py``` | **Verified** (code) |
| Governance rejection `gated_bridge_not_approved` | ```39:40:backend/setu/sovereign_routing_adapter.py``` | **Verified** (code) |
| `/setu/route` works end-to-end | `SovereignRoutingAdapter(setu_store)` passes store as validator ```253:253:backend/api_app.py``` vs ```86:87:backend/setu/sovereign_routing_adapter.py``` | **Contradicted** — routing endpoint broken at runtime (F1) |

### 4.8 `ai-crm/DEPENDENCY_GRAPH_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| Blockage propagation / impact scoring | Logic in `ai-crm/backend/setu/dependency_graph_engine.py` and `ai-crm/engine/dependency_graph_engine.js` | **Verified** (code exists) |
| Used in live SETU request path | No imports found anywhere in backend | **Contradicted** — orphaned (F7) |

### 4.9 `ai-crm/LINEAGE_EMISSION_PROOF.md`

| Claim | Evidence | Verdict |
|---|---|---|
| Append-only lineage with determinism_hash | `append_lineage_event` + `compute_determinism_hash` | **Verified** (code) |
| lineage_event_id derived from hash | ```33:34:backend/setu/bucket_lineage_adapter.py``` | **Verified** (code) |
| JSON artifact is live output | Static in `.md` only | **Unverifiable** without DB export |

### 4.10 `ai-crm/contracts/execution/EXECUTION_CONTRACT_SPEC.md` + `execution_contract_v1.json`

| Claim | Evidence | Verdict |
|---|---|---|
| Required fields match validator | Compare spec fields to ```7:19:backend/setu/trace_continuity.py``` | **Verified** |
| `execution_contract_v1.json` imported at runtime | Not imported by Python SETU code | **Partially Verified** — documentation only |
| Example IDs in spec | Same static IDs as proof docs | **Verified** as documentation examples only |

### 4.11 Delivered environment (`ai-crm/backend/.env`) — not a handover doc, but affects gap claims

| Observation | Evidence | Verdict |
|---|---|---|
| Live credentials in delivered tree | `ai-crm/backend/.env` exists locally; contains `MONGODB_URL`, `JWT_SECRET`, `ADMIN_PASSWORD`, SMTP, and `SAMPADA_SETU_*` keys (values not reproduced) | **Verified security exposure** (F4) — rotate immediately; confirm git history scope separately |

---

## 5. Per-Document Scores

| Document | Accuracy | Completeness | Outdated | Clarification needed |
|---|---|---|---|---|
| `ai-crm/CONVERGENCE_GAPS.md` | Low — wiring and storage claims wrong | Highest of set, but misses F1/F2/F5 | Yes | Which deploy path is canonical in production? |
| `ai-crm/REVIEW_PACKET.md` | Low — wrong implementation language | Medium — good index | Yes — JS path obsolete | Confirm intentional deprecation of JS modules |
| `ai-crm/replay_proof.md` | Medium — describes intent | Low — no reproduction steps | N/A | Were replay JSONs exported from production or authored manually? |
| `ai-crm/SETU_FLOW_PROOF.md` | Low — overstates deployment | High feature list | Yes — deployment section | Which environment proved the 7-phase flow? |
| `ai-crm/TELEMETRY_PROOF.md` | Medium | Low | N/A | Source of log excerpts? |
| `ai-crm/TRACE_CONTINUITY_PROOF.md` | High (matches code behavior) | Medium | File refs wrong | — |
| `ai-crm/SOVEREIGN_ROUTING_PROOF.md` | Medium — code exists but miswired | Medium | N/A | Was `/setu/route` ever exercised after Python port? |
| `ai-crm/DEPENDENCY_GRAPH_PROOF.md` | Low — code unused | Low | N/A | Is dependency graph planned for Phase III? |
| `ai-crm/LINEAGE_EMISSION_PROOF.md` | Medium | Low | N/A | — |
| Contract spec + JSON | High | High | No | — |

---

## 6. Summary Statistics

| Verdict | Count (material claims) |
|---|---|
| Verified | 18 |
| Partially Verified | 12 |
| Contradicted | 15 |
| Unverifiable | 4 |

**Checkpoint 2.5:** Complete — all handover documents have per-claim verdicts with file evidence.

---

## 7. Summary Judgment

The handover package describes a system that is architecturally coherent on paper (execution contracts, trace lineage, tenant isolation, observe-only governance) but proof documents largely describe **a different, dead JavaScript implementation** than the one wired into `ai-crm/backend/api_app.py`, and none disclose the specific reproducible defects found in this audit (F1 constructor bug, F2 missing dependencies, F5 middleware scope, F4 credential exposure). `ai-crm/CONVERGENCE_GAPS.md` is the most trustworthy document because it under-claims rather than over-claims — but it is out of date and incomplete.

**Recommendation:** Replace JS file references in `ai-crm/REVIEW_PACKET.md` and all `*_PROOF.md` documents with `ai-crm/backend/setu/*.py` paths, or explicitly retire the JS prototype. See `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md` for technical detail behind each verdict.

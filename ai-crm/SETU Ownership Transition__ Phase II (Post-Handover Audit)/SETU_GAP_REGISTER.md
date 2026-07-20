# SETU Gap Register

**Audit date:** 2026-07-04  
**Repository root:** `ai-crm/` — all paths below are relative to this folder (not parent directories such as `INFIVERSE-HR-PLATFORM/ai-crm`).  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`

**Source:** Consolidated from `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_HANDOVER_AUDIT.md`, `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md`, `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_PRODUCTION_AUDIT.md`  
**Checkpoint 5.4:** Every gap traces to a Phase 1–3 finding (F# / section ref). No unsourced items.

---

## Priority Summary

| Priority | Count |
|---|---|
| **Critical Blocker** | 6 |
| **High** | 9 |
| **Medium** | 5 |
| **Nice-to-have** | 2 |
| **Total** | 22 |

---

## Critical Blockers (resolve first)

### GAP-001 — Missing production entry point `start_server.py` (F3)

| Field | Value |
|---|---|
| **Source** | Repository Audit §7; Handover Audit §2 |
| **Evidence** | `ai-crm/backend/Procfile:1`, `ai-crm/backend/railway.json:6` — file absent |
| **Impact** | Railway/Heroku-style deploy fails immediately; SETU unreachable via documented prod path |
| **Effort** | S (1–4 hours) — add thin wrapper or align Procfile to `uvicorn api_app:app` |
| **Dependencies** | None — unblocks deploy verification |

---

### GAP-002 — `SovereignRoutingAdapter` mis-initialized (F1)

| Field | Value |
|---|---|
| **Source** | Repository Audit §3.1, §8.3; Handover Audit §4.7 |
| **Evidence** | `api_app.py:253` passes `setu_store`; adapter expects callable validator `sovereign_routing_adapter.py:86-87,108` |
| **Impact** | `POST /setu/route` raises TypeError; sovereign routing proof non-functional |
| **Effort** | S (< 1 hour) — change to `SovereignRoutingAdapter()` |
| **Dependencies** | GAP-004 or working uvicorn path to verify |

---

### GAP-003 — `TraceContinuityMiddleware` blocks non-execution POST endpoints (F5)

| Field | Value |
|---|---|
| **Source** | Repository Audit §3.2, §8.3; Handover Audit §4.6 |
| **Evidence** | Middleware scope `trace_continuity_middleware.py:19-21`; execution fields `trace_continuity.py:7-19` vs signal fields `signal_ingestion.py:9-17` |
| **Impact** | Six POST endpoints reject valid payloads: `/signals/ingest`, three `/niyantran/*`, `/contract/validate`, `/test/failures` |
| **Effort** | M (4–8 hours) — narrow middleware to `/setu/route` or add path exclusions |
| **Dependencies** | GAP-002 for full routing chain test |

---

### GAP-004 — MongoDB drivers missing from `requirements.txt` (F2)

| Field | Value |
|---|---|
| **Source** | Repository Audit §4; Production Audit §6 |
| **Evidence** | `mongodb_connection.py:7-8` imports pymongo/motor; `requirements.txt` has neither |
| **Impact** | Clean pip install → SETU init fails → routes never mount (`api_app.py:283-285`) |
| **Effort** | S (< 1 hour) |
| **Dependencies** | None — should land before GAP-002 verification |

---

### GAP-005 — Live credentials in delivered `ai-crm/backend/.env` (F4)

| Field | Value |
|---|---|
| **Source** | Repository Audit §4; Production Audit §2 |
| **Evidence** | `ai-crm/backend/.env` exists with plaintext MongoDB, JWT, admin, SMTP, Sampada keys (values not reproduced) |
| **Impact** | Active security incident — credential exposure independent of SETU code quality |
| **Effort** | S for rotation; M if git history scrub required |
| **Dependencies** | None — **immediate, out-of-band** |

---

### GAP-006 — Zero automated SETU test coverage (F10)

| Field | Value |
|---|---|
| **Source** | Production Audit §3; Repository Audit |
| **Evidence** | No `test_setu*` or setu references in `ai-crm/backend/tests/` |
| **Impact** | F1/F5 shipped undetected; regressions ungated |
| **Effort** | L (3–5 days) — pytest for trace continuity, routing, signal ingest + boot smoke test |
| **Dependencies** | GAP-002, GAP-003, GAP-004 fixed first |

---

## High Priority

### GAP-007 — Orphaned JavaScript duplicate implementation (F6)

| Field | Value |
|---|---|
| **Source** | Handover Audit §3; Repository Audit §1.2, §8.2 |
| **Evidence** | `ai-crm/integration/*.js`, `ai-crm/middleware/traceContinuityValidator.js` — zero importers |
| **Impact** | New owners follow REVIEW_PACKET to dead code |
| **Effort** | M — archive or delete JS modules; update REVIEW_PACKET |
| **Dependencies** | Document Python as canonical (GAP-016) |

---

### GAP-008 — Orphaned dependency graph engines (JS + Python) (F7)

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.8; Repository Audit §8.2 |
| **Evidence** | `ai-crm/engine/dependency_graph_engine.js`, `ai-crm/backend/setu/dependency_graph_engine.py` — no imports |
| **Impact** | DEPENDENCY_GRAPH_PROOF describes non-integrated capability |
| **Effort** | M–L — wire into routing/telemetry or remove from scope |
| **Dependencies** | Product decision on dependency graph in SETU v1 |

---

### GAP-009 — Sampada dispatch misconfiguration / silent failure (F9)

| Field | Value |
|---|---|
| **Source** | Repository Audit §5; Production Audit §4 |
| **Evidence** | `SAMPADA_SETU_*` in `.env`; `telemetry_layer.py:35-36` swallows exceptions; code default `SAMPADA_SETU_ENABLED=false` |
| **Impact** | Outbound telemetry may fail with zero visibility |
| **Effort** | S — add warning log on dispatch failure; correct base URL |
| **Dependencies** | Staging Sampada credentials |

---

### GAP-010 — CONVERGENCE_GAPS claims outdated

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.1 |
| **Evidence** | Wiring exists `api_app.py:235-303` but POST endpoints broken (GAP-003); storage configured but F2/F4 caveats |
| **Impact** | Misleading gap doc |
| **Effort** | S — rewrite after fixes |
| **Dependencies** | GAP-003 |

---

### GAP-011 — SETU absent from API contract docs and health check

| Field | Value |
|---|---|
| **Source** | Repository Audit §2, §7; Production Audit §4 |
| **Evidence** | No setu in `api_contracts.md`; `/health` modules omit SETU `api_app.py:350-358` |
| **Impact** | Ops cannot detect SETU init failure |
| **Effort** | M (1 day) |
| **Dependencies** | Stable API surface (GAP-003) |

---

### GAP-012 — Gated Bridge is local schema check only

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.1; CONVERGENCE_GAPS |
| **Evidence** | `_default_gated_bridge_validator` — no external call `sovereign_routing_adapter.py:30-42` |
| **Impact** | Governance boundary not enforced by external policy engine |
| **Effort** | L — integrate real Gated Bridge service |
| **Dependencies** | External policy service (clarification from prior owner) |

---

### GAP-013 — Handover replay/telemetry proofs are static fixtures (F12)

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.3; Production Audit §8 |
| **Evidence** | Proof IDs absent from `ai-crm/backend/setu/*.py`; no reproduction harness |
| **Impact** | Ownership cannot trust operational claims |
| **Effort** | M (1–2 days) — run live flow, export Mongo collections |
| **Dependencies** | GAP-001 through GAP-004, GAP-006 |

---

### GAP-014 — Deploy path fragmentation (F3)

| Field | Value |
|---|---|
| **Source** | Repository Audit §7; Production Audit §6 |
| **Evidence** | Dockerfile vs Procfile vs run scripts use different commands |
| **Impact** | Environment drift; SETU may work in Docker but not Railway |
| **Effort** | S — single canonical start command documented |
| **Dependencies** | GAP-001 |

---

### GAP-015 — SETU init failure silent to operators

| Field | Value |
|---|---|
| **Source** | Repository Audit §6; Production Audit §6 |
| **Evidence** | `except Exception` prints warning only `api_app.py:283-285` |
| **Impact** | Production runs without SETU routes; no alert |
| **Effort** | S — fail fast or expose in `/health` |
| **Dependencies** | GAP-011 |

---

## Medium Priority

### GAP-016 — SETU_FLOW_PROOF deployment section overstated

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.6; Production Audit §8 |
| **Evidence** | Claims "Middleware integrated ✅" but POST paths broken |
| **Impact** | Onboarding risk |
| **Effort** | S — update doc after fixes |
| **Dependencies** | GAP-003, GAP-013 |

---

### GAP-017 — "Bucket" adapters use local Mongo, not external Bucket service

| Field | Value |
|---|---|
| **Source** | Repository Audit §4, §8.4 |
| **Evidence** | `BucketLineageAdapter` → `MongoSetuStore.append_lineage_event` |
| **Impact** | Architectural mismatch with TANTRA Bucket naming |
| **Effort** | L — integrate real Bucket API or rename modules |
| **Dependencies** | Bucket service API spec |

---

### GAP-018 — Incomplete SETU collection registry

| Field | Value |
|---|---|
| **Source** | Repository Audit §4 |
| **Evidence** | `setu_signal_ingestion`, `setu_visibility_records` use fallback strings; not in COLLECTIONS dict `mongodb_connection.py:151-156` |
| **Impact** | Index/ops scripts may miss collections |
| **Effort** | S |
| **Dependencies** | None |

---

### GAP-019 — No CRM/Logistics caller integration (F11)

| Field | Value |
|---|---|
| **Source** | Repository Audit §6 |
| **Evidence** | Only `api_app.py` imports setu modules |
| **Impact** | SETU visibility not triggered by real CRM/Logistics events |
| **Effort** | L — define integration points |
| **Dependencies** | Product requirements / scope clarification |

---

### GAP-020 — `ai-crm/backend/main.py` entry point confusion

| Field | Value |
|---|---|
| **Source** | Handover Audit §2 |
| **Evidence** | Minimal inventory API `main.py:1-32` unrelated to SETU |
| **Impact** | Developer may start wrong app |
| **Effort** | S — README clarification |
| **Dependencies** | None |

---

## Nice-to-have

### GAP-021 — SETU omitted from root API feature list

| Field | Value |
|---|---|
| **Source** | Repository Audit §2 |
| **Evidence** | `api_app.py:312-326` features list has no SETU |
| **Impact** | Discoverability |
| **Effort** | S |
| **Dependencies** | GAP-003 |

---

### GAP-022 — Archive or relocate stale proof JSON under ``ai-crm/``

| Field | Value |
|---|---|
| **Source** | Handover Audit §4.3 |
| **Evidence** | `ai-crm/replay_demo.json`, `ai-crm/end_to_end_trace.json` |
| **Impact** | Clutter; mistaken for live data |
| **Effort** | S — move to `ai-crm/docs/setu/fixtures/` after GAP-013 |
| **Dependencies** | GAP-013 |

---

## Sequenced Backlog (Checkpoint 5.3)

```
Immediate (out of band)
  GAP-005 (credential rotation)

Phase A — Unblock verification (Week 1)
  GAP-004 → GAP-001 → GAP-002 → GAP-003 → GAP-014

Phase B — Trust & observability (Week 2)
  GAP-006 (start) → GAP-011 → GAP-015 → GAP-013

Phase C — Architecture clarity (Week 3–4)
  GAP-007 → GAP-010 → GAP-016 → GAP-018 → GAP-009

Phase D — External integration (Month 2+)
  GAP-012 → GAP-017 → GAP-008 → GAP-019
```

---

## Cross-reference Index

| Gap | F# | Phase 1 ref | Phase 2 ref | Phase 3 ref |
|---|---|---|---|---|
| GAP-001 | F3 | Handover §2 | Repo §7 | Prod §6 |
| GAP-002 | F1 | Handover §4.7 | Repo §3.1 | Prod §6 |
| GAP-003 | F5 | Handover §4.6 | Repo §3.2 | Prod §6 |
| GAP-004 | F2 | Handover §4.1 | Repo §4 | Prod §6 |
| GAP-005 | F4 | Handover §4.11 | Repo §4 | Prod §2 |
| GAP-006 | F10 | — | Repo | Prod §3 |
| GAP-007 | F6 | Handover §3 | Repo §1.2 | Prod §8 |
| GAP-008 | F7 | Handover §4.8 | Repo §8.2 | Prod §8 |
| GAP-009 | F9 | — | Repo §5 | Prod §4 |
| GAP-010 | — | Handover §4.1 | — | Prod §8 |
| GAP-011 | — | — | Repo §2, §7 | Prod §4 |
| GAP-012 | — | Handover §4.1 | Repo §1.1 | Prod §2 |
| GAP-013 | F12 | Handover §4.3 | — | Prod §8 |
| GAP-014 | F3 | Handover §2 | Repo §7 | Prod §6 |
| GAP-015 | — | — | Repo §6 | Prod §6 |
| GAP-016 | — | Handover §4.6 | — | Prod §8 |
| GAP-017 | — | Handover §4.6 | Repo §4 | — |
| GAP-018 | — | — | Repo §4 | — |
| GAP-019 | F11 | — | Repo §6 | — |
| GAP-020 | — | Handover §2 | Repo §7 | — |
| GAP-021 | — | — | Repo §2 | — |
| GAP-022 | F12 | Handover §4.3 | — | — |

**Dead/orphaned code coverage:** GAP-007, GAP-008 map to Repository Audit §8.2 items.

**Contradicted claims coverage:** GAP-007, GAP-010, GAP-013, GAP-016 map to Production Audit §8 deductions.

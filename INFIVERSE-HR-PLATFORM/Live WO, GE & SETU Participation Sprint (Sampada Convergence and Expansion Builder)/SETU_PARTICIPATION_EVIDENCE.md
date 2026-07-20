# SETU Participation Evidence (Live WO/GE/SETU Sprint · Phase 5)

**Workflow position:** Steps 5, 9, 10 of 11 (three evidence layers + post-deploy refresh)  
**Prerequisites:** Step 1 employee `workforce_ref_id` for correlation; Steps 9–10 require `ACCESS_AND_INTEGRATION_REQUEST.md`  
**Next step:** Step 6 → `LINEAGE_PROPAGATION_EVIDENCE.md`

---

## Document structure (read in order)

This file has **four layers** — each builds on the previous. Do not skip layers when reviewing acceptance.

| Layer | Step | What it proves | Environment |
|---|---|---|---|
| **Layer 1** | Step 5 | Sampada ingests all 4 signal types; lineage + trace work | Local in-process (2026-06-27) |
| **Layer 2** | Step 9 | Same flows on deployed Render gateway | Live gateway (2026-07-02) |
| **Layer 3** | Step 10 | Partner systems dispatch outbound HTTP to Sampada | Live gateway Tier 2 (2026-07-02) |
| **Layer 4** | Step 11 | Post-deploy re-confirmation after repo pushes | Live gateway (2026-07-03) |

---

## Execution method (summary)

| Layer | Harness / action |
|---|---|
| Layer 1 | `harness/run_capture.py` — Phase 5 section |
| Layer 2 | `harness/run_capture_live.py` |
| Layer 3 | `harness/run_partner_capture.py` + per-partner scripts |
| Layer 4 | Re-run `run_partner_capture.py` after deploy |

**Auth (live layers):** `Authorization: Bearer <API_KEY_SECRET>` — not `GATEWAY_SECRET_KEY`.

---

# Layer 1 — Local in-process SETU participation (Step 5)

## Capture metadata

**Date**: 2026-06-27  
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router  
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; not deployed  
**Auth type used**: API key (platform/admin)  
**Status**: `partial_capture` — Sampada-side mechanics runtime-proven; external callers simulated  
**Raw capture**: `evidence/live_workforce_governance_setu/setu_participation/phase5_signals.json`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario narrative

All four SETU signal types — `niyantran_telemetry`, `artha_payroll_visibility`, `crm_participation`, `setu_aggregation` — were ingested through the real `/v1/setu/signals/{signal_type}` endpoint with realistic payloads, each referencing the Phase 1 employee's `workforce_ref_id = wf-bf29e5b85bc4`. Each signal was read back (scoped list by `signal_type` + `correlation_id`) and trace continuity reconstructed (`/v1/setu/trace/{trace_id}`). The niyantran signal was linked to the Phase 1 lifecycle correlation/trace id (`9fda459e-1916-42f8-81d1-f9a6f7d7f7ec`) to prove cross-system trace continuity (1 signal + 14 workforce/governance audit events).

---

## Verified vs Simulated (Layer 1)

| Capability | Status |
|---|---|
| Sampada-side signal ingestion (all 4 types) | **Verified (runtime-proven)** |
| Ownership metadata per type | **Verified** |
| Lineage envelope (7 fields incl. schema_version) | **Verified** |
| Correlation/trace continuity & replay | **Verified** |
| Scoped signal list | **Verified** |
| External system initiating participation | **Not Yet Available** — Sampada-side simulation only |

---

## Step-by-step evidence table (Layer 1)

| Signal Type | Ingest → signal_id | trace_id | owning_system | List HTTP | Trace HTTP | Ingest Timestamp (UTC) |
|---|---|---|---|---|---|---|
| niyantran_telemetry (linked) | `sig-a101a7ebdd58` | `9fda459e-1916-42f8-81d1-f9a6f7d7f7ec` | niyantran | 200 | 200 (**1 signal / 14 audits**) | 10:27:12.437392Z |
| artha_payroll_visibility | `sig-1abd2cd401c7` | `c71cb3c7-11cb-430a-a3e4-72b00c1c0cfc` | artha | 200 | 200 (1/1) | 10:27:12.468988Z |
| crm_participation | `sig-870d5d57d618` | `b1e11c75-0943-4208-8ec1-99da4cf6fe39` | crm | 200 | 200 (1/1) | 10:27:12.489679Z |
| setu_aggregation | `sig-859ddc573082` | `e709101b-06dc-49bb-a12b-07c3d39719e2` | setu | 200 | 200 (1/1) | 10:27:12.512424Z |

---

## Replay confirmation (Layer 1)

- `GET /v1/setu/trace/9fda459e-1916-42f8-81d1-f9a6f7d7f7ec` → niyantran signal + 14 audit events (cross-system continuity).
- Other three signals each reconstructed own (signal + ingest-audit) trace.

---

# Layer 2 — Live deployed gateway (Step 9)

## Capture metadata

**Date**: 2026-07-02  
**Gateway**: `https://bhiv-hr-gateway-l0xp.onrender.com`  
**Environment**: deployed Render gateway + production Mongo (`bhiv_hr`)  
**Auth**: `Authorization: Bearer <API_KEY_SECRET>`  
**Raw capture**: `evidence/live_workforce_governance_setu/live/20260702T063831Z/`

---

## Step-by-step evidence table (Layer 2)

| Signal Type | signal_id | trace_id | List HTTP | Trace HTTP |
|---|---|---|---|---|
| niyantran_telemetry (linked) | `sig-a810511a2509` | `3d0a7d1a-1be8-4267-af5b-8d239ea25049` | 200 | 200 |
| artha_payroll_visibility | `sig-ea9866e71888` | `95bbcea8-b565-4214-8bf8-a5041d769449` | 200 | 200 |
| crm_participation | `sig-e138e93526f1` | `626f10d3-5764-493a-ba39-2f46c472fe8d` | 200 | 200 |
| setu_aggregation | `sig-78548e3c1c17` | `e3cce9b5-dcee-4f08-a6cf-b5c52f25e0a4` | 200 | 200 |

**Run summary:** 41 calls, all HTTP 200; lifecycle replay event_count=13; decision id `dec-7a2fbd790e70`.

**Shared correlation_id:** `3d0a7d1a-1be8-4267-af5b-8d239ea25049` (threads with partner layers below).

---

# Layer 3 — Partner-initiated live participation (Step 10)

## Capture metadata

**Date**: 2026-07-02  
**Gateway**: `https://bhiv-hr-gateway-l0xp.onrender.com`  
**Auth resolved**: `API_KEY_SECRET` → 200; `GATEWAY_SECRET_KEY` → 401  
**Shared correlation_id**: `3d0a7d1a-1be8-4267-af5b-8d239ea25049`  
**Raw capture**: `evidence/live_workforce_governance_setu/partner_live/20260702T073708Z/`

---

## Auth resolution

| Candidate key | `GET /v1/setu/signals?limit=1` | Partner-facing? |
|---|---|---|
| `API_KEY_SECRET` | **200** | **Yes** |
| `GATEWAY_SECRET_KEY` | **401** | No |

---

## Partner dispatcher inventory

| Partner | Repo | Dispatcher | Sampada route |
|---|---|---|---|
| Artha | `Artha/` | `sampadaAdapter.js` | `/v1/setu/signals/artha_payroll_visibility` |
| CRM | `ai-crm/backend/setu/` | `sampada_dispatcher.py` | `/v1/setu/signals/crm_participation` |
| Logistics | via CRM | `subsystem: "logistics"` | same as CRM |
| Niyantran | `workflow-blackhole/server/` | `setuDispatcher.js` | `/v1/setu/signals/niyantran_telemetry` |

---

## Step-by-step evidence table (Layer 3 — Tier 2)

| Partner | Tier | signal_id | trace_id | Evidence file |
|---|---|---|---|---|
| Artha | Tier 2 | `sig-9802342a158c` | `TRC-20260702-19f21bf0` | `artha_payroll_visibility_capture.json` |
| CRM | Tier 2 | `sig-5ffbd0b0bde4` | `crm-trace-3d0a7d1a` | `crm_participation_capture.json` |
| Logistics | Tier 2 | `sig-3acbbfa3ca0a` | `logistics-trace-3d0a7d1a` | `logistics_crm_participation_capture.json` |
| Niyantran | Tier 2 | `sig-29f9efbb899a` | `trace_demo_002` | `niyantran_telemetry_capture.json` |

All four: real HTTP POST → 200 → confirmed via `GET /v1/setu/signals?signal_type=…&correlation_id=3d0a7d1a-…`.

---

## Verified vs Simulated (Layer 3)

| Capability | Status |
|---|---|
| Partner outbound HTTP to live Sampada (all four) | **Verified Tier 2** |
| Full Tier 1 (business route → server → dispatcher) | **Not Yet Available** |
| Sampada contract unchanged | **Verified** |

---

# Layer 4 — Post-deploy re-confirmation (Step 11)

## Capture metadata

**Date**: 2026-07-03  
**Context:** All partner repos deployed to Render; env verified; functions working  
**Raw capture**: `evidence/live_workforce_governance_setu/partner_live/20260703T100843Z/`

---

## Step-by-step evidence table (Layer 4)

| Partner | Fresh signal_id | HTTP | Notes |
|---|---|---|---|
| Artha | `sig-43d05ebea091` | 200 | After `AI-Artha` + `Artha_Update_T29` aligned on `04608e5` |
| CRM | `sig-b83c10ba250c` | 200 | After `ai-crm` `main` `5633c13` |
| Logistics | `sig-077b665909d2` | 200 | `subsystem: logistics` marker present |
| Niyantran | `sig-89a4b9062553` | 200 | After `workflow-blackhole` `main` `fbcfa73` |

**Harness:** `post_deploy_smoke.py` + `run_partner_capture.py`  
**Gateway tests:** 35 passed (2026-07-02 baseline, re-confirmed post-deploy)

---

## Known limitations (all layers)

- **Tier 2 only** for partner path — dispatcher invoked directly; partner API servers not booted through full business routes.
- **Logistics** has no separate backend — rides `crm_participation` + `subsystem: "logistics"` (owner decision pending).
- **ai-crm** Render runs Node; Python SETU dispatcher not auto-wired to Node API routes.
- Local in-process caveat applies to Layer 1 only.
- Recommend rotating `API_KEY_SECRET` after live captures.

---

## Cross-references

| Topic | Document |
|---|---|
| Lineage field proof | `LINEAGE_PROPAGATION_EVIDENCE.md` |
| Linked workforce lifecycle | `LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md` |
| Access / integration | `ACCESS_AND_INTEGRATION_REQUEST.md` |
| Testing & post-deploy | `TESTING_AND_ACCEPTANCE_EVIDENCE.md` |
| Deployment runbook | `PARTNER_SETU_LIVE_RUNBOOK.md` |
| Running log | `EXECUTION_LOG.md` |
| Raw Layer 1 | `evidence/.../setu_participation/phase5_signals.json` |
| Raw Layer 2 | `evidence/.../live/20260702T063831Z/` |
| Raw Layer 3 | `evidence/.../partner_live/20260702T073708Z/` |
| Raw Layer 4 | `evidence/.../partner_live/20260703T100843Z/` |

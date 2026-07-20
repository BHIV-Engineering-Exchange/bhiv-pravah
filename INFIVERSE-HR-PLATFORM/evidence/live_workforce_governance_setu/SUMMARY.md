# Live WO/GE/SETU Sprint Evidence Bundle — Index

**Date**: 2026-06-27
**Sprint**: Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)
**Environment**: local in-process FastAPI runtime over in-memory async Mongo (`mongomock_motor`). Real runtime code path (real request/response/status/timestamp); **not** the deployed Render gateway and **not** a persistent DB.
**Owner / acceptance authority**: Rishabh Yadav. Builder surfaces evidence only.

Every ID/timestamp in the `docs/*` deliverables traces to a file below. Capture run: 68 API calls, 67×HTTP 200 + 1×HTTP 404 (deliberate negative path).

## Index

| File | Description |
|---|---|
| `capture_index.json` | Master index: environment, all real IDs, per-phase summary counts. |
| `full_capture.json` | Every one of the 68 calls (method, path, request, status, response, correlation id, timestamp). |
| `harness/run_capture.py` | The continuous capture harness that produced all evidence (reproducible). |
| `harness/run_capture_addendum.py` | Supplemental harness added after reading the real Review Feedback: multi-org proof (finding #3) + consolidated replay packet (finding #5). |
| `harness/_envcheck.py` | Environment/package availability check. |
| `addendum/multiorg_and_replay_packet.json` | Supplemental capture: 2 organizations (disjoint listings) + correlation-linked Decision→Challenge→Review→Override→Final replay packet (18 calls, all 200). |
| `workforce_operations/phase1_capture.json` | Phase 1: full lifecycle (org→…→offboard) + 13-event trace-replay. |
| `workforce_operations/phase2_hierarchy.json` | Phase 2: hierarchy traversal, inheritance, admin-vs-client visibility, 404 negative path. |
| `governance_replay/phase3_scenarios.json` | Phase 3: 3 governance scenarios (leave/visibility/approval) full chain + decision replay. |
| `governance_replay/phase4_policy_state.json` | Phase 4: policy definitions list + re-evaluations (policy-state angle). |
| `setu_participation/phase5_signals.json` | Phase 5: 4 SETU signal types ingest + list + trace continuity. |
| `lineage/phase6_lineage.json` | Phase 6: 3 cross-system lineage samples + cross-system trace on lifecycle correlation id. |
| `control_center/phase7_control_center.json` | Phase 7: Control Center audit-events + audit-replay reads. |
| `test_results/compileall_after_gapfix.txt` | `compileall` output immediately after Gap Fix #1. |
| `test_results/pytest_after_gapfix.txt` | pytest output after gap fix (24 passed). |
| `test_results/compileall_final.txt` | Final `compileall` (Phase C). |
| `test_results/pytest_final.txt` | Final pytest incl. new gap-fix tests (**29 passed, 6 warnings**). |
| `live/latest_run.json` | Pointer to latest deployed-gateway run folder. |
| `live/20260702T063831Z/capture_index_live.json` | Live deployment run index (41 calls, status counts, IDs). |
| `live/20260702T063831Z/full_capture_live.json` | Full request/response log for deployed-gateway run. |
| `harness/run_capture_live.py` | Deployed-gateway capture harness (loads env, writes live evidence). |
| `partner_live/latest_run.json` | Pointer to latest partner-initiated live capture. |
| `partner_live/20260702T073708Z/capture_index_partner_live.json` | Partner closeout index (all four systems, Tier 2, real sig ids). |
| `partner_live/20260702T073708Z/SUMMARY.md` | Partner closeout human summary. |
| `harness/run_partner_capture.py` | Partner-initiated live SETU capture harness. |
| `harness/auth_probe.py` | Live gateway auth key probe (status codes only). |

## Key threaded identifiers

- Lifecycle / cross-system correlation id: `9fda459e-1916-42f8-81d1-f9a6f7d7f7ec`
- Employee: `wf-bf29e5b85bc4` (id `6a3fa580df4f34fc035c561d`)
- Org `6a3fa580df4f34fc035c5611`; depts A/B/C `…5617 / …5619 / …561b`
- Governance decisions: `dec-502dd9179340` → `dec-847bc3155d34` (2-link replay), `dec-b40efca0fdd0`, `dec-9f508b6e94b4`
- SETU signals: `sig-a101a7ebdd58` (niyantran, linked), `sig-1abd2cd401c7` (artha), `sig-870d5d57d618` (crm), `sig-859ddc573082` (setu)

## Runtime changes made this sprint (additive only)

- Gap Fix #1: `transition_type` field + `employee_promotion` audit action in `backend/services/gateway/app/workforce_lifecycle.py`.
- Gap Fix #2: `schema_version` confirmed already present in `backend/services/gateway/app/lineage_envelope.py` (no change).
- New additive test file `backend/tests/gateway/test_live_workforce_governance_setu_gapfix.py`.

## Live deployment addendum (2026-07-02)

- Deployed gateway capture completed via `harness/run_capture_live.py`.
- Run id: `20260702T063831Z`; total calls: **41**; status counts: `{"200": 41}`.
- Threaded IDs:
  - Lifecycle correlation id: `3d0a7d1a-1be8-4267-af5b-8d239ea25049`
  - Decision id: `dec-7a2fbd790e70`
  - SETU signals: `sig-a810511a2509`, `sig-ea9866e71888`, `sig-e138e93526f1`, `sig-78548e3c1c17`

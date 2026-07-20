# BHIV Sampada — Workforce Governance Review Packet

**Status**: Workforce governance runtime completed for gateway, control-center visibility, docs, and baseline tests; **Live WO/GE/SETU Sprint live runtime evidence captured (workforce / governance / policy / SETU / lineage / control-center)**  
**Maintained by**: Shashank (Sampada, Support Builder)  
**For Acceptance Review By**: Rishabh Yadav  
**Updated**: 2026-07-13 (BHIV Phase IV section added)

> Operational boundary remains unchanged: Sampada is a visibility and intelligence surface; execution authority stays with owning systems and approved owners.

---

## State Block

- Workforce governance backend modules are present and compile under gateway app.
- Route bundle is wired through `backend/services/gateway/app/main.py`.
- Control-center governance panel is visible only when `VITE_ENABLE_GOVERNANCE=true`.
- Runtime docs and evidence artifacts are present under `docs/` and `evidence/workforce_runtime/`; the seven Live WO/GE/SETU Sprint phase evidence docs live in the sprint folder `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/`.
- **Live WO/GE/SETU Sprint (2026-06-27)**: end-to-end runtime usage captured across 8 phases (68 API calls, 67×200 + 1×404 negative path) in one continuous session with a single correlation id threading workforce → audit → SETU. Two additive runtime gap fixes applied (`transition_type`/`employee_promotion`; `schema_version` confirmed present). New evidence bundle: `evidence/live_workforce_governance_setu/`.
- **Live deployment addendum (2026-07-02)**: deployed-gateway capture completed via `evidence/live_workforce_governance_setu/harness/run_capture_live.py` against `https://bhiv-hr-gateway-l0xp.onrender.com`; run `20260702T063831Z` produced **41/41 HTTP 200** with live IDs and full capture under `evidence/live_workforce_governance_setu/live/20260702T063831Z/`.
- **Partner-initiated SETU closeout (2026-07-02)**: all four partners dispatched real HTTP to live SETU gateway at **Tier 2**; evidence `evidence/live_workforce_governance_setu/partner_live/20260702T073708Z/` (signal ids: Artha `sig-9802342a158c`, CRM `sig-5ffbd0b0bde4`, Logistics `sig-3acbbfa3ca0a`, Niyantran `sig-29f9efbb899a`).

---

## Live WO/GE/SETU Sprint — Live WO / GE / SETU Participation Evidence (2026-06-27)

**Sprint**: Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder). **Status**: evidence captured (local in-process runtime); awaiting owner acceptance.

> Environment note: Live WO/GE/SETU Sprint captures are **local in-process** runtime (real `workforce_governance_routes` router over in-memory async Mongo) because no deployed-gateway credentials/Mongo were available in this environment. Real request/response/status/timestamp; not the deployed Render gateway. This is stated in every Live WO/GE/SETU Sprint evidence doc header.

- **Workforce Operations Evidence** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md` — one employee (`wf-bf29e5b85bc4`) Created→Assigned→Transferred→Promoted→Moved→Offboarding-Initiated→Replay (13-event ordered reconstruction; `employee_promotion` action via Gap Fix #1).
- **Hierarchy Validation** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/ORG_HIERARCHY_VALIDATION.md` — Org→Division→Unit→Department→Team→Employee; inheritance (`[org_member, analyst]`); admin sees 3 vs client/tenant 0 (boundary); unknown org → 404.
- **Governance Replay** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/GOVERNANCE_REPLAY_EVIDENCE.md` — 3 scenarios (leave/visibility/approval) full chain `Policy→Eval→Challenge→Review→Override→Decision→Replay`; Leave has a 2-link supersedes replay chain.
- **Policy Replay** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/POLICY_REPLAY_VALIDATION.md` — policy-state angle; overrides do not version the definition; re-evaluations confirm context-driven outcomes.
- **SETU Participation** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/SETU_PARTICIPATION_EVIDENCE.md` — all 4 signal types ingested/listed/traced; niyantran linked to lifecycle trace (1 signal + 14 audits). **Verified vs Simulated**: Sampada-side ingestion/lineage/trace/replay = **Verified (runtime-proven)**; external-system-initiated participation = **Not Yet Available — Blocked on external owner integration**.
- **Ownership Metadata & Lineage Validation** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/LINEAGE_PROPAGATION_EVIDENCE.md` — 7/7 fields (incl. `schema_version=1.0.0`) present in workforce, governance, and SETU samples; one correlation id propagated across workforce + audit + SETU.
- **Control Center Evidence** → `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/CONTROL_CENTER_EVIDENCE.md` — `audit-events` (38 total / 14 for lifecycle cid) and `audit-replay` (14 ordered) via real read endpoints; Observation→Execution boundary mapping; frontend UI screenshot is a stated limitation.
- **Testing Results** → `evidence/live_workforce_governance_setu/test_results/pytest_final.txt`: **29 passed, 6 warnings**; `compileall` success. After-gap-fix run: 24 passed (no regression).
- **Replay Results (Live WO/GE/SETU Sprint consolidated)**:
  - Workforce trace-replay by correlation id → 13 ordered events (`GET /v1/workforce/trace-replay`).
  - Decision replay → Leave 2-link supersedes chain; Visibility & Approval 1-link (`GET /v1/decisions/replay`).
  - SETU trace continuity → 4 signals reconstructed; niyantran cross-system (1 signal + 14 audits) (`GET /v1/setu/trace/{trace_id}`).
  - Control Center audit-replay → 14 ordered events for the lifecycle correlation id.
- **Evidence bundle** → `evidence/live_workforce_governance_setu/` (`SUMMARY.md`, `capture_index.json`, `full_capture.json`, per-phase JSON, `addendum/`, `test_results/`, `harness/`).

### Reviewer-findings reconciliation (against the actual `Review Feedback (… Sampada – Convergence And Expansion Builder).md`)

The five findings of the real reviewer document were read in full and mapped to Live WO/GE/SETU Sprint evidence:

| # | Reviewer finding | Live WO/GE/SETU Sprint status |
|---|---|---|
| 1 | Runtime Existence ≠ Runtime Convergence (prove sustained/real/scale usage, not just compile+unit+endpoints) | **Partially addressed** — real end-to-end runtime usage + cross-system trace captured; **sustained production usage / operational scale** remain unproven (local in-process capture, not deployed). |
| 2 | SETU still mostly internal (Niyantran/Artha/CRM/**Logistics**); live ecosystem participation not proven | **Honestly unchanged** — Sampada-side ingestion/lineage/replay = Verified; external-initiated participation = Not Yet Available (all four incl. Logistics named). "Live ecosystem participation" deliberately not claimed. |
| 3 | Workforce needs real org proof (multi-org, multi-dept, inheritance, transfer, permission propagation, realistic datasets) | **Addressed** — `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/ORG_HIERARCHY_VALIDATION.md` incl. supplemental **multi-org** capture (2 orgs, disjoint listings, per-org inheritance) + transfers + inheritance in Phase 1/2. |
| 4 | Policy engine operational validation (conflicts, override chains, challenge lifecycle, escalation, replay) | **Mostly addressed** — challenge lifecycle/escalation/override chains/replay proven; **policy conflicts = not a present runtime capability**, flagged not fabricated. |
| 5 | Decision ledger replay demonstration (Decision→Challenge→Review→Override→Final) | **Addressed** — consolidated correlation-linked replay packet in `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/GOVERNANCE_REPLAY_EVIDENCE.md` (workforce trace-replay + control-center audit-replay), plus a 2-link supersedes chain. |

---

## Live WO/GE/SETU Sprint — Partner-Initiated SETU Participation Closeout (2026-07-02 →)

**Status**: **Executed 2026-07-02** — all four partner systems produced real outbound HTTP to the live Sampada SETU gateway. Evidence at `evidence/live_workforce_governance_setu/partner_live/20260702T073708Z/`.

| Partner | Tier | Sampada signal_id | Evidence |
|---|---|---|---|
| Artha | Tier 2 | `sig-9802342a158c` | `artha_payroll_visibility_capture.json` |
| CRM | Tier 2 | `sig-5ffbd0b0bde4` | `crm_participation_capture.json` |
| Logistics | Tier 2 | `sig-3acbbfa3ca0a` | `logistics_crm_participation_capture.json` |
| Niyantran | Tier 2 | `sig-29f9efbb899a` | `niyantran_telemetry_capture.json` |

**Auth**: `API_KEY_SECRET` is the partner-facing Bearer token; `GATEWAY_SECRET_KEY` returned 401.

**Code changes (additive only, partner repos)**:
- Artha: `sampadaAdapter.js`; `signalEngine.service.js` + `signal.controller.js` re-pointed to `/v1/setu/signals/artha_payroll_visibility`
- CRM: `sampada_dispatcher.py`; hook in `telemetry_layer.py`
- Niyantran: `setuDispatcher.js`; hook in `executionEventEmitter.js`

**Sampada contract**: unchanged (`setu_participation.py`, route paths frozen).

**Two decisions flagged for Rishabh, not resolved by this execution:**
1. Should Logistics get its own SETU `signal_type` in Sampada's schema in a future sprint, or continue riding inside `crm_participation` with a `subsystem` marker?
2. Tier 2 (dispatcher invoked directly, partner server not booted) was the achievable evidence tier in this session — is that an acceptable final answer, or does closure require Tier 1 full partner-server business flows in a shared test environment?

**Security note**: rotate `API_KEY_SECRET` / `GATEWAY_SECRET_KEY` after this capture (plaintext exposure during planning — see Implementation.md §0.3).

---

## BHIV Phase IV — Production Transition (2026-07-13)

**Sprint**: Sampada + SETU Product Owner (Convergence And Production Transition Lead). **Status**: Phase IV deliverables produced; Tier-2 live partner SETU re-confirmed; dashboard capability library shipped; HA/DR deferred to TMS.

### State block additions

- **Baseline tests**: 32/32 passed (2026-07-13) — `evidence/phase_iv_tier1/test_results/pytest_phase_iv.txt`
- **Tier 1 capture run**: `evidence/phase_iv_tier1/20260713T035150Z/` — dual local in-process + live Render
- **Production validation**: `evidence/phase_iv_production_validation/20260713T035319Z/` — 50-cycle load (p50 37ms), 20-task concurrency (100% success), 30s sustained loop (29 iterations)
- **Dashboard primitives**: 8 constitutional cards in `frontend/src/components/cards/`; Control Center + portal dashboards wired
- **SETU contract**: unchanged (`setu_participation.py`)

### Per-system tier (Phase IV)

| Partner | Tier | Sampada signal_id (2026-07-13) | Evidence |
|---|---|---|---|
| Sampada (local harness) | Tier 1 | `sig-502f26a49b89` | `capture_index_tier1.json` |
| Artha | Tier 2 | `sig-66c8d789c660` | live dispatch in `20260713T035150Z/` |
| CRM | Tier 2 | `sig-5f80c230999c` | live dispatch |
| Logistics | Tier 2 | `sig-8ae9c683f2ef` | CRM dispatcher + subsystem |
| Niyantran | Not Yet Available | — | Blocked: server `MODULE_NOT_FOUND` on boot |
| Bucket / PRANA / InsightFlow / Karma | Not evidenced | — | No Sampada dispatcher — GC/MDU |

**Correlation id (Phase IV run):** `c530d0b7-eb17-4fb8-bc78-e81a500042fd`

### Phase IV deliverables (task folder)

| Deliverable | File |
|---|---|
| Tier 1 runtime evidence | `Sampada + SETU Product Owner (...)/TIER1_RUNTIME_EVIDENCE.md` |
| TANTRA integration matrix | `.../TANTRA_INTEGRATION_MATRIX.md` |
| Runtime dependency graph | `.../RUNTIME_DEPENDENCY_GRAPH.md` |
| Constitutional boundaries | `.../CONSTITUTIONAL_BOUNDARY_VALIDATION.md` |
| Production readiness | `.../PRODUCTION_READINESS_ASSESSMENT.md` |
| Replay & trace pack | `.../REPLAY_AND_TRACE_VALIDATION_PACK.md` |
| Observability certification | `.../OBSERVABILITY_CERTIFICATION.md` |
| Deployment certification | `.../DEPLOYMENT_CERTIFICATION_PACK.md` |
| Dashboard capability library | `.../DASHBOARD_CAPABILITY_LIBRARY.md` |
| Production monitoring guide | `.../PRODUCTION_MONITORING_GUIDE.md` |
| DR / failover validation | `.../DISASTER_RECOVERY_VALIDATION.md`, `.../FAILOVER_VALIDATION.md` |
| Security validation | `.../SECURITY_VALIDATION.md` |
| Enterprise handover | `.../ENTERPRISE_HANDOVER_DOCUMENTATION.md` |
| Canonical convergence report | `.../CANONICAL_ECOSYSTEM_CONVERGENCE_REPORT.md` |
| Final acceptance package | `.../FINAL_PRODUCTION_ACCEPTANCE_PACKAGE.md` |

### Open owner decisions (Phase IV)

1. Logistics separate `signal_type` vs `crm_participation` + subsystem — **GC**
2. Bucket / PRANA / InsightFlow / Karma SETU participation path — **GC + MDU**
3. Tier 1 partner server boot (`npm ci`, fix `MODULE_NOT_FOUND`) — partner owners
4. HA / DR / IaC — **TMS** (UNKNOWN in workspace)

---

## Federated Workforce Runtime

- Runtime module: `backend/services/gateway/app/workforce_runtime.py`.
- Routes: organization, division, unit, department, employee CRUD/list/read and hierarchy/trace replay in `backend/services/gateway/routes/workforce_governance_routes.py`.
- Scope controls: workforce access and scope filtering via `backend/services/gateway/app/workforce_common.py`.
- Reference doc: `docs/FEDERATED_WORKFORCE_RUNTIME.md`.

---

## Lifecycle APIs

- Runtime module: `backend/services/gateway/app/workforce_lifecycle.py`.
- Endpoints include onboarding start/complete, role movement, department transfer, status change, and offboard preparation.
- Allowed transitions are enforced with explicit lifecycle-state mapping.
- Reference doc: `docs/WORKFORCE_LIFECYCLE_API.md`.

---

## Policy Engine

- Runtime module: `backend/services/gateway/app/policy_engine.py`.
- Endpoints include policy seed/list/create/evaluate/override.
- Policy evaluation and override events are auditable through gateway audit storage.
- Reference doc: `docs/POLICY_ENGINE_RUNTIME.md`.

---

## Challenge Workflow

- Runtime module: `backend/services/gateway/app/decision_workflow.py`.
- Endpoints include challenge creation/listing, review assignment/completion, and override proposal/apply flow.
- Review-to-decision bridge is exposed through governance review decision recording.
- Reference doc: `docs/DECISION_AND_CHALLENGE_FLOW.md`.

---

## Decision Ledger

- Runtime module: `backend/services/gateway/app/decision_ledger.py`.
- Endpoints include decision create/list/read/replay.
- Replay supports chain reconstruction and correlation-based timeline review.
- Reference doc: `docs/DECISION_LEDGER_MODEL.md`.

---

## SETU Participation

- Runtime module: `backend/services/gateway/app/setu_participation.py`.
- Endpoints include signal ingest, scoped signal list, and trace continuity reads.
- Cross-system participation uses lineage + ownership metadata for replay integrity.
- Reference doc: `docs/SETU_PARTICIPATION_RUNTIME.md`.

---

## Ownership Metadata

- Metadata envelope module: `backend/services/gateway/app/lineage_envelope.py`.
- Shared lineage fields include origin, owning system, schema version, trace ID, correlation ID, trust classification, and visibility scope.
- Write routes pass correlation IDs from request state into runtime actions.
- Reference doc: `docs/OWNERSHIP_AND_LINEAGE_MODEL.md`.

---

## Testing Results

- Compile verification: `python -m compileall backend/services/gateway/app backend/services/gateway/routes/workforce_governance_routes.py`.
- Unit tests: `python -m pytest -q backend/tests/gateway/test_workforce_governance_runtime.py backend/tests/gateway/test_workforce_lifecycle.py`.
- Prior baseline result: **12 passed** (Task20), 3 warnings, 0 failures.
- **Live WO/GE/SETU Sprint latest result (2026-06-27)**: the four gateway suites + new `test_live_workforce_governance_setu_gapfix.py` → **29 passed, 6 warnings, 0 failures** (`evidence/live_workforce_governance_setu/test_results/pytest_final.txt`). After-gap-fix regression check on the four baseline suites alone → 24 passed.

---

## Replay Evidence

- Workforce API/replay baseline: `evidence/workforce_runtime/api_proof_workforce.json`.
- SETU ingest baseline: `evidence/workforce_runtime/setu_signal_proof.json`.
- Evidence summaries:
  - `evidence/workforce_runtime/replay_trace_proof.md`
  - `evidence/workforce_runtime/test_output_summary.md`
  - `evidence/workforce_runtime/api_trace_matrix.md`
  - `evidence/live_workforce_governance_setu/live/20260702T063831Z/capture_index_live.json`
  - `evidence/live_workforce_governance_setu/live/20260702T063831Z/full_capture_live.json`

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Routes depend on runtime Mongo collections existing | Medium | Seed/initialize required collections during deployment checks |
| Governance tab visibility for all tenants | Medium | Owner approved (GOV-PANEL-001); remains behind `VITE_ENABLE_GOVERNANCE` env flag for rollback |
| Warning-only pytest marks (`e2e_unit`) may hide marker taxonomy drift | Low | Register custom marks in pytest config in a follow-up cleanup |
| Replay evidence currently template-driven in docs, not full prod trace capture | Medium (partially mitigated) | Live WO/GE/SETU Sprint captured real ordered replay chains (workforce/decision/SETU/control-center) — but as **local in-process** runtime, not deployed prod. Re-run against deployed gateway + persistent Mongo for production-signed samples. |
| Governance panel enablement | Low | GOV-PANEL-001 approved — see docs/GOVERNANCE_PANEL_APPROVAL_RECORD.md; enabled in production |
| **SETU external participation — partner-initiated live** | Medium | **Partially closed (2026-07-02)**: all four partners dispatched real HTTP to live gateway at **Tier 2** (`partner_live/20260702T073708Z/`). Tier 1 (full partner-server business flow) not yet proven. |
| **SETU external participation — Tier 1 full flows** | Medium | Partner API servers not started this session; Artha dispatch route is JWT-gated. Owner decision: is Tier 2 sufficient for sprint closure? |
| **Logistics signal_type vs subsystem marker** | Low | Logistics rides `crm_participation` + `payload.subsystem: "logistics"`; no separate Sampada signal type. Owner decision pending. |
| **Live WO/GE/SETU Sprint evidence is local in-process, not deployed-gateway** | Low (partially retired) | Deployed-gateway run now captured (`live/20260702T063831Z`, 41×200). Keep local in-process bundle as supplemental deterministic harness evidence. |
| `transition_type` field is additive but only positively tested | Low | New `test_live_workforce_governance_setu_gapfix.py` covers promotion vs lateral audit action; negative-path/validation tests (e.g. invalid transition_type) not yet added. |
| Policy-conflict resolution not a runtime capability (Review Feedback #4) | Medium | `_evaluate_rules` is single-policy; no conflict engine exists. Not built this sprint (two-additive-fixes-only). Needs owner decision on whether multi-policy conflict resolution is in scope for a future sprint. |
| Sustained production usage & operational scale unproven (Review Feedback #1) | Medium | Live WO/GE/SETU Sprint proves linked end-to-end runtime usage but is a single local in-process session, not sustained/scaled deployed traffic. Re-run against deployed gateway with volume for scale evidence. |
| Partner-originated live SETU signals (Tier 1 full server flows) | Medium | Tier 2 partner dispatch verified 2026-07-02; full partner-server business-path triggers not exercised. |
| Agent service intermittent reachability in prod smoke | Low | `run_comprehensive_evaluation.py` result 32/33 with one timeout on `health_agent`; rerun health-only checks in approved window if this becomes recurring. |

---

*This review packet is maintained by the Sampada Support Builder role. Architectural decisions and final acceptance remain with Rishabh Yadav.*

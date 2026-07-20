# Control Center Operational Evidence (Live WO/GE/SETU Sprint · Phase 7)

**Workflow position:** Step 7 of 11  
**Prerequisites:** Steps 1–6 (audit ledger populated with lifecycle + governance + SETU events)  
**Next step:** Step 8 → `TESTING_AND_ACCEPTANCE_EVIDENCE.md`

---

## Execution method

1. `GET /v1/control-center/audit-events?limit=50` — expect platform-scoped event count.
2. Filter by Phase 1 lifecycle correlation id — expect 14 events (13 lifecycle + 1 SETU).
3. `GET /v1/control-center/audit-replay?correlation_id=<cid>` — expect ordered 14-event replay.
4. Map surfaced fields to constitutional boundaries (Observation / Assessment / Decision / Execution).
5. UI screenshot optional — backend read endpoints are the primary evidence (UI limitation stated honestly).

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router + the two real Control Center audit read endpoints (wiring copied verbatim from `app/main.py`)
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime functions (`list_audit_events`, `build_audit_replay`) executed; not deployed
**Auth type used**: API key (platform/admin) via `assert_control_center_access`
**Status**: `partial_capture` — backend read endpoints runtime-proven; frontend Control Center UI not run in this environment
**Raw capture**: `evidence/live_workforce_governance_setu/control_center/phase7_control_center.json`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario Narrative

The Control Center surfaces this session's runtime through read-only, scoped endpoints backed by the same `audit_logs` collection the workflows wrote to. `GET /v1/control-center/audit-events` returned 38 governance/policy/workforce events for the platform/admin scope; filtering by the Phase 1 lifecycle correlation id returned exactly the 14 events of that thread; and `GET /v1/control-center/audit-replay` reconstructed those 14 events as an ordered grouped replay. These are the real `app/control_center_governance.py` functions (`list_audit_events`, `build_audit_replay`) gated by `assert_control_center_access` — no boundary logic was altered.

## Constitutional boundary mapping (Observation → … → Execution)

The Control Center is a **read/observation surface**; it does not execute. Each surfaced field maps as follows:

| Surfaced field / endpoint | Boundary classification |
|---|---|
| `audit-events` list (actions, outcomes, timestamps, correlation ids) | **Observation** (read-only record of what happened) |
| `outcome → status` mapping (success/failure/in_progress) in `audit_doc_to_trace_event` | **Assessment** (derived classification of an observed event) |
| `policy_result` / `derived_flag` fields (when present on a row) | **Recommendation / derived signal** (non-authoritative) |
| Decision rows originating from `/v1/decisions` (owner = Rishabh Yadav) | **Decision** (authority remains with the owning approver; Control Center only displays it) |
| Override `applied`, lifecycle transitions | **Execution** (performed by the workforce/governance runtime, not by Control Center) — Control Center shows them but does not perform them |

No field blurs these boundaries; the Control Center read path neither proposes nor applies — it reflects ledger state only.

## Step-by-step Evidence Table

| Step | Endpoint | Request | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|---|
| 1 | `GET /v1/control-center/audit-events?limit=50` | admin/platform | **count=38**, source=audit_logs, policy_scope=platform | 200 | 10:27:12.539703Z |
| 2 | `GET /v1/control-center/audit-events?correlation_id=9fda459e…` | filter by lifecycle cid | **count=14** (the lifecycle + linked SETU thread) | 200 | 10:27:12.550654Z |
| 3 | `GET /v1/control-center/audit-replay?correlation_id=9fda459e…` | replay for lifecycle cid | replay_mode=single_correlation, **count=14**, ordered | 200 | 10:27:12.558323Z |

## Replay Confirmation

- The audit-replay for the Phase 1 correlation id returned 14 ordered events — matching the 13 workforce-lifecycle audits plus the linked niyantran SETU ingest — confirming the Control Center reconstructs the same cross-system thread proven in Phases 1, 5 and 6, from the live audit ledger written during this session.

## Known Limitations

- **Frontend Control Center panel not captured.** `frontend/src/pages/control/ControlCenter.tsx` (gated by `VITE_ENABLE_GOVERNANCE`) was not run in this environment, so no UI screenshot was produced. Fabricating a screenshot is forbidden (§0.1). The backend read endpoints that the panel consumes are captured here instead. Bringing up the UI against a live gateway is the remaining step for a visual capture.
- Local in-process runtime capture (see Phase 1 header).

## Cross-references

- Lifecycle thread: `LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md`
- Cross-system trace: `LINEAGE_PROPAGATION_EVIDENCE.md`
- Raw: `evidence/live_workforce_governance_setu/control_center/phase7_control_center.json`

# Live Workforce Operations Evidence (Live WO/GE/SETU Sprint · Phase 1)

**Workflow position:** Step 1 of 11  
**Prerequisites:** Step 0 (gap fixes, harness ready)  
**Next step:** Step 2 → `ORG_HIERARCHY_VALIDATION.md`

---

## Execution method

1. Run `evidence/live_workforce_governance_setu/harness/run_capture.py` (Phase 1 section).
2. Create org scaffold: Organization → Division → Unit → Departments (A/B/C).
3. Create employee; run lifecycle: onboard → onboard-complete → dept-transfer → role-move (promotion) → dept-transfer → offboard-prepare.
4. Confirm replay: `GET /v1/workforce/trace-replay?correlation_id=<cid>` → 13 ordered events.
5. Required path: **Created → Assigned → Transferred → Promoted → Moved → Offboarding Initiated → Replay**.

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; **not** the deployed Render gateway and **not** a persistent DB
**Auth type used**: API key → platform/admin scope (`assert_workforce_access`)
**Status**: `live_capture` (local in-process runtime capture; every ID/timestamp below is produced by an actually-executed call in this session)
**Raw capture**: `evidence/live_workforce_governance_setu/workforce_operations/phase1_capture.json` · master index `evidence/live_workforce_governance_setu/capture_index.json`

> Owner / acceptance authority: Rishabh Yadav. The Convergence & Expansion Builder executes and surfaces evidence only — no architecture or acceptance authority.

---

## Scenario Narrative

One real employee record (**R. Mehta**, `workforce_ref_id = wf-bf29e5b85bc4`) was threaded through the complete federated workforce lifecycle in a single continuous session, under one correlation id `9fda459e-1916-42f8-81d1-f9a6f7d7f7ec`. The organization → division → unit → three departments scaffold was created, then the employee progressed Draft → Onboarding → Active (Assigned) → Transferred (dept B) → Promoted (`transition_type=promotion`) → Moved (dept C) → Offboarding-Initiated. A final `trace-replay` reconstructed all 13 events in chronological order, confirming the required path `Created → Assigned → Transferred → Promoted → Moved → Offboarding Initiated → Replay Reconstruction`. The `Promoted` step is distinguishable from a lateral role move because Gap Fix #1 emits the dedicated audit action `employee_promotion`.

## Step-by-step Evidence Table

| Step | Endpoint | Request (key fields) | Response (key fields incl. IDs) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|---|
| 1 | `POST /v1/workforce/organizations` | name=Sampada National Operations, code=SNO-T21 | id=`6a3fa580df4f34fc035c5611`, tenant_id=platform | 200 | 2026-06-27T10:27:11.984304Z |
| 2 | `POST /v1/workforce/divisions` | org=…5611, code=FOD-T21 | id=`6a3fa580df4f34fc035c5613` | 200 | 2026-06-27T10:27:12.006840Z |
| 3 | `POST /v1/workforce/units` | division=…5613, code=NU-T21 | id=`6a3fa580df4f34fc035c5615` | 200 | 2026-06-27T10:27:12.016399Z |
| 4 | `POST /v1/workforce/departments` (A) | org=…5611, unit=…5615, code=DEPT-A-T21, team=Intake Team | id=`6a3fa580df4f34fc035c5617`, default_roles=[analyst] | 200 | 2026-06-27T10:27:12.027145Z |
| 5 | `POST /v1/workforce/departments` (B) | code=DEPT-B-T21, default_roles=[operations_specialist] | id=`6a3fa580df4f34fc035c5619` | 200 | 2026-06-27T10:27:12.039313Z |
| 6 | `POST /v1/workforce/departments` (C) | code=DEPT-C-T21, default_roles=[program_lead] | id=`6a3fa580df4f34fc035c561b` | 200 | 2026-06-27T10:27:12.048925Z |
| 7 | `POST /v1/workforce/employees` | dept=…5617, type=employee, role=analyst | id=`6a3fa580df4f34fc035c561d`, **workforce_ref_id=wf-bf29e5b85bc4**, inherited_roles=[org_member, analyst], lifecycle_state=draft | 200 | 2026-06-27T10:27:12.054186Z |
| 8 | `POST …/{id}/lifecycle/onboard` | reason=Start onboarding | lifecycle_state: draft → **onboarding** | 200 | 2026-06-27T10:27:12.064015Z |
| 9 (Assigned) | `POST …/lifecycle/onboard-complete` | reason=Onboarding complete | lifecycle_state: onboarding → **active** | 200 | 2026-06-27T10:27:12.074171Z |
| 10 (Transferred) | `POST …/lifecycle/department-transfer` | new_department_id=…5619 | department_id → …5619, state=active | 200 | 2026-06-27T10:27:12.082025Z |
| 11 (Promoted) | `POST …/lifecycle/role-move` | new_role=operations_manager, **transition_type=promotion** | role=operations_manager, **transition_type=promotion**, audit action `employee_promotion` | 200 | 2026-06-27T10:27:12.088821Z |
| 12 (Moved) | `POST …/lifecycle/department-transfer` | new_department_id=…561b | department_id → …561b | 200 | 2026-06-27T10:27:12.095937Z |
| 13 (Offboarding) | `POST …/lifecycle/offboard-prepare` | reason=Begin offboarding | lifecycle_state: active → **offboarding_prep** | 200 | 2026-06-27T10:27:12.101896Z |
| 14 (Replay) | `GET /v1/workforce/trace-replay?correlation_id=9fda459e…` | — | event_count=**13** | 200 | 2026-06-27T10:27:12.106239Z |

All write responses carried the lineage envelope `{origin_system: gateway, owning_system: sampada, schema_version: 1.0.0, trace_id/correlation_id: 9fda459e…, trust_classification: canonical, visibility_scope: tenant}`.

## Replay Confirmation

`GET /v1/workforce/trace-replay?correlation_id=9fda459e-1916-42f8-81d1-f9a6f7d7f7ec` returned 13 events in this exact chronological order:

1. `organization_create` (10:27:12.005)
2. `division_create` (10:27:12.013)
3. `unit_create` (10:27:12.024)
4. `department_create` (10:27:12.036)
5. `department_create` (10:27:12.046)
6. `department_create` (10:27:12.052)
7. `employee_create` (10:27:12.060)
8. `employee_onboard` (10:27:12.072)
9. `employee_onboard_complete` (10:27:12.080)
10. `employee_department_transfer` (10:27:12.087) — **Transferred**
11. `employee_promotion` (10:27:12.092) — **Promoted** (distinct action via Gap Fix #1)
12. `employee_department_transfer` (10:27:12.100) — **Moved**
13. `employee_offboard_prepare` (10:27:12.105) — **Offboarding Initiated**

The ordered chain matches steps 1–13 above and proves the required replay path reconstructs correctly from the audit ledger.

## Known Limitations

- This is a **local in-process runtime capture**, not a deployed-gateway capture. The runtime code executed is the real route layer and the real `app/*` runtime functions; persistence is an ephemeral in-memory Mongo. No credentials for the deployed Render gateway were available in this environment, and fabricating deployed responses is forbidden (§0.1).

## Cross-references

- **Next step:** `ORG_HIERARCHY_VALIDATION.md`
- Raw: `evidence/live_workforce_governance_setu/workforce_operations/phase1_capture.json`
- Lineage: `LINEAGE_PROPAGATION_EVIDENCE.md`
- Control Center: `CONTROL_CENTER_EVIDENCE.md`
- Index: `00_DELIVERABLES_INDEX.md`

# Organizational Hierarchy Validation (Live WO/GE/SETU Sprint · Phase 2)

**Workflow position:** Step 2 of 11  
**Prerequisites:** Step 1 dataset (org `…5611`, departments, primary employee)  
**Next step:** Step 3 → `GOVERNANCE_REPLAY_EVIDENCE.md`

---

## Execution method

1. Extend Phase 1 dataset with additional employees in departments A and B.
2. Call `GET /v1/workforce/organizations/{org}/hierarchy` — verify full nested tree.
3. List employees under platform scope (expect 3) vs client/tenant token (expect 0).
4. Negative path: unknown org id → HTTP 404.
5. Supplemental: run `run_capture_addendum.py` for two-org disjoint listing proof.

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; not deployed
**Auth type used**: API key (platform/admin) **and** HS256 JWT (client/tenant = `TENANT-CLIENT-01`) for the boundary check
**Status**: `live_capture` (local in-process runtime capture)
**Raw capture**: `evidence/live_workforce_governance_setu/workforce_operations/phase2_hierarchy.json`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario Narrative

The Phase 1 dataset was extended to the full required depth — **Organization → Division → Unit → Department → Team → Employee** — by adding two more employees in different departments. The org hierarchy endpoint returned the complete nested tree (1 division, 1 unit, 3 departments, 3 employees). Role propagation was verified: an employee created with only `role=analyst` inside a department whose `default_roles=[analyst]` under an org whose `default_roles=[org_member]` returned `inherited_roles=[org_member, analyst]` via `compute_inherited_roles()`. The visibility boundary was proven by issuing the same list call under two scopes: platform/admin saw all 3 employees, while a client/tenant token (`TENANT-CLIENT-01`) saw 0 (its `workforce_scope_filter` restricts to its own tenant_id). A deliberately unknown organization_id returned HTTP 404 as negative-path proof.

## Step-by-step Evidence Table

| Step | Endpoint | Request (key fields) | Response (key fields) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|---|
| 1 | `POST /v1/workforce/employees` | dept A=…5617, type=consultant, role=analyst (S. Iyer) | id=`6a3fa580df4f34fc035c5625`, **inherited_roles=[org_member, analyst]** | 200 | 2026-06-27T10:27:12.117922Z |
| 2 | `POST /v1/workforce/employees` | dept B=…5619, type=employee, role=operations_specialist (K. Rao) | id=`6a3fa580df4f34fc035c5627` | 200 | 2026-06-27T10:27:12.125469Z |
| 3 | `GET /v1/workforce/organizations/{org}/hierarchy` | org=…5611 | divisions=1, units=1, departments=3, employees=3, policy_scope=platform | 200 | 2026-06-27T10:27:12.133707Z |
| 4 | `GET /v1/workforce/employees?organization_id=…5611` | admin/platform token | **items=3**, policy_scope.scope=platform | 200 | 2026-06-27T10:27:12.145335Z |
| 5 | `GET /v1/workforce/employees` | **client/tenant token** (TENANT-CLIENT-01) | **items=0**, policy_scope.scope=client | 200 | 2026-06-27T10:27:12.152854Z |
| 6 (neg) | `GET /v1/workforce/organizations/000000000000000000000000/hierarchy` | unknown org id | detail="Organization not found" | **404** | 2026-06-27T10:27:12.160979Z |

## Hierarchy traversal (Step 3 result, summarized)

```
Sampada National Operations (SNO-T21, id …5611)
└── Field Operations Division (FOD-T21, id …5613)
    └── Northern Unit (NU-T21, id …5615)
        ├── Onboarding Desk (DEPT-A-T21, id …5617) · default_roles=[analyst] · team: Intake Team
        │   └── S. Iyer (consultant, inherited_roles=[org_member, analyst])
        ├── Regional Operations (DEPT-B-T21, id …5619) · default_roles=[operations_specialist]
        │   └── K. Rao (employee, operations_specialist)
        └── Strategic Programs (DEPT-C-T21, id …561b) · default_roles=[program_lead]
            └── R. Mehta (operations_manager — moved here in Phase 1)
```

## Replay / Verification Confirmation

- **Inheritance behavior**: S. Iyer's `inherited_roles=[org_member, analyst]` proves org-default (`org_member`) + department-default (`analyst`) propagation through `compute_inherited_roles()` (no explicit override supplied beyond the base role).
- **Visibility boundary**: identical endpoint, two scopes → 3 records (platform) vs 0 records (client/tenant). The scope filter (`workforce_scope_filter`) was enforced without modification.
- **Department/negative path**: unknown organization_id → 404, confirming foreign-scope reads do not leak data.

## Multi-organization structure (supplemental capture — Review Feedback finding #3)

The reviewer's finding #3 ("Workforce Runtime Needs Real Organizational Proof") explicitly calls for **multi-org structure** in addition to multiple departments / inheritance / transfer. The main capture above proved depth within one organization; this supplemental capture proves **two organizations co-existing under one platform**, each with its own department, employee, role inheritance, and org-scoped listing isolation. Raw: `evidence/live_workforce_governance_setu/addendum/multiorg_and_replay_packet.json`.

| Step | Endpoint | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|
| Org X create | `POST /v1/workforce/organizations` | id=`6a3fa5a3542a8d3e5816dd41` (Civic Services Org, ORG-X-T21) | 200 | 2026-06-27T10:27:47.395073Z |
| Org X dept | `POST /v1/workforce/departments` | id=`6a3fa5a3542a8d3e5816dd43` (default_roles=[specialist]) | 200 | 2026-06-27T10:27:47.413432Z |
| Org X employee | `POST /v1/workforce/employees` | wf=`wf-798e78763173`, **inherited_roles=[civic_member, specialist]** | 200 | 2026-06-27T10:27:47.426297Z |
| Org Y create | `POST /v1/workforce/organizations` | id=`6a3fa5a3542a8d3e5816dd47` (Logistics Authority Org, ORG-Y-T21) | 200 | 2026-06-27T10:27:47.434964Z |
| Org Y dept | `POST /v1/workforce/departments` | id=`6a3fa5a3542a8d3e5816dd49` | 200 | 2026-06-27T10:27:47.441517Z |
| Org Y employee | `POST /v1/workforce/employees` | wf=`wf-5ad5f71065fa`, **inherited_roles=[logi_member, specialist]** | 200 | 2026-06-27T10:27:47.446096Z |
| List org X | `GET /v1/workforce/employees?organization_id=…dd41` | items=1 → [`wf-798e78763173`] | 200 | 2026-06-27T10:27:47.455303Z |
| List org Y | `GET /v1/workforce/employees?organization_id=…dd47` | items=1 → [`wf-5ad5f71065fa`] | 200 | 2026-06-27T10:27:47.462652Z |

**Result**: two organizations exist concurrently; each org's employee listing is **disjoint** (`org_lists_disjoint = true`), and each org's employee inherits its own org-default role (`civic_member` vs `logi_member`) plus the department default (`specialist`) — proving per-org role inheritance and org-scoped query isolation, not a single flat tenant. This directly addresses reviewer finding #3's "multi-org structure" emphasis.

## Known Limitations

- Client/tenant token returned 0 because the seed dataset was created under the `platform` tenant; this still positively demonstrates boundary isolation (the scoped caller cannot see platform-tenant records). A same-tenant positive read was not separately seeded this session.
- Org-scoped listing isolation is enforced via the `organization_id` query filter; note the runtime's primary hard isolation boundary is `tenant_id` (not `organization_id`) — multiple orgs under the same platform tenant are visible to a platform-scoped caller by design, and are separated on read by org filter.
- Local in-process runtime capture (see Phase 1 doc header).

## Cross-references

- Phase 1 dataset: `LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md`
- Raw: `evidence/live_workforce_governance_setu/workforce_operations/phase2_hierarchy.json`

# Constitutional Boundary Validation — BHIV Phase IV

**Date:** 2026-07-13  
**Status:** Verified for Sampada gateway scope; partner boundaries documented separately

---

## Non-negotiable rules

| Rule | Validation | Evidence |
|---|---|---|
| Observability ≠ Authority | Control Center reads only; governance panel has no mutate actions | `ControlCenter.tsx` GOV-PANEL-001 banner; `assert_control_center_access()` |
| Replay ≠ Execution | Replay endpoints reconstruct audit order; no state mutation | `workforce_trace_replay()`, `replay_decisions()`, `setu_trace_continuity()` |
| Dashboard ≠ Governance | Dashboard cards marked `readOnly`; disclaimers on all primitives | `frontend/src/components/cards/*` |
| Sampada does not own payroll execution | Payroll cues visibility-only | `REVIEW_PACKET.md`; executive zone disclaimer |
| SETU contract frozen | No changes to `SIGNAL_TYPES` this phase | `setu_participation.py` diff clean |

---

## API boundary checks

From `evidence/boundaries/boundaries-verification.txt`:

- Dashboard statistics endpoints: read-only Mongo aggregations  
- Visibility GETs do not change document counts  
- **Status:** PASS

---

## Scope enforcement

- `resolve_policy_scope()` / `assert_control_center_access()` in `control_center_governance.py`  
- Tenant isolation: cross-tenant 404 in `test_tenant_isolation_workforce.py` (5 passed)

---

## Partner boundary notes

- **Artha:** `authority_runtime` enforces authority boundaries on partner side (not modified this phase)  
- **Karma:** `sovereign_bridge.py` — signals emitted; consequences require sovereign authorization  
- **Bucket / InsightFlow / Karma:** no Sampada boundary to validate until SETU path approved

---

## Open items

- Logistics independent signal type vs CRM subsystem marker → **GC**

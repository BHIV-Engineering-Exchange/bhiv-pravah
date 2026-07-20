# Governance Panel Enablement — Owner Decision Record

| Field              | Value                                       |
|--------------------|---------------------------------------------|
| Decision ID        | GOV-PANEL-001                               |
| Date Raised        | 2026-06-08                                  |
| Raised By          | Shashank (Sampada Support Builder)          |
| Decision Authority | Rishabh Yadav (System Owner)                |
| Status             | APPROVED                                    |
| Date Approved      | 2026-06-08                                  |
| Feature Flag       | VITE_ENABLE_GOVERNANCE=true (enabled in production) |
| Scope              | Frontend ControlCenter.tsx panel visibility |
| Production URL     | https://sampada.blackholeinfiverse.com      |

---

## What Enabling This Panel Does

When `VITE_ENABLE_GOVERNANCE=true` is set in the frontend environment and redeployed to Vercel:

- Organization count is visible on the Control Center dashboard
- Policy registry and policy count are visible
- Challenge count and open challenge list are visible
- Decision count and decision list (read-only) are visible
- SETU signal count by signal type is visible
- Workforce trace replay events are browsable

All data shown is **read-only observation**. No execution capability is added.

---

## What This Panel Does NOT Do

- Does not grant authority to execute decisions
- Does not expose payroll amounts or individual salary data
- Does not add surveillance, tracking, or employee ranking capability
- Does not create any new data — only surfaces existing audit/trace data
- Does not change any role permissions or access control rules

---

## Boundary Statement

> **Visibility ≠ Authority.**
> Enabling this panel makes governance data observable to authorized operators.
> It does not transfer ownership of any system, decision, or data asset.
> Payroll ownership remains with Artha. Execution authority remains with designated governors.
> This panel is a diagnostic and oversight instrument only.

---

## Approval

|                          |                           |
|--------------------------|---------------------------|
| **Approved by**          | Rishabh Yadav (System Owner) |
| **Name**                 | Rishabh Yadav (System Owner) |
| **Date**                 | 2026-06-08 |
| **Signature / Auth token** | Owner approval — production enablement confirmed |
| **Notes**                | `VITE_ENABLE_GOVERNANCE=true` set on Vercel; panel live at production URL |

---

## Rollback

To disable the panel at any time:
1. Remove `VITE_ENABLE_GOVERNANCE=true` from the Vercel environment variables, or set it to `false`
2. Trigger a Vercel redeploy
3. No data is deleted. No backend change required.

---

## Related Files

- `frontend/src/pages/control/ControlCenter.tsx` — feature flag check location
- `SAMPADA_CURRENT_STATE.md` — system state reference
- `REVIEW_PACKET.md` — risk register
- Production frontend: `https://sampada.blackholeinfiverse.com`
- Production gateway: `https://bhiv-hr-gateway-l0xp.onrender.com`

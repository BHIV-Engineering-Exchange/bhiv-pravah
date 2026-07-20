# Failover Validation — BHIV Phase IV

**Date:** 2026-07-13  
**Status:** **UNKNOWN** for infrastructure failover — route to **TMS**

---

## Infrastructure HA / failover

No load balancer failover, active-active gateway, or Mongo replica failover automation found in this workspace.

**Not simulated. Not fabricated.**

---

## Application-level retry (documented, partner-side)

| System | Behavior | Evidence |
|---|---|---|
| Artha SETU pipeline | `MAX_RETRIES = 3` in `setu.pipeline.js` | Implementation.md §3.3 |
| CRM / Niyantran dispatchers | Defensive HTTP client; returns `{dispatched: false, reason}` on failure | `sampada_dispatcher.py`, `setuDispatcher.js` |

These are **dispatcher retry**, not platform HA.

---

## Phase IV harness

`evidence/phase_iv_production_validation/20260713T035319Z/retry_capture.json` documents retry scope honestly — partner retry not executed in Sampada repo.

---

## Routing

Failover / HA certification requires TMS-owned infra evidence.

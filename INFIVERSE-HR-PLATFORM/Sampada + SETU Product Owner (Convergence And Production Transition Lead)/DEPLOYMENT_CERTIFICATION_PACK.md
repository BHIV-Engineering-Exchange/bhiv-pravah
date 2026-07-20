# Deployment Certification Pack — BHIV Phase IV

**Date:** 2026-07-13

---

## Deployed gateway

| Item | Value |
|---|---|
| URL | `https://bhiv-hr-gateway-l0xp.onrender.com` |
| Prior live capture | `evidence/live_workforce_governance_setu/live/20260702T063831Z/` (41/41 HTTP 200) |
| Phase IV partner capture | `evidence/phase_iv_tier1/20260713T035150Z/` |

---

## Auth model (partner-facing)

- Bearer `API_KEY_SECRET` → HTTP 200 on SETU routes  
- `GATEWAY_SECRET_KEY` → HTTP 401 (not used by partner dispatchers)  
- Evidence: `evidence/live_workforce_governance_setu/harness/auth_probe.py`

---

## Sampada deployment artifacts

- Gateway: `backend/services/gateway/` (Render / Docker per existing pipeline)  
- Frontend: `frontend/` with `VITE_ENABLE_CONTROL_CENTER`, `VITE_ENABLE_GOVERNANCE`  
- SETU routes: unchanged `/v1/setu/signals/{signal_type}`

---

## Local deployment validation

- In-process harness proves route wiring without persistent Mongo  
- 32/32 offline tests pass on 2026-07-13

---

## Not certified

- IaC templates for full TANTRA stack — **UNKNOWN / TMS**  
- Multi-region deployment — **UNKNOWN / TMS**

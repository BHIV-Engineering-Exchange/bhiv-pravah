# Enterprise Handover Documentation — BHIV Phase IV

**Date:** 2026-07-13  
**Handover from:** Convergence And Production Transition Lead sprint  
**Acceptance authority:** Rishabh Yadav

---

## What was delivered

1. **Tier 1/2 runtime evidence** — `TIER1_RUNTIME_EVIDENCE.md` + `evidence/phase_iv_tier1/`  
2. **TANTRA integration matrix** — `TANTRA_INTEGRATION_MATRIX.md`  
3. **Dashboard capability library** — 8 primitives under `frontend/src/components/cards/`  
4. **Certification pack** — production readiness, replay, observability, deployment, security, boundaries  
5. **Production validation harness** — `evidence/phase_iv_production_validation/`  
6. **Canonical convergence report** — `CANONICAL_ECOSYSTEM_CONVERGENCE_REPORT.md`  
7. **Updated review packet** — `REVIEW_PACKET.md` (BHIV Phase IV section)

---

## Operator quick start

1. Read `ECOSYSTEM_REPOSITORY_MAP.md` — partner folders are gitignored  
2. Restore deps per map §9 (`backend/venv`, partner `npm ci`)  
3. Run 32-test baseline (see `PRODUCTION_MONITORING_GUIDE.md`)  
4. Enable Control Center: `VITE_ENABLE_CONTROL_CENTER=true`, `VITE_ENABLE_GOVERNANCE=true`

---

## Evidence locations

| Bundle | Path |
|---|---|
| Prior sprint | `evidence/live_workforce_governance_setu/` |
| Phase IV Tier 1 | `evidence/phase_iv_tier1/20260713T035150Z/` |
| Phase IV production validation | `evidence/phase_iv_production_validation/20260713T035319Z/` |
| Implementation analysis | `Sampada + SETU Product Owner (...)/Implementation.md` |

---

## Open decisions for owner

1. Logistics independent `signal_type` vs CRM subsystem — **GC**  
2. Bucket / PRANA / InsightFlow / Karma SETU onboarding — **GC + MDU**  
3. Tier 1 partner server environment — partner owners + TMS  
4. HA / DR / IaC — **TMS**

---

## Constraints carried forward

- Do not modify `setu_participation.py` without owner approval  
- Do not commit partner repos or secrets  
- Unknown stays UNKNOWN until routed

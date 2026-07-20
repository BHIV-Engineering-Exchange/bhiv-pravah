# Access & Integration Request — Live WO/GE/SETU Sprint

**Workflow position:** Required before Steps 9–10 (live gateway + partner closeout)  
**Purpose:** Unblock remaining proof items — deployed gateway access, live DB, and external partner integration  
**Requested by:** Shashank (Sampada, Support Builder)  
**Approval / owner:** Rishabh Yadav  
**Date raised:** 2026-06-27 · last updated 2026-07-03

---

## When to use this document

| Workflow step | Sections needed |
|---|---|
| Step 9 (live deployment capture) | **B** (gateway) + **C** (database) |
| Step 10 (partner SETU closeout) | **D** (all four partners) |
| Step 11 (post-deploy) | B + C + D (all verified) |
| Optional scale test | **E** |

---

## Why this is needed (plain summary)

The system has been proven on a **local practice copy** and Sampada-side ingestion works. Three gaps drove this request:

1. Same behaviour on the **real deployed server** with the **real database** → **RESOLVED** (2026-07-02 live capture)
2. **Live data sent by four external partner systems** → **RESOLVED Tier 2** (2026-07-02 partner closeout; redeployed 2026-07-03)
3. **Sustained higher-volume real use** → **OPEN** (Section E)

---

## Status dashboard

| Section | Topic | Status |
|---|---|---|
| **A** | Owner decisions | Partial — A1 open; A2 open |
| **B** | Live gateway access | **Complete** |
| **C** | Live database access | **Complete** |
| **D** | Partner systems (×4) | **Complete** (Tier 2) |
| **E** | Scale / sustained test | Open |

---

## SECTION A — Owner decision (Rishabh)

- [ ] **A1.** Approval to contact the four external partner teams for live integration.
- [ ] **A2.** Decision on whether "policy-conflict resolution" should be built in a future sprint *(currently not a system capability; flagged honestly — yes/no for roadmap only).*

---

## SECTION B — Live server (deployed gateway) access

- [x] **B1.** Deployed gateway URL  
  _Received:_ `https://bhiv-hr-gateway-l0xp.onrender.com`
- [x] **B2.** API key / access credentials  
  _Received via secure env:_ `backend/.env` (`API_KEY_SECRET`; redacted in docs)
- [x] **B3.** Permission for controlled evidence capture  
  _Completed 2026-07-02:_ `evidence/live_workforce_governance_setu/live/20260702T063831Z/` (41/41 HTTP 200)

**Verification command:** `python evidence/live_workforce_governance_setu/harness/auth_probe.py`

---

## SECTION C — Live database access

- [x] **C1.** Live MongoDB connection string  
  _Received via secure env:_ `backend/.env` (`DATABASE_URL` / `MONGODB_URI`)
- [x] **C2.** Database name  
  _Received:_ `MONGODB_DB_NAME=bhiv_hr`
- [x] **C3.** Read/write permission for evidence capture  
  _Inferred from successful live write/read in production capture_

---

## SECTION D — External partner systems

For **each** of the four systems: repo access, dispatcher wiring, and live test signal.

### D1. Niyantran

| Item | Status | Detail |
|---|---|---|
| Repo received | [x] 2026-07-02 | `workflow-blackhole` |
| Owner / contact | [ ] | — |
| Connection / dispatcher | [x] | `server/services/setuDispatcher.js`; `SAMPADA_SETU_*` env |
| Live test signal | [x] Tier 2 | `sig-29f9efbb899a` (closeout) · `sig-89a4b9062553` (post-deploy 2026-07-03) |
| Evidence | | `partner_live/20260702T073708Z/` · `partner_live/20260703T100843Z/` |
| Deployed | [x] 2026-07-03 | `workflow-blackhole` `main` → Render |

### D2. Artha

| Item | Status | Detail |
|---|---|---|
| Repo received | [x] 2026-07-02 | `Artha` / `Artha_Update_T29` |
| Owner / contact | [ ] | — |
| Connection / dispatcher | [x] | `sampadaAdapter.js`; `SETU_*` env → `/v1/setu/signals/artha_payroll_visibility` |
| Live test signal | [x] Tier 2 | `sig-9802342a158c` · `sig-43d05ebea091` (post-deploy) |
| Evidence | | `partner_live/20260702T073708Z/` · `partner_live/20260703T100843Z/` |
| Deployed | [x] 2026-07-03 | `AI-Artha` + `Artha_Update_T29` `main` aligned (`04608e5`) |

### D3. CRM

| Item | Status | Detail |
|---|---|---|
| Repo received | [x] 2026-07-02 | `ai-crm` (CRM + SETU module + Logistics frontend) |
| Owner / contact | [ ] | — |
| Connection / dispatcher | [x] | `backend/setu/sampada_dispatcher.py`; `SAMPADA_SETU_*` env |
| Live test signal | [x] Tier 2 | `sig-5ffbd0b0bde4` · `sig-b83c10ba250c` (post-deploy) |
| Evidence | | `partner_live/20260702T073708Z/` · `partner_live/20260703T100843Z/` |
| Deployed | [x] 2026-07-03 | `ai-crm` `main` → Render (`backend-nodejs`) |
| Caveat | | Node API on Render; Python SETU dispatcher not auto-wired to Node routes |

### D4. Logistics

| Item | Status | Detail |
|---|---|---|
| Repo received | [x] 2026-07-02 | Inside `ai-crm` — `frontend/src/pages/Logistics.jsx` only; no separate backend |
| Owner / contact | [ ] | — |
| Connection / dispatcher | [x] | CRM dispatcher + `subsystem: "logistics"` |
| Live test signal | [x] Tier 2 | `sig-3acbbfa3ca0a` · `sig-077b665909d2` (post-deploy) |
| Evidence | | `partner_live/20260702T073708Z/` · `partner_live/20260703T100843Z/` |
| Owner decision pending | | Separate `signal_type` vs `crm_participation` + subsystem marker |

---

## SECTION E — (Optional) Scale / sustained-use test

- [ ] **E1.** Go-ahead for higher-volume / repeated run against live server (depends on B + C).

---

## What happens once provided

| Sections complete | Unblocks |
|---|---|
| **B + C** | Production-grade Sampada evidence (Step 9) |
| **D** (per partner) | Partner participation: "Not Yet Available" → "Verified Tier 2" |
| **E** | Sustained-use / scale proof |

> Credentials via secure channel only — never commit to repo or paste in shared docs.

---

## Cross-references

- Master workflow: `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder).md` Steps 9–11
- SETU evidence: `SETU_PARTICIPATION_EVIDENCE.md`
- Deployment runbook: `PARTNER_SETU_LIVE_RUNBOOK.md`
- Running log: `EXECUTION_LOG.md` §Live deployment · §Partner closeout

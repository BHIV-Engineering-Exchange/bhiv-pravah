# SETU Ownership Acceptance Report

**Audit date:** 2026-07-04  
**Repository root:** `ai-crm/` — all paths below are relative to this folder (not parent directories such as `INFIVERSE-HR-PLATFORM/ai-crm`).  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`

**Decision authority:** Incoming Technical Lead (Post-Handover Audit)  
**Evidence basis:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_HANDOVER_AUDIT.md`, `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md`, `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_PRODUCTION_AUDIT.md`, `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_GAP_REGISTER.md`

---

## 1. Ownership Decision

## **Ownership Accepted with Conditions**

SETU cannot be accepted unconditionally. Six **Critical Blockers** (GAP-001 through GAP-006) prevent safe operation as documented and undermine handover proof claims. The Python implementation under `ai-crm/backend/setu/` is real and partially wired, but core POST flows are broken, the declared production deploy path is missing, delivered credentials are exposed, and there is no automated test coverage.

**Acceptance stands only if the conditions in §3 are met within the stated timelines.**

The defects blocking full acceptance are shallow and narrow (a one-line constructor mismatch, two missing `requirements.txt` lines, overly broad middleware scope, a broken deployment file reference, credential rotation) rather than evidence of an unsound architecture — which is why **Deferred** is not warranted, but plain **Accepted** is also not justified while Critical blockers remain.

*(Checkpoint 6.4: Decision consistent with Gap Register — not "Accepted" while Critical Blockers exist.)*

---

## 2. Current System Maturity

**Tier: Prototype — 27/100 production readiness** (see `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_PRODUCTION_AUDIT.md`).

SETU exists as a JWT-authenticated FastAPI router bundle (`ai-crm/backend/setu/routes.py`, **20 endpoints**) mounted from `ai-crm/backend/api_app.py` when initialization succeeds. Trace continuity, telemetry, signal ingestion, Niyantran visibility, contract validation, and UI read endpoints are implemented in Python with MongoDB persistence via `MongoSetuStore`. However, the sovereign routing endpoint is miswired (F1), trace middleware incorrectly guards all POST `/setu/*` paths (F5), the Railway/Procfile entry point file is absent (F3), MongoDB drivers are missing from `requirements.txt` (F2), live credentials sit in delivered `ai-crm/backend/.env` (F4), and there is no automated test coverage (F10). Handover documentation partially describes an obsolete JavaScript implementation and static proof fixtures rather than reproducible runtime evidence.

---

## 3. Conditions for Acceptance

| # | Condition | Gap ID | Deadline |
|---|---|---|---|
| C0 | Rotate all credentials in `ai-crm/backend/.env`; assess git history exposure | GAP-005 | **Immediate** |
| C1 | Single working production start command; `start_server.py` exists or Procfile/railway aligned to `uvicorn api_app:app` | GAP-001, GAP-014 | Day 7 |
| C2 | `POST /setu/route` succeeds with valid execution contract | GAP-002 | Day 7 |
| C3 | Signal ingest + niyantran POST endpoints accept their documented payloads | GAP-003 | Day 14 |
| C4 | `pymongo` + `motor` in `requirements.txt`; clean install boots SETU | GAP-004 | Day 7 |
| C5 | Minimum pytest suite: trace continuity, routing, signal ingest + boot smoke test (≥3 tests) | GAP-006 | Day 30 |
| C6 | Live replay proof exported from MongoDB replacing static JSON fixtures | GAP-013 | Day 21 |
| C7 | SETU status exposed in `/health` or startup fails loud | GAP-011, GAP-015 | Day 21 |
| C8 | Handover docs updated: Python canonical, JS archived, CONVERGENCE_GAPS accurate | GAP-007, GAP-010, GAP-016 | Day 30 |

**Failure to meet C0 immediately or C1–C4 by Day 14 → revert to Ownership Deferred review.**

---

## 4. Major Risks (Critical + High from Gap Register)

1. **GAP-005 — Active credential exposure (F4):** Live database, auth, and third-party API credentials in plaintext in delivered `ai-crm/backend/.env`. Highest urgency, independent of SETU code quality.

2. **GAP-001 / GAP-014 — Deploy path broken (F3):** Procfile and Railway reference missing `start_server.py`; production deploy may never reach SETU code.

3. **GAP-002 — Routing endpoint non-functional (F1):** `SovereignRoutingAdapter(setu_store)` causes runtime failure on the primary execution observation route.

4. **GAP-003 — Middleware overreach (F5):** Trace continuity middleware rejects valid signal and Niyantran payloads — most SETU_FLOW_PROOF curl examples cannot succeed.

5. **GAP-004 — Dependency gap (F2):** Missing MongoDB packages in `requirements.txt` causes silent SETU disable on fresh installs.

6. **GAP-006 — No test safety net (F10):** Zero SETU tests; F1 and F5 shipped undetected; fixes may re-break governance invariants.

7. **GAP-007 / GAP-013 — Documentation untrustworthy (F6, F12):** Handover proofs use static IDs and point to orphaned JS; new owner cannot verify claims without re-proving everything.

8. **GAP-009 — Sampada outbound misconfiguration (F9):** Dispatch may fail silently when env enables outbound but points at wrong base URL.

9. **GAP-012 — Governance is local-only:** Gated Bridge validates JSON shape, not external policy — compliance risk for TANTRA participation.

---

## 5. Recommended Milestones

### Milestone 0 — Security containment (immediate)
- Rotate credentials (C0 / GAP-005)

### Milestone 1 — Operable Core (Days 1–14)
- Fix deploy entry (C1)
- Fix requirements (C4)
- Fix routing adapter + middleware scope (C2, C3)
- Smoke-test all 20 routes manually

### Milestone 2 — Verifiable Trust (Days 15–21)
- Generate live replay proof from MongoDB (C6)
- Add SETU to health endpoint (C7)
- Document env vars for Sampada (GAP-009)

### Milestone 3 — Sustainable Ownership (Days 22–30)
- Pytest suite (C5)
- Update handover docs; archive JS duplicates (C8)
- Document SETU in `api_contracts.md` (GAP-011)

### Milestone 4 — External Integration (Month 2+)
- Real Gated Bridge policy integration (GAP-012)
- External Bucket service or rename (GAP-017)
- CRM/Logistics event hooks (GAP-019)
- Dependency graph wiring decision (GAP-008)

---

## 6. First 30-Day Execution Plan

### Days 1–2 — Security (Milestone 0)
| Action | Files |
|---|---|
| Rotate MongoDB Atlas, JWT, admin, SMTP, Sampada credentials | `ai-crm/backend/.env` (replace with secrets manager / local-only copy) |
| Confirm git history scope for `.env` exposure | `git log --all -- ai-crm/backend/.env` |

### Week 1 — Critical blockers (Milestone 1)
| Day | Action | Files |
|---|---|---|
| 1–2 | Add `pymongo`, `motor` to requirements; verify `MongoSetuStore` init | `ai-crm/backend/requirements.txt` |
| 2–3 | Create `start_server.py` wrapping uvicorn **or** update Procfile/railway.json | `ai-crm/backend/Procfile`, `ai-crm/backend/railway.json` |
| 3–4 | Fix `SovereignRoutingAdapter()` init | `ai-crm/backend/api_app.py:253` |
| 4–5 | Restrict middleware to `/setu/route` only (or exclude signal/niyantran/contract paths) | `ai-crm/backend/setu/trace_continuity_middleware.py`, `ai-crm/backend/api_app.py:276-280` |
| 5–7 | Manual E2E: route → lineage → telemetry; document curl results | — |

### Week 2 — Observability & proof (Milestone 2)
| Day | Action | Files |
|---|---|---|
| 8–10 | Add `setu: operational|degraded|unavailable` to `/health` | `ai-crm/backend/api_app.py:329-362` |
| 10–12 | Run full SETU_FLOW_PROOF curl sequence; capture responses | — |
| 12–14 | Export Mongo SETU collections → replace `ai-crm/replay_demo.json` | ``ai-crm/`` proof files |

### Week 3 — Tests & docs (Milestone 3)
| Day | Action | Files |
|---|---|---|
| 15–18 | Write pytest: trace_id immutability, routing packet, signal ingest, boot smoke | `ai-crm/backend/tests/test_setu_*.py` |
| 18–21 | Update CONVERGENCE_GAPS, REVIEW_PACKET, SETU_FLOW_PROOF | root `*.md` |
| 21 | Mark JS modules deprecated; add `ai-crm/docs/setu/ARCHITECTURE.md` | `ai-crm/integration/`, `ai-crm/middleware/` |

### Week 4 — Hardening
| Day | Action | Files |
|---|---|---|
| 22–25 | Add SETU routes to `api_contracts.md` | `ai-crm/backend/api_contracts.md` |
| 25–28 | Add SETU collections to COLLECTIONS + indexes | `ai-crm/backend/database/mongodb_connection.py` |
| 28–30 | CI gate: pytest setu + import check; acceptance review | `.github/` if present |

---

## 7. Assumptions & Blockers Requiring Clarification

| Item | Assumption made | What would resolve |
|---|---|---|
| Production deploy target | Docker/uvicorn is intended prod path; Railway config is stale | Confirmation from Rishabh on live Railway command |
| External Bucket service | "Bucket" is naming convention for Mongo collections in v1 | Bucket API spec if external service exists |
| Gated Bridge policy service | Not in repo; local validation accepted for Prototype | Policy engine URL + integration contract |
| Sampada gateway | Env vars exist in deployment but not in `.env.example` | Staging credentials + base URL |
| CRM/Logistics producers | No in-repo callers is intentional (external Niyantran/Sampada) | Scope confirmation (GAP-019) |

---

## 8. Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Incoming Technical Lead | _[assign name]_ | 2026-07-04 | __________________ |

This report constitutes the formal post-handover ownership decision by the **incoming Technical Lead**, based solely on evidence in:

- `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_HANDOVER_AUDIT.md`
- `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md`
- `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_PRODUCTION_AUDIT.md`
- `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_GAP_REGISTER.md`

**Decision:** Ownership Accepted with Conditions  
**Rationale:** Substantive SETU code exists and is partially wired, but Critical Blockers (including F4 credential exposure) prevent trusting handover claims or operating safely in production until C0–C4 are closed.

**Next review date:** Day 14 (Critical condition checkpoint)  
**Full acceptance target:** Day 30 (all C0–C8 conditions)

---

## 9. Cross-Consistency Verification (Section 7)

| Check | Status |
|---|---|
| Every Critical/High gap appears in §4 risks | ✅ GAP-001 through GAP-015 covered |
| Every contradicted handover claim in Production Audit §8 | ✅ Reflected in risks GAP-007, GAP-010, GAP-013, GAP-016 |
| Every dead/broken/orphaned finding in Gap Register | ✅ GAP-007, GAP-008, GAP-002, GAP-003, GAP-004 |

**All five deliverables produced and internally consistent.**

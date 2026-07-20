# SETU Production Readiness Audit

**Audit date:** 2026-07-04  
**Repository root:** `ai-crm/` — all paths below are relative to this folder (not parent directories such as `INFIVERSE-HR-PLATFORM/ai-crm`).  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`

**Maturity tier:** **Prototype** (not Alpha — core happy path does not work as wired)  
**Overall score:** **27 / 100**

Scoring derived solely from Phases 1–2 evidence. No handover document tone used. Finding IDs (F#) refer to `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_REPOSITORY_AUDIT.md`.

---

## 1. Dimension Scores

| Dimension | Score (0–5) | Weight | Weighted | Evidence summary |
|---|---|---|---|---|
| Security | 2 | 15% | 6.0 | JWT on all routes; **F4** plaintext credentials in delivered `.env`; Gated Bridge self-attested only |
| Testing | 0 | 15% | 0.0 | Zero SETU test files — F1/F5 shipped undetected |
| Monitoring / Observability | 2 | 12% | 4.8 | Mongo persistence; no SETU in `/health`; F9 silent dispatch failure |
| Performance | 2 | 8% | 3.2 | Async routes + motor; no load tests; not fully exercisable (F1/F2/F5) |
| Deployment | 1 | 20% | 4.0 | F3 missing `start_server.py`; F2 dep gaps; init failure swallowed |
| Disaster Recovery | 2 | 15% | 6.0 | Mongo durability possible; no SETU backup/restore runbooks |
| Documentation quality | 2 | 15% | 6.0 | ~15 contradicted handover claims (see §8) |
| **Total** | | **100%** | **~27** | Formula: (score ÷ 5) × weight% |

---

## 2. Security — Score 2/5

**Strengths**
- All 20 SETU routes require authentication:

```35:35:backend/setu/routes.py
        current_user: User = Depends(get_current_user)
```

- Input validation on execution contracts ```62:69:backend/setu/trace_continuity.py``` and signals via Pydantic ```23:31:backend/setu/signal_ingestion.py```.
- Tenant isolation enforced in `TraceContinuityValidator` (cross-tenant trace reuse rejected).

**Weaknesses**
- **F4 (Critical):** Delivered `ai-crm/backend/.env` contains live MongoDB Atlas credentials, JWT secret, admin password, SMTP credentials, and Sampada API key material in plaintext. This caps the score regardless of other controls.
- No external policy engine — governance is schema validation only; caller can self-attest `governance.gated_bridge.status: "approved"`.
- No tenant-scoped authorization on trace reads beyond route-level JWT.
- `.env.example` has no SETU/Sampada variables — operators may misconfigure outbound dispatch.

---

## 3. Testing — Score 0/5

**Evidence:** Repository search of `ai-crm/backend/tests/*` and `ai-crm/backend/test_*.py` for `setu` returned **zero SETU-specific tests**. Existing tests cover agent, API, CRM — not trace continuity, routing, or signal ingest.

**Rough coverage of `ai-crm/backend/setu/*.py`:** **0%** by automated tests.

**Note:** `POST /setu/test/failures` runs inline handlers ```257:261:backend/setu/routes.py``` — manual self-test only, not CI. Zero coverage is why F1 and F5 shipped undetected.

---

## 4. Monitoring / Observability — Score 2/5

**Telemetry sink:** Events persisted to MongoDB ```46:48:backend/setu/mongo_store.py```.

**Optional external sink:** Sampada HTTP dispatch ```46:79:backend/setu/sampada_dispatcher.py``` — env-gated; code default disabled.

**Gaps:**
- `/health` reports logistics, CRM, infiverse — **not SETU** ```350:358:backend/api_app.py```.
- No structured logging integration (Datadog, etc.) in SETU modules.
- F9: dispatch failures swallowed in `TelemetryLayer.emit` ```35:36:backend/setu/telemetry_layer.py```.
- Success-path telemetry on `/setu/route` cannot be emitted while F1 persists.
- No frontend in repo consumes `SetuUIVisibilityService` endpoints.

---

## 5. Performance — Score 2/5

- Routes are `async def` — e.g. ```122:126:backend/setu/routes.py```.
- Mongo I/O via motor async client — appropriate.
- No load/latency benchmarks found in repository.
- Middleware reads full request body on every POST `/setu/*` ```23:23:backend/setu/trace_continuity_middleware.py``` — acceptable at prototype scale.
- Full performance assessment blocked until F1/F2/F5 resolved.

---

## 6. Deployment — Score 1/5

**Single reproducible path:** Only Docker/local uvicorn paths work reliably.

| Issue | Evidence |
|---|---|
| Missing production entry file | `Procfile` + `railway.json` → `start_server.py` (absent) — F3 |
| requirements gap | No `pymongo`/`motor` in `requirements.txt` — F2 |
| Init failure swallowed | ```283:285:backend/api_app.py``` — SETU silently disabled |
| Dockerfile vs Procfile mismatch | Dockerfile uses uvicorn; Procfile uses missing script |

**Verified working command (local/dev):** `uvicorn api_app:app --host 0.0.0.0 --port 8000`

---

## 7. Disaster Recovery — Score 2/5

- State in MongoDB collections — survives process restart **if MongoDB available**.
- No SETU-specific backup scripts, replication config, or restore runbooks in repo.
- Atlas-level backup policy may exist outside repo — unverifiable from code alone.
- JS in-memory prototype (`traceContinuityValidator.js`) would lose all state — orphaned, not production path.
- `DependencyGraphEngine` is in-memory only — moot while unwired (F7).

---

## 8. Documentation Quality — Score 2/5

**Method:** Ratio of contradicted vs verified claims from `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/SETU_HANDOVER_AUDIT.md`.

| Metric | Value |
|---|---|
| Material claims audited | 49 |
| Verified | 18 (37%) |
| Contradicted | 15 (31%) |
| Partially verified | 12 (24%) |
| Unverifiable | 4 (8%) |

**Documentation-quality deductions (contradicted claims reflected here):**

1. **REVIEW_PACKET** — JS listed as core flow; Python is live (F6).
2. **CONVERGENCE_GAPS** — "Runtime wiring not applied" contradicted by `api_app.py:235-303`; "storage not configured" contradicted by `mongo_store.py` + delivered `.env`.
3. **SETU_FLOW_PROOF** — "Deployment Status ✅" contradicted by F3, F1, F5.
4. **replay_proof / telemetry proofs** — static IDs not generated by running code (F12).
5. **SOVEREIGN_ROUTING_PROOF** — routing adapter miswired at init (F1).
6. **DEPENDENCY_GRAPH_PROOF** — engine code unused in runtime (F7).
7. **Bucket naming** — implies external service; implementation is local Mongo.

**Effective documentation accuracy for a new owner:** ~37% of verifiable claims check out fully. Volume of proof docs does not translate to reliability.

---

## 9. Overall Readiness Justification

SETU has substantial **prototype code** under `ai-crm/backend/setu/` with JWT-protected routes and Mongo-backed persistence design. It is **not production-ready** because:

1. **F3:** Declared Railway/Procfile deploy path is broken (missing entry file).
2. **F1 + F5:** Core POST flows are broken (routing adapter bug + middleware overreach).
3. **F2:** MongoDB drivers missing from `requirements.txt` — silent disable on clean install.
4. **F4:** Active credential exposure in delivered environment.
5. **Zero automated test coverage** — defects found only by manual code reading.
6. Handover documentation materially misidentifies the live implementation and overstates deployment completeness.

**Tier:** **Prototype** — underlying design is coherent and mostly well-implemented at unit level; failures are shallow wiring/packaging defects, not deep architectural flaws. But "well-designed, unverified, and currently non-functional at its core entry point" is Prototype, not Alpha or Beta.

**Checkpoint 4.1:** Score derivable without reading handover docs — based on code inspection, deploy configs, and test search only.

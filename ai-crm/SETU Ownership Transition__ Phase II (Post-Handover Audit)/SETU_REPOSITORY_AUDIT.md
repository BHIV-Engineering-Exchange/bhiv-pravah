# SETU Repository Audit

**Audit date:** 2026-07-04  
**Repository root:** `ai-crm/` — all paths below are relative to this folder (not parent directories such as `INFIVERSE-HR-PLATFORM/ai-crm`).  
**Audit bundle:** `ai-crm/SETU Ownership Transition__ Phase II (Post-Handover Audit)/`

**Scope:** Independent mapping of SETU code, APIs, runtime paths, storage, integrations, build/deploy.  
**Finding IDs (F#):** Carried through to `SETU_GAP_REGISTER.md` as GAP-### items.

---

## 1. Structure & Module Ownership Map

### 1.1 `ai-crm/backend/setu/` (Python — live implementation)

| Module | Public interface | Consumers | State |
|---|---|---|---|
| `routes.py` | `create_setu_router(...)` — 20 routes under `/setu` | `ai-crm/backend/api_app.py:248,263-273,300` | **Implemented & Wired** |
| `trace_continuity.py` | `TraceContinuityValidator`, `extract_execution` | `routes.py`, `trace_continuity_middleware.py`, `api_app.py` | **Implemented & Wired** |
| `trace_continuity_middleware.py` | `TraceContinuityMiddleware` | `api_app.py:276-280` | **Implemented & Wired** (mis-scoped — F5) |
| `sovereign_routing_adapter.py` | `SovereignRoutingAdapter.build_routing_packet` | `routes.py:44`; init at `api_app.py:253` | **Broken integration** — F1 |
| `bucket_lineage_adapter.py` | `BucketLineageAdapter.emit_execution_event`, verify APIs | `routes.py`, `api_app.py:254` | **Implemented & Wired** |
| `telemetry_layer.py` | `TelemetryLayer.emit_*`, `list_events` | `routes.py`, `signal_ingestion.py`, `api_app.py:255` | **Implemented & Wired** |
| `signal_ingestion.py` | `SignalIngestionModule.ingest_sampada_signal` | `routes.py:122`, `api_app.py:256` | **Implemented & Wired** (blocked by F5) |
| `niyantran_integration_adapter.py` | consume_* visibility methods | `routes.py`, `ui_visibility_service.py`, `api_app.py:257` | **Implemented & Wired** (blocked by F5 on POST) |
| `contract_validation.py` | `ContractValidator.validate_*` | `routes.py:204-234`, `api_app.py:258` | **Implemented & Wired** (blocked by F5) |
| `failure_handler.py` | failure handlers + `test_failure_scenarios` | `routes.py`, `api_app.py:259` | **Implemented & Wired** |
| `ui_visibility_service.py` | read-only UI aggregation | `routes.py:270-304`, `api_app.py:260` | **Implemented & Wired** |
| `mongo_store.py` | `MongoSetuStore` persistence | All adapters above | **Implemented & Wired** |
| `sampada_dispatcher.py` | `dispatch_to_sampada` | `telemetry_layer.py:31-34` | **Implemented & Wired** (env-gated; F9 risk) |
| `dependency_graph_engine.py` | `DependencyGraphEngine` | **None** | **Implemented but Orphaned** (F7) |
| `utils.py` | hash helpers | trace_continuity, bucket_lineage | **Implemented & Wired** |

### 1.2 Root `ai-crm/integration/` + `ai-crm/middleware/` (JavaScript — duplicate prototype)

| Module | Consumers | State |
|---|---|---|
| `ai-crm/middleware/traceContinuityValidator.js` | None | **Orphaned** — in-memory store only (F6) |
| `ai-crm/integration/sovereign_routing_adapter.js` | None | **Orphaned** (F6) |
| `ai-crm/integration/bucket_lineage_adapter.js` | None | **Orphaned** (F6) |
| `ai-crm/integration/telemetry_layer.js` | None | **Orphaned** (F6) |

### 1.3 `ai-crm/engine/dependency_graph_engine.js`

| Module | Consumers | State |
|---|---|---|
| `dependency_graph_engine.js` | None | **Orphaned** — mirrors Python engine (F7) |

### 1.4 `ai-crm/contracts/execution/`

| Artifact | Role | Wired to runtime |
|---|---|---|
| `EXECUTION_CONTRACT_SPEC.md` | Canonical contract documentation | Indirect — validators mirror fields (P3) |
| `execution_contract_v1.json` | JSON schema | **Not imported** by Python code — documentation only |

---

## 2. API Surface Audit

All routes from `ai-crm/backend/setu/routes.py` (prefix `/setu`, **20 routes**):

| Method | Path | Auth | Mounted | Middleware compatible? |
|---|---|---|---|---|
| POST | `/setu/route` | `get_current_user` | Yes | **Yes** — only POST whose payload matches execution contract |
| GET | `/setu/lineage/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/telemetry/{trace_id}` | Yes | Yes | N/A |
| POST | `/setu/signals/ingest` | Yes | Yes | **No — F5** |
| GET | `/setu/signals/{trace_id}` | Yes | Yes | N/A |
| POST | `/setu/niyantran/task-state` | Yes | Yes | **No — F5** |
| POST | `/setu/niyantran/submission-state` | Yes | Yes | **No — F5** |
| POST | `/setu/niyantran/execution-status` | Yes | Yes | **No — F5** |
| GET | `/setu/niyantran/timeline/{trace_id}` | Yes | Yes | N/A |
| POST | `/setu/contract/validate` | Yes | Yes | **No — F5** |
| GET | `/setu/bucket/verify/{execution_id}/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/bucket/lineage/{trace_id}` | Yes | Yes | N/A |
| POST | `/setu/test/failures` | Yes | Yes | **No — F5** |
| GET | `/setu/failures/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/candidate/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/tasks/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/signals/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/severity/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/timeline/{trace_id}` | Yes | Yes | N/A |
| GET | `/setu/ui/dashboard/{trace_id}` | Yes | Yes | N/A |

**Auth evidence:** Every handler uses `Depends(get_current_user)` — e.g. ```35:35:backend/setu/routes.py```.

**Contract drift:**
- `ai-crm/backend/api_contracts.md` — **no SETU routes documented**.
- `EXECUTION_CONTRACT_SPEC.md` aligns with `TraceContinuityValidator.REQUIRED_FIELDS` ```7:19:backend/setu/trace_continuity.py```.
- Signal ingestion uses additional fields (`signal_type`, `severity`) not in execution contract spec — intentional separation.

---

## 3. Runtime Flow Tracing

### 3.1 Intended flow: `POST /setu/route`

```
uvicorn api_app:app
  → TraceContinuityMiddleware (POST /setu/*)
  → route_execution (routes.py:31)
  → TraceContinuityValidator.validate
  → SovereignRoutingAdapter.build_routing_packet  ← BREAKS HERE (F1)
  → TelemetryLayer + BucketLineageAdapter
  → MongoSetuStore.append_*
```

### Finding F1 — `SovereignRoutingAdapter` wiring bug (Critical)

```253:253:backend/api_app.py
    routing_adapter = SovereignRoutingAdapter(setu_store)
```

```86:87:backend/setu/sovereign_routing_adapter.py
    def __init__(self, gated_bridge_validator=None):
        self.gated_bridge_validator = gated_bridge_validator or _default_gated_bridge_validator
```

At runtime, `build_routing_packet` calls `self.gated_bridge_validator(execution)` ```108:108:backend/setu/sovereign_routing_adapter.py``` with a `MongoSetuStore` instance — **TypeError: 'MongoSetuStore' object is not callable**. Exception is not caught in `route_execution()` → HTTP 500 on every call.

**Fix scope:** one line — `SovereignRoutingAdapter()` or separate `store` from `gated_bridge_validator` parameters. All other adapter constructor calls in `api_app.py` match their class signatures; F1 is isolated.

### 3.2 Intended flow: `POST /setu/signals/ingest` (and five other POST endpoints)

```
TraceContinuityMiddleware intercepts ALL POST /setu/*
  → expects execution contract body (11 required fields)
  → signal payload has trace_id, entity_id, signal_type, severity ...
  → validation fails: execution_missing_fields
```

### Finding F5 — ai-crm/middleware/endpoint contract mismatch (Critical)

```19:21:backend/setu/trace_continuity_middleware.py
        if not request.url.path.startswith(self.path_prefix) or request.method.upper() not in self.methods:
            return await call_next(request)
```

```62:69:backend/setu/trace_continuity.py
        missing = [field for field in REQUIRED_FIELDS if execution.get(field) is None]
        if missing:
            raise TraceContinuityError(..., "execution_missing_fields", ...)
```

**Effect:** Six POST endpoints (`/signals/ingest`, three `/niyantran/*`, `/contract/validate`, `/test/failures`) are rejected before route handlers run. Only `POST /setu/route` is middleware-compatible — and F1 breaks that endpoint too.

### 3.3 Divergence from `ai-crm/SETU_FLOW_PROOF.md`

| SETU_FLOW_PROOF claim | Actual trace |
|---|---|
| Signal ingest works with sample curl | Blocked by middleware unless body is full execution contract |
| All phases "COMPLETED" end-to-end | Code exists; POST paths broken or untested |
| Middleware preserves trace on signals | Middleware rejects non-execution payloads |

---

## 4. Database / Storage Schema

**Store:** `MongoSetuStore` → MongoDB via `database.mongodb_connection.get_async_db()`.

| Collection constant | Used for |
|---|---|
| `setu_trace_lineage` | Trace records |
| `setu_trace_logs` | Trace continuity + failure logs |
| `setu_telemetry_events` | Telemetry stream |
| `setu_lineage_events` | Lineage events |
| `setu_signal_ingestion` | Ingested signals (fallback string in mongo_store) |
| `setu_visibility_records` | Niyantran visibility (fallback string) |

**Evidence:** ```5:10:backend/setu/mongo_store.py```, ```151:156:backend/database/mongodb_connection.py```.

**Assessment:**
- Not in-memory mock — real MongoDB driver calls ```46:48:backend/setu/mongo_store.py```.
- **Not external "Bucket" service** — `BucketLineageAdapter` persists to local Mongo collections ```36:36:backend/setu/bucket_lineage_adapter.py``` despite naming.
- Durability requires `MONGODB_URL` / local Mongo; delivered `ai-crm/backend/.env` contains `MONGODB_URL` (F4).
- No backup/restore logic in SETU modules.

### Finding F2 — Missing `pymongo`/`motor` in `requirements.txt` (Critical)

```7:8:backend/database/mongodb_connection.py
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
```

`ai-crm/backend/requirements.txt` (25 lines) lists neither package. Clean `pip install -r requirements.txt` → `ImportError` caught by ```283:285:backend/api_app.py``` → SETU router never mounts, with only a printed warning.

### Finding F4 — Live secrets in delivered `ai-crm/backend/.env` (Critical — security)

`ai-crm/backend/.env` exists in the delivered workspace and contains plaintext keys for MongoDB Atlas (`MONGODB_URL`), JWT signing, admin password, SMTP, and Sampada API credentials (values not reproduced in this audit). **Rotate all credentials immediately** and verify whether the file was ever committed to git history.

---

## 5. Sampada Dispatch Path

`sampada_dispatcher.py` performs real outbound `httpx` POST, gated by `SAMPADA_SETU_ENABLED` (code default: `false` ```17:18:backend/setu/sampada_dispatcher.py```). Delivered `ai-crm/backend/.env` contains `SAMPADA_SETU_ENABLED` and `SAMPADA_SETU_BASE_URL` keys.

### Finding F9 — Sampada dispatch misconfiguration risk (High)

If `SAMPADA_SETU_ENABLED=true` with `SAMPADA_SETU_BASE_URL` pointing at localhost (as reported in delivered environment), dispatch fails outside local dev. `TelemetryLayer.emit()` swallows dispatch exceptions ```35:36:backend/setu/telemetry_layer.py``` with no log line — silent failure mode. Note: `sampada_dispatcher.py` does log wire failures at warning level when dispatch itself is reached; the telemetry wrapper still suppresses all exceptions.

---

## 6. Integration Points with CRM & Logistics

| Integration | Evidence | Finding |
|---|---|---|
| SETU called from CRM | Only `api_app.py` imports `setu.*` | **No direct CRM→SETU coupling** (F11) |
| SETU called from Logistics | Same | **No direct Logistics→SETU coupling** (F11) |
| Shared auth | `auth_system.get_current_user` on all SETU routes | **Shared** (P1) |
| Shared database | CRM + SETU use same MongoDB via adapter | **Shared infrastructure** |
| Outbound Sampada | `sampada_dispatcher.py` — opt-in via env | **Additive side-effect** (F9) |
| Telemetry → external sink | MongoDB + optional Sampada HTTP | No log aggregator integration |

**Coupling risk:** SETU init failure is caught silently ```283:285:backend/api_app.py``` — CRM continues without SETU.

---

## 7. Build & Deployment Process

| Mechanism | Start command | SETU reachable? |
|---|---|---|
| `ai-crm/backend/Dockerfile` | `uvicorn api_app:app --host 0.0.0.0 --port 8000` | Yes (if Mongo + deps OK) |
| `ai-crm/backend/Procfile` | `python start_server.py` | **No** — file missing (F3) |
| `ai-crm/backend/railway.json` | `python start_server.py` | **No** — file missing (F3) |
| `ai-crm/backend/run_project.sh` | `uvicorn api_app:app` | Yes |
| `ai-crm/backend/docker-entrypoint.sh` | `uvicorn api_app:app` | Yes |
| `ai-crm/backend/main.py` | Inventory-only FastAPI | **No SETU** |

### Finding F3 — Conflicting deployment declarations (Critical)

Only Docker/local uvicorn paths are reproducible. Railway and Procfile both reference `start_server.py`, which does not exist.

**Health check:** `/health` exists ```329:362:backend/api_app.py``` but **does not report SETU module status**.

---

## 8. Duplicate / Dead / Broken / Inconsistent Code

### 8.1 Missing code

| Item | Referenced in | Evidence |
|---|---|---|
| `ai-crm/backend/start_server.py` | `Procfile:1`, `railway.json:6` | File absent — `Test-Path` → False (F3) |

### 8.2 Dead code (zero live-path importers)

| Path | Evidence |
|---|---|
| `ai-crm/middleware/traceContinuityValidator.js` | No importers (F6) |
| `ai-crm/integration/sovereign_routing_adapter.js` | No importers (F6) |
| `ai-crm/integration/bucket_lineage_adapter.js` | No importers (F6) |
| `ai-crm/integration/telemetry_layer.js` | No importers (F6) |
| `ai-crm/engine/dependency_graph_engine.js` | No importers (F7) |
| `ai-crm/backend/setu/dependency_graph_engine.py` | No importers (F7) |

### 8.3 Broken integrations

| Issue | Location | Impact |
|---|---|---|
| `SovereignRoutingAdapter(setu_store)` | `api_app.py:253` | `/setu/route` crashes (F1) |
| Middleware on all POST `/setu/*` | `trace_continuity_middleware.py:19-21`, `api_app.py:279` | Six POST endpoints blocked (F5) |
| Missing MongoDB deps | `requirements.txt` vs `mongodb_connection.py:7-8` | Silent SETU disable (F2) |
| SETU router included only on startup | `api_app.py:298-300` | If init fails, routes never mount |

### 8.4 Architectural inconsistencies

| Issue | Detail |
|---|---|
| Dual language adapters | JS at ``ai-crm/integration/`` + ``ai-crm/middleware/`` vs Python in `ai-crm/backend/setu/` — only Python wired (F6) |
| Dual dependency graph engines | `ai-crm/engine/*.js` and `ai-crm/backend/setu/*.py` — neither used (F7) |
| "Bucket" naming vs Mongo storage | Adapters named for external Bucket; store is local Mongo |
| Multiple entry points | `main.py`, `api_app.py`, missing `start_server.py` — deploy confusion (F3) |

---

## 9. Positive Findings

- **P1:** Every SETU route requires `Depends(get_current_user)` — real JWT verify chain, not a stub.
- **P2:** `TraceContinuityValidator`/`TraceContinuityMiddleware` implement trace-id immutability, tenant-boundary checks, and lineage-hash computation — real logic for compatible endpoints.
- **P3:** `EXECUTION_CONTRACT_SPEC.md` required-fields list matches Python `REQUIRED_FIELDS` exactly.
- **P4:** `sampada_dispatcher.py` fail-open design is sound in principle (downstream outage should not block core telemetry), independent of F9 misconfiguration.

---

## 10. Inventory Verification (Checkpoint 1.1)

| Area | Expected location | Verified present |
|---|---|---|
| Core SETU module | `ai-crm/backend/setu/` | Yes — 16 files |
| Legacy JS adapters | `ai-crm/integration/`, `ai-crm/middleware/` | Yes — orphaned |
| Execution contracts | `ai-crm/contracts/execution/` | Yes |
| Handover proofs | Root `*_PROOF.md`, etc. | Yes — 13 artifacts |
| Backend entry points | `api_app.py`, `Procfile`, `railway.json` | Partial — `start_server.py` missing |
| Dependency engine | `ai-crm/engine/` + `ai-crm/backend/setu/dependency_graph_engine.py` | Yes — both orphaned |

**Checkpoint 3.8:** All findings above cite concrete file paths.

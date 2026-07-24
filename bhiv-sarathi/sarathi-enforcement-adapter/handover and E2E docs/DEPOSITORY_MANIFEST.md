# Sarathi — Central Depository Transfer Manifest (Phase 5)

This manifest makes Sarathi transfer-ready: it catalogs every package a new
owner / depository needs, points to where each lives, and states what is proven
vs. pending. The transfer-ready archive is the repository itself (pushed to the
central depository / version control); this manifest is its index.

---

## 1. Asset package (the runnable system)

| Item | Location |
|---|---|
| Source code | 135 `.go` files (root) + `go.mod` / `go.sum` |
| Build command | `go build -o sarathi-enforcement-adapter.exe .` |
| Config/schema inputs | `evaluator_registry_config.json`, `registry_config.json`, `sovereign-response-schema.json`, `execution_trace_schema.json` |
| Key material | `live/keys/` (enforcement + peer keys) |
| Container build | `Dockerfile` |

Reproducibility: a clean clone builds with `go build` and passes `go vet` with no
output. No database required at runtime.

---

## 2. Documentation package (onboarding < 30 min)

| Document | Purpose |
|---|---|
| `SYSTEM_OVERVIEW.md` | What Sarathi is and does. |
| `ARCHITECTURE_FLOW.md` | End-to-end data flow. |
| `REPO_MAP.md` | Where every subsystem lives. |
| `SETUP_GUIDE.md` | Build, run, env vars, cloud deploy, troubleshooting. |
| `FAQ.md` | Common questions. |
| `BUILD_STATE.md` | What works / incomplete / tech debt. |
| `PENDING_WORK.md` | Open items, owners, done-criteria. |

Suggested reading order for a new owner: `SYSTEM_OVERVIEW` → `SETUP_GUIDE` →
`ARCHITECTURE_FLOW` → `REPO_MAP` → `BUILD_STATE` → `PENDING_WORK`.

---

## 3. Deployment package

| Item | Location |
|---|---|
| Build + run + env reference | `SETUP_GUIDE.md` §3–§6 |
| Cloud binding requirement | `SETUP_GUIDE.md` §6 (`SARATHI_SERVICE_ADDR=0.0.0.0:<port>`) |
| Production boot gates | `SETUP_GUIDE.md` §5.5 |
| Container build | `Dockerfile` |

---

## 4. Testing package

| Item | Location |
|---|---|
| E2E validation runbook | `E2E_VALIDATION.md` |
| Bucket integration runbook | `BUCKET_TEST_COMMANDS.md` |
| Bucket test script | `scripts/test_bucket.ps1` |
| InsightFlow test script | `scripts/test_insightflow.ps1` |
| InsightFlow wire contract | `INSIGHTFLOW_INTEGRATION.md` |
| Captured proof | `validation screenshots/` (see §6) |
| Go unit/integration tests | 17 `*_test.go` files |

---

## 5. Review package

| Item | Location |
|---|---|
| Integration/deployment review | `REVIEW_PACKET.md` |
| Closure report | `SARATHI_CLOSURE_REPORT.md` |
| This manifest | `DEPOSITORY_MANIFEST.md` |

---

## 6. Proof evidence (captured)

Under `validation screenshots/`:

| Evidence | File(s) | Result |
|---|---|---|
| Clean build + vet | `deployment validation- build.png` | no errors |
| Service boot | `sarathi service .png` | banner + routes, READY |
| Health | `Sarathi health check.png` | healthy, bridge_active True |
| Deep health | `sarathi deep healt check.png` | healthy + checks |
| 5 E2E traces | `bucket trace -1.png` … `-5.png` | all `success:true`, `chain_verified:true` |
| Chain advance | `bucket-artifact-1.png` … `-5.png` | artifact_count 0 → 5 |
| Failure handling | `bucket failure test-duplicate .png` | HTTP 400, fail-closed chain integrity |

---

## 7. Transfer readiness statement

| Phase (task.md) | Deliverable | State |
|---|---|---|
| 1 Build Audit | `BUILD_STATE.md` | ✅ |
| 2 Handover Package | `SYSTEM_OVERVIEW`, `ARCHITECTURE_FLOW`, `REPO_MAP`, `SETUP_GUIDE`, `FAQ`, `PENDING_WORK` | ✅ |
| 3 Deployment Validation | proof screenshots | ✅ captured |
| 4 E2E Testing | 5 traces + failure case | ✅ captured |
| 5 Depository Transfer | this manifest + repo archive | ✅ |
| 6 Closure Report | `SARATHI_CLOSURE_REPORT.md`, `REVIEW_PACKET.md` | ✅ |

**Honest open items (external blockers, documented in `PENDING_WORK.md`):**
- InsightFlow live propagation — blocked on InsightFlow's server (returns 500 on
  all POST endpoints; independently verified as server-side). Sarathi side ready.
- Bridge inbound JWKS and Core live E2E — pending reachable URLs.
- Full service-ingest + fan-out E2E — gated on the two items above; the captured
  E2E proves the live Bucket custody path instead.

**Conclusion:** Sarathi is transfer-ready. The enforcement asset is complete,
documented, deployment-ready, and proven against the live Bucket peer. Remaining
items are integration closures owned outside Sarathi and are fully documented
with owners and done-criteria. A new developer can take ownership from this
repository and its documents alone.

# Sarathi — Review Packet (Operational Closure)

**Purpose:** the reviewer's single-document view of what Sarathi is, how the
enforcement path works, what is implemented and verified, what is proven, and
what remains open. Scope per task.md: **operational closure** — complete,
document, deploy, prove. Not redesign, not new features.

**Status:** Build green, vet clean, full test suite green (161/161). Bucket
integration verified live end-to-end. Handover package complete. Deployment +
E2E proof captured.

**Verified this session:** `go build`, `go vet`, `go test ./...`, and the live
Bucket exchange — all re-run and confirmed (see §6).

---

## 1. Entry point

Sarathi is a Policy Enforcement Point exposed as a long-lived HTTP service.

- **Start:** `./sarathi-enforcement-adapter --service`
- **Primary ingest:** `POST /v1/ingest-decision` — enforces a decision and, when
  enabled, fires peer propagation.
- **TANTRA convergence ingest:** `POST /sarathi/enforce` — Sovereign Core posts a
  signed `tantra.decision.v1` decision; Sarathi runs the 12-step verifier, then
  proxies into the same enforcement pipeline.
- **Receipt callback:** `POST /v1/downstream-ack` — peers post signed receipts.
- **Health / metrics:** `GET /health`, `/health/deep`, `/metrics`,
  `/metrics/prometheus`.
- **Public key discovery:** `GET /sarathi/.well-known/jwks.json` (peers fetch
  Sarathi's PUBLIC key to verify its tokens; private keys never leave the host).

Listen address is `SARATHI_SERVICE_ADDR` (default `127.0.0.1:8443`; set
`0.0.0.0:<port>` on a cloud host). Full env reference: `SETUP_GUIDE.md` §5.

---

## 2. Core execution flow (three files to read in order)

### 2.1 `service_boundary.go` / `service_boundary_tantra.go`
Registers all routes and owns the request boundary. For TANTRA ingest,
`handleSarathiEnforceTantra` runs preflight (method, content-type, key,
pipeline-readiness), invokes the 12-step verifier, performs the API-key
fingerprint check, translates the verified decision into the internal
`ExternalDecision`, and proxies into `handleIngestDecision` so the enforcement
pipeline runs unchanged.

### 2.2 `tantra_verifier.go::Verify`
The 12-step fail-closed verifier: strict body decode → required fields →
evaluator_id format → timestamp skew → signature extract → canonical signing
bytes → registry lookup (5 gates: exists / active / schema / key_id / algorithm)
→ canonical wire round-trip → Ed25519 verify via the active crypto provider →
decision_hash recompute → decision_id recompute → replay-store check. Every step
is a gate; any failure rejects before enforcement.

### 2.3 `service_boundary_propagation_hook.go::firePostIngestPropagation`
Post-ingest peer fan-out, gated by `SARATHI_PROPAGATE_ON_INGEST=1` (default OFF).
Runs entirely in a background goroutine — never blocks the inbound response.
It fans out to:
- **Bucket** (in-chain custody) and **InsightFlow** (off-chain observability) via
  `BHIVTranslatedFanOut` — each peer receives its declared wire shape with the
  sealed canonical response carried as `canonical_response_b64`.
- **Core** (`/v1/enforce`) — the raw canonical envelope for the post-execution
  record.

Every hop writes one row to `proof_logs/peer_propagation_audit.jsonl`; per-peer
outbound body hashes go to `proof_logs/peer_outbound_hashes.jsonl`.

---

## 3. Live execution flow

```
Core ── POST /sarathi/enforce ──► Sarathi
                                     │ 12-step verifier (fail-closed)
                                     │ API-key fingerprint check
                                     │ translate → ExternalDecision
                                     │ enforce + seal (response_hash, chain_binding_hash)
                                     │ sign custody receipt (Ed25519)
                                     │ append audit
                                     ├─► 200 OK + envelope ──► Core
                                     │
                                     ▼ (goroutine, async; only if PROPAGATE_ON_INGEST=1)
                          ┌──────────┼───────────────┐
                          ▼          ▼               ▼
                       Bucket   InsightFlow      Core /v1/enforce
                  (read-back   (4 endpoints,    (post-exec record)
                   verify +     off-chain)
                   chain)            │
                          peers POST signed receipt → /v1/downstream-ack
                                     ▼
                          VerifyReceipt: signature + dual-hash + peer pinning
                          + status ACTIVE + replay rejection
```

Per-execution audit files: `enforcement_audit_backup.jsonl`,
`tantra_translation_map.jsonl`, `sarathi_enforcement_attestations.jsonl`,
`peer_outbound_hashes.jsonl`, `peer_propagation_audit.jsonl`,
`downstream_ack_receipts.jsonl` / `..._rejections.jsonl`, `tantra_replay.jsonl`.

---

## 4. What is implemented and done (closure scope)

| Area | State |
|---|---|
| Enforcement pipeline (PEP) | ✅ Complete; every request transits the gated bridge; fail-closed. |
| 12-step TANTRA verifier | ✅ Implemented; real Ed25519, registry 5-gate lookup, replay store. |
| Crypto-agility | ✅ Ed25519 default + ML-DSA-65 hybrid toggle via one env var; fail-closed on unknown provider. |
| Custody receipts | ✅ Sarathi signs its own receipts under its enforcement key. |
| Peer-key registry | ✅ Pinned per-peer Ed25519 keys; cross-peer impersonation defence; replay rejection. |
| **Bucket integration** | ✅ **Verified live** — `POST /bucket/artifact` 200, read-back `chain_verified: true`, chain advances; adapted to two undocumented live rules (trace_id in payload; genesis omits parent_hash). |
| Dual-hash protocol | ✅ Transport `body_hash` + decision `response_hash`, minted before send, verified on return. |
| Propagation fan-out | ✅ Implemented (Bucket + InsightFlow + Core), env-gated, audited. |
| Audit / observability | ✅ Immutable JSONL trails; health, deep-health, Prometheus metrics. |
| Public-key discovery (JWKS) | ✅ Exposed for peers to fetch; private keys never transported. |
| Handover documentation | ✅ Full package (see §8). |

---

## 5. Failure cases (selected — every gate is fail-closed and audited)

| Scenario | Code | HTTP | Where |
|---|---|---|---|
| Unknown schema_version | `ERR_TANTRA_SCHEMA_VERSION_UNKNOWN` | 400 | `tantra_verifier.go` |
| Extra/unknown field | `ERR_TANTRA_UNKNOWN_FIELD` | 400 | strict decoder |
| Missing required field | `ERR_TANTRA_MISSING_FIELD` | 400 | required-fields gate |
| Timestamp skew > ±300 s | `ERR_TANTRA_TIMESTAMP_SKEWED` | 401 | skew gate |
| Signature invalid | `ERR_TANTRA_SIGNATURE_INVALID` | 401 | Ed25519 verify |
| Evaluator not registered / not active | `ERR_TANTRA_EVALUATOR_NOT_REGISTERED` / `_NOT_ACTIVE` | 403 | registry lookup |
| key_id / algorithm mismatch | `ERR_TANTRA_KEY_ID_MISMATCH` / `_ALG_MISMATCH` | 403 | rotation / downgrade defence |
| API key required / invalid | `ERR_TANTRA_API_KEY_REQUIRED` / `_INVALID` | 401 | fingerprint check |
| decision_hash / decision_id mismatch | `ERR_TANTRA_DECISION_HASH_MISMATCH` / `_ID_MISMATCH` | 409 | mutation evidence |
| Replay within 300 s | `ERR_TANTRA_REPLAY` | 409 | replay store |
| Receipt signature / pinning / replay fail | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | `peer_common.go` / `peer_key_registry.go` |
| Unknown crypto provider / pinning mode | panic at boot | — | fail-closed; refuses to start |

Bucket chain integrity (observed live): a stale `parent_hash` is rejected with
HTTP 400 (`Invalid parent_hash. Expected… Got…`) — fail-closed, chain not
corrupted.

---

## 6. Proof (verified this session)

### 6.1 Build, vet, tests
```
$ go build -o sarathi-enforcement-adapter.exe .   → OK (no output)
$ go vet ./...                                     → OK (no output)
$ go test ./... -count=1                           → ok  4.061s
```
161 test functions defined; **161 PASS**. Coverage spans the TANTRA verifier
(real Ed25519 + hybrid), canonical-JSON determinism, the peer-key registry
(pinning, cross-peer impersonation, replay), and the crypto-agility provider —
all against real code paths, no mocks on the load-bearing crypto.

### 6.2 Deployment proof (`validation screenshots/`)
- Clean build + vet.
- Service boot with full banner and route list.
- `/health` → `status: healthy, service_status: READY, bridge_active: True`.
- `/health/deep` → healthy with bridge / router / service checks.

### 6.3 End-to-end proof (`validation screenshots/`)
- Five complete custody traces (`bucket trace -1..5`): each input → seal →
  write (`success:true`) → log → read-back (`chain_verified: true`).
- Chain advanced `artifact_count` 0 → 5 (`bucket-artifact-1..5`).
- Failure handling: stale `parent_hash` rejected, HTTP 400, fail-closed.

**Honest scope note.** The five traces exercise the live Bucket custody +
chain-integrity path against the real peer (the strongest external proof
available today). They are not driven through `/v1/ingest-decision` with full
fan-out, which additionally needs Bridge inbound auth and a healthy InsightFlow
(both external blockers, §7). The traces cover every stage task.md requires
(input → processing → output → logging → observability → failure handling).

---

## 7. Open items (honest, current)

| # | Item | Owner | Note |
|---|---|---|---|
| 1 | InsightFlow live propagation | InsightFlow team | Their deployed server returns 500 on ALL POST endpoints (and on `/openapi.json`), independent of key and body — a broken deployment on their side. Sarathi side ready and correct. |
| 2 | Bridge inbound JWKS | Joint | Bridge must fetch Sarathi's JWKS from a reachable URL; 401 diagnosed, not closed. |
| 3 | Core live end-to-end | Joint | Endpoints wired; one live post-exec confirmation pending. |
| 4 | Enable propagation in deployment | Operator | Set `SARATHI_PROPAGATE_ON_INGEST=1` + peer URLs + InsightFlow API key. |
| 5 | Cloud listener binding | Operator | Set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>` on a cloud host. |
| 6 | Bucket doc vs deployment | Bucket team | Their doc omits two rules the live server enforces (trace_id placement, genesis parent_hash). Sarathi already adapted. |

Full detail and done-criteria: `PENDING_WORK.md`.

---

## 8. Deliverable inventory (task.md)

| Deliverable | Status | File |
|---|---|---|
| Build audit | ✅ | `BUILD_STATE.md` |
| System overview | ✅ | `SYSTEM_OVERVIEW.md` |
| Architecture flow | ✅ | `ARCHITECTURE_FLOW.md` |
| Repo map | ✅ | `REPO_MAP.md` |
| Setup guide | ✅ | `SETUP_GUIDE.md` |
| FAQ | ✅ | `FAQ.md` |
| Pending work | ✅ | `PENDING_WORK.md` |
| Closure report | ✅ | `SARATHI_CLOSURE_REPORT.md` |
| Review packet | ✅ | this file |
| Depository manifest | ✅ | `DEPOSITORY_MANIFEST.md` |
| Deployment proof | ✅ | `validation screenshots/` |
| E2E proof (5 traces + failure) | ✅ | `validation screenshots/` |
| Integration runbooks | ✅ | `BUCKET_TEST_COMMANDS.md`, `E2E_VALIDATION.md`, `INSIGHTFLOW_INTEGRATION.md` |

---

**Submission status:** Complete per task.md operational-closure scope. The
enforcement asset is built, documented, deployment-ready, and proven against the
live Bucket peer. Remaining items are integration closures owned outside Sarathi
(InsightFlow server health, Bridge/Core reachable URLs), all documented with
owners and done-criteria. A new developer can take ownership from this repository
and its documents alone.

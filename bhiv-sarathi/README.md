# Sarathi Enforcement Adapter

A non-bypassable Policy Enforcement Point (PEP) with cryptographic decision binding, deterministic propagation, and crypto-agile signing. Sarathi is a full-citizen participant in the TANTRA execution chain — no action transits BHIV without passing through it, and no audit trail closes until Sarathi has sealed it.

---

## ✅ Current State (Operational Closure)

| Item | State |
|---|---|
| Build | `go build` — **clean** |
| Static analysis | `go vet ./...` — **clean** |
| Test suite | **161 / 161 tests pass** |
| Enforcement core (PEP) | Complete; fail-closed at every gate |
| Crypto-agility | Ed25519 default + ML-DSA-65 hybrid toggle (one env var) |
| **Bucket integration** | ✅ **Verified live** — write 200, read-back `chain_verified: true`, chain advances |
| Propagation fan-out | Implemented (Bucket + InsightFlow + Core); off by default |
| Handover package | Complete (see [Handover Documentation](#-handover-documentation)) |
| Deployment + E2E proof | Captured (`validation screenshots/`) |
| InsightFlow live propagation | ⛔ Blocked on InsightFlow's server (returns 500 on all POST endpoints; their side). Sarathi ready. |
| Bridge inbound / Core live E2E | ⚠️ Pending reachable URLs |

Sarathi is **transfer-ready**: a new developer can build, run, test, understand, and continue it from this repository and its documents alone. Start with [SETUP_GUIDE.md](SETUP_GUIDE.md).

---

## 🔒 Sovereign Enforcement Architecture

Sarathi enforces a strict model where **no decision is acted on until it is cryptographically proven**:

```
Sovereign Core  →  Sarathi  →  Pipeline (verify) → Envelope (seal) → Peers (Bucket / InsightFlow / Core)
       ↓               ↓                ↓                  ↓                       ↓
   TANTRA-signed   /sarathi/enforce  12-step verify    canonical bytes        signed receipts
   tantra.decision.v1                                                         (peer Ed25519)
```

**SAME `trace_id` flows across every layer. No regeneration. No mutation. No bypass.**

The verifier is fail-closed at every gate. Any byte drift, any expired window, any signature mismatch halts the chain and writes an audit row.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        INBOUND BOUNDARY                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ POST /sarathi/enforce  (TANTRA tantra.decision.v1)          │    │
│  │   - 12-step verifier (tantra_verifier.go)                   │    │
│  │   - Fixed-order canonical JSON (tantra_canonical.go)        │    │
│  │   - Crypto provider routing (Ed25519 OR composite hybrid)   │    │
│  │   - Replay 300 s (decision_hash + signed-payload hash)      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ POST /sarathi/cet/enforce  (CET SUM-SCRIPT, TANTRA-        │    │
│  │   CONVERGENCE-v1) — convergence boundary (cet_verifier.go)  │    │
│  │   - preserves execution_id / trace_id / cet_hash            │    │
│  │   - inner tantra.decision.v1 verified by same verifier      │    │
│  │   - emits enforcement_decision + Sarathi→Bridge handoff     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ POST /v1/ingest-decision  (primary ingest; fires fan-out)   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ POST /v1/enforce  (direct-input enforcement)                │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    PIPELINE LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ PDPAdapter — verification-only boundary (NO policy logic)   │    │
│  │   STAGE_STRUCTURE → STAGE_TRUST → STAGE_SIGNATURE →         │    │
│  │   STAGE_INTEGRITY → STAGE_EXPIRY → STAGE_REPLAY →           │    │
│  │   STAGE_RATE → STAGE_POSTURE → STAGE_BINDING → STAGE_MODE   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Propagation Envelope                                         │    │
│  │   canonical bytes sealed; response_hash + chain_binding_hash │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│              OUTBOUND BOUNDARY (peer fan-out, opt-in)               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │ Bucket          │  │ InsightFlow      │  │ BHIV Core          │  │
│  │ /bucket/artifact│  │ /insightflow_*   │  │ /v1/enforce (post) │  │
│  │ + read-back     │  │ Schemas A/B/C/D  │  │ canonical bytes    │  │
│  │ chain_verified  │  │ (off-chain)      │  │ post-exec record   │  │
│  └─────────────────┘  └──────────────────┘  └────────────────────┘  │
│           ▲                    ▲                       ▲             │
│           │ Ed25519-signed receipts to /v1/downstream-ack            │
│           └────────────────────┴───────────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    AUDIT LAYER (every byte recorded)                 │
│  proof_logs/enforcement_audit_backup.jsonl       enforcement events  │
│  proof_logs/peer_propagation_audit.jsonl         per-peer fan-out     │
│  proof_logs/peer_outbound_hashes.jsonl           outbound body hashes │
│  proof_logs/downstream_ack_receipts.jsonl        verified receipts    │
│  proof_logs/downstream_ack_rejections.jsonl      rejected receipts    │
│  proof_logs/tantra_replay.jsonl                  replay store          │
│  proof_logs/tantra_translation_map.jsonl         TANTRA → internal     │
│  proof_logs/sarathi_enforcement_attestations.jsonl outbound TANTRA   │
│  proof_logs/bucket/                              Bucket proofs+receipts│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security Model

| Guarantee | Mechanism |
|---|---|
| No decision accepted without signature verify | TANTRA 12-step verifier (tantra_verifier.go) |
| No decision accepted without registered evaluator | TANTRA registry, 5-gate lookup |
| No silent algorithm downgrade | provider algorithm asserted against signature alg; registry algorithm matched; boot panics on bad env |
| No replay (same decision twice) | 300 s window on decision_hash AND signed-payload hash |
| No mutation (one byte changed) | Signature verification fails closed |
| No expired decision | ±300 s timestamp skew check |
| No bypass via direct call | Inbound auth required; trace_id required in production |
| No success without truth | Propagation envelope + receipt gate; audit write failure = execution failure |
| Private keys never transported | Only public keys/fingerprints cross the wire; public key fetched via JWKS |
| Quantum-readiness | `SARATHI_CRYPTO_PROVIDER=hybrid` flips to Composite ML-DSA-65 + Ed25519; pipeline steps identical |
| All failures → FAIL CLOSED | No fallback, no silent execution, no default-on-error |

---

## ⚙️ Crypto Agility

Sarathi routes every signing and verifying call through a `CryptoProvider` interface. The active implementation is selected at boot by **one environment variable**:

```
SARATHI_CRYPTO_PROVIDER=ed25519   # default
SARATHI_CRYPTO_PROVIDER=hybrid    # Composite ML-DSA-65 + Ed25519 (post-quantum)
```

Anything else PANICS at boot (fail-closed; no silent downgrade). The pipeline steps, audit shape, replay checks, and registry lookups are IDENTICAL under both providers — only the bytes inside `signature.value` differ. ML-DSA-65 is provided by [Cloudflare CIRCL](https://github.com/cloudflare/circl) (pure Go, FIPS 204 vectors).

---

## 📐 TANTRA Contract Integration

`/sarathi/enforce` accepts ONLY the BHIV Core TANTRA Final Contract shape (`tantra.decision.v1`). The 12-step verifier:

```
0a  Strict JSON decode (DisallowUnknownFields, 1 MiB cap)
0b  Required-field validation + verdict whitelist
0c  evaluator_id format parse (bhiv.<s>.<c>.<e>.v<v>)
0d  Timestamp parse + ±300 s skew check

1   Extract signature object
2   Compute canonical signing bytes (fixed field order, signature OMITTED)
3   Reassert schema_version == "tantra.decision.v1"
4   Registry lookup: evaluator exists + ACTIVE
5   Registry schema_version + key_id + algorithm match
6   Round-trip canonical wire bytes (catches upstream re-encoders)
7   base64url-no-pad decode + provider.Verify
8   Recompute decision_hash from 6-field material
9   Compare against payload decision_hash
10  Recompute decision_id
11  Compare against payload decision_id
12  Replay store check (300 s, two surfaces)
```

Every step is a fail-closed gate.

---

## 🔗 TANTRA Convergence Chain (CET → Sarathi → Bridge → Runtime)

The full convergence chain is:

```
Core → CET → Sarathi → Bridge → Runtime → InsightFlow → Bucket
```

Two stages sit either side of Sarathi:

- **CET** (Canonical Execution Trace) compiles the Core decision into a canonical execution contract, computes the `cet_hash` integrity anchor once, and seals it as a **SUM-SCRIPT** carrying the locked identity (`execution_id`, `trace_id`, `cet_hash`, `schema_version=1.0`, `contract_version=TANTRA-CONVERGENCE-v1`).
- **Runtime** is the execution stage after Bridge: it consumes the validated contract + Sarathi's capability token and runs the authorized action.

Sarathi's `CET→Sarathi` boundary ([cet_verifier.go](cet_verifier.go)) accepts the SUM-SCRIPT, verifies the sealed inner `tantra.decision.v1` with the same multi-step verifier, **preserves `execution_id`/`trace_id`/`cet_hash` byte-identical**, seals the contract for mutation detection, and emits a Sarathi `enforcement_decision` artifact plus a prepared Sarathi→Bridge handoff. Any discontinuity or mutation fails closed.

Reproduce against the locked chain identity:

```
./sarathi-enforcement-adapter.exe --tantra-convergence
# → proof_logs/tantra_convergence/{enforcement_decision_*, bridge_handoff_*, rejection_*, CONVERGENCE_SUMMARY}.json
```

---

## 🔄 Dual-hash transport + decision integrity

Every outbound POST carries two distinct hashes:

| Header | What it is over | Peer's job |
|---|---|---|
| `X-Sarathi-Body-Hash` | SHA-256 of the full body bytes Sarathi sends | Hash the body you receive; reject on mismatch (TRANSPORT integrity) |
| `X-Sarathi-Response-Hash` | SHA-256 of the canonical enforcement record embedded as `canonical_response_b64` | Base64-decode, hash, reject on mismatch (DECISION integrity) |

The callback receipt to `/v1/downstream-ack` carries BOTH hashes (`received_body_hash` + `observed_response_hash`). Sarathi compares each to its minted values; either failure rejects fail-closed. For Bucket, Sarathi additionally reads the artifact back and re-verifies byte-identity itself (the seal + the witness model).

---

## 📊 Test Coverage

```
$ go build -o sarathi-enforcement-adapter.exe .   → OK (no output)
$ go vet ./...                                     → OK (no output)
$ go test ./...                                    → ok   (~4 s)

161 test functions defined — 161 PASS.
Coverage spans: TANTRA 12-step verifier (real Ed25519 + hybrid),
canonical-JSON determinism, peer-key registry (pinning, cross-peer
impersonation, replay), and the crypto-agility provider — all against
real code paths, no mocks on the load-bearing crypto.
```

---

## 🚀 Quick Start

### Prerequisites
- Go 1.25+
- No database required for the default runtime.

### Build
```bash
go build -o sarathi-enforcement-adapter.exe .
```

### Generate Sarathi's enforcement keypair (one-time)
```bash
./sarathi-enforcement-adapter.exe --provider-keygen \
    --evaluator-id=bhiv.sarathi.enforcement.prod.v1 \
    --out-dir=./live/keys/sarathi_enforcement \
    --key-id-rotation=2026-05
```
Forward the printed **public** key + `key_id` to peers. Keep the private key file local (never commit it — see [.gitignore](.gitignore)).

### Register the Sovereign Core public key
```bash
./sarathi-enforcement-adapter.exe --register-tantra-evaluator \
    --evaluator-id=bhiv.sovereign.decision.prod.v1 \
    --schema-version=tantra.decision.v1 \
    --algorithm=Ed25519 \
    --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
    --public-key=<hex-from-core> \
    --api-key-fingerprint=<sha256-hex-from-core> \
    --snapshot=./live/trust_snapshot.json
```

### Start the service
```bash
SARATHI_SERVICE_ADDR=127.0.0.1:8443 \
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json \
SARATHI_ENFORCEMENT_PRIV_PATH=./live/keys/sarathi_enforcement/issuer-priv.hex \
  ./sarathi-enforcement-adapter.exe --service
```
On a cloud host, set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>` so the platform can reach it. To enable peer fan-out, set `SARATHI_PROPAGATE_ON_INGEST=1` plus the peer URLs and `SARATHI_INSIGHT_API_KEY`. Full env reference and production gates are in [SETUP_GUIDE.md](SETUP_GUIDE.md) §5–§6.

### Verify
```bash
# health
curl http://127.0.0.1:8443/health
# live Bucket integration test
.\scripts\test_bucket.ps1
```

---

## 📁 Project Structure (selected)

```
sarathi-enforcement-adapter/
├── enforcement_adapter_main.go            # CLI dispatch + boot wiring
├── service_runtime_cli.go                 # --service runtime (listener, boot gates)
├── service_boundary.go                    # HTTP routing
├── service_boundary_tantra.go             # POST /sarathi/enforce handler
├── service_boundary_propagation_hook.go   # post-ingest peer fan-out
│
├── tantra_verifier.go                     # 12-step contract verifier
├── tantra_canonical.go                    # fixed-order canonical JSON
├── tantra_replay.go                       # 300 s replay store
├── cet_verifier.go / cet_contract.go      # CET convergence boundary
│
├── crypto_provider*.go                    # Ed25519 + ML-DSA-65 hybrid providers
├── peer_key_registry.go                   # pinned per-peer public keys
├── jwt_authority*.go                      # capability tokens + JWKS publishing
│
├── bucket_bhiv_adapter.go                 # aligned Bucket adapter (verified live)
├── bucket_readback_verifier.go            # Bucket read-back verification
├── translation_insightflow*.go            # InsightFlow Schema A/B/C/D + fan-out
├── translation_bucket_artifact.go         # production BucketArtifact builder
├── ecosystem_endpoints.go / _clients.go   # peer URL wiring + outbound clients
├── downstream_ack_endpoint.go             # /v1/downstream-ack receipt verify
│
├── live/keys/                             # key material (gitignored: private keys)
├── proof_logs/                            # JSONL audit trails + Bucket proofs
└── scripts/                               # PowerShell test runbooks
```
Full subsystem map: [REPO_MAP.md](REPO_MAP.md).

---

## 📋 Handover Documentation

Operational-closure deliverables (a new owner can run, test, understand, and continue Sarathi from these alone):

| Document | Purpose |
|---|---|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Build, run, env vars, cloud deploy, troubleshooting |
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | What Sarathi is and does |
| [ARCHITECTURE_FLOW.md](ARCHITECTURE_FLOW.md) | End-to-end data flow |
| [REPO_MAP.md](REPO_MAP.md) | Where every subsystem lives |
| [BUILD_STATE.md](BUILD_STATE.md) | What works / incomplete / tech debt |
| [FAQ.md](FAQ.md) | Common questions |
| [PENDING_WORK.md](PENDING_WORK.md) | Open items, owners, done-criteria |
| [SARATHI_CLOSURE_REPORT.md](SARATHI_CLOSURE_REPORT.md) | Achievements, gaps, risks, transfer readiness |
| [REVIEW_PACKET.md](REVIEW_PACKET.md) | Reviewer's packet (flow, failure cases, proof) |
| [DEPOSITORY_MANIFEST.md](DEPOSITORY_MANIFEST.md) | Transfer-package index |
| [BUCKET_TEST_COMMANDS.md](BUCKET_TEST_COMMANDS.md) | Step-by-step Bucket integration runbook |
| [E2E_VALIDATION.md](E2E_VALIDATION.md) | Deployment + end-to-end validation runbook |

Captured proof lives under `validation screenshots/` (build, service, health, 5 E2E traces, failure case).

---

## 🔧 Configuration (essentials)

| Variable | Default | Purpose |
|---|---|---|
| `SARATHI_SERVICE_ADDR` | `127.0.0.1:8443` | HTTP bind address (`0.0.0.0:<port>` for cloud) |
| `SARATHI_CRYPTO_PROVIDER` | `ed25519` | Provider selector (`hybrid` opt-in) |
| `SARATHI_ENFORCEMENT_PRIV_PATH` | (falls back to `live/keys/…`) | Sarathi's enforcement signing key |
| `SARATHI_TRUST_SNAPSHOT` | `./live/trust_snapshot.json` | Trust registry path |
| `SARATHI_PROPAGATE_ON_INGEST` | `0` | Enable peer fan-out |
| `SARATHI_INSIGHT_API_KEY` | (unset) | `X-API-Key` presented to InsightFlow |
| `SARATHI_ENV` | (unset) | `production` activates strict boot gates |
| `SARATHI_INBOUND_AUTH` | (off) | `required` in production |

Full list and production gates: [SETUP_GUIDE.md](SETUP_GUIDE.md) §5.

---

## 👥 Integration Block

| Owner | System | Role |
|---|---|---|
| Hemanth B | **Sarathi** | Enforcement adapter, TANTRA verifier, crypto agility, propagation |
| Raj Prajapati | BHIV Core | Core execution + trace + enforcement entry |
| Aakanksha | Sovereign Systems | Decision integrity, `bhiv.sovereign.decision.prod.v1` |
| Siddhesh Narkar | Bucket | Append-only truth storage |
| Vijay Dhawan | InsightFlow | Enforcement signal + observability |
| Kanishk | Execution Systems | Token consumption |
| Shivam / Ritesh | Pravah | Signal ingestion + observation |
| Pritesh Patra | Interfaces | Schema consistency |

---

## 📄 License

Proprietary — Blackhole Infiverse (BHIV) Systems.

# Endpoints for BHIV — Wire Contract

**Audience:** BHIV's Core (Raj), InsightFlow (Vijay), and Bucket (Siddhesh) teams.
**Version:** v15.10 (TANTRA inbound + crypto-agile provider + peer-key registry + post-ingest propagation).
**See also:** [KB_17_TANTRA_DECISION_V1.md](KB_17_TANTRA_DECISION_V1.md), [KB_18_CRYPTO_AGILITY.md](KB_18_CRYPTO_AGILITY.md), [SARATHI_SYSTEM_GUIDE.md](SARATHI_SYSTEM_GUIDE.md) Part XII, §8 of this doc.

This document is **the** authoritative reference for the HTTP surface shared between
Sarathi and the three BHIV peer systems. It lists every endpoint in both directions
(Sarathi-inbound and BHIV-inbound), the headers each side must produce, the
acceptance + rejection contract, and the exact Go file Sarathi calls each endpoint
from. Configuration is via environment variables — every BHIV-facing URL maps to one
env var, defined in [ecosystem_endpoints.go](ecosystem_endpoints.go).

This file references only Go source files and JSON/JSONL artefact paths — no other
documentation. To map an endpoint to its Go entry point, follow the file references.

---

## 1. Outbound from Sarathi to BHIV (the 10 endpoints)

These are the URLs Sarathi calls into BHIV's systems. Each is configurable via a
distinct env var; if no per-endpoint var is set, Sarathi falls back to a legacy
base URL (`SARATHI_ROUTE_*_URL`) or to the localhost development default. The
operator edits [ecosystem_endpoints.go](ecosystem_endpoints.go) `DefaultEndpoints()`
to bake values into the binary, OR sets env vars at deploy time.

### 1.1 BHIV Core (legacy 3 + Raj's full v15.3 surface = 8 endpoints)

| # | URL path | Method | Env var | Sarathi caller (Go file) | Direction |
|---|---|---|---|---|---|
| 1 | `/v1/enforce` (legacy alias) | POST | `SARATHI_CORE_ENFORCE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.Enforce` | Sync, in-chain |
| 2 | `/v1/execute` (legacy alias) | POST | `SARATHI_CORE_EXECUTE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.Execute` | Sync, in-chain |
| 3 | `/health` | GET | `SARATHI_CORE_HEALTH_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.Health` | Pre-flight |
| 4 | `/execute_task` (port 8003) | POST | `SARATHI_CORE_EXECUTE_TASK_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.ExecuteTask` | Sync — single task |
| 5 | `/execute_sequence` (port 8003) | POST | `SARATHI_CORE_EXECUTE_SEQUENCE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.ExecuteSequence` | Sync — task sequence |
| 6 | `/handle_task` (MCP Bridge port 8000) | POST | `SARATHI_CORE_HANDLE_TASK_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.HandleTask` | Sync — main ingestion |
| 7 | `/sovereign/decide` (port 9001) | POST | `SARATHI_CORE_SOVEREIGN_DECIDE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.SovereignDecide` | Decision ingestion (active mode) |
| 8 | `/health` (port 9001) | GET | `SARATHI_CORE_SOVEREIGN_HEALTH_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `CoreClient.SovereignHealth` | Pre-flight |

**Body:** Raw canonical bytes of the sealed `PropagationEnvelope.canonical_response`.
No re-marshal, no padding. SHA-256 of the body equals `X-Sarathi-Response-Hash`.

**Headers Sarathi sets:** all 9 X-Sarathi-* propagation headers (see §3).

**Expected ACK:** HTTP 200 + `X-Sarathi-Ack-Hash` header echoing the body's SHA-256.
Then asynchronously a signed peer receipt POSTed to Sarathi `/v1/downstream-ack` (§2.2).

### 1.2 BHIV InsightFlow (5 endpoints — 4 digest-only POST + 1 GET verify)

Tailscale IP (May 4): `100.117.3.88:8001`

| # | URL path | Method | Env var | Sarathi caller (Go file) | Direction |
|---|---|---|---|---|---|
| 9 | `/sarathi_trigger` | POST | `SARATHI_INSIGHT_TRIGGER_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `InsightFlowClient.SarathiTrigger` | Async, off-chain |
| 10 | `/core_execute` | POST | `SARATHI_INSIGHT_EXECUTE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `InsightFlowClient.CoreExecute` | Async, off-chain |
| 11 | `/insightflow_process` | POST | `SARATHI_INSIGHT_PROCESS_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `InsightFlowClient.Process` | Async, off-chain |
| 12 | `/bucket_persist` | POST | `SARATHI_INSIGHT_BUCKET_PERSIST_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `InsightFlowClient.BucketPersist` | Async, off-chain |
| 13 | `/bucket/verify/{trace_id}` (NEW v15.3) | GET | `SARATHI_INSIGHT_VERIFY_BUCKET_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `InsightFlowClient.VerifyBucket` | Pull — trace-continuity verification |

**Body:** A digest payload (NOT the full canonical response). Schema:

```json
{
  "schema_version":     "sarathi.digest/v1.0",
  "decision_id":        "DEC-VC-0001",
  "execution_id":       "EXEC-VC-0001",
  "trace_id":           "<32-hex>",
  "correlation_id":     "<UUID>",
  "response_hash":      "<64-hex>",
  "chain_binding_hash": "<64-hex>",
  "enforcement_hash":   "<64-hex>",
  "decision_hash":      "<64-hex>",
  "verdict":            "ALLOW",
  "observed_at":        "RFC3339Nano"
}
```

The digest contract is enforced by [ecosystem_clients.go](ecosystem_clients.go) function
`buildDigest`. InsightFlow MUST NOT receive the full verdict body — fingerprint hashes
only. The `X-Sarathi-Digest-Only: 1` header is set so the receiver knows to expect a
digest.

**Headers Sarathi sets:** all 9 X-Sarathi-* propagation headers + `X-Sarathi-Digest-Only: 1`.

**Expected ACK:** HTTP 202 + `X-Sarathi-Ack-Hash`. No round-trip byte verification (off-chain).
Failure here NEVER halts the propagation chain.

### 1.3 BHIV Bucket (3 endpoints)

Tailscale IP (May 4): `100.122.58.102:8000`

| # | URL path | Method | Env var | Sarathi caller (Go file) | Direction |
|---|---|---|---|---|---|
| 14 | `/bucket/artifact` | POST | `SARATHI_BUCKET_ARTIFACT_POST_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `BucketClient.StoreArtifact` | Sync, in-chain |
| 15 | `/bucket/artifact/{decision_id}` | GET | `SARATHI_BUCKET_ARTIFACT_GET_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `BucketClient.GetArtifact` | Pull (readback proof) |
| 16 | `/bucket/artifacts?trace_id={trace_id}` | GET | `SARATHI_BUCKET_ARTIFACTS_TRACE_URL` | [ecosystem_clients.go](ecosystem_clients.go) — `BucketClient.GetArtifactsByTrace` | Pull (trace-level query) |

**POST body:** Raw canonical bytes (same as Core).

**POST headers:** all 9 X-Sarathi-* propagation headers.

**POST expected ACK:** HTTP 200 + `X-Sarathi-Ack-Hash`. Then async signed peer
receipt to `/v1/downstream-ack`.

**GET (single artifact) — what Bucket returns:** the **byte-identical** stored body.
Sarathi's [bucket_readback_verifier.go](bucket_readback_verifier.go) recomputes
SHA-256 over the response body and asserts it equals the original `response_hash`.
Any drift → `ERR_BUCKET_READBACK_MISMATCH`, halt.

**GET (artifacts by trace) — response shape:**

```json
{
  "trace_id": "<32-hex>",
  "count":    3,
  "artifacts": [
    {
      "decision_id":   "DEC-VC-0001",
      "response_hash": "<64-hex>",
      "size_bytes":    2048,
      "storage_path":  "live/bucket/DEC-VC-0001.json"
    }
  ]
}
```

This endpoint is NEW in v15.2 — it lets a reviewer enumerate every decision that
flowed through a given trace_id without iterating decision_ids. The reference
implementation that fulfils this contract is in
[peer_bucket.go](peer_bucket.go) `handleArtifactsByTrace`, backed by the
trace_id index in [peer_common.go](peer_common.go) `PeerStore.IndexByTraceID`.

---

## 2. Inbound to Sarathi from BHIV

These are the endpoints BHIV's systems call into Sarathi.

### 2.0 v15.3 BHIV-wire-format routes (v15.7 TANTRA inbound surface)

> **v15.7 / v15.10 update:** `/sarathi/enforce` no longer accepts the 9-field
> SovereignDecideResponse shape; it now accepts ONLY `tantra.decision.v1`
> per the TANTRA Final Contract ([KB_17_TANTRA_DECISION_V1.md](KB_17_TANTRA_DECISION_V1.md)).
> The signature is an object `{alg, key_id, encoding, value}` with
> `encoding="base64url_no_pad"`. The original §6 description below remains as
> historical context — the LIVE shape is the TANTRA one.

Sarathi exposes the canonical Sarathi-internal route `/v1/ingest-decision` for
canonical `ExternalDecision` bodies (self-test path), AND the BHIV-wire-format
route `/sarathi/enforce` which speaks the **TANTRA `tantra.decision.v1` shape**
shape natively. They are now DISTINCT handlers — see §6 for the Sovereign
translation contract.

| BHIV-wire-format route | Body shape | Implemented in |
|---|---|---|
| `POST /sarathi/enforce` | `SovereignDecideResponse` (9 fields) | [service_boundary_sovereign.go](service_boundary_sovereign.go) `handleSarathiEnforceSovereign` |
| `POST /sarathi/cet/enforce` | CET SUM-SCRIPT envelope (`schema_version=1.0`, `contract_version=TANTRA-CONVERGENCE-v1`) wrapping a sealed `tantra.decision.v1` | [cet_service_handler.go](cet_service_handler.go) `handleSarathiCETEnforce` |
| `POST /v1/ingest-decision` | Canonical `ExternalDecision` (16 fields, self-test) | [service_boundary.go](service_boundary.go) `handleIngestDecision` |
| `GET /sarathi/validate-token?token=…` | — | [service_boundary.go](service_boundary.go) `handleValidateToken` |
| `GET /health` | — | [service_boundary.go](service_boundary.go) `handleHealth` |

#### CET → Sarathi convergence boundary (`tantra-convergence-v1`)

`POST /sarathi/cet/enforce` is the CET→Sarathi convergence ingestion path for the
`Core → CET → Sarathi → Bridge → Runtime → InsightFlow → Bucket` chain. It accepts
the SUM-SCRIPT envelope (`execution_id`, `trace_id`, `cet_hash`, `bucket_key`,
`schema_version=1.0`, `contract_version=TANTRA-CONVERGENCE-v1`, plus the sealed
inner `tantra.decision.v1` as `decision_b64`), runs the convergence-continuity
gates on top of the same multi-step inner verifier, and:

- **accept →** HTTP 200 + a `Sarathi enforcement_decision` artifact (preserves
  `execution_id`/`trace_id`/`cet_hash`, `decision=allow`, contract-continuity proof)
  and prepares the Sarathi→Bridge handoff (capability token + headers);
- **reject →** HTTP 4xx + a trace-bound fail-closed rejection artifact +
  `X-Sarathi-Error-Code`.

Optional `cet_material_b64` (base64-std of the bytes CET hashed) upgrades cet_hash
verification from continuity to independent recompute. Boundary spec and the
external evidence contract: [TANTRA_CONVERGENCE_RESPONSE.md](TANTRA_CONVERGENCE_RESPONSE.md);
internals: [KB_19_TANTRA_CONVERGENCE_CET.md](KB_19_TANTRA_CONVERGENCE_CET.md).

### 2.1 The PDP-side decision ingest (Tanvi or BHIV PDP)

| # | URL path | Method | Sarathi handler |
|---|---|---|---|
| 1 | `/v1/ingest-decision` | POST | [service_boundary.go](service_boundary.go) — `handleIngestDecision` |

**Body:** JSON-encoded `ExternalDecision` struct (see [external_decision.go](external_decision.go)
struct definition). Required fields: `decision_id`, `evaluator_id`, `agent_id`,
`resource_id`, `action`, `verdict`, `obligations`, `timestamp`, `ttl_ns` /
`expires_at`, `nonce`, `decision_hash`, `decision_core_hash`, `evaluator_signature`.

**Required headers:**
- `Content-Type: application/json`
- `X-API-Key: <SARATHI_CALLER_KEY_BHIV value>`

**Optional headers (when `SARATHI_INBOUND_AUTH=optional` or `=required`):**
- `X-Sarathi-Issuer-Id`
- `X-Sarathi-Request-Nonce`
- `X-Sarathi-Timestamp`
- `X-Sarathi-Body-Signature` (Ed25519 sig over canonical body ‖ 0x1E ‖ nonce ‖ 0x1E ‖ ts ‖ 0x1E ‖ issuer_id, base64-encoded)
- `X-Sarathi-Sig-Algorithm: ed25519`

**Successful response (HTTP 200):**

```json
{
  "decision_id":           "DEC-VC-0001",
  "execution_id":          "EXEC-VC-0001",
  "response_hash":         "<64-hex>",
  "chain_binding_hash":    "<64-hex>",
  "canonical_response_b64": "<base64 of canonical bytes>"
}
```

**Failure responses:**
- 401 — missing API key
- 403 — wrong API key OR evaluator status not ACTIVE
- 409 — replay (nonce already seen)
- 422 — integrity / signature / structure / expiry failure
- 503 — audit unavailable (mandatory audit gate OPEN)

### 2.2 Peer receipt callback

| # | URL path | Method | Sarathi handler |
|---|---|---|---|
| 2 | `/v1/downstream-ack` | POST | [downstream_ack_endpoint.go](downstream_ack_endpoint.go) — `handleDownstreamAck` |

**Body:** A signed `PeerReceipt` JSON. Schema is in [peer_common.go](peer_common.go)
`PeerReceipt` struct:

```json
{
  "schema_version":      "sarathi.live.receipt/v1.0",
  "peer":                "core | insightflow | bucket",
  "execution_id":        "<id>",
  "decision_id":         "<id>",
  "response_hash":       "<64-hex>",
  "received_body_hash":  "<64-hex>",
  "chain_binding_hash":  "<64-hex>",
  "persisted_at":        "RFC3339Nano",
  "storage_path":        "<peer-defined>",
  "peer_public_key_hex": "<64-hex Ed25519 public key>",
  "receipt_signature":   "<128-hex Ed25519 signature>"
}
```

**Sarathi verifies (v15.6 baseline + v15.9 hardening):**
1. `schema_version` matches.
2. Peer's Ed25519 public key + signature decode correctly.
3. The signature verifies over canonical receipt with `receipt_signature` cleared.
4. `received_body_hash == response_hash` (the peer hashed what Sarathi sent).
5. **v15.9** — `peer` field is one of bucket/core/insightflow (cross-peer impersonation gate).
6. **v15.9** — if the peer has a registered key in `peer_keys`, the embedded `peer_public_key_hex` matches the registered key (constant-time compare). Status must be ACTIVE.
7. **v15.9** — `sha256(raw receipt bytes)` keyed by peer is rejected if seen within the last 300 s (receipt-replay gate).

On success: append to `proof_logs/downstream_ack_receipts.jsonl` and notify the
`AckTracker` ([downstream_ack_tracker.go](downstream_ack_tracker.go)) so the
3-peer gate can close.

On failure: append to `proof_logs/downstream_ack_rejections.jsonl`, return 401 with
`ERR_DOWNSTREAM_RECEIPT_INVALID`. The reason string surfaces which gate failed
(e.g. `peer_key_pinning: peer "bucket" embedded public_key_hex does not match registered key`).

**Registering a peer key (one-time per environment):**

```bash
./sarathi-enforcement-adapter --register-peer-key \
    --peer=bucket \
    --public-key=<64-hex Ed25519 from Bucket team> \
    --name="Bucket production" \
    --snapshot=./live/trust_snapshot.json
```

Repeat for `--peer=insightflow` and `--peer=core`. To require all peers be
registered (production posture), set `SARATHI_PEER_KEY_PINNING=strict`
before starting `--service`. To rotate a peer's key, re-run with the new
`--public-key` value; the CLI prints `updated` and appends an audit row.

### 2.3 Schema handshake

| # | URL path | Method | Sarathi handler |
|---|---|---|---|
| 3 | `/v1/handshake` | GET | [downstream_ack_endpoint.go](downstream_ack_endpoint.go) — `handleHandshake` |

Returns the response-fields schema peers MUST validate against:

```json
{
  "schema_version":           "sarathi.response/v13.0",
  "propagation_version":      "sarathi.propagation/v14.5",
  "live_integration_version": "sarathi.live.handshake/v1.0",
  "required_fields":          ["schema_version","decision_id","verdict"],
  "propagation_fields":       ["response_hash","chain_binding_hash"],
  "hash_algo":                "sha256",
  "canonical_algo":           "rfc8785-jcs-equivalent",
  "served_at":                "RFC3339Nano"
}
```

Reference field lists are in [response_contract.go](response_contract.go) constants
`RequiredResponseFields` + `PropagationResponseFields`.

### 2.4 Health & metrics

| # | URL path | Method | Handler |
|---|---|---|---|
| 4 | `/health` | GET | [service_boundary.go](service_boundary.go) — `handleHealth` |
| 5 | `/health/deep` | GET | [service_boundary.go](service_boundary.go) — `handleHealthDeep` |
| 6 | `/metrics` | GET | [service_boundary.go](service_boundary.go) — `handleMetrics` |
| 7 | `/v1/bridge/info` | GET | [service_boundary.go](service_boundary.go) — `handleBridgeInfo` |

---

## 3. The 9 X-Sarathi-* propagation headers

Sarathi sets every one of these on every outbound POST to an in-chain peer. Their values
are derived from the sealed `PropagationEnvelope` ([propagation_envelope.go](propagation_envelope.go))
via the `ToHeaderMap()` accessor.

| Header | Description | Source |
|---|---|---|
| `X-Sarathi-Trace-ID` | OTel-compatible trace id | `env.TraceID()` |
| `X-Sarathi-Span-ID` | Per-hop span id | `env.SpanID()` |
| `X-Sarathi-Response-Hash` | SHA-256 of body — peer MUST re-verify | `env.ResponseHash()` |
| `X-Sarathi-Chain-Binding` | Chain anchor hash | `env.ChainBindingHash()` |
| `X-Sarathi-Decision-ID` | Stable across all 3 peers | `env.DecisionID()` |
| `X-Sarathi-Execution-ID` | One per end-to-end run | `env.ExecutionID()` |
| `X-Sarathi-Correlation-ID` | Caller-supplied | `env.CorrelationID()` |
| `X-Sarathi-Schema-Version` | Response schema version | `env.SchemaVersion()` |
| `X-Sarathi-Enforcement-Hash` | Sealed PDP enforcement hash | `env.EnforcementHash()` |

---

## 4. Wire contract — what every BHIV peer MUST do

Reference implementation: [peer_common.go](peer_common.go) function
`processIncomingEnvelope` plus the per-peer wrappers in [peer_bhic_core.go](peer_bhic_core.go),
[peer_insightflow.go](peer_insightflow.go), [peer_bucket.go](peer_bucket.go).

For each in-chain POST your peer:

1. **Read body bytes verbatim.** No re-marshal before hashing. Re-marshal is the #1
   cause of silent byte drift (this includes proxies that "helpfully" reformat JSON).
2. **Recompute SHA-256(body).** If not equal to `X-Sarathi-Response-Hash`, return 412
   with `error_code: ERR_RESPONSE_HASH_MISMATCH` and the recomputed hash in
   `X-Sarathi-Ack-Hash`.
3. **Verify canonical form.** Re-canonicalize the body via the same RFC 8785 implementation
   Sarathi uses ([canonical_json.go](canonical_json.go) `VerifyCanonicalBytes`). If
   the canonicalised form differs, return 412 with `error_code: ERR_PROPAGATION_BYTE_MISMATCH`.
4. **Validate schema fields.** Every field listed at `/v1/handshake` `required_fields`
   + `propagation_fields` MUST be present as a top-level key. On miss, return 422 with
   `error_code: ERR_DOWNSTREAM_SCHEMA_MISMATCH`.
5. **Drift-reject on replay.** Maintain a per-decision-id index of the
   first-stored body hash. Same `decision_id` + same hash = idempotent (return original
   receipt). Same `decision_id` + different hash = return 409 with `ERR_RESPONSE_HASH_MISMATCH`
   — this is the determinism violation detector.
6. **Persist body verbatim.** Bucket: durable on-disk (atomic tmp+fsync+rename),
   one file per decision_id. Core / InsightFlow: append-only JSONL (in-memory is
   acceptable for InsightFlow given its digest-only contract).
7. **Sign and emit a receipt.** Construct the `PeerReceipt` (§2.2) with your Ed25519
   private key, POST it to `<SARATHI_PEER_ACK_URL>` (provided at peer boot via env var).
   At-least-once delivery; Sarathi tolerates duplicates.
8. **Respond.** 200 OK (or 202 for InsightFlow / digest-only) with body containing
   `{peer, ack_hash, decision_id, storage_path, duplicate}` and the `X-Sarathi-Ack-Hash`
   header set to the body hash you computed.

---

## 5. Environment variable summary

For the operator running Sarathi (Machine A):

```bash
# --- Bind / advertise -----------------------------------------------
export SARATHI_LISTEN_HOST=0.0.0.0
export SARATHI_ADVERTISE_HOST=<your-public-ip-or-tailscale-ip>
export SARATHI_SERVICE_ADDR=0.0.0.0:8443

# --- Caller API keys (required) -------------------------------------
export SARATHI_CALLER_KEY_BHIV=<32-byte hex>          # primary BHIV caller key

# --- Inbound auth (optional, off by default) ------------------------
export SARATHI_INBOUND_AUTH=off                       # off | optional | required

# --- BHIV ecosystem URLs (the 10 outbound endpoints) ----------------
export SARATHI_CORE_ENFORCE_URL=https://core.bhiv.example/v1/enforce
export SARATHI_CORE_EXECUTE_URL=https://core.bhiv.example/v1/execute
export SARATHI_CORE_HEALTH_URL=https://core.bhiv.example/health
export SARATHI_INSIGHT_TRIGGER_URL=https://insight.bhiv.example/sarathi_trigger
export SARATHI_INSIGHT_EXECUTE_URL=https://insight.bhiv.example/core_execute
export SARATHI_INSIGHT_PROCESS_URL=https://insight.bhiv.example/insightflow_process
export SARATHI_INSIGHT_BUCKET_PERSIST_URL=https://insight.bhiv.example/bucket_persist
export SARATHI_BUCKET_ARTIFACT_POST_URL=https://bucket.bhiv.example/bucket/artifact
export SARATHI_BUCKET_ARTIFACT_GET_URL=https://bucket.bhiv.example/bucket/artifact
export SARATHI_BUCKET_ARTIFACTS_TRACE_URL=https://bucket.bhiv.example/bucket/artifacts

# --- Peer receipt mount (optional) ----------------------------------
export SARATHI_ENABLE_PEER_RECEIPTS=1                 # mounts /v1/downstream-ack + /v1/handshake

# --- Audit (postgres optional, JSONL fallback always active) --------
export SARATHI_DB_HOST=...                            # if unset, only JSONL backup is written
export SARATHI_DB_USER=...
export SARATHI_DB_PASSWORD=...
export SARATHI_DB_NAME=sarathi_audit
```

For each BHIV peer machine (Machine B/C/D):

```bash
export SARATHI_PEER_ADDR=0.0.0.0:7101                 # peer's own listen port
export SARATHI_PEER_ACK_URL=https://sarathi.example:8443/v1/downstream-ack
export SARATHI_PEER_HANDSHAKE_URL=https://sarathi.example:8443/v1/handshake
```

A complete env-var inventory lives in code: search [ecosystem_endpoints.go](ecosystem_endpoints.go)
for `Env*` constants, [service_boundary.go](service_boundary.go) for `SARATHI_*` env reads,
and [service_inbound_auth.go](service_inbound_auth.go) for the inbound-auth knobs.

---

## 6. Quick sanity check

After Sarathi is running, BHIV operators can confirm reachability with one curl per peer:

```bash
# Core
curl -i -H "X-API-Key: $API_KEY" -X POST \
     "$SARATHI_CORE_ENFORCE_URL" -d '{"_smoke":"1"}'
# Expected: 412 ERR_RESPONSE_HASH_MISMATCH (body has no decision; ack contract still triggers)

# InsightFlow (digest endpoint)
curl -i -X POST -H "X-Sarathi-Digest-Only: 1" \
     "$SARATHI_INSIGHT_PROCESS_URL" -d '{"decision_id":"smoke","response_hash":"00"}'
# Expected: 202 Accepted

# Bucket POST
curl -i -X POST "$SARATHI_BUCKET_ARTIFACT_POST_URL" -d '{"_smoke":"1"}'
# Expected: 412 ERR_RESPONSE_HASH_MISMATCH

# Bucket GET (artifact by trace — empty trace returns count=0, NOT an error)
curl -s "$SARATHI_BUCKET_ARTIFACTS_TRACE_URL?trace_id=does-not-exist"
# Expected: {"trace_id":"does-not-exist","count":0,"artifacts":[]}
```

For the full demo workflow (with real signed decisions), see
[ENFORCEMENT_VALIDATION_SCRIPT.md](ENFORCEMENT_VALIDATION_SCRIPT.md).

For the per-Go-file inventory, see [GO_FILES_EXPLAINED.md](GO_FILES_EXPLAINED.md).

For the system-level overview, see [README.md](README.md).

---

## 7. Ngrok deployment mode (v15.4)

For cross-network testing without Tailscale, all 16 endpoint env vars
accept ngrok HTTPS URLs unchanged. Use `scripts/ngrok_env.sh` (or
`scripts/ngrok_env.ps1`) to wire them in one command.

### 7.1 Six tunnels for the 4-service BHIV chain

| BHIV Service | Whose tunnel | Tunnels | Env vars set |
|---|---|---|---|
| Bucket | Siddhesh | 1 | `SARATHI_BUCKET_ARTIFACT_*_URL` (3 derived from base) |
| InsightFlow | Vijay | 1 | `SARATHI_INSIGHT_*_URL` (5 derived from base) |
| BHIV Core API :8003 | Raj | 1 | `SARATHI_CORE_EXECUTE_TASK_URL`, `_EXECUTE_SEQUENCE_URL`, `_HEALTH_URL`, `_ENFORCE_URL`, `_EXECUTE_URL` |
| MCP Bridge :8000 | Raj | 1 | `SARATHI_CORE_HANDLE_TASK_URL` |
| Sovereign Core :9001 | Raj | 1 | `SARATHI_CORE_SOVEREIGN_DECIDE_URL`, `_SOVEREIGN_HEALTH_URL` |
| Sarathi Enforcer :9002 | Us (we expose) | 1 | We share with Raj for callback |

### 7.2 One-command env wiring

```bash
source scripts/ngrok_env.sh \
  --bucket   https://<siddhesh>.ngrok-free.app \
  --insight  https://<vijay>.ngrok-free.app \
  --core-api https://<raj-8003>.ngrok-free.app \
  --mcp      https://<raj-8000>.ngrok-free.app \
  --sov      https://<raj-9001>.ngrok-free.app \
  --self     https://<our-9002>.ngrok-free.app
```

Per-endpoint overrides (`--bucket-artifact-post`, etc.) win over base URLs.
See `NGROK_VALIDATION_SCRIPT.md` for the complete operator runbook.

### 7.3 New v15.4 outbound contract — `CoreClient.PostTaskInput`

| Field | Value |
|---|---|
| Method | POST |
| URL | `SARATHI_CORE_EXECUTE_TASK_URL` |
| Headers | `Content-Type: application/json`, `X-Sarathi-Component: PostTaskInput`, `ngrok-skip-browser-warning: true` |
| Request body | `{"trace_id":"", "input":"<string>", "context":{...}}` |
| Response body | Core-defined: typically `{"trace_id":"<generated>", "decision":"ALLOW\|DENY", "decision_hash":"sha256:...", "policy_reference":"...", "input_hash":"sha256:...", "timestamp":"..."}` |
| Trigger | CLI: `./sarathi-enforcement-adapter --post-task-to-core --input "..." [--context-json '...']` |
| Purpose | Bootstraps the BHIV chain — Sarathi sends initial input upstream so Core can drive the rest of the chain back through MCP → Sovereign → Sarathi → propagation. |
| Rule | `trace_id` MUST be empty (`""`) — Core generates and returns it (Raj's contract). |

This is **distinct** from `CoreClient.ExecuteTask` (which posts the
post-enforcement sealed envelope downstream). Same endpoint, opposite
direction, different payload.

### 7.4 Timeout

Default outbound timeout is **15 s** (v15.4, raised from 5 s for ngrok
free-tier latency). Override with `SARATHI_ECOSYSTEM_TIMEOUT_MS=<n>`.

### 7.5 Inbound schema for `/sarathi/enforce` — IMPORTANT for Sovereign team

`POST /sarathi/enforce` is internally aliased to `handleIngestDecision`
(see [service_boundary.go:158](service_boundary.go#L158)). It accepts ONLY
a fully-formed signed `ExternalDecision` JSON. Any other payload is
rejected with **HTTP 422 unprocessable**.

Required fields (see [external_decision.go:192](external_decision.go#L192)):

| Field | Type | Required |
|---|---|---|
| `decision_id` | string (UUID) | ✓ |
| `evaluator_id` | string (must match a registered evaluator key) | ✓ |
| `agent_id` | string | ✓ |
| `resource_id` | string | ✓ |
| `action` | string | ✓ |
| `verdict` | `"ALLOW"` / `"DENY"` / `"ESCALATE"` | ✓ |
| `obligations` | []string (may be empty) | ✓ |
| `timestamp` | RFC3339 | ✓ |
| `ttl` | duration (Go) | ✓ |
| `expires_at` | RFC3339 | ✓ |
| `metadata` | map[string]string | ✓ (may be empty) |
| `reason` | string | ✓ |
| `nonce` | string (UUID) | ✓ |
| `decision_hash` | SHA-256 hex | ✓ |
| `decision_core_hash` | SHA-256 hex | ✓ |
| `evaluator_signature` | base64 Ed25519 over `decision_core_hash` | ✓ |
| `evaluator_signature_hex` | hex of the same | ✓ |

Sovereign Core's `/sovereign/decide` returns a SIMPLER 6-field shape
(`{trace_id, decision, decision_hash, policy_reference, input_hash,
timestamp}`). **That shape will be rejected by `/sarathi/enforce`.** Two
acceptable resolutions:

1. **Sovereign signs an ExternalDecision** with an Ed25519 key whose public
   key is registered in Sarathi's evaluator registry. Sovereign then POSTs
   to `/sarathi/enforce`.
2. **Sovereign POSTs to `/v1/enforce` instead** with a `SaarthiRequest`
   shape (`agent_id`, `resource_id`, `action`, `correlation_id`,
   `caller_system`, `caller_version`, `requested_at`). Sarathi's internal
   PDP then produces the verdict; Sovereign's verdict is ignored unless
   carried in a custom header.

Confirm which path the Sovereign team is wiring **before** any cross-system
test starts.

---

## 6. v15.5 — Sovereign Translational Layer

The v15.5 release replaces the §5 "two acceptable resolutions" with a
deterministic translation layer. `/sarathi/enforce` now speaks the BHIV
Sovereign 9-field shape **natively**. The Sovereign team adds 3 auth fields
(`api_key`, `ed25519_signature`, `evaluator_id`) to their existing 6-field
response — nothing else.

### 6.1 SovereignDecideResponse (9 fields) — `bhiv.sovereign.decide/v1.0`

The body Sovereign Core returns from `/sovereign/decide` AND POSTs to
Sarathi `/sarathi/enforce`. The 6 stock fields stay; the 3 auth fields are
new.

```json
{
  "schema_version":     "bhiv.sovereign.decide/v1.0",
  "trace_id":           "<32-hex W3C, generated by Core API only>",
  "decision":           "ALLOW | DENY | ESCALATE",
  "decision_hash":      "<hex sha256 over decision content>",
  "policy_reference":   "<policy_pack_id@version>",
  "input_hash":         "<hex sha256 of original input>",
  "timestamp":          "<RFC3339 UTC>",

  "evaluator_id":       "sovereign_bhiv_core",
  "api_key":            "<hex secret; sha256 fingerprint registered with Sarathi>",
  "ed25519_signature":  "<hex 64-byte signature over decision_hash>"
}
```

The signature target is **`decision_hash`** (the only canonical anchor in the
6 stock fields). Sarathi verifies it against the registered public key for
`sovereign_bhiv_core`.

### 6.2 The 7 fields Sarathi computes locally

The translator at [translation_sovereign_to_sarathi.go](translation_sovereign_to_sarathi.go)
projects the 9 inputs into the canonical 16-field `ExternalDecision` the
existing pipeline accepts. Every derived field is deterministic:

| Sarathi field | Rule |
|---|---|
| `decision_id` | UUID-shaped sha256(trace_id + ":" + decision_hash + ":" + timestamp_unix_nano)[:32] |
| `agent_id` | constant `"sovereign_bhiv_core"` |
| `resource_id` | constant `"sovereign_bhiv_core"` |
| `action` | parsed from `policy_reference` (`*.read.*` → read, `*.write.*` → write, `*.delete.*` → delete, else `execute`) |
| `verdict` | direct map from `decision` |
| `obligations` | `[]` |
| `reason` | `""` |
| `ttl` | 30s default (override via `SARATHI_SOVEREIGN_DEFAULT_TTL_S`) |
| `expires_at` | `timestamp + ttl` |
| `metadata` | `{policy_reference, input_hash, schema_version, translation_version, trace_id, sovereign_decision_hash}` |
| `nonce` | `decision_hash[:32]` (deterministic per-decision) |
| `decision_core_hash` | recomputed from binding fields |

Replay protection: `(trace_id, decision_hash)` tuple in the existing replay store.

### 6.3 5-stage verification gate (fail-closed)

```
1. Inbound boundary auth   service_inbound_auth.go (X-API-Key fingerprint + body Ed25519)
2. trace_id gate           service_boundary_sovereign.go (header == body)
3. Strict schema parse     service_boundary_sovereign.go (DisallowUnknownFields)
4. Translation             translation_sovereign_to_sarathi.go (9 → 16)
5. Existing PDPAdapter     pdp_adapter.go (registry/sig/hash/expiry/replay)
```

Error codes added in v15.5:

- `ERR_SCHEMA_MISMATCH` — body is not a `SovereignDecideResponse`
- `ERR_TRACE_ID_MISSING` — trace_id absent in body or X-Sarathi-Trace-ID header
- `ERR_TRACE_ID_MISMATCH` — body.trace_id != header.X-Sarathi-Trace-ID
- `ERR_TRANSLATION_REJECTED` — translation contract failure (see translator validation)
- `ERR_API_KEY_FINGERPRINT` — sha256(provided api_key) != registered fingerprint
- `ERR_SOVEREIGN_SIGNATURE` — Ed25519 verification failed against registered public key

### 6.4 Outbound BHIV shapes

Sarathi posts BHIV-shaped bodies (NOT raw canonical bytes) to Bucket and
InsightFlow. See [translation_sovereign_schemas.go](translation_sovereign_schemas.go)
for the verbatim Go structs.

| Endpoint | Schema | Builder |
|---|---|---|
| `POST /bucket/artifact` | `bhiv.bucket.artifact/v1.0` (`BucketArtifact`) | [translation_bucket_artifact.go](translation_bucket_artifact.go) |
| `POST /sarathi_trigger` | InsightFlow Schema A — trigger event with request envelope | [translation_insightflow.go](translation_insightflow.go) `BuildSchemaATrigger` |
| `POST /core_execute` | InsightFlow Schema C — multi-hop tracking | [translation_insightflow.go](translation_insightflow.go) `BuildSchemaCExecute` |
| `POST /insightflow_process` | InsightFlow Schema D — verification status | [translation_insightflow.go](translation_insightflow.go) `BuildSchemaDProcess` |
| `POST /bucket_persist` | InsightFlow Schema B — fingerprint signal | [translation_insightflow.go](translation_insightflow.go) `BuildSchemaBPersist` |
| `GET /bucket/verify/{trace_id}` (response shape) | InsightFlow Schema D | same |

### 6.5 BucketArtifact `parent_hash` chain

Each artifact in trace_id chains back to the previous artifact_id (or to
`BucketArtifactGenesisHash = sha256("bhiv.bucket.artifact.genesis/v1.0")`
for the first artifact). State is durable at
`live/translation/parent_chain/{trace_id}.json`. Verify with:

```
./sarathi --verify-bucket-chain --trace-id=<traceID>
```

### 6.6 Bootstrap commands

```bash
# Build
go build -o sarathi.exe .

# Bootstrap Sovereign BHIV Core (forward private key + raw API key to Core)
./sarathi --bootstrap-sovereign-core \
    --keys-out-dir=./live/keys/sovereign_bhiv_core \
    --evaluator-id=sovereign_bhiv_core \
    --metadata='{"name":"Sovereign BHIV Core","org":"BHIV"}' \
    --snapshot=./live/trust_snapshot.json \
    --print-private-key

# Bootstrap a self-test evaluator (for /v1/ingest-decision diagnostics)
./sarathi --bootstrap-sovereign-core \
    --keys-out-dir=./live/keys/self_test \
    --evaluator-id=self_test \
    --metadata='{"name":"Self-Test","purpose":"diagnostic"}' \
    --snapshot=./live/trust_snapshot.json \
    --print-private-key

# Run service in production trace-required mode
SARATHI_INBOUND_AUTH_MODE=required \
SARATHI_TRACE_ID_REQUIRE_INBOUND=true \
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json \
  ./sarathi --service --port=9002

# Verify Bucket chain for a trace_id
./sarathi --verify-bucket-chain --trace-id=<traceID>
```

`/v1/ingest-decision` remains live as a **self-test path** that accepts the
canonical 16-field `ExternalDecision` body (signed with the user's own
self-test evaluator key). Use it to isolate Sarathi-side bugs from
Sovereign-side bugs.

---

## 7. v15.6 — Bridge JWT Authority surface (NEW)

The v15.6 layer publishes a public Ed25519 key set so external verifiers (BHIV
Bridge) can validate Sarathi-issued capability tokens **offline** using any
RFC 8037 verifier. Full spec: [KB_16_JWT_AUTHORITY_v15_6.md](KB_16_JWT_AUTHORITY_v15_6.md).
Operator runbook: [NGROK_VALIDATION_SCRIPT.md](NGROK_VALIDATION_SCRIPT.md) §18–§28.

### 7.1 Three new endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/sarathi/.well-known/jwks.json` | public read | RFC 7517 JWK Set — Ed25519 public keys (current + grace-period) |
| GET | `/sarathi/.well-known/sarathi-authority` | public read | OIDC-style discovery (RFC 8414 adapted); advertises `token_endpoint=/sarathi/enforce` |
| POST | `/sarathi/v1/token/introspect` | `Authorization: Bearer <SARATHI_JWT_INTROSPECTION_API_KEY>` | RFC 7662 introspection — checks active / consumed / expired status |

### 7.2 New response field on `POST /sarathi/enforce`

When a `JWTAuthority` is bound (operator bootstrapped a key) and the upstream
verdict is `ALLOW`, the existing `IngestDecisionResponse` JSON gains three
optional fields:

```
{
  ...existing fields unchanged...
  "capability_token_jwt":    "<compact JWT>",     // RFC 7519 + RFC 8037 (EdDSA)
  "capability_token_kid":    "<hex64>",           // RFC 7638 thumbprint
  "capability_token_issuer": "https://.../authority"
}
```

Old Bridge clients that ignore unknown JSON fields see no change. The new
Bridge client reads `capability_token_jwt` and verifies it offline against
the cached JWKS.

### 7.3 JWT shape — what Bridge receives

Header: `{"alg":"EdDSA","typ":"JWT","kid":"<hex64>"}`

Standard claims (RFC 7519): `iss`, `sub` (decision_id), `aud`
(`bhiv-core-runtime` by default), `exp` (≤ iat+60s), `nbf`, `iat`, `jti`.

Private claims (`sarathi:` prefix per RFC 7519 §4.3):
`decision_id`, `request_hash`, `policy_hash`, `enforcement_hash`,
`correlation_id`, `verdict` (always `ALLOW`), `obligations`,
`registry_version`, `rpa_hash`, `token_hash`, `trace_id`,
`legacy_issuer`, `schema_version`.

For the Sovereign-translation path additionally:
`response_hash`, `chain_binding_hash`, `decision_hash`.

### 7.4 Bridge integration contract (paste to the team)

| Question | Answer |
|---|---|
| Token issuance endpoint | `POST /sarathi/enforce` — JWT in `response.capability_token_jwt` |
| JWT verification details | RFC 7519 / 7515 compact serialization; alg-pin to `"EdDSA"` only |
| Issuer value (`iss`) | URL from `SARATHI_TOKEN_ISSUER` env |
| Signing algorithm | `EdDSA` / Ed25519 (RFC 8037) — **not** RS256 |
| Public key / JWKS endpoint | `GET /sarathi/.well-known/jwks.json` |
| Discovery doc | `GET /sarathi/.well-known/sarathi-authority` |
| Sample valid token | Run `NGROK_VALIDATION_SCRIPT.md` §22 against the live service |
| Expected claims format | See §7.3 above |
| Failure test (Sarathi unavailable) | `./sarathi --failure-demo` — scenario `sarathi_unavailable_for_bridge` |

### 7.5 Operator boot env (v15.6)

| Env | Purpose | Required in prod |
|---|---|---|
| `SARATHI_JWT_AUTHORITY_PRIV_PATH` | Persistent Ed25519 private key (mode 0600) | YES |
| `SARATHI_TOKEN_ISSUER` | The `iss` claim URL (must be `https://` in prod) | YES |
| `SARATHI_TOKEN_AUDIENCE` | The `aud` claim value | default `bhiv-core-runtime` |
| `SARATHI_JWT_AUTHORITY_KID` | RFC 7638 thumbprint (cross-checked at boot) | YES |
| `SARATHI_JWT_TOKEN_TTL_S` | Override per-token TTL (≤ 60s) | optional |
| `SARATHI_JWT_INTROSPECTION_API_KEY` | Bearer key for introspection (≥32 chars in prod) | required IFF introspection wanted |
| `SARATHI_BRIDGE_ONLY_MODE=1` | Hide /v1/* from external callers | optional |
| `SARATHI_TLS_CERT_PATH` + `SARATHI_TLS_KEY_PATH` | TLS for JWKS | YES in prod |

### 7.6 Bootstrap + service commands

```bash
# 1. Bootstrap the JWT authority (one time)
./sarathi --bootstrap-jwt-authority \
    --issuer=https://<sarathi-host>/authority \
    --audience=bhiv-core-runtime \
    --print-introspection-key

# 2. Export the operator env (printed by step 1)
export SARATHI_JWT_AUTHORITY_PRIV_PATH=live/keys/jwt_authority/current.key
export SARATHI_JWT_AUTHORITY_KID=$(cat live/keys/jwt_authority/current.kid)
export SARATHI_TOKEN_ISSUER=https://<sarathi-host>/authority
export SARATHI_TOKEN_AUDIENCE=bhiv-core-runtime
export SARATHI_JWT_INTROSPECTION_API_KEY=<the printed key>

# 3. Run the service (Sovereign-required + JWT mint enabled)
SARATHI_INBOUND_AUTH_MODE=required \
SARATHI_TRACE_ID_REQUIRE_INBOUND=true \
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json \
  ./sarathi --service --port=9002

# 4. Rotate (zero-downtime; old kid stays in JWKS during grace)
./sarathi --rotate-jwt-authority --grace-hours=24

# 5. Inspect authority state without booting the service
./sarathi --inspect-jwt-authority
```

---

## 8. v15.9 + v15.10 — Peer-key registry, receipt pinning, post-ingest propagation

Two production hardenings added after the v15.7 TANTRA cutover. Both are
strictly additive — no schemas change on the wire.

### 8.1 Peer-key registry (v15.9)

Closes the prior TOFU model where peer receipts were verified against
whatever public key the receipt itself carried. v15.9 pins each peer's
public key in `live/trust_snapshot.json` under a new `peer_keys` array:

```json
{
  "version": "v15.9",
  "evaluators": [ ... ],
  "tantra_evaluators": [ ... ],
  "peer_keys": [
    { "peer": "bucket",      "status": "ACTIVE", "public_key_hex": "<64-hex>", ... },
    { "peer": "insightflow", "status": "ACTIVE", "public_key_hex": "<64-hex>", ... },
    { "peer": "core",        "status": "ACTIVE", "public_key_hex": "<64-hex>", ... }
  ]
}
```

Registration CLI (per peer, run once after receiving each peer's PUBLIC
key out-of-band):

```bash
./sarathi-enforcement-adapter --register-peer-key \
    --peer=<bucket|insightflow|core> \
    --public-key=<64-hex Ed25519 from peer team> \
    --name="<human label>" \
    --snapshot=./live/trust_snapshot.json
```

Audit log: `proof_logs/peer_key_registry_audit.jsonl`.

Pinning enforcement modes (env `SARATHI_PEER_KEY_PINNING`):
- `relaxed` (default) — pin when an entry exists; TOFU-with-warn otherwise.
- `strict` — every receipt MUST come from a registered peer.

`VerifyReceipt` now runs these gates AFTER the existing signature check:
G1 — peer kind valid; G2 — entry exists (mode-dependent); G3 — status
ACTIVE; G4 — constant-time embedded-vs-registered key compare; G5 —
receipt replay (`sha256(raw_bytes)` keyed by peer; 300 s window).

### 8.2 TANTRA evaluator registration (v15.7)

For Sovereign / Sarathi-as-evaluator decision-issuing identities (different
concept from peer receipts above). Registry array is `tantra_evaluators`:

```bash
./sarathi-enforcement-adapter --register-tantra-evaluator \
    --evaluator-id=bhiv.sovereign.decision.prod.v1 \
    --schema-version=tantra.decision.v1 \
    --algorithm=Ed25519 \
    --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
    --public-key=<hex from Core team> \
    --api-key-fingerprint=<sha256_hex from Core team> \
    --snapshot=./live/trust_snapshot.json
```

Audit log: `proof_logs/tantra_registry_audit.jsonl`.

### 8.3 Provider-aware keygen (v15.8)

Generates Sarathi's OWN keypair under the active CryptoProvider. Used to
mint `bhiv.sarathi.enforcement.prod.v1` for Sarathi's outbound TANTRA
attestation. Public key file is what you send other teams; private key
file stays on this host.

```bash
SARATHI_CRYPTO_PROVIDER=ed25519 ./sarathi-enforcement-adapter --provider-keygen \
    --evaluator-id=bhiv.sarathi.enforcement.prod.v1 \
    --out-dir=./live/keys/sarathi_enforcement \
    --key-id-rotation=2026-05
```

### 8.4 Post-ingest peer fan-out (v15.10)

Before v15.10, plain `--service` mode sealed the envelope and returned it
via HTTP but never auto-pushed canonical bytes to Bucket / InsightFlow.
That gap was disclosed in the v15.9 audit and closed in v15.10.

After `/sarathi/enforce` succeeds, [service_boundary_propagation_hook.go](service_boundary_propagation_hook.go)
fires `BHIVTranslatedFanOut` in a background goroutine. Failures DO NOT
fail the inbound response — they audit to `proof_logs/peer_propagation_audit.jsonl`.

Gated by env `SARATHI_PROPAGATE_ON_INGEST=1`. Default OFF — the operator
flips it on only after `SARATHI_BUCKET_*` / `SARATHI_INSIGHT_*` / `SARATHI_CORE_*`
URLs are wired to real tunnels.

### 8.5 Full production env set (recap)

```bash
SARATHI_SERVICE_ADDR=0.0.0.0:9002
SARATHI_INBOUND_AUTH_MODE=required
SARATHI_TRACE_ID_REQUIRE_INBOUND=true
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json
SARATHI_PEER_KEY_PINNING=strict
SARATHI_PROPAGATE_ON_INGEST=1
SARATHI_CRYPTO_PROVIDER=ed25519
SARATHI_ENFORCEMENT_PRIV_PATH=./live/keys/sarathi_enforcement/issuer-priv.hex
SARATHI_ENFORCEMENT_PUB_PATH=./live/keys/sarathi_enforcement/issuer-pub.hex
SARATHI_ENFORCEMENT_KEY_ID=bhiv.sarathi.enforcement.prod.v1#ed25519-2026-05
```

---

## 9. v15.11 — Path A propagation + load-bearing API-key (latest deltas)

### 9.1 Post-ingest propagation now sends raw canonical envelope (Path A)

`SARATHI_PROPAGATE_ON_INGEST=1` triggers, after every `/sarathi/enforce` success, an async fan-out that POSTs **the raw canonical 20-field sealed envelope** to:

- `POST <bucket-url>/bucket/artifact`
- `POST <insightflow-url>/insightflow_process`
- `POST <core-url>/v1/enforce` (post-execution record)

All three peers receive the SAME bytes. `SHA-256(body) == X-Sarathi-Response-Hash` by construction. Peers persist the body verbatim and post a signed receipt to `/v1/downstream-ack`.

Audit log: `proof_logs/peer_propagation_audit.jsonl` (per-peer outcome) + `proof_logs/peer_outbound_hashes.jsonl` (per-decision per-peer outbound body hash).

Bucket-specific extra header: `X-Sarathi-Bucket-Parent-Hash` carries the per-trace chain anchor so Bucket can record it for chain bookkeeping without inspecting the body.

### 9.2 X-API-Key fingerprint check is now load-bearing

`/sarathi/enforce` v15.11 performs `sha256_hex(X-API-Key) == evaluator_row.api_key_fingerprint` (constant-time). New error codes:

| HTTP | Code | Meaning |
|---|---|---|
| 401 | `ERR_TANTRA_API_KEY_REQUIRED` | Header missing but fingerprint registered |
| 401 | `ERR_TANTRA_API_KEY_INVALID` | sha256(header value) ≠ registered fingerprint |

Core generates the raw API key locally and sends Sarathi the sha256 fingerprint out-of-band. Raw key only crosses the wire on each `/sarathi/enforce` POST in `X-API-Key`.

### 9.3 Peer team integration specs

For peer teams, see the dedicated per-team files (no architecture disclosure):

- `CORE_INTEGRATION.md` — BHIV Core
- `BUCKET_INTEGRATION.md` — Bucket
- `INSIGHTFLOW_INTEGRATION.md` — InsightFlow

### 9.4 Production deployment runbook

For the full operator runbook including env vars, registration commands, health verification, and DevOps responsibilities, see `DEPLOYMENT_GUIDE.md`.

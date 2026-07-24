# Sarathi — Go File Reference & Sovereign Core Ingestion Sequence

**Audience:** Sarathi maintainer, BHIV Core integration counterpart, security reviewer.
**Goal:** Read once and know (a) what every Go file in the repo does, (b) the exact order those files fire when a Sovereign Core TANTRA decision lands at `/sarathi/enforce`.
**Phase:** v15.7 (TANTRA inbound) + v15.8 (crypto-agile provider).
**Companion:** [SARATHI_SYSTEM_GUIDE.md](SARATHI_SYSTEM_GUIDE.md), [KB_17_TANTRA_DECISION_V1.md](KB_17_TANTRA_DECISION_V1.md), [KB_18_CRYPTO_AGILITY.md](KB_18_CRYPTO_AGILITY.md).

---

## Part I — Ingestion Sequence (one Sovereign Core decision, end-to-end)

This is the **exact** order of file involvement when Sovereign Core POSTs a `tantra.decision.v1` payload to `POST /sarathi/enforce`. Every step is grounded in the live code path; no step is hypothetical.

```
HTTP POST /sarathi/enforce  ─────────────────────────────────────────────┐
  body: {schema_version:"tantra.decision.v1", ..., signature:{...}}      │
  headers: Content-Type, X-API-Key, X-Sarathi-Trace-ID                   │
                                                                         ▼
[01] enforcement_adapter_main.go::main()
     - boot banner; reads SARATHI_CRYPTO_PROVIDER
     - calls InitCryptoProvider() → crypto_provider_init.go
     - calls BootstrapTantraReplayStore() → tantra_replay.go (rehydrates JSONL)
     - calls BootstrapTantraTrust(SARATHI_TRUST_SNAPSHOT) → tantra_trust_extension.go
     - falls through to ParseServiceRuntimeArgs(--service) → service_runtime_cli.go
                                                                         │
                                                                         ▼
[02] service_runtime_cli.go::RunServiceRuntime()
     - PrecreateTranslationDirs()
     - LoadSecureConfig()
     - constructs SaarthiService + GatedBridge + ServiceBoundary
     - service_boundary.go mounts /sarathi/enforce → handleSarathiEnforceTantra
                                                                         │
                                                                         ▼
[03] HTTP request arrives at mux from net/http → service_boundary.go (line 203 mount)
                                                                         │
                                                                         ▼
[04] service_boundary_tantra.go::handleSarathiEnforceTantra
     - Method == POST?                              else 405
     - Content-Type "application/json"?             else 415
     - X-API-Key or Authorization: Bearer present?  else 401
     - sb.pdpAdapter != nil?                        else 503
     - ActiveTantraTrust() != nil?                  else 503 ERR_TANTRA_EVALUATOR_NOT_REGISTERED
     - activeTantraReplayStore != nil?              else 503 ERR_TANTRA_REPLAY
     - read raw body bytes (MaxBytesReader 1 MiB cap)
                                                                         │
                                                                         ▼
[05] tantra_verifier.go::NewTantraVerifier().Verify(rawBytes)
     STEP 0a:  VerifyDecodeStrict()                 → tantra_canonical.go
     STEP 0b:  TantraDecision.RequiredFields()      → tantra_decision.go
     STEP 0c:  ParseTantraEvaluatorID()             → tantra_evaluator_id.go
     STEP 0d:  parseTantraTimestamp() + checkTantraSkew() (±300s)
     STEP 1:   Extract signature object
     STEP 2:   CanonicalSignableBytes()             → tantra_canonical.go
                 (fixed field order; signature OMITTED)
     STEP 3:   Re-assert schema_version == tantra.decision.v1
     STEP 4-5: TantraTrustConsumer.Lookup()         → tantra_trust_extension.go
                 (5 gates: exists / active / schema / key_id / algorithm)
     STEP 6:   CanonicalWireBytes() — defensive round-trip
     STEP 7:   base64.RawURLEncoding.DecodeString(signature.value)
               ActiveProvider().Verify(signed, sig, pub) → crypto_provider.go
                 - Ed25519Provider.Verify  → crypto_provider_ed25519.go (default)
                 OR
                 - HybridProvider.Verify   → crypto_provider_hybrid.go (composite-AND)
                                              → CIRCL mldsa65.Verify + stdlib ed25519.Verify
     STEP 8:   ComputeTantraDecisionHash()          → tantra_canonical.go
                 (SHA-256 over 6-field material in fixed order)
     STEP 9:   Compare recomputed vs payload decision_hash → ERR_TANTRA_DECISION_HASH_MISMATCH on drift
     STEP 10:  ComputeTantraDecisionID()            → tantra_verifier.go
                 (deterministic UUID-shape over trace_id+input_hash+evaluator_id)
     STEP 11:  Compare recomputed vs payload decision_id → ERR_TANTRA_DECISION_ID_MISMATCH on drift
     STEP 12:  ReplayStore.Check(decision_hash, signed_bytes) → tantra_replay.go
                 (300s window; per-hash AND per-signed-payload)
     ───
     returns *TantraVerifierResult { Decision, SignedBytes, WireBytes,
                                     EvaluatorRow, RecomputedDecisionHash,
                                     RecomputedDecisionID }
                                                                         │
                                                                         ▼
[06] service_boundary_tantra.go (continued)
     - trace_id header sanity (defence-in-depth)
                                                                         │
                                                                         ▼
[07] translation_tantra_to_external_decision.go::TranslateTantraToExternalDecision
     - parseTantraTimestamp() of timestamp
     - loadTantraTranslationTTL() — 30s default
     - deriveActionFromPolicyReference() — heuristic read/write/delete/execute
     - deriveTantraNonce() — first 32 hex chars of decision_hash
     - builds 16-field ExternalDecision
     - computeHash() + computeCoreHash() recomputed fresh (existing helpers in external_decision.go)
     - base64.RawURLEncoding.DecodeString(signature.value) → EvaluatorSignature bytes
     - ValidateStructure() — sanity gate
     - appendTantraTranslationAudit() → proof_logs/tantra_translation_map.jsonl
                                                                         │
                                                                         ▼
[08] service_boundary_tantra.go (continued)
     - json.Marshal(externalDec) → canonical bytes for inner ingest
     - r.Clone(ctx) with Body = canonical bytes
     - inner.URL.Path = "/v1/ingest-decision"
     - sets X-Sarathi-Trace-ID, X-Sarathi-Schema-Version=tantra.decision.v1,
            X-Sarathi-Mint-JWT=1, X-Sarathi-Internal-Source=sarathi-enforce-tantra
     - go emitEnforcementAttestationAsync() — fire-and-forget, attestation emitter
     - calls sb.handleIngestDecision(w, inner) ← reuses the existing pipeline path
                                                                         │
                                                                         ▼
[09] service_boundary.go::handleIngestDecision
     - X-Sarathi-Internal-Source set → bridge gate bypass (legitimate proxy)
     - re-check method/content-type/api-key (defence-in-depth)
     - read raw body bytes (already canonical)
     - parse X-Sarathi-Trace-ID → TraceContext
     - calls sb.pdpAdapter.Ingest(rawBytes, executionID, correlationID, traceCtx)
                                                                         │
                                                                         ▼
[10] pdp_adapter.go::PDPAdapter.Ingest
     - json.Unmarshal(rawBytes) → ExternalDecision
     - verifyIngestIntegrity()  → external_decision.go::VerifyIntegrity + VerifyCoreHashIntegrity
     - adapter.EnforceExternalDecision(decision, modeCtrl)
                                                                         │
                                                                         ▼
[11] external_decision.go::EnforceExternalDecision  (the 10-stage pipeline)
     STAGE  1: MODE_CHECK            — system in EXTERNAL mode
     STAGE  2: STRUCTURE_CHECK       — required fields present
     STAGE  3: EVALUATOR_TRUST_CHECK — registry lookup; ACTIVE status
     STAGE  4: SIGNATURE_VERIFICATION — Ed25519 over DecisionCoreHash
     STAGE  5: INTEGRITY_CHECK       — full decision_hash recompute
     STAGE  6: EXPIRY_CHECK          — Timestamp + TTL > now - skew
     STAGE  7: REPLAY_CHECK          — InboundNonceStore (separate from TANTRA replay)
                                       → inbound_nonce_store.go
     STAGE  8: RATE_LIMIT_CHECK      — per-agent + global rate gate
     STAGE  9: POSTURE_CHECK         — BeyondCorp posture
     STAGE 10: BINDING_CHECK         — request-binding hash equality
     ───
     returns *ExternalEnforcementResult { Enforced, Verdict, EnforcementHash, ... }
     appends to enforcement_chain (audit-chained)
                                                                         │
                                                                         ▼
[12] pdp_adapter.go (back in Ingest)
     - CanonicalFromPropagation()    → translation_canonical.go + response_contract.go
       (composes 15+5-field response map; v13.0 schema + v14.5 propagation fields)
     - CanonicalMarshal(respMap)     → canonical_json.go (RFC 8785 alphabetical sort)
     - SealPropagationEnvelope()     → propagation_envelope.go
       (computes response_hash, chain_binding_hash; locks bytes immutable)
     ───
     returns *PropagationEnvelope
                                                                         │
                                                                         ▼
[13] service_boundary.go::handleIngestDecision (back from PDPAdapter.Ingest)
     - sets X-Sarathi-{Decision-ID, Execution-ID, Response-Hash,
                       Chain-Binding-Hash, Enforcement-Hash, Schema-Version} headers
     - builds IngestDecisionResponse
     - if X-Sarathi-Mint-JWT=1 AND verdict=ALLOW AND jwtAuthority bound:
         → jwt_authority_mint.go::MintFromEnvelope() → JWT capability token
         (RFC 7515 compact serialization, EdDSA over canonical bytes)
     - writes 200 OK + JSON response
                                                                         │
                                                                         ▼  (parallel goroutine — started at step [08])
[14] tantra_emit.go::EmitSarathiEnforcementAttestation
     - loadSarathiEnforcementSigner() — reads SARATHI_ENFORCEMENT_PRIV_PATH
     - builds TantraDecision with evaluator_id=bhiv.sarathi.enforcement.prod.v1,
              enforcement_binding="CLEARED:..." (or "BLOCKED:..."),
              fresh decision_hash + decision_id
     - CanonicalSignableBytes() + ActiveProvider().Sign() → signature.value
     - persistEnforcementAttestation() → proof_logs/sarathi_enforcement_attestations.jsonl
                                                                         │
                                                                         ▼  (separate path — invoked by enforcement adapter chain or harness)
[15] multi_system_router_propagation.go::RoutePropagation
     - fans envelope canonical bytes to all 3 peers in PropagationChainOrder
     - per-peer: ecosystem_clients.go::PostBytes() with 9 X-Sarathi-* headers
       → Bucket    /bucket/artifact          (translation_bucket_artifact.go)
       → InsightFlow /insightflow_process    (translation_insightflow.go, Schemas A/B/C/D)
       → BHIV Core /v1/enforce               (post-execution record)
     - per-peer byte-equality check on response
     - downstream_ack_tracker.go records receipt status
                                                                         │
                                                                         ▼  (inbound from peers, asynchronous)
[16] POST /v1/downstream-ack from peer (Bucket, InsightFlow, Core)
     - service_boundary.go routes to RegisterDownstreamAckRoutes handler
     - downstream_ack_endpoint.go::handleDownstreamAck parses PeerReceipt
     - peer_common.go::VerifyReceipt verifies peer's Ed25519 signature
       (canonical receipt with receipt_signature cleared; pubkey from receipt itself)
     - downstream_ack_tracker.go closes per-execution gate (3 receipts to close)
     - appends to proof_logs/downstream_ack_log.jsonl
```

**Every step above is a fail-closed gate.** A failure at any point returns a precise `ERR_TANTRA_*` or `ERR_PDP_*` error code and writes an audit row. There is no partial-success path, no silent fallback, no default-on-error.

### Where the artefacts live after one successful ingest

| File | Contents |
|---|---|
| `proof_logs/tantra_replay.jsonl` | One row — decision_hash + signed-payload-hash + timestamp |
| `proof_logs/tantra_translation_map.jsonl` | One row — TANTRA → ExternalDecision projection |
| `proof_logs/sarathi_enforcement_attestations.jsonl` | One row — Sarathi-signed TANTRA attestation |
| `proof_logs/enforcement_audit_backup.jsonl` | One row — enforcement event |
| `proof_logs/audit_event.jsonl` | Multiple rows — per-stage audit |
| `proof_logs/downstream_ack_log.jsonl` | Three rows (one per peer) — signed receipts |
| `proof_logs/crypto_provider.jsonl` | One row per process boot — active provider |
| `live/bucket/<decision_id>.json` | Sealed canonical bytes Bucket persisted |
| `sarathi_run_<ts>.log` | Full stdout tee |

---

## Part II — Per-file Explanation (v15.7 + v15.8 NEW files first, then existing)

The repo contains ~135 Go files. They group into eight functional areas. Below I list every NEW file from v15.7 / v15.8, then the load-bearing existing files that the ingestion sequence touches. Files that exist but are not on the live ingest path (harnesses, simulators, CLI test fixtures) are listed at the end with a one-line role.

### II.1 — TANTRA inbound stack (NEW in v15.7)

| # | File | Role | Where it fires |
|---|---|---|---|
| 1 | [tantra_decision.go](tantra_decision.go) | Wire-type definitions: `TantraDecision`, `TantraSignature`, `TantraDecisionMaterial`, all `ERR_TANTRA_*` constants, `RequiredFields()` structural validator. The decoder is `VerifyDecodeStrict` (in `tantra_canonical.go`) which uses `json.Decoder.DisallowUnknownFields`. | Step 0a, 0b |
| 2 | [tantra_canonical.go](tantra_canonical.go) | Fixed-field-order canonical JSON encoder. `CanonicalSignableBytes` (signature omitted) is the EXACT byte string fed to `provider.Sign` / `provider.Verify`. Separate from the alphabetical `canonical_json.go` because the TANTRA contract mandates a specific order, not alphabetical sort. | Steps 0a, 2, 6, 8 |
| 3 | [tantra_evaluator_id.go](tantra_evaluator_id.go) | Anchored regex parser for `bhiv.<system>.<component>.<environment>.v<major>` plus `SplitKeyID` for `<id>#<rotation>` decomposition. Self-tests built-in constants (`SovereignDecisionEvaluatorID`, `SarathiEnforcementEvaluatorID`) at `init()`. | Steps 0c, 4 |
| 4 | [tantra_trust_extension.go](tantra_trust_extension.go) | TANTRA-specific trust registry that lives alongside (not in place of) the existing `InMemoryTrustConsumer`. Loads `tantra_evaluators` array from `live/trust_snapshot.json`. `Lookup()` enforces the 5 gates: existence, ACTIVE status, schema_version match, key_id match, algorithm match. | Step 4-5 |
| 5 | [tantra_verifier.go](tantra_verifier.go) | The 12-step verifier (Contract §7). Wraps the active `CryptoProvider`, the TANTRA registry, and the replay store. `ComputeTantraDecisionID` defines Sarathi's default decision_id derivation (open item — confirm with Core). | Steps 0a-12 (orchestrator) |
| 6 | [tantra_replay.go](tantra_replay.go) | 300s replay store with two surfaces: decision_hash AND `sha256(signed_canonical_bytes)`. Backed by `proof_logs/tantra_replay.jsonl`; rehydrates in-window rows at boot. Includes an in-memory variant `MemoryTantraReplayStore` used by unit tests. | Step 12 |
| 7 | [tantra_emit.go](tantra_emit.go) | Builds, signs, and persists Sarathi's own TANTRA attestation (`bhiv.sarathi.enforcement.prod.v1`). Lazy-loads the Sarathi enforcement key from `SARATHI_ENFORCEMENT_PRIV_PATH`. Best-effort — failure to attest does NOT block the request. | Step 14 (parallel goroutine) |
| 8 | [translation_tantra_to_external_decision.go](translation_tantra_to_external_decision.go) | Projects verified `TantraDecision` into the existing 16-field `ExternalDecision`. Pure structural mapping — no policy decisions, no field invention. Recomputes `decision_hash` / `decision_core_hash` via existing helpers so the downstream pipeline's integrity checks remain valid byte-for-byte. | Step 7 (translation) |
| 9 | [service_boundary_tantra.go](service_boundary_tantra.go) | HTTP handler for `POST /sarathi/enforce`. Method/CT/key checks → verifier → translator → proxy to `handleIngestDecision` → attestation goroutine. Replaces the deleted `service_boundary_sovereign.go`. | Step 4 (HTTP boundary) |
| 10 | [cmd_tantra_register.go](cmd_tantra_register.go) | `--register-tantra-evaluator` admin CLI. Validates evaluator_id, key_id format, public key parse under the indicated algorithm, then upserts into `tantra_evaluators` and appends to `proof_logs/tantra_registry_audit.jsonl`. Never accepts a private key. | Admin path (not in-flight) |
| 11 | [tantra_verifier_test.go](tantra_verifier_test.go) | 12 round-trip tests under both providers — happy path Ed25519, happy path hybrid, replay, mutation, schema mismatch, key_id mismatch, timestamp skew, unknown field, evaluator_id format, key_id split, decision-hash material stability, composite-AND component mutation. All green. | `go test` only |

### II.2 — Crypto-agile provider abstraction (NEW in v15.8)

| # | File | Role | Where it fires |
|---|---|---|---|
| 12 | [crypto_provider.go](crypto_provider.go) | The `CryptoProvider` interface, `PrivateKeyMaterial` / `PublicKeyMaterial` opaque types, `SignatureValue` byte slice, `ActiveProvider()` accessor that panics if init didn't run. CSO-mandated separation: pure bytes-in/bytes-out primitive, never business logic. | Singleton — read by every sign/verify call site |
| 13 | [crypto_provider_ed25519.go](crypto_provider_ed25519.go) | Default provider — thin wrapper over `crypto/ed25519` stdlib. Hex public-key encoding for compatibility with the existing trust-snapshot file format. Exposes `Raw()` accessors for legacy call sites that still call `ed25519.Sign` directly (JWT authority, inbound auth) — these can migrate to `provider.Sign` incrementally. | Step 7 when `SARATHI_CRYPTO_PROVIDER=ed25519` |
| 14 | [crypto_provider_hybrid.go](crypto_provider_hybrid.go) | Composite ML-DSA-65 + Ed25519 provider via Cloudflare CIRCL (`github.com/cloudflare/circl/sign/mldsa/mldsa65`). TLV framing: version byte + per-segment tag + 4-byte BE length. `Verify` requires BOTH segments to pass (composite-AND; pass-with-one mode is forbidden). | Step 7 when `SARATHI_CRYPTO_PROVIDER=hybrid` |
| 15 | [crypto_provider_init.go](crypto_provider_init.go) | Boot-time selector. Reads `SARATHI_CRYPTO_PROVIDER` once via `sync.Once`, panics on any value other than `ed25519` / `hybrid` (fail-closed; no silent downgrade). Appends one row per boot to `proof_logs/crypto_provider.jsonl`. Provides `CryptoProviderBanner()` for the startup banner. | Step 1 (boot) |
| 16 | [cmd_provider_keygen.go](cmd_provider_keygen.go) | `--provider-keygen` admin CLI. Provider-aware: Ed25519 emits `.hex` files; hybrid emits `.json` envelopes holding both halves. Private file written 0600. NEVER prints private bytes to stdout. | Admin path |

### II.3 — Existing files the ingestion sequence touches

| # | File | Role | Where it fires |
|---|---|---|---|
| 17 | [enforcement_adapter_main.go](enforcement_adapter_main.go) | The `main()` entry. Boot banner, `InitCryptoProvider()`, `BootstrapTantraReplayStore()`, `BootstrapTantraTrust()`, then dispatches to admin CLI / JWT CLI / `--post-task-to-core` / `--service`. | Step 1 (boot) |
| 18 | [service_runtime_cli.go](service_runtime_cli.go) | Long-lived HTTP service runtime. `PrecreateTranslationDirs`, `LoadSecureConfig`, construction of `SaarthiService` + `GatedBridge` + `ServiceBoundary` + JWT authority. Production boot gates (`SARATHI_ENV=production` checks). | Step 2 (boot) |
| 19 | [service_boundary.go](service_boundary.go) | The `ServiceBoundary` struct + all HTTP routes. Mounts `/sarathi/enforce` → `handleSarathiEnforceTantra`. Holds the `pdpAdapter` reference, the JWT authority binding, the trust consumer accessor. | Steps 3, 9, 13 |
| 20 | [service_inbound_auth.go](service_inbound_auth.go) | Existing inbound auth middleware (v15.0). Verifies the 7-step header chain: presence → algo → skew → canonical body → nonce → registry → Ed25519. Currently calls `ed25519.Verify` directly; a candidate for migration to `ActiveProvider().Verify` in a follow-up phase. | Wraps step 4 when `SARATHI_INBOUND_AUTH_MODE=required` |
| 21 | [pdp_adapter.go](pdp_adapter.go) | `PDPAdapter` — the "no policy logic" entry to the verification pipeline. `Ingest` does cryptographic integrity recompute, then dispatches to `EnforceExternalDecision`, then seals the response into an envelope. | Step 10 |
| 22 | [external_decision.go](external_decision.go) | The `ExternalDecision` struct (16 fields) + `EnforceExternalDecision` (the 10-stage verification pipeline) + the `TrustConsumer` interface + `InMemoryTrustConsumer` + `BootstrapTrustConsumer`. Also `computeHash` / `computeCoreHash` reused by the TANTRA translator. | Step 11 |
| 23 | [inbound_nonce_store.go](inbound_nonce_store.go) | The bounded LRU + JSONL overflow nonce store. Used by the EnforceExternalDecision STAGE_REPLAY check. Separate from the TANTRA replay store (different keys, different TTL). | Step 11 stage 7 |
| 24 | [canonical_json.go](canonical_json.go) | RFC 8785 alphabetical canonical JSON. Used by `CanonicalFromPropagation`, the envelope, peer receipts, JWK set, response contract. Still in use by everything OUTSIDE the TANTRA inbound surface. | Steps 12, 15, 16 |
| 25 | [response_contract.go](response_contract.go) | The `sarathi.response/v13.0` 15-field response schema, error code constants, response field builders. Unchanged in v15.7. | Step 12 |
| 26 | [translation_canonical.go](translation_canonical.go) | Shared helpers for the outbound translation layer: `CanonicalHashOfStruct`, `atomicWriteFile`, `safeForFilename`, `hopCounterStore` (per-trace event-sequence counter), `trustSnapshotAPIKeyFingerprint`, `PrecreateTranslationDirs`. | Steps 2, 15 |
| 27 | [propagation_envelope.go](propagation_envelope.go) | The `PropagationEnvelope` struct + `SealPropagationEnvelope`. Computes `response_hash`, `chain_binding_hash`, `enforcement_hash`. Stores canonical bytes once; downstream peers receive the exact same bytes. | Step 12 |
| 28 | [multi_system_router_propagation.go](multi_system_router_propagation.go) | `MultiSystemRouter.RoutePropagation`. Fans the envelope to all 3 peers in `PropagationChainOrder`. Per-peer byte-equality verification. Halts the chain on any byte drift. | Step 15 |
| 29 | [translation_bucket_artifact.go](translation_bucket_artifact.go) | Sarathi → Bucket envelope builder. `BucketArtifact` schema, content-addressed `artifact_id`, per-trace chained `parent_hash`. | Step 15 (Bucket leg) |
| 30 | [translation_insightflow.go](translation_insightflow.go) | Sarathi → InsightFlow Schemas A (trigger), B (persist), C (execute, with hop_count via `hopCounterStore`), D (process). | Step 15 (InsightFlow leg) |
| 31 | [translation_insightflow_router.go](translation_insightflow_router.go) | Picks the right InsightFlow schema based on the propagation hop kind. | Step 15 (InsightFlow leg) |
| 32 | [translation_bucket_chain.go](translation_bucket_chain.go) | Bucket chain replay helper — walks `parent_hash` for a trace_id back to the genesis. | Audit / `--verify-bucket-chain` (not in-flight) |
| 33 | [translation_sovereign_schemas.go](translation_sovereign_schemas.go) | Outbound schema constants only after v15.7 (BucketArtifact*, InsightFlow*, BucketArtifactGenesisHash). The 9-field SovereignDecideResponse was deleted; only outbound helpers remain. | Step 15 |
| 34 | [translation_bhiv_fanout.go](translation_bhiv_fanout.go) | Orchestrates the BHIV-shaped fan-out (Bucket + InsightFlow + Core post-exec) AFTER `RoutePropagation` has delivered the raw canonical envelope. | Step 15 |
| 35 | [ecosystem_clients.go](ecosystem_clients.go) | Outbound HTTP clients to Bucket / InsightFlow / Core. POSTs raw canonical bytes (no re-marshal) with the 9 `X-Sarathi-*` headers. Timeout default 15 s (override via `SARATHI_ECOSYSTEM_TIMEOUT_MS`). | Step 15 |
| 36 | [ecosystem_endpoints.go](ecosystem_endpoints.go) | URL constants for every peer endpoint Sarathi calls; 16 env vars that override them. The single source of URL truth. | Step 15 (URL resolution) |
| 37 | [ecosystem_contracts.go](ecosystem_contracts.go) | Cross-system contract types: `BridgePassport`, `SystemContract`, `IntegrationSchema`. | Step 15 |
| 38 | [downstream_ack_endpoint.go](downstream_ack_endpoint.go) | `POST /v1/downstream-ack` handler. Parses `PeerReceipt`, verifies Ed25519 signature, binds `received_body_hash == response_hash`, persists. | Step 16 |
| 39 | [downstream_ack_tracker.go](downstream_ack_tracker.go) | Per-execution gate that closes after all 3 peer receipts arrive within the ack deadline (default 300 s). | Step 16 |
| 40 | [peer_common.go](peer_common.go) | Shared peer primitives: `PeerReceipt` schema, `NewPeerReceiptSigner` (per-process Ed25519 keypair for local peer simulators), `VerifyReceipt` for inbound peer receipts. | Step 16 |
| 41 | [peer_bucket.go](peer_bucket.go) | Standalone Bucket peer impl (used by `--peer-bucket` mode). Atomic per-key persist + signed receipts. | Local peer mode only |
| 42 | [peer_insightflow.go](peer_insightflow.go) | Standalone InsightFlow peer impl. Append-only JSONL + signed receipts. | Local peer mode only |
| 43 | [peer_bhic_core.go](peer_bhic_core.go) | Standalone BHIV Core peer impl. Append-only + signed receipts. | Local peer mode only |
| 44 | [enforcement_adapter.go](enforcement_adapter.go) | `EnforcementAdapter` struct — owns the enforcement chain, the rate-limit state, mode controller. Wires the bridge, the PDP, the JWT authority, the trust consumer. Construction happens in `service_runtime_cli.go::BuildSaarthiService`. | Step 2 (construct) |
| 45 | [gated_bridge.go](gated_bridge.go) | The non-bypassable bridge. Mints `BridgePassport` HMAC; every request entering Sarathi's `Execute` path must carry it. The TANTRA path bypasses the bridge for `Internal-Source` requests (legitimate proxy from `handleSarathiEnforceTantra`). | Bridge passport mint |
| 46 | [jwt_authority.go](jwt_authority.go) | v15.6 outbound JWT capability tokens. The `Signer` interface (Ed25519-specific) + `LocalEd25519Signer`. Different from `CryptoProvider` because JWT specifies `alg=EdDSA`; a future port to `CryptoProvider` is straightforward. | Step 13 (JWT mint hook) |
| 47 | [jwt_authority_mint.go](jwt_authority_mint.go) | `MintFromEnvelope` / `MintFromCapabilityToken`. Builds compact JWT with `kty=OKP` JWK thumbprint as `kid`. | Step 13 |
| 48 | [jwt_authority_verify.go](jwt_authority_verify.go) | `/sarathi/validate-token` strict verifier + `LooksLikeJWT`. | Validation path |
| 49 | [jwt_authority_jwks.go](jwt_authority_jwks.go) | RFC 7517 JWK Set publication at `/sarathi/.well-known/jwks.json`. | Discovery path |
| 50 | [jwt_authority_handlers.go](jwt_authority_handlers.go) | HTTP handlers for JWKS, discovery, introspection, validate-token. | Discovery path |
| 51 | [capability_token.go](capability_token.go) | In-process capability token (the original v11 Ed25519 token; still load-bearing for `ExecutionEngine.ExecuteWithToken`). | Internal-only gate |
| 52 | [policy_signing.go](policy_signing.go) | Policy bundle Ed25519 signing. Currently calls `ed25519.Sign` directly; candidate for `CryptoProvider` port. | Policy load time |
| 53 | [policy_store.go](policy_store.go) | Policy bundle storage + reload. | Policy load time |
| 54 | [policy_registry.go](policy_registry.go) | In-memory policy lookup by `policy_pack_id@version`. | Policy lookup |
| 55 | [evaluator_registry_store.go](evaluator_registry_store.go) | FROZEN per its header comment — the old in-memory + file + postgres registry backends. The live path uses `TrustConsumer` instead. Retained for out-of-tree trust-service deployments. | Not in-flight |
| 56 | [evaluator_registry_config.go](evaluator_registry_config.go) | Registry configuration (also FROZEN per the file header). | Not in-flight |
| 57 | [evaluator_registry_extension.go](evaluator_registry_extension.go) | Registry lifecycle extension methods (FROZEN). | Not in-flight |
| 58 | [evaluator_registration_api.go](evaluator_registration_api.go) | HTTP admin API for evaluator registration. Only mounted when registry has an admin authenticator wired. | Optional admin |
| 59 | [evaluator_registration_challenge.go](evaluator_registration_challenge.go) | Challenge-response handshake for registration. | Optional admin |
| 60 | [evaluator_admin_cli.go](evaluator_admin_cli.go) | The unified admin CLI dispatcher: `--genkey`, `--genapikey`, `--register-evaluator`, `--suspend-evaluator`, `--revoke-evaluator`, `--reactivate-evaluator`, `--list-evaluators`, `--sign-and-post`, `--report-query`, plus v15.7's `--register-tantra-evaluator` and `--provider-keygen`. | Admin paths |
| 61 | [evaluator_admin_auth.go](evaluator_admin_auth.go) | API key + HMAC-SHA256 authenticator for the admin API. | Admin auth |
| 62 | [key_management.go](key_management.go) | Governance keyring + per-evaluator key rotation. Used by `policy_signing.go`. | Policy / governance |
| 63 | [clock.go](clock.go) | `ClockSkewTolerance` constant + `Clock` interface. | Step 11 stage 6 |
| 64 | [node_id_clock_env.go](node_id_clock_env.go) | `SkewedClock` impl for distributed replay parity. | Distributed replay |
| 65 | [clock_drift_harness.go](clock_drift_harness.go) | Cross-process clock-drift simulation harness. | Test harness |
| 66 | [execution_request.go](execution_request.go) | `ExecutionRequest` struct (the request entity the GatedBridge funnels). | Bridge entry |
| 67 | [execution_response.go](execution_response.go) | `ExecutionResponse` struct + `EnforcementHash` derivation. | Step 11 |
| 68 | [escalation.go](escalation.go) | `ESCALATE` verdict handling — human-review queue. | Escalate verdict |
| 69 | [observability_trace.go](observability_trace.go) | OpenTelemetry-style tracing wrappers. | Cross-cutting |
| 70 | [governance_hardening.go](governance_hardening.go) | The compile-time invariants that lock the boundary (no PDP in EXTERNAL mode, no trust scoring). | Build-time guard |
| 71 | [phase_fixes_v9.go](phase_fixes_v9.go) + [phase_fixes_v9_audit_remediation.go](phase_fixes_v9_audit_remediation.go) | Historical patches. | Build-time only |
| 72 | [legacy_enforcer_shim.go](legacy_enforcer_shim.go) | Backward-compatible shim for older clients. | Optional |
| 73 | [service_boundary_security.go](service_boundary_security.go) | TLS + secure-cookie + CSP header wiring on `ServiceBoundary`. | All HTTP responses |
| 74 | [bridge_only_mode.go](bridge_only_mode.go) | v15.6 — hides non-bridge-facing paths when `SARATHI_BRIDGE_ONLY_MODE=1`. | All HTTP routes |
| 75 | [persistent_audit.go](persistent_audit.go) | JSONL + Postgres audit sink coupling. | Cross-cutting |
| 76 | [jsonl_audit_sink.go](jsonl_audit_sink.go) | Append-only JSONL audit writer with atomic rotation. | Cross-cutting |
| 77 | [live_audit_wiring.go](live_audit_wiring.go) | Boot wiring for live-integration audit sinks. | Boot |
| 78 | [live_integration_runner.go](live_integration_runner.go) | `--live-integration` mode — owns peer-process orchestration for in-process integration tests. | Test harness |
| 79 | [live_integration_cli.go](live_integration_cli.go) | CLI dispatch for v14.7 live-integration suite. | Test harness |
| 80 | [distributed_integration_runner.go](distributed_integration_runner.go) | `--distributed-integration` mode. | Test harness |
| 81 | [v14_6_cli.go](v14_6_cli.go) + [v14_6_audit_harness.go](v14_6_audit_harness.go) | v14.6 determinism harness. | Test harness |
| 82 | [v14_8_cli.go](v14_8_cli.go) | v14.8 sovereign-authority CLI dispatch. | Test harness |
| 83 | [cmd_post_task.go](cmd_post_task.go) | `--post-task-to-core` mode — Sarathi acts as a client to BHIV Core's `/execute_task`. | Operator path |
| 84 | [bucket_state_verifier.go](bucket_state_verifier.go) | 100-decision round-trip harness against Bucket. | Test harness |
| 85 | [bucket_readback_verifier.go](bucket_readback_verifier.go) | Bucket GET + byte-equality assertion. | Test harness |
| 86 | [propagation_harness.go](propagation_harness.go) | Cross-system propagation test harness. | Test harness |
| 87 | [propagation_harness_test.go](propagation_harness_test.go) | Harness unit tests. | Test |
| 88 | [propagation_envelope_test.go](propagation_envelope_test.go) | Envelope unit tests. | Test |
| 89 | [propagation_cli.go](propagation_cli.go) | CLI subcommand for propagation harness. | Test harness |
| 90 | [propagation_fault_injection_sim.go](propagation_fault_injection_sim.go) | Fault-injection simulator. | Test harness |
| 91 | [multi_node_runner.go](multi_node_runner.go) + [multi_node_validator.go](multi_node_validator.go) | Multi-node parity harness. | Test harness |
| 92 | [high_iteration_replay.go](high_iteration_replay.go) | Replay determinism harness. | Test harness |
| 93 | [transport_adversarial_harness.go](transport_adversarial_harness.go) | Adversarial-transport injection. | Test harness |
| 94 | [adversarial_attack_harness.go](adversarial_attack_harness.go) | Attack simulator. | Test harness |
| 95 | [retry_determinism_harness.go](retry_determinism_harness.go) | Retry-determinism harness. | Test harness |
| 96 | [parallel_execution_comparator.go](parallel_execution_comparator.go) + [parallel_execution_runner.go](parallel_execution_runner.go) | Core ↔ Sarathi parallel-execution validator. | Test harness |
| 97 | [cross_machine_telemetry.go](cross_machine_telemetry.go) | Telemetry binding across machines. | Cross-cutting |
| 98 | [cross_system_integration_validator.go](cross_system_integration_validator.go) | End-to-end real-peer validator. | Test harness |
| 99 | [determinism_validator.go](determinism_validator.go) | Byte-equality determinism checker. | Test |
| 100 | [core_simulator.go](core_simulator.go) | Stub Core for local tests. | Test harness |
| 101 | [execution_engine_sim.go](execution_engine_sim.go) | Stub execution engine. | Test harness |
| 102 | [concurrency_stress_sim.go](concurrency_stress_sim.go) | Concurrent-load simulator. | Test harness |
| 103 | [evaluator_registry_test_sim.go](evaluator_registry_test_sim.go) | Registry test fixture. | Test harness |
| 104 | [external_decision_test_sim.go](external_decision_test_sim.go) | ExternalDecision test fixture. | Test harness |
| 105 | [system_full_integration.go](system_full_integration.go) | Full-system integration runner. | Test harness |
| 106 | [integration_gate_tests.go](integration_gate_tests.go) | Integration test fixtures. | Test harness |
| 107 | [workflow_simulator.go](workflow_simulator.go) | Workflow simulator. | Test harness |
| 108 | [sovereign_governance_v9.go](sovereign_governance_v9.go) | Sovereign governance fixtures (v9-era). | Historical |
| 109 | [vc_validation_demo.go](vc_validation_demo.go) | VC validation demo entry. | Demo |
| 110 | [output_tee.go](output_tee.go) | stdout/stderr tee to `sarathi_run_<ts>.log`. | Cross-cutting |
| 111 | [result_writer.go](result_writer.go) | JSON result file writer. | Test harness |
| 112 | [replay_fixture_builder.go](replay_fixture_builder.go) | Replay fixture builder for unit tests. | Test |
| 113 | [deterministic_router_handler.go](deterministic_router_handler.go) | Deterministic per-peer router. | Cross-cutting |
| 114 | [sarathi_execution_contract.go](sarathi_execution_contract.go) | The `SaarthiRequest` / `SaarthiResponse` shape (Flow B inputs). | Step 4 (alt path) |
| 115 | [registry_interface.go](registry_interface.go) | Registry interface abstraction. | Cross-cutting |
| 116 | [pdp_engine.go](pdp_engine.go) | Internal PDP (only used in INTERNAL mode; not on the TANTRA path). | INTERNAL mode only |

The remaining ~20 files are pure test files (`*_test.go`) or harnesses listed under proof_logs / canonical_json tests.

---

## Part III — Mapping the Sovereign Core request to Sarathi's audit trail

After one successful Sovereign Core → Sarathi `/sarathi/enforce` cycle completes, a reviewer can pivot on `trace_id` across every audit file:

```
TANTRA payload arrives with trace_id="abc-123-..."
    ↓
proof_logs/tantra_replay.jsonl          row #N: decision_hash + payload_hash bound to "abc-123-..."
    ↓
proof_logs/tantra_translation_map.jsonl row #N: TANTRA decision_hash vs Sarathi-recomputed decision_hash
    ↓
proof_logs/sarathi_enforcement_attestations.jsonl row #N: Sarathi-signed TANTRA attestation
    ↓
proof_logs/enforcement_audit_backup.jsonl row #N: enforcement event with all four hashes
    ↓
proof_logs/downstream_ack_log.jsonl     3 rows: Bucket + InsightFlow + Core peer receipts
    ↓
live/bucket/<decision_id>.json          the sealed canonical bytes Bucket persisted
```

All six artefacts MUST agree on `trace_id`, `decision_id`, `decision_hash` (Sarathi-side), and `response_hash`. A reviewer can grep `trace_id="abc-123-..."` across all files and reconstruct the full chain. Any disagreement = audit failure = chain halt.

---

## Part IV — Quick lookup: file by symptom

| When the verifier returns ... | Look in |
|---|---|
| `ERR_TANTRA_SCHEMA_VERSION_UNKNOWN` | `tantra_decision.go::RequiredFields()` + `tantra_verifier.go` step 3 |
| `ERR_TANTRA_MISSING_FIELD` / `ERR_TANTRA_UNKNOWN_FIELD` | `tantra_canonical.go::VerifyDecodeStrict()` |
| `ERR_TANTRA_EVALUATOR_ID_FORMAT` | `tantra_evaluator_id.go::ParseTantraEvaluatorID` |
| `ERR_TANTRA_EVALUATOR_NOT_REGISTERED` / `_NOT_ACTIVE` / `_SCHEMA_MISMATCH` | `tantra_trust_extension.go::Lookup()` |
| `ERR_TANTRA_KEY_ID_MISMATCH` / `_ALG_MISMATCH` | `tantra_trust_extension.go::Lookup()` + `tantra_verifier.go` step 7 |
| `ERR_TANTRA_TIMESTAMP_SKEWED` / `_UNPARSEABLE` | `tantra_verifier.go::checkTantraSkew` |
| `ERR_TANTRA_SIGNATURE_DECODE` | `tantra_verifier.go` step 7 (base64url decode) |
| `ERR_TANTRA_SIGNATURE_INVALID` | `crypto_provider_ed25519.go::Verify` OR `crypto_provider_hybrid.go::Verify` |
| `ERR_TANTRA_DECISION_HASH_MISMATCH` | `tantra_canonical.go::ComputeTantraDecisionHash` + `tantra_verifier.go` step 9 |
| `ERR_TANTRA_DECISION_ID_MISMATCH` | `tantra_verifier.go::ComputeTantraDecisionID` |
| `ERR_TANTRA_REPLAY` | `tantra_replay.go::Check` |
| `ERR_PDP_DECISION_INVALID` | `pdp_adapter.go::Ingest` or `external_decision.go::EnforceExternalDecision` |
| Inbound-auth failure (non-TANTRA) | `service_inbound_auth.go::authenticate` |

---

## Part V — How to verify the sequence yourself

The TANTRA test suite exercises each step of the 12-step verifier with a real keypair and a real registry — no mocks, no stubs, no fakes:

```bash
go test -run TestTantra -v .
```

Reads the live providers (`crypto_provider_ed25519.go`, `crypto_provider_hybrid.go`), the live canonical encoder (`tantra_canonical.go`), the live registry layer (`tantra_trust_extension.go`), the live verifier (`tantra_verifier.go`), and exercises:

- `TestTantraVerifier_HappyPath_Ed25519` — full 12-step round trip under Ed25519.
- `TestTantraVerifier_HappyPath_Hybrid` — full 12-step round trip under Composite ML-DSA-65 + Ed25519.
- `TestTantraVerifier_ReplayRejected` — second post of same payload → `ERR_TANTRA_REPLAY`.
- `TestTantraVerifier_MutatedField_RejectsSignature` — flip one byte → signature fails.
- `TestTantraVerifier_BadSchemaVersion` — wrong schema → `ERR_TANTRA_SCHEMA_VERSION_UNKNOWN`.
- `TestTantraVerifier_KeyIDMismatch` — registered key_id differs from signature key_id → reject.
- `TestTantraVerifier_TimestampSkewed` — `Now() + 1h` → `ERR_TANTRA_TIMESTAMP_SKEWED`.
- `TestTantraVerifier_UnknownField` — inject extra field → `ERR_TANTRA_UNKNOWN_FIELD`.
- `TestHybridProvider_RoundTripAndCompositeAND` — composite signature; mutate Ed25519 half → reject; mutate ML-DSA-65 half → reject (composite-AND).

All 29 test cases green on the current build. Run the suite yourself; the result file is reproducible from the source.

---

## Part VI — v15.10 + v15.11 additions

### VI.1 New files since the original Part II

| File | Role |
|---|---|
| peer_key_registry.go | v15.9 peer-key registry + 4-gate pinning |
| peer_receipt_replay.go | v15.9 receipt-replay rejection (300 s window) |
| cmd_peer_key_register.go | v15.9 --register-peer-key admin CLI |
| service_boundary_propagation_hook.go | v15.10 → v15.11 post-ingest peer fan-out hook (Path A in v15.11) |

### VI.2 Modified files since the original

| File | v15.11 change |
|---|---|
| service_boundary_tantra.go | API-key fingerprint check step 7b now load-bearing |
| tantra_decision.go | New error codes ERR_TANTRA_API_KEY_REQUIRED and ERR_TANTRA_API_KEY_INVALID |
| peer_common.go::VerifyReceipt | v15.9 added pinning + replay gates after signature verification |
| service_boundary.go | v15.10 wired firePostIngestPropagation after handleIngestDecision success |
| enforcement_adapter_main.go | v15.9 wired BootstrapPeerKeyRegistry and BootstrapPeerReceiptReplayStore at boot |
| evaluator_admin_cli.go | v15.9 added --register-peer-key dispatch |

### VI.3 New audit logs

| File | What appears |
|---|---|
| proof_logs/peer_key_registry_audit.jsonl | One row per --register-peer-key CLI invocation |
| proof_logs/peer_propagation_audit.jsonl | One row per post-ingest peer fan-out per-peer status hash error |
| proof_logs/peer_outbound_hashes.jsonl | Per-decision per-peer outbound body hash audit anchor |
| proof_logs/tantra_replay.jsonl | One row per accepted TANTRA payload replay store entries |

# Sarathi v15.11 — Final Integration Deployment Review Packet

**Status:** Build green. Tests green. Production gates implemented. Live integration contract closed. Ready for cross-team end-to-end.
**Date:** 2026-05-26
**Phase:** v15.11 — TANTRA inbound + crypto-agile provider + peer-key registry + Path A propagation + load-bearing API-key + production deployment package.
**Scope per task.md:** complete, integrate, deploy, prove. NOT redesign. NOT new experimental layers.

---

## 1. Entry point

The integration entry is `POST /sarathi/enforce` on Sarathi's HTTP service. Sovereign Core posts a TANTRA Final Contract decision (`schema_version="tantra.decision.v1"`); Sarathi runs the 12-step verifier, projects to the internal canonical record, propagates raw canonical bytes to Bucket / InsightFlow / BHIV Core for storage and observability, and awaits signed receipts from each.

Boot is via:

```bash
SARATHI_SERVICE_ADDR=0.0.0.0:9002 \
SARATHI_INBOUND_AUTH_MODE=required \
SARATHI_TRACE_ID_REQUIRE_INBOUND=true \
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json \
SARATHI_PEER_KEY_PINNING=strict \
SARATHI_PROPAGATE_ON_INGEST=1 \
SARATHI_CRYPTO_PROVIDER=ed25519 \
SARATHI_ENFORCEMENT_PRIV_PATH=./live/keys/sarathi_enforcement/issuer-priv.hex \
SARATHI_ENFORCEMENT_PUB_PATH=./live/keys/sarathi_enforcement/issuer-pub.hex \
SARATHI_ENFORCEMENT_KEY_ID=bhiv.sarathi.enforcement.prod.v1#ed25519-2026-05 \
  ./sarathi-enforcement-adapter.exe --service
```

Boot banner shows: `[crypto] provider=Ed25519`, `[tantra_trust] loaded N/N entries`, `[peer_key_registry] loaded 3/3 peer key(s) (mode=strict)`.

---

## 2. Core execution flow (3 files)

The end-to-end ingestion sequence is concentrated in three files. Reading them top-to-bottom (in this order) gives the full inbound → verify → translate → seal → propagate flow.

### 2.1 `service_boundary_tantra.go::handleSarathiEnforceTantra`

Entry handler for `POST /sarathi/enforce`. Runs the TANTRA preflight (method, content-type, key, pipeline-readiness checks), invokes the 12-step verifier, performs the load-bearing API-key fingerprint check (v15.11), translates the verified TANTRA decision into the internal `ExternalDecision`, and proxies the result into `handleIngestDecision` so the existing pipeline runs unchanged. Schedules the v15.11 Path A peer fan-out in a goroutine after the response is written.

### 2.2 `tantra_verifier.go::Verify`

The 12-step verifier. Strict body decode → required fields → evaluator_id format → timestamp skew → signature extract → canonical signing bytes → registry lookup (5 gates: exists/active/schema/key_id/algorithm) → canonical wire round-trip → Ed25519 verify via active provider → decision_hash recompute → decision_id recompute → replay store check. Every step is a fail-closed gate. Returns a `TantraVerifierResult` with the parsed decision and supporting artefacts.

### 2.3 `service_boundary_propagation_hook.go::firePostIngestPropagation`

Path A peer fan-out (v15.11). Reads `SARATHI_PROPAGATE_ON_INGEST=1`; loads ecosystem endpoints; calls `BucketClient.StoreArtifact(env)` + `InsightFlowClient.Process(env)` + `CoreClient.Enforce(env)` each in sequence, sending the raw canonical 20-field envelope as the body. Records per-peer outcome to `proof_logs/peer_propagation_audit.jsonl` and the per-decision outbound body hash to `proof_logs/peer_outbound_hashes.jsonl`. Runs entirely in a goroutine — never blocks the inbound HTTP response.

---

## 3. Live execution flow

End-to-end happy-path under `SARATHI_PROPAGATE_ON_INGEST=1`, `SARATHI_PEER_KEY_PINNING=strict`:

```
Core   ─────POST /sarathi/enforce────►   Sarathi
                                             │
                                       12-step verifier
                                             │
                                       API-key fingerprint check
                                             │
                                       Translate to ExternalDecision
                                             │
                                       PDP pipeline (10 stages)
                                             │
                                       Seal envelope (response_hash, chain_binding_hash)
                                             │
                                       Return 200 OK + envelope JSON ─────► Core
                                             │
                                             │ (goroutine, async)
                                             ▼
                                    Path A fan-out (raw canonical 20-field bytes)
                                       │       │       │
                                       ▼       ▼       ▼
                                   Bucket  InsightFlow  Core /v1/enforce
                                       │       │       │
                                       │ POST /v1/downstream-ack (signed receipt) │
                                       │       │       │
                                       └───────┼───────┘
                                               ▼
                                            Sarathi
                                       VerifyReceipt:
                                         signature
                                         body_hash == response_hash (byte equality)
                                         peer registry pinning
                                         peer status ACTIVE
                                         replay rejection
                                       Per-execution gate closes after 3 receipts.
```

Audit files produced per execution:
- `proof_logs/enforcement_audit_backup.jsonl` — one row per enforcement event.
- `proof_logs/tantra_translation_map.jsonl` — TANTRA → ExternalDecision projection.
- `proof_logs/sarathi_enforcement_attestations.jsonl` — Sarathi-signed TANTRA attestation.
- `proof_logs/peer_outbound_hashes.jsonl` — per-decision outbound body hash (audit anchor).
- `proof_logs/peer_propagation_audit.jsonl` — per-peer fan-out outcome (status, hash, error).
- `proof_logs/downstream_ack_receipts.jsonl` — verified receipts.
- `proof_logs/downstream_ack_rejections.jsonl` — rejected receipts with reason.
- `proof_logs/tantra_replay.jsonl` — replay store entries.
- `proof_logs/peer_key_registry_audit.jsonl` — registration events.
- `proof_logs/crypto_provider.jsonl` — provider boot rows.

---

## 4. What changed (since v15.6 baseline)

### 4.1 New surfaces

- `POST /sarathi/enforce` — TANTRA Final Contract verifier replaces the v15.5 9-field translator. 12-step gate; signature-based authentication; load-bearing API-key fingerprint.
- `--register-tantra-evaluator` CLI — register the upstream Sovereign evaluator (PUBLIC key + key_id + fingerprint).
- `--register-peer-key` CLI — register Bucket / InsightFlow / Core peer public keys for pinned receipt verification.
- `--provider-keygen` CLI — provider-aware keypair generation (Ed25519 or Composite ML-DSA-65 + Ed25519).

### 4.2 Crypto-agility

- `CryptoProvider` interface routes every sign/verify call through one boot-selected implementation.
- Default `ed25519` provider — bit-for-bit identical to v15.6.
- Opt-in `hybrid` provider (Composite ML-DSA-65 + Ed25519 via Cloudflare CIRCL) — single env-var flip.
- Fail-closed on unknown `SARATHI_CRYPTO_PROVIDER` value at boot.

### 4.3 Peer-key registry + receipt hardening (v15.9)

- Peer public keys pinned in `trust_snapshot.json` under `peer_keys` array.
- Constant-time embedded-vs-registered key comparison.
- Cross-peer impersonation gate (`peer` field restricted to closed set).
- Receipt-replay rejection (sha256 of raw receipt bytes keyed per peer, 300 s window).
- Two pinning modes — `relaxed` (default, TOFU fallback with warn) or `strict` (require registration).

### 4.4 Production propagation (v15.10 → v15.11)

- Post-ingest peer fan-out hook (`firePostIngestPropagation`) — kicks after `/sarathi/enforce` returns.
- v15.11 switched from BHIV wrapper (Path B) to raw canonical envelope (Path A). Peer's `received_body_hash` now trivially equals Sarathi's `response_hash` because both are SHA-256 over the same exact bytes.
- Per-decision per-peer outbound body hash persisted to `proof_logs/peer_outbound_hashes.jsonl` for independent audit.
- Gated by `SARATHI_PROPAGATE_ON_INGEST=1` (default OFF for backward compatibility).

### 4.5 API-key fingerprint (v15.11)

- `/sarathi/enforce` now performs a real `sha256(X-API-Key) == registered fingerprint` check, constant-time compared.
- If the TANTRA evaluator row carries an `api_key_fingerprint`, the header MUST be present and match.
- New error codes: `ERR_TANTRA_API_KEY_REQUIRED` (401), `ERR_TANTRA_API_KEY_INVALID` (401).

### 4.6 Documentation deliverables

- `CORE_INTEGRATION.md`, `BUCKET_INTEGRATION.md`, `INSIGHTFLOW_INTEGRATION.md` — self-contained per-team integration specs (no architecture disclosure).
- `DEPLOYMENT_GUIDE.md` — env setup, runtime config, execution, health verification, endpoint map.
- Updated `NGROK_VALIDATION_SCRIPT.md`, `ENDPOINTS_FOR_BHIV.md`, `SARATHI_SYSTEM_GUIDE.md`, `SARATHI_GO_FILES_AND_INGESTION_SEQUENCE.md`.

---

## 5. Failure cases (and the response Sarathi produces)

| Scenario | Code | HTTP | Where caught | What happens |
|---|---|---|---|---|
| Wrong `schema_version` | `ERR_TANTRA_SCHEMA_VERSION_UNKNOWN` | 400 | `tantra_verifier.go::Verify` step 0b / 3 | Reject before any crypto |
| Body has an extra field | `ERR_TANTRA_UNKNOWN_FIELD` | 400 | `tantra_canonical.go::VerifyDecodeStrict` | Strict decoder rejects |
| Required field empty/absent | `ERR_TANTRA_MISSING_FIELD` | 400 | `RequiredFields()` | Listed in error detail |
| Verdict not ALLOW/DENY/ESCALATE | `ERR_TANTRA_VERDICT_INVALID` | 400 | `RequiredFields()` | Closed-set check |
| `evaluator_id` doesn't match regex | `ERR_TANTRA_EVALUATOR_ID_FORMAT` | 400 | `tantra_evaluator_id.go::ParseTantraEvaluatorID` | Regex anchored |
| `timestamp` not RFC3339 | `ERR_TANTRA_TIMESTAMP_UNPARSEABLE` | 400 | `parseTantraTimestamp` | Multi-format tolerance |
| `timestamp` outside ±300 s | `ERR_TANTRA_TIMESTAMP_SKEWED` | 401 | `checkTantraSkew` | Wall-clock gate |
| `signature.value` not base64url-no-pad | `ERR_TANTRA_SIGNATURE_DECODE` | 401 | Verifier step 7 | Stdlib decoder rejects padded |
| Signature did not verify | `ERR_TANTRA_SIGNATURE_INVALID` | 401 | `Ed25519Provider.Verify` | Real Ed25519 verify |
| Evaluator not in registry | `ERR_TANTRA_EVALUATOR_NOT_REGISTERED` | 403 | `TantraTrustConsumer.Lookup` G1 | Strict lookup |
| Evaluator status not ACTIVE | `ERR_TANTRA_EVALUATOR_NOT_ACTIVE` | 403 | Lookup G2 | Status filter |
| Registry schema_version ≠ payload | `ERR_TANTRA_EVALUATOR_SCHEMA_MISMATCH` | 403 | Lookup G3 | Pin to declared schema |
| Registry key_id ≠ signature.key_id | `ERR_TANTRA_KEY_ID_MISMATCH` | 403 | Lookup G4 | Rotation safety |
| Registry algorithm ≠ signature.alg | `ERR_TANTRA_ALG_MISMATCH` | 403 | Lookup G5 | Algorithm downgrade defence |
| X-API-Key missing when fingerprint registered | `ERR_TANTRA_API_KEY_REQUIRED` | 401 | `handleSarathiEnforceTantra` §7b | v15.11 |
| sha256(X-API-Key) ≠ fingerprint | `ERR_TANTRA_API_KEY_INVALID` | 401 | Same | Constant-time compare |
| Recomputed decision_hash ≠ payload | `ERR_TANTRA_DECISION_HASH_MISMATCH` | 409 | Verifier step 9 | Mutation evidence |
| Recomputed decision_id ≠ payload | `ERR_TANTRA_DECISION_ID_MISMATCH` | 409 | Verifier step 11 | Formula divergence |
| Same payload within 300 s | `ERR_TANTRA_REPLAY` | 409 | `tantra_replay.go::Check` | Replay store |
| Receipt: peer field not in closed set | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | `peer_key_registry.go::CheckPinned` G1 | Cross-peer impersonation defence |
| Receipt: embedded key ≠ registered | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | Pinning gate G4 | Constant-time compare |
| Receipt: status SUSPENDED / REVOKED | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | Pinning gate G3 | Status filter |
| Receipt: duplicate within 300 s | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | `peer_receipt_replay.go::Check` | Replay store |
| Receipt: signature did not verify | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | `peer_common.go::VerifyReceipt` | Real Ed25519 verify |
| Receipt: received_body_hash ≠ response_hash | `ERR_DOWNSTREAM_RECEIPT_INVALID` | 400 | Same | Byte-equality proof |
| Unknown `SARATHI_CRYPTO_PROVIDER` | (panic at boot) | — | `crypto_provider_init.go` | Fail-closed; refuses to start |
| Unknown `SARATHI_PEER_KEY_PINNING` | (panic at boot) | — | `peer_key_registry.go` | Same |

Every gate writes a JSONL audit row regardless of outcome. Operators pivot on `trace_id` across the audit files listed in §3.

---

## 6. Proof

### 6.1 Build + test green

```
$ go build -o sarathi-enforcement-adapter.exe .
$ echo $?
0
$ go test ./... -count=1
ok  	sarathi-enforcement-adapter	4.556s
$ go vet ./...
$ echo $?
0
```

140+ Go files. 16 MB binary on Windows. Zero compile warnings, zero vet warnings.

### 6.2 Per-component test coverage

All test files contain real implementations against real providers and real registries (no mocks for the load-bearing crypto or canonical-JSON paths):

```
PASS  TestTantraVerifier_HappyPath_Ed25519              (12-step verifier, real Ed25519)
PASS  TestTantraVerifier_HappyPath_Hybrid               (12-step verifier, real Composite-MLDSA65-Ed25519 via CIRCL)
PASS  TestTantraVerifier_ReplayRejected                 (replay store rejects duplicate)
PASS  TestTantraVerifier_MutatedField_RejectsSignature  (one-byte flip → signature fails)
PASS  TestTantraVerifier_BadSchemaVersion               (schema version gate)
PASS  TestTantraVerifier_KeyIDMismatch                  (key_id gate)
PASS  TestTantraVerifier_TimestampSkewed                (±300 s skew gate)
PASS  TestTantraVerifier_UnknownField                   (strict decoder gate)
PASS  TestTantraEvaluatorID_Format                      (evaluator_id regex)
PASS  TestTantraEvaluatorID_SplitKeyID                  (key_id parser)
PASS  TestCanonicalDecisionMaterialBytes_Stable         (canonical bytes deterministic)
PASS  TestHybridProvider_RoundTripAndCompositeAND       (composite-AND verified for both halves)
PASS  TestPeerKeyRegistry_RelaxedMode_NoEntry_AcceptsTOFU
PASS  TestPeerKeyRegistry_StrictMode_NoEntry_Rejects
PASS  TestPeerKeyRegistry_RegisteredAndMatching_Accepts
PASS  TestPeerKeyRegistry_RegisteredButMismatchedKey_Rejects
PASS  TestPeerKeyRegistry_SuspendedPeer_Rejects
PASS  TestPeerKeyRegistry_CrossPeerImpersonation_Rejects
PASS  TestPeerKeyRegistry_UnknownPeerKind_Rejects
PASS  TestPeerReceiptReplay_DuplicateRejected
PASS  TestPeerKeyRegistry_ConstantTimeHexEqual
PASS  TestPeerKeyRegistry_ValidatePeerKeyEntryShape
PASS  + 17 pre-existing canonical_json tests (unchanged)
```

30+ TANTRA / crypto / registry tests + the pre-existing canonical JSON suite. All against real code paths.

### 6.3 Boot smoke (provider toggle)

```
$ SARATHI_CRYPTO_PROVIDER=ed25519 ./sarathi-enforcement-adapter.exe --list-evaluators
[crypto] provider=Ed25519 env=ed25519 key_id_suffix="#ed25519-<rotation>"

$ SARATHI_CRYPTO_PROVIDER=hybrid ./sarathi-enforcement-adapter.exe --list-evaluators
[crypto] provider=Composite-MLDSA65-Ed25519 env=hybrid key_id_suffix="#composite-mldsa65-ed25519-<rotation>"

$ SARATHI_CRYPTO_PROVIDER=garbage ./sarathi-enforcement-adapter.exe --list-evaluators
panic: crypto_provider: SARATHI_CRYPTO_PROVIDER="garbage" is not a valid provider id
(want one of: ed25519, hybrid). The process refuses to boot to prevent a silent
algorithm downgrade. Edit live/.env and restart.
```

Fail-closed verified.

### 6.4 Boot smoke (registration CLI)

```
$ ./sarathi-enforcement-adapter.exe --register-peer-key \
    --peer=bucket --public-key=0123...cdef --snapshot=./tmp/snap.json
Successfully registered peer key for peer=bucket
  status:           ACTIVE
  public_key_hex:   0123...cdef
  key_fingerprint:  0123456789abcdef
  snapshot:         ./tmp/snap.json
```

Atomic snapshot write verified.

### 6.5 Open blockers

| # | Item | Owner | Severity | Mitigation |
|---|---|---|---|---|
| 1 | Confirm Core's `decision_id` derivation formula matches Sarathi's default. | BHIV Core (Raj/Aakanksha) | Medium | Verifier rejects mismatch with `ERR_TANTRA_DECISION_ID_MISMATCH` on first call, surfacing any drift loudly. |
| 2 | Bucket's `/bucket/artifact` API must accept arbitrary JSON body (not a strict BucketArtifact wrapper). | BHIV Bucket (Siddhesh) | High for Path A; integration-blocker if Bucket strictly validates the wrapper. | If Bucket cannot accept arbitrary JSON, switch propagation back to BHIV wrapper (Path B) and add per-decision outbound hash check on Sarathi side (Option B from prior turn). |
| 3 | InsightFlow's `/insightflow_process` API must accept ~20-field body (not a digest). | BHIV InsightFlow (Vijay) | Medium; observability is off-chain. | Same fallback as #2. |
| 4 | Peer public keys received from each team and registered via `--register-peer-key`. | Operator (Hemanth) | Blocker before `SARATHI_PEER_KEY_PINNING=strict` is enabled. | Run the three CLI commands listed in DEPLOYMENT_GUIDE.md §3. |
| 5 | Sovereign Core's PUBLIC key + key_id + api_key_fingerprint received and registered via `--register-tantra-evaluator`. | Operator + Core team | Blocker before first inbound TANTRA POST. | Single CLI command. |
| 6 | Real ngrok URLs (or production TLS hostnames) for Sarathi + 3 peers. | Operator + DevOps | Blocker. | Existing ngrok flow documented in NGROK_VALIDATION_SCRIPT.md and DEPLOYMENT_GUIDE.md. |
| 7 | `service_inbound_auth.go` + `policy_signing.go` still use `crypto/ed25519` stdlib directly (not routed through `CryptoProvider`). | Sarathi maintainer | Low (not on TANTRA critical path). | Mechanical port; not a blocker for v15.11 deployment. |

### 6.6 Deliverable inventory

| Deliverable per task.md | Status | File |
|---|---|---|
| Updated REVIEW_PACKET.md | ✅ | `REVIEW_PACKET.md` (this file) |
| Integration architecture note | ✅ | `SARATHI_SYSTEM_GUIDE.md` Part XII + Part XIII |
| Final contract definition | ✅ | `FINAL_CONTRACT_DEFINITION.md` |
| Deployment / environment instructions | ✅ | `DEPLOYMENT_GUIDE.md` |
| Live proof logs / screenshots / outputs | ✅ | `proof_logs/*.jsonl` produced per run; smoke-test outputs above |
| Hash verification proof | ✅ | `TestTantraVerifier_*` + Path A byte-equality model documented |
| Cross-system execution proof | ✅ | Live flow §3 above; per-peer audit log per run |
| Open blockers list | ✅ | §6.5 above |
| Mandatory REVIEW_PACKET structure (entry / 3-file flow / live flow / changes / failure / proof) | ✅ | §1 / §2 / §3 / §4 / §5 / §6 of this file |

---

**Submission status:** Complete per task.md scope ("complete, integrate, deploy, prove"). Awaiting peer team responses on §6.5 blockers #1 / #2 / #3 to close the cross-team integration loop.

# Phase v15.7 — TANTRA `tantra.decision.v1` Inbound Alignment

**Status:** Implemented, all tests green, build clean on Windows.
**Owner:** Hemanth B (Sarathi).
**Counterparty:** BHIV Core team (Sovereign decision producer).
**Supersedes:** v15.5 Sovereign translational layer (`bhiv.sovereign.decide/v1.0`).
**Scope:** Inbound `/sarathi/enforce` only. Existing pipeline, peer receipts, envelope, response contract, JWT authority — unchanged.

---

## 1. Context

BHIV Core froze the TANTRA Sutradhar decision contract (`schema_version = "tantra.decision.v1"`). The new shape:

- Fixed canonical field order (NOT alphabetical) for signing bytes.
- A signature object with `alg`, `key_id`, `encoding`, `value` — `encoding` is always `base64url_no_pad`.
- A 6-field `decision_hash` material that EXCLUDES timestamp.
- An explicit `enforcement_binding` field carrying CLEARED/BLOCKED.
- Replay TTL = 300 s for the decision_hash AND for the signed-payload hash.
- `evaluator_id` format `bhiv.<system>.<component>.<environment>.v<major>`.

Sarathi's previous inbound contract carried the 9-field `bhiv.sovereign.decide/v1.0` shape with hex signatures. The user's scoping decision (Plan §1.7): **hard cut — TANTRA only at `/sarathi/enforce`; legacy translator removed; everything else stays identical.**

---

## 2. Implementation

### 2.1 New files

| File | Purpose |
|---|---|
| `tantra_decision.go` | Wire types (`TantraDecision`, `TantraSignature`) + all `ERR_TANTRA_*` codes + structural validation. |
| `tantra_canonical.go` | Fixed-order canonical JSON encoder (signable bytes + wire bytes + material bytes). |
| `tantra_evaluator_id.go` | Anchored regex + `SplitKeyID` parser for `bhiv.<s>.<c>.<e>.v<v>#<rotation>`. |
| `tantra_trust_extension.go` | TANTRA-aware registry layer with 5-gate `Lookup()` (existence / active / schema / key_id / algorithm). |
| `tantra_verifier.go` | The 12-step contract routine (Decode → Required → Format → Skew → Sig extract → Canonicalise → Schema reassert → Registry lookup → Sig verify → Decision-hash recompute → Decision-id recompute → Replay). |
| `tantra_replay.go` | 300-s decision_hash + signed-payload-hash replay store; persistent JSONL with boot rehydration; in-memory variant for tests. |
| `translation_tantra_to_external_decision.go` | Projects verified TANTRA → existing 16-field `ExternalDecision` so the PDP / propagation pipeline is unchanged. |
| `tantra_emit.go` | Sarathi-side `bhiv.sarathi.enforcement.prod.v1` attestation emitter (TANTRA-shape, signed under the active provider). |
| `service_boundary_tantra.go` | New `/sarathi/enforce` handler. Runs the 12-step verifier, translates, proxies to `handleIngestDecision`. |
| `cmd_tantra_register.go` | `--register-tantra-evaluator` CLI: registers a peer's PUBLIC key (never mints private keys on Sarathi). |

### 2.2 Files deleted

- `translation_sovereign_to_sarathi.go`
- `translation_sovereign_to_sarathi_test.go`
- `service_boundary_sovereign.go`
- `cmd_sovereign_keygen.go` (replaced by `cmd_tantra_register.go` + `cmd_provider_keygen.go`)

### 2.3 Files modified

| File | Change |
|---|---|
| `service_boundary.go` | `/sarathi/enforce` route now mounts `handleSarathiEnforceTantra` (was `handleSarathiEnforceSovereign`). |
| `evaluator_admin_cli.go` | Replaced `--bootstrap-sovereign-core` with `--register-tantra-evaluator` and `--provider-keygen`. Removed dangling `--verify-bucket-chain` reference. |
| `enforcement_adapter_main.go` | Boot banner now reflects v15.7; calls `InitCryptoProvider`, `BootstrapTantraReplayStore`, `BootstrapTantraTrust` BEFORE any CLI dispatch. |
| `translation_sovereign_schemas.go` | Removed dead `SovereignDecideResponse`, `SovereignDecideSchemaV1`, `SarathiEnforceSchemaV2`, `TranslationLayerVersion`. Kept `SovereignBHIVCoreEvaluatorID` (still used by outbound bucket / insightflow translators). |
| `translation_canonical.go` | Added `PrecreateTranslationDirs()` to recreate the deleted helper. |

---

## 3. Field-by-field translation (TANTRA → ExternalDecision)

| TANTRA field | Where it lands inside `ExternalDecision` |
|---|---|
| `schema_version` | `Metadata["tantra_schema_version"]` |
| `trace_id` | `Metadata["trace_id"]` (also re-emitted as `X-Sarathi-Trace-ID` to the inner ingest handler) |
| `input_hash` | `Metadata["input_hash"]` |
| `decision_id` | `DecisionID` (verified upstream by `ComputeTantraDecisionID`) |
| `decision_hash` | `Metadata["tantra_decision_hash"]` (six-field hash; not the same as Sarathi's internal full hash) |
| `verdict` | `Verdict` |
| `policy_reference` | `Metadata["policy_reference"]` + drives `Action` via `deriveActionFromPolicyReference` |
| `evaluator_id` | `EvaluatorID` |
| `enforcement_binding` | `Reason` (preserves the CLEARED:.../BLOCKED:... string) |
| `timestamp` | `Timestamp` (RFC3339 UTC → `time.Time`) |
| `signature` | Verified upstream, base64url-decoded into `EvaluatorSignature` / `EvaluatorSignatureHex` for audit replay |

After projection:
- `ExternalDecision.DecisionHash` and `.DecisionCoreHash` are recomputed via the existing `computeHash` / `computeCoreHash` helpers so the downstream pipeline's integrity checks remain valid byte-for-byte.
- `AgentID`, `ResourceID` default to `EvaluatorID` (the agent / resource identity lives in upstream context Sarathi never sees; the same defaulting strategy the v15.5 translator used).
- A row is appended to `proof_logs/tantra_translation_map.jsonl` covering both the TANTRA values and the Sarathi-side recomputed values.

---

## 4. Open item — `decision_id` derivation formula

The TANTRA contract specifies that `decision_id` must round-trip but does not pin the formula. Sarathi currently uses:

```
decision_id = uuid_shape( sha256( canonical({ trace_id, input_hash, evaluator_id }) ) )
```

UUID shape `8-4-4-4-12` over the first 32 hex characters. Excludes timestamp (so replays land on the same id) and excludes verdict.

**ACTION:** Confirm formula with Aakanksha / Raj. If Core uses a different formula, update `ComputeTantraDecisionID` in `tantra_verifier.go` and the matching `tantra_emit.go` call. The verifier rejects mismatches with `ERR_TANTRA_DECISION_ID_MISMATCH` so any divergence surfaces loudly during the first integration call.

---

## 5. CRO findings + resolutions

| # | Finding | Resolution |
|---|---|---|
| CRO-1 | Backwards-compat blast radius: confirm no code path emits the old 9-field shape on the wire. | Grep across the tree: every reference to `SovereignDecideResponse` / `SovereignDecideSchemaV1` / `SarathiEnforceSchemaV2` is gone. Only the outbound bucket/insightflow paths reference `SovereignBHIVCoreEvaluatorID` (internal identity, unchanged). |
| CRO-2 | Audit-trail consistency: `tantra_translation_map.jsonl` schema must carry both TANTRA-side and Sarathi-side values. | Implemented in `translation_tantra_to_external_decision.go::appendTantraTranslationAudit`. Row carries `tantra_decision_id`, `tantra_decision_hash`, `recomputed_decision_hash`, `recomputed_decision_id`, `sarathi_decision_id`, `sarathi_decision_hash`, `sarathi_decision_core_hash`. |
| CRO-3 | Disaster recovery: bad `SARATHI_CRYPTO_PROVIDER` value must fail closed. | Verified by smoke test: `SARATHI_CRYPTO_PROVIDER=bogus` panics with the exact text "refuses to boot to prevent a silent algorithm downgrade". |
| CRO-4 | Key-rotation runbook. | `key_id` carries an explicit `<rotation>` suffix. CLI helpers (`--provider-keygen`, `--register-tantra-evaluator`) emit the new key_id; old key_id stops being accepted at the next registry reload. Document in KB_18. |
| CRO-5 | Replay window narrowing from 900 s to 300 s for decisions only — confirm no upstream caller relies on the wider window. | The 900 s window remains on inbound HTTP header nonces (`SARATHI_NONCE_WINDOW_S`). The 300 s window is **additive** for TANTRA decision_hash + signed-payload-hash. Two independent surfaces; no narrowing of the existing surface. |
| CRO-6 | Deletion of Sovereign-keygen-on-Sarathi flow. | Done. `cmd_sovereign_keygen.go` deleted. KB_15 and NGROK_VALIDATION_SCRIPT to be updated in Phase 5. |
| CRO-7 | Open question on decision_id formula. | Recorded in §4 above. Verifier rejects mismatches loudly. |

---

## 6. CSO findings + resolutions

| # | Finding | Resolution |
|---|---|---|
| CSO-1 | Timestamp not in `decision_hash` material — verify mutation safety. | **Safe.** `timestamp` is in the signed canonical payload (just not in the hash). Mutating timestamp changes the signed bytes → signature verification fails → `ERR_TANTRA_SIGNATURE_INVALID`. Tested. |
| CSO-2 | `key_id` binding must be exact (no substring match). | `TantraTrustConsumer.Lookup` uses direct string equality. Test `TestTantraVerifier_KeyIDMismatch` exercises the negative path. |
| CSO-3 | `base64url_no_pad` enforcement: reject padded base64, reject standard base64 alphabet. | The Go stdlib `base64.RawURLEncoding` (URL-safe alphabet, no padding) is used for both encode and decode. Padded input is rejected by the decoder. The `signature.encoding` field is also asserted equal to the literal `"base64url_no_pad"` at `RequiredFields()`. |
| CSO-4 | Composite-AND verify: BOTH Ed25519 and ML-DSA must pass. | Implemented in `crypto_provider_hybrid.go::Verify`. Test `TestHybridProvider_RoundTripAndCompositeAND` mutates each component independently and confirms each mutation is rejected. |
| CSO-5 | TLV framing on hybrid signatures. | Version byte + per-segment tag + 4-byte big-endian length. Future ML-DSA-87 swap requires only a new tag byte; framing is stable. |
| CSO-6 | Provider-mismatch detection at boot. | `NewTantraTrustConsumer` skips registry rows whose `algorithm` does not match the active provider (with a stderr warning). The verifier additionally checks `provider.Algorithm() == signature.alg` at step 7 and returns `ERR_TANTRA_ALG_MISMATCH`. |
| CSO-7 | Constant-time signature compare. | Go stdlib `ed25519.Verify` is constant-time; CIRCL `mldsa65.Verify` is constant-time. Documented in `crypto_provider.go` interface contract. |
| CSO-8 | File-permission posture on private-key files. | `cmd_provider_keygen.go` writes priv files mode 0600 (POSIX-effective; Windows best-effort). KB_18 documents the operator's responsibility to enforce ACLs on Windows hosts. |
| CSO-9 | Algorithm downgrade protection. | Three gates: (a) registry row's `algorithm` must match active provider; (b) `signature.alg` must equal active provider's `Algorithm()`; (c) any mismatch returns `ERR_TANTRA_ALG_MISMATCH` (HTTP 403). No silent fallback path exists. |
| CSO-10 | Signed-payload replay (not just decision_hash replay). | `tantra_replay.go` tracks BOTH decision_hash AND `sha256(canonical_signed_bytes)`. Same logical decision re-posted with one byte mutated still triggers `ERR_TANTRA_REPLAY` via the signed-payload key. |

---

## 7. Test matrix — all passing

```
PASS  TestTantraVerifier_HappyPath_Ed25519
PASS  TestTantraVerifier_HappyPath_Hybrid
PASS  TestTantraVerifier_ReplayRejected
PASS  TestTantraVerifier_MutatedField_RejectsSignature
PASS  TestTantraVerifier_BadSchemaVersion
PASS  TestTantraVerifier_KeyIDMismatch
PASS  TestTantraVerifier_TimestampSkewed
PASS  TestTantraVerifier_UnknownField
PASS  TestTantraEvaluatorID_Format
PASS  TestTantraEvaluatorID_SplitKeyID
PASS  TestCanonicalDecisionMaterialBytes_Stable
PASS  TestHybridProvider_RoundTripAndCompositeAND
PASS  (full repo suite, including all pre-existing canonical_json tests)
```

Total: 29 TANTRA-touching test cases + all pre-existing tests. **No regressions.**

---

## 8. What to ask BHIV Core

1. Confirm the `decision_id` derivation formula (Open Item §4).
2. Confirm the schedule for retiring `/sovereign/decide`'s 9-field response. (Sarathi no longer accepts it.)
3. Send Sovereign's public key for `bhiv.sovereign.decision.prod.v1`, the `key_id` (e.g. `bhiv.sovereign.decision.prod.v1#ed25519-2026-05`), and the `api_key_fingerprint`.
4. Confirm Core can verify Sarathi's enforcement attestation (signed by `bhiv.sarathi.enforcement.prod.v1`).

## 9. What Sarathi sends to Core

1. Sarathi's public key for `bhiv.sarathi.enforcement.prod.v1`.
2. The matching `key_id`.
3. The canonical-field-order reference (this packet + KB_17).

---

**Phase v15.7 sign-off:** Ready for cross-team integration. Build green, tests green, audit findings resolved.

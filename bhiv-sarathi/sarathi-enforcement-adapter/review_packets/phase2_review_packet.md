# PHASE 2 REVIEW PACKET — BHIV TRUST BOUNDARY HARDENING (v11.0)

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Zero-Trust Verification + Enforcement Boundary
**Version:** 11.0
**Date:** 2026-04-07
**Review Time:** 15–20 minutes
**Classification:** Internal Sovereign Design / Strictly Confidential

---

## ENTRY POINT

**Function:** `EnforceExternalDecision(decision *ExternalDecision, modeCtrl *ModeController) *ExternalEnforcementResult`
**File:** `external_decision.go`
**Purpose:** Accepts an externally signed decision and runs a 10-stage verification pipeline before issuing a capability token. This is the ONLY entry point for external decisions into the Sarathi enforcement boundary.

**Critical constraint:** This function NEVER calls `PDP.Evaluate()`, `KSML.GovernIntent()`, or `GovernanceKernel.Decide()`. All decision interfaces are blocked by the centralized guard in EXTERNAL mode.

---

## CORE FLOW (3 files)

| File | Lines | Purpose | Key Functions |
|------|-------|---------|---------------|
| `external_decision.go` | ~1765 | Trust model, evaluator registry, signature system, verification pipeline, mode lock, centralized guard, enforcement entry point | `EnforceExternalDecision()`, `SignDecision()`, `VerifySignature()`, `CentralGuardCheck()`, `RegisterEvaluator()`, `RevokeEvaluator()`, `RotateKey()` |
| `external_decision_test_sim.go` | ~821 | 20 deterministic test cases with 55+ assertions, full proof logs | `RunExternalDecisionTests()`, `RunExternalDecisionDemo()` |
| `enforcement_adapter.go` | ~640 | Adapter struct with `evaluatorRegistry` field, existing `Enforce()` method unchanged | `Enforce()` (internal path, UNCHANGED), `externalReplayTracker`, `evaluatorRegistry` |

---

## LIVE FLOW (actual execution trace)

```
1. Evaluator (Ishan) creates ExternalDecision:
   decision = NewExternalDecision("ishan-evaluator-v2", "agent-alpha", "project-data", "execute", ALLOW, ...)

2. Evaluator signs with Ed25519 private key:
   decision.SignDecision(ishanPrivateKey)
   → DecisionCoreHash computed: SHA256(decision_id + evaluator_id + agent_id + resource_id + action + verdict + timestamp + nonce)
   → EvaluatorSignature = Ed25519.Sign(privateKey, DecisionCoreHash)

3. Sarathi receives decision and runs 10-stage verification pipeline:
   STEP 1:  MODE CHECK           → EXTERNAL confirmed (lock=IMMUTABLE)
   STEP 2:  STRUCTURE CHECK      → All fields present, action valid, signature present
   STEP 3:  EVALUATOR TRUST      → "ishan-evaluator-v2" found in registry, status=ACTIVE
   STEP 4:  SIGNATURE CHECK      → Ed25519.Verify(publicKey, coreHash, signature) = TRUE
   STEP 5:  INTEGRITY CHECK      → DecisionHash matches recomputed hash
   STEP 6:  EXPIRY CHECK         → Decision within TTL (30s remaining)
   STEP 7:  REPLAY CHECK         → Nonce not seen before → recorded
   STEP 8:  RATE LIMIT CHECK     → Agent within limits
   STEP 9:  POSTURE CHECK        → Agent posture OK (BeyondCorp)
   STEP 10: BINDING CHECK        → DecisionCoreHash matches recomputed binding hash

   → VerificationTrace: 10/10 stages PASSED, FinalVerdict = "VERIFIED"

4. Token issued (Ed25519 signed by TokenAuthority):
   token.policyHash = decision.DecisionCoreHash  (binding: token → decision)
   token.decisionID = decision.DecisionID
   TokenAuthority.SignToken(token)

5. Execution Engine receives token:
   engine.ExecuteWithToken(token) → 9-check validation gate → EXECUTION_PERMITTED

6. Audit chain updated:
   enforcement_hash recorded in append-only chain
   VerificationTrace persisted for audit
```

---

## WHAT WAS BUILT

### Trust Model (Phase 1)
Explicit separation between EXECUTION VALIDITY (Sarathi's domain) and DECISION CORRECTNESS (evaluator's domain). Sarathi verifies structure, authenticity, integrity, temporality, and binding. It NEVER evaluates policy logic, interprets context, or introduces trust scoring.

### Evaluator Trust Registry (Phase 2)
Production-grade registry of trusted evaluators with lifecycle management. Each evaluator has an Ed25519 public key registered at trust time. Lifecycle: REGISTERED -> ACTIVE -> SUSPENDED -> REVOKED. Key rotation with configurable grace periods. Append-only audit log of all registry events.

### Decision Signature System (Phase 3)
Every ExternalDecision carries an Ed25519 signature from the evaluator. The signature covers the `DecisionCoreHash` (SHA-256 over all binding fields). Sarathi verifies the signature using the evaluator's registered public key. Without a valid signature from a trusted, ACTIVE evaluator, the decision is REJECTED.

### Strict Verification Pipeline (Phase 4)
Fixed 10-stage pipeline that cannot be reordered or skipped. If any stage fails, the pipeline halts immediately. Every stage produces a `VerificationResult` recorded in the `VerificationTrace` for audit.

### Decision-Request Binding (Phase 5)
`DecisionCoreHash = SHA256(decision_id + evaluator_id + agent_id + resource_id + action + verdict + timestamp + nonce)`. This hash is: (a) signed by the evaluator, (b) verified by Sarathi, (c) bound to the issued token. If the request drifts from the decision, enforcement fails.

### Mode Lock + Centralized Guard (Phase 6)
Three lock levels: NONE (testing), PRIVILEGED (staging), IMMUTABLE (production). `NewProductionModeController()` creates EXTERNAL-locked, IMMUTABLE controller. `CentralGuardCheck()` is a single enforcement gate that blocks ALL decision interfaces (PDP/KSML/GovernanceKernel) in EXTERNAL mode. The legacy per-function guards delegate to this central interceptor.

---

## FAILURE CASES

### Invalid Signature (TEST 15)
Decision claims evaluator_id="ishan-evaluator-v1" but signed with a rogue private key. Pipeline halts at STEP 4 (SIGNATURE_VERIFICATION). Error: `SIGNATURE_INVALID: no matching key found`. Decision DENIED.

### Unknown Evaluator (TEST 12)
Decision from evaluator_id="rogue-evaluator-999" not in trust registry. Pipeline halts at STEP 3 (EVALUATOR_TRUST_CHECK). Error: `EVALUATOR_NOT_FOUND: not registered`. Decision DENIED.

### Revoked Evaluator (TEST 13)
Evaluator "revoked-eval-001" was permanently revoked (SECURITY_INCIDENT). Pipeline halts at STEP 3. Error: `EVALUATOR_REVOKED: revoked at <timestamp>`. Decision DENIED. Revocation is IRREVERSIBLE.

### Suspended Evaluator (TEST 14)
Evaluator "suspended-eval-001" temporarily suspended. Pipeline halts at STEP 3. Error: `EVALUATOR_SUSPENDED`. After reactivation, new decision from same evaluator is accepted.

### Unsigned Decision (TEST 11)
Decision created without calling `SignDecision()`. Pipeline halts at STEP 2 (STRUCTURE_CHECK). Error: `STRUCTURE_INVALID: missing evaluator_signature`. Decision DENIED.

### Replay Attack (TEST 3)
Same decision submitted twice (same nonce). First attempt succeeds. Second halts at STEP 7 (REPLAY_CHECK). Error: `REPLAY_DETECTED: nonce already seen`. Decision DENIED.

### Expired Decision (TEST 6)
Decision backdated 10 seconds (past TTL 1s + ClockSkewTolerance 5s). Pipeline halts at STEP 6 (EXPIRY_CHECK). Error: `DECISION_EXPIRED`. Decision DENIED.

### Mode Lock Bypass (TEST 17)
Attacker attempts `SetMode(INTERNAL)` on IMMUTABLE production controller. SetMode returns error: `MODE_LOCKED_IMMUTABLE`. Mode remains EXTERNAL. Violation recorded in guard violations.

### Tampered Core Hash (TEST 16)
Decision signed correctly, then DecisionCoreHash manually tampered. Pipeline halts at STEP 4 (SIGNATURE_VERIFICATION) because the signature was over the original core hash, not the tampered value.

### Wrong Mode (TEST 10)
`EnforceExternalDecision()` called with INTERNAL mode controller. Pipeline halts at STEP 1 (MODE_CHECK). Error: `MODE_NOT_EXTERNAL`. Decision DENIED.

---

## PROOF

### Test Results
- 20 test cases, 55+ assertions
- ALL TESTS PASSED
- Proof logs generated for every failure mode

### No-PDP Logs in EXTERNAL Mode
- `EnforceExternalDecision()` has zero calls to `ea.pdp.Evaluate()`
- `CentralGuardCheck(PDP, ...)` returns error in EXTERNAL mode (TEST 5)
- `CentralGuardCheck(KSML, ...)` returns error in EXTERNAL mode (TEST 5)
- `CentralGuardCheck(GovernanceKernel, ...)` returns error in EXTERNAL mode (TEST 5)

### Audit Chain Entries
- Every enforcement (success or failure) appended to hash chain
- Chain integrity verified after external enforcements (TEST 8)
- `VerificationTrace` recorded for every pipeline run

### Evaluator Trust Proof
- Only ACTIVE evaluators accepted (TEST 12, 13, 14)
- Signature must match registered public key (TEST 15)
- Key rotation with grace period works (TEST 19)

### Decision-Request Binding Proof
- DecisionCoreHash computed deterministically (TEST 20)
- Token carries DecisionCoreHash as policyHash (TEST 20)
- Tampered binding detected and rejected (TEST 16)

---

## INTEGRATION BLOCK

| Person | Role | Interface |
|--------|------|-----------|
| Ishan Shirode | Evaluator System | Provides Ed25519-signed `ExternalDecision` via `NewExternalDecision()` + `SignDecision()` |
| Hemanth B | Governance Engineer | Built verification + enforcement boundary (this system) |
| Raj Prajapati | Execution Engine | Consumes `CapabilityToken` via `ExecuteWithToken()` — unchanged |
| Nilesh | Backend Integration | API wiring: evaluator HTTP endpoint → `ExternalDecision` → `EnforceExternalDecision()` |
| Sankalp | Intelligence Layer | MUST NOT influence Sarathi logic — Sarathi is verification-only |
| Chandragupta | Frontend | Optional visualization of `VerificationTrace` and enforcement logs |

---

## INDUSTRY STANDARDS COMPLIANCE

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| RFC 8032 (Ed25519) | Digital signatures for authentication | `SignDecision()`, `VerifySignature()`, `VerifySignatureWithRotation()` |
| NIST 800-207 | Zero Trust per-request verification | 10-stage pipeline, no implicit trust, continuous posture monitoring |
| Google Zanzibar | Capability-based access with external auth | `EvaluatorTrustRegistry`, `CapabilityToken` with binding |
| SPIFFE/SPIRE | Workload identity with key rotation | `RotateKey()` with grace period, `EvaluatorKeyVersion` |
| XACML | PDP/PEP separation | Sarathi = PEP only in EXTERNAL mode, PDP blocked by centralized guard |
| BeyondCorp | Continuous agent posture assessment | `AgentPostureMonitor` integrated in pipeline STEP 9 |
| NIST SP 800-63 | Replay protection | Nonce tracking with TTL-based cleanup |

---

## ISSUES RESOLVED (v10.0 → v11.0)

| Issue | Title | Root Cause | Fix |
|-------|-------|------------|-----|
| 1 | Validation vs enforcement confusion | No explicit naming separation | `ValidateStructure()`, `VerificationStage`, `VerificationTrace`, documented boundaries |
| 2 | Decision trust boundary weak | No evaluator authentication | `EvaluatorTrustRegistry` + Ed25519 `SignDecision()`/`VerifySignature()` |
| 3 | Mode control too flexible | Anyone can call `SetMode()` | `ModeLockLevel` (NONE/PRIVILEGED/IMMUTABLE), `NewProductionModeController()` |
| 4 | Synthetic request underdefined | Token can drift from decision | `DecisionCoreHash = SHA256(binding_fields)`, token carries this hash |
| 5 | Guard needs non-bypass proof | Scattered per-function guards | `CentralGuardCheck()` — single gate, `DecisionInterface` enum |
| 6 | Token implicitly trusts decision | No evaluator auth before token | 10-stage pipeline: signature + trust verified BEFORE token issued |

---

## FILE INVENTORY

| File | Lines | Modified | Purpose |
|------|-------|----------|---------|
| `external_decision.go` | ~1765 | REWRITTEN | Trust model, evaluator registry, signature system, verification pipeline, mode lock, centralized guard |
| `external_decision_test_sim.go` | ~821 | REWRITTEN | 20 deterministic test cases, 55+ assertions, proof logs |
| `enforcement_adapter.go` | ~640 | +2 lines | Added `evaluatorRegistry *EvaluatorTrustRegistry` field |
| `enforcement_adapter_main.go` | ~2460 | +8 lines | Updated Phase 10 header text for v11.0 |
| `REVIEW_PACKET.md` | ~950 | UPDATED | v11.0 sections added |

---

## TESTING NOTE

This task is runnable in under 10 minutes:
1. Clone repo
2. `go build ./...` — verify compilation
3. `go run .` — runs all tests including 20 hardened external decision tests
4. Look for "EXTERNAL DECISION TRUST BOUNDARY TEST SUMMARY" in output
5. Verify: "ALL TESTS PASSED — TRUST BOUNDARY VERIFIED"

---

## HANDOVER READINESS

- Zero ambiguity naming: `ValidateStructure`, `VerifySignature`, `CentralGuardCheck`, `EvaluatorTrustRegistry`
- No hidden assumptions: every field documented, every function has doc comments
- Clear comments explaining WHY (not just what)
- Verification trace provides full audit trail of every pipeline run
- A zero-context developer can read `external_decision.go` top-to-bottom and understand the entire trust boundary

---

## BENCHMARK

**Before v11.0:** Sarathi enforced external decisions but any system that could construct an `ExternalDecision` struct could inject ALLOW. Mode could be switched freely. Guards were scattered per-function.

**After v11.0:** Sarathi is a cryptographic enforcement boundary. ONLY decisions signed by Ed25519 keys of trusted, ACTIVE evaluators pass the 10-stage verification pipeline. Mode is IMMUTABLE in production. ALL decision interfaces blocked by single centralized guard. Decision-request binding prevents token drift. Every step auditable via `VerificationTrace`.

**v11.0.1 Deep Audit Fixes (3 gaps):**

| Gap | Issue | Fix |
|-----|-------|-----|
| GAP-1 | `DecisionHash` == `DecisionCoreHash` (identical payloads) | `externalDecisionHashPayload` now includes obligations, reason, TTL, metadata_hash — full integrity vs binding-only |
| GAP-2 | Data race: `VerifySignatureWithRotation()` wrote `LastActiveAt` under RLock | Changed to `Lock()` — write operations require exclusive lock |
| GAP-3 | Nonce recorded at Step 7, before rate/posture checks — retry blocked as replay | Nonce commit deferred to after Step 9 (posture), before Step 10 (binding) |

All 3 fixes are backward-compatible. No existing tests broken. The gaps were identified through manual code review (not test failure), which is why they were not caught in the initial v11.0 build.

**Sarathi trusts ONLY proof, not logic.**

---

# PHASE 12 — EXTERNAL EVALUATOR HARDENING

**Author:** Hemanth B  •  **Scope:** Operational surface around the existing v11 evaluator registry  •  **Invariant:** ZERO changes to the 10-stage verification pipeline.

## PURPOSE

Phase 11 shipped the cryptographic core (10-stage verification, Ed25519 signatures, mode lock, central guard). Phase 12 closes the **operational gaps** around it so the system can actually be run in production:

- Persistence across restarts (no more map-in-RAM trust)
- External registration path (HTTP API + config-file bootstrap + manual CLI)
- Proof-of-possession on every key binding (ACME RFC 8555-style)
- Admin authentication, replay protection, nonce binding, rate limiting on every lifecycle op
- Tamper-evident append-only audit chain for every registry mutation
- RFC 7517 JWKS trust bundle discovery
- Key expiry (NIST SP 800-57 crypto period)
- Zanzibar-style registry consistency version stamped on every response

## DESIGN PRINCIPLE

**Additive-only.** No line in the Phase 11 verification pipeline changed. `EnforceExternalDecision`, `ExternalDecision`, and the 10-stage order are frozen. Every existing test — including [external_decision_test_sim.go](../external_decision_test_sim.go) — still compiles and passes without edit. New behaviour is opt-in via `SARATHI_EVALUATOR_REGISTRY_CONFIG` env var; absent ⇒ legacy in-memory path.

## ENTRY POINT

1. **Boot** — [enforcement_adapter_main.go](../enforcement_adapter_main.go) calls `BootstrapEvaluatorRegistry(ctx, adapter, db)` after `InitExternalMode`.
2. **Config gate** — absent `SARATHI_EVALUATOR_REGISTRY_CONFIG` ⇒ no-op, legacy path.
3. **Store build** — [evaluator_registry_config.go](../evaluator_registry_config.go) `BuildStore()` constructs memory / file / postgres backend.
4. **Hydrate** — `registry.HydrateFromStore(ctx)` replays records + event chain, verifies chain hash integrity; fatal on tamper.
5. **Bootstrap entries** — `ApplyBootstrapEntries()` idempotent pre-seed with fingerprint validation; fingerprint mismatch ⇒ fatal.
6. **Admin keys** — `SecureConfig.EvaluatorAdminKeys` loaded from `SARATHI_EVAL_ADMIN_KEY_<NAME>` env vars; `ValidateForProduction()` requires ≥1 non-default admin key.
7. **Routes registered** — [service_boundary.go](../service_boundary.go) mounts Phase 12 API on the same mux, conditional on `registry.adminAuth != nil`.

## CORE FLOW — REGISTRATION (ACME-STYLE POP)

```
                            ┌─────────────────────────────┐
                            │  Evaluator operator + admin │
                            └──────────────┬──────────────┘
                                           │
                     1. POST /v1/evaluators/register/challenge
                        envelope = { admin: AdminRequest, payload: {id, name, pub_hex, meta} }
                                           │
                                           ▼
                    ┌──────────────────────────────────────┐
                    │ EvaluatorAdminAuthenticator          │
                    │   admin known → rate-limit → sig OK  │
                    │   → ts skew → op=REGISTER_INIT       │
                    │   → body hash → nonce unseen         │
                    │   → Ed25519.Verify                   │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ evaluatorChallengeStore.Issue()      │
                    │   challenge_id = uuid                │
                    │   message = sha256("BHIV-PoP|v1|"+…) │
                    │   TTL = 5 min   single-use           │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                      returns { challenge_id, message, expires_at }

          ────────────────── evaluator signs ───────────────────
                  sig = Ed25519.Sign(priv_evaluator, message)

                     2. POST /v1/evaluators/register/complete
                        envelope = { admin: AdminRequest(op=REGISTER_COMPLETE), payload: {challenge_id, sig} }
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ RegisterEvaluatorWithPoP(ctx, cid,   │
                    │                          sig, init)  │
                    │   1. Consume(cid, sig)   — PoP check │
                    │   2. fingerprint = SHA256(pub)[:16]  │
                    │   3. idempotent: same fp ⇒ return    │
                    │   4. RegisterEvaluator (existing v11)│
                    │   5. store.PutRecord  (fail-closed)  │
                    │   6. chain_hash = SHA256(prev || ev) │
                    │   7. store.AppendEvent               │
                    │   8. bumpVersion                     │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                    201 Created { evaluator_id, status, fingerprint }
                    X-Sarathi-Registry-Version: <n>
```

**Rejected at step 1.b:** `POP_FAILED`, `CHALLENGE_EXPIRED`, `CHALLENGE_ALREADY_CONSUMED`, `CHALLENGE_PUBKEY_MISMATCH`.

## CORE FLOW — LIFECYCLE (SUSPEND / REACTIVATE / REVOKE / ROTATE)

Every mutation follows the exact same 8-step fail-closed ritual:

```
request ─► parse admin envelope ─► RequireAdminAuth(op, target, body)
           │
           └─ unknown admin → 401 ADMIN_UNKNOWN
           └─ rate limited  → 429 ADMIN_RATE_LIMITED
           └─ bad sig       → 401 ADMIN_SIG_INVALID
           └─ skew          → 401 ADMIN_TIMESTAMP_SKEW
           └─ op mismatch   → 403 ADMIN_OP_MISMATCH
           └─ nonce seen    → 401 ADMIN_NONCE_REPLAY
           └─ body tamper   → 401 ADMIN_BODY_HASH_MISMATCH
           │ ok
           ▼
       r.mu.Lock()
       existing := cloneEvaluatorRecord(r.evaluators[id])   ── snapshot for rollback
       apply mutation on in-memory record (status / revokeReason / key rotation)
       ev := EvaluatorRegistryEvent{…}
       prevHash := r.prevEventHash
       ev.PrevEventID = last
       ev.ChainHash = computeEventChainHash(prevHash, ev)
       if err := store.PutRecord(ctx, rec); err != nil {
           ROLLBACK r.evaluators[id] = existing; return err        ── fail-closed
       }
       if err := store.AppendEvent(ctx, ev); err != nil {
           ROLLBACK r.evaluators[id] = existing; return err        ── fail-closed
       }
       r.prevEventHash = ev.ChainHash
       bumpVersion()
       r.mu.Unlock()
```

Never a partial update. Never a silent drop. Chain is linear + append-only, verified on hydrate.

## WHAT WAS BUILT

| File | Role |
|---|---|
| [evaluator_registry_store.go](../evaluator_registry_store.go) | `EvaluatorRegistryStore` interface; `InMemoryEvaluatorStore`, `FileEvaluatorStore` (atomic JSON w/ fsync+rename + chain_hash verify), `PostgresEvaluatorStore` (serializable txn). `ComputeKeyFingerprint()`, `computeEventChainHash()`. |
| [evaluator_admin_auth.go](../evaluator_admin_auth.go) | `AdminRequest` envelope, `Canonical()`, `EvaluatorAdminAuthenticator` with 9-check pipeline, token-bucket per-admin rate limit, 5-min skew window, nonce replay window. `SignAdminRequest()` CLI helper. |
| [evaluator_registration_challenge.go](../evaluator_registration_challenge.go) | PoP challenge store, single-use, 5-min TTL, domain-separated message `"BHIV-PoP|v1|<id>|<pubhex>|<nonce>|<exp>"`. |
| [evaluator_registry_extension.go](../evaluator_registry_extension.go) | Additive methods on `*EvaluatorTrustRegistry`: `SetStore`, `SetAdminAuth`, `SetClock`, `HydrateFromStore`, `RegisterEvaluatorWithPoP`, `SuspendEvaluatorAuthed`, `ReactivateEvaluatorAuthed`, `RevokeEvaluatorAuthed`, `RotateKeyAuthed`, `IsKeyExpired`, `TrustBundleJWKS`, `Version`. |
| [evaluator_registry_config.go](../evaluator_registry_config.go) | `EvaluatorRegistryConfig` loader + `Validate()` + `BuildStore()` + `LoadAdminKeysFromEnv()` + `ApplyBootstrapEntries()` + `BootstrapEvaluatorRegistry()` entry helper. |
| [evaluator_registration_api.go](../evaluator_registration_api.go) | HTTP handlers wired to the existing `ServiceBoundary` mux. Conditional: only registered when `registry.adminAuth != nil`. |
| [evaluator_registry_config.json](../evaluator_registry_config.json) | Sample config (postgres, require_durable_store, default_key_ttl_days, metadata_allow_list). |
| [evaluator_registry_test_sim.go](../evaluator_registry_test_sim.go) | 19-assertion deterministic proof suite. |

**Edits (additive only, no deletions):**

| File | Change |
|---|---|
| [external_decision.go](../external_decision.go) | Added fields: `KeyFingerprint`, `ExpiresAt *time.Time` on `EvaluatorRecord` (both `omitempty`); `store`, `adminAuth`, `challenges`, `clock`, `version`, `prevEventHash`, `metadataAllowList` on `EvaluatorTrustRegistry`. Key-expiry check added to `GetActiveEvaluator()` *after* the status check. |
| [enforcement_adapter_main.go](../enforcement_adapter_main.go) | One call: `BootstrapEvaluatorRegistry(ctx, adapter, nil)` after `InitExternalMode`. Wiring Phase 12 proof suite into the final harness total. |
| [service_boundary.go](../service_boundary.go) | Conditional mux wiring of 9 new routes. |
| [persistent_audit.go](../persistent_audit.go) | `EnsureEvaluatorSchema()` creates `evaluator_records` + `evaluator_registry_events` (append-only NIST AU-9 trigger). `DB()` accessor. |
| [governance_hardening.go](../governance_hardening.go) | `SecureConfig.EvaluatorAdminKeys` map, env scan, production guard check. |

## ENDPOINTS

| Method | Path | Auth | Operation |
|---|---|---|---|
| POST | `/v1/evaluators/register/challenge` | admin | `REGISTER_INIT` |
| POST | `/v1/evaluators/register/complete`  | admin | `REGISTER_COMPLETE` + PoP |
| GET  | `/v1/evaluators`                    | admin | `LIST` |
| GET  | `/v1/evaluators/{id}`               | admin | `GET` |
| POST | `/v1/evaluators/{id}/suspend`       | admin | `SUSPEND` |
| POST | `/v1/evaluators/{id}/reactivate`    | admin | `REACTIVATE` |
| POST | `/v1/evaluators/{id}/revoke`        | admin | `REVOKE` |
| POST | `/v1/evaluators/{id}/rotate`        | admin | `ROTATE_KEY` + PoP on new key |
| GET  | `/v1/evaluators/.well-known/jwks`   | **public** | RFC 7517 trust bundle |

Every mutating response carries `X-Sarathi-Registry-Version: <n>` (Zanzibar-style consistency token).

## GAP → FIX TRACEABILITY

| ID | Gap | Phase 12 fix |
|---|---|---|
| C1 | No persistence | `EvaluatorRegistryStore` + Postgres/File/Memory backends + `HydrateFromStore` |
| C2 | No external registration path | HTTP API + config-file bootstrap + admin CLI |
| C3 | No proof-of-possession | `evaluator_registration_challenge.go` + `RegisterEvaluatorWithPoP` |
| C4 | No admin auth on lifecycle | `EvaluatorAdminAuthenticator` + `*_Authed` wrappers |
| C5 | PDP/KSML must stay out | New code imports zero PDP/KSML symbols; CentralGuard invariant asserted by proof suite |
| H1 | No config/bootstrap | `evaluator_registry_config.json` + loader |
| H2 | No event persistence | `evaluator_registry_events` table + append-only chain hash |
| H3 | Admin replay | Nonce + timestamp + signature in every `AdminRequest` |
| H4 | No rate limit | Token-bucket per-admin with exponential failure drain |
| H5 | No consistency token | `registry.version` stamped in `X-Sarathi-Registry-Version` |
| H6 | Fail-closed audit | `*_Authed` wrappers roll back in-memory on persistence failure |
| M1 | No key expiry | `ExpiresAt` + `IsKeyExpired` in `GetActiveEvaluator` |
| M2 | No fingerprint | `KeyFingerprint` = `SHA256(pub)[:16]` |
| M3 | No idempotency | Fingerprint-based dedupe in `RegisterEvaluatorWithPoP` |
| M4 | Metadata schema | Config-driven allow-list |
| M5 | No JWKS discovery | `GET /v1/evaluators/.well-known/jwks` |

## FAILURE CASES (all DENY fail-closed)

| Code | Emitted at | Reason |
|---|---|---|
| `POP_FAILED` | `RegisterEvaluatorWithPoP` | Ed25519 verify of challenge signature failed |
| `CHALLENGE_EXPIRED` | `challengeStore.Consume` | > 5 min since issue |
| `CHALLENGE_ALREADY_CONSUMED` | `challengeStore.Consume` | Single-use challenge replayed |
| `CHALLENGE_PUBKEY_MISMATCH` | `challengeStore.Consume` | Claimed pubkey changed between issue + complete |
| `ADMIN_UNKNOWN` | `RequireAdminAuth` step 1 | admin_id not in SecureConfig.EvaluatorAdminKeys |
| `ADMIN_RATE_LIMITED` | step 2 | Token bucket empty |
| `ADMIN_SIG_INVALID` | step 3/9 | Signature missing or Ed25519 verify failed |
| `ADMIN_TIMESTAMP_SKEW` | step 4 | `|now - ts| > 5 min` |
| `ADMIN_OP_MISMATCH` | step 5 | Signed op ≠ URL op |
| `ADMIN_TARGET_MISMATCH` | step 6 | Signed target ≠ URL evaluator_id |
| `ADMIN_BODY_HASH_MISMATCH` | step 7 | SHA-256 of body ≠ signed body_hash |
| `ADMIN_NONCE_REPLAY` | step 8 | Nonce already consumed |
| `EVALUATOR_KEY_EXPIRED` | `GetActiveEvaluator` | Past `ExpiresAt` |
| `REGISTRY_CHAIN_TAMPERED` | `HydrateFromStore` | `computeEventChainHash(prev, ev)` ≠ stored chain_hash |
| `INVALID_STORE_TYPE` | `Config.Validate` | store_type ∉ {memory,file,postgres} |
| `STORE_PERSIST_FAILED` | any `*_Authed` wrapper | Backend rejected PutRecord/AppendEvent ⇒ rollback |
| `FINGERPRINT_MISMATCH` | `ApplyBootstrapEntries` | Someone swapped the key under an existing evaluator_id |

## PROOF — 19-assertion deterministic suite

Runs as part of the main harness (`RunEvaluatorRegistryPhase12Tests()` wired into [enforcement_adapter_main.go](../enforcement_adapter_main.go)):

```
==============================================================
 PHASE 12 — EVALUATOR REGISTRY HARDENING PROOF SUITE
==============================================================
  [PASS] pop_challenge_issue              — challenge_id=<id8> err=<nil>
  [PASS] pop_register_happy               — evaluator_id=ishan-evaluator-v1 fingerprint=<16hex>
  [PASS] pop_wrong_key_rejected           — err=POP_FAILED
  [PASS] pop_replay_rejected              — err=CHALLENGE_ALREADY_CONSUMED
  [PASS] store_hydrate_idempotent         — records=N
  [PASS] file_store_create                — path=evaluators.json
  [PASS] file_store_register_persists     — err=<nil>
  [PASS] file_store_hydrate_survives_restart — found=true
  [PASS] admin_auth_suspend_happy         — err=<nil>
  [PASS] admin_auth_body_tamper_rejected  — err=ADMIN_BODY_HASH_MISMATCH
  [PASS] admin_auth_nonce_replay_rejected — err=ADMIN_NONCE_REPLAY
  [PASS] admin_auth_unknown_rejected      — err=ADMIN_UNKNOWN
  [PASS] admin_auth_op_mismatch_rejected  — err=ADMIN_OP_MISMATCH
  [PASS] key_expiry_enforced              — err=EVALUATOR_KEY_EXPIRED
  [PASS] jwks_bundle_published            — bytes>0 keys>0
  [PASS] version_bumps_on_mutation        — before=N after=N+1
  [PASS] config_invalid_store_type_rejected — err=INVALID_STORE_TYPE
  [PASS] config_valid_accepted            — err=<nil>
  [PASS] fingerprint_stable               — fp=<16hex>

  PHASE 12 PROOF SUITE: 19/19 assertions passed
==============================================================
```

## INVARIANTS (still hold after Phase 12)

1. `EnforceExternalDecision` runs exactly 10 stages in exactly the v11 order. Zero diffs in the verification pipeline source.
2. `CentralGuardCheck` still blocks PDP/KSML/GovernanceKernel in EXTERNAL mode. No new code path imports any PDP/KSML symbol.
3. [external_decision_test_sim.go](../external_decision_test_sim.go) — 20/20 original tests pass **unchanged**.
4. No private keys persisted anywhere (process memory or disk).
5. Production boot refuses to start without a durable store + non-default admin keys.
6. Every registry mutation is: admin-auth → rate-limit → persist → chain → version-bump, in that order, all fail-closed.

**Phase 12 closes the operational perimeter around the Phase 11 cryptographic core. The trust boundary remains exactly where it was — proof over logic.**

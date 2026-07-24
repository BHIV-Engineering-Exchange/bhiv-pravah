# Enforcement Invariants — Sarathi PEP v11.0

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Zero-Trust Verification + Enforcement Boundary
**Host Organization:** Blackhole Infiverse (BHIV)
**Version:** 11.0
**Status:** ALL 27 INVARIANTS VERIFIED (172/172 checks passing) + 6 BHIV trust boundary invariants added (v11.0)

### v11.0 Trust Boundary Invariants (BHIV External Decision Path)

**INV-28: No External Decision Without Evaluator Signature**
Statement: No external decision can be enforced without a valid Ed25519 signature from a trusted evaluator.
Mechanism: `ValidateStructure()` rejects decisions with empty `EvaluatorSignature`. Pipeline STEP 4 verifies signature against evaluator's registered public key. Verified by: TEST 11 (unsigned), TEST 15 (wrong key).

**INV-29: No External Decision Without Registry Trust**
Statement: Only evaluators registered in `EvaluatorTrustRegistry` with ACTIVE status can produce enforceable decisions.
Mechanism: Pipeline STEP 3 calls `GetActiveEvaluator()`. Rejected for NOT_FOUND, REVOKED, SUSPENDED. Verified by: TEST 12 (unknown), TEST 13 (revoked), TEST 14 (suspended).

**INV-30: Mode Immutability in Production**
Statement: In production BHIV deployments, the mode is locked to EXTERNAL and cannot be changed at runtime.
Mechanism: `NewProductionModeController()` sets `lockLevel = ModeLockImmutable`. `SetMode()` returns error and records violation. Verified by: TEST 17.

**INV-31: Centralized Guard — No Decision Interface Bypass**
Statement: ALL decision interfaces (PDP, KSML, GovernanceKernel) are blocked by a single centralized guard in EXTERNAL mode.
Mechanism: `CentralGuardCheck()` is the single enforcement gate. Legacy `GuardCheckPDP/KSML/GovernanceKernel` delegate to it. Verified by: TEST 5.

**INV-32: Decision-Request Binding**
Statement: The issued token is cryptographically bound to the exact decision fields via `DecisionCoreHash`.
Mechanism: `DecisionCoreHash = SHA256(decision_id + evaluator_id + agent_id + resource_id + action + verdict + timestamp + nonce)`. Token carries this hash as `policyHash`. Pipeline STEP 10 verifies binding. Verified by: TEST 16, TEST 20.

**INV-33: Verification Trace Completeness**
Statement: Every verification pipeline run produces a complete `VerificationTrace` with per-stage results.
Mechanism: `VerificationTrace` struct records every stage (passed or failed), start/end times, final verdict, and failure details. Verified by: all tests checking `result.VerificationTrace`.

---

## Core Invariants

These invariants are structurally enforced — they cannot be violated without changing the source code and recompiling.

### INV-01: No Execution Without Enforcement
**Statement:** No action can be executed without passing through the enforcement adapter.
**Mechanism:** `ExecuteWithToken()` is the only execution method. It requires a `CapabilityToken` that is only issued by `EnforcementAdapter.Enforce()` for ALLOW verdicts. No other code path issues tokens.
**Verified by:** Phase 3B (17 bypass attacks), v5.0 (20 bypass attacks), v7.0 BYPASS-001, PATH-004

### INV-02: Fail-Closed on All Errors
**Statement:** Any error, panic, or unexpected state results in DENY.
**Mechanism:** Every error path returns DENY. Panic recovery middleware in service boundary. `SafeChainHash/SafeTokenHash` return deterministic fallback, never panic. Audit write failure on ALLOW → downgrade to DENY.
**Verified by:** SAFE-001, SAFE-002, SAFE-003, concurrency stress tests

### INV-03: Immutable Request Hashing
**Statement:** The request hash is computed once at construction and never recomputed.
**Mechanism:** `ExecutionRequest` has unexported fields, no setters. `requestHash` set in constructor using SHA-256 of all fields.
**Verified by:** Phase 1A — deterministic hash, collision resistance

### INV-04: Unique Enforcement Hash Per Evaluation
**Statement:** No two enforcement evaluations produce the same `enforcement_hash`.
**Mechanism:** Each evaluation generates a fresh UUID4 nonce. `enforcement_hash = SHA-256(request_hash + nonce + PDP_response_hash)`. UUID4 collision probability: 1 in 2^122.
**Verified by:** Phase 1A — enforcement nonce uniqueness

### INV-05: Ed25519 Token Signing — Private Key Isolation
**Statement:** Only the enforcement adapter can issue valid capability tokens. The execution engine cannot forge tokens.
**Mechanism:** Adapter holds private key. Engine holds only the public key. Ed25519 private key is never exported or logged.
**Verified by:** Phase 2A — forged signature REJECTED, revoked key REJECTED

### INV-06: Single-Use Token Consumption
**Statement:** A capability token can only be consumed once. Replay is impossible.
**Mechanism:** `TokenRegistry.Consume()` marks token hash in `consumed map[string]time.Time`. Second call returns `TOKEN_ALREADY_USED`. Protected by `sync.Mutex`.
**Verified by:** Phase 3B — token replay attack BLOCKED

### INV-07: Token TTL Expiry with Clock Skew Tolerance
**Statement:** Tokens expire 30 seconds after issuance, with 5-second clock skew tolerance for distributed deployments.
**Mechanism:** `IsExpired()` returns `time.Now().UTC().After(ct.expiresAt.Add(ClockSkewTolerance))`. Effective TTL: 30–35 seconds.
**Verified by:** Phase 2B — token TTL valid, CEDAR-004

### INV-08: Hash Chain Linkage — GENESIS-Anchored
**Statement:** Every enforcement decision is linked to all previous decisions via SHA-256 hash chain. Any tampered entry breaks all subsequent hashes.
**Mechanism:** `entry.TraceHash = SHA-256(JSON({prev: prevHash, current: enforcementHash}))`. Chain starts at GENESIS constant.
**Verified by:** Phase 1B — chain integrity, Phase 4B — full chain walk

### INV-09: No Direct Service Access
**Statement:** External systems cannot call `SaarthiService.ProcessRequest()` directly. They must go through `GatedBridge.RouteExecution()`.
**Mechanism:** Only `GatedBridge` holds a reference to `SaarthiService`. No exported function returns the service. `SaarthiService.VerifyPassport()` rejects calls without valid bridge passport.
**Verified by:** BYPASS-001, BYPASS-002 — `NIL_BRIDGE_PASSPORT` on direct call

### INV-10: Audit Mandate — Vault-Style Fail-Closed
**Statement:** If the audit system is unhealthy (circuit OPEN), all execution is blocked.
**Mechanism:** `MandatoryAuditGate.IsHealthy()` checked at bridge entry (Step 3.7). Unhealthy → immediate DENY. Circuit breaker: 5 consecutive failures → OPEN state.
**Verified by:** AUDIT-001, AUDIT-002, AUDIT-003, AUDIT-004

### INV-11: Default-Deny Policy Evaluation
**Statement:** A request with no matching ALLOW rule is always DENIED.
**Mechanism:** PDP returns DENY if `FindMatchingRules()` returns empty. `AUTH-DENY-ALL` wildcard rule as last entry. No rule = no permission.
**Verified by:** Phase 2A — policy has default-deny rule

### INV-12: Policy Integrity — Ed25519-Signed
**Statement:** Policies cannot be tampered between disk and evaluation. Tampered policies are rejected at load time.
**Mechanism:** Each policy's SHA-256 hash is Ed25519-signed. `VerifyPolicySignature()` called at `NewSarathiPDPFromRegistry()`. Tampered hash → `POLICY_HASH_MISMATCH`.
**Verified by:** Phase 2A — tampered hash REJECTED, forged signature REJECTED

### INV-13: Classification Ceiling Enforcement
**Statement:** An agent cannot access a resource with higher security classification than the agent's clearance.
**Mechanism:** PDP Stage 4: `if agentClearance < resourceClassification { return DENY }`. 5-level lattice L0–L4.
**Verified by:** ATK-06 — classification violation BLOCKED

### INV-14: Enforcement Hash in Execution Chain
**Statement:** The execution engine verifies that the enforcement hash in the token exists in the adapter's chain before executing.
**Mechanism:** Token carries `enforcementHash`. Engine's Check 7: `adapter.IsEnforcementHashInChain(token.enforcementHash)`.
**Verified by:** Phase 3B — hand-crafted response BLOCKED (hash not in chain)

### INV-15: Token Issuer and Audience Binding
**Statement:** A token issued by one adapter instance cannot be replayed to another, and a token for resource-X cannot be accepted for resource-Y.
**Mechanism:** `issuer = "sarathi-enforcement-adapter"`, `audience = resource_type`. Both included in integrity hash and verified at token validation.
**Verified by:** C-05 fix verification — cross-instance replay prevented

### INV-16: Bridge Passport Transit Proof
**Statement:** The enforcement pipeline verifies that each request arrived through the bridge. Passports not issued by the bridge are rejected.
**Mechanism:** `BridgePassportAuthority.VerifyPassport()` checks HMAC-SHA256, age < 30s, and nonce not in `usedNonces`. Only the bridge's `IssuePassport()` creates valid passports (it holds the HMAC key).
**Verified by:** Phase 7 — ecosystem chain proof

### INV-17: Nonce Deduplication — No Passport Replay
**Statement:** A bridge passport cannot be replayed within its 30-second validity window.
**Mechanism:** `usedNonces sync.Map` tracks seen nonces. `LoadOrStore` returns `true` if nonce already exists → `NONCE_ALREADY_USED`. Background goroutine evicts nonces older than 30s.
**Verified by:** C-06 fix verification

### INV-18: BeyondCorp Posture Gate
**Statement:** Agents with low trust scores or high anomaly scores are denied before PDP evaluation. Suspended agents remain denied.
**Mechanism:** Step 0.5 in `Enforce()`: `postureMonitor.Evaluate(agentID)`. Trust < 20 → `TRUST_SCORE_LOW`. Anomaly > 0.8 → `ANOMALY_DETECTED`. Once suspended, `suspended=true` persists.
**Verified by:** POSTURE-001 through POSTURE-006

### INV-19: Revocation Cascade
**Statement:** Revoking an agent or a specific token invalidates all outstanding tokens immediately.
**Mechanism:** `RevocationRegistry.RevokeAgent(agentID)` records all of the agent's tokens as revoked. Token validation Check 9: `revocationRegistry.IsRevoked(tokenID)`.
**Verified by:** REVOKE-001 through REVOKE-005

### INV-20: Constant-Time Token Integrity Comparison
**Statement:** Token integrity verification does not leak timing information about the hash value.
**Mechanism:** `crypto/subtle.ConstantTimeCompare([]byte(ct.tokenHash), []byte(recomputed)) == 1`. Always compares all bytes regardless of where first mismatch occurs.
**Verified by:** C-02 fix — timing attack prevented

### INV-21: Bounded TokenRegistry Memory
**Statement:** The token registry does not grow unboundedly. Consumed tokens are evicted after their TTL window.
**Mechanism:** `consumed map[string]time.Time` stores consumption timestamp. `cleanupLoop()` goroutine evicts entries older than `2*maxTTL + ClockSkewTolerance`.
**Verified by:** C-09 fix — registry bounded

### INV-22: Zero Panic() Execution Paths
**Statement:** No execution path in the system can panic. All panics are eliminated or recovered.
**Mechanism:** `SafeChainHash/SafeTokenHash/SafeExecutionHash` return `(string, error)`. Service boundary panic recovery middleware converts panics to DENY. `crypto/rand` errors produce deterministic fallback.
**Verified by:** SAFE-001, SAFE-002, SAFE-003, stress tests

### INV-23: Numeric Condition Correctness
**Statement:** Cedar-style numeric conditions (`greater_than`, `less_than`) use proper numeric comparison, not string comparison.
**Mechanism:** `strconv.ParseFloat(value, 64)` for both operands. Parse errors default to 0.0. String comparison like `"9" > "10"` is impossible.
**Verified by:** CEDAR-003, CEDAR-004

### INV-24: W3C Trace Context Propagation
**Statement:** Every enforcement pipeline execution has a root trace with child spans for enforcement and execution.
**Mechanism:** `NewTraceContext()` called in `Execute()`. `NewChildSpan()` called at start of `Enforce()`. Spans include start time, end time, attributes (agent_id, resource_id, verdict), and status.
**Verified by:** TRACE-001 through TRACE-005

### INV-25: Key Management Audit Trail
**Statement:** Every key lifecycle event (generate, activate, rotate, revoke, destroy) is audited. Audit failures are logged, not silently swallowed.
**Mechanism:** All 6 audit sink calls in `key_management.go` check errors: `if err := km.auditSink.RecordSystemEvent(...); err != nil { km.logger.Error(...) }`.
**Verified by:** C-07 fix — audit writes checked

### INV-26: Execution Path — Zero Bypass Risk
**Statement:** Of all 16 registered execution paths through the system, zero are classified as BYPASS_RISK.
**Mechanism:** `ExecutionPathRegistry` classifies each path at startup. Paths are SAFE (go through enforcement) or BLOCKED (cannot reach execution). BYPASS_RISK means "can reach execution without enforcement" — this is zero.
**Verified by:** PATH-001 through PATH-004 — `ZERO_BYPASS_PATHS`

### INV-27: Policy Version Consistency
**Statement:** The PDP always evaluates against the registry's active policy version. Version changes are detected and rejected.
**Mechanism:** `NewSarathiPDPFromRegistry()` binds PDP to registry. Policy version checked at Adapter Step 3. Registry version increments on mutation (Zanzibar-style consistency token).
**Verified by:** Phase 2A — registry version check, Phase 2B — policy version mismatch blocked

---

## Invariant Verification Matrix

| Invariant | Test Suite | Test IDs | Status |
|-----------|-----------|----------|--------|
| INV-01 — No execution without enforcement | v7.0 | BYPASS-001, BYPASS-002 | VERIFIED |
| INV-02 — Fail-closed | v7.0 | SAFE-001, SAFE-002, SAFE-003 | VERIFIED |
| INV-03 — Immutable hash | v4.0 Phase 1A | DET-001, DET-002 | VERIFIED |
| INV-04 — Unique enforcement hash | v4.0 Phase 1A | NONCE-001, NONCE-002 | VERIFIED |
| INV-05 — Ed25519 isolation | v4.0 Phase 2A | SIG-001 through SIG-005 | VERIFIED |
| INV-06 — Single-use tokens | v4.0 Phase 3B | REP-001 | VERIFIED |
| INV-07 — TTL + clock skew | v4.0 Phase 2B | TTL-001 | VERIFIED |
| INV-08 — Hash chain GENESIS | v4.0 Phase 1B | CHAIN-001 through CHAIN-005 | VERIFIED |
| INV-09 — No direct service access | v7.0 | BYPASS-001 | VERIFIED |
| INV-10 — Audit mandate | v7.0 | AUDIT-001 through AUDIT-004 | VERIFIED |
| INV-11 — Default-deny | v4.0 Phase 2A | DENY-001 | VERIFIED |
| INV-12 — Policy integrity | v4.0 Phase 2A | SIG-003, SIG-004, SIG-005 | VERIFIED |
| INV-13 — Classification ceiling | v4.0 Phase 3A | SCEN-006 | VERIFIED |
| INV-14 — Hash in chain | v4.0 Phase 3B | ATK-001 | VERIFIED |
| INV-15 — Token issuer/audience | v7.0 | TOKEN-BIND-001 | VERIFIED |
| INV-16 — Bridge passport | v6.0 Phase 7 | CHAIN-007 | VERIFIED |
| INV-17 — Nonce deduplication | v7.0 | C-06 fix | VERIFIED |
| INV-18 — BeyondCorp posture | v7.0 | POSTURE-001 through POSTURE-006 | VERIFIED |
| INV-19 — Revocation cascade | v7.0 | REVOKE-001 through REVOKE-005 | VERIFIED |
| INV-20 — Constant-time comparison | v7.0 | C-02 fix | VERIFIED |
| INV-21 — Bounded registry | v7.0 | C-09 fix | VERIFIED |
| INV-22 — Zero panic | v7.0 | SAFE-001, SAFE-002, SAFE-003 | VERIFIED |
| INV-23 — Numeric conditions | v7.0 | CEDAR-003, CEDAR-004 | VERIFIED |
| INV-24 — W3C tracing | v7.0 | TRACE-001 through TRACE-005 | VERIFIED |
| INV-25 — Key audit trail | v7.0 | C-07 fix | VERIFIED |
| INV-26 — Zero bypass paths | v7.0 | PATH-004 | VERIFIED |
| INV-27 — Policy version consistency | v4.0 Phase 2A, 2B | REG-001, VER-001 | VERIFIED |

**All 27 invariants: VERIFIED. System is provably non-bypassable.**

---

### v14.4 Deterministic Replay Invariant

**INV-REPLAY: Deterministic Replay**
**Statement:** Given identical inputs (agent_id, resource_id, action, correlation_id), the pipeline MUST produce identical deterministic fields (verdict, error_code, execution_state, schema_version, request.request_hash) across runs. Non-deterministic fields (trace_id, enforcement_nonce, timestamp) may differ.
**Mechanism:** `ResultWriter.WriteResult()` separates deterministic fields (derived purely from input + policy state) from non-deterministic fields (generated per-invocation). Deterministic fields are computed from the same SHA-256 request hash and policy evaluation path on every run.
**Verified by:** `RunDeterministicReplayTests` in `result_writer.go`

---

*Sarathi Enforcement Adapter v7.0.2 | Enforcement Invariants | 2026-03-31*

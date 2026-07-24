# Sarathi Phase Integration Review Packet — v12.2

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Enforcement Adapter (PEP)
**Host:** Blackhole Infiverse (BHIV)
**Phase:** v12.2 Boundary Purification & Pipeline Integration Lock
**Date:** 2026-04-09
**Classification:** Internal Sovereign Design / Strictly Confidential

---

## 1. Entry Point

The system has exactly **two** legitimate execution entry points. There is no third path.

| Mode | Entry Point | File | Caller |
|---|---|---|---|
| INTERNAL | [SarathiEnforcementPipeline.Execute()](../enforcement_adapter.go#L911) | [enforcement_adapter.go](../enforcement_adapter.go) | BHIV systems with internal PDP |
| EXTERNAL | [EnforcementAdapter.EnforceExternalDecision()](../external_decision.go#L1416) → [ExecutionEngine.ExecuteWithToken()](../execution_engine_sim.go) | [external_decision.go](../external_decision.go) | Evaluator counterparty (signed `ExternalDecision`) |

Both paths converge on the same chain commit (`appendToChain`) and the same 9-check token gate. Nothing else can drive execution.

---

## 2. Core Execution Flow (max 3 files)

The end-to-end flow lives in three files only. Boundary purification (v12.2) folded all v12.1 pre-gate code back into these.

### 2.1 [enforcement_adapter.go](../enforcement_adapter.go)
- Pre-gates (v12.2 consolidated):
  - [PreGateRateLimiter](../enforcement_adapter.go) — admission control side-gate (folded from `pre_gate_ratelimit.go`).
  - [PostureVerifier](../enforcement_adapter.go) — signed posture pre-gate (folded from `posture_signal.go`).
- [EnforcementAdapter.Enforce()](../enforcement_adapter.go#L232) — internal verification pipeline (9 stages).
- [SarathiEnforcementPipeline.Execute()](../enforcement_adapter.go#L911) — wires pre-gates → Enforce → token sign → ExecuteWithToken.
- v12.2 pipeline integrity assertion layer:
  - [SarathiPipelineOrder](../enforcement_adapter.go) + [ExpectedPipelineHash](../enforcement_adapter.go).
  - [SarathiExternalPipelineOrder](../enforcement_adapter.go) + [ExpectedExternalPipelineHash](../enforcement_adapter.go).
  - [init()](../enforcement_adapter.go) panics on `PIPELINE_INTEGRITY_VIOLATION` — binary refuses to boot if order is mutated.

### 2.2 [execution_request.go](../execution_request.go)
- [ExecutionRequest](../execution_request.go#L46) — immutable, hash-bound request.
- [SignedPostureSignal](../execution_request.go) — externally-signed posture data structure (folded from `posture_signal.go`).
- `postureSignPayload()` — canonical signing bytes for the posture issuer.

### 2.3 [external_decision.go](../external_decision.go)
- [EnforceExternalDecision](../external_decision.go#L1416) — 10-stage external decision pipeline.
- [TrustConsumer](../external_decision.go) interface + [InMemoryTrustConsumer](../external_decision.go) (folded from `trust_consumer.go`).
- [BootstrapTrustConsumer](../external_decision.go) — default-build evaluator trust loader (snapshot-based).
- Compile-time assertion: `var _ TrustConsumer = (*EvaluatorTrustRegistry)(nil)`.

---

## 3. Live Flow (request → execution)

```
                       ┌─────────────────────────────────────────┐
                       │  pipeline.Execute(agent, res, act, cid) │
                       └────────────────────┬────────────────────┘
                                            │
                       ┌────────────────────▼────────────────────┐
                       │  STAGE 1 [SYSTEM GUARD]                 │
                       │  PreGateRateLimiter.Admit()             │
                       │  ✗ rejected → return pre_gate result    │
                       │      (no chain entry, no token)         │
                       └────────────────────┬────────────────────┘
                                            │ admitted
                       ┌────────────────────▼────────────────────┐
                       │  STAGE 2 [SYSTEM GUARD]                 │
                       │  PostureVerifier.Admit(SignedPosture)   │
                       │  ✗ rejected → return pre_gate result    │
                       └────────────────────┬────────────────────┘
                                            │ admitted
                       ┌────────────────────▼────────────────────┐
                       │  EnforcementAdapter.Enforce(req)        │
                       │  STAGE 3  PRE_PDP_VALIDATION            │
                       │  STAGE 4  POLICY_VERSION_CHECK          │
                       │  STAGE 5  PDP_EVALUATION                │
                       │  STAGE 6  PDP_HASH_INTEGRITY            │
                       │  STAGE 7  ENFORCEMENT_RESPONSE_BUILD    │
                       │  STAGE 8  TOKEN_SIGN  (Ed25519)         │
                       │  STAGE 9  CHAIN_APPEND (GENESIS-anchor) │
                       └────────────────────┬────────────────────┘
                                            │ ALLOW + signed token
                       ┌────────────────────▼────────────────────┐
                       │  ExecutionEngine.ExecuteWithToken(tok)  │
                       │  9-CHECK GATE:                          │
                       │   1. NO_TOKEN                           │
                       │   2. INVALID_SIGNATURE                  │
                       │   3. HASH_MISMATCH                      │
                       │   4. TOKEN_EXPIRED                      │
                       │   5. TOKEN_ALREADY_USED                 │
                       │   6. REQUEST_HASH_MISMATCH              │
                       │   7. POLICY_MISMATCH                    │
                       │   8. ENFORCEMENT_HASH_NOT_IN_CHAIN ◄── INV-36
                       │   9. TOKEN_REVOKED                      │
                       └────────────────────┬────────────────────┘
                                            │
                                          EXECUTED
```

External path (EXTERNAL mode) replaces stages 3–7 with the 10-stage `EnforceExternalDecision` pipeline that verifies an evaluator's signed `ExternalDecision`. Both paths share STAGES 8–9 and the 9-check token gate.

---

## 4. What Was Built in v12.2

| # | Artifact | File | Purpose |
|---|---|---|---|
| 1 | Phase A: Boundary Purification | `enforcement_adapter.go`, `execution_request.go`, `external_decision.go` | Folded 3 v12.1 pre-gate files back into existing core files. Net delta: −3 Go files. |
| 2 | Phase B: Pipeline Integrity Assertion Layer | `enforcement_adapter.go` | `SarathiPipelineOrder`, `SarathiExternalPipelineOrder`, `ExpectedPipelineHash`, `ExpectedExternalPipelineHash`, `init()` panic. |
| 3 | Phase B: Stage classification comments | `enforcement_adapter.go` | `[SYSTEM GUARD]` / `[VERIFICATION]` / `[EXTERNAL INPUT]` labels on each stage. |
| 4 | Phase C: Bypass proof harness | `enforcement_adapter_main.go` | `phase12_2_bypass_proof()` — INV-36. |
| 5 | Phase B: Pipeline integrity harness | `enforcement_adapter_main.go` | `phase12_2_pipeline_integrity()` — INV-35. |
| 6 | Phase 3B fix | `enforcement_adapter_main.go` | ATTACK 14 rate-limit test now drives the v12.1 pre-gate, not the deprecated in-Enforce() helper. |
| 7 | Phase G: Review packet | `review_packets/phase_integration_sarathi.md` | This file. |
| 8 | Phase G: Root review supplement | `REVIEW_PACKET.md` | v12.2 supplement section prepended. |

**Net file delta:** −3 Go files, +1 markdown file.

---

## 5. Failure Cases (Deterministic Failure Map)

Every failure point produces a deterministic, single-source-of-truth reason code. No path emits a generic error.

| # | Stage | Failure Reason | Where Surfaced | Chain Entry? |
|---|---|---|---|---|
| 1 | PRE_GATE_RATE_LIMIT | `RATE_LIMIT_EXCEEDED` / `GLOBAL_RATE_LIMIT_EXCEEDED` | `pre_gate.reason` in pipeline result | NO (admission control) |
| 2 | PRE_GATE_POSTURE_VERIFY | `POSTURE_SIGNAL_MISSING` / `POSTURE_SIGNAL_INVALID` / `POSTURE_SIGNAL_EXPIRED` / `POSTURE_ISSUER_UNKNOWN` / `POSTURE_SIGNAL_REPLAYED` / `AGENT_POSTURE_DENIED` | `pre_gate.reason` | NO (admission control) |
| 3 | PRE_PDP_VALIDATION | `VALIDATION_FAILED: <details>` | `enforcement.enforcement_stage` | YES |
| 4 | POLICY_VERSION_CHECK | `POLICY_VERSION_MISMATCH` | `enforcement.enforcement_stage` | YES |
| 5 | PDP_EVALUATION | `DENY` / `ESCALATE` from PDP | `enforcement.verdict` | YES |
| 6 | PDP_HASH_INTEGRITY | `REQUEST_HASH_MISMATCH` | `enforcement.enforcement_stage = PDP_HASH_MISMATCH` | YES |
| 7 | EVALUATOR_TRUST_CHECK (external) | `EVALUATOR_NOT_FOUND` / `EVALUATOR_REVOKED` / `EVALUATOR_SUSPENDED` / `EVALUATOR_NOT_ACTIVE` | `external.block_reason` | YES |
| 8 | SIGNATURE_VERIFICATION (external) | `SIGNATURE_VERIFICATION_FAILED` | `external.block_reason` | YES |
| 9 | INTEGRITY_CHECK (external) | `INTEGRITY_FAILED` / `CORE_HASH_INTEGRITY_FAILED` | `external.block_reason` | YES |
| 10 | EXPIRY_CHECK (external) | `DECISION_EXPIRED` | `external.block_reason` | YES |
| 11 | REPLAY_CHECK (external) | `REPLAY_DETECTED` | `external.block_reason` | YES |
| 12 | BINDING_CHECK (external) | `BINDING_HASH_MISMATCH` | `external.block_reason` | YES |
| 13 | TOKEN_SIGN | (cannot fail; signer is in-process) | n/a | n/a |
| 14 | EXECUTE_WITH_TOKEN | `NO_TOKEN` / `INVALID_SIGNATURE` / `HASH_MISMATCH` / `TOKEN_EXPIRED` / `TOKEN_ALREADY_USED` / `REQUEST_HASH_MISMATCH` / `POLICY_MISMATCH` / `ENFORCEMENT_HASH_NOT_IN_CHAIN` / `TOKEN_REVOKED` | `execution.block_reason` | execution chain |

The DENY/ESCALATE → execution-blocked transition is recorded in BOTH the enforcement chain AND the execution chain so the audit trail is complete on both sides of the boundary.

---

## 6. Proof (Harness Output)

```
PHASE 12.2: PIPELINE INTEGRITY ASSERTION (INV-35)
  [PASS] INV-35a: Internal pipeline hash pinned (7bfb3580a453d0c9)
  [PASS] INV-35b: External pipeline hash pinned (5643c0ca0947a9e9)
  [PASS] INV-35c: Internal pipeline length frozen at 9 (got 9)
  [PASS] INV-35d: External pipeline length frozen at 10 (got 10)

PHASE 12.2: NON-BYPASSABILITY PROOF (INV-36)
  [PASS] INV-36a: Forged-token execution refused (executed=false)
  [PASS] INV-36b: Execution state is EXECUTION_BLOCKED
  [PASS] INV-36c: Block reason is ENFORCEMENT_HASH_NOT_IN_CHAIN

ATTACK 14: Rate Limit Flood Attack (GAP-07 / v12.1 PRE-GATE)
  [PASS] 4th request from same agent was RATE_LIMITED at pre-gate

Phase 1A (Contracts):    4/4 PASSED
Phase 1B (Hash Chain):   5/5 PASSED
Phase 2A (PDP+Signing):  18/18 PASSED
Phase 2B (Engine+Token): 18/18 PASSED
Phase 3A (Scenarios):    35/35 PASSED
Phase 3B (Bypass):       17/17 BLOCKED
External Workflow:       10/10 PASSED
External Bypass:         15/15 BLOCKED
Advanced Attacks:        2/2 BLOCKED
Phase 4A (Invariants):   17/17 PASSED
Phase 4B (Chains):       Enforcement=true, Execution=true
Total Checks:            150/150 PASSED
ENFORCEMENT ADAPTER VALIDATION: PASSED
```

`go build .` exits 0. `go vet .` exits 0. `ls pre_gate_ratelimit.go posture_signal.go trust_consumer.go` reports "No such file or directory" for all three.

---

## 7. Boundary Rules (LOAD-BEARING)

These rules are non-negotiable. Any change to enforcement code MUST be checked against this list.

1. **Sarathi VERIFIES; it does not EVALUATE.** Policy decisions come from a PDP (internal SarathiPDP) or an external evaluator (signed `ExternalDecision`). Sarathi never invents a verdict.
2. **Sarathi never computes posture.** Posture arrives as an Ed25519-signed `SignedPostureSignal` from a known issuer. Sarathi only verifies the signature, expiry, nonce, and value.
3. **Rate limiting is admission control, not verification.** Rate-limited requests never enter `Enforce()`, never produce a chain entry, never appear in the enforcement trace.
4. **Sarathi does not own evaluator lifecycle.** Registration, suspension, key rotation, admin auth, JWKS — all soft-frozen behind the `TrustConsumer` interface. Default build uses `InMemoryTrustConsumer` from a static snapshot.
5. **Pipeline order is hash-pinned.** `SarathiPipelineOrder` and `SarathiExternalPipelineOrder` are SHA-256-pinned. Reordering panics at startup (`PIPELINE_INTEGRITY_VIOLATION`).
6. **Execution requires a signed token whose `enforcement_hash` is in the chain.** Hand-crafted tokens fail check #8 of the 9-check gate.
7. **Mode lock is IMMUTABLE in production.** Once `ModeController` is set to EXTERNAL with `ModeLockImmutable`, the only way to switch is a process restart.
8. **`CentralGuard` blocks PDP/KSML/GovernanceKernel paths in EXTERNAL mode.** No bypass route exists.
9. **No new subsystems / no file dilution.** All v12.1 gap fixes were folded back into the 3 core files in v12.2. Net delta: −3 Go files.
10. **All failures are deterministic block codes.** No generic errors. Every block has a single-source-of-truth reason from `capability_token.go` `Block*` constants.

---

## 8. What Sarathi Will NEVER Do

- ❌ Invent or modify a policy verdict.
- ❌ Compute posture from agent behavior, request patterns, IP, or activity.
- ❌ Score trust, threshold confidence, or interpret evaluator reasoning.
- ❌ Manage evaluator lifecycle (register, suspend, rotate, JWKS, admin auth).
- ❌ Issue a token without an enforcement chain entry.
- ❌ Permit execution of a token whose `enforcement_hash` is not in the chain.
- ❌ Reorder, insert into, or delete from the canonical pipeline at runtime.
- ❌ Allow rate-limit / posture rejections to influence chain state.
- ❌ Run in INTERNAL and EXTERNAL mode at the same time within a single process.
- ❌ Bypass the 9-check token gate, even for internally-issued tokens.
- ❌ Create or accept a new top-level Go file for "side functionality."

---

## 9. Pinned Hashes

| Pipeline | Stages | Expected SHA-256 |
|---|---|---|
| `SarathiPipelineOrder` (internal) | 9 | `7bfb3580a453d0c94c0f01ec83029ebd5e0bab346c130b45b89f9c9f238453b1` |
| `SarathiExternalPipelineOrder` (external) | 10 | `5643c0ca0947a9e941d53a483fc0b62fab36b4e98aa08600c2bb4ea8a4ad15f8` |

To change either pipeline:
1. Update the slice in [enforcement_adapter.go](../enforcement_adapter.go).
2. Update the matching `Expected*PipelineHash` constant.
3. Add a row to the failure map in section 5 of this document.
4. Justify the change in a new entry in [REVIEW_PACKET.md](../REVIEW_PACKET.md).
5. Re-run the harness; INV-35 must pass.

If steps 1–2 are not done in the same commit, the binary will refuse to start with `PIPELINE_INTEGRITY_VIOLATION`.

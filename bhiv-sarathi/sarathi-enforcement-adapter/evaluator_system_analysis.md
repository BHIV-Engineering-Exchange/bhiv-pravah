# External Evaluator System — Production Readiness Analysis

## Question 1: Where Can an Evaluator Enter Their Credentials?

Currently, the **only** way to register an evaluator is via **Go code** — calling `RegisterEvaluator()` programmatically:

```go
// From external_decision_test_sim.go (line 79)
registry.RegisterEvaluator(
    "ishan-evaluator-v1",           // evaluator ID
    "Ishan Shirode Evaluator v1",   // human-readable name
    ishanPub,                       // Ed25519 public key
    map[string]string{"version": "1.0", "org": "BHIV"},  // metadata
    "system-init",                  // who initiated
)
```

> [!WARNING]
> **There is NO external-facing API, HTTP endpoint, CLI command, or configuration file** where an evaluator can submit their credentials. Registration is hardcoded into test/demo flows. There are zero calls to `RegisterEvaluator()` outside of test simulation files (`external_decision_test_sim.go`).

### What's missing for evaluator self-registration:
- ❌ No HTTP/gRPC API for evaluator registration
- ❌ No config file (JSON/YAML) to pre-register evaluators at startup
- ❌ No admin CLI to manage evaluators
- ❌ No mutual-TLS or challenge-response flow for evaluator identity verification during registration
- ❌ No approval workflow (evaluator submits → admin approves)

---

## Question 2: Separate Evaluator Registry vs. In external_decision.go?

### Current State
The `EvaluatorTrustRegistry` is **embedded inside `external_decision.go`** (lines 500–887) — a 1,802-line file that also contains the ExternalDecision model, signature system, mode controller, centralized guard, verification pipeline, and enforcement logic.

### Recommendation: **Build a Separate Module**

For production, the evaluator registry should be **its own file or package** because:

| Concern | Why Separate |
|---|---|
| **Lifecycle management** | Register/suspend/revoke/rotate are admin operations with different access patterns than enforcement |
| **Persistence** | The registry needs its own storage backend (database/file); currently it's **purely in-memory and lost on restart** |
| **API surface** | Registration should expose an HTTP/gRPC API separate from the enforcement endpoint |
| **Testing** | Registry logic (CRUD + lifecycle) should be testable independently of the verification pipeline |
| **Security boundary** | Registration requires admin authentication; enforcement requires evaluator authentication — different trust boundaries |
| **Scalability** | In a multi-instance deployment, registries need synchronization; enforcement is stateless per-decision |

---

## Question 3: Where Does the External Evaluator Get Evaluated?

The evaluator gets checked at **two stages** in the 10-step verification pipeline inside `EnforceExternalDecision()` (line 1381):

### Step 3: EVALUATOR_TRUST_CHECK (lines 1472–1484)
```go
evaluatorRecord, evalErr := ea.evaluatorRegistry.GetActiveEvaluator(decision.EvaluatorID)
if evalErr != nil {
    return blocked(StageEvaluatorTrustCheck, "EVALUATOR_NOT_TRUSTED", evalErr.Error())
}
```
This rejects:
- `EVALUATOR_NOT_FOUND` — evaluator ID not in registry
- `EVALUATOR_REVOKED` — permanently revoked  
- `EVALUATOR_SUSPENDED` — temporarily suspended
- `EVALUATOR_NOT_ACTIVE` — any other non-active status

### Step 4: SIGNATURE_VERIFICATION (lines 1487–1499)
```go
sigValid, sigKeySource, sigReason := ea.evaluatorRegistry.VerifySignatureWithRotation(
    decision.EvaluatorID,
    []byte(decision.DecisionCoreHash),
    decision.EvaluatorSignature,
)
```
This checks:
- Ed25519 signature against current public key
- Falls back to previous keys within grace period (key rotation support)
- Returns key source (`CURRENT_KEY` or `PREVIOUS_KEY_N`)

---

## Question 4: Is the System Production-Grade?

### ✅ What IS Built Properly

| Feature | Status | Evidence |
|---|---|---|
| Ed25519 signature verification | ✅ Complete | `VerifySignature()`, `VerifySignatureWithRotation()` |
| Evaluator lifecycle (ACTIVE/SUSPENDED/REVOKED) | ✅ Complete | Full state machine with irreversible revocation |
| Key rotation with grace period | ✅ Complete | `RotateKey()` + `VerifySignatureWithRotation()` |
| 10-stage verification pipeline | ✅ Complete | Mode → Structure → Trust → Signature → Integrity → Expiry → Replay → Rate → Posture → Binding |
| Capability token issuance after verification | ✅ Complete | Lines 1649–1703: creates token bound to decision core hash |
| Token Ed25519 signing | ✅ Complete | `TokenAuthority.SignToken()` signs with adapter's private key |
| Token 8-check validation on execution | ✅ Complete | `ValidateTokenFull()`: existence → signature → integrity → expiry → consumed → verdict → chain → decision_id |
| Replay protection (nonce tracking) | ✅ Complete | `externalReplayTracker` with deferred commit (GAP-3 fix) |
| Mode lock (IMMUTABLE in production) | ✅ Complete | `NewProductionModeController()` locks to EXTERNAL, cannot be changed at runtime |
| Centralized guard blocking PDP/KSML | ✅ Complete | `CentralGuardCheck()` blocks ALL decision interfaces in EXTERNAL mode |
| Append-only audit event log | ✅ Complete | Every registry mutation logged to `eventLog` |
| Thread safety | ✅ Complete | `sync.RWMutex` on registry, `sync.Mutex` on adapter |
| Test coverage | ✅ Complete | 20 test cases, 55+ assertions — tests 11–16, 19 specifically test evaluator trust |

### ❌ What IS Missing for Production

| Gap | Severity | Detail |
|---|---|---|
| **No evaluator registration API** | 🔴 CRITICAL | No HTTP/gRPC/CLI interface for evaluators to register. All registration is hardcoded in test files. |
| **No registry persistence** | 🔴 CRITICAL | `EvaluatorTrustRegistry` is purely **in-memory** (`map[string]*EvaluatorRecord`). Every restart loses all registered evaluators. Unlike `TokenRegistryStore` which has a persistence interface, the evaluator registry has **no `Store` interface, no save/load, no database backend**. |
| **No evaluator identity verification during registration** | 🟡 HIGH | Anyone who can call `RegisterEvaluator()` can register any public key. There's no challenge-response, no mTLS, no proof-of-possession during key registration. The system trusts whoever calls `RegisterEvaluator()` without verifying they actually hold the corresponding private key. |
| **No rate limit on registration** | 🟡 HIGH | No limit on how many evaluators can be registered. An attacker with code access could flood the registry. |
| **No admin authentication for lifecycle ops** | 🟡 HIGH | `SuspendEvaluator()`, `RevokeEvaluator()`, `ReactivateEvaluator()` take an `initiator` string parameter for audit logging, but there's no authentication — the initiator string is just logged, not verified. |
| **No registry config file** | 🟡 MEDIUM | Unlike `PolicyRegistry` which loads from `registry_config.json`, the evaluator registry has no config file. Evaluators can't be pre-configured at deployment. |
| **No event log persistence** | 🟡 MEDIUM | The append-only `eventLog` is in-memory only. Registry audit trail is lost on restart. |
| **No key expiry** | 🟢 LOW | Evaluator keys don't have an inherent expiry. Once registered, a key is valid forever unless manually rotated/revoked. |
| **No evaluator certificate/metadata validation** | 🟢 LOW | Metadata is a bare `map[string]string` with no schema validation. |

---

## Question 5: Capability Token Flow — Is It Complete?

### YES — The Full Flow Exists and Works

Here is the complete chain when an external evaluator passes a decision:

```
Evaluator creates ExternalDecision
    → Evaluator signs with Ed25519 private key (SignDecision())
    → Decision submitted to Sarathi
    → EnforceExternalDecision() runs 10-stage pipeline:
        Step 1: Mode check (EXTERNAL confirmed)
        Step 2: Structure validation (all fields present)
        Step 3: Evaluator trust check (ACTIVE in registry)      ← REGISTRY
        Step 4: Signature verification (Ed25519 against public key) ← REGISTRY
        Step 5: Integrity check (SHA-256 hash recomputed)
        Step 6: Expiry check (TTL + clock skew)
        Step 7: Replay check (nonce not seen before)
        Step 8: Rate limit check (global + per-agent)
        Step 9: Posture check (BeyondCorp agent trust)
        Step 10: Binding check (decision-request hash match)
    → ALL 10 STAGES PASS
    → IF verdict == ALLOW:
        → Create synthetic ExecutionRequest (line 1655)
        → Create synthetic PDPResponse bound to decision_core_hash (line 1662)
        → Issue CapabilityToken via NewExecutionResponse (line 1679)
        → Sign token with TokenAuthority Ed25519 (line 1683)
        → Append to enforcement chain (line 1687)
        → Return ExternalEnforcementResult with Token (line 1690)
    → Token can be used with ExecutionEngine.ExecuteWithToken()
        → 8-check validation gate (existence, signature, integrity, expiry, 
           consumed, verdict, chain, decision_id)
        → Execution permitted
```

> [!NOTE]
> The token issued for external decisions carries the `DecisionCoreHash` as its `policyHash` field (line 1666). This cryptographically binds the token to the specific external decision — the token **cannot** drift to a different decision or be used for a different request. The token is also Ed25519-signed by Sarathi's own `TokenAuthority` (separate key from evaluator's key), so even the evaluator cannot forge capability tokens.

---

## Summary

| Aspect | Status |
|---|---|
| Evaluator verification against registry | ✅ Built and working |
| Ed25519 signature authentication | ✅ Built and working |
| Decision hash integrity validation | ✅ Built and working |
| Capability token issuance after verification | ✅ Built and working |
| Token signing and execution gate | ✅ Built and working |
| **External interface for evaluator registration** | ❌ **NOT built** |
| **Evaluator registry persistence** | ❌ **NOT built** |
| **Admin authentication for lifecycle ops** | ❌ **NOT built** |

**Bottom line**: The core cryptographic plumbing (signature verification → token issuance → execution gate) is **production-grade**. But the operational layer around it (how evaluators register, how keys persist, how admins manage lifecycle) is **missing entirely**. For production you need: (1) a persistence layer for the evaluator registry, (2) an API for evaluator onboarding, and (3) admin authentication for lifecycle operations.

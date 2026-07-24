# Evaluator Trust Registry — Location & Analysis

## Where It Lives

The **`EvaluatorTrustRegistry`** is fully implemented in a single file:

### 📁 [external_decision.go](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go) — Lines 500–887

This is the **Phase 2** section of the file, titled **"EVALUATOR TRUST REGISTRY"**.

---

## Registry Structure

The registry is a struct at [line 566](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L566-L570):

```go
type EvaluatorTrustRegistry struct {
    mu          sync.RWMutex
    evaluators  map[string]*EvaluatorRecord    // evaluator_id → record
    eventLog    []EvaluatorRegistryEvent        // Append-only audit log
}
```

Each evaluator is stored as an [EvaluatorRecord](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L526-L540):

| Field | Type | Purpose |
|---|---|---|
| `EvaluatorID` | `string` | Unique identifier |
| `Name` | `string` | Human-readable name |
| `Status` | `EvaluatorStatus` | `ACTIVE` / `SUSPENDED` / `REVOKED` |
| `PublicKey` | `ed25519.PublicKey` | Ed25519 public key for signature verification |
| `PreviousKeys` | `[]EvaluatorKeyVersion` | Rotated keys with grace periods |
| `RegisteredAt` | `time.Time` | Registration timestamp |
| `LastActiveAt` | `time.Time` | Last successful verification |
| `RevokedAt` | `*time.Time` | Revocation timestamp (if revoked) |
| `RevokeReason` | `string` | Reason for revocation |

---

## Registry Methods (Authentication, Validation, Verification)

### Registration & Lifecycle Management

| Method | Lines | Purpose |
|---|---|---|
| [NewEvaluatorTrustRegistry()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L573-L578) | 573–578 | Creates empty registry |
| [RegisterEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L583-L625) | 583–625 | Register evaluator with Ed25519 public key, starts as `ACTIVE` |
| [SuspendEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L664-L689) | 664–689 | Set status to `SUSPENDED` (reversible) |
| [ReactivateEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L692-L718) | 692–718 | Move from `SUSPENDED` → `ACTIVE` |
| [RevokeEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L722-L748) | 722–748 | Permanently revoke (IRREVERSIBLE) |

### Trust & Signature Verification

| Method | Lines | Purpose |
|---|---|---|
| [GetActiveEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L639-L660) | 639–660 | Returns evaluator ONLY if `ACTIVE`; rejects `NOT_FOUND`, `REVOKED`, `SUSPENDED` |
| [VerifySignatureWithRotation()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L806-L838) | 806–838 | Verifies Ed25519 signature against current key AND grace-period keys |
| [RotateKey()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L753-L799) | 753–799 | Replaces public key, old key valid during grace period |

### Query & Audit

| Method | Lines | Purpose |
|---|---|---|
| [GetEvaluator()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L629-L634) | 629–634 | Raw lookup, does NOT check status |
| [EvaluatorCount()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L850-L854) | 850–854 | Total registered evaluators |
| [ActiveEvaluatorCount()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L857-L867) | 857–867 | Only ACTIVE evaluators |
| [ListEvaluators()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L870-L887) | 870–887 | Summary map for audit/debugging |
| [GetEventLog()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L841-L847) | 841–847 | Full append-only audit trail of registry events |

---

## How the Registry Wires into Enforcement

### Field on EnforcementAdapter

In [enforcement_adapter.go:138-142](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/enforcement_adapter.go#L138-L142):
```go
// Phase 11 (BHIV Trust Hardening): Evaluator trust registry.
// Holds Ed25519 public keys of trusted evaluators. Only decisions signed by
// ACTIVE evaluators in this registry are accepted for enforcement.
evaluatorRegistry *EvaluatorTrustRegistry
```

### Initialization

In [external_decision.go:1714-1723](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L1714-L1723):
```go
func (ea *EnforcementAdapter) InitExternalMode() {
    if ea.evaluatorRegistry == nil {
        ea.evaluatorRegistry = NewEvaluatorTrustRegistry()
    }
}
```

### Accessor Methods

| Method | Lines | Purpose |
|---|---|---|
| [GetEvaluatorRegistry()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L1726-L1728) | 1726–1728 | Returns registry for configuration |
| [SetEvaluatorRegistry()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L1731-L1735) | 1731–1735 | Sets pre-configured registry |

---

## 10-Stage Verification Pipeline (Where Registry is Checked)

The registry is used at **STEP 3** and **STEP 4** of the [EnforceExternalDecision()](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go#L1381-L1703) pipeline:

| Step | Stage | Lines | What It Does |
|---|---|---|---|
| 1 | `MODE_CHECK` | 1448–1457 | Confirms system is in `EXTERNAL` mode |
| 2 | `STRUCTURE_CHECK` | 1460–1469 | All required fields present, signature not empty |
| **3** | **`EVALUATOR_TRUST_CHECK`** | **1472–1484** | **`GetActiveEvaluator()` — verifies evaluator exists, is ACTIVE, not REVOKED/SUSPENDED** |
| **4** | **`SIGNATURE_VERIFICATION`** | **1487–1499** | **`VerifySignatureWithRotation()` — Ed25519 signature against registered public key(s)** |
| 5 | `INTEGRITY_CHECK` | 1502–1513 | SHA-256 hash recomputation (full + core) |
| 6 | `EXPIRY_CHECK` | 1516–1524 | Timestamp + TTL + clock skew tolerance |
| 7 | `REPLAY_CHECK` | 1527–1538 | Nonce tracker (deferred commit after step 9) |
| 8 | `RATE_LIMIT_CHECK` | 1541–1572 | Global + per-agent rate limits |
| 9 | `POSTURE_CHECK` | 1575–1585 | BeyondCorp-style agent trust posture |
| 10 | `BINDING_CHECK` | 1599–1612 | Decision-request hash binding verification |

> [!IMPORTANT]
> If ANY step fails, the pipeline **HALTS immediately**. No subsequent steps execute. The exact failed stage is recorded in the `VerificationTrace`.

---

## Test Coverage

The registry is exercised by 20 test cases in [external_decision_test_sim.go](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision_test_sim.go):

| Test | What It Proves |
|---|---|
| TEST 1 | Valid signed ALLOW → token issued |
| TEST 11 | Unsigned decision → rejected at `STRUCTURE_CHECK` |
| TEST 12 | Unknown evaluator → rejected at `EVALUATOR_TRUST_CHECK` |
| TEST 13 | Revoked evaluator → rejected at `EVALUATOR_TRUST_CHECK` |
| TEST 14 | Suspended evaluator → rejected; reactivated → accepted |
| TEST 15 | Wrong key signature → rejected at `SIGNATURE_VERIFICATION` |
| TEST 16 | Tampered core hash → rejected at `SIGNATURE_VERIFICATION` |
| TEST 19 | Key rotation → old key accepted during grace period |

---

## Summary

> [!NOTE]
> The evaluator registry **exists and is fully implemented** in [external_decision.go](file:///c:/Users/acer/Downloads/Sarathi/sarathi-enforcement-adapter/external_decision.go) lines 500–887. It provides:
> - **Authentication**: Ed25519 public key binding per evaluator
> - **Validation**: Lifecycle status checks (ACTIVE/SUSPENDED/REVOKED)
> - **Verification**: Ed25519 signature verification with key rotation + grace periods
> - **Audit**: Append-only event log of all registry mutations
> - **Thread safety**: `sync.RWMutex` for concurrent access

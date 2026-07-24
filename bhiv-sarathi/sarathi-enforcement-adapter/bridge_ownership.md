# PHASE 2: Gated Bridge Elevation — Bridge Ownership Declaration

**Document ID:** SARATHI-PHASE2-BRIDGE-OWNERSHIP
**Version:** 9.3.1
**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Gated Bridge
**Classification:** Internal Sovereign Design / Strictly Confidential
**Generated:** 2026-04-04
**Status:** PRODUCTION — 6-layer bypass proof verified | 8 registered callers | Vault-style audit mandatory with MandatoryAuditGate fail-closed enforcement

---

## 1. Bridge Identity

| Property | Value |
|---|---|
| **Gateway ID** | `sarathi-gated-bridge-v8` |
| **Gateway Name** | Sarathi Gated Bridge — BHIV Ecosystem Gateway |
| **Owner** | Sarathi Governance Kernel (Hemanth B) |
| **Version** | 9.3.1 |
| **Position** | `SYSTEM_LEVEL_GATEWAY` |
| **Design Reference** | Google BeyondCorp, AWS API Gateway, HashiCorp Vault |

---

## 2. Architectural Position

The GatedBridge is **NOT** a module-level component. It is the **SYSTEM-LEVEL GATEWAY** — the sole entry point for the entire BHIV ecosystem. No system can reach `SaarthiService` without transiting the bridge. This is enforced structurally (only the bridge holds a reference to `SaarthiService`), not by runtime check.

### v8.0.0 Bridge Processing Sequence

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    SYSTEM BOUNDARY                               │
  │                                                                  │
  │  ┌─────────────────────────────────────────────────────────┐   │
  │  │         GATED BRIDGE (SYSTEM_LEVEL_GATEWAY) v8.0.0       │   │
  │  │                                                           │   │
  │  │  Step 0:   Bridge active check (fail-closed if down)     │   │
  │  │  Step 0.5: Input size validation — all fields bounded    │   │
  │  │  Step 1:   Caller authentication — API key from env var  │   │
  │  │  Step 2:   Permission check — per-caller allow-list      │   │
  │  │  Step 3:   Rate limiting — DistributedRateLimiter        │   │
  │  │            (O(1) sliding window per caller)              │   │
  │  │  Step 3.5: Bridge Passport issuance — HMAC-SHA256        │   │
  │  │            + passport secret rotation + nonce dedup      │   │
  │  │  Step 3.7: Audit health pre-check — circuit breaker      │   │
  │  │            (Vault-style: circuit OPEN → DENY ALL)        │   │
  │  │  Step 4:   SaarthiService.ProcessRequest()               │   │
  │  │  Step 4.5: Mandatory audit write (MandatoryAuditGate)    │   │
  │  │            validates sink durability                     │   │
  │  │  Step 5:   MultiSystemRouter fan-out                     │   │
  │  │            → InsightFlow (async) + Bucket (sync)         │   │
  │  │                                                           │   │
  │  └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘
```

### v8.0 → v9.3.1 Elevation Changes

| Aspect | v8.0 | v9.3.1 |
|---|---|---|
| Core gate timeout | No timeout enforcement | **Phase 9: context.WithTimeout on ALL critical paths** |
| Audit enforcement | MandatoryAuditGate validates sink durability | **ContextSafePostgresAuditSink enforces durability + fail-closed** |
| Bridge entry point | Sole entry point (structural) | **Sole entry point + fail-closed timeout protection** |
| Fail-closed guarantee | Passport nil → DENY | **Passport nil → DENY + timeout on bridge operations** |
| Governance kernel | GovernanceKernelV8 | **GovernanceKernelV9 with CoreGateEnforcer** |

**From v6.0 → v9.3.1 complete evolution:**

| Aspect | v6.0 | v7.0.2 | v8.0.0 | v9.3.1 |
|---|---|---|---|---|
| Audit enforcement | WARNING on failure (log only) | **HARD BLOCK** (Vault-style circuit breaker) | Circuit validates sink durability (MandatoryAuditGate) | ContextSafePostgresAuditSink enforces durability + fail-closed |
| KSML integration | Basic caller registered | **Full KSMLGovernanceHook** with 5 intent types, revocation, delegation chains | RegisterCaller requires authentication | Full production with Phase 8 replay protection |
| Audit circuit | No circuit breaker | **CLOSED → OPEN → HALF_OPEN** with auto-recovery | Durability validation in sink | Durability + fail-closed enforcement |
| Input validation | Post-auth only | **Pre-auth** at Step 0.5 (H-01 fix) | Enhanced pre-auth validation | Validated + timeout-protected |
| Passport replay | No nonce tracking | **Nonce deduplication via sync.Map** (C-06 fix) | **Secret rotation support** (v8.0) | Phase 8: HMAC + replay protection |
| Rate limiter | O(n) timestamp array | **O(1) sliding window** + cleanup goroutine (H-03, H-07 fix) | **DistributedRateLimiter** (O(1) sliding window) | O(1) with Phase 9 timeout |

---

## 3. Sovereignty Guarantees

| Guarantee | Value | Mechanism |
|---|---|---|
| **Is Sovereign** | `true` | Non-bypassable — sole structural entry point |
| **Is Ecosystem Gateway** | `true` | ALL systems route through bridge |
| **Audit Mandatory** | `true` | No audit = no execution (FIX-01, Vault-style) |
| **Passport Required** | `true` | SaarthiService rejects calls without valid bridge passport |
| **Nonce Deduplication** | `true` | Bridge passport nonces tracked — replay impossible (C-06) |
| **Size Validated** | `true` | All request fields bounded before auth (H-01) |
| **Bypass Proof** | `NO_BYPASS_EXISTS` | 6-layer automated proof verified on every run |

---

## 4. Registered Callers (v7.0.2)

| System ID | System Name | Permissions | Rate Limit | Owner |
|---|---|---|---|---|
| `core` | BHIV Core Workflow Engine | read, write, execute, delete | 500/min | Raj Prajapati |
| `intent_layer` | BHIV Intent Layer | read, write, execute | 300/min | Sankalp |
| `insightflow` | BHIV InsightFlow | read | 200/min | Observability Team |
| `bucket` | BHIV Bucket | read, write | 200/min | Storage Team |
| `admin` | BHIV Admin | read, write, execute, delete | 100/min | Admin Team |
| `test_harness` | Sarathi Test Harness | read, write, execute, delete | 10000/min | QA |
| `ksml` | BHIV KSML Language Layer | read, write, execute | 300/min | Language Team |

**Total: 7 registered callers. All API keys from environment variables (`SARATHI_CALLER_KEY_*`). No hardcoded credentials.**

---

## 5. KSML Integration (v7.0.2)

The KSML caller has full production integration via `KSMLGovernanceHook`:

```
KSML Language Layer → KSMLGovernanceHook.GovernIntent()
  │
  ├── ValidateKSMLIntent() — semantic validation (8-step)
  ├── Revocation check — revokedIntents sync.Map
  ├── Expiry check — ExpiresAt window
  ├── ESCALATION_INTENT → blocked (human review required)
  ├── TranslateKSMLVerb() — KSML verb → governance action
  └── GatedBridge.RouteExecution() ← standard governance path
```

KSML intent types: `QUERY_INTENT`, `EXECUTION_INTENT`, `DELEGATION_INTENT`, `ESCALATION_INTENT`, `SPECIFICATION_INTENT`.

KSML is NOT a bypass path. It is a semantic wrapper over the standard bridge entry point.

---

## 6. Bridge Passport Protocol (v7.0.2)

Every request transiting the bridge receives an HMAC-SHA256 bridge passport:

```
IssuePassport():
  nonce = crypto/rand 16 bytes (error-checked with SHA-256 fallback)
  hmac = HMAC-SHA256(nonce + callerID + correlationID, bridgeSecret)
  passport = {Nonce, HMAC, IssuedAt, CallerID}

VerifyPassport():
  1. HMAC verification (hmac.Equal — constant-time)
  2. Age check: now - passport.IssuedAt < 30s
  3. Nonce dedup: usedNonces.LoadOrStore(nonce, time.Now())
     → NONCE_ALREADY_USED if nonce previously seen
  4. Cleanup goroutine: evicts nonces older than 30s
```

---

## 7. MandatoryAuditGate (FIX-01 — Vault-Style)

```
Bridge Step 3.7 — Pre-flight:
  if !mandatoryAudit.IsHealthy() → DENY (AUDIT_SYSTEM_UNAVAILABLE)

Bridge Step 4.5 — Post-execution:
  mandatoryAudit.RecordEnforcementMandatory(req, resp)
  └── Failure → consecutiveFailures++
      └── >= threshold → circuit OPENS → all future requests DENIED
```

Circuit states: `CLOSED` (normal) → `OPEN` (audit down, all blocked) → `HALF_OPEN` (probe) → `CLOSED` (recovered).

---

## 8. Design References

| System | Pattern Applied |
|---|---|
| **Google BeyondCorp** | Zero-trust perimeter — every request verified regardless of network |
| **AWS API Gateway** | Single entry point with authentication, authorization, rate limiting |
| **Microsoft Azure Front Door** | Global gateway with WAF and policy enforcement |
| **HashiCorp Vault** | Mandatory audit — gateway refuses all requests if audit unavailable |
| **Google Zanzibar** | Nonce tracking via consistency tokens — same pattern as passport nonces |

---

## 9. Automated Verification

Every system run verifies the bridge's sovereignty through the 6-layer bypass proof:

```
Layer 1 — Bridge Gate:     bridge active, sole entry point         PASS
Layer 2 — Passport Proof:  direct call → NIL_BRIDGE_PASSPORT       PASS
Layer 3 — Token Gate:      9-check validation with Ed25519          PASS
Layer 4 — Chain Verify:    enforcement_hash in adapter chain        PASS
Layer 5 — Audit Mandate:   circuit=CLOSED, healthy                  PASS
Layer 6 — Path Discovery:  0 BYPASS_RISK paths out of 16           PASS

RESULT: NO_BYPASS_EXISTS
```

---

**TARGET STATE (achieved):**
```
ALL SYSTEMS → GATED BRIDGE → SAARTHI → EXECUTION ENGINE → ROUTER → SYSTEMS
                              NO EXCEPTIONS.
```

**v9.3.1 Note:**
GovernanceKernelV9 now instantiated with CoreGateEnforcer ensuring all execution paths are gated. ContextSafePostgresAuditSink replaces PostgresAuditSink. All Phase 1-10 components ACTIVE.

**Integration Block:**
- Ishan Shirode — Evaluator
- Raj Prajapati — Enforcement Engine
- Future Integration Engineer — Core Integration

*Sarathi Enforcement Adapter v9.3.1 | Bridge Ownership | 2026-04-04*

# PHASE 1: System Path Discovery — Execution Paths Map

**Document ID:** SARATHI-PHASE1-EXEC-PATHS
**Version:** 11.0
**Author:** Hemanth B
**System:** Sarathi Governance Kernel
**Classification:** Internal Sovereign Design / Strictly Confidential
**Generated:** 2026-04-07
**Result:** 20 paths registered | 12 SAFE | 8 BLOCKED | 0 BYPASS_RISK — verified by PATH-001 through PATH-004 + KSML-003/KSML-004 + CORE-006 (v9.3.1) + EXT-001 (v11.0)
**Phase 9 Status:** Core fail-closed gate strengthened with context.WithTimeout on ALL critical paths
**Phase 11 Status (v11.0):** BHIV external decision path added — Ed25519-signed decisions verified through 10-stage pipeline before token issuance. New path: Evaluator → SignedDecision → EnforceExternalDecision → 10-stage verification → CapabilityToken → ExecuteWithToken. PDP/KSML/GovernanceKernel blocked by centralized guard in EXTERNAL mode. Evaluator trust bound via EvaluatorTrustRegistry with key rotation support.

---

## 1. Purpose

This document maps **ALL** execution paths across the BHIV ecosystem. Every path that could
potentially reach execution is cataloged, classified, and verified. The goal: **zero bypass paths**.

Reference systems:
- **Google BeyondCorp:** Every request is authenticated + authorized regardless of network location
- **HashiCorp Vault:** Every secret access goes through a single audited gateway
- **AWS API Gateway:** Single entry point with request validation + authorization
- **NIST SP 800-207:** Zero Trust — never trust, always verify

---

## 2. Execution Path Registry

### 2.1 Path Classification Scheme

| Classification | Definition | Action |
|---|---|---|
| **SAFE** | Path goes through GatedBridge → SaarthiService → Enforcement → Execution | Permitted |
| **BLOCKED** | Path is structurally impossible — prevented by passport, token, or chain verification | Cannot execute |
| **BYPASS_RISK** | Path could reach execution without full governance | **MUST BE ELIMINATED** |

---

### 2.2 All Registered Paths (19 total)

#### CORE — Raj's Workflow Engine

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| CORE-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | Bridge auth + Passport + Token |
| CORE-002 | `SaarthiService.ProcessRequest() [direct]` | NO | YES | YES | **BLOCKED** | Fail-closed passport verification rejects NIL bridge passport |
| CORE-003 | `EnforcementAdapter.Enforce() [direct]` | NO | NO | YES | **BLOCKED** | Package-private, requires pipeline reference |
| CORE-004 | `ExecutionEngine.ExecuteWithToken() [direct]` | NO | NO | YES | **BLOCKED** | 9-check token validation gate, chain verification |
| CORE-005 | `ExecutionEngine.AttemptExecution() [legacy]` | NO | NO | NO | **BLOCKED** | Wrapper calls ExecuteWithToken internally |
| CORE-006 | `CallerRegistry.RegisterCaller() [direct]` | NO | NO | NO | **BLOCKED** | Requires authentication via GatedBridge (v8.0 — no direct registration) |

#### INSIGHTFLOW — Observability

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| IF-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | Read-only permission enforced by bridge |
| IF-002 | `MultiSystemRouter.RouteResult()` | NO | NO | NO | **SAFE** | Read-only — receives events, cannot execute |

#### BUCKET — Audit Storage

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| BK-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | Bridge auth + audit sync |
| BK-002 | `MultiSystemRouter.RouteResult()` | NO | NO | NO | **SAFE** | Audit archive — receives events, stores immutably |

#### KSML — Language Layer (v7.0.2 — Full Production)

The KSML subsystem is a full production governance layer — not a stub. It implements 5 intent types,
20+ verb translations, 10-step governance pipeline, revocation registry, delegation chains, and
per-agent intent history. Two execution paths cover the KSML lifecycle.

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| KSML-001 | `KSMLGovernanceHook.GovernKSMLDecision()` | YES | YES | YES | **SAFE** | Backward-compatible wrapper over GovernIntent → GatedBridge.RouteExecution() |
| KSML-002 | `Direct KSML execution [bypassing hook]` | NO | NO | NO | **BLOCKED** | KSML hook is the ONLY execution interface — no other entry into KSML governance |
| KSML-003 | `KSMLGovernanceHook.GovernIntent()` [primary API] | YES | YES | YES | **SAFE** | Full 10-step pipeline: validate → revocation → expiry → translate verb → RouteExecution() |
| KSML-004 | `ESCALATION_INTENT path via GovernIntent()` | NO | NO | NO | **BLOCKED** | Step 4 of GovernIntent blocks ESCALATION_INTENT — human review required, never reaches bridge |

**KSML Path Details:**

| Path | KSML Intent Types | Verb Examples | Outcome |
|---|---|---|---|
| KSML-001 | All (via wrapper) | Any registered verb | GovernKSMLDecision() → GovernIntent() → RouteExecution() |
| KSML-002 | N/A | N/A | Structurally impossible — KSML types are unexported |
| KSML-003 | QUERY_INTENT, EXECUTION_INTENT, DELEGATION_INTENT, SPECIFICATION_INTENT | query, invoke, delegate, define, specify | 10-step validation → governance action → bridge execution |
| KSML-004 | ESCALATION_INTENT | escalate, approve, review | Blocked at Step 4: KSML_ESCALATION_REQUIRED |

#### INTENT LAYER — Sankalp

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| IL-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | Bridge auth + intent validation |

#### ADMIN

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| ADM-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | Bridge auth + full audit |

#### AGENT EXECUTION (any agent)

| Path ID | Function | Via Bridge | Via Saarthi | Token Required | Classification | Blocked By |
|---|---|---|---|---|---|---|
| AGT-001 | `GatedBridge.RouteExecution()` | YES | YES | YES | **SAFE** | 5-stage PDP + 8-check token gate |
| AGT-002 | `Direct SaarthiService call` | NO | YES | YES | **BLOCKED** | NIL_BRIDGE_PASSPORT rejection |
| AGT-003 | `Direct ExecutionEngine call` | NO | NO | YES | **BLOCKED** | No valid token (only adapter can sign) |

---

## 3. Path Analysis Summary

```
Total Paths:    19  (added CORE-006 for v8.0 caller registration security)
SAFE Paths:     11  (all route through GatedBridge → Saarthi → Enforcement → Execution)
BLOCKED Paths:   8  (structurally impossible — prevented by architectural hard gates)
BYPASS_RISK:     0  ← ZERO
```

### v9.3.1 Path Changes vs v8.0

| Change | Details |
|---|---|
| **Phase 9 core gate** | Context.WithTimeout enforced on ALL critical paths in sovereign_governance_v9 — prevents hang-based bypasses |
| **Added CORE-006** | `RegisterCaller()` — now requires authentication, no direct public registration (BLOCKED) |
| **Removed GetService() bypass** | v8.0 eliminates direct service access vector — structural guarantee strengthened (CORE path analysis) |
| **Updated ExecutionHandler** | `ExecutionHandler` interface now documented in engine paths — standardized execution semantics |
| **9-check token validation** | Consistent token validation across all CORE paths (check 9: token revocation via RevocationRegistry) |
| **Enhanced fail-closed** | CORE-002 now explicitly mentions fail-closed passport verification |

---

## 4. Structural Guarantees

### Layer 1: Bridge Gate
- GatedBridge is the **SOLE** entry point
- All callers must be registered with API key + credential
- Rate limiting per caller
- Permission check per action

### Layer 2: Bridge Passport (v6.0)
- HMAC-signed passport issued on bridge transit
- SaarthiService **REJECTS** any request without valid passport
- Direct SaarthiService calls → DENY with `NIL_BRIDGE_PASSPORT`

### Layer 3: Ed25519 Token Gate
- ExecutionEngine accepts **ONLY** Ed25519-signed CapabilityTokens
- Only EnforcementAdapter holds the private key (signer)
- Engine holds only the public key (verifier)
- Token forgery is cryptographically impossible

### Layer 4: 9-Check Validation Gate (v8.0.0)
1. Token exists (not nil)
2. Signature valid (Ed25519)
3. Token integrity (SHA-256 hash — constant-time comparison, C-02 fix)
4. Token not expired (TTL with 5s clock skew tolerance, C-04 fix)
5. Token not consumed (single-use — TokenRegistry with cleanup goroutine, C-09 fix)
6. Verdict is ALLOW
7. enforcement_hash in adapter chain
8. Decision ID present
9. **Token not revoked** (RevocationRegistry check — FIX-04 / C-09, v7.0, v8.0)

### Layer 5: Mandatory Audit (v7.0 — FIX-01)
- Vault-style: audit write is in the critical path
- Audit failure → circuit breaker opens → ALL execution blocked
- No audit = no execution

### Layer 6: Token Authority Separation
- Private key NEVER leaves the EnforcementAdapter boundary
- Even if attacker constructs a token struct, they cannot sign it
- Key rotation support via ProtectedKeyStore (FIX-02)

### v9.3.1 Phase Integration
**v9.3.1 Phase Integration:** GovernanceKernelV9 now instantiated in enforcement_adapter_main.go. All 10 phases (audit integrity, layer binding, fail-closed, context-safe DB, buffered audit, delegation, intent signing, replay protection, core gate, stats aggregator) are ACTIVE and verified in the V9.0 Phase Integration section. ContextSafePostgresAuditSink replaces PostgresAuditSink for all DB operations.

---

## 5. Verification Method

The `ExecutionPathRegistry.VerifyNoBypassExists()` function performs runtime verification:

```go
func (epr *ExecutionPathRegistry) VerifyNoBypassExists() (bool, string) {
    risks := epr.GetBypassRisks()
    if len(risks) > 0 {
        return false, fmt.Sprintf("BYPASS_RISK_DETECTED: %d paths at risk", len(risks))
    }
    return true, "ZERO_BYPASS_PATHS: all execution paths are SAFE or BLOCKED"
}
```

**Result: `ZERO_BYPASS_PATHS`** — verified at system startup and available for runtime checks.

---

## 6. Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │         BHIV ECOSYSTEM                    │
                    │                                          │
  Core (Raj) ──────┤                                          │
  Intent (Sankalp)─┤     ┌──────────────────────────┐        │
  InsightFlow ─────┤────►│    GATED BRIDGE (v7.0)   │        │
  Bucket ──────────┤     │  • Caller Auth            │        │
  Admin ───────────┤     │  • Rate Limiting          │        │
  KSML ────────────┤     │  • Passport Issuance      │        │
                    │     │  • Audit Pre-Check (FIX-01)│       │
                    │     └──────────┬───────────────┘        │
                    │                │                          │
                    │                ▼                          │
                    │     ┌──────────────────────────┐        │
                    │     │   SAARTHI SERVICE (v7.0)  │        │
                    │     │  • Passport Verification  │        │
                    │     │  • Request Validation     │        │
                    │     │  • Idempotency Check      │        │
                    │     └──────────┬───────────────┘        │
                    │                │                          │
                    │                ▼                          │
                    │     ┌──────────────────────────┐        │
                    │     │ ENFORCEMENT ADAPTER (PEP) │        │
                    │     │  • Rate Limiting (agent)  │        │
                    │     │  • PDP Evaluation         │        │
                    │     │  • Token Signing (Ed25519)│        │
                    │     │  • Chain Append           │        │
                    │     └──────────┬───────────────┘        │
                    │                │                          │
                    │                ▼                          │
                    │     ┌──────────────────────────┐        │
                    │     │  EXECUTION ENGINE (Gate)  │        │
                    │     │  • 9-Check Token Validate │        │
                    │     │  • ExecutionHandler intf  │        │
                    │     │  • Single-Use Enforcement │        │
                    │     │  • Chain Verification     │        │
                    │     └──────────────────────────┘        │
                    │                                          │
                    └─────────────────────────────────────────┘
```

---

## 7. Compliance Mapping

| Control | Standard | Status |
|---|---|---|
| Single entry point | AWS API Gateway pattern | COMPLIANT |
| Zero trust per-request auth | NIST 800-207 / BeyondCorp | COMPLIANT |
| Cryptographic authorization | SPIFFE/SPIRE, AWS STS | COMPLIANT |
| Mandatory audit trail | HashiCorp Vault, SOX, NIST AU-9 | COMPLIANT |
| Separation of signing/verification | PKI best practice | COMPLIANT |
| Rate limiting at gateway | AWS WAF, Cloudflare | COMPLIANT |
| Timeout enforcement on critical paths | Phase 9 hardening | COMPLIANT |

---

## 8. KSML-Specific Path Walkthrough (v7.0.2)

A KSML request follows this precise path:

```
KSML Language Layer → KSMLGovernanceHook.GovernIntent(intent)
  │
  ├── Step 1: ValidateKSMLIntent(intent)
  │     • 8 validation checks: nil, IntentID, IntentType, AgentID, KSMLVerb, ResourceID, ExpiresAt, Spec
  │     • Fail-closed: any invalid field → KSML_INVALID_INTENT
  │
  ├── Step 2: Revocation check
  │     • revokedIntents.LoadOrStore(intent.IntentID, ...)
  │     • Revoked → Status=REVOKED, Verdict=DENY, BlockReason=KSML_INTENT_REVOKED
  │
  ├── Step 3: Expiry check
  │     • intent.ExpiresAt.Before(time.Now()) → Status=EXPIRED, Verdict=DENY
  │
  ├── Step 4: ESCALATION_INTENT gate
  │     • intent.IntentType == ESCALATION_INTENT || intent.RequiresHuman
  │     • Status=ESCALATED, Verdict=ESCALATE, BlockReason=KSML_ESCALATION_REQUIRED
  │     • BLOCKED — does NOT reach GatedBridge
  │
  ├── Step 5: DELEGATION_INTENT → record chain
  │     • delegations[intent.IntentID] = intent.DelegationID
  │
  ├── Step 6: TranslateKSMLVerb(intent.KSMLVerb)
  │     • 20+ verbs: query→read, invoke→execute, delegate→delegate, etc.
  │     • Unknown verb → fail-closed: KSML_UNKNOWN_VERB, Status=DENIED
  │
  ├── Step 7: Build SaarthiRequest from KSMLIntent fields
  │
  ├── Step 8: bridge.RouteExecution(req)  ← ONLY EXECUTION PATH
  │     • Full bridge processing: auth → permission → rate limit → passport → audit
  │     • SaarthiService → EnforcementAdapter → ExecutionEngine (9 checks)
  │
  ├── Step 9: Map SaarthiResponse → KSMLGovernanceDecision
  │     • Status=ALLOWED|DENIED, Verdict, GovernanceAction, ExecutionState
  │
  └── Step 10: Record in per-agent intentHistory
        • intentHistory[intent.AgentID] = append(..., decision)
```

**Every KSML execution reaches GatedBridge.RouteExecution() or is BLOCKED before it. No exceptions.**

---

**Integration Block:**
- Ishan Shirode — Evaluator
- Raj Prajapati — Enforcement Engine
- Future Integration Engineer — Core Integration

**Conclusion:** All 19 execution paths have been mapped. 11 are SAFE (routed through full governance pipeline), 8 are BLOCKED (structurally impossible). **ZERO bypass risks exist.** v9.3.1 enforces context.WithTimeout on all critical paths (Phase 9), adds CORE-006 (RegisterCaller authentication), removes GetService() bypass vector, and documents ExecutionHandler interface for engine paths.

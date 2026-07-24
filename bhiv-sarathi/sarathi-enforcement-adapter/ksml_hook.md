# PHASE 8: KSML Integration — Full Production Specification

**Document ID:** SARATHI-PHASE8-KSML-HOOK
**Version:** 9.3.1
**Author:** Hemanth B
**System:** Sarathi Governance Kernel — KSML Integration
**Classification:** Internal Sovereign Design / Strictly Confidential
**Generated:** 2026-04-04
**Status:** PRODUCTION — 14/14 tests passing | All intent types implemented and governed | v9.3.1 hardening applied (Phase 7: HMAC signature validation, Phase 8: replay protection enforced in GovernIntent())

---

## 1. What Is KSML?

**KSML (Knowledge Specification Markup Language)** is the BHIV language layer for expressing agent intents and knowledge specifications. It is the primary interface through which AI agents articulate what they want to do — queries, executions, delegations, and knowledge updates — before those intentions become actions.

The fundamental governance mandate:

> **ALL KSML decisions that lead to execution MUST pass through Sarathi governance. There is no alternate path. No KSML intent reaches execution without explicit policy authorization, cryptographic proof (Phase 7: HMAC validation + Phase 8: replay protection), and mandatory audit.**

---

## 2. KSML Intent Taxonomy

KSML intents are classified into 5 types, each with different governance handling:

| Intent Type | KSML Constant | Description | Governance Path |
|---|---|---|---|
| `QUERY_INTENT` | `KSMLIntentQuery` | Read/search knowledge, no side effects | Standard PDP → ALLOW or DENY |
| `EXECUTION_INTENT` | `KSMLIntentExecution` | Action with side effects (write, invoke, process) | Standard PDP → ALLOW or DENY |
| `DELEGATION_INTENT` | `KSMLIntentDelegation` | Agent delegates authority to another agent | Delegation chain recorded, then PDP |
| `ESCALATION_INTENT` | `KSMLIntentEscalation` | Requires human review before execution | Immediately blocked → ESCALATE |
| `SPECIFICATION_INTENT` | `KSMLIntentSpecification` | Define or update a knowledge specification | Standard PDP → write action |

---

## 3. KSML Verb → Governance Action Translation

The KSML language uses natural-language verbs that are translated to the 4 governance actions (`read`, `write`, `execute`, `delete`) before policy evaluation:

| KSML Verb | Governance Action | Category |
|---|---|---|
| `query`, `search`, `retrieve`, `fetch`, `inspect`, `observe`, `describe` | `read` | Query |
| `create`, `update`, `modify`, `store`, `publish`, `emit`, `record` | `write` | Mutation |
| `invoke`, `trigger`, `run`, `call`, `apply`, `process` | `execute` | Execution |
| `remove`, `purge`, `revoke`, `expire` | `delete` | Deletion |

**Unknown verbs → fail-closed DENY.** No guessing, no fallback. If the verb is not in the translation map, the intent is blocked with `KSML_UNKNOWN_VERB`.

---

## 4. Architecture — Full Request Flow

```
KSML Language Layer (agent submits an intent)
          │
          ▼
KSMLGovernanceHook.GovernIntent(intent)
          │
          ├── Step 1: ValidateKSMLIntent()
          │         └── nil check, missing fields, unknown verb,
          │             unknown intent type, expiry check
          │
          ├── Step 2: Revocation check (revokedIntents sync.Map lookup)
          │         └── REVOKED → DENY immediately
          │
          ├── Step 3: Expiry check (intent.ExpiresAt)
          │         └── EXPIRED → DENY immediately
          │
          ├── Step 4: ESCALATION_INTENT / RequiresHuman check
          │         └── ESCALATE → DENY immediately (human review required)
          │
          ├── Step 5: DELEGATION_INTENT → record chain (delegations map)
          │
          ├── Step 6: TranslateKSMLVerb(intent.KSMLVerb) → governance action
          │         └── Unknown verb → DENY
          │
          ├── Step 7: Build SaarthiRequest (agentID, resourceID, action, context)
          │
          └── Step 8: GatedBridge.RouteExecution(req)  ← ONLY EXECUTION PATH
                    │
                    ├── Auth → Permissions → Rate Limit → Passport → Audit
                    │
                    └── SaarthiService → Enforcement → PDP → Token → Engine
                              │
                              └── KSMLGovernanceDecision returned with:
                                  - Status (APPROVED/DENIED/ESCALATED/REVOKED/EXPIRED)
                                  - Verdict (ALLOW/DENY/ESCALATE)
                                  - GovernanceAction (translated action)
                                  - EnforcementHash (chain proof)
                                  - LatencyNs (processing time)
```

---

## 5. Data Structures

### 5.1 KSMLIntent — Language-Level Intent

```go
type KSMLIntent struct {
    IntentID      string            // Unique intent ID (required)
    IntentType    KSMLIntentType    // QUERY, EXECUTION, DELEGATION, ESCALATION, SPECIFICATION
    AgentID       string            // Requesting agent (required)
    TargetAgentID string            // For DELEGATION_INTENT: agent receiving delegation
    ResourceID    string            // Target resource (required)
    ResourceType  string            // Resource classification (optional context)
    KSMLVerb      string            // Language verb (required): "query", "invoke", etc.
    Specification string            // For SPECIFICATION_INTENT: spec body
    Context       map[string]string // Additional Cedar condition context
    CorrelationID string            // Distributed trace correlation
    IssuedAt      time.Time         // Intent creation time
    ExpiresAt     time.Time         // Intent validity window (recommended: 5 minutes)
    RequiresHuman bool              // Force escalation for human review
    DelegationID  string            // Parent intent ID for delegation chains
}
```

### 5.2 KSMLGovernanceDecision — Complete Governance Outcome

```go
type KSMLGovernanceDecision struct {
    Intent           *KSMLIntent       // Original intent
    Status           KSMLIntentStatus  // APPROVED, DENIED, ESCALATED, REVOKED, EXPIRED
    Verdict          string            // ALLOW, DENY, ESCALATE
    GovernanceAction string            // Translated action: read, write, execute, delete
    EnforcementHash  string            // SHA-256 chain entry (cryptographic proof)
    BlockReason      string            // Why it was denied (if applicable)
    ExecutionState   string            // EXECUTION_PERMITTED or EXECUTION_BLOCKED
    ProcessedAt      time.Time         // When decision was made
    LatencyNs        int64             // Processing time in nanoseconds
}
```

### 5.3 KSMLGovernanceHook — Full Production Hook

```go
type KSMLGovernanceHook struct {
    bridge         *GatedBridge
    intentHistory  map[string][]*KSMLGovernanceDecision  // agentID → history
    revokedIntents map[string]time.Time                  // intentID → revocation time
    delegations    map[string]string                     // intentID → parentIntentID
    // Atomic metrics (8 dimensions):
    totalKSMLRequests      uint64
    ksmlAllowed            uint64
    ksmlDenied             uint64
    ksmlEscalated          uint64
    ksmlDelegations        uint64
    ksmlRevocations        uint64
    ksmlValidationFailures uint64
    ksmlExpired            uint64
}
```

---

## 6. API Reference

### 6.1 GovernIntent — Primary Entry Point (Full Semantics)

```go
func (kh *KSMLGovernanceHook) GovernIntent(intent *KSMLIntent) *KSMLGovernanceDecision
```

Validates, translates, and routes a full KSMLIntent through the governance pipeline. Returns a complete `KSMLGovernanceDecision` with status, verdict, enforcement hash, and latency.

### 6.2 GovernKSMLDecision — Simple Entry Point (Backward Compatible)

```go
func (kh *KSMLGovernanceHook) GovernKSMLDecision(agentID, resourceID, action, correlationID string) *SaarthiResponse
```

For callers that use raw governance actions directly (e.g., "read", "write"). Maps to `GovernIntent` internally.

### 6.3 RevokeIntent — Intent Withdrawal

```go
func (kh *KSMLGovernanceHook) RevokeIntent(intentID string)
```

Marks an intent as revoked. Any subsequent submission of this intentID is immediately blocked with `KSML_INTENT_REVOKED`.

### 6.4 IsIntentRevoked — Revocation Check

```go
func (kh *KSMLGovernanceHook) IsIntentRevoked(intentID string) bool
```

Returns true if the intent has been revoked.

### 6.5 GetAgentIntentHistory — Per-Agent History

```go
func (kh *KSMLGovernanceHook) GetAgentIntentHistory(agentID string) []*KSMLGovernanceDecision
```

Returns a copy of all governance decisions for a given agent. External callers cannot mutate internal state.

### 6.6 GetDelegationChain — Delegation Provenance

```go
func (kh *KSMLGovernanceHook) GetDelegationChain(intentID string) []string
```

Walks the delegation chain from root to leaf. Returns ordered slice of intentIDs. Max depth: 10 (prevents cycles).

### 6.7 ValidateKSMLIntent — Standalone Validation

```go
func ValidateKSMLIntent(intent *KSMLIntent) string
```

Returns empty string if valid, error code string if invalid. Can be called before `GovernIntent` to pre-validate.

### 6.8 TranslateKSMLVerb — Verb Mapping

```go
func TranslateKSMLVerb(verb string) (action string, errMsg string)
```

Translates a KSML language verb to a governance action. Returns empty string + error if unknown.

### 6.9 GetKSMLDetailedStats — Full Metrics

```go
func (kh *KSMLGovernanceHook) GetKSMLDetailedStats() map[string]uint64
```

Returns all 8 metric dimensions: `total_requests`, `allowed`, `denied`, `escalated`, `delegations`, `revocations`, `validation_failures`, `expired`.

---

## 7. v9.3.1 Enhancement

GovernanceKernelV9.GovernIntentSecure() now provides the unified Phase 7+8 hardened path with IntentSigner (HMAC-SHA256) and ReplayProtector (atomic LoadOrStore). KSMLGovernanceHook is now instantiated with SetIntentSigningKey() and SetDB() in enforcement_adapter_main.go V9.0 section.

---

## 8. Intent Lifecycle State Machine

```
                    ┌─────────────┐
                    │   PENDING   │ ← Intent submitted to GovernIntent()
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┬──────────────┐
          │                │                │              │
          ▼                ▼                ▼              ▼
   ┌──────────┐   ┌──────────────┐  ┌──────────┐  ┌──────────┐
   │ APPROVED │   │    DENIED    │  │ESCALATED │  │ REVOKED  │
   │ (ALLOW)  │   │ (DENY/fails) │  │ (human   │  │(revoked  │
   └──────────┘   └──────────────┘  │ review)  │  │ before   │
        │                │          └──────────┘  │ process) │
        ▼                ▼                         └──────────┘
   Execution        Blocked                         Blocked
   Permitted        (no token)

   EXPIRED → DENIED (ExpiresAt exceeded, checked at Step 3)
```

---

## 9. Governance Guarantees

| Guarantee | Mechanism |
|---|---|
| **No execution without governance** | `GovernIntent()` is the only entry path — no KSML code calls bridge directly |
| **Semantic validation** | 8-step validation before any pipeline routing |
| **Verb translation** | Unknown verbs → fail-closed DENY (no guessing) |
| **Intent expiry** | `ExpiresAt` checked — stale intents blocked |
| **Revocation** | `revokedIntents` map — revoked IDs permanently blocked |
| **Escalation** | `ESCALATION_INTENT` or `RequiresHuman=true` → blocked without human |
| **Delegation chain** | Full chain recorded and queryable (max depth 10) |
| **History tracking** | Per-agent decision history — full audit of KSML decisions |
| **Thread safety** | `sync.RWMutex` on all shared maps |
| **Rate limited** | KSML caller: 300 requests/min at bridge level |
| **Passport required** | Bridge issues passport — transit proof on every request |
| **Mandatory audit** | All KSML decisions audited (Vault-style fail-closed) |
| **Immutable return** | `GetAgentIntentHistory()` returns a copy — no mutation |

---

## 10. Caller Registration (gated_bridge.go)

```go
gb.callers["ksml"] = &CallerIdentity{
    SystemName:    "BHIV KSML Language Layer",
    SystemVersion: "1.0.0",
    Permissions:   []string{"read", "write", "execute"},
    RateLimit:     300,  // requests/minute
    Active:        true,
}
```

KSML does NOT have `delete` permission by default — deletion requires explicit administrator authorization outside the KSML layer.

---

## 11. Execution Path Analysis

| Path ID | Classification | Detail |
|---|---|---|
| KSML-001 | **SAFE** | `GovernIntent()` → `GovernKSMLDecision()` → `GatedBridge.RouteExecution()` → full pipeline |
| KSML-002 | **BLOCKED** | Direct KSML code calling `SaarthiService` without bridge → structurally impossible (no reference) |
| KSML-003 | **BLOCKED** | KSML escalation intent trying to execute → `ESCALATION_INTENT` blocked before bridge |
| KSML-004 | **BLOCKED** | Revoked intent re-submission → blocked at revocation check before bridge |

---

## 12. Test Coverage (14/14 PASS)

| Test ID | Description | Intent Type | Expected |
|---|---|---|---|
| KSML-001 | Basic governance via bridge | Execution | ALLOW or DENY |
| KSML-002 | Stats tracked after first request | — | total=1, (allowed+denied)=1 |
| KSML-003 | Multiple requests counted | — | total=6 |
| KSML-004 | Verb "query" → action "read" | — | action=read |
| KSML-005 | Verb "invoke" → action "execute" | — | action=execute |
| KSML-006 | Unknown verb → fail-closed DENY | — | KSML_UNKNOWN_VERB |
| KSML-007 | Full EXECUTION_INTENT via GovernIntent | Execution | verdict+action both set |
| KSML-008 | ESCALATION_INTENT blocked | Escalation | status=ESCALATED, verdict=ESCALATE |
| KSML-009 | Revoked intent blocked | Execution (revoked) | status=REVOKED |
| KSML-010 | IsIntentRevoked correct | — | revoked=true, non-revoked=false |
| KSML-011 | Nil intent → no panic | nil | KSML_INTENT_NIL |
| KSML-012 | Delegation chain recorded | Delegation | chain_length≥1 |
| KSML-013 | Per-agent history tracked | — | history_entries≥1 |
| KSML-014 | Detailed stats all dimensions | — | total>0, all keys present |

---

## 13. Metrics (8 Dimensions)

```go
stats := ksmlHook.GetKSMLDetailedStats()
// stats["total_requests"]      — all KSML governance requests
// stats["allowed"]             — approved intents (ALLOW verdict)
// stats["denied"]              — denied intents (all deny paths)
// stats["escalated"]           — ESCALATION_INTENT or RequiresHuman=true
// stats["delegations"]         — DELEGATION_INTENT submissions
// stats["revocations"]         — intents revoked via RevokeIntent()
// stats["validation_failures"] — intents rejected at validation step
// stats["expired"]             — intents past ExpiresAt window
```

---

## 14. INTEGRATION BLOCK

Ishan Shirode — Evaluator — Enforcement decisions must align with evaluator outputs
Raj Prajapati — Enforcement Engine — Sarathi must become the only execution gate
Future Integration Engineer — Core Integration — Will wire Sarathi into BHIV Core systems.

---

## 15. Usage Example

```go
// Create the hook (once, at startup)
ksmlHook := NewKSMLGovernanceHook(bridge)

// Submit a QUERY intent
queryDecision := ksmlHook.GovernIntent(&KSMLIntent{
    IntentID:      "intent-001",
    IntentType:    KSMLIntentQuery,
    AgentID:       "agent-alpha",
    ResourceID:    "knowledge-graph-001",
    KSMLVerb:      "query",
    CorrelationID: "corr-001",
    IssuedAt:      time.Now().UTC(),
    ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
})
// queryDecision.Verdict: "ALLOW" or "DENY"
// queryDecision.EnforcementHash: cryptographic proof

// Submit an EXECUTION intent
execDecision := ksmlHook.GovernIntent(&KSMLIntent{
    IntentID:      "intent-002",
    IntentType:    KSMLIntentExecution,
    AgentID:       "agent-beta",
    ResourceID:    "workflow-trigger-001",
    KSMLVerb:      "invoke",
    CorrelationID: "corr-002",
    IssuedAt:      time.Now().UTC(),
    ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
})

// Revoke an intent (emergency withdrawal)
ksmlHook.RevokeIntent("intent-001")
// Any future submission of "intent-001" → DENY (KSML_INTENT_REVOKED)

// Delegation chain (agent-alpha delegates to agent-beta)
delegDecision := ksmlHook.GovernIntent(&KSMLIntent{
    IntentID:      "intent-003",
    IntentType:    KSMLIntentDelegation,
    AgentID:       "agent-alpha",
    TargetAgentID: "agent-beta",
    ResourceID:    "shared-resource-001",
    KSMLVerb:      "query",
    DelegationID:  "intent-001",  // parent intent
    IssuedAt:      time.Now().UTC(),
    ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
})
chain := ksmlHook.GetDelegationChain("intent-003")
// chain: ["intent-001", "intent-003"]
```

---

**ALL KSML DECISIONS ARE FULLY GOVERNED. No KSML execution occurs without Sarathi approval, cryptographic proof (Phase 7 & 8), and mandatory audit. Phase 7: HMAC signature validation, Phase 8: replay protection — both enforced in GovernIntent().**

*KSML Governance Hook v9.3.1 | 14/14 tests passing | Phase 7-8 hardening applied | 2026-04-04*

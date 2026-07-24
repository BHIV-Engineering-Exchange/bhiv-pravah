# SARATHI EVALUATION ORDER SPECIFICATION

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Task 4 — Sarathi PDP Minimal Implementation Specification (Day 3)  
**Upstream Dependencies:**  
- `sarathi_request_schema.md` (Task 4 — Day 1)  
- `sarathi_response_schema.md` (Task 4 — Day 2)  
- `SARATHI_PDP_INTERFACE.md` — 17-Step Evaluation Pipeline (Task 3)  
- `SARATHI_HIGH_DENSITY_CANON_FORMALIZATION.md` — 60 Canon Rules (Task 2)  
- `AMBIGUITY_RESOLUTION_SPEC.md` — 7 Global Principles, 14 Resolutions (Task 3)  
- Sarathi PDP Research Report — Constitutional Blueprint for Sovereign AI Governance

---

## PURPOSE

This document defines the **deterministic evaluation sequence** of the Sarathi PDP — the exact order in which the PDP processes every request, from raw bytes to signed verdict.

If the Request Schema (Day 1) defines WHAT the PDP receives, and the Response Schema (Day 2) defines WHAT the PDP returns, this Evaluation Order Specification defines HOW the PDP transforms input to output. It is the algorithm of governance.

This specification exists because **evaluation order is a security property**, not an implementation detail. Consider:

- If Eligibility Logic runs before Identity Validation, a spoofed identity can trigger eligibility checks that leak information about the policy.
- If Risk Gates run before Authority Validation, an expired token can reach the risk engine, consuming expensive computation.
- If Audit Write runs before the verdict is computed, a failed audit write cannot override the verdict to DENY.

Every stage order is derived from a security principle. Every short-circuit is derived from a fail-closed guarantee. Every conflict resolution is derived from GP-03 (Conflict Resolves to Restriction).

**Constitutional Authority:**
- **GP-03 (Conflict Resolves to Restriction):** DENY always overrides ALLOW.
- **GP-04 (Input Validity Is Security):** Input validation is the first barrier — before any policy evaluation.
- **GP-06 (Fail-Closed on Uncertainty):** Any stage that cannot complete resolves to DENY.
- **Saltzer & Schroeder's Economy of Mechanism:** The evaluation path is as simple and short as possible.
- **Saltzer & Schroeder's Complete Mediation:** Every request traverses every required stage.

**Industry Grounding:**
- OASIS XACML 3.0 Authorization Decision Flow (Section 7.17)
- NIST SP 800-162 ABAC evaluation model
- AWS Cedar evaluation model (deterministic, deny-overrides, formally verified in Lean 4)
- OPA/Rego evaluation (top-down, complete, with early termination on deny)
- Google Zanzibar check algorithm (namespace-config lookup → userset rewrite → checks)
- Task 3 PDP Interface 17-Step Pipeline (this document refines and locks that pipeline)

---

## TABLE OF CONTENTS

1. [Evaluation Invariants](#1-evaluation-invariants)
2. [The Seven Stages — Overview](#2-the-seven-stages--overview)
3. [Stage 1 — Identity Validation](#3-stage-1--identity-validation)
4. [Stage 2 — Lifecycle Validation](#4-stage-2--lifecycle-validation)
5. [Stage 3 — Authority Validation](#5-stage-3--authority-validation)
6. [Stage 4 — Eligibility Logic](#6-stage-4--eligibility-logic)
7. [Stage 5 — Risk Gates](#7-stage-5--risk-gates)
8. [Stage 6 — Refusal Classification](#8-stage-6--refusal-classification)
9. [Stage 7 — Audit Write](#9-stage-7--audit-write)
10. [Precedence Rules](#10-precedence-rules)
11. [Conflict Resolution Rules](#11-conflict-resolution-rules)
12. [Short-Circuit Logic](#12-short-circuit-logic)
13. [Evaluation Timing Constraints](#13-evaluation-timing-constraints)
14. [The Complete Evaluation Flowchart](#14-the-complete-evaluation-flowchart)


---

## 1. EVALUATION INVARIANTS

| Invariant ID | Property | Definition |
|:---:|---|---|
| **EVAL-01** | **Total Ordering** | The seven stages execute in strict sequence: 1→2→3→4→5→6→7. No stage may execute out of order. No parallel execution. The order is a security property. |
| **EVAL-02** | **Stage Isolation** | Each stage receives the original request (immutable) and produces a stage result (PASS, DENY, or ESCALATE). Stages do not modify the request or each other's results. |
| **EVAL-03** | **Fail-Closed Stages** | Every stage has exactly two outcomes: PASS (proceed) or TERMINAL (emit DENY/ESCALATE immediately). No "WARN and continue." No "degraded ALLOW." |
| **EVAL-04** | **Short-Circuit on DENY** | If any stage produces DENY, subsequent stages DO NOT execute (except Stage 7). Prevents information leakage from later stages. |
| **EVAL-05** | **Mandatory Audit** | Stage 7 (Audit Write) executes for EVERY verdict. Never skipped. If Stage 7 fails, pending ALLOW is overridden to DENY. |
| **EVAL-06** | **No Backtracking** | Once a stage completes, it is not re-evaluated. Each stage is evaluated once with information available at that point. |
| **EVAL-07** | **Deterministic Duration** | Every stage has a maximum execution time. Exceeding timeout → DENY with `ERR_EVALUATION_TIMEOUT`. Total budget: 50ms (p99). |
| **EVAL-08** | **Immutable Input** | The request envelope is read-only. No stage modifies, enriches, or transforms the request. The PDP evaluates what it received. |

---

## 2. THE SEVEN STAGES — OVERVIEW

### 2.1 Stage Mapping from Task 3 Pipeline

| Day 3 Stage | Task 3 Steps | Purpose |
|:---:|---|---|
| **Stage 1: Identity Validation** | Steps 1-4 (Schema), 5-8 (Token, Binding, Dedup) | Establish WHO with cryptographic certainty |
| **Stage 2: Lifecycle Validation** | Step 9 (Agent State) | Verify agent EXISTS and is ACTIVE |
| **Stage 3: Authority Validation** | Steps 10-11 (Delegation, Scope) | Verify agent has the RIGHT to act |
| **Stage 4: Eligibility Logic** | Steps 12-14 (Classification, SoD, Mutation) | Verify action is ELIGIBLE under policy |
| **Stage 5: Risk Gates** | Steps 15-16 (Velocity/Mosaic, Break Glass) | Verify action within RISK thresholds |
| **Stage 6: Refusal Classification** | Step 17 (Verdict assembly) | Classify and finalize the verdict |
| **Stage 7: Audit Write** | Post-pipeline | Record decision for accountability |

### 2.2 Why Seven Stages and Not Seventeen

- **17 steps** = implementation checklist (what to check).
- **7 stages** = evaluation contract (in what order, with what guarantees).

An engineer uses both: the 7 stages define the architecture; the 17 steps define the checks within each stage.

### 2.3 Pipeline Visualization

```
REQUEST ENVELOPE
     │
     ▼
┌─────────────────────────────┐
│  STAGE 1: IDENTITY          │ ── DENY → ─┐
│  (Schema + Crypto + Binding)│             │
└─────────────┬───────────────┘             │
              │ PASS                        │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 2: LIFECYCLE         │ ── DENY → ─┤
│  (Agent State)              │             │
└─────────────┬───────────────┘             │
              │ PASS                        │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 3: AUTHORITY         │ ── DENY → ─┤
│  (Delegation + Scope)       │             │
└─────────────┬───────────────┘             │
              │ PASS                        │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 4: ELIGIBILITY       │ ── DENY → ─┤
│  (Classification + SoD)     │             │
└─────────────┬───────────────┘             │
              │ PASS                        │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 5: RISK GATES        │ ── DENY → ─┤
│  (Velocity + Mosaic)        │             │
└─────────────┬───────────────┘             │
              │ PASS                        │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 6: REFUSAL           │ ── DENY → ─┤
│  CLASSIFICATION             │  ESCALATE → ┤
└─────────────┬───────────────┘             │
              │ ALLOW/DENY/ESCALATE         │
              ▼                             │
┌─────────────────────────────┐             │
│  STAGE 7: AUDIT WRITE       │ ◄───────────┘
│  (ALL paths converge here)  │
│  If write fails → DENY      │
└─────────────┬───────────────┘
              │
              ▼
       SIGNED VERDICT RETURNED
```

**Critical:** Every DENY short-circuit converges at Stage 7. No verdict is returned without an audit write attempt.

---

## 3. STAGE 1 — IDENTITY VALIDATION

### 3.1 Purpose

**Is this a well-formed request from a verifiable entity?**

### 3.2 Sub-Steps (Strict Order)

| Step | Check | Failure Result | Reference |
|:---:|---|---|---|
| **1.1** | Parse JSON | `ERR_MALFORMED_JSON` (400) | GP-04 |
| **1.2** | Schema validation (6 sections, types, additionalProperties: false) | `ERR_SCHEMA_VIOLATION` (400) | INV-01, INV-07 |
| **1.3** | Null/empty check (no "", null, "null", "none", "nil", "N/A") | `ERR_NULL_INPUT` (400) | RES-08 |
| **1.4** | Timestamp within [now - 5000ms, now + 1000ms] | `ERR_REPLAY_DETECTED` / `ERR_CLOCK_SKEW` (400) | INV-08 |
| **1.5** | Resource path canonical (no "..", "\x00", "%2F") | `ERR_PATH_TRAVERSAL` (400) | RES-11 |
| **1.6** | correlation_id not in DEDUP_WINDOW (60s) | `ERR_REPLAY_DETECTED` (400) | INV-09 |
| **1.7** | policy_version_hash matches PDP bundle | `ERR_POLICY_VERSION_MISMATCH` (409) | LS-15 |
| **1.8** | System state (CRL reachable, clock synced, bundle loaded) | `ERR_SYSTEM_UNCERTAINTY` (503) | GP-06, RES-04 |
| **1.9** | Token signature (Ed25519 against IdP key) | `ERR_TOKEN_INVALID` (401) | AC-22 |
| **1.10** | Token claims (sub==agent_id, exp valid, iss valid, jti unique) | `ERR_TOKEN_EXPIRED` / `ERR_IDENTITY_MISMATCH` (401) | AC-24, ID-01 |
| **1.11** | Channel binding (session_binding == SHA-256(TLS cert)) | `ERR_SESSION_BINDING` (401) | RES-09 |
| **1.12** | Payload < MAX_PAYLOAD (64KB) | `ERR_PAYLOAD_TOO_LARGE` (400) | GP-04 |

### 3.3 Design Rationale

**Syntactic checks (1.1-1.7) before cryptographic checks (1.8-1.11):** Crypto operations cost 10-50μs each. Schema validation costs 1-5μs. Running syntactic checks first rejects malformed requests at near-zero cost, preventing DoS via garbage requests that consume signature verification CPU. This is Economy of Mechanism applied to evaluation order.

**Channel binding (1.11) after token verification (1.9-1.10):** Binding requires a valid token to extract the `sub` claim. Verifying binding against an invalid token wastes computation.

---

## 4. STAGE 2 — LIFECYCLE VALIDATION

### 4.1 Purpose

**Does this agent currently exist in a valid operational state?**

A cryptographically valid token from a revoked agent must still be rejected.

### 4.2 Sub-Steps

| Step | Check | Failure Result | Canon Rule |
|:---:|---|---|---|
| **2.1** | Agent state lookup from State Registry | If lookup fails → `ERR_SYSTEM_UNCERTAINTY` (503) | GP-06 |
| **2.2** | Agent.State == ACTIVE | SUSPENDED → DENY (403) / REVOKED → DENY PERMANENT (403) / DEPRECATED → DENY new tasks (403) / TERMINATED → DENY PERMANENT (403) / Not found → DENY (GP-01) | LS-11, LS-12, LS-13, LS-14, LS-20 |
| **2.3** | All parents in delegation_chain are ACTIVE | Any parent REVOKED → DENY `ERR_CASCADING_REVOCATION` (403) | LS-19 |
| **2.4** | agent_class matches registered class | Mismatch → DENY `ERR_CLASS_MISMATCH` (403) | ID-03 |
| **2.5** | agent_class not in Forbidden Six | Forbidden → DENY `ERR_FORBIDDEN_CLASS` PERMANENT (403) | ID-05, ID-06, ID-07 |

### 4.3 Design Rationale

**Why lifecycle AFTER identity?** To look up state, we need a verified agent_id. Unverified IDs could: cause registry errors, leak another agent's state, or enumerate existing agent IDs.

---

## 5. STAGE 3 — AUTHORITY VALIDATION

### 5.1 Purpose

**Does this agent have the RIGHT to perform this specific action on this specific resource?**

### 5.2 Sub-Steps

| Step | Check | Failure Result | Canon Rule |
|:---:|---|---|---|
| **3.1** | Action within capability_token.scope | DENY `ERR_SCOPE_MISMATCH` (403) | AC-23 |
| **3.2** | Resource within capability_token.scope | DENY `ERR_SCOPE_MISMATCH` (403) | AC-23 |
| **3.3** | Delegation validation (if USER_PROXY) | DENY `ERR_PARTIAL_AUTHORITY` / `ERR_DELEGATION_VIOLATION` (403) | ID-08, RES-01 |
| **3.4** | Non-transitivity (delegation_token.aud == this agent) | DENY `ERR_DELEGATION_VIOLATION` (403) | RES-01 |
| **3.5** | Cross-tenant isolation | DENY `ERR_CROSS_TENANT_VIOLATION` (403) | AC-25 |
| **3.6** | Break-glass validation (if required by policy) | DENY `ERR_INSUFFICIENT_PROOF` (403) | AC-26, AC-27, RES-05 |

### 5.3 Design Rationale

**Why authority AFTER lifecycle?** A revoked agent should never reach authority checks. Running lifecycle first means revoked agents get generic `ERR_STATE_INVALID` — the attacker never learns whether their authority was valid.

**Non-transitivity (3.4) as separate check:** Per AMB-01/RES-01, delegation tokens must be ADDRESSED TO the bearer, not just POSSESSED BY the bearer. This is Hardy's Confused Deputy fix: the token must name this specific agent as its audience.

---

## 6. STAGE 4 — ELIGIBILITY LOGIC

### 6.1 Purpose

**Is this specific action ELIGIBLE under current policy constraints?**

Authority (Stage 3) = CAN the agent act. Eligibility (Stage 4) = SHOULD the action proceed.

### 6.2 Sub-Steps

| Step | Check | Failure Result | Canon Rule |
|:---:|---|---|---|
| **4.1** | Data classification cross-reference (declared vs. registry; actual > clearance → DENY) | DENY `ERR_DATA_CLASSIFICATION_EXCEEDED` (403) | AC-23 |
| **4.2** | Segregation of Duties (APPROVE action: Author ≠ Approver) | DENY `ERR_SOD_VIOLATION` (403) | EL-43, RES-12 |
| **4.3** | Runtime mutation block (agent modifying own state/rules → DENY) | DENY `ERR_RUNTIME_MUTATION` (403) | GP-07, LS-18 |
| **4.4** | BHIV Bucket immutability (DELETE on BHIV_BUCKET → DENY unconditionally) | DENY (405) | AI-53, RES-02 |
| **4.5** | Canon modification control (WRITE/DELETE on CANON_RULE → require quorum) | DENY `ERR_CANON_MODIFICATION_BLOCKED` (403) | AC-31, MF-04 |
| **4.6** | Class-specific restrictions (SUMMARIZER can't access CONFIDENTIAL, etc.) | DENY with class-specific reason | EL-36, AC-28, ID-10 |

### 6.3 Design Rationale

**Why eligibility AFTER authority?** If eligibility ran first, an unauthorized agent could learn about resource protections (e.g., BHIV Bucket is immutable) from the error code. Authority validation acts as a "need-to-know" gate.

---

## 7. STAGE 5 — RISK GATES

### 7.1 Purpose

**Even if authorized and eligible, does this action exceed acceptable risk thresholds?**

### 7.2 Sub-Steps

| Step | Check | Failure Result | Canon Rule |
|:---:|---|---|---|
| **5.1** | Velocity check (per-agent request rate) | DENY `ERR_RATE_LIMIT_EXCEEDED` (429) | EL-39 |
| **5.2** | Mosaic risk (≥3 data categories in 60s exceeding threshold) | DENY displayed as `ERR_RATE_LIMIT_EXCEEDED` (429) — NOT as mosaic detection per RES-03 | RES-03, EL-44 |
| **5.3** | Risk classification cross-reference (PDP vs. declared) | Flag anomaly in audit (currently informational) | EL-44 |
| **5.4** | Irreversibility gate (IRREVERSIBLE + CROSS_SERVICE/SYSTEM_WIDE + CONFIDENTIAL/RESTRICTED → require Safety Vote) | DENY `ERR_SAFETY_VOTE_REQUIRED` (403) | EL-42 |
| **5.5** | Temporal window (future — currently informational) | Log and pass | EL-41 (deferred) |

### 7.3 Design Rationale

**Why risk gates AFTER eligibility?** Risk gates are stateful (rate counters, mosaic accumulators). Running them only for authorized AND eligible requests prevents state pollution from invalid requests.

**Why Mosaic masked as rate limiting (5.2)?** Per RES-03: "The agent sees a rate limit, not an intelligence detection. This prevents threshold probing."

---

## 8. STAGE 6 — REFUSAL CLASSIFICATION

### 8.1 Purpose

**Assemble the final verdict from all prior stage results.**

### 8.2 Sub-Steps

| Step | Logic | Output |
|:---:|---|---|
| **6.1** | Combine all rule results via deny-overrides (Section 11) | ALLOW, DENY, or ESCALATE |
| **6.2** | Escalation detection (same-class mutual SUSPEND/TERMINATE per RES-13) | ESCALATE if detected |
| **6.3** | If ALLOW → generate capability token (Day 2, TI-01 through TI-14) | Token + obligations |
| **6.4** | If DENY → select highest-severity reason_code | Reason code + rules |
| **6.5** | If ESCALATE → create escalation case (id, deadline=15min, interim=DENY) | Escalation reference |

---

## 9. STAGE 7 — AUDIT WRITE

### 9.1 Purpose

**Record the decision to BHIV Bucket and verify success before releasing the verdict.**

### 9.2 Sub-Steps

| Step | Action | Failure Behavior |
|:---:|---|---|
| **7.1** | Construct BHIV audit record (Day 2, Section 5.2) | Internal error → override to DENY |
| **7.2** | Write to BHIV Bucket (append-only) | Write failure → see 7.4 |
| **7.3** | Verify write acknowledgment (AUDIT_WRITE_TIMEOUT: 200ms) | No ack → treat as failure |
| **7.4** | On failure: override verdict to DENY, set reason=AUDIT_WRITE_FAILED, write to emergency buffer, trigger NOTIFY_SECURITY | No ALLOW without audit |
| **7.5** | Sign response with Ed25519 | If HSM unavailable → unsigned DENY |

### 9.3 Design Rationale

**Why audit AFTER verdict but BEFORE delivery?** Ensures: (1) audit contains the actual verdict, (2) failed audit can override to DENY, (3) caller never receives unrecorded verdict.

**Why ALLOW overridden on audit failure?** An unauditable ALLOW is invisible to compliance, investigation, and revocation. A false DENY causes friction. Friction is recoverable; governance blind spots are not.

---

## 10. PRECEDENCE RULES

### 10.1 Rule Category Precedence

| Priority | Category | Override Behavior |
|:---:|---|---|
| **1 (Highest)** | SAFETY_CRITICAL | DENY overrides ALL ALLOW results |
| **2** | CORE | DENY overrides SUPPORTING ALLOW |
| **3 (Lowest)** | SUPPORTING | DENY still overrides ALLOW (GP-03 is absolute) |

### 10.2 Key Principle

Category precedence matters for **audit severity** (SAFETY_CRITICAL triggers alerts), not for **DENY/ALLOW resolution** — because GP-03 is unconditional: ANY DENY from ANY category wins over ANY ALLOW.

---

## 11. CONFLICT RESOLUTION RULES

### 11.1 Deny-Overrides Algorithm

```
FUNCTION combine(rule_results[]):
    has_deny = false; has_allow = false; has_escalate = false

    FOR EACH result IN rule_results:
        IF result == TRIGGERED_DENY:    has_deny = true
        IF result == TRIGGERED_ALLOW:   has_allow = true
        IF result == TRIGGERED_ESCALATE: has_escalate = true

    IF has_deny:     RETURN DENY      // GP-03: restriction wins
    IF has_escalate: RETURN ESCALATE  // Deferral > permission
    IF has_allow:    RETURN ALLOW     // Explicit permission
    RETURN DENY                       // GP-01: silence = denial
```

### 11.2 Conflict Scenarios

| Rule A | Rule B | Resolution | Rationale |
|---|---|---|---|
| ALLOW | DENY | **DENY** | GP-03 |
| ALLOW | ESCALATE | **ESCALATE** | More restrictive than ALLOW |
| DENY | ESCALATE | **DENY** | More restrictive than ESCALATE |
| ALLOW | ALLOW | **ALLOW** | Agreement |
| (none) | (none) | **DENY** | GP-01: silence = denial |

### 11.3 Why Deny-Overrides

- **First-applicable** depends on rule order — reordering changes verdict (maintenance hazard).
- **Permit-overrides** means any ALLOW wins — fail-OPEN (violates GP-03).
- **Only-one-applicable** returns Indeterminate — Sarathi has no Indeterminate.
- **Deny-overrides** is order-independent, fail-closed, and GP-03 aligned. AWS Cedar chose the same algorithm, formally verified in Lean 4.

---

## 12. SHORT-CIRCUIT LOGIC

| Rule | Statement | Rationale |
|:---:|---|---|
| **SC-01** | Stage N DENY → Stages N+1 through 6 skipped. Stage 7 always executes. | Earlier DENY is sufficient. Prevents leakage from later stages. |
| **SC-02** | Within a stage, sub-step DENY → remaining sub-steps skipped. | Economy of mechanism. |
| **SC-03** | Skipped stages recorded as `SKIPPED_SHORT_CIRCUIT` in determining_rules. | Audit completeness. |
| **SC-04** | Stage 7 (Audit) is NEVER skipped. | OUT-07: every verdict must be audited. |
| **SC-05** | Short-circuit reduces evaluation path but does NOT change the verdict. | Performance optimization with security benefit (leakage prevention), not semantic change. |

**Information Leakage Prevention:** Without short-circuit, an attacker can measure timing differences to identify which check failed. With short-circuit, all failures stop at approximately the same point.

---

## 13. EVALUATION TIMING CONSTRAINTS

| Parameter | Value | Rationale |
|---|---|---|
| Total Evaluation Budget | 50ms (p99) | Governance must not bottleneck agents |
| Stage 1 (Identity) | 15ms max | Schema ~2ms + signature ~5ms + system checks ~8ms |
| Stage 2 (Lifecycle) | 5ms max | Single registry lookup + chain check |
| Stage 3 (Authority) | 10ms max | Scope eval + delegation + break-glass |
| Stage 4 (Eligibility) | 8ms max | Classification cross-ref + SoD + mutation |
| Stage 5 (Risk) | 7ms max | Rate counter + mosaic + risk cross-ref |
| Stage 6 (Classification) | 3ms max | Combining + token generation |
| Stage 7 (Audit) | 2ms eval + 200ms write timeout | Audit write is synchronous, separate timeout |
| Evaluation Timeout | >50ms → DENY `ERR_EVALUATION_TIMEOUT` | Per EVAL-07: fail-closed on timeout |

---

## 14. THE COMPLETE EVALUATION FLOWCHART

```
                        REQUEST ENVELOPE ARRIVES
                                │
                ┌───────────────┴───────────────┐
                │   STAGE 1: IDENTITY            │
                │   1.1  Parse JSON              │
                │   1.2  Schema validation       │
                │   1.3  Null/empty check        │
                │   1.4  Timestamp validation    │
                │   1.5  Path canonicalization   │
                │   1.6  Deduplication           │
                │   1.7  Policy version check    │
                │   1.8  System state check      │
                │   1.9  Token signature         │
                │   1.10 Token claims            │
                │   1.11 Channel binding         │
                │   1.12 Payload size            │
                └───────────┬───────────────────┘
                            │
                    PASS?  ─┤── NO → DENY → Stage 7
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 2: LIFECYCLE           │
                │   2.1  Agent state lookup      │
                │   2.2  State validation        │
                │   2.3  Cascading revocation    │
                │   2.4  Class verification      │
                │   2.5  Forbidden class check   │
                └───────────┬───────────────────┘
                            │
                    PASS?  ─┤── NO → DENY → Stage 7
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 3: AUTHORITY           │
                │   3.1  Action scope check      │
                │   3.2  Resource scope check    │
                │   3.3  Delegation validation   │
                │   3.4  Non-transitivity        │
                │   3.5  Cross-tenant isolation  │
                │   3.6  Break-glass validation  │
                └───────────┬───────────────────┘
                            │
                    PASS?  ─┤── NO → DENY → Stage 7
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 4: ELIGIBILITY         │
                │   4.1  Classification check    │
                │   4.2  SoD enforcement         │
                │   4.3  Mutation block          │
                │   4.4  BHIV immutability       │
                │   4.5  Canon modification      │
                │   4.6  Class-specific rules    │
                └───────────┬───────────────────┘
                            │
                    PASS?  ─┤── NO → DENY → Stage 7
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 5: RISK GATES          │
                │   5.1  Velocity check          │
                │   5.2  Mosaic risk             │
                │   5.3  Risk cross-reference    │
                │   5.4  Irreversibility gate    │
                │   5.5  Temporal window         │
                └───────────┬───────────────────┘
                            │
                    PASS?  ─┤── NO → DENY → Stage 7
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 6: REFUSAL             │
                │   CLASSIFICATION               │
                │   6.1  Combine rule results    │
                │   6.2  Escalation detection    │
                │   6.3  Token gen (ALLOW)       │
                │   6.4  Denial classify (DENY)  │
                │   6.5  Escalation case (ESC)   │
                └───────────┬───────────────────┘
                            │
                  VERDICT: ALLOW / DENY / ESCALATE
                            │
                ┌───────────┴───────────────────┐
                │   STAGE 7: AUDIT WRITE         │
                │   7.1  Construct record        │
                │   7.2  Write BHIV Bucket       │
                │   7.3  Verify acknowledgment   │
                │   7.4  On failure → DENY       │
                │   7.5  Sign response           │
                └───────────┬───────────────────┘
                            │
                     SIGNED VERDICT RETURNED
```

---

## 15. Relationship to Previous Tasks


 

| Artifact | Relationship |
|---|---|
| **Task 1** | Addresses A4 (Atomic Evaluation — Stages 4-5 add stateful checks), A10 (Binary Classification — Stage 6 produces three-valued verdict) |
| **Task 2 (60 Rules)** | ID-01→ID-10 in Stages 1-2, LS-11→LS-20 in Stage 2, AC-21→AC-32 in Stage 3, EL-33→EL-44 in Stages 4-5, AI-53→AI-55 in Stage 7, RF-46→RF-51 in Stage 6 |
| **Task 3 (17-Step Pipeline)** | 17 steps nested within 7 stages (Section 2.1). This document elevates pipeline from checklist to architectural contract with invariants, short-circuits, and timing budgets. |
| **Task 3 (Ambiguity)** | RES-01 in Stage 3, RES-03 masked in Stage 5, RES-04 in Stage 1, RES-12 in Stage 4, RES-13 in Stage 6 |
| **Day 1 (Request Schema)** | Stage 1 validates Request Envelope. Stage 3 evaluates authority tokens. Stage 5 evaluates risk_classification. |
| **Day 2 (Response Schema)** | Stage 6 assembles Response Envelope. Stage 7 populates audit_id. determining_rules populated across Stages 3-6. |

---

**END OF SARATHI EVALUATION ORDER SPECIFICATION**

---

## 11. EXTENDED EVALUATION SUB-STEPS (GAP RESOLUTION PHASE)

*Added to integrate runtime enforcement (Gap 1), delegation tokens (Gap 2), and audit integrity (Gap 5) into the evaluation pipeline.*

### 11.1 Stage 1 — Extended: Delegation Token Validation

The following sub-steps are added to Stage 1 (Identity Validation) AFTER session binding (sub-step 1.11):

| Sub-Step | Check | Canon Rule | Fail Action |
|---|---|---|---|
| **1.12** | Validate Biscuit token structure and Ed25519 root signature | AC-22 | DENY (ERR_TOKEN_INVALID) |
| **1.13** | Verify DPoP proof: signature matches agent key, `ath` matches Biscuit hash, SPIFFE ID matches workload attestation | RES-09, ENF-11 | DENY (ERR_PROOF_INVALID) |
| **1.14** | Check delegation depth: `current_depth <= max_delegation_depth` from authority block | RES-15 (AMB-15) | DENY (ERR_DELEGATION_DEPTH_EXCEEDED) |
| **1.15** | Verify Biscuit revocation ID not in revocation list | LS-15 | DENY (ERR_TOKEN_REVOKED) |
| **1.16** | Verify `data_classification_ceiling` propagation from parent token | RES-16 (AMB-16) | DENY (ERR_CLASSIFICATION_EXCEEDED) |

### 11.2 Stage 5 — Extended: Circuit Breaker State Check

Added to Stage 5 (Risk Gates) AFTER velocity check (sub-step 5.1):

| Sub-Step | Check | Invariant | Fail Action |
|---|---|---|---|
| **5.1c** | Verify agent-level circuit breaker state is CLOSED or HALF-OPEN | ENF-12 | DENY (ERR_CIRCUIT_OPEN) if OPEN |
| **5.1d** | Verify tenant-level circuit breaker state is CLOSED | ENF-14 (RES-20) | DENY (ERR_TENANT_CIRCUIT_OPEN) if OPEN |
| **5.6** | Check accumulated cost against Biscuit `max_cost` caveat | AC-29, GP-08 | DENY (ERR_COST_EXCEEDED) |
| **5.7** | Check shutdown deadline against Biscuit `shutdown_deadline` | AC-32 | DENY (ERR_SHUTDOWN_EXPIRED) |

### 11.3 Stage 7 — Extended: Hash Chain Audit Integrity

The following sub-steps replace/extend the audit write in Stage 7:

| Sub-Step | Action | Integrity Guarantee |
|---|---|---|
| **7.1b** | PII scrub via `scrub_pii()` (AI-56) | HMAC-SHA256 pseudonymization |
| **7.1c** | Compute `prev_event_hash` from last written event | Hash chain continuity |
| **7.1d** | Compute `current_event_hash = sha256(audit_record + prev_event_hash)` | Tamper evidence |
| **7.1e** | Add JA3/JA4 TLS fingerprint from request context to `network` block | Device identification |
| **7.2** | Write to BHIV Bucket with timeout (200ms) | Append-only |
| **7.2b** | If hourly batch boundary crossed: construct Merkle tree, HSM-sign root | Batch integrity |
| **7.3** | On write failure: emergency buffer with separate hash chain (RES-19) | Split-brain recovery |
| **7.3b** | On BHIV recovery: write MERGE_EVENT bridging both chains | Chain reconciliation |

### 11.4 Updated Timing Budget

| Stage | Original Budget | Extended Budget | Added Sub-Steps |
|---|---|---|---|
| Stage 1 | 5ms | 7ms | +1.12-1.16 (Biscuit + DPoP validation) |
| Stage 5 | 15ms | 17ms | +5.1c-5.7 (circuit breaker + cost + deadline) |
| Stage 7 | 5ms + 200ms timeout | 5ms + 200ms timeout | +7.1c-7.3b (hash chain + Merkle) |
| **Total** | **50ms p99** | **54ms p99** | Within acceptable margin |

---

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Evaluation Stages | 7 |
| Total Sub-Steps | 52 (41 original + 11 from gap resolution) |
| Evaluation Invariants | 8 |
| Precedence Levels | 3 (SAFETY_CRITICAL > CORE > SUPPORTING) |
| Conflict Scenarios | 5 |
| Short-Circuit Rules | 5 |
| Timing Budgets | 7 stages + total + audit timeout |
| Canon Rules Mapped | All 60 rules assigned to stages |
| Global Principles | GP-01, GP-03, GP-04, GP-06, GP-07, GP-08, GP-09 |
| Ambiguity Resolutions | RES-01 through RES-14 + RES-15 through RES-20 |
| Industry Standards | XACML 3.0, NIST SP 800-162, AWS Cedar, OPA/Rego, Google Zanzibar, NIST SP 800-207, DeepMind DCT, Biscuit, SPIFFE/SPIRE, RFC 9449, EU AI Act Art. 12 |

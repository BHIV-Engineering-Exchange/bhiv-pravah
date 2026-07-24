# SARATHI RESPONSE SCHEMA — MINIMAL OUTPUT CONTRACT

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Task 4 — Sarathi PDP Minimal Implementation Specification (Day 2)  
**Upstream Dependencies:**  
- `sarathi_request_schema.md` (Task 4 — Day 1)  
- `GOVERNANCE_VALIDATION_REPORT.md` (Task 1)  
- `SARATHI_HIGH_DENSITY_CANON_FORMALIZATION.md` (Task 2)  
- `AMBIGUITY_REGISTER.md` / `AMBIGUITY_RESOLUTION_SPEC.md` / `SARATHI_PDP_INTERFACE.md` (Task 3)  
- Sarathi PDP Research Report — Constitutional Blueprint for Sovereign AI Governance

---

## PURPOSE

This document defines the **Sarathi Response Envelope** — the exact, minimal, non-negotiable data structure that the Sarathi PDP returns after evaluating every request. It constitutes the **output contract** of the Action Authorization Boundary (AAB).

If the Request Schema (Day 1) defines what the PDP demands, this Response Schema defines what the PDP promises. Together they form a complete, bilateral contract: the caller sends a valid Request Envelope; the PDP returns a signed Verdict Envelope. No other interaction pattern exists.

This document specifies:
- **What MUST be in every response** — the structural guarantee.
- **What appears only under specific verdicts** — conditional fields for ALLOW, DENY, and ESCALATE.
- **What must NEVER appear in any response** — the information leakage prohibition.
- **How responses are cryptographically signed** — the tamper-evidence guarantee.
- **How responses feed the audit trail** — the accountability guarantee.

**Constitutional Authority:**
- **GP-03 (Conflict Resolves to Restriction):** DENY overrides ALLOW in all conflict scenarios.
- **GP-05 (Observation ≠ Verification):** Responses reveal minimum information to prevent adversarial learning.
- **GP-06 (Fail-Closed on Uncertainty):** Indeterminate evaluation = DENY, never "not applicable."
- **Canon Rules:** AI-53 (Write-Only Audit), AI-54 (Audit Completeness), AI-55 (Audit Integrity), AC-21 (Zero Trust Default), EL-42 (Safety Voting), EL-43 (Segregation of Duties).

**Industry Grounding:**
- OASIS XACML 3.0 Response Context model (Decision, Obligations, Advice, Status)
- NIST SP 800-162 PDP response attributes
- OPA Decision Log format (decision_id, input hash, result, timestamp)
- AWS Cedar authorization response (ALLOW/DENY with determining policies)
- Google Zanzibar check response (allowed: boolean, zookie consistency token)
- RFC 9449 (DPoP) proof-of-possession for issued tokens
- XACML Obligations/Advice model for post-decision enforcement directives

---

## TABLE OF CONTENTS

1. [Output Invariants](#1-output-invariants)
2. [Response Envelope — Complete Schema Definition](#2-response-envelope--complete-schema-definition)
3. [Verdict Semantics — The Three Decisions](#3-verdict-semantics--the-three-decisions)
4. [Rule References — What Triggered the Decision](#4-rule-references--what-triggered-the-decision)
5. [Audit Payload Structure](#5-audit-payload-structure)
6. [Token Issuance Rules — ALLOW Only](#6-token-issuance-rules--allow-only)
7. [Escalation Protocol — ESCALATE Only](#7-escalation-protocol--escalate-only)
8. [What Must NEVER Be Included — The Prohibition List](#8-what-must-never-be-included--the-prohibition-list)
9. [Response Signing and Verification](#9-response-signing-and-verification)
10. [Verdict-to-HTTP Mapping](#10-verdict-to-http-mapping)


---

## 1. OUTPUT INVARIANTS

These properties are axiomatic for every response the PDP produces. They mirror the input invariants from Day 1 and complete the bilateral contract.

| Invariant ID | Property | Definition | Violation Consequence |
|:---:|---|---|---|
| **OUT-01** | **Totality** | Every request produces exactly one response. No silent drops. A PDP that drops requests creates a fail-open vulnerability (caller may assume timeout = ALLOW). | Architectural invariant — if evaluation fails, emit DENY response, not silence. |
| **OUT-02** | **Determinism** | Same request + same policy state + same system state = same verdict. Always. No randomness. No sampling. No probabilistic decisions. | Architectural invariant — non-determinism in governance is indistinguishable from adversarial behavior. |
| **OUT-03** | **Completeness** | Every response contains the `verdict` field. Even error responses carry `verdict: "DENY"`. There is no response shape without a verdict. | Structural invariant — callers MUST receive an explicit decision. |
| **OUT-04** | **Signed** | Every response carries an Ed25519 signature over the entire response body. Unsigned or tampered responses MUST be treated as DENY by the caller. Per Canon Section 6.9: "Never Ignore the Signature." | Per Canon operational parameter: `VERDICT_SIGNATURE_ALG: Ed25519`. |
| **OUT-05** | **Minimality** | Responses contain the minimum information required for the caller to act. No explanations. No suggestions. No alternative paths. | Per GP-05: excess information enables adversarial learning. |
| **OUT-06** | **Non-Negotiability** | The verdict is final for this request. No "appeal" endpoint. No "reconsider" API. DENY is DENY. Caller may submit a NEW request with DIFFERENT evidence. | Output-side corollary of INV-05 (Non-Negotiation from Day 1). |
| **OUT-07** | **Audit-Coupled** | Every response has a corresponding audit record in the BHIV Bucket. The `audit_id` is the key to that record. If audit write fails, verdict = DENY regardless of evaluation outcome. | Per AI-53, AI-54, AI-55: unauditable decisions are ungovernable. |
| **OUT-08** | **Temporally Bounded** | ALLOW verdicts are valid for max 60 seconds. They do not persist. They cannot be cached. Per Canon Section 6.5: "Never Cache ALLOW Verdicts." | Per MF-05: token TTL is 60 seconds maximum. Not configurable upward. |
| **OUT-09** | **Three-Valued** | Verdict is one of exactly three values: ALLOW, DENY, ESCALATE. There is no INDETERMINATE. No NOT_APPLICABLE. No PENDING. Per GP-01: if no rule explicitly ALLOWs, result is DENY. Per GP-06: if evaluation cannot complete, result is DENY. ESCALATE exists only for RES-13 (mutual same-class agent suspension). | XACML allows Indeterminate/NotApplicable. Sarathi collapses all ambiguity to three deterministic outcomes. |
| **OUT-10** | **Immutable Once Signed** | Once signed and returned, the verdict cannot be modified, retracted, or amended. If the PDP discovers an error after issuance, it must revoke the issued capability token through the CRL — not modify the response retroactively. | Immutability guarantees that audit records match actual decisions. |

---

## 2. RESPONSE ENVELOPE — COMPLETE SCHEMA DEFINITION

```json
{
  "$schema": "https://sarathi.governance/v1/response-envelope.json",
  "$id": "sarathi-response-envelope-v1.0.0",
  "title": "Sarathi PDP Response Envelope",
  "description": "The verdict issued by the Sarathi PDP for a single Request Envelope. This is the ONLY output the PDP produces. There are no side-channel responses, no partial verdicts, and no deferred notifications.",
  "type": "object",
  "required": [
    "verdict",
    "correlation_id",
    "audit_id",
    "timestamp",
    "evaluation_duration_ms",
    "pdp_instance",
    "policy_version_hash",
    "determining_rules",
    "signature"
  ],
  "additionalProperties": false,

  "properties": {

    "verdict": {
      "type": "string",
      "enum": ["ALLOW", "DENY", "ESCALATE"],
      "description": "The singular, authoritative governance decision. See Section 3 for exact semantics of each value."
    },

    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Echoed from the request. Links this response to its originating request and downstream execution. The audit thread anchor."
    },

    "audit_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for the audit record written to the BHIV Bucket for this decision. Callers can use this to retrieve the full audit trail entry. Generated by the PDP — never by the caller."
    },

    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 UTC timestamp of when the PDP rendered the verdict. Used for audit sequencing, latency measurement (compare against request_timestamp), and token expiry calculation."
    },

    "evaluation_duration_ms": {
      "type": "number",
      "minimum": 0,
      "description": "Wall-clock time in milliseconds from request receipt to verdict rendering. Included for operational monitoring — not for authorization decisions. Enables SLO enforcement (target: p99 < 50ms) and anomaly detection (unusually long evaluations may indicate complex policy traversal or system strain)."
    },

    "pdp_instance": {
      "type": "string",
      "minLength": 1,
      "description": "Identifier of the specific PDP instance that rendered this verdict. Required for: (1) debugging — trace which instance produced an unexpected result, (2) incident response — isolate a compromised or misconfigured instance, (3) audit — prove which PDP version and configuration were active. Format: hostname or pod identifier."
    },

    "policy_version_hash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of the policy bundle used for this evaluation. This is the PDP's declaration of which rules it applied. If this differs from the request's policy_version_hash, the request was rejected with ERR_POLICY_VERSION_MISMATCH (see Day 1). For successful evaluations, these hashes MUST match. Enables retroactive audit: given any historical decision, you can reconstruct exactly which policy version produced it."
    },

    "determining_rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule_id", "rule_name", "evaluation_result", "category"],
        "additionalProperties": false,
        "properties": {
          "rule_id": {
            "type": "string",
            "pattern": "^(ID|LS|AC|EL|AI|RF|BN)-[0-9]{2}$",
            "description": "Canon Rule identifier (e.g., AC-21, ID-08, EL-42). Maps directly to the Master Rule Inventory from Task 2."
          },
          "rule_name": {
            "type": "string",
            "description": "Human-readable rule name (e.g., 'Zero Trust Default', 'Delegation Token Requirement'). For audit readability."
          },
          "evaluation_result": {
            "type": "string",
            "enum": ["TRIGGERED_DENY", "TRIGGERED_ALLOW", "TRIGGERED_ESCALATE", "NOT_APPLICABLE", "SKIPPED_SHORT_CIRCUIT"],
            "description": "What this specific rule contributed to the final verdict."
          },
          "category": {
            "type": "string",
            "enum": ["CORE", "SAFETY_CRITICAL", "SUPPORTING"],
            "description": "Rule priority classification from Canon Task 2."
          }
        }
      },
      "minItems": 1,
      "description": "Ordered list of Canon rules that participated in this verdict. See Section 4 for full specification. Minimum 1 rule: even an ALLOW must cite at least one permitting rule. A verdict without rule references is structurally invalid — it would mean the PDP rendered a decision without consulting policy."
    },

    "reason_code": {
      "type": "string",
      "description": "PRESENT ONLY ON DENY AND ESCALATE. Machine-readable code identifying the primary reason. Per Canon Section 6.4: callers must NOT use reason_code for control flow. It is for logging and debugging only. Using it for branching logic constitutes adversarial probing behavior."
    },

    "capability_token": {
      "type": "string",
      "description": "PRESENT ONLY ON ALLOW. A signed, time-bounded, scope-restricted JWT that the caller presents to the downstream resource to execute the authorized action. See Section 6 for complete issuance rules. On DENY or ESCALATE: this field is absent (not null, not empty — absent)."
    },

    "obligations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["obligation_id", "obligation_type", "parameters"],
        "additionalProperties": false,
        "properties": {
          "obligation_id": {
            "type": "string",
            "description": "Unique identifier for this obligation instance."
          },
          "obligation_type": {
            "type": "string",
            "enum": [
              "LOG_ACCESS",
              "NOTIFY_SECURITY",
              "RATE_LIMIT_APPLY",
              "ENHANCED_AUDIT",
              "TIME_BOUND_RESTRICT",
              "HUMAN_REVIEW_REQUIRED"
            ],
            "description": "Category of post-decision enforcement directive. Per XACML: obligations are MANDATORY — the PEP must fulfill them or treat the verdict as DENY."
          },
          "parameters": {
            "type": "object",
            "description": "Obligation-specific parameters (e.g., retention period for LOG_ACCESS, rate limit values for RATE_LIMIT_APPLY)."
          }
        }
      },
      "description": "CONDITIONAL. Present when the verdict carries mandatory post-decision enforcement directives. Per XACML Obligations model: if the PEP cannot fulfill an obligation, it MUST treat the verdict as DENY. This is how the PDP extends enforcement beyond the binary ALLOW/DENY — an ALLOW with obligations means 'allowed IF you also do these things.'"
    },

    "escalation_reference": {
      "type": "object",
      "required": ["escalation_id", "escalation_target", "escalation_deadline", "interim_verdict"],
      "additionalProperties": false,
      "properties": {
        "escalation_id": {
          "type": "string",
          "format": "uuid",
          "description": "Unique tracking ID for this escalation case."
        },
        "escalation_target": {
          "type": "string",
          "enum": ["GOVERNANCE_COUNCIL", "SECURITY_TEAM", "HUMAN_OPERATOR"],
          "description": "Who must resolve this escalation."
        },
        "escalation_deadline": {
          "type": "string",
          "format": "date-time",
          "description": "ISO-8601 UTC timestamp by which the escalation must be resolved. If unresolved by deadline, the interim_verdict becomes permanent. Default: 15 minutes."
        },
        "interim_verdict": {
          "type": "string",
          "enum": ["DENY"],
          "description": "The verdict that applies while the escalation is pending. This is ALWAYS DENY. Per GP-06: uncertainty during escalation = fail-closed. The agent cannot act while the escalation is unresolved."
        }
      },
      "description": "PRESENT ONLY ON ESCALATE. See Section 7 for full protocol. The interim_verdict is hardcoded to DENY — there is no scenario where an unresolved escalation permits action."
    },

    "signature": {
      "type": "string",
      "description": "Ed25519 signature over the canonical JSON serialization of all other fields in this response (excluding the signature field itself). The caller MUST verify this signature using the PDP's public key before acting on the verdict. An unverified response MUST be treated as DENY. See Section 9."
    }
  }
}
```

---

## 3. VERDICT SEMANTICS — THE THREE DECISIONS

### 3.1 ALLOW — Conditional Permission

**Meaning:** The PDP has determined that the requesting agent, with the presented authority, is permitted to perform the specified action on the specified resource under the current conditions.

**ALLOW is never unconditional.** Every ALLOW carries:
1. A **capability token** that is the physical key to execution (without it, the downstream resource rejects).
2. A **time boundary** — the token expires in ≤60 seconds.
3. A **scope boundary** — the token is valid only for the exact action, resource, and parameters_hash authorized.
4. **Zero or more obligations** — mandatory post-decision directives the PEP must fulfill.

**ALLOW does NOT mean:**
- The payload is safe to execute (Sarathi checks authorization, not sanitization — per Canon Section 6.2).
- The action will succeed (the downstream resource may be unavailable, the data may not exist).
- Future requests will also be allowed (permissions are ephemeral, evaluated per-request).
- The agent is "trusted" (Zero Trust means every request is evaluated independently).

**When ALLOW is produced:**
1. All 17 steps of the evaluation pipeline pass (from Task 3 PDP Interface Spec).
2. At least one Canon rule explicitly permits the action (ALLOW is never default — GP-01).
3. No SAFETY_CRITICAL rule triggers DENY (deny-overrides combining per GP-03).
4. The audit write to BHIV Bucket succeeds (per OUT-07).

**ALLOW Response Shape:**

```json
{
  "verdict": "ALLOW",
  "correlation_id": "a1b2c3d4-...",
  "audit_id": "aud-7f8e9d0c-...",
  "timestamp": "2026-02-26T10:30:01.234Z",
  "evaluation_duration_ms": 3.7,
  "pdp_instance": "pdp-east-1a-003",
  "policy_version_hash": "sha256:abcdef1234567890...",
  "determining_rules": [
    {
      "rule_id": "AC-23",
      "rule_name": "Scope Confinement",
      "evaluation_result": "TRIGGERED_ALLOW",
      "category": "CORE"
    }
  ],
  "capability_token": "<signed_jwt>",
  "obligations": [
    {
      "obligation_id": "obl-001",
      "obligation_type": "LOG_ACCESS",
      "parameters": { "retention_days": 90 }
    }
  ],
  "signature": "<ed25519_signature>"
}
```

---

### 3.2 DENY — Unconditional Refusal

**Meaning:** The PDP has determined that the requesting agent is NOT permitted to perform the specified action. The denial is absolute, immediate, and non-negotiable for this request.

**DENY is the default.** Per GP-01 (Silence Implies Denial) and AC-21 (Zero Trust Default): if the PDP cannot affirmatively confirm that every condition for ALLOW is met, the answer is DENY. DENY requires no justification — ALLOW requires justification.

**DENY carries:**
1. A **reason_code** for logging/debugging (NOT for control flow — Canon Section 6.4).
2. The **determining_rules** that triggered the denial.
3. The **audit_id** linking to the full BHIV Bucket record.
4. **No capability token** (field is absent, not null).
5. **No remediation hints** (per GP-05: do not teach the attacker).

**When DENY is produced:**
1. Any of the 7 pre-policy validation stages fails (Day 1, Section 5).
2. Any cryptographic validation fails (token signature, expiry, issuer, subject match).
3. Any SAFETY_CRITICAL Canon rule triggers denial.
4. Any rule conflict where one rule says ALLOW and another says DENY (GP-03: DENY wins).
5. Policy evaluation produces no applicable ALLOW rule (GP-01: silence = DENY).
6. Audit write fails (OUT-07: unauditable = DENY).
7. Any system uncertainty (CRL stale, clock desync, dependency unavailable — GP-06).

**DENY Reason Codes (Complete Registry):**

| Reason Code | Trigger | Canon Reference | Severity |
|---|---|---|---|
| `SCHEMA_VIOLATION` | Pre-policy validation failure (Day 1 Stages 1-5) | GP-04, EL-33 | WARN |
| `TOKEN_INVALID` | Capability token signature verification failed | AC-22 | ERROR |
| `TOKEN_EXPIRED` | Capability token past expiry time | AC-24 | WARN |
| `IDENTITY_MISMATCH` | agent_id ≠ capability_token.sub | ID-01 | ERROR |
| `SESSION_BINDING_FAILED` | session_binding ≠ TLS client cert hash | RES-09 | ERROR |
| `SCOPE_MISMATCH` | Requested action/resource outside token scopes | AC-23 | WARN |
| `STATE_INVALID` | Agent state is not ACTIVE (SUSPENDED/REVOKED/DEPRECATED) | LS-11, LS-12, LS-13 | ERROR |
| `DELEGATION_VIOLATION` | Transitive delegation attempted or delegation_token invalid | RES-01, ID-08 | ERROR |
| `CROSS_TENANT_VIOLATION` | Agent targeting resource in foreign tenant | AC-25 | ERROR |
| `DATA_CLASSIFICATION_EXCEEDED` | Agent clearance < resource classification | AC-23 | WARN |
| `SOD_VIOLATION` | Author == Approver on approval actions | RES-12, EL-43 | ERROR |
| `RUNTIME_MUTATION` | Agent attempting to modify own weights/rules/state | GP-07, LS-18 | CRITICAL |
| `MOSAIC_RISK` | Aggregate access pattern exceeds threshold | RES-03, EL-44 | ERROR |
| `RATE_LIMIT_EXCEEDED` | Request velocity exceeds per-agent limit | EL-39 | WARN |
| `POLICY_VERSION_MISMATCH` | Caller's policy hash ≠ PDP's loaded bundle | LS-15 | INFO |
| `SYSTEM_UNCERTAINTY` | PDP cannot verify system state (CRL stale, dependency down) | GP-06, RES-04 | CRITICAL |
| `AUDIT_WRITE_FAILED` | BHIV Bucket write failed — decision cannot be recorded | AI-53 | CRITICAL |
| `REPLAY_DETECTED` | Duplicate correlation_id or stale timestamp | INV-08, INV-09 | ERROR |
| `INSUFFICIENT_PROOF` | Break-glass token required but absent/invalid | RES-05, AC-26 | ERROR |
| `FORBIDDEN_CLASS` | Agent class is one of the Forbidden Six | ID-05, ID-06, ID-07 | CRITICAL |
| `CASCADING_REVOCATION` | Parent agent has been revoked | LS-19 | ERROR |
| `PARTIAL_AUTHORITY` | USER_PROXY without delegation_token | ID-08 | ERROR |

**DENY Response Shape:**

```json
{
  "verdict": "DENY",
  "correlation_id": "a1b2c3d4-...",
  "audit_id": "aud-3e4f5a6b-...",
  "timestamp": "2026-02-26T10:30:01.234Z",
  "evaluation_duration_ms": 1.2,
  "pdp_instance": "pdp-east-1a-003",
  "policy_version_hash": "sha256:abcdef1234567890...",
  "determining_rules": [
    {
      "rule_id": "AC-23",
      "rule_name": "Scope Confinement",
      "evaluation_result": "TRIGGERED_DENY",
      "category": "CORE"
    }
  ],
  "reason_code": "SCOPE_MISMATCH",
  "signature": "<ed25519_signature>"
}
```

**Note:** No `capability_token` field. No `escalation_reference` field. No remediation hints. The response is deliberately sparse.

---

### 3.3 ESCALATE — Deferred Authority

**Meaning:** The PDP has encountered a specific scenario where it cannot render a final ALLOW or DENY and must defer to human governance authority.

**ESCALATE is extremely rare.** It exists for exactly ONE class of scenarios: **same-class mutual conflicts** as defined in AMB-13/RES-13. Specifically: when two agents of the same ontological class simultaneously attempt to suspend each other, the PDP cannot apply class precedence (because they are the same class) and cannot safely allow either suspension (because it might be weaponized). The conflict is escalated to human governance.

**ESCALATE is NOT a "maybe."** While the escalation is pending:
- The `interim_verdict` is **DENY** — always. The agent cannot act.
- Both conflicting agents continue operating under **enhanced logging** (per RES-13).
- Neither suspension takes effect until the Governance Council resolves it.
- If the `escalation_deadline` passes without resolution, DENY becomes permanent.

**When ESCALATE is produced:**
1. Two agents of the same `agent_class` simultaneously issue SUSPEND or TERMINATE intents against each other.
2. No class precedence rule can break the tie (per RES-13: Safety > Non-Safety, but same-class = tie).
3. The PDP creates an escalation case, assigns an `escalation_id`, and returns ESCALATE with interim DENY.

**ESCALATE Response Shape:**

```json
{
  "verdict": "ESCALATE",
  "correlation_id": "a1b2c3d4-...",
  "audit_id": "aud-9c8d7e6f-...",
  "timestamp": "2026-02-26T10:30:01.234Z",
  "evaluation_duration_ms": 5.1,
  "pdp_instance": "pdp-east-1a-003",
  "policy_version_hash": "sha256:abcdef1234567890...",
  "determining_rules": [
    {
      "rule_id": "LS-12",
      "rule_name": "Suspension Enforcement",
      "evaluation_result": "TRIGGERED_ESCALATE",
      "category": "CORE"
    }
  ],
  "reason_code": "MUTUAL_SUSPENSION_CONFLICT",
  "escalation_reference": {
    "escalation_id": "esc-5a4b3c2d-...",
    "escalation_target": "GOVERNANCE_COUNCIL",
    "escalation_deadline": "2026-02-26T10:45:01.234Z",
    "interim_verdict": "DENY"
  },
  "signature": "<ed25519_signature>"
}
```

**What ESCALATE is NOT used for:**
- Ambiguous policy interpretation → DENY (per GP-01)
- Missing information → DENY (per GP-04, INV-05)
- System uncertainty → DENY (per GP-06)
- "I'm not sure" → DENY (the PDP does not express uncertainty)
- Human-in-the-loop approval workflows → Out of scope (per Canon Deferred Scope Register)

---

## 4. RULE REFERENCES — WHAT TRIGGERED THE DECISION

### 4.1 Why Rule References Are Required

Every verdict must cite which Canon rules determined the outcome. This is the governance equivalent of "showing your work." A verdict without rule references is a verdict without accountability — it cannot be audited, challenged, or debugged.

This requirement derives from:
- **AI-54 (Audit Completeness):** The audit record must contain sufficient information to reconstruct the decision.
- **NIST AI RMF GOVERN function:** Organizational accountability requires traceability from decision to policy.
- **EU AI Act Article 12 (Automatic Event Logging):** High-risk AI systems must maintain logs that enable tracing the system's operations.
- **AWS Cedar design:** Every authorization decision returns the list of determining policies, enabling policy debugging.

### 4.2 Rule Reference Structure

Each entry in `determining_rules` answers four questions:

| Field | Question | Example |
|---|---|---|
| `rule_id` | WHICH rule? | `AC-23` |
| `rule_name` | What is it called? | `Scope Confinement` |
| `evaluation_result` | What did it decide? | `TRIGGERED_DENY` |
| `category` | How critical is it? | `CORE` |

### 4.3 Evaluation Result Semantics

| Result | Meaning | Implication |
|---|---|---|
| `TRIGGERED_DENY` | This rule evaluated the request and determined DENY. | This rule is a primary cause of the denial. |
| `TRIGGERED_ALLOW` | This rule evaluated the request and determined ALLOW. | This rule permitted the action (may be overridden by a DENY from another rule per GP-03). |
| `TRIGGERED_ESCALATE` | This rule determined that human review is required. | Only produced by RES-13 conflict detection logic. |
| `NOT_APPLICABLE` | This rule's conditions did not match this request. | The rule was consulted but had nothing to say. E.g., EL-43 (SoD) is not applicable if the action is READ. |
| `SKIPPED_SHORT_CIRCUIT` | This rule was not evaluated because an earlier rule already produced a terminal verdict. | For DENY verdicts: rules after the first DENY trigger may be skipped for efficiency. Documented for audit completeness. |

### 4.4 Combining Algorithm — Deny-Overrides

Sarathi uses **deny-overrides** combining (XACML 3.0 standard combining algorithm):

1. If ANY rule produces TRIGGERED_DENY → final verdict is DENY (regardless of how many rules produced TRIGGERED_ALLOW).
2. If NO rule produces TRIGGERED_DENY and at least one produces TRIGGERED_ALLOW → final verdict is ALLOW.
3. If ALL rules produce NOT_APPLICABLE → final verdict is DENY (GP-01: silence = denial).
4. If any rule produces TRIGGERED_ESCALATE and no rule produces TRIGGERED_DENY → final verdict is ESCALATE.
5. TRIGGERED_DENY always overrides TRIGGERED_ESCALATE (denial is more restrictive than deferral).

This is the formalization of GP-03 (Conflict Resolves to Restriction). The deny-overrides algorithm ensures that safety constraints always win over utility permissions.

### 4.5 What Rule References Must NOT Include

| Excluded | Why |
|---|---|
| Rule evaluation logic/pseudocode | Reveals policy implementation details |
| Attribute values that triggered the rule | Reveals what the PDP knows about the agent/resource |
| Other rules that were "close to triggering" | Enables probing ("I was almost denied by X, so I'll adjust Y") |
| Rule source code or Rego snippets | Intellectual property and security sensitive |
| Policy file paths or line numbers | Internal infrastructure detail |

Rule references are for **accountability** (which rules decided) not for **education** (how the rules work).

---

## 5. AUDIT PAYLOAD STRUCTURE

### 5.1 The Dual-Record Model

Every PDP decision produces TWO records:

1. **The Response Envelope** — returned to the caller (minimal, per OUT-05).
2. **The Audit Record** — written to the BHIV Bucket (comprehensive, for forensics).

The response is a redacted summary. The audit record is the full evidence file. The `audit_id` in the response is the foreign key linking the two.

### 5.2 BHIV Bucket Audit Record Schema

This record is written to the BHIV Bucket (Write-Only, per AI-53) for EVERY decision — ALLOW, DENY, and ESCALATE. No exceptions. No sampling. No "only log errors."

```json
{
  "audit_id": "aud-7f8e9d0c-...",
  "correlation_id": "a1b2c3d4-...",
  "timestamp": "2026-02-26T10:30:01.234Z",
  "pdp_instance": "pdp-east-1a-003",
  "pdp_version": "v1.4.2",
  "policy_version_hash": "sha256:abcdef1234567890...",

  "request_summary": {
    "agent_id": "spiffe://bhiv.io/agents/researcher-7f3a",
    "agent_class": "DATA_PROCESSOR",
    "agent_version": "v2.1.0",
    "action": "READ",
    "resource_type": "DB_TABLE",
    "resource_id": "/data/users/profiles",
    "data_classification_declared": "INTERNAL",
    "data_classification_actual": "CONFIDENTIAL",
    "risk_classification": {
      "action_sensitivity": "MEDIUM",
      "reversibility": "REVERSIBLE",
      "blast_radius": "COLLECTION"
    },
    "environment": "PRODUCTION",
    "source_ip": "10.0.1.47",
    "delegation_chain_depth": 2,
    "request_hash": "sha256:fedcba0987654321..."
  },

  "evaluation_trace": {
    "pre_policy_result": "PASS",
    "pre_policy_stages_completed": 7,
    "token_verification_result": "VALID",
    "token_issuer": "idp.bhiv.io",
    "token_expiry": "2026-02-26T10:31:00Z",
    "session_binding_verified": true,
    "delegation_chain_verified": true,
    "delegation_chain_depth_verified": 2,
    "policy_rules_evaluated": 12,
    "policy_rules_triggered": 1,
    "combining_algorithm": "deny-overrides",
    "short_circuit_applied": false
  },

  "determining_rules": [
    {
      "rule_id": "AC-23",
      "rule_name": "Scope Confinement",
      "evaluation_result": "TRIGGERED_DENY",
      "category": "CORE",
      "rule_condition_met": "intent.resource.data_classification (CONFIDENTIAL) > agent.clearance (INTERNAL)",
      "rule_version": "v2.3.1"
    }
  ],

  "verdict": "DENY",
  "reason_code": "DATA_CLASSIFICATION_EXCEEDED",
  "capability_token_issued": false,
  "evaluation_duration_ms": 3.7,

  "anomaly_signals": {
    "classification_downgrade_attempted": true,
    "declared_vs_actual_classification_gap": "INTERNAL → CONFIDENTIAL",
    "velocity_current": 12,
    "velocity_threshold": 50
  },

  "response_hash": "sha256:1234567890abcdef...",
  "signature": "<ed25519_audit_signature>"
}
```

### 5.3 What the Audit Record Contains That the Response Does NOT

| Audit-Only Field | Purpose | Why Not in Response |
|---|---|---|
| `request_summary` (full) | Reconstruct what was asked | Reveals schema structure to potential attacker |
| `evaluation_trace` | Reconstruct HOW the decision was made | Reveals evaluation pipeline internals |
| `rule_condition_met` | Exact condition that triggered each rule | Reveals policy logic |
| `data_classification_actual` | What the Resource Registry says | Reveals asset classification to agent |
| `anomaly_signals` | Behavioral deviation indicators | Reveals detection capabilities |
| `token_issuer`, `token_expiry` | Token provenance details | Reveals IdP infrastructure |
| `delegation_chain_depth_verified` | Verified chain length | Reveals chain validation logic |
| `response_hash` | Integrity link between response and audit | Internal consistency mechanism |

### 5.4 Audit Write Failure Behavior

Per OUT-07 and AI-53: if the BHIV Bucket write fails, the PDP MUST:
1. **Override the verdict to DENY** regardless of what the evaluation produced.
2. Set `reason_code` to `AUDIT_WRITE_FAILED`.
3. Log the audit write failure to a local emergency buffer (best-effort fallback).
4. Return the DENY response to the caller.
5. Trigger a `NOTIFY_SECURITY` alert for ops team.

The principle: **an unauditable ALLOW is more dangerous than a false DENY.** A false DENY causes operational friction. An unauditable ALLOW creates a governance blind spot that may never be discovered.

---

## 6. TOKEN ISSUANCE RULES — ALLOW ONLY

### 6.1 What the Capability Token Is

The capability token is a **cryptographically signed, time-bounded, scope-restricted JWT** that serves as the physical key to execute the authorized action. It is the enforcement mechanism that makes Sarathi's governance binding rather than advisory. Without this token, downstream resources reject the request — regardless of what the agent claims.

This implements Canon MUST-FIX MF-02: "Downstream Resource Servers MUST validate Sarathi-issued tokens. Governance logic is sound; enforcement depends on token verification."

### 6.2 Token Structure (JWT Claims)

```json
{
  "header": {
    "alg": "EdDSA",
    "typ": "JWT",
    "kid": "sarathi-pdp-signing-key-2026-02"
  },
  "payload": {
    "iss": "sarathi.governance.bhiv.io",
    "sub": "<agent_id from request>",
    "aud": "<resource_type>:<resource_id>",
    "exp": "<timestamp + MAX_TOKEN_TTL (60s)>",
    "nbf": "<timestamp>",
    "iat": "<timestamp>",
    "jti": "<unique token ID, UUIDv4>",

    "sarathi_claims": {
      "correlation_id": "<echoed from request>",
      "audit_id": "<from this response>",
      "action": "<authorized action verb>",
      "resource_type": "<authorized resource type>",
      "resource_id": "<authorized resource ID>",
      "parameters_hash": "<echoed from request>",
      "data_classification": "<PDP-verified classification>",
      "risk_assessment": "<PDP-determined risk level>",
      "session_binding": "<echoed from request>",
      "delegation_chain_hash": "<hash of verified delegation chain>",
      "obligations": ["<obligation_ids from response>"],
      "policy_version_hash": "<policy bundle used for this decision>"
    }
  },
  "signature": "<EdDSA signature>"
}
```

### 6.3 Token Issuance Rules (Non-Negotiable)

| Rule ID | Rule | Rationale |
|:---:|---|---|
| **TI-01** | Token is issued ONLY on verdict ALLOW. Never on DENY. Never on ESCALATE. | A token is proof of authorization. No authorization = no proof. |
| **TI-02** | Token TTL MUST NOT exceed 60 seconds (`exp - iat ≤ 60`). | Per MF-05. Limits blast radius of token theft. |
| **TI-03** | Token is scoped to EXACTLY the action, resource, and parameters_hash from the request. No wildcards. No broader scopes. | Per AC-23 (Scope Confinement). The token authorizes precisely what was evaluated — nothing more. |
| **TI-04** | Token `sub` claim MUST match the `agent_id` from the request. | Prevents Confused Deputy. The token is bound to the requesting agent. |
| **TI-05** | Token `aud` claim MUST specify the target resource. | Prevents token replay against different resources. The downstream resource rejects tokens not addressed to it. |
| **TI-06** | Token includes `session_binding` from the request. | Downstream resource verifies that the token is presented from the same TLS session. Per RES-09. |
| **TI-07** | Token includes `parameters_hash` from the request. | Downstream resource verifies that the actual parameters match the authorized parameters. TOCTOU prevention per CWE-367. |
| **TI-08** | Token includes `delegation_chain_hash` (hash of the verified chain, not the chain itself). | Proves the delegation chain was verified without exposing the chain to the downstream resource. Least privilege. |
| **TI-09** | Token is signed with Ed25519 using the PDP's private key. | Per Canon operational parameter. Ed25519 is deterministic (no nonce reuse risk), fast, and compact. |
| **TI-10** | Token `jti` (JWT ID) is unique and registered in the dedup store. | Prevents token replay. A token can be used exactly once. |
| **TI-11** | Token includes the `policy_version_hash` used for the decision. | Downstream resource can verify the token was issued under the current policy version. |
| **TI-12** | Token includes `obligations` list. Downstream resource MUST fulfill obligations or reject. | Per XACML Obligations model. Obligations are mandatory post-decision directives. |
| **TI-13** | Token is NEVER cached by the PDP. Each ALLOW generates a fresh token. | Cached tokens could be issued after the agent is revoked but before the cache is invalidated. |
| **TI-14** | Token is NEVER logged in plaintext in the audit record. Only the `jti` and a hash of the token are logged. | The token is a bearer credential. Logging it in plaintext enables insider extraction from audit logs. |

### 6.4 What the Downstream Resource MUST Verify

The capability token shifts enforcement from "trust the PDP response" to "verify the cryptographic proof." The downstream resource MUST:

1. Verify the Ed25519 signature against the PDP's public key.
2. Verify `exp` is in the future (token not expired).
3. Verify `aud` matches this resource's identifier.
4. Verify `sarathi_claims.action` matches the requested action.
5. Verify `sarathi_claims.resource_id` matches the requested resource.
6. Verify `sarathi_claims.parameters_hash` matches the hash of the actual parameters.
7. Verify `sarathi_claims.session_binding` matches the TLS client cert hash.
8. Verify `jti` has not been seen before (single-use enforcement).
9. Fulfill all obligations listed in `sarathi_claims.obligations`.

If ANY verification fails: reject the request. Do NOT call the PDP to "re-check." The token is self-contained proof — it either verifies or it doesn't.

---

## 7. ESCALATION PROTOCOL — ESCALATE ONLY

### 7.1 When Escalation Occurs

ESCALATE is triggered by exactly ONE scenario per current Canon (RES-13):

**Two agents of the SAME ontological class simultaneously issue SUSPEND or TERMINATE against each other.**

The PDP cannot resolve this because:
- Class precedence (RES-13 rule: Safety > Non-Safety) requires DIFFERENT classes.
- Allowing either suspension may be weaponized (the "first to click" problem).
- Denying both removes the ability to legitimately suspend a misbehaving same-class agent.

### 7.2 Escalation Reference Fields

| Field | Specification |
|---|---|
| `escalation_id` | UUIDv4. Unique case identifier. Both conflicting agents receive the SAME escalation_id so the Governance Council can correlate. |
| `escalation_target` | `GOVERNANCE_COUNCIL` for same-class mutual suspension. `SECURITY_TEAM` may be used for future escalation types. `HUMAN_OPERATOR` reserved for operational escalations. |
| `escalation_deadline` | Default: 15 minutes from verdict timestamp. After deadline, the interim verdict (DENY) becomes permanent. The escalation is marked EXPIRED. The agent must submit a new request if circumstances change. |
| `interim_verdict` | **Always DENY.** There is no scenario where a pending escalation permits action. Per GP-06: uncertainty = fail-closed. |

### 7.3 Escalation Lifecycle

```
[PDP detects same-class mutual suspension conflict]
     │
     ▼
[PDP creates escalation case with escalation_id]
     │
     ├── Returns ESCALATE + interim DENY to Agent A
     ├── Returns ESCALATE + interim DENY to Agent B (same escalation_id)
     ├── Writes escalation record to BHIV Bucket
     ├── Notifies GOVERNANCE_COUNCIL via obligation: HUMAN_REVIEW_REQUIRED
     ▼
[Governance Council reviews within escalation_deadline]
     │
     ├── RESOLVE_ALLOW_A: Agent A's suspension of B is authorized → PDP issues new verdict
     ├── RESOLVE_ALLOW_B: Agent B's suspension of A is authorized → PDP issues new verdict
     ├── RESOLVE_DENY_BOTH: Neither suspension is authorized → both agents continue
     ├── RESOLVE_SUSPEND_BOTH: Both agents are suspended → PDP issues HALT for both
     │
     └── DEADLINE_EXPIRED: No resolution → interim DENY becomes permanent
```

### 7.4 Escalation Anti-Patterns

| Anti-Pattern | Why Prohibited |
|---|---|
| Escalation as "soft deny" | ESCALATE is not a polite DENY. It exists for a specific structural conflict. |
| Self-escalation | An agent cannot request escalation of its own denial. DENY is DENY. |
| Escalation chains | An escalation cannot trigger another escalation. That would be infinite deferral. |
| Interim ALLOW | The interim verdict is ALWAYS DENY. A pending conflict does not permit action. |
| Escalation without audit | Every escalation is logged. If audit fails, verdict falls to DENY per OUT-07. |

---

## 8. WHAT MUST NEVER BE INCLUDED — THE PROHIBITION LIST

This section is as important as the schema definition. These items are **explicitly prohibited** from appearing in any Sarathi PDP response. Every prohibition prevents a specific attack class.

### 8.1 Information That Must NEVER Appear in Responses

| Prohibited Item | Attack It Prevents | Applicable Verdict |
|---|---|---|
| **Which specific field caused the rejection** | Schema probing: attacker iterates fields to discover validation rules | DENY |
| **Expected field format or pattern** | Validation bypass: attacker learns regex patterns and crafts compliant malicious input | DENY |
| **The actual value the PDP received** | Reflection attack: attacker uses echoed values to understand server-side processing | ALL |
| **Alternative actions that would be permitted** | Privilege probing: "you can't DELETE but you CAN READ" teaches the attacker what IS allowed | DENY |
| **Internal PDP state or configuration** | Infrastructure reconnaissance: reveals deployment topology, version, capacity | ALL |
| **Other agents' identity or state information** | Cross-agent information leakage: reveals who else is in the system | ALL |
| **Resource Registry classifications** | Asset discovery: agent learns actual classification of resources it cannot access | DENY |
| **Full delegation chain details** | Authority mapping: attacker learns organizational delegation structure | ALL |
| **Policy rule source code, Rego, or pseudocode** | Policy reverse-engineering: attacker reconstructs the rule set | ALL |
| **Number of rules that "almost triggered"** | Near-miss probing: "3 of 4 checks passed" reveals how close the attacker is | DENY |
| **Timing side-channels beyond evaluation_duration_ms** | Timing attack: different rejection speeds for different failure types reveal which check failed | DENY |
| **Stack traces, error messages, or debug output** | Implementation leakage: reveals language, framework, and code structure | ALL |
| **Capability token from a different request** | Token confusion: mixing tokens between requests enables replay | ALLOW |
| **Historical verdicts for this agent** | Behavioral profiling: agent learns which requests succeeded and adjusts strategy | ALL |
| **The Mosaic Risk score or threshold** | Threshold probing: attacker learns exactly how many queries they can make before detection (per RES-03: agent sees rate limit, not mosaic detection) | DENY |
| **Session_binding verification details** | Channel binding bypass: learning what the PDP checks about TLS certificates | DENY |
| **Suggestions, recommendations, or hints** | Adversarial coaching: any hint teaches the attacker how to succeed next time | DENY |

### 8.2 The Principle Behind the Prohibitions

Per GP-05 (Observation ≠ Verification): the PDP treats all requesting agents as potentially adversarial. Information in the response is information the attacker receives. Every additional field is an oracle that the attacker can query to learn about the system.

Per the Ambiguity Resolution Spec (Task 3), every resolution explicitly defines "Not Exposed" — what the agent must NOT learn from the rejection:
- RES-01: "Not Exposed: the fact that scopes technically matched" (prevents probing delegation chain as the weak link).
- RES-03: "Not Exposed: the words 'Mosaic,' 'Inference,' or any indication that the semantic pattern was detected" (prevents threshold probing).
- RES-13: "Not Exposed: the precedence hierarchy logic" (prevents learning class-based authority structures).

### 8.3 Differential Information by Verdict

| Verdict | Information Provided | Information Withheld |
|---|---|---|
| **ALLOW** | capability_token, obligations, determining_rules (rule_id + name only), audit_id | Alternative scopes, broader permissions, risk score details |
| **DENY** | reason_code, determining_rules (rule_id + name only), audit_id | Which field failed, expected format, how to fix, what would succeed |
| **ESCALATE** | escalation_reference (id, target, deadline, interim=DENY), determining_rules, audit_id | Conflict details, other agent identity, precedence logic |

---

## 9. RESPONSE SIGNING AND VERIFICATION

### 9.1 Why Every Response Is Signed

Per Canon Section 6.9: "The signature field on the verdict is MANDATORY to verify before acting. An unsigned or tampered verdict from a man-in-the-middle must be treated as DENY."

Without response signing:
- A network-level attacker could intercept a DENY and replace it with an ALLOW.
- A compromised proxy could inject capability tokens.
- A rogue orchestrator could forge PDP responses.

The Ed25519 signature makes the response tamper-evident. The caller (orchestrator/PEP) holds the PDP's public key and verifies every response before acting on it.

### 9.2 Signing Process

1. Construct the response JSON with all fields EXCEPT `signature`.
2. Canonicalize the JSON (deterministic key ordering, no whitespace, UTF-8 NFC normalization).
3. Compute Ed25519 signature over the canonical JSON bytes using the PDP's private key.
4. Add the `signature` field to the response.
5. Return the complete response.

### 9.3 Verification Process (Caller-Side)

1. Extract the `signature` field from the response.
2. Remove the `signature` field from the response JSON.
3. Canonicalize the remaining JSON (same algorithm as signing).
4. Verify the Ed25519 signature using the PDP's public key.
5. If verification fails → treat the response as DENY regardless of the `verdict` field.
6. If verification succeeds → proceed with the verdict.

### 9.4 Key Management

| Parameter | Value | Rationale |
|---|---|---|
| Algorithm | Ed25519 (EdDSA) | Deterministic (no nonce reuse risk), fast (62,000 verify ops/sec), compact (64-byte signatures). |
| Key Rotation | Every 90 days minimum | Limits blast radius of key compromise. |
| Key Distribution | Public key distributed to all PEPs/orchestrators via secure channel (not via the PDP itself). | If the PDP distributes its own key, a compromised PDP distributes a compromised key. |
| Key Storage | PDP private key in HSM or equivalent hardware security module. | Per Canon Readiness Condition 5: "IdP key management follows HSM or equivalent hardware security standards." Same applies to PDP signing keys. |

---

## 10. VERDICT-TO-HTTP MAPPING

The Sarathi PDP communicates over HTTPS. The HTTP status code provides a coarse signal; the response body provides the precise verdict. Callers MUST use the `verdict` field in the signed response body — NOT the HTTP status code — for authorization decisions.

| Verdict | HTTP Status | Rationale |
|---|---|---|
| **ALLOW** | `200 OK` | Authorization granted. Body contains capability_token. |
| **DENY** (schema/input failure) | `400 Bad Request` | Request was malformed. Caller error. |
| **DENY** (authentication failure) | `401 Unauthorized` | Token invalid, expired, or missing. Identity cannot be established. |
| **DENY** (authorization failure) | `403 Forbidden` | Identity established, but action not permitted. |
| **DENY** (audit write failure) | `500 Internal Server Error` | PDP internal failure. Fail-closed to DENY. |
| **DENY** (system uncertainty) | `503 Service Unavailable` | PDP cannot verify system state. Fail-closed to DENY. |
| **DENY** (policy version mismatch) | `409 Conflict` | Caller's policy version ≠ PDP's policy version. |
| **DENY** (rate limit exceeded) | `429 Too Many Requests` | Per RES-03: mosaic detection appears as rate limit to caller. |
| **ESCALATE** | `202 Accepted` | Request received, but decision deferred to human authority. Interim verdict (DENY) in body. |
| **DENY** (replay detected) | `400 Bad Request` | Duplicate correlation_id or stale timestamp. |

**CRITICAL:** HTTP status codes are a convenience mapping. The authoritative decision is the `verdict` field in the signed response body. If the HTTP status says 200 but the body says DENY — the verdict is DENY. If the HTTP status says 500 but the body is unsigned — the verdict is DENY (per Section 9.3).

---

## 11. Relationship to Previous Tasks
 

| Previous Artifact | Relationship to Day 2 |
|---|---|
| **Task 1 — Governance Validation** | Addresses Assumption A3 (Orchestrator Compliance — capability tokens force compliance). Addresses A8 (Bucket Immutability — audit records in WORM storage). |
| **Task 2 — Canon (60 Rules)** | 22 DENY reason_codes map directly to Canon rules. Token issuance rules implement MF-02 and MF-05. Audit structure implements AI-53, AI-54, AI-55. |
| **Task 3 — Ambiguity (14 Scenarios)** | Prohibition list derives from all 14 RES "Not Exposed" specifications. ESCALATE protocol implements RES-13 exactly. |
| **Task 3 — PDP Interface (17-Step Pipeline)** | Response schema is the OUTPUT of the pipeline defined in Task 3. Steps 1-16 determine the verdict; Step 17 (Audit Write) determines whether the verdict can be issued. |
| **Task 4 Day 1 — Request Schema** | Response echoes correlation_id (audit thread), reflects policy_version_hash (version agreement), includes parameters_hash in capability token (TOCTOU binding). |

---

**END OF SARATHI RESPONSE SCHEMA — MINIMAL OUTPUT CONTRACT**

---

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Verdicts Defined | 3 (ALLOW, DENY, ESCALATE) |
| Output Invariants | 10 |
| DENY Reason Codes | 22 |
| Token Issuance Rules | 14 |
| Prohibited Response Items | 18 |
| Audit Record Fields | 28 |
| Escalation Anti-Patterns | 5 |
| HTTP Status Mappings | 10 |
| Canon Rules Implemented | AC-21, AC-22, AC-23, AC-24, AC-25, AC-26, AC-27, AC-30, AC-31, AI-53, AI-54, AI-55, ID-01, ID-05, ID-06, ID-07, ID-08, EL-33, EL-39, EL-42, EL-43, EL-44, LS-11, LS-12, LS-13, LS-15, LS-18, LS-19, LS-20 |
| Global Principles Invoked | GP-01, GP-03, GP-04, GP-05, GP-06, GP-07 |
| Ambiguity Resolutions Referenced | RES-01, RES-03, RES-04, RES-05, RES-09, RES-12, RES-13 |
| Industry Standards Referenced | XACML 3.0, NIST SP 800-162, NIST AI RMF, EU AI Act Art. 12, OPA Decision Logs, AWS Cedar, Google Zanzibar, RFC 9449, CWE-367 |

---

## EXTENDED RESPONSE FIELDS (GAP RESOLUTION PHASE)

*Added to support delegation tokens (Gap 2), runtime enforcement (Gap 1), and audit integrity (Gap 5).*

### EXT-1: Delegation Token Fields in ALLOW Response

When the PDP issues an ALLOW verdict for a request containing a Delegation Capability Token, the response includes additional delegation-specific fields:

```json
{
  "verdict": {
    "decision": "ALLOW",
    "capability_token": {
      "...existing fields...",
      "delegation_context": {
        "delegation_depth": 2,
        "max_delegation_depth": 3,
        "data_classification_ceiling": "CONFIDENTIAL",
        "scope_id": "scope-9f8e7d6c",
        "delegating_user_pseudonym": "hmac-sha256(user_id)",
        "chain_hash": "sha256(delegation_chain)",
        "can_delegate": true,
        "remaining_cost_budget": 800.00,
        "shutdown_deadline": "2026-02-28T12:00:00Z"
      }
    }
  }
}
```

**Delegation Context Rules:**
- `can_delegate` is TRUE only if `delegation_depth < max_delegation_depth` (GP-08)
- `remaining_cost_budget` decremented from parent token's budget
- `data_classification_ceiling` inherited from parent (RES-16)
- `shutdown_deadline` cannot be extended beyond parent's deadline

### EXT-2: Circuit Breaker State in Response Metadata

Every response includes circuit breaker state for observability:

```json
{
  "meta": {
    "...existing fields...",
    "enforcement": {
      "pep_type": "sidecar",
      "circuit_breaker_state": "CLOSED",
      "evaluation_latency_us": 87,
      "cache_hit": false
    }
  }
}
```

### EXT-3: Audit Integrity Fields in Audit Record

The audit record embedded in every response now includes hash chain integrity:

```json
{
  "audit": {
    "...existing 28 fields...",
    "integrity": {
      "prev_event_hash": "sha256(previous_audit_event)",
      "current_event_hash": "sha256(this_event + prev_hash)",
      "merkle_batch_id": "batch-2026022810",
      "chain_type": "primary"
    },
    "network_fingerprint": {
      "source_ip_hash": "sha256(source_ip)",
      "ja3": "tls_fingerprint_v1",
      "ja4": "tls_fingerprint_v2"
    }
  }
}
```

### EXT-4: Extended Denial Reason Codes

| Code | Meaning | Category |
|---|---|---|
| ERR_DELEGATION_VIOLATION | Biscuit validation failed | Delegation |
| ERR_DELEGATION_DEPTH_EXCEEDED | Chain depth > max_delegation_depth | Delegation |
| ERR_CLASSIFICATION_EXCEEDED | Data classification > ceiling | Delegation |
| ERR_PROOF_INVALID | DPoP proof verification failed | Identity |
| ERR_REPLAY_DETECTED | DPoP jti already consumed | Identity |
| ERR_COST_EXCEEDED | Accumulated cost > Biscuit max_cost | Risk |
| ERR_SHUTDOWN_EXPIRED | Request after shutdown_deadline | Risk |
| ERR_CIRCUIT_OPEN | PEP circuit breaker in OPEN state | Infrastructure |
| ERR_TENANT_CIRCUIT_OPEN | Tenant-level circuit breaker OPEN | Infrastructure |

### EXT-5: Updated Output Invariants

| ID | Invariant | Status |
|---|---|---|
| OUT-01 through OUT-10 | (Unchanged — see original specification) | ✅ Original |
| **OUT-11** | **Delegation-Aware** — ALLOW responses for delegated requests MUST include delegation_context | NEW |
| **OUT-12** | **Integrity-Chained** — Every audit record MUST contain prev_event_hash and current_event_hash for hash chain continuity | NEW |
| **OUT-13** | **Fingerprinted** — Every audit record MUST contain JA3/JA4 TLS fingerprints when available | NEW |


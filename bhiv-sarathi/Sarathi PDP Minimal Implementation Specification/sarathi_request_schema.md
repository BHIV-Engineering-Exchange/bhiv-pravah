# SARATHI REQUEST SCHEMA — MINIMAL INPUT CONTRACT

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Task 4 — Sarathi PDP Minimal Implementation Specification (Day 1)  
**Upstream Dependencies:**  
- `GOVERNANCE_VALIDATION_REPORT.md` (Task 1)  
- `SARATHI_HIGH_DENSITY_CANON_FORMALIZATION.md` (Task 2)  
- `AMBIGUITY_REGISTER.md` / `AMBIGUITY_RESOLUTION_SPEC.md` / `SARATHI_PDP_INTERFACE.md` (Task 3)  
- Sarathi PDP Research Report — Constitutional Blueprint for Sovereign AI Governance

---

## PURPOSE

This document defines the **Sarathi Request Envelope** — the exact, minimal, non-negotiable data structure that every agent must submit to the Sarathi PDP before any action is permitted. It constitutes the **input contract** of the Action Authorization Boundary (AAB).

This is not a recommendation. This is a contract. An engineer reading this document must be able to implement the request validation layer without interpretation, without asking clarifying questions, and without making assumptions about what "should probably be there."

Every field defined here exists because its absence creates a governance bypass. Every constraint defined here exists because its relaxation enables an attack. Every rejection behavior defined here exists because the alternative is silent authority drift.

**Constitutional Authority:** This schema derives its authority from:
- **GP-01 (Silence Implies Denial):** Fields not present cannot be evaluated; absent data = DENY.
- **GP-04 (Input Validity Is Security):** Malformed input is a hostile act, not a data error.
- **GP-05 (Observation ≠ Verification):** Agent claims are noise; only cryptographic proofs are data.
- **GP-06 (Fail-Closed on Uncertainty):** If the PDP cannot determine field validity, it assumes worst-case.
- **Canon Rules:** AC-21 (Zero Trust Default), AC-22 (Token Signature Validation), AC-23 (Scope Confinement), ID-01 (Identity Signature Verification), ID-02 (Session Binding Requirement), EL-33 (Input Validation).

**Industry Grounding:** This schema is architecturally aligned with:
- OASIS XACML 3.0 Request Context model (Subject, Action, Resource, Environment)
- NIST SP 800-162 ABAC attribute categories (Subject, Action, Resource, Environment)
- NIST SP 800-207 Zero Trust Architecture Policy Engine input model
- Google Zanzibar relationship tuple model (Object#Relation@Subject)
- AWS Cedar Entity-Action-Resource-Context authorization model
- RFC 9449 (DPoP) proof-of-possession token binding
- SPIFFE/SPIRE workload identity model (SVIDs for agent identity)
- Norm Hardy's Confused Deputy prevention (designation + authority colocation)
- UCAN delegation chain model (non-transitive capability delegation)

---

## TABLE OF CONTENTS

1. [Interface Invariants](#1-interface-invariants)
2. [Request Envelope — Complete Schema Definition](#2-request-envelope--complete-schema-definition)
3. [Field-Level Specification](#3-field-level-specification)
   - 3.1 [Agent Identity Fields](#31-agent-identity-fields)
   - 3.2 [Intent Structure](#32-intent-structure)
   - 3.3 [Authority Token Structure](#33-authority-token-structure)
   - 3.4 [Context Object](#34-context-object)
   - 3.5 [Risk Classification Field](#35-risk-classification-field)
   - 3.6 [Correlation ID](#36-correlation-id)
4. [Absence Behavior Matrix](#4-absence-behavior-matrix)
5. [Input Validation Pipeline — Pre-Policy Stage](#5-input-validation-pipeline--pre-policy-stage)
6. [Rejection Taxonomy for Input Failures](#6-rejection-taxonomy-for-input-failures)
7. [Anti-Patterns — What Must Never Be Accepted](#7-anti-patterns--what-must-never-be-accepted)
8. [Schema Evolution Rules](#8-schema-evolution-rules)


---

## 1. INTERFACE INVARIANTS

Before any field is discussed, the following properties are **axiomatic**. They cannot be negotiated, configured, or overridden. They apply to every request, every field, every agent, every time.

| Invariant ID | Property | Definition | Violation Consequence |
|:---:|---|---|---|
| **INV-01** | **Totality** | Every request MUST contain all six top-level required sections. There is no "partial request" concept. | Immediate DENY — `ERR_SCHEMA_VIOLATION` (HTTP 400) |
| **INV-02** | **Atomicity** | Each request is evaluated as one indivisible unit. No batching. No pipelining. No multi-intent envelopes. One request = one intent = one verdict. | Immediate DENY — `ERR_BATCH_REJECTED` (HTTP 400) |
| **INV-03** | **Idempotency** | The same request with the same state MUST produce the same verdict. The PDP has no side effects on evaluation. | Architectural invariant — violation is a PDP implementation bug, not a request error. |
| **INV-04** | **Synchronicity** | Request in, verdict out. No callbacks. No webhooks. No deferred evaluation. No "pending" states. | Architectural invariant — the PDP is a synchronous function: `f(request, policy, state) → verdict`. |
| **INV-05** | **Non-Negotiation** | The PDP does not ask for more information. It does not suggest corrections. It does not return "try again with X." Incomplete = DENY. | DENY with appropriate error code. No remediation hints in response (per GP-05). |
| **INV-06** | **Non-Orchestration** | The PDP does not call external services to gather evidence. All evidence must arrive WITH the request. The PDP is a judge, not an investigator. | Architectural invariant — the PDP evaluates what it receives. PIPs are the caller's responsibility. |
| **INV-07** | **Closure** | `additionalProperties: false` on every object. Unknown fields are rejected, not ignored. Permissive parsing enables injection. | Immediate DENY — `ERR_UNKNOWN_FIELD` (HTTP 400) |
| **INV-08** | **Freshness** | Every request carries a timestamp. Requests older than `MAX_REQUEST_AGE` (5000ms) or future-dated beyond `MAX_CLOCK_SKEW` (1000ms) are rejected. | Immediate DENY — `ERR_REPLAY_DETECTED` or `ERR_CLOCK_SKEW` (HTTP 400) |
| **INV-09** | **Non-Replayability** | Every request carries a unique `correlation_id`. IDs seen within the `DEDUP_WINDOW` (60s) are rejected. | Immediate DENY — `ERR_REPLAY_DETECTED` (HTTP 400) |
| **INV-10** | **Cryptographic Binding** | Identity claims must be cryptographically verifiable. Free-text identity assertions are semantically equivalent to null. | Immediate DENY — `ERR_NO_AUTH` (HTTP 401) |

**Rationale for INV-07 (Closure):** XACML 3.0 allows "Indeterminate" results from unknown attributes. Sarathi does not. Per GP-04 (Input Validity Is Security), unknown fields are treated as injection attempts. This aligns with AWS Cedar's design decision to reject unknown entities rather than returning "not applicable." OPA/Rego's default behavior of treating undefined as falsy is insufficient — undefined is not false, it is unknown, and unknown in a governance context is hostile.

---

## 2. REQUEST ENVELOPE — COMPLETE SCHEMA DEFINITION

```json
{
  "$schema": "https://sarathi.governance/v1/request-envelope.json",
  "$id": "sarathi-request-envelope-v1.0.0",
  "title": "Sarathi PDP Request Envelope",
  "description": "The atomic unit of governance evaluation. Represents an agent's intent to perform a specific action on a specific resource, accompanied by all evidence required for sovereign authorization. This envelope is the ONLY input the PDP accepts. There are no alternative entry points, simplified formats, or legacy compatibility modes.",
  "type": "object",
  "required": [
    "agent_identity",
    "intent",
    "authority",
    "context",
    "risk_classification",
    "correlation_id"
  ],
  "additionalProperties": false,

  "properties": {

    "agent_identity": {
      "type": "object",
      "description": "Section 3.1 — Cryptographically verifiable identity of the requesting agent. Answers: WHO is asking?",
      "required": ["agent_id", "agent_version", "agent_class", "session_binding", "delegation_chain"],
      "additionalProperties": false,
      "properties": {
        "agent_id": {
          "type": "string",
          "format": "uri",
          "minLength": 1,
          "maxLength": 512,
          "description": "Immutable agent identifier. MUST be a DID (Decentralized Identifier) or SPIFFE ID (spiffe://trust-domain/path). This is the agent's constitutional identity — it cannot change across sessions, restarts, or version upgrades. Maps to XACML Subject-ID. Must match the `sub` claim in the capability token."
        },
        "agent_version": {
          "type": "string",
          "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+(-[a-zA-Z0-9.]+)?$",
          "description": "Semantic version of the agent's deployed code (e.g., v1.2.0, v2.0.0-rc.1). Required for audit trail reconstruction and vulnerability-correlated revocation. If agent v1.2.0 is found vulnerable, all requests from v1.2.0 can be retroactively traced. Maps to Canon Rule ID-09 (Ephemeral Identity TTL)."
        },
        "agent_class": {
          "type": "string",
          "enum": [
            "AUTONOMOUS_EXECUTOR",
            "USER_PROXY",
            "SAFETY_MONITOR",
            "ORCHESTRATOR",
            "DATA_PROCESSOR",
            "BIAS_AUDITOR",
            "PENETRATION_TESTER",
            "CONTEXT_FREE_SUMMARIZER",
            "REPORTING_BOT",
            "ADMINISTRATIVE"
          ],
          "description": "The ontological classification of this agent from the Sarathi Agent Ontology. Determines which Canon rules apply, which risk gates activate, and which actions are categorically prohibited. Maps to Canon Categories: 'Sanctioned Three' (AUTONOMOUS_EXECUTOR, USER_PROXY, DATA_PROCESSOR), 'Dangerous Four' (SAFETY_MONITOR, ORCHESTRATOR, BIAS_AUDITOR, PENETRATION_TESTER), and monitored classes. The 'Forbidden Six' classes (RECURSIVE_POLICY_OPTIMIZER, SHADOW_AI, EMERGENCY_BACKDOOR, etc.) are NOT enumerated here — they are banned at the identity provider level and will never receive valid capability tokens per Canon Rules ID-05, ID-06, ID-07."
        },
        "session_binding": {
          "type": "string",
          "minLength": 64,
          "maxLength": 64,
          "pattern": "^[a-f0-9]{64}$",
          "description": "SHA-256 hash of the TLS client certificate used for this connection. Implements Channel Binding per AMB-09/RES-09 resolution: Token.Subject MUST match TLS.Client. Prevents Ghost Session attacks where a stolen token is replayed from a different transport channel. Aligned with RFC 9449 DPoP proof-of-possession model — the token is cryptographically bound to the connection."
        },
        "delegation_chain": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["principal_id", "principal_type", "delegated_at", "delegation_proof"],
            "additionalProperties": false,
            "properties": {
              "principal_id": {
                "type": "string",
                "minLength": 1,
                "description": "Identifier of the delegating principal (human user DID, parent agent SPIFFE ID, or system service account)."
              },
              "principal_type": {
                "type": "string",
                "enum": ["HUMAN_USER", "PARENT_AGENT", "SYSTEM_SERVICE"],
                "description": "Type classification of the delegating principal."
              },
              "delegated_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO-8601 UTC timestamp of when delegation was granted."
              },
              "delegation_proof": {
                "type": "string",
                "minLength": 1,
                "description": "Cryptographic proof of delegation (signed JWT, UCAN token, or ZCAP-LD proof). Free-text assertions are rejected per GP-05."
              }
            }
          },
          "minItems": 1,
          "maxItems": 5,
          "description": "Ordered provenance chain from the root authority (human user or system) to the requesting agent. Item [0] is the root delegator. Item [last] is the immediate parent. Maximum depth of 5 prevents unbounded delegation chains. Per AMB-01/RES-01 resolution: delegation is NON-TRANSITIVE by default. Each link must carry its own cryptographic proof. The chain is verified bottom-up: if any link is invalid, expired, or revoked, the entire chain is invalid. Aligned with UCAN specification: derived capabilities cannot exceed their parent."
        }
      }
    },

    "intent": {
      "type": "object",
      "description": "Section 3.2 — What the agent wants to do and to what target. Answers: WHAT is being requested?",
      "required": ["action", "resource", "parameters_hash"],
      "additionalProperties": false,
      "properties": {
        "action": {
          "type": "string",
          "enum": [
            "READ",
            "WRITE",
            "DELETE",
            "EXECUTE",
            "DELEGATE",
            "APPROVE",
            "SUSPEND",
            "TERMINATE",
            "DECRYPT"
          ],
          "description": "Deterministic verb from the fixed Sarathi Action Vocabulary. These 9 verbs are the ONLY operations the PDP recognizes. No fuzzy verbs ('Process', 'Handle', 'Manage') are permitted. Each verb maps to specific Canon rules: DELETE triggers AI-53 (Write-Only Bucket) checks, DELEGATE triggers ID-08 (Delegation Token Requirement), APPROVE triggers EL-43/RES-12 (Segregation of Duties), SUSPEND/TERMINATE trigger class precedence checks per RES-13. Maps to XACML Action-ID attribute."
        },
        "resource": {
          "type": "object",
          "required": ["resource_type", "resource_id", "data_classification"],
          "additionalProperties": false,
          "properties": {
            "resource_type": {
              "type": "string",
              "minLength": 1,
              "maxLength": 128,
              "pattern": "^[A-Z][A-Z0-9_]{0,127}$",
              "description": "Resource Ontology Type from the registered asset type registry (e.g., 'S3_BUCKET', 'DB_TABLE', 'API_ENDPOINT', 'AGENT_STATE_RECORD', 'CANON_RULE', 'BHIV_BUCKET'). Must match exactly against the Sarathi Resource Registry. Unknown resource types are rejected per INV-07."
            },
            "resource_id": {
              "type": "string",
              "minLength": 1,
              "maxLength": 2048,
              "description": "Fully qualified, pre-canonicalized resource path or URI. MUST NOT contain: relative path components ('..', '.'), null bytes ('\\x00'), URL encoding of path separators ('%2F', '%5C'), or Unicode normalization variants of the above. Per AMB-11/RES-11: canonicalization-before-authorization is mandatory. The caller is responsible for canonicalization. The PDP verifies it was done correctly; it does not do it. Maps to XACML Resource-ID."
            },
            "data_classification": {
              "type": "string",
              "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
              "description": "Data sensitivity level as declared by the caller. CRITICAL: Per Section 6.7 of the Task 3 PDP Interface Spec — the PDP MUST cross-reference this against the Resource Registry. Agent-supplied classifications are hints, not facts. If the registry says CONFIDENTIAL and the agent says PUBLIC, the registry wins. This field exists so the PDP can detect classification downgrade attempts — an agent claiming a RESTRICTED resource is PUBLIC is an immediate anomaly signal."
            }
          }
        },
        "parameters_hash": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$",
          "description": "SHA-256 hash of the serialized action parameters (the actual payload the agent will send to the downstream resource). The PDP does not inspect parameters — it is not a content filter. But the hash is included in the audit record and in the capability token, enabling downstream resources to verify that the action performed matches the action authorized. Prevents TOCTOU attacks where parameters change between authorization and execution. Aligned with CWE-367 (TOCTOU) prevention."
        }
      }
    },

    "authority": {
      "type": "object",
      "description": "Section 3.3 — Cryptographic proof of authorization. Answers: BY WHAT RIGHT is this requested?",
      "required": ["capability_token"],
      "additionalProperties": false,
      "properties": {
        "capability_token": {
          "type": "string",
          "minLength": 1,
          "maxLength": 8192,
          "description": "Signed JWT issued by the Sarathi-trusted Identity Provider (IdP). This is the PRIMARY authentication and authorization credential. The PDP verifies: (1) Signature validity against the IdP's public key (Ed25519 per operational parameters), (2) `sub` claim matches `agent_identity.agent_id`, (3) `exp` claim is not past (maximum token TTL: 60 seconds per Canon MUST-FIX MF-05), (4) `iss` claim matches the registered IdP issuer, (5) `scope` claim encompasses the requested action and resource, (6) `jti` (JWT ID) is unique within the deduplication window. Per Canon AC-21: if this field is missing or null, the verdict is DENY. Per Canon AC-22: if the signature is invalid, the verdict is DENY with 'Forgery Attempt' alert. Per Canon AC-24: if expired, the verdict is DENY. There is no grace period for expired tokens."
        },
        "delegation_token": {
          "type": "string",
          "maxLength": 8192,
          "description": "CONDITIONALLY REQUIRED. Mandatory when `agent_identity.agent_class` is 'USER_PROXY'. This is a separate signed JWT proving that a specific human user delegated specific scopes to this agent. Per Canon ID-08: absence when acting as proxy = DENY with 'Delegation Required'. Per AMB-01/RES-01: delegation tokens are NON-TRANSFERABLE. The `sub` claim must match the root of the delegation_chain. The scopes must be a SUBSET of the capability_token scopes (authority only shrinks through delegation, per capability theory). The delegation_token is verified against the human user's public key, NOT the IdP's key."
        },
        "break_glass_token": {
          "type": "string",
          "maxLength": 8192,
          "description": "CONDITIONALLY REQUIRED. Mandatory for operations that would normally be denied but are overridden under emergency protocol. Per Canon AC-26/AC-27 and AMB-05/RES-05: emergency access MUST flow through governance, not around it. This token must be a cryptographically signed assertion from the Break Glass Ticket Authority (not a ticket ID string, not a free-text justification). The PDP verifies: (1) Ticket Authority signature, (2) Ticket is not expired, (3) Ticket scope covers the requested action, (4) Ticket has not been used before (single-use). Absence when break-glass is required = DENY with 'ERR_INSUFFICIENT_PROOF'. Per RES-05: free-text emergency claims are ignored per GP-05."
        }
      }
    },

    "context": {
      "type": "object",
      "description": "Section 3.4 — Environmental and situational metadata. Answers: UNDER WHAT CONDITIONS is this requested?",
      "required": ["request_timestamp", "source_ip", "environment", "policy_version_hash"],
      "additionalProperties": false,
      "properties": {
        "request_timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "ISO-8601 UTC timestamp of when the request was constructed by the caller. Used for: (1) Replay prevention — rejected if older than MAX_REQUEST_AGE (5000ms), (2) Future-dating detection — rejected if more than MAX_CLOCK_SKEW (1000ms) in the future, (3) Stale revocation detection per AMB-04/RES-04 — if this timestamp is fresher than the PDP's CRL, the PDP's state is considered stale and the PDP halts (Zanzibar zookie model), (4) Audit trail sequencing. Maps to XACML Environment current-time attribute."
        },
        "source_ip": {
          "type": "string",
          "format": "ipv4",
          "description": "IPv4 address of the requesting agent's network endpoint. Used for: (1) Geofencing enforcement when EL-40 is implemented, (2) Anomaly detection — a sudden change in source IP for the same agent session is an indicator of session hijacking, (3) Audit trail enrichment. Note: This field is informational for current policy evaluation but MUST be present for audit completeness. The PDP does not trust this field for authorization decisions (IP spoofing is trivial) — it is defense-in-depth context."
        },
        "environment": {
          "type": "string",
          "enum": ["PRODUCTION", "STAGING", "DEVELOPMENT", "SANDBOX"],
          "description": "Deployment environment classification. Affects policy evaluation: (1) PRODUCTION — full policy enforcement, no exemptions, (2) STAGING — full policy enforcement, penetration testing exemptions per Canon ID-10, (3) DEVELOPMENT — full policy enforcement with relaxed rate limits, (4) SANDBOX — full policy enforcement with synthetic data isolation. CRITICAL: There is no environment that bypasses governance. Per Canon Section 6.6: 'God Mode does not exist in a sovereign system.' The environment affects WHICH policies apply, not WHETHER policies apply."
        },
        "policy_version_hash": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$",
          "description": "SHA-256 hash of the policy bundle that the caller believes is current. The PDP compares this against its loaded policy bundle hash. A mismatch indicates policy version drift — the caller is operating against stale rules. Per AMB-04/RES-04 and Canon LS-15 (State Synchronization): if the policy version has changed, the token is invalidated and the agent must re-authenticate against current policy. This prevents TOCTOU attacks where a token was issued under old permissive policy and used after restrictive policy is deployed. Aligned with OPA bundle hash verification pattern."
        }
      }
    },

    "risk_classification": {
      "type": "object",
      "description": "Section 3.5 — Caller's self-assessment of the risk profile of this request. Answers: HOW DANGEROUS is this action?",
      "required": ["action_sensitivity", "reversibility", "blast_radius"],
      "additionalProperties": false,
      "properties": {
        "action_sensitivity": {
          "type": "string",
          "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
          "description": "The caller's assessment of the sensitivity level of the requested action. LOW = read-only, non-PII, non-financial. MEDIUM = write operations, internal data. HIGH = PII access, financial operations, cross-tenant. CRITICAL = DECRYPT, DELETE on restricted resources, DELEGATE, APPROVE, SUSPEND, TERMINATE operations. CRITICAL: As with data_classification, the PDP cross-references this against the Action-Sensitivity Registry. Understatement is an anomaly signal. An agent claiming LOW sensitivity for a DELETE on RESTRICTED data triggers an immediate risk escalation. Maps to Canon EL-44 (Aggregate Risk Tracking)."
        },
        "reversibility": {
          "type": "string",
          "enum": ["REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE"],
          "description": "Whether the requested action can be undone. REVERSIBLE = read operations, idempotent writes. PARTIALLY_REVERSIBLE = data modifications with backup/rollback. IRREVERSIBLE = DELETE, TERMINATE, DECRYPT (decrypted data cannot be re-encrypted without re-collection). Irreversible actions require heightened scrutiny. Per Canon EL-42 (Safety Voting): irreversible actions on CONFIDENTIAL or RESTRICTED resources mandate additional validation gates."
        },
        "blast_radius": {
          "type": "string",
          "enum": ["SINGLE_RECORD", "COLLECTION", "SERVICE", "CROSS_SERVICE", "SYSTEM_WIDE"],
          "description": "The scope of impact if this action is executed. SINGLE_RECORD = affects one entity. COLLECTION = affects a dataset or table. SERVICE = affects an entire service's state. CROSS_SERVICE = affects multiple services. SYSTEM_WIDE = affects the governance infrastructure itself (Canon rules, agent state records, BHIV Bucket). SYSTEM_WIDE blast radius triggers Canon AC-31 (Canon Modification Control) — requires multi-party quorum. Per Canon MUST-FIX MF-04: single-admin risk is mitigated by requiring multi-party approval for system-wide actions."
        }
      }
    },

    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Section 3.6 — UUIDv4 that uniquely identifies this specific request across the entire distributed system. Used for: (1) End-to-end audit trail threading — this ID appears in the PDP decision log, the capability token, and the downstream resource execution log, creating an unbroken chain of custody, (2) Deduplication — if this ID has been seen within the DEDUP_WINDOW (60s), the request is rejected as a replay per INV-09, (3) Incident investigation — given a correlation_id, an investigator can reconstruct the complete lifecycle: who requested, what was decided, why, and what happened downstream, (4) Cross-system tracing — equivalent to W3C Trace Context trace-id for distributed tracing. This field MUST be generated by the caller. The PDP never generates correlation IDs — doing so would make the PDP a participant rather than a judge."
    }
  }
}
```

---

## 3. FIELD-LEVEL SPECIFICATION

### 3.1 Agent Identity Fields

**Purpose:** Establish WHO is making the request with cryptographic certainty.

**Why these fields and not others:** The identity section is designed around Saltzer and Schroeder's **Complete Mediation** principle — every access to every object must be checked against the authority of the subject. To check authority, you must first establish identity beyond doubt. This section implements three layers of identity verification:

| Layer | Field | What It Proves | Attack It Prevents |
|:---:|---|---|---|
| **Existence** | `agent_id` | The agent is a registered entity in the system | Unknown/unregistered agents (Canon ID-01) |
| **Version** | `agent_version` | The agent's code matches a known-good deployment | Supply chain attacks, compromised binaries |
| **Class** | `agent_class` | The agent's ontological role is declared and verifiable | Class spoofing (claiming SAFETY_MONITOR when actually DATA_PROCESSOR) |
| **Binding** | `session_binding` | The token is being used from the same TLS session it was issued to | Ghost Session attacks (AMB-09/RES-09), token theft and replay |
| **Provenance** | `delegation_chain` | The authority trail from human to agent is complete and cryptographically verifiable | Confused Deputy attacks (AMB-01/RES-01), transitive delegation exploitation |

**`agent_id` — Deep Specification:**

The agent_id is the constitutional identity of the agent. It MUST be one of:
- A **Decentralized Identifier (DID):** `did:method:specific-id` per W3C DID Core 1.0
- A **SPIFFE ID:** `spiffe://trust-domain/workload-path` per SPIFFE specification

Plain strings, email addresses, UUIDs without namespace, or human-readable names are NOT acceptable. The rationale: DIDs and SPIFFE IDs are cryptographically verifiable without calling a central authority. A DID resolves to a DID Document containing public keys. A SPIFFE ID resolves to an SVID (SPIFFE Verifiable Identity Document) containing an X.509 certificate. Both enable the PDP to verify identity using "hard physics" (cryptography) rather than "soft assertions" (string matching). This aligns with GP-05 (Observation ≠ Verification).

The agent_id MUST match the `sub` (subject) claim in the `capability_token`. If they differ, the request is carrying someone else's credential — a classic Confused Deputy scenario. Verdict: DENY with `ERR_IDENTITY_MISMATCH`.

**`delegation_chain` — Deep Specification:**

The delegation chain implements the provenance model required by Norm Hardy's Confused Deputy prevention and formalized in the UCAN (User Controlled Authorization Network) specification. Key properties:

1. **Non-Transitivity (RES-01):** Each link carries its own cryptographic proof. Agent A cannot pass User X's delegation to Agent B without User X's explicit consent manifested as a signed delegation to Agent B specifically.

2. **Attenuation Only:** Each delegation in the chain may have EQUAL OR FEWER permissions than its parent. Authority shrinks through delegation. This is the fundamental capability invariant proven in Tyler Close's "ACLs Don't" (2009): capabilities can be attenuated but never amplified.

3. **Maximum Depth = 5:** Unbounded delegation chains create computational complexity and make revocation verification exponentially expensive. 5 levels (Human → Orchestrator → Agent → Sub-Agent → Leaf) covers all legitimate Sarathi use cases. Deeper chains indicate architectural problems, not legitimate delegation.

4. **Bottom-Up Verification:** The PDP verifies the chain from the requesting agent upward to the root. If ANY link is invalid, expired, or revoked, the ENTIRE chain is invalid. There is no "partially valid" delegation.

---

### 3.2 Intent Structure

**Purpose:** Define WHAT action the agent wants to perform on WHAT resource with a tamper-evident hash of HOW.

**Why these fields and not others:** The intent section maps directly to the XACML Action + Resource attributes and implements the NIST SP 800-162 ABAC model's Action and Resource categories. It answers the second half of the authorization question: "Is subject S allowed to perform action A on resource R?"

**`action` — The Fixed Vocabulary:**

The 9 permitted verbs are a **closed enumeration**. This is a deliberate design decision aligned with the principle of **Least Surprise** in authorization systems. If the PDP accepted arbitrary action strings, policy writers would need to anticipate infinite variations ("read", "Read", "READ", "fetch", "get", "retrieve", "access", "view", "inspect"...). A closed vocabulary eliminates semantic ambiguity in policy matching. Each verb has a precise, non-overlapping definition:

| Verb | Definition | Canon Rules Triggered | Risk Profile |
|---|---|---|---|
| `READ` | Retrieve data without modification | AC-23, EL-36, EL-44 | LOW-MEDIUM (depends on data_classification) |
| `WRITE` | Create or modify data | AC-23, EL-33, EL-44 | MEDIUM-HIGH |
| `DELETE` | Permanently remove data | AI-53, EL-42, AC-23 | HIGH-CRITICAL (irreversible) |
| `EXECUTE` | Invoke a function, API, or process | AC-23, EL-42 | MEDIUM-CRITICAL (depends on target) |
| `DELEGATE` | Grant authority to another agent | ID-08, RES-01, AC-30 | HIGH (authority propagation) |
| `APPROVE` | Authorize another agent's pending action | EL-43, RES-12 | HIGH (SoD enforcement required) |
| `SUSPEND` | Temporarily disable an agent or resource | LS-12, RES-13 | HIGH (availability impact) |
| `TERMINATE` | Permanently disable an agent or resource | LS-13, LS-20, RES-13 | CRITICAL (irreversible, cascading) |
| `DECRYPT` | Access plaintext of encrypted data | AC-26, AC-27 | CRITICAL (break-glass may apply) |

**`resource.resource_id` — Canonicalization Requirement:**

Per AMB-11/RES-11, the resource_id MUST be pre-canonicalized by the caller. The PDP verifies canonicalization but does not perform it. This is critical because:

1. If the PDP canonicalizes, it must parse untrusted input — creating an injection vector.
2. Different canonicalization algorithms can produce different results — the caller knows the resource namespace.
3. Canonicalization is idempotent: `canonicalize(canonicalize(x)) == canonicalize(x)`. The PDP can verify this property without performing full canonicalization.

The PDP rejects resource_ids containing:
- `..` (directory traversal)
- `\x00` (null byte injection)
- `%2F` or `%5C` (encoded path separators)
- Mixed-case normalization variants that resolve to different paths on different filesystems

**`parameters_hash` — TOCTOU Prevention:**

This field implements the architectural solution to CWE-367 (Time-of-Check to Time-of-Use). The problem: an agent requests authorization for `READ /data/public.csv`, receives an ALLOW token, then uses that token to execute `READ /data/secrets.csv`. The parameters_hash binds the authorization to the specific parameters:

1. Caller computes `sha256(canonical_json(parameters))` and includes it in the request.
2. PDP includes the parameters_hash in the capability token it issues.
3. Downstream resource computes the same hash on the actual parameters it receives.
4. If the hashes don't match, the capability token is invalid — the action was not the action authorized.

This mirrors Google Macaroons' contextual caveats — the authorization is bound to the specific context of the request.

---

### 3.3 Authority Token Structure

**Purpose:** Provide cryptographic PROOF that the agent has the right to perform this action.

**Why three token types:** The authority section implements a **layered proof model** reflecting three distinct authority sources:

| Token | Authority Source | When Required | What It Proves |
|---|---|---|---|
| `capability_token` | Identity Provider (System) | **ALWAYS** | The agent is authenticated and has been granted scopes |
| `delegation_token` | Human User (Delegator) | When `agent_class == USER_PROXY` | A specific human authorized this specific agent for specific scopes |
| `break_glass_token` | Ticket Authority (Emergency) | When action would otherwise be denied under emergency | A pre-provisioned emergency procedure has been invoked through proper channels |

This three-layer model ensures that:
- **No action proceeds without system authentication** (capability_token is always required per AC-21).
- **Human delegation is explicit, not ambient** (delegation_token prevents Confused Deputy per RES-01).
- **Emergency access flows THROUGH governance, not AROUND it** (break_glass_token prevents panic-mode bypass per RES-05).

**Token TTL Enforcement:**

Per Canon MUST-FIX MF-05, the maximum token TTL is **60 seconds**. This is not configurable. The rationale:

- Average time from agent revocation to CRL propagation: variable (can be >500ms per RES-04).
- A token that outlives its agent's revocation creates a window of unauthorized access.
- 60 seconds is long enough for a single authorization cycle but short enough to limit the blast radius of a stolen token.
- Aligned with SPIFFE SVID short-lived certificate model and Google's BeyondCorp token rotation.

**Mutual Exclusivity Rules:**

- `delegation_token` is REQUIRED if and only if `agent_class == USER_PROXY`. Presence when not USER_PROXY is suspicious but not rejected (the token simply won't be evaluated). Absence when USER_PROXY is DENY per Canon ID-08.
- `break_glass_token` is REQUIRED if and only if the requested action + resource combination would trigger a break-glass policy (AC-26, AC-27). The PDP determines this during policy evaluation, not during input validation. If break-glass is required and absent, verdict is DENY with `ERR_INSUFFICIENT_PROOF`.

---

### 3.4 Context Object

**Purpose:** Provide the environmental CONDITIONS under which this request is being made.

**Why these fields and not others:** The context section maps to the XACML Environment attributes and NIST SP 800-207 Zero Trust Architecture's principle that "access to resources is determined by dynamic policy — including the observable state of client identity, application/service, and the requesting asset." These fields capture the state of the world at the time of the request.

**`policy_version_hash` — The Anti-Drift Sentinel:**

This is perhaps the most unusual field in the schema. Standard authorization systems (XACML, OPA, Cedar) do not require the caller to declare which policy version they expect. Sarathi does, because of a specific threat identified in the research:

> OPA starts answering queries immediately upon startup, before policy bundles finish downloading — returning `undefined` (empty object `{}`), which callers may interpret as "allowed."

The policy_version_hash forces both parties — caller and PDP — to agree on which rules are in play. If they disagree, something has changed (policy update, PDP restart, bundle propagation delay), and the safe response is to reject the request and force re-authentication against current policy. This implements Canon LS-15 (State Synchronization — "The New Enemy"):

> If Token.Timestamp < Canon.LastUpdateTimestamp → INVALIDATE Token; force re-authentication.

---

### 3.5 Risk Classification Field

**Purpose:** Declare the caller's ASSESSMENT of this request's danger level.

**Why the PDP needs the caller's risk assessment when it has its own:** The risk_classification is NOT trusted for authorization decisions. The PDP always cross-references against its own registries (see Section 3.2 on data_classification). So why require it?

1. **Anomaly Detection:** A caller consistently understating risk (claiming LOW for CRITICAL operations) is exhibiting adversarial probing behavior. The pattern can be tracked per Canon EL-44 (Aggregate Risk Tracking).

2. **Honest Caller Signal:** A caller that accurately assesses risk is more likely to be operating in good faith. This feeds into behavioral baselines that, when implemented, will enable dynamic risk scoring (currently deferred per Canon Deferred Scope Register).

3. **Audit Enrichment:** The gap between declared risk and actual risk, recorded in the audit trail, provides forensic value during incident investigation.

4. **Downstream Enforcement:** The capability token issued on ALLOW includes the PDP's risk assessment. Downstream resources can use this to apply additional controls (e.g., rate limiting HIGH-risk operations even when authorized).

**`blast_radius` — Why It Matters:**

The blast_radius field operationalizes the "principle of proportionate governance." A READ on a single PUBLIC record requires less scrutiny than a DELETE on an entire RESTRICTED collection. Without blast_radius, the PDP would need to infer scope from the resource_id — which may not be possible (is `/data/users` a single record or a collection?). By requiring explicit declaration, the PDP can:

- Apply Canon AC-31 (Canon Modification Control) to SYSTEM_WIDE operations.
- Apply Canon EL-42 (Safety Voting) to CROSS_SERVICE irreversible operations.
- Apply Canon MUST-FIX MF-04 (Multi-Party Quorum) to SYSTEM_WIDE + IRREVERSIBLE combinations.

---

### 3.6 Correlation ID

**Purpose:** Create an unbreakable audit thread from request to decision to execution.

**Why UUIDv4 specifically:** UUIDv4 provides 122 bits of randomness, making collision probability negligible at any practical scale (p(collision) < 10⁻¹⁸ at 10 billion IDs). More importantly:

- UUIDv4 is **not sequential** — an attacker cannot predict the next correlation_id or enumerate previous ones.
- UUIDv4 is **not derived from system state** — unlike UUIDv1 (MAC address + timestamp), UUIDv4 reveals nothing about the caller's infrastructure.
- UUIDv4 is **not centrally issued** — any caller can generate one without coordinating with a central authority, preserving the PDP's non-orchestrating property (INV-06).

**The Audit Thread Model:**

```
[Caller generates correlation_id: "a1b2c3d4-..."]
        │
        ▼
[Sarathi PDP receives request with correlation_id]
        │
        ├── Logs decision with correlation_id to BHIV Bucket
        │
        ├── Includes correlation_id in capability token (if ALLOW)
        │
        ▼
[Downstream Resource receives capability token]
        │
        ├── Logs execution with correlation_id
        │
        ▼
[Audit Investigation]
        │
        └── Query BHIV Bucket + Resource Logs by correlation_id
            └── Complete chain: Request → Decision → Execution
```

This model is equivalent to the W3C Trace Context specification's trace-id, purpose-built for governance audit trails rather than performance tracing.

---

## 4. ABSENCE BEHAVIOR MATRIX

This matrix is the **definitive reference** for what happens when any field is missing. There is no "graceful degradation." Every missing field has exactly one consequence. An engineer implementing this can use this table as a test specification.

### 4.1 Top-Level Section Absence

| Section | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `agent_identity` | **YES** | DENY — Cannot evaluate WHO is asking | `ERR_SCHEMA_VIOLATION` | 400 | GP-01: No identity = no implicit permission. AC-21: Zero Trust Default. |
| `intent` | **YES** | DENY — Cannot evaluate WHAT is requested | `ERR_SCHEMA_VIOLATION` | 400 | GP-01: No intent = nothing to evaluate. |
| `authority` | **YES** | DENY — Cannot verify BY WHAT RIGHT | `ERR_NO_AUTH` | 401 | AC-21: Missing token = Zero Trust denial. AC-22: No proof = no trust. |
| `context` | **YES** | DENY — Cannot evaluate CONDITIONS | `ERR_SCHEMA_VIOLATION` | 400 | GP-06: Unknown context = hostile context. |
| `risk_classification` | **YES** | DENY — Cannot assess DANGER level | `ERR_SCHEMA_VIOLATION` | 400 | EL-44: No risk signal = maximum assumed risk = DENY. |
| `correlation_id` | **YES** | DENY — Cannot audit this request | `ERR_SCHEMA_VIOLATION` | 400 | AI-53: Unauditable requests are ungovernable requests. |

### 4.2 Nested Field Absence — Agent Identity

| Field Path | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `agent_identity.agent_id` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | ID-01: Anonymous agents do not exist. |
| `agent_identity.agent_version` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Audit trail requires version for vulnerability correlation. |
| `agent_identity.agent_class` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | GP-01: Unknown class = no applicable rules = DENY. |
| `agent_identity.session_binding` | **YES** | DENY | `ERR_SESSION_BINDING` | 401 | RES-09: Channel Binding is mandatory. No exceptions. |
| `agent_identity.delegation_chain` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Every agent has at least one delegator (system or human). |

### 4.3 Nested Field Absence — Intent

| Field Path | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `intent.action` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | No verb = no evaluable intent. |
| `intent.resource.resource_type` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Unknown resource type = no applicable policy. |
| `intent.resource.resource_id` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | No target = nothing to authorize against. |
| `intent.resource.data_classification` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Missing classification = assumed RESTRICTED (worst-case per GP-06). |
| `intent.parameters_hash` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Missing hash = TOCTOU vulnerability = ungovernable. |

### 4.4 Nested Field Absence — Authority

| Field Path | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `authority.capability_token` | **YES** | DENY | `ERR_NO_AUTH` | 401 | AC-21: This is the Zero Trust gate. No token = no trust = no access. |
| `authority.delegation_token` | **CONDITIONAL** | DENY (if agent_class == USER_PROXY) | `ERR_PARTIAL_AUTHORITY` | 403 | ID-08: Proxies without delegation proof are Confused Deputies. |
| `authority.break_glass_token` | **CONDITIONAL** | DENY (if break-glass required by policy) | `ERR_INSUFFICIENT_PROOF` | 403 | RES-05: Emergency without proof = social engineering attempt. |

### 4.5 Nested Field Absence — Context

| Field Path | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `context.request_timestamp` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | INV-08: No timestamp = no freshness guarantee = replay risk. |
| `context.source_ip` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | Required for audit completeness even if not used for authorization. |
| `context.environment` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | GP-06: Unknown environment = assume hostile = DENY. |
| `context.policy_version_hash` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | LS-15: No version agreement = potential policy drift = unsafe to evaluate. |

### 4.6 Nested Field Absence — Risk Classification

| Field Path | Required | If Absent | Error Code | HTTP | Rationale |
|---|:---:|---|---|:---:|---|
| `risk_classification.action_sensitivity` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | EL-44: No risk signal = no risk gate evaluation possible. |
| `risk_classification.reversibility` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | EL-42: Cannot apply Safety Voting without reversibility knowledge. |
| `risk_classification.blast_radius` | **YES** | DENY | `ERR_SCHEMA_VIOLATION` | 400 | AC-31: Cannot enforce quorum requirement without blast radius. |

**Summary Rule:** There are **zero** truly optional fields in this schema. Every field is either ALWAYS required or CONDITIONALLY required (and the condition is deterministic). Per Canon Task 3, Section 2.2: "There are no truly 'optional' fields for governance purposes. Every absent field either triggers a denial or is irrelevant to the current action type. There is no 'graceful degradation.'"

---

## 5. INPUT VALIDATION PIPELINE — PRE-POLICY STAGE

Input validation executes **BEFORE** any policy evaluation. These are syntactic and cryptographic checks that determine whether the request is well-formed enough to even reach the policy engine. The ordering is deliberate: cheap checks first, expensive checks last.

```
REQUEST ARRIVES
     │
     ▼
[Stage 1] ENVELOPE STRUCTURE VALIDATION
     │── Is the body valid JSON?                          → NO  → 400 ERR_MALFORMED_JSON
     │── Does it parse without unknown fields?            → NO  → 400 ERR_UNKNOWN_FIELD
     │── Are all 6 required top-level sections present?   → NO  → 400 ERR_SCHEMA_VIOLATION
     │── Are all nested required fields present?          → NO  → 400 ERR_SCHEMA_VIOLATION
     │── Do all fields match type/format/pattern?         → NO  → 400 ERR_SCHEMA_VIOLATION
     │── Is total payload size < MAX_PAYLOAD (64KB)?      → NO  → 400 ERR_PAYLOAD_TOO_LARGE
     ▼
[Stage 2] NULL AND EMPTY CHECK
     │── Are any required string fields empty ("")?       → YES → 400 ERR_NULL_INPUT
     │── Are any fields null/undefined?                   → YES → 400 ERR_NULL_INPUT
     │── Do any strings contain null bytes (\x00)?        → YES → 400 ERR_NULL_INPUT (AMB-08/RES-08)
     │── Do any strings match semantic null patterns?     → YES → 400 ERR_NULL_INPUT
     │   ("null", "none", "undefined", "nil", "N/A", "")
     ▼
[Stage 3] TIMESTAMP VALIDATION
     │── Is request_timestamp valid ISO-8601 UTC?         → NO  → 400 ERR_SCHEMA_VIOLATION
     │── Is request_timestamp > (now - MAX_REQUEST_AGE)?  → NO  → 400 ERR_REPLAY_DETECTED
     │── Is request_timestamp < (now + MAX_CLOCK_SKEW)?   → NO  → 400 ERR_CLOCK_SKEW
     ▼
[Stage 4] RESOURCE PATH CANONICALIZATION CHECK
     │── Does resource_id contain '..'?                   → YES → 400 ERR_PATH_TRAVERSAL
     │── Does resource_id contain '\x00'?                 → YES → 400 ERR_PATH_TRAVERSAL
     │── Does resource_id contain '%2F' or '%5C'?         → YES → 400 ERR_PATH_TRAVERSAL
     │── Does canonicalize(resource_id) == resource_id?   → NO  → 400 ERR_PATH_TRAVERSAL
     ▼
[Stage 5] CORRELATION ID DEDUPLICATION
     │── Has this correlation_id been seen in DEDUP_WINDOW? → YES → 400 ERR_REPLAY_DETECTED
     │── Register correlation_id in dedup store            (proceed)
     ▼
[Stage 6] POLICY VERSION AGREEMENT
     │── Does policy_version_hash match PDP's loaded bundle? → NO → 409 ERR_POLICY_VERSION_MISMATCH
     │── Is PDP's policy bundle loaded and ready?            → NO → 503 ERR_SYSTEM_UNCERTAINTY
     ▼
[Stage 7] PASSES PRE-POLICY VALIDATION
     │
     └── Request proceeds to CRYPTOGRAPHIC VALIDATION (Token verification, etc.)
         └── Then to POLICY EVALUATION (Canon rules, risk gates, etc.)
```

**Critical Design Properties:**

1. **Stages 1-5 require NO cryptographic operations.** They are pure syntactic checks. This means a malformed request is rejected in microseconds, never consuming expensive signature verification CPU cycles. This is defense against denial-of-service via malformed request floods.

2. **Stage 6 prevents a subtle class of attacks:** If the PDP just restarted and policies haven't finished loading, it MUST NOT evaluate requests against an empty policy set (which would produce `undefined`/ALLOW in naive implementations). The policy_version_hash check forces the PDP to have loaded policies before serving any request.

3. **The pipeline is a strict sequence.** There is no parallel evaluation. A failure at Stage 1 means Stages 2-7 never execute. This ensures that error codes are deterministic — the first failure found is the failure reported.

---

## 6. REJECTION TAXONOMY FOR INPUT FAILURES

Every input validation failure produces exactly one error response. The response structure for rejections is minimal and deliberately opaque:

```json
{
  "verdict": "DENY",
  "error_code": "ERR_SCHEMA_VIOLATION",
  "correlation_id": "<echoed if present, otherwise 'UNKNOWN'>",
  "timestamp": "<PDP timestamp>",
  "pdp_instance": "<PDP instance identifier>",
  "signature": "<Ed25519 signature of this response>"
}
```

**What is NOT included in rejection responses (per GP-05 and RES information exposure rules):**

| Excluded Information | Why Excluded |
|---|---|
| Which specific field was missing | Prevents attacker from iterating fields one by one to discover schema |
| What the expected format was | Prevents attacker from learning validation patterns |
| What the actual value was | Prevents reflection attacks |
| How many validation checks passed | Prevents progress-tracking toward valid requests |
| Internal policy rule IDs | Prevents policy enumeration |
| PDP internal state | Prevents reconnaissance |

**Exception:** During the **Deprecation Window** (72 hours per RES-14/AMB-14), schema violation responses MAY include `required_version` to aid legitimate agents in upgrading. After the window expires, legacy agents are indistinguishable from malformed requests.

### Complete Error Code Registry

| Error Code | HTTP Status | Trigger | Logged Severity | Retry Permitted |
|---|:---:|---|:---:|:---:|
| `ERR_MALFORMED_JSON` | 400 | Unparseable request body | WARN | YES |
| `ERR_UNKNOWN_FIELD` | 400 | `additionalProperties` violation | WARN | YES (after fixing) |
| `ERR_SCHEMA_VIOLATION` | 400 | Missing required field or type mismatch | WARN | YES (after fixing) |
| `ERR_NULL_INPUT` | 400 | Empty string, null, or semantic null detected | WARN | YES (after fixing) |
| `ERR_PAYLOAD_TOO_LARGE` | 400 | Request exceeds MAX_PAYLOAD (64KB) | WARN | YES (with smaller payload) |
| `ERR_REPLAY_DETECTED` | 400 | Stale timestamp or duplicate correlation_id | ERROR | NO — indicates replay attack |
| `ERR_CLOCK_SKEW` | 400 | Future-dated timestamp beyond tolerance | WARN | YES (after clock sync) |
| `ERR_PATH_TRAVERSAL` | 400 | Non-canonical resource_id detected | ERROR | NO — indicates injection attempt |
| `ERR_POLICY_VERSION_MISMATCH` | 409 | Caller's policy hash ≠ PDP's loaded policy | INFO | YES (after re-authentication) |
| `ERR_SYSTEM_UNCERTAINTY` | 503 | PDP cannot serve (policies not loaded, CRL stale) | CRITICAL | YES (after PDP recovers) |
| `ERR_NO_AUTH` | 401 | capability_token missing or null | ERROR | YES (with valid token) |
| `ERR_SESSION_BINDING` | 401 | session_binding missing or invalid | ERROR | NO — indicates session hijack |
| `ERR_IDENTITY_MISMATCH` | 401 | agent_id ≠ token.sub | ERROR | NO — indicates Confused Deputy |
| `ERR_PARTIAL_AUTHORITY` | 403 | delegation_token missing for USER_PROXY | ERROR | YES (with delegation token) |
| `ERR_INSUFFICIENT_PROOF` | 403 | break_glass_token missing when required | ERROR | YES (with break-glass token) |
| `ERR_BATCH_REJECTED` | 400 | Multiple intents in single request | WARN | YES (as individual requests) |

---

## 7. ANTI-PATTERNS — WHAT MUST NEVER BE ACCEPTED

These are explicit prohibitions. An engineer who encounters these patterns in a request MUST reject. An engineer who builds a system that accepts these patterns has violated the contract.

| Anti-Pattern ID | Description | Why It's Dangerous | Detection Rule |
|:---:|---|---|---|
| **AP-01** | **Wildcard scopes** (`"action": "*"`, `"resource_id": "/*"`) | Violates Least Privilege. A wildcard scope is an open door. Per Canon AC-23: scope must be specific. | Reject any field containing `*` as a value. |
| **AP-02** | **Self-referential intents** (agent requesting WRITE to its own `agent_state_record`) | Violates GP-07 (No Feedback Loops). The governed cannot edit the governor. Per Canon LS-18: self-modification is blocked. | `intent.resource.resource_id` must not resolve to the requesting agent's own state record. |
| **AP-03** | **Future-dated delegation** (`delegation_chain[n].delegated_at` in the future) | A delegation that hasn't happened yet cannot grant authority now. | Reject if any `delegated_at` > `now + MAX_CLOCK_SKEW`. |
| **AP-04** | **Token in URL parameters** (capability_token passed as query string) | Tokens in URLs are logged in server access logs, browser history, and referrer headers. Per RFC 9700 (OAuth 2.0 Security BCP): bearer tokens MUST NOT appear in URIs. | The PDP accepts requests ONLY via POST body. GET requests with tokens in URLs are rejected with `ERR_SCHEMA_VIOLATION`. |
| **AP-05** | **Nested JSON in string fields** (e.g., `"agent_id": "{\"real_id\": \"admin\"}"`) | JSON injection. A parser that evaluates nested JSON in string fields may extract unintended values. Per GP-04: untrusted input is not parsed; it is validated against patterns. | All string fields are validated against their declared patterns. Strings containing `{`, `}`, `[`, `]` where not expected are rejected. |
| **AP-06** | **Unicode normalization attacks** (e.g., `resource_id` uses fullwidth characters: `＄ｅｃｒｅｔｓ` instead of `secrets`) | Different Unicode normalization forms (NFC, NFD, NFKC, NFKD) can make different strings look identical or make identical strings look different. | Normalize all string fields to NFC before validation. Reject strings containing characters outside the expected character class for that field. |
| **AP-07** | **Empty delegation chain** (`"delegation_chain": []`) | An empty chain means no authority source. The agent appeared from nowhere. | `minItems: 1` enforced at schema level. |
| **AP-08** | **Duplicate delegation chain entries** (same principal_id appears twice) | Circular delegation: A delegates to B delegates to A. Creates infinite loops in chain verification. | Verify all `principal_id` values in the chain are unique. |

---

## 8. SCHEMA EVOLUTION RULES

Schemas evolve. This section defines HOW without breaking the fail-closed guarantee.

| Rule ID | Rule | Rationale |
|:---:|---|---|
| **SE-01** | New REQUIRED fields can only be added with a **72-hour Deprecation Window** (per RES-14/AMB-14). During this window, requests missing the new field receive DENY with `ERR_SCHEMA_DEPRECATED` and a `required_version` field. After the window: standard `ERR_SCHEMA_VIOLATION` with no special treatment. | Prevents mass bricking of legitimate agents while maintaining fail-closed on new security requirements. |
| **SE-02** | REQUIRED fields can NEVER be made optional. Security requirements are monotonically increasing. | Removing a required field means past rejections were "wrong" — it retroactively legitimizes previously hostile requests. |
| **SE-03** | Enum values can be ADDED but never REMOVED from `action` or `agent_class`. | Removing an enum value would make existing valid requests suddenly invalid. Adding values extends capabilities under governance. |
| **SE-04** | The `$id` field contains a semantic version (`v1.0.0`). Major version increments (v1 → v2) indicate breaking changes requiring the Deprecation Window. Minor/patch increments are backward-compatible. | Callers can detect breaking changes from the schema version without parsing the full schema. |
| **SE-05** | Schema changes require **multi-party quorum** per Canon MUST-FIX MF-04. No single administrator can modify the input contract. | The input schema IS the constitution's front door. Changing it unilaterally is equivalent to rewriting the constitution. |
| **SE-06** | Every schema version is archived in the BHIV Bucket as a write-only record. | Per Canon AI-57: Policy Version Archive. Enables forensic reconstruction of what schema was in effect during any historical request. |

---


## 9 Relationship to Previous Sarathi Tasks

| Previous Artifact | How This Schema Relates |
|---|---|
| **Task 1 — Governance Validation Report** | Addresses Assumptions A1 (Semantic Consistency — fixed vocabulary eliminates ambiguity), A2 (Identity Persistence — session_binding + short-lived tokens), A3 (Orchestrator Compliance — parameters_hash prevents token misuse), A7 (Intent Honesty — parameters_hash binds intent to action). |
| **Task 2 — Canon Formalization (60 Rules)** | Implements Canon Rules AC-21, AC-22, AC-23, AC-24, ID-01, ID-02, ID-08, EL-33, LS-15 as schema-level enforcement. 35 compliance matrix entries map to fields in this schema. |
| **Task 3 — Ambiguity Register (14 Scenarios)** | Schema prevents AMB-01 (delegation_chain non-transitivity), AMB-04 (policy_version_hash), AMB-05 (break_glass_token structure), AMB-08 (null detection), AMB-09 (session_binding), AMB-11 (canonicalization check), AMB-14 (schema evolution rules). |
| **Task 3 — PDP Interface Spec (17-Step Pipeline)** | This schema feeds directly into Steps 1-4 (input validation) and Steps 5-8 (cryptographic validation) of the existing pipeline. The pre-policy validation in Section 5 is the implementation specification for Steps 1-4. |

---

**END OF SARATHI REQUEST SCHEMA — MINIMAL INPUT CONTRACT**

---

## 10. EXTENDED REQUEST FIELDS (GAP RESOLUTION PHASE)

*Added to support Delegation Capability Tokens (Gap 2), Runtime Enforcement (Gap 1), and Audit Trail Integrity (Gap 5).*

### EXT-1: Delegation Capability Token (Biscuit)

When the requesting agent operates under a delegated authority chain using Biscuit cryptographic tokens (Gap 2 resolution), the `authority` section accepts an additional field:

```json
{
  "authority": {
    "capability_token": "...",
    "delegation_token": "...",
    "break_glass_token": "...",
    "delegation_capability_token": {
      "type": "string",
      "maxLength": 16384,
      "description": "Biscuit v2 token (base64url-encoded) carrying cryptographic delegation chain with Ed25519 root signature. Contains authority block (human origin, scope, max_cost, max_delegation_depth, shutdown_deadline, data_classification_ceiling) and zero or more attenuation blocks (each restricting permissions further). Each block carries a unique revocation_id for cascading revocation. Verified offline using root public key — no IdP call required."
    },
    "dpop_proof": {
      "type": "string",
      "maxLength": 4096,
      "description": "DPoP proof-of-possession JWT (RFC 9449). Binds the Biscuit token to the requesting agent's identity. Contains: ath (SHA-256 hash of delegation_capability_token), spiffe_id (agent workload identity from SPIFFE/SPIRE attestation), jti (unique proof ID for replay prevention). Verified by: (1) signature matches agent's key, (2) ath matches Biscuit hash, (3) spiffe_id matches workload attestation, (4) jti not in replay cache."
    }
  }
}
```

**Validation Rules:**
- If `delegation_capability_token` is present, `dpop_proof` is REQUIRED (never accept a Biscuit without proof-of-possession)
- Biscuit root signature verified against registered root public key (Ed25519)
- Delegation depth counted from attenuation blocks: `depth <= authority_block.max_delegation_depth`
- Every block's `revocation_id` checked against CRL (LS-15)
- `data_classification_ceiling` propagated to all downstream decisions (RES-16)
- Attenuation blocks can ONLY restrict, never expand (GP-08 — cryptographically enforced)

### EXT-2: TLS Fingerprint Context

For audit trail integrity (Gap 5 resolution), the `context` section accepts additional fields:

```json
{
  "context": {
    "request_timestamp": "...",
    "source_ip": "...",
    "environment": "...",
    "policy_version_hash": "...",
    "tls_fingerprint": {
      "type": "object",
      "required": ["ja3"],
      "properties": {
        "ja3": {
          "type": "string",
          "description": "JA3 TLS client fingerprint hash (MD5 of SSLVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats). Used for device identification in audit trail."
        },
        "ja4": {
          "type": "string",
          "description": "JA4 TLS fingerprint (improved successor to JA3 with protocol version separation). Optional but recommended."
        }
      }
    },
    "pep_type": {
      "type": "string",
      "enum": ["GATEWAY", "SIDECAR", "EMBEDDED"],
      "description": "Identifies which PEP layer is forwarding this request. GATEWAY = API gateway/load balancer (coarse-grained, <15ms). SIDECAR = OPA/Cedar sidecar per pod (fine-grained, <1ms). EMBEDDED = Cedar Rust crate in-process (<100μs). Logged in audit trail for enforcement layer tracing."
    }
  }
}
```

### EXT-3: Updated Input Invariants

| ID | Invariant | Status |
|---|---|---|
| INV-01 through INV-10 | (Unchanged — see Section 1) | ✅ Original |
| **INV-11** | **DPoP Binding** — If delegation_capability_token is present, dpop_proof MUST be present and valid. Biscuit without proof = DENY. | NEW |
| **INV-12** | **Delegation Depth Bound** — delegation_capability_token depth (counted from attenuation blocks) MUST NOT exceed max_delegation_depth from authority block. | NEW |
| **INV-13** | **Classification Ceiling** — No request may target a resource whose data_classification exceeds the Biscuit's data_classification_ceiling. | NEW |

### EXT-4: Updated Anti-Patterns

| Anti-Pattern ID | Description | Detection Rule |
|---|---|---|
| **AP-09** | **Biscuit without DPoP** — Presenting a delegation_capability_token without dpop_proof allows token theft and replay | Reject if delegation_capability_token present but dpop_proof absent |
| **AP-10** | **DPoP spiffe_id mismatch** — DPoP proof's spiffe_id doesn't match agent_identity.agent_id's SPIFFE component | Reject with ERR_PROOF_INVALID |
| **AP-11** | **Attenuation expansion** — A Biscuit attenuation block that grants broader permissions than its parent block (violates GP-08) | Reject with ERR_DELEGATION_VIOLATION + CRITICAL alert (indicates implementation bug or forgery) |

---

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Total Required Sections | 6 |
| Total Required Fields (Leaf) | 24 (original) + 4 (gap extensions) |
| Conditional Fields | 4 (delegation_token, break_glass_token, delegation_capability_token, dpop_proof) |
| Interface Invariants | 13 (10 original + 3 from gap resolution) |
| Absence Behaviors Defined | 26 |
| Error Codes Defined | 16 + 5 (ERR_DELEGATION_VIOLATION, ERR_DELEGATION_DEPTH_EXCEEDED, ERR_CLASSIFICATION_EXCEEDED, ERR_PROOF_INVALID, ERR_REPLAY_DETECTED for DPoP) |
| Anti-Patterns Defined | 11 (8 original + 3 from gap resolution) |
| Schema Evolution Rules | 6 |
| Pre-Policy Validation Stages | 7 |
| Industry Standards Referenced | XACML 3.0, NIST SP 800-162, NIST SP 800-207, RFC 9449, RFC 9700, SPIFFE/SPIRE, UCAN, W3C DID, Google Zanzibar, AWS Cedar, CWE-367, Biscuit (Eclipse Foundation), DeepMind DCT, EU AI Act Art. 12 |
| Canon Rules Implemented | AC-21, AC-22, AC-23, AC-24, AC-26, AC-27, AC-30, AC-31, ID-01, ID-02, ID-05, ID-06, ID-07, ID-08, ID-09, ID-10, EL-33, EL-36, EL-42, EL-43, EL-44, LS-12, LS-13, LS-15, LS-18, LS-19, LS-20, AI-53, AI-57 |
| Global Principles Invoked | GP-01, GP-04, GP-05, GP-06, GP-07, GP-08, GP-09 |
| Ambiguity Resolutions Referenced | RES-01, RES-04, RES-05, RES-08, RES-09, RES-11, RES-12, RES-13, RES-14, RES-15, RES-16, RES-17 |

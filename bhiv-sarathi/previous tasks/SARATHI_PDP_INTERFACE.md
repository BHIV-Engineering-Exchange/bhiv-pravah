# SARATHI PDP INTERFACE SPECIFICATION

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Test Task 3 — Ambiguity Resolution & PDP Interface Definition (Day 3)

---

## PURPOSE

This document defines the **strict Input/Output contract** for the Sarathi Policy Decision Point. It is designed to be:

- **Ambiguity-Safe** — Every undefined input state maps to DENY
- **Fail-Closed** — Every failure mode defaults to restriction, never permission
- **Implementable** — Engineers can build against this spec without interpretation

This is the law. Implementers who deviate from this contract void system safety.

---

## 1. INTERFACE PHILOSOPHY

The Sarathi PDP interface is:

| Property | Definition |
|---|---|
| **Idempotent** | The same request with the same state produces the same verdict. No side effects. |
| **Atomic** | Each request is evaluated independently. No batching. No pipelining. |
| **Synchronous** | Request in, verdict out. No callbacks, webhooks, or deferred responses. |
| **Non-Negotiating** | The PDP does not ask for more information. It does not suggest alternatives. Incomplete requests are denied. |
| **Non-Orchestrating** | The PDP does not call external services to gather evidence. All evidence must arrive with the request. |

The PDP implements the **Action Authorization Boundary (AAB)**: execution is physically impossible without a signed verdict. The PDP accepts an Intent and returns a Verdict. It does not perform actions. It does not queue requests. It does not "negotiate."

---

## 2. REQUEST SCHEMA (INPUT CONTRACT)

Implementers must provide a valid JSON object matching this schema. **Failure to match any constraint results in an immediate DENY (HTTP 400).** There is no partial validation. There is no "try your best."

### 2.1 Schema Definition

```json
{
  "$schema": "http://sarathi.governance/v1/intent.json",
  "title": "Sarathi Action Intent",
  "type": "object",
  "description": "The atomic unit of governance. Represents an Agent's intent to perform an Action on a Resource.",
  "required": ["id", "timestamp", "agent", "action", "resource", "proofs"],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique Request ID (UUIDv4). Used for audit tracing and non-repudiation. Must be unique per request."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 UTC. Requests older than MAX_REQUEST_AGE (5000ms) are rejected (Replay Prevention)."
    },
    "agent": {
      "type": "object",
      "required": ["id", "version", "session_binding"],
      "additionalProperties": false,
      "properties": {
        "id": {
          "type": "string",
          "minLength": 1,
          "description": "Immutable Agent UUID (DID or internal ID). Must match the token's subject claim."
        },
        "version": {
          "type": "string",
          "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+$",
          "description": "Semantic Version of Agent Code (e.g., v1.2.0). Required for audit trail."
        },
        "session_binding": {
          "type": "string",
          "minLength": 1,
          "description": "SHA-256 hash of the TLS client certificate. Binds the token to the transport channel (Channel Binding). See RES-09."
        }
      }
    },
    "action": {
      "type": "string",
      "enum": ["READ", "WRITE", "DELETE", "EXECUTE", "DELEGATE", "APPROVE", "SUSPEND", "TERMINATE", "DECRYPT"],
      "description": "Deterministic verb from the fixed vocabulary. No fuzzy actions like 'Process' or 'Handle'."
    },
    "resource": {
      "type": "object",
      "required": ["type", "id", "classification"],
      "additionalProperties": false,
      "properties": {
        "type": {
          "type": "string",
          "description": "Resource Ontology Type (e.g., 'S3_BUCKET', 'DB_TABLE', 'API_ENDPOINT'). Must match registered asset types."
        },
        "id": {
          "type": "string",
          "minLength": 1,
          "description": "Fully qualified canonical path/URI. Must be pre-canonicalized by the caller (no '..' sequences, no null bytes, no relative paths). See RES-11."
        },
        "classification": {
          "type": "string",
          "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
          "description": "Data sensitivity level. Must match the registered asset tag in the resource registry."
        }
      }
    },
    "proofs": {
      "type": "object",
      "required": ["capability_token"],
      "additionalProperties": false,
      "properties": {
        "capability_token": {
          "type": "string",
          "minLength": 1,
          "description": "Signed JWT from IdP. Contains agent identity, scopes, and expiry. This is the primary authentication credential."
        },
        "delegation_token": {
          "type": "string",
          "description": "Required if acting as Proxy (User Proxy class). Proves delegated authority from a human user. Non-transferable (RES-01)."
        },
        "break_glass_token": {
          "type": "string",
          "description": "Required for AC-26/AC-27 override scenarios. Must be a cryptographically signed assertion from the Ticket Authority (RES-10). Not a ticket ID string."
        }
      }
    }
  }
}
```

### 2.2 Required vs. Optional Fields

| Field Path | Required | Absence Behavior |
|---|:---:|---|
| `id` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `timestamp` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `agent.id` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `agent.version` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `agent.session_binding` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` (Channel Binding mandatory per RES-09) |
| `action` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `resource.type` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `resource.id` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `resource.classification` | **YES** | DENY — `ERR_SCHEMA_VIOLATION` |
| `proofs.capability_token` | **YES** | DENY — `ERR_NO_AUTH` |
| `proofs.delegation_token` | Conditional | Required if agent class is Proxy. Absence for Proxy → DENY — `ERR_PARTIAL_AUTHORITY` |
| `proofs.break_glass_token` | Conditional | Required for Break Glass actions. Absence → DENY — `ERR_INSUFFICIENT_PROOF` |

**Rule:** There are no truly "optional" fields for governance purposes. Every absent field either triggers a denial or is irrelevant to the current action type. There is no "graceful degradation."

### 2.3 Input Validation Rules (Pre-Policy)

These checks execute **before** any policy evaluation. They are the first barrier. A request that fails these checks never reaches the policy engine.

| Check | Condition | Result |
|---|---|---|
| Schema Validation | JSON does not match schema | DENY — `ERR_SCHEMA_VIOLATION` (400) |
| Timestamp Freshness | `now() - request.timestamp > 5000ms` | DENY — `ERR_REPLAY_DETECTED` (400) |
| Timestamp Future | `request.timestamp > now() + 1000ms` | DENY — `ERR_CLOCK_SKEW` (400) |
| UUID Format | `id` is not valid UUIDv4 | DENY — `ERR_SCHEMA_VIOLATION` (400) |
| Null Detection | Any required field is null/empty/"null"/0x00 | DENY — `ERR_NULL_INPUT` (400) — per RES-08 |
| Unknown Fields | `additionalProperties` detected | DENY — `ERR_SCHEMA_VIOLATION` (400) |
| Action Vocabulary | `action` not in enum | DENY — `ERR_UNKNOWN_ACTION` (400) |
| Path Canonicalization | `resource.id` contains `..`, `%2e`, null bytes | DENY — `ERR_PATH_TRAVERSAL` (400) — per RES-11 |

---

## 3. RESPONSE SCHEMA (OUTPUT CONTRACT)

Sarathi returns a **deterministic, signed verdict**. Downstream systems **MUST** check the `verdict` field. If `verdict != "ALLOW"`, execution **MUST NOT** proceed. The verdict is cryptographically signed; tampering is detectable.

### 3.1 Schema Definition

```json
{
  "$schema": "http://sarathi.governance/v1/verdict.json",
  "title": "Sarathi Governance Verdict",
  "type": "object",
  "required": ["request_id", "verdict", "timestamp", "audit_id", "signature"],
  "properties": {
    "request_id": {
      "type": "string",
      "format": "uuid",
      "description": "Echoed from the request. Links Intent to Verdict for non-repudiation."
    },
    "verdict": {
      "type": "string",
      "enum": ["ALLOW", "DENY", "HALT"],
      "description": "ALLOW: Proceed with constraints. DENY: Stop, do not execute. HALT: Stop, suspend agent immediately (Critical Threat Detected)."
    },
    "reason_code": {
      "type": "string",
      "description": "Machine-readable error code (e.g., 'ERR_SCOPE_MISMATCH'). For logging and debugging ONLY. Never for control flow."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 UTC. When the verdict was issued. Establishes temporal ordering of decisions."
    },
    "audit_id": {
      "type": "string",
      "format": "uuid",
      "description": "Reference ID for the corresponding entry in the BHIV Bucket. Enables post-hoc forensics."
    },
    "constraints": {
      "type": "object",
      "description": "Additional obligations for the Orchestrator when verdict is ALLOW. Examples: { 'mask_pii': true, 'ttl': 300, 'max_output_tokens': 1000 }. Ignored on DENY/HALT."
    },
    "signature": {
      "type": "string",
      "description": "Cryptographic signature of this verdict envelope by the Sarathi Governance Key (Ed25519 or equivalent). Orchestrators MUST verify this signature before acting on the verdict."
    }
  }
}
```

### 3.2 Verdict Semantics

| Verdict | Meaning | Orchestrator Obligation | Agent Effect |
|---|---|---|---|
| **ALLOW** | Action is authorized for this specific request at this specific time | Execute the action; enforce `constraints`; verify `signature` | Proceed |
| **DENY** | Action is not authorized | Do NOT execute; log the denial; return appropriate error to agent | Blocked |
| **HALT** | Critical threat detected. Action denied and agent is suspended | Do NOT execute; immediately revoke agent's active sessions; alert Security | Agent suspended, all tokens invalidated |

### 3.3 Reason Code Vocabulary

| Reason Code | Category | Description |
|---|---|---|
| `ERR_SCHEMA_VIOLATION` | Input | Request JSON does not match schema |
| `ERR_REPLAY_DETECTED` | Input | Timestamp too old (>5000ms) |
| `ERR_CLOCK_SKEW` | Input | Timestamp in the future (>1000ms ahead) |
| `ERR_NULL_INPUT` | Input | Required field is null/empty/semantic-null |
| `ERR_UNKNOWN_ACTION` | Input | Action verb not in vocabulary |
| `ERR_PATH_TRAVERSAL` | Input | Resource ID contains traversal sequences |
| `ERR_NO_AUTH` | Auth | Capability token missing |
| `ERR_TOKEN_INVALID` | Auth | Capability token signature invalid |
| `ERR_TOKEN_EXPIRED` | Auth | Capability token past expiry |
| `ERR_SESSION_BINDING` | Auth | Token subject ≠ TLS client identity |
| `ERR_PARTIAL_AUTHORITY` | Auth | Proxy without delegation token |
| `ERR_INSUFFICIENT_PROOF` | Auth | Break glass action without cryptographic proof |
| `ERR_SCOPE_MISMATCH` | Policy | Action/Resource outside authorized scope |
| `ERR_STATE_INVALID` | Policy | Agent in invalid state (suspended/terminated) |
| `ERR_CLASS_RESTRICTED` | Policy | Agent class prohibited for this action |
| `ERR_DATA_CLASSIFICATION` | Policy | Resource classification exceeds agent clearance |
| `ERR_SOD_VIOLATION` | Policy | Author == Approver identity violation |
| `ERR_DELEGATION_VIOLATION` | Policy | Transitive delegation attempted |
| `ERR_RUNTIME_MUTATION` | Policy | Runtime self-modification attempted |
| `ERR_MOSAIC_RISK` | Policy | Aggregate access pattern exceeded threshold |
| `ERR_SYSTEM_UNCERTAINTY` | System | CRL/State unreachable or stale |
| `ERR_INTERNAL_FAULT` | System | Unhandled exception in governance logic |
| `ERR_RATE_LIMIT` | System | Request volume exceeds safety threshold |

---

## 4. FAILURE MODES & BEHAVIOR CONTRACT (FMEA)

This section defines explicit Sarathi behavior for every failure category. This is the Failure Mode and Effects Analysis for the PDP interface. Implementers must handle these exact HTTP codes and response shapes.

---

### Failure Mode A: Missing Fields / Malformed Input

**Condition:** Input JSON violates the schema — missing required fields, wrong types, unknown fields, action not in enum, invalid UUID format.

**Sarathi Verdict:** DENY  
**HTTP Status:** `400 Bad Request`

```json
{
  "request_id": "<echoed or 'UNKNOWN'>",
  "verdict": "DENY",
  "reason_code": "ERR_SCHEMA_VIOLATION",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `MALFORMED_INPUT`. High frequency of 400s from the same agent triggers Mosaic/DoS detection (Rule EL-37).

---

### Failure Mode B: Stale State / System Uncertainty

**Condition:** Sarathi cannot reach the Revocation List (CRL), the internal clock is desynchronized (NTP drift > 500ms), or the policy database is unreachable.

**Sarathi Verdict:** DENY (FAIL-CLOSED)  
**HTTP Status:** `503 Service Unavailable`

```json
{
  "request_id": "<echoed>",
  "verdict": "DENY",
  "reason_code": "ERR_SYSTEM_UNCERTAINTY",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `SYSTEM_INTEGRITY_FAIL`. Immediate alert to Operations. All pending requests during uncertainty window are denied.

**Recovery:** When connectivity/consistency is restored, Sarathi resumes normal operation. No automatic retry of denied requests. Each must be resubmitted.

---

### Failure Mode C: Partial Authority (Proxy Without Delegation)

**Condition:** Agent is classified as a Proxy (User Proxy class) but provides only a root capability token. The required `delegation_token` is absent.

**Sarathi Verdict:** DENY  
**HTTP Status:** `403 Forbidden`

```json
{
  "request_id": "<echoed>",
  "verdict": "DENY",
  "reason_code": "ERR_PARTIAL_AUTHORITY",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `PRIVILEGE_VIOLATION`. Repeated violations trigger enhanced monitoring of the agent.

---

### Failure Mode D: Internal Error / Logic Fault

**Condition:** Sarathi encounters an unhandled exception, null pointer, policy evaluation loop, or any internal bug that prevents a deterministic verdict.

**Sarathi Verdict:** DENY (FAIL-CLOSED)  
**HTTP Status:** `500 Internal Server Error`

```json
{
  "request_id": "<echoed or 'UNKNOWN'>",
  "verdict": "DENY",
  "reason_code": "ERR_INTERNAL_FAULT",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Full core dump written to Cold Storage. Alert to Security Engineering. This is a governance-critical bug and must be treated as a production incident.

**Critical:** Even when Sarathi is broken, the answer is DENY. There is no state where a fault results in ALLOW.

---

### Failure Mode E: Token Expired / Invalid

**Condition:** The `capability_token` signature fails verification, or the token's `exp` claim is in the past.

**Sarathi Verdict:** DENY  
**HTTP Status:** `401 Unauthorized`

```json
{
  "request_id": "<echoed>",
  "verdict": "DENY",
  "reason_code": "ERR_TOKEN_EXPIRED",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `AUTH_FAILURE`. Repeated failures from the same agent trigger HALT consideration.

---

### Failure Mode F: Channel Binding Mismatch

**Condition:** `Token.Subject` does not match the transport-layer identity (`TLS.ClientCertificate.Subject`). See RES-09.

**Sarathi Verdict:** DENY  
**HTTP Status:** `401 Unauthorized`

```json
{
  "request_id": "<echoed>",
  "verdict": "DENY",
  "reason_code": "ERR_SESSION_BINDING",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `SESSION_BINDING_MISMATCH`. This is a strong indicator of token theft. Immediate security alert.

---

### Failure Mode G: Replay Detection

**Condition:** `now() - request.timestamp > MAX_REQUEST_AGE (5000ms)` or the request `id` has been seen before within the deduplication window.

**Sarathi Verdict:** DENY  
**HTTP Status:** `400 Bad Request`

```json
{
  "request_id": "<echoed>",
  "verdict": "DENY",
  "reason_code": "ERR_REPLAY_DETECTED",
  "timestamp": "<server_time>",
  "audit_id": "<uuid>",
  "signature": "<signed>"
}
```

**Audit Requirement:** Logged as `REPLAY_ATTEMPT`. May trigger HALT if correlated with other suspicious behavior.

---

### Failure Mode Summary Table

| Failure Mode | Condition | Verdict | HTTP Code | Alert Level |
|---|---|:---:|:---:|:---:|
| A — Malformed Input | Schema violation | DENY | 400 | LOW |
| B — System Uncertainty | CRL/DB/Clock failure | DENY | 503 | CRITICAL |
| C — Partial Authority | Proxy without delegation | DENY | 403 | MEDIUM |
| D — Internal Fault | Unhandled exception | DENY | 500 | CRITICAL |
| E — Token Invalid/Expired | Auth failure | DENY | 401 | MEDIUM |
| F — Channel Binding Mismatch | Token theft indicator | DENY | 401 | HIGH |
| G — Replay Detection | Stale/duplicate request | DENY | 400 | HIGH |

---

## 5. SARATHI DECISION FLOW

The following is the exact evaluation order for every request. Steps are executed sequentially. A failure at any step short-circuits to the corresponding DENY response.

```
REQUEST ARRIVES
     │
     ▼
[Step 1] SCHEMA VALIDATION
     │── FAIL → 400 ERR_SCHEMA_VIOLATION
     ▼
[Step 2] NULL DETECTION (all required fields, expanded per RES-08)
     │── FAIL → 400 ERR_NULL_INPUT
     ▼
[Step 3] TIMESTAMP VALIDATION (freshness + clock skew)
     │── FAIL → 400 ERR_REPLAY_DETECTED / ERR_CLOCK_SKEW
     ▼
[Step 4] PATH CANONICALIZATION CHECK (resource.id)
     │── FAIL → 400 ERR_PATH_TRAVERSAL
     ▼
[Step 5] SYSTEM STATE CHECK (CRL reachable? Clock synced? DB available?)
     │── FAIL → 503 ERR_SYSTEM_UNCERTAINTY
     ▼
[Step 6] TOKEN VERIFICATION (signature, expiry, issuer)
     │── FAIL → 401 ERR_TOKEN_INVALID / ERR_TOKEN_EXPIRED
     ▼
[Step 7] CHANNEL BINDING (Token.Subject == TLS.Client)
     │── FAIL → 401 ERR_SESSION_BINDING
     ▼
[Step 8] DEDUPLICATION CHECK (request.id seen before?)
     │── FAIL → 400 ERR_REPLAY_DETECTED
     ▼
[Step 9] AGENT STATE CHECK (active? suspended? terminated?)
     │── FAIL → DENY / HALT ERR_STATE_INVALID
     ▼
[Step 10] DELEGATION CHECK (if agent is Proxy, delegation_token present + valid + non-transitive?)
     │── FAIL → 403 ERR_PARTIAL_AUTHORITY / ERR_DELEGATION_VIOLATION
     ▼
[Step 11] SCOPE CONFINEMENT (action + resource within token scopes?)
     │── FAIL → 403 ERR_SCOPE_MISMATCH
     ▼
[Step 12] DATA CLASSIFICATION (resource.classification <= agent clearance?)
     │── FAIL → 403 ERR_DATA_CLASSIFICATION
     ▼
[Step 13] SEGREGATION OF DUTIES (Author != Approver for approval actions)
     │── FAIL → 403 ERR_SOD_VIOLATION
     ▼
[Step 14] RUNTIME MUTATION CHECK (is agent modifying own weights/rules?)
     │── FAIL → 403 ERR_RUNTIME_MUTATION
     ▼
[Step 15] VELOCITY / MOSAIC CHECK (aggregate access pattern within bounds?)
     │── FAIL → 429 ERR_MOSAIC_RISK / ERR_RATE_LIMIT
     ▼
[Step 16] BREAK GLASS CHECK (if privileged action, break_glass_token signature valid?)
     │── FAIL → 403 ERR_INSUFFICIENT_PROOF
     ▼
[Step 17] ALL CHECKS PASSED
     │
     ▼
VERDICT: ALLOW (with constraints) — SIGNED
```

**Critical Property:** Steps 1–4 are input validation (syntactic). Steps 5–8 are system/auth validation (cryptographic). Steps 9–16 are policy evaluation (semantic). The order is designed so that cheap checks fail fast and expensive checks are reached only for well-formed, authenticated requests.

---

## 6. WHAT IMPLEMENTERS MUST NEVER ASSUME

> **WARNING: VIOLATION OF THESE ASSUMPTIONS VOIDS SYSTEM SAFETY.**

### 6.1. Never Assume "Allow" on Error

If Sarathi returns HTTP 500, 503, or times out, **the answer is DENY**. Never fallback to "Allow" (fail-open) when governance is unreachable. This is the Fail-Closed invariant. Your retry logic must retry the governance check, not bypass it.

### 6.2. Never Assume Input Safety After ALLOW

An ALLOW verdict means **permission is granted**, not that the payload is safe to execute. Sarathi checks authorization, not sanitization. The Orchestrator remains responsible for preventing SQL Injection, XSS, command injection, and all input sanitization.

### 6.3. Never Assume Transitivity

If Agent A can talk to Agent B, and B can talk to C, **do not assume A can talk to C**. There is no transitive trust. Every agent-to-agent interaction requires its own authorization.

### 6.4. Never Parse `reason_code` for Control Flow

The `reason_code` is for **logging and debugging only**. Do not write code like `if (reason == 'SCOPE_MISMATCH') → try_again_with_different_scope()`. This is adversarial probing behavior. Treat DENY as DENY regardless of reason.

### 6.5. Never Cache ALLOW Verdicts

Permissions are ephemeral. A verdict is valid **only** for the exact timestamped request that generated it. Do not reuse a verdict for a subsequent request even 1 second later; the agent may have been revoked in that second. Every action requires a fresh verdict.

### 6.6. Never Bypass for "Root" or "Admin"

There is no "Root" agent that bypasses Sarathi. Even the Admin agent passes through the PDP with full evaluation. "God Mode" does not exist in a sovereign system. Break Glass is a governed privilege, not an ungoverned one.

### 6.7. Never Trust Agent-Supplied Classification

If Agent claims `resource.classification: "PUBLIC"` but the resource registry says `CONFIDENTIAL`, the registry wins. Agent-supplied classifications are **hints**, not facts. Sarathi must cross-reference against the registered asset tag.

### 6.8. Never Retry HALT Verdicts

A HALT verdict means the agent is considered a critical threat and is being suspended. Do not retry. Do not reconfigure. Do not resubmit from the same agent identity. The agent must be reviewed by Security before it can be reactivated through the unfreeze protocol.

### 6.9. Never Ignore the Signature

The `signature` field on the verdict is **mandatory** to verify before acting. An unsigned or tampered verdict from a man-in-the-middle must be treated as DENY. The Orchestrator must hold Sarathi's public key and verify every response.

### 6.10. Never Construct Synthetic Intents

The Orchestrator must forward the agent's actual intent, not construct a simplified or "cleaned up" version. Modifying the intent before sending it to Sarathi defeats the purpose of governance. Sarathi must see exactly what the agent wants to do, in its raw form (within the schema).

---

## 7. OPERATIONAL PARAMETERS

| Parameter | Value | Rationale |
|---|---|---|
| `MAX_REQUEST_AGE` | 5000ms | Replay prevention window |
| `MAX_CLOCK_SKEW` | 1000ms | Future timestamp tolerance |
| `MAX_CRL_STALENESS` | 500ms | Maximum age of revocation list before FAIL-CLOSED |
| `DEDUP_WINDOW` | 60s | Window for request ID deduplication |
| `MOSAIC_THRESHOLD` | 50 requests/60s across ≥3 data categories | Aggregate access pattern trigger |
| `DEPRECATION_WINDOW` | 72 hours | Schema version transition grace period |
| `VERDICT_SIGNATURE_ALG` | Ed25519 | Cryptographic algorithm for verdict signing |
| `TOKEN_BINDING_ALG` | SHA-256 | Hash algorithm for session/channel binding |

---

## 8. GOVERNANCE READINESS STATEMENT (VC DEMO)

### Status: GO (CONDITIONAL)

### Statement

The Sarathi Governance Core — comprising the Ambiguity Register, Ambiguity Resolution Specification, and this PDP Interface Definition — is **Architecturally Sound and Implementation-Ready** for the VC Demo.

### Strengths

- **14 ambiguity scenarios identified and resolved** with deterministic, fail-closed logic. Zero scenarios resolved to ALLOW under ambiguity.
- **7 Global Ambiguity Resolution Principles** (the Meta-Canon) provide axiomatic fallback for any future ambiguity not yet catalogued.
- **Strict PDP interface** with typed schemas, pre-policy validation, 17-step evaluation pipeline, and cryptographic verdict signing.
- **7 explicit failure modes** mapped to exact HTTP codes, response shapes, and audit requirements.
- **10 "Never Assume" rules** for implementers, preventing the most common governance bypass patterns.
- **Effective blocking of all threat classes**: Forbidden Six (blocked by GP-07, RES-07), Dangerous Four (managed via FAIL-CLOSED, velocity controls), Ambiguous Two (managed via delegation requirements, SoD checks).

### Limitations

- **IdP Trust Assumption**: Sarathi trusts the upstream Identity Provider's cryptographic integrity. If IdP keys are compromised, Sarathi cannot distinguish thieves from users. Key rotation and HSM protection are external dependencies.
- **Aggregate Detection is Heuristic**: The Mosaic Risk Threshold (RES-03) is a configurable heuristic, not a proof-based detection. Sophisticated adversaries may stay below the threshold.
- **No Dynamic Risk Scoring**: Per the Deferred Scope Register (Task 2), real-time behavioral risk scoring is out of scope. Decisions are binary (ALLOW/DENY/HALT), not probabilistic.

### Readiness Conditions (Non-Negotiable)

This readiness verdict is conditional on the following being true at demo time:

| # | Condition | Owner |
|---|---|---|
| 1 | **Orchestration Layer strictly adheres to the Fail-Closed contract** (Section 4). Any fail-open behavior voids this readiness. | Engineering |
| 2 | **Verdict signatures are verified** by all downstream consumers before acting on ALLOW. | Engineering |
| 3 | **BHIV Bucket is configured as Write-Only** with no delete or edit API exposed. | Ops |
| 4 | **CRL propagation latency** is monitored and the MAX_CRL_STALENESS (500ms) window is enforceable. | Ops |
| 5 | **IdP key management** follows HSM or equivalent hardware security standards. | Security |

### Verdict

> The Sarathi PDP is ready for the VC Demo **IF and ONLY IF** the five conditions above are satisfied. Any deviation renders this governance specification null and void. We do not half-enforce a constitution.

**Signed:**  
Senior Governance Engineer  
Sarathi Sovereign Core Team

---

---

## 9. RUNTIME ENFORCEMENT ARCHITECTURE (PEP/PDP SEPARATION)

*Added during Gap Resolution Phase — Addresses Gap 1: "No runtime enforcement architecture." This section defines HOW PDP decisions are enforced at runtime, following NIST SP 800-207 Zero Trust Architecture.*

### 9.1 Architectural Principle

The PDP (Sarathi) sits in the **control plane** and renders authorization decisions. Policy Enforcement Points (PEPs) sit in the **data plane** and enforce those decisions. This separation is mandatory — no component both decides AND enforces.

```
                    CONTROL PLANE
    +------------------------------------------+
    |  +--------+   +--------+   +---------+   |
    |  | Policy |   | Policy |   |  Policy |   |
    |  | Store  |-->| Engine |-->|  Admin  |   |
    |  |        |   |(Sarathi|   |(Session |   |
    |  | (Canon)|   |  PDP)  |   | Mgmt)   |   |
    |  +--------+   +--------+   +---------+   |
    +------------------------------------------+
              ^           |
              |           v
    +------------------------------------------+
    |          DATA PLANE (PEPs)               |
    |  +----------+ +----------+ +----------+  |
    |  | Gateway  | | Sidecar  | | Embedded |  |
    |  | PEP      | | PEP      | | Library  |  |
    |  | (<15ms)  | | (<1ms)   | | PEP      |  |
    |  |          | |          | | (<100μs) |  |
    |  +----------+ +----------+ +----------+  |
    +------------------------------------------+
              ^           ^           ^
              |           |           |
         External    Service-to-   Tool
         Ingress     Service     Invocation
```

### 9.2 PEP Placement Requirements

| PEP Type | Location | Latency SLA | Authorization Scope | Mandatory? |
|---|---|---|---|---|
| **Gateway PEP** | API Gateway / Load Balancer | < 15ms | Coarse-grained: agent authenticated, endpoint permitted for agent class | YES |
| **Sidecar PEP** | Sidecar container (OPA/Cedar) per pod | < 1ms | Fine-grained: specific action on specific resource with full context | YES |
| **Embedded Library PEP** | In-process Cedar Rust crate or OPA WASM | < 100μs | Tool-invocation gate: authorize each function call within agent runtime | YES for tool-using agents |

**Rule: A request that passes Gateway PEP but fails Sidecar PEP is DENIED. No trust inheritance between layers.**

### 9.3 Circuit Breaker for PDP Unavailability

| State | Behavior | Transition Trigger |
|---|---|---|
| **CLOSED** (normal) | Requests flow to PDP. Failures tracked on 10-call sliding window. | Failure rate > 50% → OPEN |
| **OPEN** (tripped) | All requests immediately DENIED (5ms response). PDP not contacted. | After 30 seconds → HALF-OPEN |
| **HALF-OPEN** (probing) | 3 probe requests test PDP health. Success → CLOSED. Failure → OPEN. | 2/3 probes succeed → CLOSED |

**Fallback tiers:** (1) Cached decisions with signed TTL (max 60s staleness) → (2) Degraded mode (read-only allowed, all mutations denied) → (3) Full denial.

**Every circuit state transition is logged as a security event to BHIV Bucket.**

### 9.4 Agent Runtime Sandboxing (Anthropic-Grade)

Defense-in-depth stack for each agent runtime:
1. **VM Isolation** — KVM (Linux) or Apple Virtualization Framework (macOS) hosts Ubuntu VM
2. **Namespace Isolation** — bubblewrap (`bwrap`) with `CLONE_NEWNET` + `CLONE_NEWPID`
3. **Syscall Filtering** — seccomp BPF filters (~104 bytes each for x64/ARM64) blocking unauthorized syscalls
4. **Network Control** — All traffic routes through Unix sockets to proxy server with domain-based allowlisting
5. **Filesystem** — Read-only except working directory. Mandatory deny paths: `~/.ssh`, `~/.aws`, credential stores
6. **PEP at Proxy** — Every outbound network request from agent undergoes authorization before reaching external service

---

## 10. DELEGATION CAPABILITY TOKEN FRAMEWORK

*Added during Gap Resolution Phase — Addresses Gap 2: "No delegation or capability token framework." Based on DeepMind DCT architecture (Feb 2026), Biscuit cryptographic tokens, and SPIFFE/SPIRE workload identity.*

### 10.1 Token Architecture: Biscuit with Ed25519

Delegation Capability Tokens use **Biscuit** (Eclipse Foundation) with Ed25519 public-key signatures. Unlike Macaroons (HMAC-based, shared secret), Biscuits enable offline verification by any service with the public key while only the root authority can create tokens.

**Authority Block (Block 0 — Human Origin):**
```
user("user:alice@corp.example");
delegation_origin("human", "2026-02-28T10:00:00Z");
scope_id("scope-9f8e7d6c");
allowed_tool("tool:database-read");
allowed_tool("tool:email-draft");
max_cost(1000.00);
max_delegation_depth(3);
shutdown_deadline("2026-02-28T12:00:00Z");
data_classification_ceiling("CONFIDENTIAL");

check if time($t), $t < 2026-02-28T12:00:00Z;
check if delegation_depth($d), $d <= 3;
check if accumulated_cost($c), $c <= 1000.00;
```

**Attenuation Block (Agent A → Agent B):**
```
check if resource($r), $r.starts_with("/data/sales/");
check if allowed_tool($t), ["tool:database-read"].contains($t);
check if max_cost($c), $c <= 200.00;
check if delegation_depth($d), $d <= 2;
```

**Key Properties:**
- Attenuation blocks can ONLY restrict, never expand permissions (GP-08)
- Each block carries a unique revocation identifier
- Revoking any block invalidates all downstream tokens (cascading revocation)

### 10.2 Token Binding (DPoP + SPIFFE)

Every request includes a DPoP proof (RFC 9449) binding the Biscuit to the requesting agent's identity:
- Agent identity from SPIFFE/SPIRE workload attestation (kernel-level, no pre-existing secrets)
- DPoP JWT contains: `ath` (hash of Biscuit token), `spiffe_id` (agent workload identity), `jti` (unique request ID)
- Resource server verifies: signature ✓, ath matches ✓, SPIFFE ID matches ✓, jti not replayed ✓

### 10.3 Algorithmic Circuit Breakers (3-Tier)

| Tier | Trigger | Action | Scope |
|---|---|---|---|
| **Tier 1** — Throttle | Request frequency > 3σ above baseline, or cost accumulation rate doubles | Increase authorization latency, reduce remaining risk budget | Single agent |
| **Tier 2** — Chain Invalidation | Out-of-scope access attempt, delegation to unregistered agent, risk budget exhaustion | Revoke triggering agent's Biscuit revocation ID → cascading invalidation of all downstream tokens | Agent + all delegates |
| **Tier 3** — System Pause | Rapid inter-agent transaction spike across multiple chains, anomalous resource monopolization | Halt all non-essential agent activity. Human review required before resumption. | System-wide |

Anti-gaming: Trigger thresholds are **dynamic with randomized perturbation** — agents cannot optimize behavior to stay below detection.

---

## 11. TAMPER-RESISTANT AUDIT TRAIL SPECIFICATION

*Added during Gap Resolution Phase — Addresses Gap 5: "No audit trail specification." Meets EU AI Act Article 12, NIST SP 800-53 AU controls, and exceeds OpenAI and IBM audit capabilities.*

### 11.1 Audit Event Schema

```json
{
  "event_id": "audit-{timestamp}-{sha256_hash_prefix}",
  "event_type": "authorization.decision",
  "timestamp": "ISO-8601 with microsecond precision",
  "timestamp_source": "ntp-stratum-1",
  
  "actor": {
    "agent_spiffe_id": "spiffe://corp/ns/agents/sa/{agent_id}",
    "delegating_user": "pseudonym:hmac-sha256({user_id})",
    "delegation_chain_hash": "sha256({scope_id}:{depth})",
    "delegation_depth": 2,
    "dkt_revocation_id": "biscuit-rev-{id}"
  },
  
  "request": {
    "principal": "Agent::{agent_class}::{agent_id}",
    "action": "Action::{action_type}",
    "resource": "Resource::{resource_type}::{resource_id}",
    "context_hash": "sha256(full_context_json)"
  },
  
  "decision": {
    "result": "ALLOW | DENY | ESCALATE",
    "determining_rules": ["rule-id-1", "rule-id-2"],
    "evaluation_duration_us": 87,
    "pep_type": "gateway | sidecar | embedded",
    "circuit_breaker_state": "CLOSED | OPEN | HALF-OPEN"
  },
  
  "network": {
    "source_ip_hash": "sha256({ip})",
    "ja3_fingerprint": "{tls_fingerprint}",
    "ja4_fingerprint": "{tls_fingerprint_v2}"
  },
  
  "integrity": {
    "prev_event_hash": "sha256(previous_event)",
    "current_event_hash": "sha256(this_event + prev_hash)",
    "merkle_batch_id": "batch-{hour}",
    "hsm_signature": "ed25519(merkle_root, hsm_key_id)"
  }
}
```

### 11.2 Immutability Architecture (4-Layer)

| Layer | Mechanism | Tamper Detection |
|---|---|---|
| 1. **Hash Chaining** | Each event includes SHA-256 of previous event | Any modification breaks chain at that point |
| 2. **Merkle Tree Batching** | Hourly batch → Merkle tree → HSM-signed root | Any single event verifiable with O(log n) proof |
| 3. **Append-Only Storage** | immudb (FIPS-compliant, built-in integrity auditor) | Continuous independent verification |
| 4. **WORM Archival** | S3 Object Lock (Compliance mode — root cannot delete) | Hardware-enforced immutability |

### 11.3 Retention Tiers (EU AI Act Compliant)

| Tier | Storage | Duration | Access Latency | Regulation |
|---|---|---|---|---|
| **Hot** | Elasticsearch | 0-3 months | < 1 second | PCI DSS 4.0 (3mo immediately accessible) |
| **Warm** | S3 Standard | 3-12 months | < 5 minutes | PCI DSS 4.0 (12mo total) |
| **Cold** | S3 Object Lock (WORM) | 1-10 years | < 4 hours | EU AI Act Art. 18 (10yr), SOX (7yr) |

### 11.4 PII Handling in Audit

- User identities: HMAC-SHA256 pseudonymization with organization-held salt
- Agent IDs: Pseudonymized for external queries, reversible for internal forensics
- IP addresses: SHA-256 hashed in hot/warm tiers
- Salt stored in HSM with dual-authorization access (NIST AU-9(5))
- Original PII recoverable ONLY through salt + dual authorization

---

**END OF SARATHI PDP INTERFACE SPECIFICATION**

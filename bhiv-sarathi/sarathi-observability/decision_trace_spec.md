# DECISION TRACE SPECIFICATION

**Author:** Hemanth B
**Target System:** Sarathi Governance Kernel — Policy Decision Point
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026
**Task Reference:** Observability & Traceability Contract — Phase A
**Upstream Dependencies:**
- `sarathi_request_schema.md` (Day 1) — defines input fields
- `sarathi_response_schema.md` (Day 2) — defines output fields, prohibition list, 13 output invariants
- `evaluation_order_spec.md` (Day 3) — defines 7-stage pipeline, 52 sub-steps
- `failure_mode_contract.md` (Day 4) — defines 17 failure modes
- `enforcement_model_spec.md` (Day 5) — defines 14 enforcement invariants, PEP topology
- `pdp_reference_pseudocode.md` (Day 6) — defines stage_7_audit_and_sign(), opaque refusal logic
- `sarathi_pdp_lock_v1.md` (Day 7, v1.1) — defines 12 guarantees, 20 go-live items
- `SARATHI_PDP_INTERFACE.md` (Task 3) — defines audit event schema, 4-layer immutability, PII handling

**Scope Boundary:** This document defines WHAT is recorded. It does NOT modify the request schema, response schema, evaluation order, enforcement model, or Canon rules. It is a read-only overlay on existing PDP logic.

---

## 1. PURPOSE

Every Sarathi PDP decision produces a **decision trace** — a complete, immutable, internally-rich record of how that decision was reached. The decision trace exists so that five years from now, any engineer can answer three questions about any historical decision:

1. **What happened?** — the verdict, the inputs, the output.
2. **Why?** — which rules fired, in what order, with what intermediate results.
3. **Was the system healthy?** — policy version, system state, timing, dependencies.

The decision trace is the internal record. It is not the external response. The distinction is absolute: the external response is minimal and opaque (per GP-05, RE-45). The internal trace is exhaustive and transparent — but only to authorized auditors with appropriate clearance.

---

## 2. DECISION TRACE RECORD — COMPLETE FIELD SPECIFICATION

Every PDP evaluation produces exactly one decision trace record. The record is written atomically to the BHIV Bucket as part of Stage 7 (Audit Write). If the write fails, the verdict is overridden to DENY and the record is written to the emergency buffer (FM-05).

### 2.1 Record Structure

```
DECISION_TRACE_RECORD {

  // === IDENTITY ===
  trace_id:                 STRING      // "trace-{UUIDv4}" — unique per decision
  correlation_id:           STRING      // Echoed from request — links request→decision→execution
  audit_id:                 STRING      // "aud-{UUIDv4}" — BHIV Bucket key for this record
  pdp_instance_id:          STRING      // Hostname/pod ID of the evaluating PDP instance
  pdp_version:              STRING      // Semantic version of the PDP binary (e.g., v1.2.0)

  // === TIMING ===
  request_received_at:      DATETIME    // ISO-8601 UTC, microsecond precision
  evaluation_started_at:    DATETIME    // After pre-parse, before Stage 1
  evaluation_completed_at:  DATETIME    // After Stage 7 write, before response delivery
  total_duration_us:        INTEGER     // Wall-clock microseconds (evaluation_completed - evaluation_started)
  response_delivered_at:    DATETIME    // After response sent to caller

  // === INPUT FINGERPRINT ===
  request_hash:             STRING      // SHA-256 of the canonical JSON request body
  agent_id:                 STRING      // From request.agent_identity.agent_id
  agent_class:              STRING      // From request.agent_identity.agent_class
  agent_version:            STRING      // From request.agent_identity.agent_version
  action:                   STRING      // From request.intent.action
  resource_type:            STRING      // From request.intent.resource.resource_type
  resource_id_hash:         STRING      // SHA-256 of request.intent.resource.resource_id
  data_classification:      STRING      // From request.intent.resource.data_classification
  declared_sensitivity:     STRING      // From request.risk_classification.action_sensitivity
  declared_reversibility:   STRING      // From request.risk_classification.reversibility
  declared_blast_radius:    STRING      // From request.risk_classification.blast_radius
  environment:              STRING      // From request.context.environment
  policy_version_hash:      STRING      // From request.context.policy_version_hash

  // === DELEGATION CONTEXT (if present) ===
  delegation_depth:         INTEGER     // 0 if no delegation; 1-3 if Biscuit token present
  delegation_chain_hash:    STRING      // SHA-256 of the full delegation chain (or "NONE")
  dkt_revocation_id:        STRING      // Biscuit authority block revocation_id (or "NONE")
  dpop_jti:                 STRING      // DPoP proof jti for replay correlation (or "NONE")
  classification_ceiling:   STRING      // Biscuit data_classification_ceiling (or "NONE")

  // === POLICY STATE ===
  pdp_policy_hash:          STRING      // SHA-256 of policy bundle loaded at evaluation time
  policy_version_match:     BOOLEAN     // request hash == PDP hash
  crl_staleness_ms:         INTEGER     // Milliseconds since last CRL update
  state_registry_latency_us: INTEGER    // Microseconds for State Registry lookup
  circuit_breaker_state:    STRING      // "CLOSED" | "HALF-OPEN" | "OPEN"

  // === STAGE EVALUATION TRACE ===
  stages: [
    {
      stage_number:         INTEGER     // 1-7
      stage_name:           STRING      // "IDENTITY" | "LIFECYCLE" | "AUTHORITY" | "ELIGIBILITY" | "RISK_GATES" | "CLASSIFICATION" | "AUDIT_WRITE"
      status:               STRING      // "PASS" | "DENY" | "SKIPPED_SHORT_CIRCUIT" | "ERROR"
      duration_us:          INTEGER     // Microseconds for this stage
      sub_steps_executed:   INTEGER     // Count of sub-steps that ran
      sub_steps_total:      INTEGER     // Total sub-steps defined for this stage
      determining_rules:    [STRING]    // Canon rule IDs that determined stage outcome
      deny_reason:          STRING      // Null if PASS; specific reason code if DENY
      internal_notes:       STRING      // Free-text implementation notes (never exposed externally)
    }
  ]

  // === VERDICT ===
  final_verdict:            STRING      // "ALLOW" | "DENY" | "ESCALATE"
  verdict_source:           STRING      // "EVALUATION" | "SHORT_CIRCUIT" | "AUDIT_OVERRIDE" | "TIMEOUT" | "ERROR"
  determining_rules:        [STRING]    // Canon rule IDs that produced the final verdict
  reason_code:              STRING      // Internal reason code (full detail)
  external_reason_code:     STRING      // What was sent to the caller (may be masked per RE-45)
  was_masked:               BOOLEAN     // True if external_reason != internal reason (RE-45 applied)

  // === TOKEN (if ALLOW) ===
  token_issued:             BOOLEAN
  token_jti:                STRING      // JWT ID of the issued capability token (or "NONE")
  token_exp:                DATETIME    // Expiry time (or null)
  token_scope_hash:         STRING      // SHA-256 of the token's scope claims (or "NONE")

  // === ESCALATION (if ESCALATE) ===
  escalation_reference:     STRING      // Escalation ID (or "NONE")
  escalation_target:        STRING      // "GOVERNANCE_COUNCIL" (or "NONE")
  escalation_deadline:      DATETIME    // 15-minute deadline (or null)
  interim_verdict:          STRING      // Always "DENY" for ESCALATE

  // === NETWORK CONTEXT ===
  source_ip_hash:           STRING      // SHA-256 of source IP
  pep_type:                 STRING      // "GATEWAY" | "SIDECAR" | "EMBEDDED" | "UNKNOWN"
  ja3_fingerprint:          STRING      // JA3 TLS fingerprint (or "UNAVAILABLE")
  ja4_fingerprint:          STRING      // JA4 TLS fingerprint (or "UNAVAILABLE")
  session_binding_hash:     STRING      // SHA-256 of the TLS session binding

  // === INTEGRITY ===
  prev_event_hash:          STRING      // SHA-256 of previous decision trace (hash chain)
  current_event_hash:       STRING      // SHA-256 of this record + prev_event_hash
  merkle_batch_id:          STRING      // Hourly Merkle batch identifier
  hsm_signature:            STRING      // Ed25519(merkle_root) — populated at batch time, null at write time

  // === ANOMALY SIGNALS ===
  anomaly_flags: [
    {
      flag_type:            STRING      // "CLASSIFICATION_MISMATCH" | "SENSITIVITY_UNDERSTATEMENT" | "VELOCITY_APPROACHING" | "DELEGATION_DEPTH_UNUSUAL" | "SESSION_BINDING_CHANGE" | "BRUTE_FORCE_PATTERN"
      severity:             STRING      // "INFO" | "WARN" | "ALERT"
      detail:               STRING      // Machine-readable detail
    }
  ]
}
```

### 2.2 Field Count

| Category | Fields |
|---|---|
| Identity | 5 |
| Timing | 5 |
| Input Fingerprint | 13 |
| Delegation Context | 5 |
| Policy State | 5 |
| Stage Evaluation Trace | 7 per stage × 7 stages = 49 (nested) |
| Verdict | 6 |
| Token | 4 |
| Escalation | 4 |
| Network Context | 5 |
| Integrity | 4 |
| Anomaly Signals | Variable (0-N flags) |
| **Total top-level fields** | **56 + stage array + anomaly array** |

---

## 3. WHAT MUST NEVER BE RECORDED

These items are prohibited from appearing anywhere in the decision trace — not in the primary record, not in the emergency buffer, not in debug logs, not in metrics.

| Prohibited Item | Reason | Enforcement |
|---|---|---|
| **Plaintext PII** (user names, emails, phone numbers) | GDPR Art. 5(1)(c) data minimization; NIST AU-9(5). All user identifiers are pseudonymized via HMAC-SHA256. | AI-56 (PII Redaction in Logs); pseudonymization enforced at Stage 7.1b |
| **Raw request body** | Contains authority tokens, delegation proofs, and break-glass tokens. Logging raw tokens creates a replay material store. | Request is represented by request_hash (SHA-256). Individual fields extracted as needed. |
| **Plaintext capability tokens** | A logged ALLOW token is a storable credential. If the audit store is breached, every logged token is replayable until expiry. | Token represented by token_jti + token_scope_hash. Token body never persisted. |
| **Plaintext delegation proofs** | Delegation proofs contain user cryptographic material. | Delegation represented by delegation_chain_hash + delegation_depth. |
| **HSM private keys or key material** | Catastrophic if leaked. | HSM keys never leave the hardware module. Only key_id is referenced. |
| **Policy rule logic or conditions** | Logging the full policy text enables policy enumeration. An attacker reading the audit trail learns the exact conditions for ALLOW. | Rules referenced by ID only (e.g., "AC-21"). Rule logic is in the policy bundle, not the trace. |
| **Alternative verdicts** ("would have been ALLOW if...") | Enables an attacker to learn exactly what they need to change. | Only the actual verdict and actual determining rules are recorded. |
| **Other agents' identities in ESCALATE** | RES-13 prohibits exposing the conflicting agent's identity. | Escalation records the conflict type, not the other party. |
| **Internal PDP memory addresses, stack traces, or core dumps** | Implementation details that enable targeted exploitation. | Errors recorded as structured error codes, not raw exceptions. Core dumps go to separate Cold Storage (FM-07 audit requirement). |
| **Source IP in plaintext** | IP addresses are PII under GDPR. | Stored as SHA-256 hash. Reversible only through salt + dual authorization. |

---

## 4. WHAT MUST NEVER BE EXPOSED EXTERNALLY

The decision trace is an internal record. The external response (per Day 2 Response Schema) is a strict subset. The following items exist in the trace but are NEVER included in the response sent to the caller:

| Internal-Only Field | Why Withheld | Reference |
|---|---|---|
| Stage evaluation trace (all 7 stages) | Reveals evaluation architecture and timing per stage | GP-05; Day 2 Section 8 Prohibition List |
| Internal reason code (when masked) | RE-45: security-sensitive denials use opaque "ACCESS_DENIED" | RE-45; pseudocode line 940 |
| Anomaly flags | Telling an agent it triggered an anomaly teaches it to avoid the trigger | RES-03 (Mosaic masking) |
| CRL staleness, registry latency, circuit breaker state | Reveals PDP health status — useful for timing attacks | GP-05 |
| Policy bundle hash comparison details | Reveals whether the agent's policy view is stale | Only the mismatch error code is returned |
| Other agents' identities in escalation | RES-13: precedence hierarchy logic not exposed | Day 2 Section 8.3 |
| PDP instance ID | Enables targeting specific instances for exploitation | Only included in internal trace |
| Delegation chain details beyond depth | Reveals delegation topology | Depth exposed; full chain withheld |
| request_hash | Reveals the PDP's canonicalization algorithm | Internal integrity check only |
| was_masked flag | Telling the agent its reason was masked defeats the purpose of masking | Internal audit flag only |

---

## 5. TRACE INTEGRITY GUARANTEES

Every decision trace record satisfies these properties:

| ID | Property | Mechanism |
|---|---|---|
| **DT-01** | **Completeness** — Every PDP evaluation produces exactly one trace record. No decision is untraced. | Stage 7 is EVAL-05 (never skipped). FM-05 emergency buffer catches audit failures. |
| **DT-02** | **Atomicity** — The trace record is written as one indivisible unit. No partial writes. | Single BHIV Bucket PUT operation. Emergency buffer uses append-only write with fsync. |
| **DT-03** | **Immutability** — Once written, the trace record cannot be modified or deleted. | 4-layer immutability: hash chain → Merkle batch → immudb → WORM archival. |
| **DT-04** | **Ordering** — Traces are hash-chained. The sequence of decisions is tamper-evident. | prev_event_hash links each record to its predecessor. Break detection is O(1). |
| **DT-05** | **Temporal Accuracy** — Timestamps are NTP stratum-1 synchronized with < 500ms drift. | DEP-07. Drift beyond threshold → PDP denies all requests (fail-closed). |
| **DT-06** | **Correlation** — Every trace links to its originating request via correlation_id and to downstream execution via token_jti. | Request → trace → token → resource execution log. Unbroken chain of custody. |
| **DT-07** | **Opacity** — The trace is exhaustive internally but opaque externally. No trace field leaks to the caller beyond the Day 2 response contract. | Section 4 enforcement. Response construction uses only the Day 2 defined fields. |
| **DT-08** | **Survivability** — Trace records survive PDP restarts, BHIV Bucket outages (via emergency buffer), and infrastructure failures. | Emergency buffer on local filesystem. Flush-on-recovery protocol (FM-05). |
| **DT-09** | **PII Safety** — No plaintext PII in any trace record. All user identifiers pseudonymized. | HMAC-SHA256 pseudonymization at Stage 7.1b (AI-56). Dual-authorization recovery. |
| **DT-10** | **Non-Repudiation** — Hourly Merkle batches are HSM-signed. The PDP cannot deny producing a traced decision. | Ed25519 signature over Merkle root by HSM. Signature verifiable by any party with the public key. |

---

## 6. TRACE STORAGE AND RETENTION

Per the 3-tier retention model (SARATHI_PDP_INTERFACE.md Section 11.3):

| Tier | Duration | Storage | Access Pattern | Query Capability |
|---|---|---|---|---|
| **Hot** | 0-3 months | Elasticsearch | < 1s latency | Full-text search, aggregation, real-time dashboards |
| **Warm** | 3-12 months | S3 Standard | < 5 minutes | Key-based lookup (correlation_id, trace_id, audit_id) |
| **Cold** | 1-10 years | S3 Object Lock (WORM) | < 4 hours | Key-based retrieval only. Merkle proof verification. |

**Tier transitions are non-destructive.** Records are COPIED to the next tier, then the hot-tier index is pruned. The WORM archival copy is permanent.

---

## 7. TRACE ACCESS CONTROL

| Accessor | What They See | Authorization |
|---|---|---|
| **Requesting agent** | Only the Day 2 response (verdict, reason_code, token, audit_id) | None required — this is the response |
| **Operations team** | Timing, policy state, circuit breaker state, error codes, anomaly flags — NO PII, NO rule logic | Role: `sarathi:ops:trace:read` |
| **Security team** | Full trace including anomaly flags, network context, delegation details — NO plaintext PII | Role: `sarathi:security:trace:read` |
| **Governance auditor** | Full trace + PII recovery (via dual-authorization) + Merkle proof verification | Role: `sarathi:governance:trace:full` + dual-authorization |
| **External regulator** | Redacted trace per regulatory template + Merkle proof of integrity | Role: `sarathi:external:trace:redacted` + legal approval |

**No single role has unrestricted access.** PII recovery requires two authorized parties (NIST AU-9(5)). Rule logic is never in the trace — auditors reference the archived policy bundle.

---

## 8. RELATIONSHIP TO EXISTING SPECIFICATIONS

This document does not modify any existing specification. It defines the observability contract that reads FROM existing specifications:

| Existing Spec | What This Document Uses | What This Document Does NOT Change |
|---|---|---|
| Day 1 — Request Schema | Input fields for fingerprinting | No schema changes |
| Day 2 — Response Schema | Output invariants (OUT-01 through OUT-13), prohibition list | No response changes |
| Day 3 — Evaluation Order | Stage definitions, sub-step counts, timing budget | No evaluation changes |
| Day 4 — Failure Modes | FM-05 (audit failure), FM-16 (hash chain break) | No failure mode changes |
| Day 5 — Enforcement Model | PEP topology, token issuance rules | No enforcement changes |
| Day 6 — Pseudocode | stage_7_audit_and_sign(), opaque refusal logic (RE-45) | No pseudocode changes |
| Day 7 — Lock v1.1 | Guarantees G-05 (Mandatory Audit), 20 go-live items | No lock changes |
| PDP Interface | Audit event schema, 4-layer immutability, retention tiers, PII handling | No interface changes |

---

**END OF DECISION TRACE SPECIFICATION**

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Trace Record Fields | 56 top-level + stage array + anomaly array |
| Prohibited Recording Items | 10 |
| Prohibited Exposure Items | 10 |
| Trace Integrity Properties | 10 (DT-01 through DT-10) |
| Retention Tiers | 3 (Hot 3mo, Warm 12mo, Cold 10yr) |
| Access Control Roles | 5 |
| Canon Rules Referenced | AI-53, AI-54, AI-55, AI-56, RE-45, GP-05, RES-03, RES-13 |
| Existing Specs Modified | 0 |

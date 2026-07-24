# SARATHI FAILURE MODE CONTRACT

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Task 4 — Sarathi PDP Minimal Implementation Specification (Day 4)  
**Upstream Dependencies:**  
- `sarathi_request_schema.md` (Task 4 — Day 1)  
- `sarathi_response_schema.md` (Task 4 — Day 2)  
- `evaluation_order_spec.md` (Task 4 — Day 3)  
- `SARATHI_PDP_INTERFACE.md` — Failure Modes A-G (Task 3)  
- `SARATHI_HIGH_DENSITY_CANON_FORMALIZATION.md` — 60 Canon Rules (Task 2)  
- `AMBIGUITY_RESOLUTION_SPEC.md` — 7 Global Principles, 14 Resolutions (Task 3)  
- `GOVERNANCE_VALIDATION_REPORT.md` — 12 Assumptions, Threat Model (Task 1)  
- Sarathi PDP Research Report — Six Critical Failure Modes, TOCTOU, Drift Analysis

---

## PURPOSE

This document defines the **complete failure mode contract** for the Sarathi PDP — every state in which the PDP cannot produce a normal evaluation result, and the exact behavior required in each state.

Prior specifications defined what happens when things work correctly: Day 1 (valid input), Day 2 (correct output), Day 3 (proper evaluation). This specification defines what happens when things BREAK. It is the most important document in the PDP specification because **governance systems are defined by their failure behavior, not their success behavior.** A system that works correctly 99% of the time but fails open 1% of the time is exploitable 100% of the time — an attacker simply needs to trigger the 1% failure condition.

The guiding principle is absolute: **every failure mode resolves to DENY.** There is no failure that produces ALLOW. There is no failure that produces "degraded ALLOW." There is no failure that produces "ALLOW with warning." The PDP either succeeds fully and can produce any verdict (ALLOW, DENY, or ESCALATE), or it fails and the only possible verdict is DENY.

This is Saltzer and Schroeder's **fail-safe defaults** principle (1975): "Base access decisions on permission rather than exclusion. The default situation is lack of access." NIST SP 800-53 codifies this as control SA-8(23) "Secure Defaults." CWE-636 catalogs the inverse as a formal weakness: "Not Failing Securely (Failing Open)."

**The Redis Incident:** A documented production failure involved a Redis crash causing an OPA timeout that resulted in six hours of unrestricted API access because the application defaulted to ALLOW when the policy engine was unavailable. This document exists to make such an outcome structurally impossible in Sarathi.

---

## TABLE OF CONTENTS

1. [The Fail-Closed Axiom](#1-the-fail-closed-axiom)
2. [Failure Mode Taxonomy](#2-failure-mode-taxonomy)
3. [FM-01: Missing Field](#3-fm-01-missing-field)
4. [FM-02: Stale Token](#4-fm-02-stale-token)
5. [FM-03: Policy Version Mismatch](#5-fm-03-policy-version-mismatch)
6. [FM-04: External State Unavailable](#6-fm-04-external-state-unavailable)
7. [FM-05: Audit Sink Unavailable](#7-fm-05-audit-sink-unavailable)
8. [FM-06: Ambiguous Rule Resolution](#8-fm-06-ambiguous-rule-resolution)
9. [FM-07: Internal Logic Fault](#9-fm-07-internal-logic-fault)
10. [FM-08: Channel Binding Failure](#10-fm-08-channel-binding-failure)
11. [FM-09: Replay Detection](#11-fm-09-replay-detection)
12. [FM-10: Cascading Revocation Discovery](#12-fm-10-cascading-revocation-discovery)
13. [FM-11: Evaluation Timeout](#13-fm-11-evaluation-timeout)
14. [FM-12: HSM / Signing Key Unavailable](#14-fm-12-hsm--signing-key-unavailable)
15. [Compound Failure Scenarios](#15-compound-failure-scenarios)
16. [Failure Recovery Protocol](#16-failure-recovery-protocol)
17. [Failure Mode Summary Matrix](#17-failure-mode-summary-matrix)


---

## 1. THE FAIL-CLOSED AXIOM

Before any failure mode is discussed, one axiom must be stated. It is non-negotiable, non-configurable, and applies without exception.

> **AXIOM: If the PDP cannot produce a fully evaluated, fully audited, cryptographically signed verdict with complete confidence, the verdict is DENY.**

This axiom is derived from:
- **GP-06 (Fail-Closed on Uncertainty):** "If Sarathi cannot determine the state of a required input, it assumes the worst case and defaults to DENY."
- **GP-01 (Silence Implies Denial):** "If the Canon does not explicitly ALLOW an interaction, it is DENIED."
- **OUT-07 (Audit-Coupled):** "If audit write fails, verdict = DENY regardless of evaluation outcome."
- **Canon AC-21 (Zero Trust Default):** "If Capability Token is missing or null → DENY (Fail Closed)."
- **NIST SP 800-53 SA-8(23):** "Security mechanisms deny requests unless the request is found well-formed and consistent with security policy."

**What the axiom prohibits:**
- "Fail-open temporarily until the system recovers" — NO.
- "Allow read-only operations during failure" — NO.
- "Allow previously-approved agents during failure" — NO.
- "Degrade to logging-only mode" — NO.
- "Allow with elevated monitoring" — NO.
- "Trust cached ALLOW verdicts" — NO.

**Why this strictness is necessary:** Per the research report, the difference between fail-closed and fail-open is often a single boolean: `if not user.is_allowed(): raise Error()` is fail-open (proceeds if `is_allowed()` throws), while `if user.is_allowed(): proceed; else: raise Error()` is fail-closed (proceeds only on affirmative True). This document ensures the entire PDP architecture uses the latter pattern at every decision point.

---

## 2. FAILURE MODE TAXONOMY

Each failure mode is documented with a standardized structure:

| Element | Description |
|---|---|
| **ID** | Unique failure mode identifier (FM-XX) |
| **Name** | Descriptive failure name |
| **Trigger Condition** | Exact condition(s) that cause this failure |
| **Evaluation Stage** | Which Day 3 stage(s) this failure occurs in |
| **Required Verdict** | The verdict that MUST be produced |
| **HTTP Status** | The HTTP status code returned to the caller |
| **Reason Code** | The machine-readable error code in the response |
| **Logging Requirement** | What MUST be logged, where, and at what severity |
| **Downstream Behavior** | What the caller (orchestrator/PEP) MUST do on receiving this failure |
| **Alert Requirement** | Whether operations/security must be notified |
| **Recovery Path** | How normal operation resumes after this failure |
| **Retry Permitted** | Whether the caller may retry this request |
| **Canon/GP Reference** | Which Canon rules and Global Principles govern this failure |
| **Industry Precedent** | How industry standards handle the equivalent failure |

### 2.1 Mapping to Task 3 Failure Modes

| Day 4 ID | Task 3 FMEA | Research Report Category |
|---|---|---|
| FM-01 | Failure Mode A (Malformed Input) | Missing Fields |
| FM-02 | Failure Mode E (Token Expired/Invalid) | Stale Tokens |
| FM-03 | (New — not in Task 3) | Policy Version Mismatch |
| FM-04 | Failure Mode B (System Uncertainty) | External State Unavailability |
| FM-05 | (New — not in Task 3) | Audit Sink Unavailability |
| FM-06 | (New — not in Task 3) | Ambiguous Rule Resolution |
| FM-07 | Failure Mode D (Internal Fault) | Internal Logic Fault |
| FM-08 | Failure Mode F (Channel Binding) | Channel Binding Failure |
| FM-09 | Failure Mode G (Replay Detection) | Replay/TOCTOU |
| FM-10 | (New — derived from LS-19) | Cascading Revocation |
| FM-11 | (New — derived from EVAL-07) | Evaluation Timeout |
| FM-12 | (New — derived from OUT-04) | Signing Key Unavailable |

---

## 3. FM-01: MISSING FIELD

### Trigger Condition

The request envelope is missing one or more required fields, contains null/empty values in required fields, contains semantic null patterns ("null", "none", "nil", "N/A", "undefined"), or fails JSON schema validation (wrong type, unknown fields, pattern mismatch).

### Evaluation Stage

**Stage 1 — Identity Validation** (sub-steps 1.1-1.3 per Day 3).

### Required Verdict

**DENY**

### HTTP Status

`400 Bad Request`

### Reason Code

`ERR_SCHEMA_VIOLATION` (for missing/wrong-type fields)  
`ERR_NULL_INPUT` (for null/empty/semantic-null values)  
`ERR_UNKNOWN_FIELD` (for additionalProperties violations)

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket (primary), Local emergency buffer (fallback) |
| **Severity** | WARN (single occurrence), ERROR (>3 from same agent in 60s per EL-39) |
| **Required Fields** | correlation_id (if present, else "UNKNOWN"), source_ip, timestamp, error_code, request_hash (SHA-256 of raw request body), agent_id (if parseable, else "UNPARSEABLE") |
| **Frequency Tracking** | Count per agent_id per rolling 60-second window. If count > 3 → escalate to Brute Force Detection (EL-39) |

### Downstream Behavior Requirement

1. **Orchestrator/PEP MUST:** Treat this as a non-retryable error for the same request. The request is structurally defective.
2. **Orchestrator/PEP MUST NOT:** Attempt to "fix" the request and resubmit (this violates INV-05, Non-Negotiation). The PDP does not accept corrected resubmissions of the same correlation_id.
3. **Orchestrator/PEP MAY:** Submit a NEW request with a NEW correlation_id that addresses the structural defect.

### Alert Requirement

- Single occurrence: No alert (routine validation failure).
- >3 from same agent in 60s: Alert to Security (pattern indicates brute-force schema probing).
- >100 from any source in 60s: Alert to Operations (possible DDoS via malformed requests).

### Recovery Path

No recovery required for the PDP. This is a caller-side error. The PDP continues serving other requests normally.

### Retry Permitted

**YES** — but only as a NEW request with a NEW correlation_id and with the structural defect corrected.

### Canon/GP Reference

GP-04 (Input Validity Is Security), GP-01 (Silence Implies Denial), EL-33 (Input Validation), EL-39 (Brute Force Detection), RES-08 (Null Fuzzing), INV-01 (Totality), INV-07 (Closure).

### Industry Precedent

- AWS Cedar: rejects requests with unknown entity types with "no applicable policies" (effective DENY).
- OPA: returns `undefined` for malformed queries — callers must interpret undefined as deny.
- XACML 3.0: Missing required attributes produce "Indeterminate" with MissingAttribute status code.
- Sarathi improves on XACML by collapsing Indeterminate to DENY (GP-06).

---

## 4. FM-02: STALE TOKEN

### Trigger Condition

The `authority.capability_token` is present but:
- Its `exp` (expiry) claim is in the past (expired).
- Its `iat` (issued-at) claim is older than MAX_TOKEN_TTL (60 seconds) from now.
- Its signature is valid but was signed with a rotated (no longer current) IdP key.
- Its `jti` (JWT ID) has been revoked via the Certificate Revocation List (CRL).
- Its `sub` (subject) claim references an agent that has since been SUSPENDED or REVOKED.

### Evaluation Stage

**Stage 1** (sub-steps 1.9-1.10 for signature/claims) and **Stage 2** (sub-step 2.2 for agent state since token issuance).

### Required Verdict

**DENY**

### HTTP Status

`401 Unauthorized`

### Reason Code

`ERR_TOKEN_EXPIRED` (expiry past)  
`ERR_TOKEN_INVALID` (rotated key / revoked jti)  
`ERR_STATE_INVALID` (agent revoked since token issued)

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | WARN (simple expiry — clock drift or slow agent), ERROR (revoked token or revoked agent) |
| **Required Fields** | correlation_id, agent_id, token_jti, token_exp, token_iat, current_time, delta_seconds, revocation_status, CRL_version |
| **Anomaly Signal** | If `token_iat` is within the last 60s but agent is REVOKED → the revocation happened DURING the token's lifetime. Log as `REVOCATION_DURING_TOKEN_LIFETIME` with CRITICAL severity — this is a near-miss. |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Discard the expired token. Request a fresh token from the IdP.
2. **Orchestrator MUST NOT:** Retry with the same token (it will be rejected again).
3. **Orchestrator MUST NOT:** Cache tokens beyond their stated TTL. Per Canon Section 6.5: "Never Cache ALLOW Verdicts."
4. **Orchestrator MUST:** If the agent was REVOKED, cease all operations for that agent_id and initiate the revocation protocol.

### Alert Requirement

- Simple expiry: No alert.
- Revoked token: Alert to Security (indicates token theft or delayed revocation propagation).
- Repeated expired tokens from same agent: Alert to Operations (indicates IdP clock drift or agent not refreshing tokens).

### Recovery Path

Caller must obtain a NEW token from the IdP. If the agent is REVOKED, no recovery — the agent is permanently disabled per LS-13.

### Retry Permitted

**YES** with a new valid token. **NO** if agent is REVOKED (permanent).

### Canon/GP Reference

AC-22 (Token Signature), AC-24 (Token Expiry), AC-32 (Token TTL ≤ 60s), LS-13 (Revocation Permanence), LS-15 (State Synchronization), MF-05 (Maximum 60s TTL), GP-02 (State Dominates Intent).

### Industry Precedent

- Research report: "Credentials persist average 47 days after no longer needed." The 60-second TTL (MF-05) eliminates this drift by design.
- SPIFFE/SPIRE: SVIDs are short-lived X.509 certificates with automatic rotation.
- Google BeyondCorp: Session tokens revalidated continuously, not trusted beyond issuance context.

### The Silent Authority Drift Threat

Per the research report's answer to "What failure mode causes the most silent authority drift?": **Stale, unrevoked credentials combined with missing access review processes.** FM-02 is the most critical failure mode because it directly addresses this threat. The 60-second TTL is the primary structural defense. Without it, tokens outlive their authorization context, creating invisible governance gaps.

---

## 5. FM-03: POLICY VERSION MISMATCH

### Trigger Condition

The `context.policy_version_hash` in the request does not match the SHA-256 hash of the policy bundle currently loaded in the PDP.

This means one of:
- The policy was updated after the caller's last authentication but before this request.
- The PDP restarted and loaded a newer policy bundle.
- The caller is operating against a cached/stale policy version.
- The PDP has not finished loading policies (bundle partially loaded).

### Evaluation Stage

**Stage 1** (sub-step 1.7 per Day 3).

### Required Verdict

**DENY**

### HTTP Status

`409 Conflict`

### Reason Code

`ERR_POLICY_VERSION_MISMATCH`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | INFO (normal during policy rollouts), WARN (if persistent — caller not refreshing) |
| **Required Fields** | correlation_id, agent_id, caller_policy_hash, pdp_policy_hash, policy_update_timestamp, request_timestamp |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Invalidate all cached policy state and tokens.
2. **Orchestrator MUST:** Re-authenticate the agent against the IdP to obtain tokens reflecting current policy.
3. **Orchestrator MUST:** Obtain the current policy_version_hash from the PDP metadata endpoint (if available) or from the IdP.
4. **Orchestrator MUST NOT:** Retry with the same stale policy hash.
5. **Orchestrator MUST NOT:** Attempt to "guess" the current policy hash.

### Alert Requirement

- During planned policy rollout (first 72 hours per SE-01 Deprecation Window): No alert.
- After rollout stabilization: WARN if >10% of requests show mismatch (indicates deployment propagation failure).
- Persistent mismatch from a single agent: Alert (indicates the agent is not refreshing its policy context).

### Recovery Path

Caller obtains current policy version, re-authenticates, and resubmits with matching policy_version_hash.

### Retry Permitted

**YES** — after obtaining current policy version and fresh tokens.

### Canon/GP Reference

LS-15 (State Synchronization — "The New Enemy"), RES-04 (Stale Revocation), RES-14 (Version Drift), GP-06 (Fail-Closed on Uncertainty).

### Industry Precedent

- **OPA vulnerability:** OPA starts answering queries before bundles finish downloading, returning `undefined` (empty `{}`). Callers interpret this as "allowed." The policy_version_hash prevents this: if the PDP hasn't loaded policies, its hash is null, which won't match any caller's hash → DENY.
- AWS Cedar: Policies are loaded atomically — requests during reload are queued, not served against partial state.

### Why This Failure Mode Is Critical

A policy version mismatch means the caller and the PDP disagree about the rules of the game. Any ALLOW produced under this disagreement is suspect: the token may have been issued under old, permissive policy that has since been tightened. This is a TOCTOU vulnerability at the policy level — the time of token issuance (check) and the time of PDP evaluation (use) occurred under different policy regimes. The only safe response is to invalidate everything and start fresh.

---

## 6. FM-04: EXTERNAL STATE UNAVAILABLE

### Trigger Condition

The PDP cannot reach a required external dependency:
- **Agent State Registry** unreachable (cannot verify agent lifecycle — Stage 2).
- **Certificate Revocation List (CRL)** stale (age > MAX_CRL_STALENESS = 500ms — Stage 1).
- **Resource Registry** unreachable (cannot cross-reference data classification — Stage 4).
- **Clock synchronization** lost (NTP drift > acceptable threshold — Stage 1).
- **Deduplication store** unreachable (cannot verify correlation_id uniqueness — Stage 1).
- **Rate counter / Mosaic accumulator** unreachable (cannot evaluate risk gates — Stage 5).

### Evaluation Stage

Multiple stages depending on which dependency failed.

### Required Verdict

**DENY**

### HTTP Status

`503 Service Unavailable`

### Reason Code

`ERR_SYSTEM_UNCERTAINTY`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket (if reachable), Local emergency buffer (always — defense in depth) |
| **Severity** | CRITICAL |
| **Required Fields** | correlation_id, timestamp, failed_dependency (name + endpoint), last_successful_contact, failure_type (timeout/connection_refused/dns_failure), pdp_instance |
| **Circuit Breaker State** | Log the circuit breaker state transition: CLOSED→OPEN. Include the failure threshold that triggered the transition. |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Treat `503` as a transient failure. Retry is permitted but ONLY with exponential backoff.
2. **Orchestrator MUST NOT:** Fall back to a cached ALLOW verdict. Per Canon Section 6.5: "Never Cache ALLOW Verdicts."
3. **Orchestrator MUST NOT:** Bypass Sarathi and call the downstream resource directly. The Action Authorization Boundary is inviolable.
4. **Orchestrator MUST:** Queue pending agent actions until the PDP recovers. Actions that cannot be queued (time-sensitive) must be dropped (not executed without authorization).
5. **Orchestrator SHOULD:** Implement a health check endpoint to detect PDP recovery and resume normal operation.

### Alert Requirement

**Immediate alert to Operations** with:
- Which dependency failed.
- When the failure was first detected.
- How many requests are being denied due to the failure.
- Estimated blast radius (how many agents affected).

### Recovery Path

When the external dependency becomes reachable again:
1. PDP verifies dependency state is fresh (CRL age < 500ms, registry responsive).
2. PDP transitions circuit breaker from OPEN → HALF-OPEN → CLOSED.
3. PDP logs recovery event to BHIV Bucket.
4. Normal evaluation resumes. No automatic retry of denied requests — each must be resubmitted.

### Retry Permitted

**YES** — with exponential backoff (recommended: 100ms, 200ms, 400ms, 800ms, max 5 retries).

### Canon/GP Reference

GP-06 (Fail-Closed on Uncertainty), RES-04 (Stale Revocation — CRL staleness), GP-02 (State Dominates Intent).

### Industry Precedent

- Research report: "When a dependency is unreachable, the system must deny all requests rather than assume temporary conditions warrant permissive access. Recommended timeout thresholds are 100ms with immediate fail-closed behavior."
- Google Zanzibar: Uses zookies to detect stale state — if the local cache is older than the client's consistency token, the request is denied or re-routed.
- Istio: Default `failurePolicy: Fail` for authorization webhooks — request blocked when webhook unavailable.

### The "Better to Halt the Market" Principle

Per RES-04: "It is better to halt the system than to allow an unauthorized breach." A PDP operating without reliable state is a PDP that cannot distinguish authorized from unauthorized requests. Any ALLOW it produces is a guess. In governance, guessing is indistinguishable from failure.

---

## 7. FM-05: AUDIT SINK UNAVAILABLE

### Trigger Condition

The BHIV Bucket (write-only audit store) is unreachable, returns an error, or does not acknowledge the write within AUDIT_WRITE_TIMEOUT (200ms).

### Evaluation Stage

**Stage 7 — Audit Write** (sub-steps 7.2-7.4 per Day 3).

### Required Verdict

**DENY** — regardless of the evaluation outcome from Stages 1-6. Even if the request would have been ALLOW, the verdict is overridden to DENY.

### HTTP Status

`500 Internal Server Error`

### Reason Code

`ERR_AUDIT_WRITE_FAILED`

### Logging Requirement

| Field | Value |
|---|---|
| **Primary Destination** | Local emergency buffer (since BHIV Bucket is unavailable) |
| **Secondary Destination** | Stderr/syslog (for operational visibility) |
| **Severity** | CRITICAL |
| **Required Fields** | correlation_id, original_verdict (what Stages 1-6 produced), override_verdict (DENY), agent_id, action, resource_id, timestamp, audit_write_error, bhiv_endpoint, bhiv_last_successful_write |
| **Emergency Buffer** | Must be a local, append-only file with WORM-equivalent protection. When BHIV Bucket recovers, emergency buffer contents must be flushed to BHIV Bucket in order. |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Treat this as a system failure. Do not proceed with any agent action.
2. **Orchestrator MUST NOT:** Assume the original verdict was ALLOW and act on it. The override is authoritative.
3. **Orchestrator SHOULD:** Alert human operators that the governance audit trail is broken.
4. **Orchestrator SHOULD:** Implement a BHIV Bucket health check to detect recovery.

### Alert Requirement

**IMMEDIATE alert to Security AND Operations.** This is a governance-critical failure. The audit trail is the flight recorder. A broken flight recorder during flight is a landing-condition event.

### Recovery Path

1. BHIV Bucket becomes available.
2. PDP verifies write capability (test write + verify acknowledgment).
3. PDP flushes emergency buffer to BHIV Bucket (maintaining original timestamps and ordering).
4. PDP resumes normal audit writes.
5. PDP logs recovery event including: duration of outage, count of denied-due-to-audit-failure requests, emergency buffer entries count.

### Retry Permitted

**YES** — after BHIV Bucket recovery is confirmed. But the original request must be resubmitted (the caller cannot "resume" a denied request).

### Canon/GP Reference

AI-53 (Write-Only Bucket), AI-54 (Tamper Evidence Chain), AI-55 (Full Context Logging), OUT-07 (Audit-Coupled), RE-50 (Mandatory Denial Logging).

### Why ALLOW Is Overridden

Per Day 2 Assessment (Section 11.2): "An unauditable ALLOW is more dangerous than a false DENY. A false DENY causes operational friction. An unauditable ALLOW creates a governance blind spot that may never be discovered." If the audit write fails but the ALLOW stands, there is:
- No record that the action was authorized.
- No record of which rules permitted it.
- No record for compliance (EU AI Act Article 12 requires automatic event logging).
- No evidence for incident investigation if the action causes harm.

The false DENY is recoverable (the agent resubmits when audit is available). The unauditable ALLOW is not.

---

## 8. FM-06: AMBIGUOUS RULE RESOLUTION

### Trigger Condition

During policy evaluation (Stages 3-5), one or more of the following occurs:
- Two Canon rules produce conflicting results for the same request (Rule A says ALLOW, Rule B says DENY).
- No Canon rule produces an applicable result for this request (all rules return NOT_APPLICABLE).
- A rule evaluation produces an internal error (cannot determine TRIGGERED_ALLOW or TRIGGERED_DENY).
- A rule references an undefined attribute or unknown resource type.

### Evaluation Stage

**Stage 6 — Refusal Classification** (where the deny-overrides combining algorithm resolves conflicts).

### Required Verdict

**DENY**

### HTTP Status

`403 Forbidden` (if rules conflict or are silent)  
`500 Internal Server Error` (if rule evaluation throws internal error)

### Reason Code

`ERR_RULE_CONFLICT` (conflicting rules)  
`ERR_NO_APPLICABLE_RULE` (all rules silent)  
`ERR_RULE_EVALUATION_ERROR` (internal rule error)

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | WARN (rule conflict — expected during policy transitions), ERROR (no applicable rule — potential coverage gap), CRITICAL (rule evaluation error — policy engine bug) |
| **Required Fields** | correlation_id, agent_id, action, resource_type, resource_id, conflicting_rules (ids of both ALLOW and DENY rules), combining_algorithm_applied, final_verdict, all_rule_results |
| **Policy Gap Detection** | If reason is `ERR_NO_APPLICABLE_RULE`, log as a POLICY_COVERAGE_GAP with the full request signature (agent_class + action + resource_type). This signals that the Canon needs a new rule. |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Treat as DENY. Do not retry with the same parameters (the rules haven't changed).
2. **For POLICY_COVERAGE_GAP:** Operators must review and add a Canon rule for the uncovered scenario.
3. **For RULE_EVALUATION_ERROR:** Engineering must investigate the broken rule as a production incident.

### Alert Requirement

- Rule conflict: INFO (log only — handled by deny-overrides).
- No applicable rule: WARN to Policy Administration team (Canon coverage gap).
- Rule evaluation error: CRITICAL alert to Engineering (policy engine bug).

### Recovery Path

- Rule conflict: None required — deny-overrides handles this correctly.
- No applicable rule: Policy team adds a new Canon rule. Agent retries after policy update propagates.
- Rule evaluation error: Engineering fixes the broken rule. PDP reloads policy bundle.

### Retry Permitted

- Rule conflict: **NO** (same request will produce same conflict until policy changes).
- No applicable rule: **YES** after new policy version is deployed.
- Rule evaluation error: **YES** after policy engine fix is deployed.

### Canon/GP Reference

GP-01 (Silence Implies Denial — no applicable rule = DENY), GP-03 (Conflict Resolves to Restriction — DENY wins), GP-06 (Fail-Closed on Uncertainty — error = DENY).

### The Deny-Overrides Guarantee

Per Day 3, Section 11.1 (Conflict Resolution):
```
IF has_deny:     RETURN DENY      // Any deny wins
IF has_escalate: RETURN ESCALATE  // Deferral > permission
IF has_allow:    RETURN ALLOW     // Explicit permission
RETURN DENY                       // Silence = denial
```

This algorithm makes ambiguity structurally impossible at the verdict level. There may be ambiguity at the rule level (individual rules conflict), but the combining algorithm always produces a deterministic verdict. The "ambiguity" in FM-06 refers to rule-level conditions that the combining algorithm resolves to DENY.

---

## 9. FM-07: INTERNAL LOGIC FAULT

### Trigger Condition

The PDP encounters an unhandled exception, null pointer dereference, stack overflow, out-of-memory condition, infinite loop detection, or any internal bug that prevents deterministic evaluation.

### Evaluation Stage

**Any stage** (1 through 7). Internal faults can occur anywhere in the pipeline.

### Required Verdict

**DENY**

### HTTP Status

`500 Internal Server Error`

### Reason Code

`ERR_INTERNAL_FAULT`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket (attempt), Local emergency buffer (always), Cold storage (core dump) |
| **Severity** | CRITICAL |
| **Required Fields** | correlation_id, pdp_instance, pdp_version, stage_at_failure, exception_type, stack_trace_hash (NOT the full stack trace — per GP-05, internal details are not exposed), timestamp |
| **Core Dump** | Full memory dump written to cold storage for post-mortem analysis. This is a governance-critical bug. |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Treat as system failure. Do not retry immediately — the fault may be reproducible.
2. **Orchestrator MUST NOT:** Bypass Sarathi.
3. **Orchestrator SHOULD:** Route subsequent requests to a different PDP instance (if available in HA configuration).

### Alert Requirement

**IMMEDIATE alert to Engineering AND Security.** Internal faults in a governance system are production incidents. Per Task 3, Failure Mode D: "This is a governance-critical bug and must be treated as a production incident."

### Recovery Path

Engineering investigates and patches the bug. PDP instance is restarted with the fix.

### Retry Permitted

**YES** — after the faulty PDP instance is replaced or restarted. Preferably to a different PDP instance.

### Canon/GP Reference

GP-06 (Fail-Closed on Uncertainty), Canon Section 6.1: "If Sarathi returns HTTP 500, the answer is DENY."

---

## 10. FM-08: CHANNEL BINDING FAILURE

### Trigger Condition

The `agent_identity.session_binding` (SHA-256 of TLS client certificate) does not match the TLS client certificate on the current connection. The token is valid, but it's being presented from a DIFFERENT transport channel than the one it was issued to.

### Evaluation Stage

**Stage 1** (sub-step 1.11).

### Required Verdict

**DENY**

### HTTP Status

`401 Unauthorized`

### Reason Code

`ERR_SESSION_BINDING`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | **HIGH** — this is a strong indicator of token theft |
| **Required Fields** | correlation_id, agent_id, expected_session_binding (from token), actual_session_binding (from TLS), source_ip, token_jti |
| **Anomaly Signal** | Log as `TOKEN_THEFT_INDICATOR`. Cross-reference with other requests from the same agent_id to detect if the legitimate session is still active (parallel usage = confirmed theft). |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Invalidate the token.
2. **Orchestrator MUST:** Consider the agent session compromised.
3. **Orchestrator SHOULD:** Initiate re-authentication from scratch (new TLS session, new tokens).

### Alert Requirement

**Alert to Security.** Channel binding failure is one of the strongest signals of active attack (token stolen and replayed from a different connection). Per Task 3 Failure Mode F: "This is a strong indicator of token theft. Immediate security alert."

### Retry Permitted

**NO** with the same token. The token is compromised. A completely new authentication flow is required.

### Canon/GP Reference

RES-09 (Channel Binding), GP-05 (Observation ≠ Verification), ID-02 (Session Binding Requirement).

---

## 11. FM-09: REPLAY DETECTION

### Trigger Condition

Either:
- The `context.request_timestamp` is older than MAX_REQUEST_AGE (5000ms).
- The `correlation_id` has been seen within the DEDUP_WINDOW (60s).

### Evaluation Stage

**Stage 1** (sub-steps 1.4 and 1.6).

### Required Verdict

**DENY**

### HTTP Status

`400 Bad Request`

### Reason Code

`ERR_REPLAY_DETECTED`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | ERROR |
| **Required Fields** | correlation_id, agent_id (if parseable), request_timestamp, current_timestamp, delta_ms, duplicate_of (previous audit_id if correlation_id was seen before) |

### Downstream Behavior Requirement

1. **Orchestrator MUST NOT:** Retry with the same correlation_id.
2. **Orchestrator MUST:** Generate a new correlation_id and fresh timestamp for any resubmission.

### Alert Requirement

- Single occurrence: No alert.
- Pattern (>5 replays from same agent in 60s): Alert to Security (possible replay attack).

### Retry Permitted

**YES** — as a new request with new correlation_id and fresh timestamp.

### Canon/GP Reference

INV-08 (Freshness), INV-09 (Non-Replayability), RES-04 (Stale Revocation — timestamp freshness).

---

## 12. FM-10: CASCADING REVOCATION DISCOVERY

### Trigger Condition

During Stage 2 lifecycle validation, the PDP discovers that a principal in the agent's `delegation_chain` has been REVOKED since the agent's token was issued.

### Evaluation Stage

**Stage 2** (sub-step 2.3).

### Required Verdict

**DENY**

### HTTP Status

`403 Forbidden`

### Reason Code

`ERR_CASCADING_REVOCATION`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket |
| **Severity** | ERROR |
| **Required Fields** | correlation_id, agent_id, revoked_parent_id, revocation_timestamp, delegation_chain_depth, all_affected_descendants |

### Downstream Behavior Requirement

1. **Orchestrator MUST:** Cease all operations for this agent AND all descendant agents.
2. **Orchestrator MUST:** Invalidate all tokens issued under the revoked parent's authority.
3. **Orchestrator MUST NOT:** Allow any descendant to continue operating.

### Alert Requirement

Alert to Security: cascading revocation indicates a parent entity was compromised.

### Retry Permitted

**NO.** The revocation is permanent per LS-13. The agent must be re-provisioned with a new delegation chain from a valid authority.

### Canon/GP Reference

LS-19 (Cascading Revocation), LS-13 (Revocation Permanence), GP-02 (State Dominates Intent).

---

## 13. FM-11: EVALUATION TIMEOUT

### Trigger Condition

The total evaluation time exceeds the 50ms budget (EVAL-07 from Day 3).

### Evaluation Stage

Any stage — the timeout applies to the total pipeline.

### Required Verdict

**DENY**

### HTTP Status

`500 Internal Server Error`

### Reason Code

`ERR_EVALUATION_TIMEOUT`

### Logging Requirement

| Field | Value |
|---|---|
| **Destination** | BHIV Bucket, Operations dashboard |
| **Severity** | CRITICAL |
| **Required Fields** | correlation_id, total_evaluation_ms, stage_at_timeout, stages_completed, pdp_instance, system_load |

### Downstream Behavior

Orchestrator should route to a different PDP instance. May retry after brief backoff.

### Retry Permitted

**YES** — preferably to a different PDP instance.

### Canon/GP Reference

EVAL-07 (Deterministic Duration), GP-06 (Fail-Closed).

---

## 14. FM-12: HSM / SIGNING KEY UNAVAILABLE

### Trigger Condition

The PDP cannot access its Ed25519 private key (HSM unavailable, key file corrupted) and therefore cannot sign the response.

### Evaluation Stage

**Stage 7** (sub-step 7.5).

### Required Verdict

**DENY** — an unsigned response MUST be treated as DENY by callers (OUT-04).

### HTTP Status

`500 Internal Server Error`

### Reason Code

`ERR_SIGNING_FAILURE`

### Logging Requirement

CRITICAL severity. Alert to Security and Operations immediately.

### Downstream Behavior

Per Canon Section 6.9: "An unsigned or tampered verdict from a man-in-the-middle must be treated as DENY." The caller verifies the signature and, finding it missing/invalid, treats the response as DENY.

### Recovery Path

HSM is restored or key is rotated to a backup key.

### Retry Permitted

**YES** — after PDP signing capability is restored.

### Canon/GP Reference

OUT-04 (Signed), Canon Section 6.9, VERDICT_SIGNATURE_ALG: Ed25519.

---

## 15. COMPOUND FAILURE SCENARIOS

Real failures rarely occur in isolation. This section addresses scenarios where multiple failure modes co-occur.

| Scenario | Failures Combined | Resolution | Rationale |
|---|---|---|---|
| **PDP starts with empty policy + audit sink down** | FM-03 + FM-05 | DENY. Log to emergency buffer. Alert Ops + Security. PDP refuses ALL requests until both dependencies recover. | Two independent failures, both independently produce DENY. |
| **Token expired + CRL stale** | FM-02 + FM-04 | DENY. Even if CRL were fresh, the expired token alone produces DENY. The CRL staleness is logged but doesn't change the outcome. | Earlier-stage failure (token expiry in Stage 1) short-circuits before CRL relevance (also Stage 1). |
| **Agent revoked + audit write fails** | FM-10 + FM-05 | DENY. The revocation produces DENY in Stage 2. The audit write failure is handled by the emergency buffer. | DENY from Stage 2 + DENY override from Stage 7 = DENY regardless. |
| **Rule conflict + internal fault in combining** | FM-06 + FM-07 | DENY. The internal fault prevents combining, but the fail-closed axiom produces DENY. | Any internal error = DENY (FM-07 supersedes FM-06). |
| **All external dependencies down simultaneously** | FM-04 (all variants) | DENY. The PDP cannot evaluate ANY request. It becomes a DENY-only service until recovery. ALL requests receive `503 ERR_SYSTEM_UNCERTAINTY`. | This is the "total outage" scenario. The PDP is still functional — it's denying everything, which is the correct behavior. |

### The "Total Outage" Property

When all external dependencies fail, the Sarathi PDP degrades to a **universal DENY service**. This is correct behavior. The alternative — shutting down entirely — would leave downstream systems without any governance response, and some may interpret silence as permission (the Redis incident pattern). A PDP that responds DENY to everything is safer than a PDP that responds to nothing.

---

## 16. FAILURE RECOVERY PROTOCOL

### 16.1 Recovery Sequence

When any failed dependency recovers:

1. **Verify:** Confirm the dependency is genuinely available (not just responding to health checks but serving stale data).
2. **Validate State:** Ensure the recovered dependency's state is fresh. For CRL: age < 500ms. For State Registry: consistency check against last known state.
3. **Flush Emergency Buffer:** If FM-05 occurred, flush local emergency buffer to BHIV Bucket in chronological order.
4. **Transition Circuit Breaker:** OPEN → HALF-OPEN (serve one request) → if successful → CLOSED (resume normal).
5. **Log Recovery:** Record the recovery event with: outage duration, requests denied during outage, emergency buffer entries flushed.
6. **Verify Normal Operation:** First few requests after recovery are evaluated normally AND cross-checked against the emergency buffer for consistency.

### 16.2 What Recovery Does NOT Do

- **Auto-replay denied requests:** Denied requests are gone. Each must be resubmitted by the caller.
- **Grant retroactive ALLOWs:** A request denied during outage does not become ALLOW after recovery.
- **Relax scrutiny:** The first request after recovery receives the same full evaluation as any other request.

---

## 17. FAILURE MODE SUMMARY MATRIX

| FM | Name | Verdict | HTTP | Reason Code | Severity | Retry? | Alert? | Stage |
|:---:|---|:---:|:---:|---|:---:|:---:|:---:|:---:|
| **FM-01** | Missing Field | DENY | 400 | ERR_SCHEMA_VIOLATION | WARN | YES (new request) | If pattern | 1 |
| **FM-02** | Stale Token | DENY | 401 | ERR_TOKEN_EXPIRED | WARN-ERROR | YES (new token) | If revoked | 1-2 |
| **FM-03** | Policy Mismatch | DENY | 409 | ERR_POLICY_VERSION_MISMATCH | INFO-WARN | YES (re-auth) | If persistent | 1 |
| **FM-04** | External State Down | DENY | 503 | ERR_SYSTEM_UNCERTAINTY | CRITICAL | YES (backoff) | IMMEDIATE | 1-5 |
| **FM-05** | Audit Sink Down | DENY | 500 | ERR_AUDIT_WRITE_FAILED | CRITICAL | YES (after recovery) | IMMEDIATE | 7 |
| **FM-06** | Ambiguous Rules | DENY | 403/500 | ERR_RULE_CONFLICT | WARN-CRIT | Depends | If gap/error | 6 |
| **FM-07** | Internal Fault | DENY | 500 | ERR_INTERNAL_FAULT | CRITICAL | YES (diff instance) | IMMEDIATE | Any |
| **FM-08** | Channel Binding | DENY | 401 | ERR_SESSION_BINDING | HIGH | NO (new session) | Security | 1 |
| **FM-09** | Replay | DENY | 400 | ERR_REPLAY_DETECTED | ERROR | YES (new ID) | If pattern | 1 |
| **FM-10** | Cascading Revoke | DENY | 403 | ERR_CASCADING_REVOCATION | ERROR | NO (permanent) | Security | 2 |
| **FM-11** | Eval Timeout | DENY | 500 | ERR_EVALUATION_TIMEOUT | CRITICAL | YES (diff instance) | Operations | Any |
| **FM-12** | Signing Key Down | DENY | 500 | ERR_SIGNING_FAILURE | CRITICAL | YES (after recovery) | IMMEDIATE | 7 |

**Verification Property:** Every cell in the "Verdict" column is DENY. There is no failure mode that produces ALLOW. This is the structural proof of the fail-closed axiom.

---

## 18. Relationship to Previous Tasks




| Artifact | Relationship |
|---|---|
| **Task 1 — Governance Validation** | FM-01 through FM-12 address all 12 unsafe assumptions: A1 (semantic consistency → FM-01 fixed vocabulary), A2 (identity persistence → FM-02 short-lived tokens), A3 (orchestrator compliance → FM-05 audit enforcement), A6 (clock sync → FM-09 timestamp validation), A12 (observability → FM-04 fail-closed on missing state) |
| **Task 2 — Canon (60 Rules)** | Every Canon rule that produces DENY maps to a failure mode: AC-21→FM-01, AC-22→FM-02, AC-24→FM-02, LS-15→FM-03, LS-19→FM-10, AI-53→FM-05, EL-39→FM-01 pattern detection |
| **Task 3 — PDP Interface (7 Failure Modes)** | FM-01 = Mode A, FM-02 = Mode E, FM-04 = Mode B, FM-07 = Mode D, FM-08 = Mode F, FM-09 = Mode G. This document adds FM-03 (policy mismatch), FM-05 (audit sink), FM-06 (ambiguous rules), FM-10 (cascading revocation), FM-11 (timeout), FM-12 (signing key). |
| **Task 3 — 14 Ambiguity Resolutions** | FM-06 implements the resolution for all 14 AMBs: "Zero ambiguity results in ALLOW. When the Canon is unclear, the answer is always restrictive." |
| **Day 1 — Request Schema** | FM-01 validates every field defined in Day 1. FM-09 uses correlation_id for deduplication. FM-03 uses policy_version_hash. |
| **Day 2 — Response Schema** | FM-05 enforces OUT-07 (audit-coupled). FM-12 enforces OUT-04 (signed). All 12 FMs produce the Day 2 DENY response shape. |
| **Day 3 — Evaluation Order** | FM-01 through FM-12 map to specific stages: FM-01/02/03/08/09 in Stage 1, FM-10 in Stage 2, FM-06 in Stage 6, FM-05/12 in Stage 7, FM-04/07/11 across multiple stages. |

---

**END OF SARATHI FAILURE MODE CONTRACT**

---

## 14. EXTENDED FAILURE MODES (GAP RESOLUTION PHASE)

*Added to address delegation chain failures (Gap 2), PEP failures (Gap 1), formal verification failures (Gap 3), and audit integrity failures (Gap 5).*

### FM-13: DELEGATION CHAIN VIOLATION

**Trigger:** Delegation token (Biscuit) fails validation — expired caveat, depth exceeded, revoked block, or attenuation violation.

| Field | Value |
|---|---|
| Verdict | **DENY** |
| HTTP Status | 403 Forbidden |
| Reason Code | `ERR_DELEGATION_VIOLATION` |
| External Message | "Delegation authorization failed" (opaque per RE-45) |
| Internal Audit | Full Biscuit block trace: which caveat failed, delegation depth, chain hash, revocation ID |
| Alert Level | HIGH |
| Sub-Types | FM-13a: Depth exceeded, FM-13b: Caveat expired, FM-13c: Block revoked, FM-13d: Attenuation violation (caveat expands scope) |

**Critical Rule:** An attenuation block that EXPANDS scope (violating GP-08) triggers FM-13d with CRITICAL alert and immediate SOC notification. This indicates either a Biscuit implementation bug or a forgery attempt.

### FM-14: PEP CIRCUIT BREAKER OPEN

**Trigger:** PEP's circuit breaker to PDP is in OPEN state (PDP unavailable or degraded).

| Field | Value |
|---|---|
| Verdict | **DENY** |
| HTTP Status | 503 Service Unavailable |
| Reason Code | `ERR_PEP_CIRCUIT_OPEN` |
| External Message | "Authorization service temporarily unavailable" |
| Internal Audit | Circuit breaker state, PDP failure count, last successful evaluation timestamp, PEP type |
| Alert Level | CRITICAL (if duration > 5 minutes) |
| Fallback | Cached decisions (max 60s staleness) → degraded mode (read-only) → full denial |

**Recovery:** When PDP recovers and circuit transitions to HALF-OPEN, 3 probe requests are sent. 2/3 success → CLOSED. Any failure → back to OPEN for another 30 seconds.

### FM-15: DPoP PROOF VALIDATION FAILURE

**Trigger:** DPoP proof JWT fails verification — signature mismatch, `ath` hash doesn't match Biscuit, SPIFFE ID doesn't match workload attestation, or `jti` replayed.

| Field | Value |
|---|---|
| Verdict | **DENY** |
| HTTP Status | 401 Unauthorized |
| Reason Code | `ERR_PROOF_INVALID` |
| External Message | "Authorization proof failed" (opaque) |
| Internal Audit | Which DPoP check failed, expected vs. actual values (hashed), SPIFFE attestation details |
| Alert Level | HIGH (potential token theft if ath matches but SPIFFE doesn't) |

### FM-16: AUDIT HASH CHAIN BREAK

**Trigger:** Hash chain integrity verification detects `current_event_hash != sha256(event + prev_event_hash)`, indicating potential tampering or data corruption.

| Field | Value |
|---|---|
| Verdict | Current evaluations continue (audit failure does NOT deny — audit is async) |
| Operational Response | **IMMEDIATE HALT** of audit writes to affected chain. Switch to emergency buffer. |
| Alert Level | **CRITICAL** — SOC notification within 30 seconds |
| Investigation | Forensic comparison of hash chain segments. Identify break point. Determine if corruption or tampering. |
| Recovery | RES-19 branch-and-merge reconciliation. Merkle batch integrity verification from last known-good HSM-signed root. |

### FM-17: FORMAL VERIFICATION FAILURE

**Trigger:** Lean proof fails, SMT analysis finds violation, DRT detects Lean-vs-Rust divergence, or mutation score drops below 98%.

| Field | Value |
|---|---|
| Verdict | **BLOCK DEPLOYMENT** (not a runtime failure — this is a CI/CD gate) |
| Response | Policy change rejected. Build fails. Cannot merge. |
| Alert Level | HIGH |
| Sub-Types | FM-17a: Lean proof failure (property violation), FM-17b: SMT counterexample found, FM-17c: DRT divergence, FM-17d: Mutation score < 98%, FM-17e: SMT timeout (GP-09: treated as unknown, requires human review) |

**All FM-17 sub-types block deployment. There is no override. Deployment resumes only when the verification pipeline passes completely.**

---

## UPDATED COMPOUND SCENARIOS

### Compound 6: Delegation Chain + Circuit Breaker + Audit Failure (Triple Fault)

Agent A delegates to Agent B via Biscuit token. Agent B makes a request. The PDP circuit breaker is in HALF-OPEN state. The probe request succeeds but the BHIV Bucket is also experiencing write latency.

**Sequence:**
1. Agent B presents Biscuit + DPoP proof → PEP forwards to PDP (HALF-OPEN probe)
2. PDP evaluates → ALLOW (probe succeeds, circuit transitions to CLOSED)
3. Stage 7 attempts audit write → BHIV responds slowly (> 200ms timeout)
4. FM-05 fires → ALLOW overridden to DENY
5. Agent B receives DENY despite valid delegation and passing all policy checks

**Correct Behavior:** DENY. The audit guarantee (AI-55) supersedes the delegation authorization. Agent B must retry. The circuit breaker remains CLOSED (the PDP evaluation succeeded; only the audit write failed).

### Compound 7: Multi-Tenant Circuit Breaker Isolation Test

Tenant A experiences legitimate traffic spike (Black Friday). Tenant B has normal traffic.

**Sequence:**
1. Tenant A's rate counter exceeds threshold → EL-39 fires for Tenant A agents
2. Tenant A's circuit breaker enters OPEN → all Tenant A requests DENIED
3. Tenant B's circuit breaker remains CLOSED → Tenant B requests evaluated normally
4. Tenant A's spike subsides → circuit transitions HALF-OPEN → probes succeed → CLOSED

**Correct Behavior:** Tenant B is NEVER affected. Circuit breakers are tenant-scoped (ENF-14, RES-20). The ONLY shared circuit breaker is for PDP infrastructure failure (PDP process itself is down), which affects all tenants equally.

---

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Failure Modes Defined | 17 (12 original + 5 gap resolution) |
| Compound Scenarios Documented | 7 (5 original + 2 gap resolution) |
| Recovery Protocols | 1 (unified) + 3 extended (circuit breaker, hash chain, verification) |
| Verdicts Across All Failure Modes | DENY (100% — zero ALLOW for runtime FMs), BLOCK (for CI/CD gate FM-17) |
| HTTP Status Codes Used | 400, 401, 403, 409, 500, 503 |
| Reason Codes Used | 17 unique codes |
| Alert Levels | INFO, WARN, ERROR, HIGH, CRITICAL |
| Canon Rules Referenced | AC-21, AC-22, AC-24, AC-25, AC-29, AC-30, AC-32, AI-53, AI-54, AI-55, AI-56, EL-33, EL-39, EL-44, LS-13, LS-15, LS-19, LS-20, RE-45, RE-48, RE-50 |
| Global Principles Invoked | GP-01 through GP-09 |
| Ambiguity Resolutions Referenced | RES-04, RES-05, RES-08, RES-09, RES-14, RES-15, RES-16, RES-17, RES-18, RES-19, RES-20 |
| Industry Standards | NIST SP 800-53, NIST SP 800-207, CWE-636, XACML 3.0, AWS Cedar (Lean 4), OPA, Zanzibar, SPIFFE/SPIRE, RFC 9449, Biscuit, DeepMind DCT, EU AI Act Art. 12 |
| Task 3 Failure Modes Mapped | 7/7 (A-G) mapped + 10 new modes added |

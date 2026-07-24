# AUDIT RECONSTRUCTION PROTOCOL

**Author:** Hemanth B
**Target System:** Sarathi Governance Kernel — Policy Decision Point
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026
**Task Reference:** Observability & Traceability Contract — Phase C
**Upstream Dependencies:**
- `decision_trace_spec.md` (Phase A) — defines trace record structure, integrity properties DT-01 through DT-10
- `drift_detection_spec.md` (Phase B) — defines drift metrics and alert framework
- `sarathi_response_schema.md` (Day 2) — defines audit_id, correlation_id, determining_rules
- `failure_mode_contract.md` (Day 4) — defines FM-05 (audit sink failure), FM-16 (hash chain break)
- `sarathi_pdp_lock_v1.md` (v1.1) — defines G-05 (Mandatory Audit), 4-layer immutability
- `SARATHI_PDP_INTERFACE.md` (Task 3) — defines audit event schema, retention tiers, PII handling

**Scope Boundary:** This document defines how to RECONSTRUCT past decisions. It does NOT modify the PDP evaluation logic, Canon rules, or any schema. It is a procedural specification for post-hoc analysis.

---

## 1. PURPOSE

A governance system that cannot explain its past decisions is not a governance system — it is a black box with authority. This protocol exists so that when a dispute arises ("why was Agent X denied access to Resource Y on Tuesday at 14:32 UTC?"), the answer is reconstructable, defensible, and verifiable — even years after the decision.

The protocol answers five questions for any historical decision:
1. **What was decided?** — the verdict
2. **Why?** — which rules triggered, in what order
3. **What context existed?** — agent state, policy version, system health
4. **Has anything changed since?** — policy updates, revocations, corrections
5. **Is the record authentic?** — cryptographic proof of integrity

---

## 2. RECONSTRUCTION ENTRY POINTS

An investigator may begin reconstruction from any of these identifiers:

| Entry Point | Where to Find It | Lookup Path |
|---|---|---|
| **correlation_id** | Request logs, agent logs, downstream resource logs | Direct lookup in BHIV Bucket → decision trace record |
| **audit_id** | PDP response (always returned), downstream token claims | Direct key lookup in BHIV Bucket |
| **trace_id** | Internal PDP traces, operations dashboards | Direct key lookup in BHIV Bucket |
| **token_jti** | Capability token claims, downstream resource logs | Index lookup: token_jti → trace_id → full record |
| **agent_id + time range** | Incident report, security alert | Range query: agent_id + timestamp window → list of trace records |
| **resource_id_hash + time range** | Resource access logs, compliance inquiry | Range query: resource_id_hash + timestamp window → list of trace records |
| **escalation_reference** | Governance Council records | Index lookup: escalation_reference → trace_id → full record |

Every entry point leads to a decision trace record. From that record, the full reconstruction begins.

---

## 3. RECONSTRUCTION PROCEDURE

### 3.1 Step 1 — Retrieve the Decision Trace Record

```
INPUT:  identifier (correlation_id | audit_id | trace_id | token_jti | agent_id+time | resource_id_hash+time)
OUTPUT: decision_trace_record

PROCEDURE:
  1. Determine storage tier by timestamp:
     - < 3 months ago  → Query Elasticsearch (Hot tier, < 1s)
     - 3-12 months ago → Query S3 Standard (Warm tier, < 5 min)
     - > 12 months ago → Retrieve from S3 Object Lock (Cold tier, < 4 hours)
  
  2. Retrieve record by identifier.
  
  3. If record not found:
     a. Check emergency buffer archive (FM-05 fallback records)
     b. Check immudb for hash chain continuity around the timestamp
     c. If still not found → RECORD_NOT_FOUND. Log as potential governance gap.
        This is a reportable incident (DT-01 violation).
```

### 3.2 Step 2 — Verify Record Integrity

Before using any trace record for reconstruction, verify it has not been tampered with.

```
PROCEDURE:
  1. HASH CHAIN VERIFICATION
     a. Retrieve the previous record (by prev_event_hash)
     b. Compute SHA-256(previous_record)
     c. Compare against this record's prev_event_hash
     d. If mismatch → INTEGRITY_VIOLATION. Stop reconstruction.
        This record or its predecessor has been tampered with.
        Invoke FM-16 (Hash Chain Break) incident protocol.
  
  2. MERKLE PROOF VERIFICATION
     a. Identify the Merkle batch this record belongs to (merkle_batch_id)
     b. Retrieve the HSM-signed Merkle root for that batch
     c. Compute the Merkle proof: record → intermediate hashes → root
     d. Verify Ed25519 signature on the Merkle root using HSM public key
     e. If signature invalid → INTEGRITY_VIOLATION. Stop reconstruction.
        The batch has been tampered with or the HSM key was compromised.
  
  3. IMMUDB CROSS-VERIFICATION
     a. Query immudb for the same trace_id
     b. Compare record hashes
     c. If mismatch → INTEGRITY_VIOLATION. The BHIV Bucket or immudb has diverged.
  
  4. If all three checks pass → INTEGRITY_VERIFIED. Proceed to Step 3.
```

### 3.3 Step 3 — Reconstruct the Decision Context

Retrieve the full context that existed at the time of the decision.

```
PROCEDURE:
  1. POLICY RECONSTRUCTION
     a. Read pdp_policy_hash from the trace record
     b. Retrieve the archived policy bundle with that hash
        (Policy bundles are archived per AI-57 and SE-06)
     c. Verify the bundle hash matches
     d. This is the EXACT policy the PDP used for this decision
  
  2. AGENT STATE RECONSTRUCTION
     a. Read agent_id and request_received_at from the trace record
     b. Query the Agent State Registry historical log for the agent's state
        at that timestamp (ACTIVE, SUSPENDED, REVOKED, TERMINATED)
     c. If registry historical log is unavailable, note as CONTEXT_PARTIAL
  
  3. CRL STATE RECONSTRUCTION
     a. Read crl_staleness_ms from the trace record
     b. If staleness was > 0, the CRL was not perfectly fresh at decision time
     c. Retrieve the CRL snapshot closest to decision time (if archived)
     d. Identify whether any revocations occurred between CRL snapshot and decision
  
  4. DELEGATION CHAIN RECONSTRUCTION (if delegation_depth > 0)
     a. Read delegation_chain_hash from the trace record
     b. Cross-reference with Biscuit revocation logs
     c. Verify: was the delegation chain valid at decision time?
     d. Verify: has the chain been revoked SINCE decision time?
  
  5. SYSTEM HEALTH RECONSTRUCTION
     a. Read circuit_breaker_state, state_registry_latency_us, crl_staleness_ms
     b. Cross-reference with infrastructure monitoring logs for that timestamp
     c. Identify any degraded dependencies at decision time
```

### 3.4 Step 4 — Reconstruct the Rule Evaluation Path

Explain WHY the verdict was what it was.

```
PROCEDURE:
  1. Read the stages array from the trace record
  
  2. For each stage (1-7):
     a. If status == "PASS" → this stage did not block the request
     b. If status == "DENY" → this stage blocked the request
        - Read determining_rules for the specific Canon rules
        - Read deny_reason for the internal reason code
        - Look up the rule definition in the archived policy bundle (Step 3.1)
     c. If status == "SKIPPED_SHORT_CIRCUIT" → this stage was never evaluated
        because a prior stage denied
     d. If status == "ERROR" → this stage encountered an internal error
        - Read internal_notes
        - Cross-reference with FM contract to identify which failure mode applied
  
  3. Read was_masked from the trace record
     a. If true → the external reason code sent to the caller (external_reason_code)
        differs from the internal reason (reason_code)
     b. This means RE-45 (Opaque Security Refusal) was applied
     c. The caller received "ACCESS_DENIED"; the real reason is in reason_code
  
  4. Compile the evaluation path:
     Stage 1 [PASS/DENY] → Stage 2 [PASS/DENY/SKIP] → ... → Stage 7 [PASS/ERROR]
     with determining rules at each denial point
```

### 3.5 Step 5 — Determine Post-Decision Changes

Identify whether anything has changed since the decision that would affect its validity.

```
PROCEDURE:
  1. POLICY CHANGES
     a. Compare pdp_policy_hash from the trace with the CURRENT policy hash
     b. If different → policy has changed since the decision
     c. Retrieve the policy diff (archived policy bundles are versioned)
     d. Determine: would the same request produce a different verdict under current policy?
        (This requires re-evaluation, which is separate from reconstruction)
  
  2. REVOCATIONS
     a. Has the agent been revoked since the decision?
     b. Has any entity in the delegation chain been revoked?
     c. If ALLOW was the verdict and the agent is now revoked, flag as
        ALLOW_FOLLOWED_BY_REVOCATION — potential incident indicator
  
  3. INCIDENT CORRELATION
     a. Query the incident log for incidents involving this agent,
        resource, or time window
     b. If an incident occurred → the decision may be relevant evidence
  
  4. REGULATORY CHANGES
     a. Note any compliance requirement changes since decision time
     b. The decision was valid under the policy at decision time
        regardless of subsequent regulatory changes (non-retroactive principle)
```

---

## 4. IMMUTABLE AUDIT CHAIN REQUIREMENTS

The reconstruction protocol depends on the following immutability properties being satisfied:

| Requirement | Mechanism | Verification |
|---|---|---|
| **IAC-01:** Every decision produces a trace record | Stage 7 is never skipped (EVAL-05). FM-05 emergency buffer catches failures. | DT-01 (Completeness) |
| **IAC-02:** Records cannot be modified after write | 4-layer immutability: hash chain + Merkle + immudb + WORM | DT-03 (Immutability) |
| **IAC-03:** Record ordering is tamper-evident | SHA-256 hash chain with prev_event_hash | DT-04 (Ordering) |
| **IAC-04:** Batch integrity is cryptographically provable | Hourly Merkle trees with HSM-signed Ed25519 root | DT-10 (Non-Repudiation) |
| **IAC-05:** Records survive infrastructure failures | Emergency buffer + flush-on-recovery + 3-tier retention | DT-08 (Survivability) |
| **IAC-06:** Policy bundles are archived with every version | AI-57 + SE-06 (Schema Evolution Rule 6) | Policy bundle archive in BHIV Bucket |
| **IAC-07:** CRL snapshots are archived for correlation | CRL history maintained alongside audit trail | Dependency health logs |
| **IAC-08:** Timestamps are NTP-synchronized | DEP-07 (< 500ms drift, stratum-1) | DT-05 (Temporal Accuracy) |

**If any IAC requirement is violated, reconstruction may be incomplete.** The violation itself is a reportable governance incident.

---

## 5. MINIMUM DATA RETENTION FIELDS

For reconstruction to work at any retention tier, these fields MUST be preserved. Fields not in this list MAY be pruned during tier transitions (hot → warm → cold).

### 5.1 Fields That Must Be Retained at ALL Tiers (Including Cold/WORM)

| Field | Why Required for Reconstruction |
|---|---|
| trace_id | Primary key for record lookup |
| correlation_id | Links request → decision → execution |
| audit_id | BHIV Bucket key; returned to caller |
| request_hash | Proves which request was evaluated |
| agent_id | Identifies the requesting agent (pseudonymized) |
| agent_class | Determines which Canon rules applied |
| action | What was requested |
| resource_type | What resource was targeted |
| resource_id_hash | Which specific resource (hashed) |
| data_classification | What classification was in effect |
| policy_version_hash (request) | What policy the caller expected |
| pdp_policy_hash | What policy the PDP actually used |
| final_verdict | The decision |
| verdict_source | How the verdict was reached |
| determining_rules | Which rules produced the verdict |
| reason_code | Internal reason (full detail) |
| external_reason_code | What the caller was told |
| was_masked | Whether RE-45 was applied |
| stages (all 7) | Complete evaluation path |
| request_received_at | When the request arrived |
| evaluation_completed_at | When the decision was rendered |
| total_duration_us | How long evaluation took |
| token_jti | Links to the issued token (if ALLOW) |
| token_exp | When the token expires |
| delegation_depth | Delegation chain depth |
| delegation_chain_hash | Chain fingerprint |
| prev_event_hash | Hash chain link |
| current_event_hash | This record's hash |
| merkle_batch_id | Batch membership |
| anomaly_flags | Any anomalies detected at decision time |

### 5.2 Fields That May Be Pruned at Warm/Cold Tiers

| Field | Why Prunable |
|---|---|
| pdp_instance_id | Useful for debugging recent decisions; not needed for year-old reconstruction |
| pdp_version | Archived separately in deployment logs |
| source_ip_hash | Privacy: IP data has limited forensic value after 12 months |
| ja3_fingerprint, ja4_fingerprint | TLS fingerprints useful for recent forensics, not long-term |
| session_binding_hash | Session context not reconstructable after session ends |
| pep_type | Infrastructure detail; archived in infrastructure logs |
| circuit_breaker_state | System health detail; archived in monitoring logs |
| crl_staleness_ms | System health detail; archived in monitoring logs |
| state_registry_latency_us | System health detail; archived in monitoring logs |
| evaluation_started_at | Derivable from request_received_at + parse time |
| response_delivered_at | Derivable from evaluation_completed_at + network time |

---

## 6. REDACTION REQUIREMENTS

When trace records are shared with parties outside the Security and Governance teams, the following redaction rules apply:

### 6.1 Redaction Levels

| Level | Audience | What Is Redacted |
|---|---|---|
| **FULL** | Governance auditor (with dual-authorization) | Nothing redacted. Full trace including PII recovery. |
| **INTERNAL** | Security team, Engineering (incident response) | PII remains pseudonymized. All other fields visible. |
| **OPERATIONS** | Operations team | PII pseudonymized + anomaly_flags redacted + internal_notes redacted |
| **EXTERNAL** | External regulator, legal counsel | PII pseudonymized + rule IDs only (no rule names or logic) + anomaly_flags removed + internal_notes removed + stages collapsed to verdict only + network context removed |
| **SUBJECT** | The requesting agent (via correlation_id lookup) | Only: verdict, external_reason_code, audit_id, timestamp. Nothing else. This is the Day 2 response — no additional information. |

### 6.2 Redaction is Non-Reversible in Output

When a trace is exported at a given redaction level, the redacted version is a NEW document. The original is never modified. The redacted export does not contain the redacted fields — they are not replaced with "[REDACTED]" placeholders (which would reveal the existence of the field). They are simply absent from the export.

### 6.3 PII Recovery Procedure

When a FULL-access audit requires de-pseudonymization:

1. Two authorized individuals with `sarathi:governance:trace:full` role must independently authenticate
2. Both submit a PII recovery request specifying the exact trace_id(s)
3. The HSM releases the HMAC-SHA256 salt for the specified records only
4. The pseudonymized fields are reversed to plaintext
5. The recovery event itself is logged as an audit record (who recovered what, when, why)
6. The plaintext PII is delivered to the requestors and is NOT written back to the trace

---

## 7. RECONSTRUCTION OUTPUT FORMAT

When reconstruction is complete, the output is a structured Reconstruction Report:

```
RECONSTRUCTION REPORT
=====================
Report ID:           recon-{UUIDv4}
Requested By:        {investigator identity}
Request Date:        {ISO-8601}
Redaction Level:     {FULL | INTERNAL | OPERATIONS | EXTERNAL | SUBJECT}

TARGET DECISION
  Trace ID:          {trace_id}
  Correlation ID:    {correlation_id}
  Timestamp:         {request_received_at}
  Agent:             {agent_id} (class: {agent_class})
  Action:            {action} on {resource_type}:{resource_id_hash}
  Verdict:           {final_verdict}
  Verdict Source:    {verdict_source}

INTEGRITY VERIFICATION
  Hash Chain:        {VERIFIED | FAILED | PARTIAL}
  Merkle Proof:      {VERIFIED | FAILED | NOT_YET_BATCHED}
  immudb Cross-Check:{VERIFIED | FAILED | UNAVAILABLE}
  Overall Integrity: {VERIFIED | COMPROMISED | PARTIAL}

POLICY CONTEXT
  Policy Hash:       {pdp_policy_hash}
  Policy Match:      {policy_version_match}
  Policy Archived:   {YES — location | NO — gap noted}

EVALUATION PATH
  Stage 1 (Identity):     {PASS | DENY — rules: [...]}
  Stage 2 (Lifecycle):    {PASS | DENY — rules: [...] | SKIPPED}
  Stage 3 (Authority):    {PASS | DENY — rules: [...] | SKIPPED}
  Stage 4 (Eligibility):  {PASS | DENY — rules: [...] | SKIPPED}
  Stage 5 (Risk Gates):   {PASS | DENY — rules: [...] | SKIPPED}
  Stage 6 (Classification):{PASS | DENY — rules: [...] | SKIPPED}
  Stage 7 (Audit Write):  {PASS | ERROR}
  
  Determining Rules:   {rule_id: rule_name, ...}
  Masking Applied:     {YES — RE-45 | NO}
  Internal Reason:     {reason_code}
  External Reason:     {external_reason_code}

POST-DECISION CHANGES
  Policy Changed Since:   {YES — hash_old → hash_new | NO}
  Agent Revoked Since:    {YES — revocation_date | NO}
  Delegation Revoked:     {YES — revocation_date | NO | N/A}
  Related Incidents:      {incident_id list | NONE}

CONCLUSION
  The decision was {VALID | POTENTIALLY_INVALID | REQUIRES_FURTHER_INVESTIGATION}
  under the policy and context that existed at decision time.
  
  {Free-text summary by the investigator}

SIGNED
  Investigator:      {identity}
  Date:              {ISO-8601}
  Report Hash:       SHA-256({this report})
```

---

## 8. RECONSTRUCTION TIMING GUARANTEES

| Scenario | Maximum Time to Reconstruct | Bottleneck |
|---|---|---|
| Decision < 3 months old | < 5 minutes | Elasticsearch query + Merkle proof computation |
| Decision 3-12 months old | < 30 minutes | S3 retrieval + policy bundle archive lookup |
| Decision 1-10 years old | < 8 hours | S3 Object Lock retrieval + cold-tier policy bundle |
| Decision with hash chain break | Indeterminate | Requires FM-16 incident investigation first |
| Decision during BHIV outage | < 30 minutes (if emergency buffer was flushed) | Emergency buffer archive lookup |

---

## 9. RELATIONSHIP TO EXISTING SPECIFICATIONS

| Existing Spec | What This Document Uses | What This Document Does NOT Change |
|---|---|---|
| Decision Trace (Phase A) | Record structure, integrity properties DT-01 through DT-10 | No trace field changes |
| Drift Detection (Phase B) | Anomaly context for incident correlation | No metric changes |
| Day 2 — Response Schema | audit_id, correlation_id, external response contract | No response changes |
| Day 3 — Evaluation Order | Stage definitions for evaluation path reconstruction | No evaluation changes |
| Day 4 — Failure Modes | FM-05 (audit failure), FM-16 (hash chain break) | No failure mode changes |
| Lock v1.1 | G-05 (Mandatory Audit), IAC requirements, go-live items | No lock changes |
| PDP Interface | Audit event schema, 4-layer immutability, PII handling, retention tiers | No interface changes |

---

**END OF AUDIT RECONSTRUCTION PROTOCOL**

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Reconstruction Entry Points | 7 |
| Reconstruction Steps | 5 (Retrieve → Verify → Context → Rules → Changes) |
| Immutable Audit Chain Requirements | 8 (IAC-01 through IAC-08) |
| Minimum Retention Fields | 30 (must survive to cold tier) |
| Prunable Fields | 11 (may be removed at warm/cold) |
| Redaction Levels | 5 (FULL, INTERNAL, OPERATIONS, EXTERNAL, SUBJECT) |
| Reconstruction Timing SLAs | 5 scenarios defined |
| Report Output Fields | 12 sections |
| Existing Specs Modified | 0 |

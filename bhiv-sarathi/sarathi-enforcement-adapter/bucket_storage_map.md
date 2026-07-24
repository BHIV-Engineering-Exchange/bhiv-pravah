# PHASE 7: Bucket Integration — Bucket Storage Map

**Document ID:** SARATHI-PHASE7-BUCKET-STORAGE
**Version:** 9.3.1
**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Bucket Integration
**Classification:** Internal Sovereign Design / Strictly Confidential
**Generated:** 2026-04-04

---

## 1. Purpose

Define how Bucket (BHIV audit storage system) persists governance data from Sarathi.
Bucket is an **append-only, immutable archive** — it stores audit records but cannot
modify governance decisions or trigger execution.

---

## 2. Integration Specification

| Property | Value |
|---|---|
| **System ID** | `bucket` |
| **Receives From** | `sarathi-gated-bridge` |
| **Delivery Mode** | Sync (blocking — audit must succeed before response) |
| **Schema ID** | `bhiv.bucket.audit.archive.event.v1` |
| **Immutable** | `true` — records cannot be modified or deleted |

---

## 3. Storage Types

| Storage Type | Description | Retention |
|---|---|---|
| `audit_logs` | Full enforcement decision records | 90 days (configurable) |
| `enforcement_chains` | Hash chain entries with trace hashes | Permanent |
| `execution_chains` | Execution engine chain entries | Permanent |
| `decision_traces` | PDP evaluation traces with rule matching | 90 days |
| `key_events` | Key rotation, generation, loading events | Permanent |
| `system_events` | Service start/stop, config changes | 90 days |
| `bridge_logs` | Bridge authentication, rate limiting, bypass attempts | 30 days |
| `ksml_governance_decisions` | Full KSMLGovernanceDecision records with intent metadata | 90 days |
| `ksml_intent_history` | Per-agent KSML intent decision history | 90 days |
| `ksml_delegation_chains` | DELEGATION_INTENT parent→child chain records | Permanent |
| `ksml_revocation_log` | Revoked intent IDs with timestamps and agent context | Permanent |
| `ksml_escalation_archive` | ESCALATION_INTENT records with human-review outcomes | Permanent |
| `token_registry_state` | Persistent token consumption records (crash recovery) | 24 hours |
| `passport_rotation_logs` | HMAC secret rotation events with rotation count | Permanent |
| `policy_validation_results` | ValidateForActivation conflict detection results | 90 days |
| `production_startup_checks` | ValidateForProduction results per startup | 30 days |

---

## 4. Storage Schema

### 4.1 Audit Record

```json
{
  "record_id": "uuid",
  "timestamp": "2026-03-30T12:00:00.000000Z",
  "correlation_id": "uuid",
  "agent_id": "string",
  "resource_id": "string",
  "action": "string",
  "verdict": "ALLOW | DENY | ESCALATE",
  "enforcement_hash": "sha256",
  "request_hash": "sha256",
  "policy_version": "string",
  "policy_hash": "sha256",
  "caller_system": "string",
  "executed": true,
  "block_reason": "string (if DENY)",
  "latency_ns": 12345,
  "service_version": "8.0.0",
  "registry_version": 1
}
```

### 4.2 Chain Entry

```json
{
  "sequence_number": 1,
  "correlation_id": "uuid",
  "verdict": "ALLOW",
  "enforcement_stage": "PDP_EVALUATED",
  "enforcement_hash": "sha256",
  "prev_enforcement_hash": "sha256 | GENESIS",
  "trace_hash": "sha256",
  "registry_version": 1,
  "chain_type": "enforcement | execution"
}
```

---

## 5. Immutability Guarantees

| Property | Mechanism |
|---|---|
| **Append-only** | Records are INSERT only — no UPDATE or DELETE |
| **Hash linkage** | Each chain entry references previous hash (tamper detection) |
| **Integrity verification** | `VerifyChain()` recomputes all hashes and validates linkage |
| **Audit protection** | NIST AU-9 compliant — audit records are protected from modification |

---

## 6. Routing Flow

```
  GatedBridge.RouteExecution()
       │
       ├── Step 4: SaarthiService.ProcessRequest()
       │       │
       │       └── auditSink.RecordEnforcement(req, resp)  ← sync write
       │
       ├── Step 4.5: mandatoryAudit.RecordEnforcementMandatory(req, resp)  ← v7.0
       │
       └── Step 5: MultiSystemRouter.RouteResult(req, resp)
                │
                └── Bucket: receives routed result for archival
```

---

## 7. Access Control

| Permission | Granted | Rationale |
|---|---|---|
| `read` | YES | Can query archived records |
| `write` | YES | Can receive and store new records |
| `execute` | NO | Cannot trigger execution |
| `delete` | NO | Immutable archive — no deletion |

---

## 8. v9.3.1 Note

All Phase 1-10 components are ACTIVE. Bucket continues to maintain append-only immutable archives with no operational changes.

---

## 9. v7.0.2 Additions

| Feature | What Bucket Stores |
|---|---|
| **Mandatory audit records** | All enforcement decisions with circuit breaker state |
| **Revocation events** | Token revocations and agent cascade events |
| **Posture changes** | Agent trust score history |
| **Key rotation events** | When token authority keys are rotated |
| **Escalation outcomes** | Webhook notification results |
| **KSML governance decisions** | Full KSMLGovernanceDecision: IntentID, IntentType, KSMLVerb, GovernanceAction, Status, Verdict, EnforcementHash, BlockReason, ExecutionState, ProcessedAt, LatencyNs |
| **KSML delegation chains** | Complete parent→child delegation trees for audit compliance |
| **KSML revocation log** | Permanent record of all revoked intent IDs (non-deletable) |
| **KSML escalation archive** | Every ESCALATION_INTENT that required human review — permanent retention |
| **KSML agent history** | Per-agent intent decision timeline for forensic analysis |

### KSML Decision Storage Schema (v7.0.2)

```json
{
  "record_type": "ksml_governance_decision",
  "record_id": "uuid",
  "timestamp": "2026-03-31T12:00:00.000000Z",
  "intent_id": "string",
  "intent_type": "QUERY_INTENT | EXECUTION_INTENT | DELEGATION_INTENT | ESCALATION_INTENT | SPECIFICATION_INTENT",
  "ksml_verb": "string (e.g. query, invoke, delegate)",
  "governance_action": "read | write | execute | delegate",
  "status": "ALLOWED | DENIED | ESCALATED | REVOKED | EXPIRED",
  "verdict": "ALLOW | DENY | ESCALATE",
  "agent_id": "string",
  "target_agent_id": "string (DELEGATION_INTENT only)",
  "resource_id": "string",
  "block_reason": "string (if denied/escalated)",
  "enforcement_hash": "sha256",
  "execution_state": "EXECUTION_PERMITTED | EXECUTION_BLOCKED",
  "processed_at": "2026-03-31T12:00:00Z",
  "latency_ns": 12345,
  "delegation_id": "parent intent ID (DELEGATION_INTENT only)",
  "requires_human": false
}
```

---

## 10. Storage Immutability for KSML Records

KSML records follow the same immutability guarantees as enforcement records:

| Property | Mechanism |
|---|---|
| **KSML decisions — append-only** | INSERT only — no UPDATE or DELETE on ksml_governance_decisions |
| **KSML revocations — permanent** | revocation_log is permanent retention — cannot be removed |
| **KSML escalations — permanent** | escalation_archive is permanent — full audit trail for human reviews |
| **Delegation chains — permanent** | delegation chain entries can never be deleted |
| **Intent history — hash-linked** | Per-agent history references enforcement_hash for tamper detection |

---

**Integration Block:**
- Ishan Shirode — Evaluator, Raj Prajapati — Enforcement Engine, Future Integration Engineer — Core Integration

**Bucket is a SAFE, append-only archive. It cannot bypass governance. In v9.3.1, it stores full KSML governance decisions, delegation chains, revocation logs, and escalation archives — all with permanent retention for compliance.**

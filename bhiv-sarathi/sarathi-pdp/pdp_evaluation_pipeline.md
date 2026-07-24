# PDP EVALUATION PIPELINE

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Decision Point
**Version:** 1.0.0
**Policy Hash:** `cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1`

---

## 1. PIPELINE INVARIANT

The evaluation order is fixed and NEVER changes. Every request passes through exactly 5 stages in this exact sequence. No stage may execute out of order. No stage may be skipped except when a prior stage produces DENY (short-circuit).

```
REQUEST INPUT
     │
     ▼
┌─────────────────────┐
│ Stage 1              │
│ REQUEST VALIDATION   │──── DENY → Stage 5 (trace + return)
└─────────┬───────────┘
          │ PASS
          ▼
┌─────────────────────┐
│ Stage 2              │
│ REGISTRY LOOKUP      │──── DENY → Stage 5 (trace + return)
└─────────┬───────────┘
          │ PASS
          ▼
┌─────────────────────┐
│ Stage 3              │
│ POLICY EVALUATION    │
└─────────┬───────────┘
          │ matching rules
          ▼
┌─────────────────────┐
│ Stage 4              │
│ AUTHORITY DECISION   │──── deny-overrides + BLP classification
└─────────┬───────────┘
          │ ALLOW or DENY
          ▼
┌─────────────────────┐
│ Stage 5              │
│ DECISION TRACE       │──── hash-chained, immutable
└─────────┬───────────┘
          │
          ▼
     RESPONSE OUTPUT
```

---

## 2. STAGE DEFINITIONS

### Stage 1 — Request Validation

Validates that the incoming request contains all required fields with valid values.

| Check | Failure Verdict | Reason Code |
|---|---|---|
| `agent_id` is non-empty string | DENY | `INVALID_AGENT_ID` |
| `resource_id` is non-empty string | DENY | `INVALID_RESOURCE_ID` |
| `action` is one of: read, write, delete, execute | DENY | `INVALID_ACTION` |

If any check fails, the pipeline short-circuits to Stage 5 (decision trace emission) and returns DENY immediately. Subsequent stages do not execute.

### Stage 2 — Registry Lookup

Resolves the agent and resource from canonical registries.

| Check | Failure Verdict | Reason Code |
|---|---|---|
| Agent exists in Agent Registry | DENY | `AGENT_NOT_FOUND` |
| Agent status is ACTIVE | DENY | `AGENT_{status}` (e.g., `AGENT_SUSPENDED`) |
| Resource exists in Resource Registry | DENY | `RESOURCE_NOT_FOUND` |

On failure, short-circuits to Stage 5. On success, produces: `AgentInfo` (role, clearance, status) and `ResourceInfo` (type, classification).

### Stage 3 — Policy Evaluation

Loads the frozen Authority Matrix and finds all rules matching the request.

Matching criteria (all must be true):
1. `rule.agent_role == agent.agent_role` OR `rule.agent_role == "*"`
2. `rule.resource_type == resource.resource_type` OR `rule.resource_type == "*"`
3. `rule.action == request.action` OR `rule.action == "*"`

Rules are evaluated in deterministic order (sorted by `rule_id`). The output is the set of all matching rules.

### Stage 4 — Authority Decision

Applies the deny-overrides combining algorithm and truth classification enforcement.

**Step 4.1 — Specificity separation:** Separate specific rules (no wildcards) from wildcard rules. If specific rules exist, evaluate only those. Wildcards serve as defaults.

**Step 4.2 — Deny-overrides:** Among the rules being evaluated, if ANY has `verdict == "DENY"`, the final verdict is DENY. No exceptions. This is the XACML deny-overrides algorithm and the Cedar forbid-trumps-permit property.

**Step 4.3 — Bell-LaPadula classification enforcement:** If the verdict would be ALLOW, verify:
- `agent.clearance_level >= resource.classification_level` (simple security property / "no read up")
- `rule.classification_max >= resource.classification_level` (rule ceiling check)

If either check fails, the verdict is overridden to DENY with reason `CLASSIFICATION_CEILING_EXCEEDED`.

**Step 4.4 — Default deny:** If no rules match at all, the verdict is DENY with `AUTH-DENY-ALL`.

### Stage 5 — Decision Trace Emission

Every verdict — ALLOW or DENY — produces an immutable, hash-chained decision trace.

The trace includes:
- `decision_id` — deterministic UUID derived from request content + policy hash
- `policy_hash` — SHA-256 of the policy rules that produced this decision
- `policy_version` — semantic version of the Authority Matrix
- `request_hash` — SHA-256 of the canonical request JSON
- `verdict` — ALLOW or DENY
- `determining_rules` — list of rule IDs that determined the verdict
- `truth_classification` — the resource's truth level
- `reason` — machine-readable reason code
- `timestamp` — ISO-8601 UTC
- `prev_trace_hash` — SHA-256 of the previous trace (hash chain)
- `trace_hash` — SHA-256 of this trace

Stage 5 ALWAYS executes. It cannot be skipped. An untraced decision is an ungoverned decision.

---

## 3. EXECUTION RESULTS

Executed 2026-03-07 against Authority Matrix v1 (51 rules, 7 agent roles, 9 resource types).

| Category | Count | Examples |
|---|---|---|
| ALLOW — specific rule match + classification pass | 24 | Governance reads policy registry (AUTH-001), Standard reads operational data (AUTH-007) |
| DENY — explicit deny rule | 15 | Standard denied policy registry (AUTH-003), Audit denied trace write (AUTH-006) |
| DENY — agent lifecycle (not found, suspended, revoked) | 4 | Agent not found, Suspended agent, Revoked agent |
| DENY — invalid request | 2 | Invalid action (delete), Empty agent ID |
| DENY — Resouce not found | 1 | Resource not found |
| DENY — default deny (wildcard catch-all) | 1 | (All requests matched specific rules) |
| **Total** | **47** | 24 ALLOW + 23 DENY |

**Replay test:** 30/30 identical verdicts across two independent PDP instances. Mismatch rate: 0.0000%. Determinism PROVEN.

---

## 4. NON-NEGOTIABLE PROPERTIES

| Property | Enforcement |
|---|---|
| **Determinism** | Same request + same policy = same verdict. UUIDv5 for decision_id, canonical JSON for hashing, sorted rules for evaluation. |
| **Fail-closed** | Any exception at any stage produces DENY. Default verdict is DENY before evaluation begins. |
| **Deny-overrides** | DENY always wins. No permit can override a deny at equal specificity. |
| **Classification ceiling** | Bell-LaPadula simple security property enforced after rule matching. Constitutional constraint — inviolable. |
| **Immutable trace** | Hash-chained decision traces. Each trace links to the previous via SHA-256. |
| **No heuristics** | Zero ML, zero scoring, zero probability. Pure function of (role, resource, action, policy). |
| **No policy mutation** | Authority Matrix is frozen at load time. Runtime modification is structurally impossible (immutable data structures). |

---

**END OF PDP EVALUATION PIPELINE**

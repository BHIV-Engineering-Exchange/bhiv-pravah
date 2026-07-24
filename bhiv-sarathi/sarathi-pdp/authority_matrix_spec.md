# AUTHORITY MATRIX v1 SPECIFICATION

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Decision Point
**Host:** Blackhole Infiverse (BHIV)
**Version:** 1.0.0
**Frozen:** 2026-03-07
**Policy Hash:** `cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1`

---

## 1. PURPOSE

The Authority Matrix is Sarathi's constitutional law. It contains every explicit authority rule the PDP evaluates. No authority decision exists outside this matrix. No heuristic, scoring model, or adaptive system can override it.

---

## 2. RULE FORMAT

Every rule in `authority_matrix_v1.json` contains exactly these required fields:

| Field | Type | Description |
|---|---|---|
| `rule_id` | string | Unique identifier (e.g., "AUTH-001"). Sorted lexicographically for deterministic evaluation. |
| `agent_role` | string | The role of the requesting agent. Must match exactly. Wildcard `*` matches any role (used only in default deny). |
| `resource_type` | string | The type of resource being accessed. Must match exactly. Wildcard `*` matches any resource. |
| `action` | string | The action being requested (read, write, delete, execute). Must match exactly. Wildcard `*` matches any action. |
| `classification_max` | string | The maximum truth classification level this rule permits. Agent clearance must be >= resource classification AND <= this ceiling. Values: L0, L1, L2, L3, L4. |
| `verdict` | string | Exactly "ALLOW" or "DENY". No other values. No probabilistic outcomes. |

Optional fields:

| Field | Type | Description |
|---|---|---|
| `description` | string | Human-readable explanation of the rule's purpose |
| `conditions` | object | Additional match conditions (reserved for v1.1) |
| `time_window` | object | Temporal restriction (reserved for v1.1) |
| `delegation_allowed` | boolean | Whether this authority can be delegated (reserved for v1.1) |

---

## 3. EVALUATION SEMANTICS

### 3.1 Rule Matching

A rule matches a request when ALL of the following are true:
1. `rule.agent_role == request.agent_role` OR `rule.agent_role == "*"`
2. `rule.resource_type == request.resource_type` OR `rule.resource_type == "*"`
3. `rule.action == request.action` OR `rule.action == "*"`

### 3.2 Deny-Overrides Combining

When multiple rules match a request, the combining algorithm is fixed:

1. Collect all matching rules
2. If ANY matching rule has `verdict == "DENY"` → final verdict is **DENY**
3. If no DENY rules match but at least one `verdict == "ALLOW"` matches → check classification ceiling
4. If no rules match at all → final verdict is **DENY** (default deny via AUTH-DENY-ALL)

This is the XACML deny-overrides algorithm and the Cedar forbid-trumps-permit property. It is non-configurable.

### 3.3 Truth Classification Enforcement

After rule matching, the PDP enforces the Bell-LaPadula simple security property:

```
IF resource.classification_level > agent.classification_max THEN
    verdict = DENY
    reason = "CLASSIFICATION_CEILING_EXCEEDED"
```

This check occurs AFTER rule matching. Even if a rule says ALLOW, the classification ceiling is an absolute constitutional constraint. Classification levels are ordered: L0 < L1 < L2 < L3 < L4. An agent with `classification_max = L2` can NEVER access an L3 or L4 resource, regardless of what any rule says.

### 3.4 Determinism Guarantee

Given the same `(agent_role, resource_type, action, classification_max)` tuple and the same `policy_version`, the PDP always returns the same verdict. This is guaranteed by:
- Rules are sorted by `rule_id` for deterministic iteration
- Deny-overrides is order-independent (any DENY wins)
- No randomness, no scoring, no heuristics
- No external I/O during evaluation

---

## 4. VERSIONING RULES

| Property | Value |
|---|---|
| Current version | 1.0.0 |
| Version format | Semantic versioning (MAJOR.MINOR.PATCH) |
| Hash algorithm | SHA-256 over canonical JSON of rules array |
| Hash computation | `SHA-256(json.dumps(rules, sort_keys=True, separators=(',',':')))` |
| Immutability | Once frozen, a version is NEVER modified. Changes create a new version. |
| Policy store | Content-addressed by policy_hash. Two versions with the same rules produce the same hash. |

### 4.1 Version Increment Rules

- PATCH (1.0.x): Rule description changes only. No behavioral change.
- MINOR (1.x.0): New rules added. No existing rules modified or removed.
- MAJOR (x.0.0): Existing rules modified or removed. Behavioral change.

Every version increment produces a new `policy_hash`. The PDP refuses to evaluate if the loaded `policy_hash` does not match the expected value.

---

## 5. TRUTH CLASSIFICATION LEVELS

| Level | Rank | Label | Examples |
|---|---|---|---|
| L0 | 0 | Public information | Public API schemas, documentation |
| L1 | 1 | Internal operational data | Operational metrics, analytics, logs |
| L2 | 2 | Sensitive internal data | Configuration, internal APIs, user data |
| L3 | 3 | Governance-critical data | Agent registry, model registry, decision traces, audit logs |
| L4 | 4 | Constitutional truth layer | Policy registry, authority matrix, governance rules |

### 5.1 Resource-to-Classification Mapping

| Resource Type | Classification |
|---|---|
| `policy_registry` | L4 |
| `agent_registry` | L3 |
| `decision_trace` | L3 |
| `model_registry` | L3 |
| `audit_log` | L3 |
| `configuration` | L2 |
| `operational_data` | L1 |
| `analytics` | L1 |
| `public_api` | L0 |

This mapping is embedded in the Authority Matrix and enforced by the PDP. It is not configurable at runtime.

---

## 6. AUTHORITY MATRIX v1 — RULE INVENTORY

51 rules total. 7 agent roles. 9 resource types. 2 actions.

| Rules by Verdict | Count |
|---|---|
| ALLOW | 24 |
| DENY | 22 |
| Default DENY (catch-all) | 1 |
| **Total** | **47** |

| Rules by Agent Role | Count |
|---|---|
| governance_agent | 11 |
| standard_agent | 15 |
| audit_agent | 8 |
| safety_monitor | 6 |
| data_processor | 7 |
| orchestrator | 3 |
| * (default deny) | 1 |
| **Total** | **51** (7 distinct roles including wildcard) |

---

**END OF AUTHORITY MATRIX SPECIFICATION**

# DECISION OUTPUT SCHEMA

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Decision Point
**Version:** 1.0.0

---

## 1. PURPOSE

Every Sarathi PDP decision emits a structured response. This schema defines every field, its type, its invariants, and its relationship to the governance audit trail. No field is optional. No field can be empty. Every decision is deterministic, policy-anchored, and registry-referenced.

---

## 2. RESPONSE SCHEMA

```json
{
  "decision_id":          "string — UUIDv5 deterministic from request_hash + policy_hash",
  "verdict":              "string — exactly ALLOW or DENY. No other values.",
  "policy_version":       "string — semantic version of the Authority Matrix (e.g., 1.0.0)",
  "policy_hash":          "string — SHA-256 of canonical rules JSON",
  "determining_rules":    ["string — list of rule IDs that determined the verdict"],
  "truth_classification": "string — resource's truth level (L0-L4)",
  "request_hash":         "string — SHA-256 of canonical request JSON",
  "timestamp":            "string — ISO-8601 UTC with microsecond precision",
  "reason":               "string — machine-readable reason code",
  "agent_role":           "string — resolved agent role from registry",
  "resource_type":        "string — resolved resource type from registry",
  "stage_reached":        "integer — last pipeline stage that executed (1-5)"
}
```

---

## 3. FIELD SPECIFICATIONS

### 3.1 decision_id

UUIDv5 derived deterministically from `SHA-256(request_hash + policy_hash)`. Same request with same policy always produces the same decision_id. This enables deduplication and replay correlation.

Aligns with: Day 2 Response Schema OUT-02 (Determinism).

### 3.2 verdict

Exactly one of: `"ALLOW"` or `"DENY"`. No third value for this PDP version. No INDETERMINATE, no PENDING, no NOT_APPLICABLE. If evaluation cannot complete, verdict is DENY (fail-closed).

Aligns with: Day 2 OUT-03 (Completeness), OUT-09 (Three-Valued — ESCALATE reserved for future mutual-conflict resolution per RES-13).

### 3.3 policy_version

Semantic version string (MAJOR.MINOR.PATCH) of the loaded Authority Matrix. Every decision is anchored to a specific policy version. This field is NEVER empty.

Aligns with: Task requirement "Every decision must be tied to policy_version."

### 3.4 policy_hash

SHA-256 hex digest of the canonical JSON of the rules array (6 required fields only: rule_id, agent_role, resource_type, action, classification_max, verdict). Computed from a **lexically sorted slice of rules** at policy load time to guarantee structural determinism regardless of the underlying JSON file ordering. Verified against stored hash to detect tampering.

Aligns with: Task requirement "Every decision must be tied to policy_hash."

### 3.5 determining_rules

Sorted list of rule IDs that determined the verdict. For ALLOW: the rule(s) that explicitly permitted the action. For DENY: the rule(s) that explicitly denied, or `["AUTH-DENY-ALL"]` for default deny. Sorted lexicographically for deterministic output.

Aligns with: Day 2 response requirement "determining_rules must list exact rule IDs."

### 3.6 truth_classification

The truth classification level of the accessed resource (L0 through L4). Set to "UNKNOWN" if the resource was not resolved (Stage 2 failure).

Aligns with: Task truth classification levels, Bell-LaPadula enforcement.

### 3.7 request_hash

SHA-256 hex digest of the canonical JSON of the request (agent_id, resource_id, action). Stable across runs — same request always produces the same hash.

Aligns with: Task requirement "request_hash must be stable."

### 3.8 timestamp

ISO-8601 UTC with microsecond precision. Records when the PDP rendered the verdict. 
**Determinism Guarantee:** Time is provided by an injected `Clock` interface (`RealClock` in production, `DeterministicClock` in replay testing) to ensure absolute timestamp stability during replay verification. Used for audit sequencing and TTL calculation.

### 3.9 reason

Machine-readable reason code. Values:

| Reason Code | Meaning | Stage |
|---|---|---|
| `EXPLICIT_ALLOW` | A specific ALLOW rule matched and classification checks passed | 4 |
| `EXPLICIT_DENY` | A specific DENY rule matched | 4 |
| `CLASSIFICATION_CEILING_EXCEEDED` | Agent clearance below resource classification (Bell-LaPadula) | 4 |
| `RULE_CLASSIFICATION_CEILING_EXCEEDED` | Rule's classification_max below resource classification | 4 |
| `NO_MATCHING_RULE` | No rule matched the request | 4 |
| `NO_ALLOW_RULE` | Rules matched but none were ALLOW | 4 |
| `INVALID_AGENT_ID` | Empty or invalid agent_id | 1 |
| `INVALID_RESOURCE_ID` | Empty or invalid resource_id | 1 |
| `INVALID_ACTION` | Action not in {read, write, delete, execute} | 1 |
| `AGENT_NOT_FOUND` | Agent not in registry | 2 |
| `AGENT_SUSPENDED` | Agent exists but status is SUSPENDED | 2 |
| `AGENT_REVOKED` | Agent exists but status is REVOKED | 2 |
| `RESOURCE_NOT_FOUND` | Resource not in registry | 2 |
| `INTERNAL_FAULT:{type}` | Unhandled exception (fail-closed) | Any |

---

## 4. INVARIANTS

| ID | Invariant | Enforcement |
|---|---|---|
| **DO-01** | Every response contains a verdict. No response without verdict. | PDPResponse constructor requires verdict. Default is DENY. |
| **DO-02** | decision_id is deterministic. Same request + same policy = same decision_id. | UUIDv5 from request_hash + policy_hash. |
| **DO-03** | policy_hash matches the loaded Authority Matrix. | PolicyStore verifies at load time. |
| **DO-04** | determining_rules lists the actual rules that decided. Not empty for evaluated decisions. | Stage 4 populates from matching rules. |
| **DO-05** | request_hash is stable. Same request always produces same hash. | SHA-256 of RFC 8785 canonical JSON. |
| **DO-06** | No response contains debugging information, stack traces, or internal state. | Response schema has fixed fields. No extensibility. |

---

## 5. EXAMPLE OUTPUT

### ALLOW Decision
```json
{
  "decision_id": "344ef3ec-ebc0-55d8-b4ac-5ac6293f10a9",
  "verdict": "ALLOW",
  "policy_version": "1.0.0",
  "policy_hash": "cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1",
  "determining_rules": ["AUTH-001"],
  "truth_classification": "L4",
  "request_hash": "53d5aa78850826638155c89499b8109a0ce6877ce50d5e4b74f91bcdff031539",
  "timestamp": "2026-03-07T03:45:13.547208Z",
  "reason": "EXPLICIT_ALLOW",
  "agent_role": "governance_agent",
  "resource_type": "policy_registry",
  "stage_reached": 5
}
```

### DENY Decision
```json
{
  "decision_id": "a1b2c3d4-...",
  "verdict": "DENY",
  "policy_version": "1.0.0",
  "policy_hash": "cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1",
  "determining_rules": ["AUTH-003"],
  "truth_classification": "L4",
  "request_hash": "...",
  "timestamp": "2026-03-07T03:45:13.545000Z",
  "reason": "EXPLICIT_DENY",
  "agent_role": "standard_agent",
  "resource_type": "policy_registry",
  "stage_reached": 5
}
```

---

**END OF DECISION OUTPUT SCHEMA**

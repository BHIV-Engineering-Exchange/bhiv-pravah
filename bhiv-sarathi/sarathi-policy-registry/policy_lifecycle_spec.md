# Policy Lifecycle Specification

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Lifecycle Management
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026

---

## 1. Overview

Every policy version in the Sarathi Policy Registry exists in exactly one lifecycle state at any time. The lifecycle enforces that policies progress through a disciplined pipeline from creation to retirement, with cryptographic guarantees at each transition.

This specification defines the four lifecycle states, their transition rules, and the governance invariants that prevent silent policy mutation.

---

## 2. Lifecycle States

### 2.1 DRAFT

A policy in DRAFT state is under construction. Its rules may be incomplete, its hash field is empty, and it must not be used for any governance evaluation.

**Properties:**
- `policy_hash` field is empty string (`""`)
- Rules may be added, modified, or removed
- Cannot be loaded into the Policy Registry
- Cannot be set as active policy
- Cannot be used by PDP or replay harness

**Purpose:** Allow policy authors to iterate on rule design without affecting the live system.

### 2.2 FROZEN

A policy in FROZEN state has been cryptographically sealed. Its hash has been computed from the canonical rules representation and written into the policy file. From this point forward, the rules are immutable.

**Properties:**
- `policy_hash` field contains valid SHA-256 hash
- Rules cannot be modified (hash verification will detect any change)
- Can be loaded into the Policy Registry
- Can be set as active policy
- Can be used by PDP and replay harness

**Transition from DRAFT:**
1. Author finalizes rules
2. System computes `policy_hash` = SHA-256 of canonical rules JSON
3. Hash is written into the policy file
4. Policy state becomes FROZEN
5. File is committed to version control

**Irreversibility:** Once frozen, a policy cannot return to DRAFT. If changes are needed, create a new policy version.

### 2.3 ACTIVE

A policy in ACTIVE state is the currently designated policy for live governance evaluations. Only one policy version can be ACTIVE at any time across the entire registry.

**Properties:**
- All FROZEN properties apply
- Designated as the active policy in the Policy Registry
- Used by PDP for all live evaluations
- All new decision traces reference this policy's version and hash

**Transition from FROZEN:**
1. Policy must be loaded and hash-verified in the registry
2. `SetActivePolicy(version)` is called
3. Previous active policy (if any) transitions to FROZEN (it remains loaded and available for replay)
4. New policy becomes ACTIVE

**Constraint:** Activating a policy does not delete or unload previous versions. All historical versions remain available for replay verification.

### 2.4 DEPRECATED

A policy in DEPRECATED state was previously ACTIVE but has been superseded by a newer version. It remains loaded in the registry for replay verification but is not used for new evaluations.

**Properties:**
- All FROZEN properties apply
- Not used for new evaluations
- Available for replay tests that reference its version
- Will be retained in the registry as long as decision traces reference it

**Transition from ACTIVE:**
- Automatic when a different policy version is set as ACTIVE
- The previously ACTIVE policy becomes DEPRECATED

**Note:** DEPRECATED does not mean deleted. Governance audit requires that every historical policy version referenced in the decision trace remains accessible. Deprecation is a status indicator, not a removal operation.

---

## 3. State Transition Diagram

```
+----------+     Compute Hash     +----------+
|  DRAFT   | ------------------> |  FROZEN  |
+----------+                      +----+-----+
                                       |
                                       | SetActivePolicy()
                                       v
                                  +----+-----+
                                  |  ACTIVE  |  <-- Only ONE at a time
                                  +----+-----+
                                       |
                                       | New version activated
                                       v
                                  +----+-------+
                                  | DEPRECATED |
                                  +------------+
```

---

## 4. Illegal Transitions

| Transition | Why Illegal |
|------------|-------------|
| FROZEN → DRAFT | Unfreezing a policy enables silent mutation. If a frozen policy could return to draft, the hash guarantee is meaningless. |
| ACTIVE → DRAFT | An active policy is in use for live decisions. Returning it to draft would mean live decisions use an unverified policy. |
| DEPRECATED → DRAFT | A deprecated policy has historical decision traces referencing it. Modifying it would invalidate those traces. |
| DEPRECATED → ACTIVE | Reactivating a deprecated policy is handled by creating a new version with the same rules and a new version identifier. This ensures the decision trace clearly distinguishes between the original activation period and the reactivation period. |
| Any → Deleted | Policy versions are never deleted from the registry. Deletion would break replay verification for any decision trace that references the deleted version. |

---

## 5. Policy File Naming Convention

Policy files are stored in the `/policies/` directory with the naming pattern:

```
/policies/policy_{version}.json
```

Where `{version}` is a semantic version string (e.g., `v1`, `v2`, `v1.1`).

Examples:
```
/policies/policy_v1.json    ← Original authority matrix
/policies/policy_v2.json    ← First policy upgrade
```

---

## 6. Policy Version Metadata

Each policy file includes metadata that establishes its identity and provenance:

```json
{
  "policy_version": "2.0.0",
  "policy_hash": "sha256hex...",
  "frozen_at": "2026-03-13T00:00:00Z",
  "schema_version": "authority_matrix_v1",
  "parent_version": "1.0.0",
  "change_summary": "Modified AUTH-038 verdict from DENY to ALLOW for standard_agent model_registry read. Modified AUTH-046 classification_max from L1 to L2 for data_processor configuration read.",
  "rules": [...]
}
```

The `parent_version` field establishes lineage — which policy this version evolved from. The `change_summary` field documents what changed and why, for audit purposes.

---

## 7. Governance Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| PL-01 | A policy in DRAFT state must never be loaded into the registry | LoadPolicy() rejects files with empty policy_hash |
| PL-02 | A policy in FROZEN state must pass hash verification before loading | LoadPolicy() recomputes hash and compares |
| PL-03 | Only one policy version may be ACTIVE at any time | SetActivePolicy() transitions previous active to DEPRECATED |
| PL-04 | Policy versions are never deleted | No delete operation exists in the registry interface |
| PL-05 | Every decision trace must reference the exact policy_version and policy_hash used | PDP includes both fields in every PDPResponse |
| PL-06 | Replay tests must be able to load any historical policy version | GetPolicy(version) returns any loaded version |
| PL-07 | Policy version identifiers must be unique | LoadPolicy() rejects duplicate version strings |

---

**END OF DOCUMENT**

# Policy Registry Architecture

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Registry Layer
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026

---

## 1. Purpose

The Policy Registry introduces versioned, immutable policy management to the Sarathi PDP engine. It replaces the current single-file policy loading pattern (`authority_matrix_v1.json` loaded directly into `PolicyStore`) with a registry layer that manages multiple policy versions, enforces immutability guarantees, and enables replay tests against historical policy states.

This is not a new capability. It is governance infrastructure that prevents silent rule changes — the single most common cause of governance system failure in production.

---

## 2. Why Governance Policies Must Be Versioned

Governance systems fail when rules change silently. A single-file policy model creates three fatal problems.

**Problem 1: Silent Mutation.** If the authority matrix file is edited in place, there is no record of what the rules were yesterday. A developer who changes a classification ceiling from L2 to L3 "just for testing" and forgets to revert it has silently expanded access for every agent in that role. The system continues to produce decisions, but those decisions are no longer governed by the original rules. Nobody notices until an audit reconstructs the decision trail and finds verdicts that cannot be explained by the current policy. By then, the original policy is lost.

**Problem 2: Replay Brittleness.** Deterministic replay requires that the exact policy version used during the original evaluation is available for re-evaluation. If the policy file is modified between the original decision and the replay attempt, the replay produces different verdicts — not because the system drifted, but because the reference policy changed. This makes replay verification meaningless. You cannot prove determinism if you cannot control the inputs.

**Problem 3: Upgrade Risk.** When policies evolve (new agent roles, modified classification ceilings, additional deny rules), there must be a clear boundary between "decisions made under old rules" and "decisions made under new rules." Without versioning, this boundary does not exist. A decision logged at 14:00 might have been evaluated under the old rules or the new rules depending on when the file was swapped. This ambiguity destroys audit integrity.

---

## 3. Why Policy Mutation Must Be Impossible

The Policy Registry enforces a stronger guarantee than "policies should not change." It enforces that **policies cannot change once frozen.**

Every policy version loaded into the registry is hash-verified against its declared `policy_hash`. If the file contents do not match the hash, the registry refuses to load it. This is not a warning — it is a fatal error that halts initialization.

This guarantee is cryptographic, not procedural. It does not depend on developer discipline or code review. The SHA-256 hash is computed from the canonical JSON representation of the rules (sorted by rule_id, 6 fields per rule). Any modification — adding a rule, changing a verdict, adjusting a classification ceiling — produces a different hash. The registry detects it and refuses to operate.

**Invariant: Once a policy version is frozen (hash set), it is immutable for the lifetime of the system.**

---

## 4. How Replay Depends on Policy Version History

The Sarathi PDP produces decisions that include `policy_version` and `policy_hash` in every response. During replay verification:

1. The replay harness reads the `policy_version` from the original decision trace.
2. It requests that specific policy version from the Policy Registry.
3. The registry returns the immutable PolicyStore for that version.
4. The replay PDP evaluates the same request against the historical policy.
5. The response hash is compared to the original — must be bit-exact.

Without the registry, step 2 is impossible if the policy file has been overwritten. The registry preserves every historical policy version, making replay verification possible at any point in the future.

---

## 5. How the Registry Prevents Silent Rule Changes

The prevention mechanism operates at three levels:

**Level 1: Hash Verification on Load.** Every policy file includes a `policy_hash` field. On load, the registry recomputes the hash from the rules and compares. Mismatch → fatal error.

**Level 2: Version Isolation.** Each policy version is stored as a separate file (`policy_v1.json`, `policy_v2.json`). There is no "current policy file" that gets edited in place. New policies are new files.

**Level 3: Active Policy Designation.** The registry maintains an explicit `active_policy` pointer that designates which version is used for live evaluations. Changing the active policy is an explicit operation that requires loading and verifying the new version first.

```
+-------------------+     LoadPolicy(v1)     +------------------+
|  Policy Registry  | --------------------> |  PolicyStore v1   |
|                   |                        |  (hash-verified)  |
|  ActivePolicy: v2 |     LoadPolicy(v2)     +------------------+
|                   | --------------------> |  PolicyStore v2   |
|  Versions:        |                        |  (hash-verified)  |
|    v1 (Frozen)    |     GetActivePolicy()  +------------------+
|    v2 (Active)    | --------------------> Returns PolicyStore v2
+-------------------+
```

---

## 6. Registry Interface Contract

```
PolicyRegistry
  ├── LoadPolicy(version string) error
  │     Loads a policy file from /policies/policy_{version}.json
  │     Verifies hash integrity
  │     Stores immutable PolicyStore in version map
  │
  ├── GetActivePolicy() *PolicyStore
  │     Returns the PolicyStore designated as active
  │     Used by PDP for live evaluations
  │
  ├── GetPolicy(version string) *PolicyStore
  │     Returns a specific historical PolicyStore
  │     Used by replay harness for historical evaluation
  │
  ├── SetActivePolicy(version string) error
  │     Designates a loaded policy as the active version
  │     Target version must already be loaded and verified
  │
  ├── ListPolicyVersions() []string
  │     Returns all loaded policy version identifiers
  │     Sorted lexicographically for determinism
  │
  └── VerifyAllPolicies() error
        Recomputes hashes for all loaded policies
        Returns error on first integrity violation
```

---

## 7. Initialization Flow

The PDP initialization flow changes from:

```
[Before]
PolicyStore ← NewPolicyStore("authority_matrix_v1.json")
PDP ← NewSarathiPDP(PolicyStore, Registry, Clock)
```

To:

```
[After — Config-Driven (Fix 2)]
PolicyRegistry ← NewPolicyRegistryFromConfig("registry_config.json")
  → reads active_version and policies_dir from config
  → no hardcoded version strings in source code

PolicyRegistry.InitializeFromConfig()
  → loads all policy_*.json files
  → verifies all hashes (Fix 3)
  → activates the config-specified version

PDP ← NewSarathiPDPFromRegistry(PolicyRegistry, AgentRegistry, Clock) (Fix 5)
  → PDP bound to registry's active policy
  → policyStore is unexported — cannot be replaced (Fix 1)
  → every response stamped with policy_version + policy_hash (Fix 6)
```

The PDP no longer knows about files. It receives policy through the registry interface. The active version is determined by `registry_config.json`, not hardcoded. This separation means the PDP can be tested with any policy version without changing its initialization code.

---

## 8. Governance Guarantees

| Guarantee | Mechanism | Failure Mode |
|-----------|-----------|--------------|
| Policy immutability | SHA-256 hash verification on load | Fatal error, system refuses to start |
| Version isolation | Separate files per version | No file overwrite possible |
| Replay fidelity | Historical version retrieval via GetPolicy() | Returns exact policy used at decision time |
| Deterministic evaluation | PolicyStore sorted rules (existing guarantee) | Preserved through registry layer |
| Active policy explicitness | SetActivePolicy() requires loaded version | Cannot activate unverified policy |
| Audit traceability | Every decision includes policy_version + policy_hash | Decision traceable to exact rule set |

---

## 9. What This Is Not

The Policy Registry is not:

- **A policy editor.** It loads and verifies policies. It does not create or modify them.
- **A dynamic configuration system.** Policies are loaded at startup or via explicit reload. No hot-swapping during evaluation.
- **A migration tool.** It does not convert v1 policies to v2 format. Each version is independent.
- **A rollback mechanism.** Changing the active policy to an older version is a new governance decision, not an undo.
- **A diff engine.** Comparing policy versions is an offline analysis task, not a registry responsibility.

---

**END OF DOCUMENT**

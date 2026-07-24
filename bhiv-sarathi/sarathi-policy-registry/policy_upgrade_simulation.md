# Policy Upgrade Simulation Report

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Upgrade Validation
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026

---

## 1. Simulation Overview

This document records the results of a controlled policy upgrade from v1 (1.0.0) to v2 (2.0.0). The simulation proves three things: that policy changes produce the expected verdict differences, that unchanged rules produce unchanged verdicts, and that replay determinism holds under both policy versions.

---

## 2. Policy Change Specification

### 2.1 Change 1 — Verdict Flip (AUTH-038)

| Field | v1 Value | v2 Value |
|-------|----------|----------|
| Rule ID | AUTH-038 | AUTH-038 |
| Agent Role | standard_agent | standard_agent |
| Resource Type | model_registry | model_registry |
| Action | read | read |
| Classification Max | L2 | L2 |
| **Verdict** | **DENY** | **ALLOW** |

**Rationale:** In v1, standard agents were explicitly denied read access to the model registry. In v2, this restriction is relaxed — standard agents may read model registry data, subject to the Bell-LaPadula classification ceiling.

**Expected Impact:** The rule verdict changes from DENY to ALLOW. However, because `model_registry` is classified L3 and `standard_agent` has L2 clearance, the Bell-LaPadula ceiling check (Stage 5) still produces a DENY verdict. The *reason* changes from `EXPLICIT_DENY` to `CLASSIFICATION_CEILING_EXCEEDED`. This demonstrates that the policy change had a real effect on evaluation flow — the PDP now reaches a different denial stage.

### 2.2 Change 2 — Classification Ceiling Change (AUTH-046)

| Field | v1 Value | v2 Value |
|-------|----------|----------|
| Rule ID | AUTH-046 | AUTH-046 |
| Agent Role | data_processor | data_processor |
| Resource Type | configuration | configuration |
| Action | read | read |
| **Classification Max** | **L1** | **L2** |
| **Verdict** | **DENY** | **ALLOW** |

**Rationale:** In v1, data processors were denied configuration read access with an L1 classification ceiling. In v2, the ceiling is raised to L2 and the verdict is changed to ALLOW, granting data processors read access to configuration — again subject to Bell-LaPadula.

**Expected Impact:** Configuration is classified L2. The data_processor agent has L1 clearance. Even though the rule now says ALLOW with L2 ceiling, the agent's L1 clearance is below the L2 resource classification. The Bell-LaPadula ceiling check blocks the request. The reason changes from `EXPLICIT_DENY` to `CLASSIFICATION_CEILING_EXCEEDED`.

---

## 3. Policy Hash Verification

| Version | Hash (SHA-256) | Rules | Frozen At |
|---------|---------------|-------|-----------|
| v1 (1.0.0) | `cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1` | 51 | 2026-03-09T00:00:00Z |
| v2 (2.0.0) | `74409b2c05bae043a3978bc6dc4209f44d96f596ff690db2f79aa0c93778f72e` | 51 | 2026-03-13T00:00:00Z |

Both hashes verified by independent recomputation during registry load. Hash mismatch → fatal error (never reached).

---

## 4. Verdict Change Results

### 4.1 Changed Cases (5 of 50)

| # | Agent | Resource | V1 Verdict | V2 Verdict | V1 Reason | V2 Reason | Rule |
|---|-------|----------|------------|------------|-----------|-----------|------|
| 1 | std-agent-001 | model-reg-001 | DENY | DENY | EXPLICIT_DENY | CLASSIFICATION_CEILING_EXCEEDED | AUTH-038 |
| 2 | std-agent-002 | model-reg-001 | DENY | DENY | EXPLICIT_DENY | CLASSIFICATION_CEILING_EXCEEDED | AUTH-038 |
| 3 | data-proc-001 | config-001 | DENY | DENY | EXPLICIT_DENY | CLASSIFICATION_CEILING_EXCEEDED | AUTH-046 |
| 4 | data-proc-002 | config-001 | DENY | DENY | EXPLICIT_DENY | CLASSIFICATION_CEILING_EXCEEDED | AUTH-046 |
| 5 | data-proc-001 | config-002 | DENY | DENY | EXPLICIT_DENY | CLASSIFICATION_CEILING_EXCEEDED | AUTH-046 |

**Analysis:** All five affected cases show the same pattern — the final verdict remains DENY, but the denial reason shifts from `EXPLICIT_DENY` (blocked by rule verdict) to `CLASSIFICATION_CEILING_EXCEEDED` (blocked by Bell-LaPadula). Case #5 demonstrates that the AUTH-046 change correctly propagates to all configuration resources (config-001 and config-002), proving rule-level impact coverage. This proves:

1. The policy change took effect — the evaluation path changed.
2. The Bell-LaPadula classification ceiling acts as a second defense layer.
3. Even when a rule verdict is relaxed, the security lattice provides independent protection.
4. The response `determining_rules` field changes, creating a different decision trace hash.
5. Rule changes propagate consistently across all matching resources.

**Version Binding Proof (Fix 6):** All 50 v1 responses carry `policy_version=1.0.0` and `policy_hash=cb6dac30...`. All 50 v2 responses carry `policy_version=2.0.0` and `policy_hash=74409b2c...`. This is verified by explicit assertion in both Go and Python test harnesses.

### 4.2 Control Cases — Unchanged (45 of 50)

The remaining 45 cases span 7 categories (governance ALLOWs, standard ALLOWs, standard DENYs, audit/safety controls, data processor/orchestrator operations, failure modes, and classification ceiling tests). All produce identical verdicts and reasons under both policy versions. Selected examples:

| Cat | Agent | Resource | V1 Verdict | V2 Verdict | V1 Reason | V2 Reason |
|-----|-------|----------|------------|------------|-----------|-----------|
| CAT-B | gov-agent-001 | policy-reg-001 | ALLOW | ALLOW | EXPLICIT_ALLOW | EXPLICIT_ALLOW |
| CAT-C | std-agent-001 | ops-data-001 | ALLOW | ALLOW | EXPLICIT_ALLOW | EXPLICIT_ALLOW |
| CAT-D | std-agent-001 | policy-reg-001 | DENY | DENY | EXPLICIT_DENY | EXPLICIT_DENY |
| CAT-E | audit-agent-001 | trace-001 | ALLOW | ALLOW | EXPLICIT_ALLOW | EXPLICIT_ALLOW |
| CAT-F | data-proc-001 | ops-data-001 | ALLOW | ALLOW | EXPLICIT_ALLOW | EXPLICIT_ALLOW |
| CAT-G | suspended-agent | ops-data-001 | DENY | DENY | AGENT_SUSPENDED | AGENT_SUSPENDED |
| CAT-H | std-agent-003 | ops-data-001 | ALLOW | ALLOW | EXPLICIT_ALLOW | EXPLICIT_ALLOW |

**Analysis:** All 45 control cases produce identical results. This proves the policy change affected only the targeted rules — zero collateral impact on any unrelated access decision, failure mode, or classification ceiling check.

---

## 5. Replay Determinism Results

| Policy Version | Test Cases | Passed | Failed | Mismatch Rate |
|----------------|-----------|--------|--------|---------------|
| v1 (1.0.0) | 50 | 50 | 0 | 0.0000% |
| v2 (2.0.0) | 50 | 50 | 0 | 0.0000% |
| **Total** | **100** | **100** | **0** | **0.0000%** |

Two independent PDP instances were created for each policy version. All 50 test cases (across 8 categories) were evaluated through both instances. Full response hashes were compared. Zero mismatches detected across 100 total comparisons.

Additionally, 20 cross-verification assertions were executed and all passed, confirming: only CAT-A cases changed, all governance requests remained ALLOW, all failure modes remained DENY, hashes are unique per version, and rule counts are preserved.

This proves that replay determinism holds under both the original policy and the upgraded policy. A decision made under v1 can be replayed with the v1 policy store. A decision made under v2 can be replayed with the v2 policy store. The Policy Registry makes this possible by preserving both versions simultaneously.

---

## 6. Why Decisions Changed

The policy changes altered the evaluation flow at Stage 4 (Authority Decision):

**Under v1:** The PDP finds AUTH-038 with verdict=DENY. It immediately returns DENY with reason=EXPLICIT_DENY. The Bell-LaPadula check is never reached because the deny-overrides rule stops evaluation.

**Under v2:** The PDP finds AUTH-038 with verdict=ALLOW. It proceeds to the Bell-LaPadula classification ceiling check (Stage 5). The agent's L2 clearance is below the resource's L3 classification. The PDP returns DENY with reason=CLASSIFICATION_CEILING_EXCEEDED.

The same logic applies to AUTH-046: explicit denial removed, but the security lattice independently blocks the access.

---

## 7. Why Determinism Still Holds

Determinism is preserved because:

1. **Same inputs, same outputs.** Given the same request, the same policy version, and the same registry state, the PDP always produces the same response. The DeterministicClock ensures timestamps are fixed.

2. **Policy isolation.** Each policy version is a separate, immutable PolicyStore. Loading v2 does not modify v1. The registry holds both simultaneously without interaction.

3. **No shared state.** Each PDP instance in the replay test has its own TraceStore (in replay mode, not writing to persistent chain). There is no shared mutable state between instances.

4. **Deterministic rule ordering.** Rules are sorted by rule_id before evaluation. The deny-overrides algorithm is order-independent. The classification ceiling check is a simple numeric comparison.

---

## 8. Governance Gaps Addressed

This simulation and the accompanying code changes address all six governance gaps identified during review:

| Fix | Gap | Resolution | Proof |
|-----|-----|-----------|-------|
| Fix 1 | PolicyStore immutability not strict enough | All fields unexported, no mutation methods, `frozen` flag, defensive copies | `IsFrozen()=true`, rules stored as tuple (Python) / unexported slice (Go) |
| Fix 2 | Active policy selection hardcoded | `registry_config.json` specifies `active_version` | `NewPolicyRegistryFromConfig()` reads config, no hardcoded strings |
| Fix 3 | Per-version hash validation not proven | `VerifyPolicyVersion()` returns stored + recomputed hash for each version | Explicit `[VERIFIED]` output per version in test results JSON |
| Fix 4 | Cross-version replay not proven | Same request evaluated under v1 and v2, diffs analyzed | 5/5 CAT-A cases differed, 45/45 control cases stable |
| Fix 5 | PDP can bypass registry | `NewSarathiPDPFromRegistry()` is the only production constructor | Old constructors marked Deprecated, PDP `policyStore` unexported |
| Fix 6 | Version binding not asserted | Every response carries `policy_version` + `policy_hash` | 50/50 v1 and 50/50 v2 responses carry correct version/hash |

---

## 9. Governance Implications

This simulation demonstrates that Sarathi's governance layer can evolve safely:

- **Policy changes are explicit.** The v2 policy file is a new file with a new hash. There is no silent mutation.
- **Impact is predictable.** The changed cases and unchanged cases can be identified before deployment by running the replay harness against both versions.
- **Defense in depth works.** Even when a rule is relaxed, the Bell-LaPadula security lattice provides an independent check. Two security mechanisms must both permit access.
- **Audit trail is complete.** Every decision trace records the exact policy_version and policy_hash used. Historical decisions can always be reconstructed under the original policy.
- **Active policy selection is deterministic.** The `registry_config.json` file is the single source of truth. No hardcoded version strings.
- **PDP cannot bypass the registry.** The production constructor `NewSarathiPDPFromRegistry()` requires a registry with a frozen active policy.

---

**END OF DOCUMENT**

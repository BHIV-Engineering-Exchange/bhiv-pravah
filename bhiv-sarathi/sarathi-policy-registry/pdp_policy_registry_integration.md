# PDP Policy Registry Integration

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — PDP ↔ Policy Registry Integration
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026

---

## 1. Integration Summary

This document specifies how the Sarathi PDP engine integrates with the new Policy Registry layer. The core change: the PDP no longer loads policy files directly. Instead, it receives an immutable PolicyStore from the Policy Registry. This separation enables versioned policy management, safe upgrades, and replay against historical policy versions — all without modifying the PDP evaluation logic.

---

## 2. What Changed

### 2.1 Before (Direct Policy Loading)

```
sarathi_pdp_core.go:

    ps, err := NewPolicyStore("authority_matrix_v1.json")
    registry := NewRegistryInterface()
    pdp := NewSarathiPDP(ps, registry, RealClock{})
```

The PDP knew about the file path. It loaded the policy directly. There was exactly one policy, and it was whatever was in `authority_matrix_v1.json` at startup time. If the file changed on disk after startup, the PDP would not know.

### 2.2 After (Registry-Mediated Policy Access)

```
sarathi_policy_registry_main.go:

    // FIX 2: Config-driven active policy selection
    registry, err := NewPolicyRegistryFromConfig("registry_config.json")
    loaded, err := registry.InitializeFromConfig()

    // FIX 5: PDP created via registry, not direct PolicyStore access
    pdp, err := NewSarathiPDPFromRegistry(registry, agentRegistry, clock)
```

The PDP receives a PolicyStore reference from the registry. It does not know where the policy came from, what version it is, or how many versions exist. The registry handles all of that. The active policy version is determined by `registry_config.json`, not hardcoded in source.

---

## 3. What Did NOT Change

The PDP evaluation pipeline is untouched. The 5-stage deterministic evaluation remains exactly as implemented:

1. Stage 1: Request Validation
2. Stage 2: Registry Lookup (agent + resource)
3. Stage 3: Policy Evaluation (FindMatchingRules)
4. Stage 4: Authority Decision (deny-overrides, classification ceiling)
5. Stage 5: ALLOW verdict

The `SarathiPDP` struct still takes a `*PolicyStore` (now unexported as `policyStore` — Fix 1). The `Evaluate()` method still calls `pdp.policyStore.FindMatchingRules()` via the immutable accessor. The `PDPResponse` still includes `PolicyVersion` and `PolicyHash` — now accessed via `pdp.policyStore.GetPolicyVersion()` and `pdp.policyStore.GetPolicyHash()` (Fix 6: version binding guarantee). No evaluation logic was modified.

This is intentional. The PDP is a pure function: `f(request, policy, registry) → response`. The Policy Registry changes how policy is loaded, not how it is evaluated.

---

## 4. Initialization Flow

### 4.1 Production Mode (Config-Driven — Fix 2)

```
registry_config.json → { "active_version": "v1", "policies_dir": "./policies" }

PolicyRegistry ← NewPolicyRegistryFromConfig("registry_config.json")
  ├── InitializeFromConfig()       // Loads all + activates config version
  │     ├── policy_v1.json         → ACTIVE (hash verified, config-selected)
  │     └── policy_v2.json         → FROZEN (hash verified)
  │
  └── NewSarathiPDPFromRegistry()  → SarathiPDP (Fix 5: registry-only constructor)
        │
        └── SarathiPDP.Evaluate(request) → PDPResponse
              (includes policy_version="1.0.0", policy_hash="cb6dac30...")
              (Fix 6: version binding — every response stamped)
```

### 4.2 Replay Mode (Fix 4: Cross-Version Evidence)

```
PolicyRegistry
  │
  ├── GetPolicy("v1")            → *PolicyStore (v1)
  │     └── NewSarathiPDPForReplay(v1PolicyStore, registry, deterministicClock)
  │           └── Evaluate(historicalRequest) → PDPResponse
  │                 (must match original decision trace — Fix 4 intra-version)
  │
  └── GetPolicy("v2")            → *PolicyStore (v2)
        └── NewSarathiPDPForReplay(v2PolicyStore, registry, deterministicClock)
              └── Evaluate(sameRequest) → PDPResponse
                    (controlled difference from v1 — Fix 4 cross-version)
```

---

## 5. Replay Harness Update

The existing `replay_check.go` creates two PDP instances with the same policy to prove determinism. With the Policy Registry, the replay harness gains a new capability: evaluating the same request under different policy versions to prove that policy changes produce expected (and only expected) verdict differences.

### 5.1 Same-Policy Replay (Determinism Proof)

Load the same policy version into two independent PDP instances. Evaluate the same request through both. Compare full response hashes. This is the existing replay pattern, now using the registry to retrieve the specific version.

### 5.2 Cross-Policy Replay (Upgrade Impact Proof)

Load v1 and v2 into separate PDP instances. Evaluate the same request through both. For cases affected by the policy change, verdicts or reasons will differ. For all other cases, results must be bit-exact. This proves the policy change had precisely the intended effect — no more, no less.

---

## 6. Data Flow Diagram

```
┌─────────────┐     LoadPolicy("v1")     ┌─────────────────┐
│             │ ──────────────────────── │  PolicyStore v1  │
│   Policy    │                          │  hash=cb6dac30.. │
│   Registry  │     LoadPolicy("v2")     ├─────────────────┤
│             │ ──────────────────────── │  PolicyStore v2  │
│  Active: v2 │                          │  hash=74409b2c.. │
└──────┬──────┘                          └────────┬────────┘
       │                                          │
       │  GetActivePolicy()                       │
       │  ──────────────── → PolicyStore v2 ──────┘
       │
       v
┌──────────────┐     Evaluate(req)     ┌──────────────┐
│  SarathiPDP  │ ────────────────────→ │  PDPResponse  │
│              │                        │  version=2.0.0│
│  PolicyStore │                        │  hash=74409b..│
│  = v2        │                        │  verdict=...  │
│  Clock       │                        │  trace=...    │
│  Registry    │                        └──────────────┘
└──────────────┘
```

---

## 7. Backward Compatibility and Deprecation

The integration maintains backward compatibility while establishing a clear migration path:

- `NewSarathiPDP()` — **Deprecated.** Still functional for existing tests but bypasses registry.
- `NewSarathiPDPFresh()` — **Deprecated.** Use `NewSarathiPDPForReplay()` instead.
- `NewSarathiPDPFromRegistry()` — **Production constructor.** Creates PDP bound to registry's active policy.
- `NewSarathiPDPForReplay()` — **Replay constructor.** Creates PDP for historical version verification.
- The `PDPResponse` schema is unchanged
- Decision trace format is unchanged
- `SarathiPDP.policyStore` is now unexported — external code cannot replace the policy after construction (Fix 1)
- Read-only accessors `GetPolicyVersion()` and `GetPolicyHash()` provide metadata access (Fix 6)

---

## 8. Go Compilation Instructions

From the `sarathi-policy-registry` directory on Windows:

```bash
# Build the main program
go build -o sarathi-policy-registry.exe sarathi_policy_registry_main.go pdp_engine.go policy_store.go policy_registry.go registry_interface.go clock.go

# Run
./sarathi-policy-registry.exe

# Or run directly
go run sarathi_policy_registry_main.go pdp_engine.go policy_store.go policy_registry.go registry_interface.go clock.go
```

---

**END OF DOCUMENT**

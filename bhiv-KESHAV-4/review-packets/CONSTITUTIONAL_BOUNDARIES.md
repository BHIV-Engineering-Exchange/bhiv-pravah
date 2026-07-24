# CONSTITUTIONAL BOUNDARIES — KESHAV

**Status:** Operational Freeze Preparation  
**Last Updated:** 2025-01-XX  
**Authority:** Pritesh (Architect) → Rajaryan Verma (Incoming Steward)

---

## 1. Core Constitutional Declaration

KESHAV is a **dependency intelligence participation layer** within the TANTRA ecosystem.

KESHAV **DOES NOT** and **MUST NEVER**:
- Own sovereign authority
- Own execution authority
- Mutate governance semantics
- Orchestrate downstream execution
- Persist hidden authority-bearing state
- Prioritize sovereign execution legitimacy
- Accumulate coordination authority
- Influence governance through observability

---

## 2. Authority Boundaries

### What KESHAV IS
- **Dependency intelligence analyzer** — reads SETU input, produces TANTRA output contract
- **Signal generator** — emits `resolution_signal` and `severity` based on deterministic rules
- **Stateless computation layer** — no persistent authority, no hidden state

### What KESHAV IS NOT
- **Decision authority** — RAJYA owns execution decisions
- **Enforcement authority** — Sarathi owns enforcement
- **Execution authority** — Core owns execution
- **Truth authority** — Bucket owns persistent truth
- **Observability authority** — InsightFlow owns observability

---

## 3. Orchestration Boundaries

KESHAV **DOES NOT**:
- Trigger downstream execution
- Coordinate multi-layer workflows
- Retry failed operations
- Manage execution lifecycle
- Control execution timing
- Prioritize execution order

KESHAV **ONLY**:
- Produces TANTRA output contract
- Passes output to RAJYA
- Emits observability events to InsightFlow

**Orchestration authority:** TANTRA pipeline (`tantra/pipeline.py`) owns layer coordination.

---

## 4. Downstream Influence Limits

### Severity Signal
- **Purpose:** Deterministic classification of `impact_score`
- **Mapping:** `impact_score < 3 → LOW`, `3-9 → MEDIUM`, `≥10 → HIGH`
- **NOT:** Execution priority, governance weight, or authority escalation

### Resolution Signal
- **Purpose:** Structured recommendation for RAJYA consumption
- **Format:** `UNBLOCK_DEPENDENCY:<task_id>`
- **NOT:** Execution command, enforcement directive, or orchestration instruction

### Impact Score
- **Purpose:** Passthrough from SETU propagation results
- **NOT:** KESHAV-generated authority metric

---

## 5. Observability Boundaries

InsightFlow participation is **read-only**:
- Emits structured events (`EXECUTION`, `FAILURE`)
- **DOES NOT** mutate KESHAV output
- **DOES NOT** alter execution flow
- **DOES NOT** accumulate orchestration authority

**Proof:** `test_insightflow_does_not_mutate_keshav_output` — PASS

---

## 6. Replay Participation Boundaries

KESHAV guarantees:
- **Deterministic output** — same input → identical output (excluding timestamp)
- **Trace continuity** — `trace_id` passthrough from SETU to all layers
- **No hidden state** — no caches, no adaptive behavior, no retained semantics

**Proof:** `test_deterministic_replay_10_runs` — 10/10 identical outputs

---

## 7. Governance Drift Prevention

### Prohibited Behaviors
- Adaptive severity thresholds
- Dynamic resolution signal generation
- Execution feedback loops
- Authority accumulation through repeated calls
- Hidden coordination state

### Enforcement Mechanisms
- Stateless function design
- No global mutable state
- No persistent caches
- Deterministic algorithms only
- Explicit fail-closed validation

---

## 8. Constitutional Compliance Verification

| Boundary | Verification Method | Status |
|----------|---------------------|--------|
| No execution authority | RAJYA consumes output without KESHAV triggering execution | ✅ PASS |
| No orchestration authority | Pipeline owns layer coordination | ✅ PASS |
| No truth authority | Bucket writes only on Core success | ✅ PASS |
| No observability authority | InsightFlow read-only | ✅ PASS |
| Deterministic replay | 10/10 identical outputs | ✅ PASS |
| Trace continuity | `trace_id` identical across all layers | ✅ PASS |
| Fail-closed validation | Invalid input → no downstream execution | ✅ PASS |

---

## 9. Operational Stewardship Expectations

Rajaryan Verma (incoming maintainer) must:
- **Reject** any feature request that accumulates authority
- **Reject** any adaptive behavior that breaks determinism
- **Reject** any orchestration logic that bypasses RAJYA
- **Enforce** constitutional boundaries during code review
- **Monitor** for governance drift in production

---

## 10. Convergence Freeze Recommendation

**KESHAV is constitutionally stable.**

No further capability expansion allowed without:
1. Constitutional boundary review
2. Distributed replay validation
3. Authority isolation proof
4. Governance drift assessment

**Freeze Status:** READY FOR OPERATIONAL HANDOVER

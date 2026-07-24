# SARATHI PDP — STRUCTURED DAILY LOGS

**Author:** Hemanth B  
**Task:** Task 4 — Sarathi PDP Minimal Implementation Specification  
**Period:** February 2026 — 7 Working Days  
**Status:** COMPLETE

---

## WHAT ARE STRUCTURED DAILY LOGS?

Structured daily logs are the engineering journal for the specification process. They record — for each day — what was planned, what was produced, what decisions were made, what blockers were encountered, and how the day's output connects to the overall task. They serve three purposes:

1. **Traceability:** An assessor can follow the logical progression from Day 1 to Day 7 and understand WHY each specification was written in this order.
2. **Decision Audit:** Every non-obvious design decision is recorded with rationale — not just WHAT was decided, but WHY.
3. **Dependency Tracking:** Each day's output is mapped to its inputs and downstream consumers.

---

## DAY 1 — MINIMAL INPUT SCHEMA DEFINITION

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 1 |
| **Objective** | Define the required Sarathi Request Envelope — every field the PDP needs to render a sovereign decision. |
| **Deliverable** | `sarathi_request_schema.md` (948 lines) |
| **Inputs Consumed** | Task 1 (Governance Validation — 12 assumptions); Task 2 (Canon — 60 rules); Task 3 (PDP Interface — Section 2); Research Report (canonical request envelope pattern) |
| **Key Decisions** | |
| | 1. **Six required sections** (agent_identity, intent, authority, risk_classification, context, correlation_id) — derived from NIST SP 800-162 ABAC categories (subject, action, resource, environment) + Sarathi-specific risk and correlation. |
| | 2. **Closed enumerations** for actions (9), agent classes (10), environments (4), classifications (4) — prevent semantic drift (Task 1 Assumption A1). |
| | 3. **Semantic null detection** (RES-08) — "null", "none", "nil", "N/A", empty string, and null bytes all treated as absent. |
| | 4. **parameters_hash** as SHA-256 of action parameters — binds the intent declaration to the actual parameters at the cryptographic level (addresses Task 1 A7). |
| | 5. **session_binding** as SHA-256 of TLS client cert — implements channel binding (RES-09). |
| | 6. **10 Input Invariants** (INV-01 through INV-10) — axiomatic properties every request must satisfy. |
| | 7. **4 Anti-Patterns** (AP-01 through AP-04) — explicitly prohibited input shapes (wildcard scopes, empty delegation chains, self-delegation, future timestamps). |
| **Blockers** | None. |
| **Output Consumers** | Day 3 (Stage 1 validates this schema); Day 4 (FM-01 covers missing fields); Day 6 (pseudocode implements validation). |
| **Lines of Specification** | 948 |
| **Canon Rules Addressed** | AC-21, AC-22, AC-23, AC-24, AC-32, EL-33, EL-34, ID-01, ID-02, ID-03, ID-05, ID-08 |

---

## DAY 2 — MINIMAL OUTPUT CONTRACT

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 2 |
| **Objective** | Define the exact Sarathi Response Schema — what the PDP returns for every verdict. |
| **Deliverable** | `sarathi_response_schema.md` (948 lines) |
| **Inputs Consumed** | Day 1 (Request Schema); Task 2 (Canon — refusal and audit rules RE-45 through AI-58); Task 3 (PDP Interface — Section 3); Research Report (XACML response model, capability token architecture) |
| **Key Decisions** | |
| | 1. **Three verdict types** — ALLOW (with capability token), DENY (with reason code), ESCALATE (with escalation reference + interim DENY). |
| | 2. **10 Output Invariants** (OUT-01 through OUT-10) — axiomatic properties every response must satisfy. |
| | 3. **22 DENY reason codes** — closed vocabulary, machine-readable, never used for control flow (Task 3 Section 6.4). |
| | 4. **14 Token Issuance Rules** (TI-01 through TI-14) — non-negotiable constraints on capability tokens: TTL ≤ 60s, exact scope, session-bound, single-use, Ed25519-signed. |
| | 5. **18 Prohibited Response Items** — things NEVER included in responses (internal state, stack traces, policy details, alternative actions). Implements GP-05 and RE-45. |
| | 6. **28-field audit record** structure with full evaluation trace, determining rules, and anomaly signals. |
| | 7. **Escalation protocol** — interim verdict = DENY, deadline = 15 minutes, target = Governance Council (RES-13). |
| **Blockers** | None. |
| **Output Consumers** | Day 3 (Stage 6 assembles this response); Day 4 (FM-05 covers audit failure); Day 5 (enforcement model builds on token structure); Day 6 (pseudocode generates this output). |
| **Lines of Specification** | 948 |
| **Canon Rules Addressed** | AI-53, AI-54, AI-55, AI-56, RE-45, RE-46, RE-47, RE-48, RE-49, RE-50, RE-51, RE-52, AC-32, MF-02, MF-05 |

---

## DAY 3 — EVALUATION ORDER SPECIFICATION

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 3 |
| **Objective** | Define the deterministic evaluation sequence — the algorithm that transforms Day 1 input into Day 2 output. |
| **Deliverable** | `evaluation_order_spec.md` (579 lines) |
| **Inputs Consumed** | Day 1 + Day 2; Task 3 (17-step pipeline); Task 2 (60 Canon rules — needed stage mapping); Research Report (XACML evaluation flow, Cedar deny-overrides) |
| **Key Decisions** | |
| | 1. **Seven stages** (not seventeen steps) — architectural abstraction with invariant guarantees. 17 steps map to 7 stages as implementation sub-steps. |
| | 2. **8 Evaluation Invariants** (EVAL-01 through EVAL-08) — total ordering, stage isolation, fail-closed, short-circuit, mandatory audit, no backtracking, deterministic duration, immutable input. |
| | 3. **Evaluation order is a security property** — not a performance optimization. Running stages out of order leaks information (why an agent was denied before verifying their identity). |
| | 4. **Deny-overrides combining** — chosen over first-applicable (order-dependent), permit-overrides (fail-open), only-one-applicable (requires Indeterminate). Formally verified by AWS Cedar in Lean 4. |
| | 5. **Short-circuit with audit completeness** — skipped stages recorded as SKIPPED_SHORT_CIRCUIT. Stage 7 never skipped. |
| | 6. **50ms p99 budget** with per-stage allocations: Identity 15ms, Lifecycle 5ms, Authority 10ms, Eligibility 8ms, Risk 7ms, Classification 3ms, Audit 2ms + 200ms write timeout. |
| **Blockers** | None. |
| **Output Consumers** | Day 4 (failure modes map to stages); Day 5 (enforcement model explains WHY stages matter); Day 6 (pseudocode directly implements this). |
| **Lines of Specification** | 579 |
| **Canon Rules Mapped** | All 60 rules assigned to stages (Section 2.1 mapping table) |

---

## DAY 4 — FAILURE MODE LOCKDOWN

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 4 |
| **Objective** | Define every failure state and its required behavior — the most important document because attackers exploit failure paths, not success paths. |
| **Deliverable** | `failure_mode_contract.md` (1,013 lines) |
| **Inputs Consumed** | Days 1-3; Task 3 (7 failure modes A-G); Task 1 (12 unsafe assumptions); Research Report (6 critical failure modes, Redis fail-open incident) |
| **Key Decisions** | |
| | 1. **Expanded from 6 (task requirement) to 12 failure modes** — added cascading revocation (FM-10), evaluation timeout (FM-11), HSM signing failure (FM-12), policy version mismatch (FM-03), audit sink failure (FM-05), ambiguous rules (FM-06). All derived from upstream specifications. |
| | 2. **The Fail-Closed Axiom** — every FM-XX verdict column is DENY. This is the mathematical proof of fail-closed behavior. Zero failure modes produce ALLOW. |
| | 3. **FM-05 (Audit Sink Unavailable) overrides ALLOW to DENY** — "unauditable ALLOW is more dangerous than false DENY." This is the most controversial decision; documented rationale traces to EU AI Act Article 12 and OUT-07. |
| | 4. **5 Compound Failure Scenarios** — real failures are never isolated. Documented behavior when multiple failures co-occur. |
| | 5. **Unified Recovery Protocol** — verify → validate state → flush emergency buffer → transition circuit breaker → log recovery. No auto-replay of denied requests. |
| **Blockers** | None. |
| **Output Consumers** | Day 5 (enforcement model references FM behavior); Day 6 (pseudocode implements all 12 FMs); Day 7 (this document — consolidation). |
| **Lines of Specification** | 1,013 |
| **Failure Modes Defined** | 12 (6 from task requirement + 6 additional from upstream analysis) |

---

## DAY 5 — ENFORCEMENT BOUNDARY DEFINITION

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 5 |
| **Objective** | Define HOW Sarathi prevents bypass — the mechanism that converts governance from advisory logging to physical enforcement. |
| **Deliverable** | `enforcement_model_spec.md` (702 lines) |
| **Inputs Consumed** | Days 1-4; Task 1 (Assumption A3 — Orchestrator Compliance); Task 3 (Sections 6.1-6.10 "Never Assume" rules); Research Report (Confused Deputy, capability tokens, logging insufficiency) |
| **Key Decisions** | |
| | 1. **Capability token model** — PDP issues cryptographic key on ALLOW; downstream resources require key for execution. No key = no access, regardless of caller claims. |
| | 2. **Three enforcement layers** — PDP inline (Layer 1), resource token verification (Layer 2), audit trail (Layer 3). Layer 2 is independent of Layer 1 — a compromised orchestrator is still blocked by the resource. |
| | 3. **11 resource-side verification checks** (R-01 through R-11) — mandatory, non-optional. A resource that skips checks is a governance hole. |
| | 4. **10 Enforcement Invariants** (ENF-01 through ENF-10) — no bypass mode, no cached verdicts, sole PDP token issuance, single-use tokens, HSM key. |
| | 5. **9 bypass attack vectors analyzed** — 0 achieve full bypass, 1 partial (HSM compromise). |
| | 6. **Advisory vs. Enforcement comparison** — side-by-side timeline showing 5 scenarios where logging fails but enforcement succeeds. |
| **Blockers** | None. |
| **Output Consumers** | Day 6 (pseudocode implements token generation and bypass prevention); Day 7 (enforcement dependencies in readiness statement). |
| **Lines of Specification** | 702 |
| **Industry References** | Hardy 1988, Close 2009, Dennis & Van Horn 1966, RFC 9449, NIST SP 800-207 |

---

## DAY 6 — MINIMAL REFERENCE PSEUDOCODE

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 6 |
| **Objective** | Translate Days 1-5 into executable pseudocode — the reference implementation that an engineer can directly port to any language. |
| **Deliverable** | `pdp_reference_pseudocode.md` (1,233 lines) |
| **Inputs Consumed** | All Days 1-5; all Task 1-3 artifacts |
| **Key Decisions** | |
| | 1. **Pure functions + data** — no classes, no inheritance, no dependency injection. Directly translatable to Go, Rust, Java, Python, TypeScript. |
| | 2. **19 functions total** — evaluate() + 7 stage functions + combine_deny_overrides() + generate_capability_token() + stage_7_audit_and_sign() + 6 helpers. |
| | 3. **Every line has a traceable comment** — each decision point references the Canon Rule, Global Principle, Invariant, or Failure Mode it implements. |
| | 4. **Default verdict = DENY at line 1** — ALLOW reachable only through affirmative path where all stages pass AND combining produces ALLOW AND audit succeeds AND signing succeeds. |
| | 5. **External dependencies as injected interfaces** — StateRegistry, RevocationList, ResourceRegistry, DedupStore, RateCounter, MosaicAccumulator, BHIVBucket, EmergencyBuffer, HSM. PDP does not own implementations. |
| | 6. **Verification checklist** (10 items) — what an engineer must verify when implementing from this pseudocode. |
| **Blockers** | None. |
| **Output Consumers** | Day 7 (consolidated specification references pseudocode as the authoritative implementation contract). |
| **Lines of Specification** | 1,233 |
| **Implementation Coverage** | 41/41 sub-steps, 12/12 failure modes, 14/14 token issuance rules, 8/8 evaluation invariants, 29 Canon rules directly referenced |

---

## DAY 7 — CONSOLIDATION + GOVERNANCE READINESS STATEMENT

| Field | Detail |
|---|---|
| **Date** | February 2026 — Day 7 |
| **Objective** | Consolidate all specifications into a single authoritative document; produce governance readiness statement. |
| **Deliverables** | `sarathi_pdp_lock_v1.md`, `structured_daily_logs.md`, video walkthrough script |
| **Inputs Consumed** | All Days 1-6; all Task 1-3 artifacts; Research Report |
| **Key Decisions** | |
| | 1. **12 Governance Guarantees** (G-01 through G-12) — each traced to specific spec sections. |
| | 2. **10 Explicit Non-Guarantees** (NG-01 through NG-10) — what Sarathi does NOT do. |
| | 3. **7 Hard Dependencies + 3 Soft Dependencies** — if any hard dependency is missing, specific guarantees are voided. |
| | 4. **15-item Go-Live Checklist** — all items must pass before production deployment. |
| | 5. **Readiness Verdict: GO (CONDITIONAL)** — conditional on all 15 items and 5 sign-offs. |
| **Blockers** | None. |
| **Final Output** | Complete PDP implementation contract: 7 specifications, ~5,400+ total lines, implementation-ready. |

---

## CUMULATIVE METRICS

| Metric | Value |
|---|---|
| Total Specification Lines | ~5,400+ |
| Total Deliverables | 9 files (7 specs + daily logs + video script) |
| Canon Rules Implemented | 29 in pseudocode; all 60 mapped to stages |
| Global Principles Enforced | GP-01, GP-03, GP-04, GP-06, GP-07 |
| Ambiguity Resolutions Applied | 10 of 14 |
| Industry Standards Referenced | 15+ (XACML, NIST, CWE, RFC, Cedar, Zanzibar, SPIFFE, EU AI Act) |
| Failure Modes | 12 (all DENY) |
| Attack Vectors Analyzed | 9 (0 full bypass) |
| Test Cases Derivable | 25 (Canon) + 14 (Ambiguity) + 12 (Failure) + 9 (Bypass) = 60 |
| Blockers Encountered | 0 |

---

**END OF STRUCTURED DAILY LOGS**

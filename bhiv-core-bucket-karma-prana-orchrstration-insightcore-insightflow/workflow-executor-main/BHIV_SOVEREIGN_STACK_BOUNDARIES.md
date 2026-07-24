# BHIV Sovereign Stack — Boundary & Authority Map

This document defines the **hard boundaries, responsibilities, and non-responsibilities**
of each major component in the BHIV execution stack.

Its purpose is to ensure the system remains **sovereign, auditable, deterministic, and
immune to authority leakage** under internal and public scrutiny.

This document is authoritative.

---

## 1. BHIV Core

### BHIV Core IS:
- The **originator of intent**
- The system that decides *what should be attempted*
- The source of `decision` and `trace_id`
- The owner of **business logic, intent logic, and governance rules**

### BHIV Core IS NOT:
- An execution engine
- An enforcement authority
- A system that can perform real-world actions
- A system that can override enforcement outcomes
- A system that can write or mutate truth records

### Boundary Rule:
> **BHIV Core may request execution — it can never cause execution.**

---

## 2. Enforcement Engine

### Enforcement Engine IS:
- The **authorization gate** between intent and execution
- A deterministic evaluator of safety, policy, and governance constraints
- The system that outputs exactly one of:
  - `ALLOW`
  - `REWRITE`
  - `BLOCK`
- Fail-closed by design

### Enforcement Engine IS NOT:
- A decision-maker
- A business logic engine
- A system that executes actions
- A system that retries, compensates, or reconciles failures
- A system that can modify stored truth

### Boundary Rule:
> **Enforcement may authorize or deny — it can never execute or decide intent.**

---

## 3. Workflow Executor

### Workflow Executor IS:
- The **only real-world execution engine** in the BHIV ecosystem
- A deterministic adapter router
- A system that performs side-effects **only after authorization**
- Explicit in success and explicit in failure

### Workflow Executor IS NOT:
- An enforcement system
- A policy evaluator
- A decision engine
- A system that retries side-effects implicitly
- A system that mutates historical records

### Boundary Rule:
> **Execution occurs only after authorization and never feeds authority back upstream.**

---

## 4. Execution Adapters (AI / Task / Email / WhatsApp)

### Adapters ARE:
- Isolated execution mechanisms
- Deterministic for the same input
- Fully trace-bound via `trace_id`
- Explicit in failure modes

### Adapters ARE NOT:
- Allowed to retry autonomously
- Allowed to emit hidden side-effects
- Allowed to bypass the executor
- Allowed to communicate with Core or Enforcement

### Boundary Rule:
> **Adapters perform one action or fail — nothing more.**

---

## 5. BHIV Bucket

### BHIV Bucket IS:
- The **immutable system of truth**
- Append-only
- Audit-grade
- The final recorder of what occurred

### BHIV Bucket IS NOT:
- A state store
- A reconciliation engine
- A feedback mechanism
- A decision input
- An execution influencer

### Boundary Rule:
> **Bucket records truth — it never influences behavior.**

---

## 6. Authority Flow Summary

```
BHIV Core → Enforcement → Workflow Executor → Adapters → BHIV Bucket
    ↑                                                           ↓
    └───────────────────────────────────────────────────────────┘
```

- Authority and data move strictly forward.
- Truth is recorded but never fed back.
```
BHIV Core
  → (intent)
Enforcement Engine
  → (authorization)
Workflow Executor
  → (execution)
Adapters
  → (side-effects)
BHIV Bucket
  → (immutable record only)
```

- No signal flows backward.
- No stored truth influences future authority.
- No layer may absorb another’s role.
- No layer may override another’s authority.
- No backward influence is permitted.

---

## 7. Non-Absorption Principle (Critical)

- Core can never absorb Enforcement
- Enforcement can never absorb Execution
- Execution can never absorb Truth
- Truth can never influence Authority

Any violation of this principle is considered a **sovereignty breach**.

---

## 8. Sovereign Outcome

This boundary model guarantees that:
- Authority is explicit and limited
- Execution is controlled and auditable
- Truth is immutable and pressure-safe
- No component can corrupt another under stress

**BHIV operates as a coherent sovereign stack, not a collection of parts.**

# EXECUTION_FAILURE_AND_REPLAY.md  
**Failure Handling & Deterministic Replay Guarantees**

---

## 1. Purpose

This document defines how the **Workflow Executor + Enforcement Engine** behave under:

- Partial failures
- Crashes
- Retries
- Replays
- Duplicate requests
- Infrastructure instability

The objective is to guarantee:

- No mutation of truth
- No non-deterministic behavior
- No pressure on Bucket
- No hidden recovery logic

---

## 2. Core Principles

The system is governed by the following non-negotiable principles:

1. **Fail closed**
2. **Never mutate history**
3. **Never infer intent**
4. **Never retry with side effects**
5. **Never compensate via Bucket**

Failure is treated as **truth**, not an error to be corrected later.

---

## 3. Failure Classification

### 3.1 Pre-Enforcement Failure
Examples:
- Invalid payload
- Missing required fields
- Contract violation

Behavior:
- Enforcement decision = BLOCK
- Reason code = `invalid_input`
- One Bucket write (if invocation reached enforcement)
- No retries

---

### 3.2 Enforcement Logic Failure
Examples:
- Evaluator crash
- Unexpected exception
- Dependency timeout

Behavior:
- Enforcement decision = BLOCK
- Reason code = `enforcement_exception`
- Single immutable Bucket record
- No re-execution
- No retry with side effects

---

### 3.3 Adapter Execution Failure
Examples:
- WhatsApp API failure
- Email SMTP error
- External AI timeout

Behavior:
- Adapter reports failure explicitly
- Enforcement records failure outcome
- Bucket write captures failure
- No automatic retry
- No adapter replay

---

### 3.4 Bucket Write Failure
Examples:
- Schema rejection
- Quota exceeded
- Governance denial

Behavior:
- Enforcement returns failure upstream
- No retry attempt
- No alternate storage
- No compensation logic
- Bucket remains authoritative

---

## 4. Retry Rules (Hard Lock)

The system enforces **zero automatic retries** for any execution with side effects.

This includes:
- Messaging
- Emails
- Task creation
- External AI calls

If a caller retries:
- It is treated as a **new execution**
- A new enforcement_decision_id is generated
- A new Bucket record may be written
- History remains chronological

---

## 5. Replay Guarantees

Replaying the same request payload:

- Does NOT reference prior executions
- Does NOT attempt reconciliation
- Does NOT deduplicate
- Does NOT assume idempotency

Replay behavior is deterministic **per invocation**, not across invocations.

Truth is a timeline, not a corrected state.

---

## 6. Determinism Definition

For the same input payload and environment:

- Enforcement produces the same decision
- Evaluator ordering is fixed
- Precedence rules are stable
- No randomness is introduced

The only changing values across replays:
- `enforcement_decision_id`
- `timestamp`

These changes do NOT affect outcome semantics.

---

## 7. No Hidden Recovery Logic

The system explicitly forbids:

- Background reconciliation jobs
- Delayed corrections
- Async compensation
- “Fix later” pipelines
- State repair logic

Failure is final and observable.

---

## 8. Safety Under Pressure

Under:
- High traffic
- Partial outages
- External dependency instability

The system behavior degrades safely by:
- Blocking execution
- Preserving traceability
- Avoiding side effects

Truth is preferred over availability.

---

## 9. Security & Governance Boundary

No component may:
- Request Bucket mutation
- Request replay authority
- Request enforcement override
- Bypass failure handling rules

Any such attempt is a governance violation.

---

## 10. Constitutional Statement

> **Failure is recorded, not corrected.  
> Replay is allowed, reconciliation is not.  
> Truth survives crashes.**

---

**Status:** LOCKED  
**Applies To:** Workflow Executor, Enforcement Engine, Adapters  
**Change Policy:** Governance approval required

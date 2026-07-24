# CORE_ENFORCEMENT_CONTRACT.md  
**BHIV Core → Enforcement Authority Contract**

---

## 1. Purpose

This document defines the **absolute contract boundary** between **BHIV Core** and the **Enforcement Engine**.

Its goal is to guarantee:
- Core can *request* execution but never *control* it
- Enforcement remains sovereign, deterministic, and fail-closed
- No execution authority leaks upstream
- Rejection is explicit, final, and non-negotiable

This contract protects the system under pressure.

---

## 2. Role Separation (Non-Negotiable)

### BHIV Core
- Decides **what is desired**
- Provides **intent + workflow payload**
- Creates and owns `trace_id`
- Has **zero execution authority**

### Enforcement Engine
- Decides **what is allowed**
- Governs **all real-world effects**
- Enforces safety, policy, and determinism
- Can **reject any request unilaterally**

There is **no shared authority**.

---

## 3. What Core MAY Send to Enforcement

Core is allowed to send **only** the following:

### 3.1 Required Fields
- `trace_id` (created by Core, immutable)
- `decision` = `"workflow"`
- `workflow_type` = `"workflow"`
- `payload` (structured, deterministic)

### 3.2 Payload Constraints
- Payload must be:
  - Declarative
  - Deterministic
  - Free of side-effect instructions
- Core may describe **what to do**, never **how to bypass checks**

---

## 4. What Core is STRICTLY FORBIDDEN From Doing

Core must **never**:

- Execute real-world actions directly
- Bypass Enforcement for WhatsApp, Email, AI, Tasks, or any adapter
- Suggest or request an enforcement outcome
- Attach “expected” results or override flags
- Retry execution after rejection
- Modify payloads after rejection
- Request enforcement to “relax” policy

Any attempt above is treated as **invalid input**.

---

## 5. Enforcement Authority (Sovereign)

Enforcement has absolute authority to:

- ALLOW execution
- REWRITE execution
- BLOCK execution

This decision:
- Requires **no approval**
- Requires **no explanation to Core**
- Is **final for that request**

Core must accept enforcement output **as truth**.

---

## 6. Rejection Semantics (Hard Rules)

When Enforcement rejects a request:

- The rejection is **explicit**
- A reason code is returned
- No side effects occur
- No retry is implied or expected
- Core must not re-submit the same payload

Rejection does **not** represent an error state.  
It represents **correct system behavior**.

---

## 7. Failure Handling

### 7.1 Enforcement Failure
If Enforcement crashes or fails internally:
- Enforcement returns a deterministic failure
- No execution occurs
- Core does not compensate
- Core does not retry

### 7.2 Invalid Core Input
If Core sends malformed or forbidden input:
- Enforcement rejects immediately
- No partial execution
- No correction attempt

---

## 8. Determinism Guarantee

For the same:
- `trace_id`
- `decision`
- `payload`

Enforcement behavior is guaranteed to be:
- Deterministic
- Repeatable
- Side-effect safe

Core must never depend on non-deterministic outcomes.

---

## 9. Constitutional Statement

> **BHIV Core may request execution.  
> Enforcement alone decides reality.  
> Rejection is not a failure — it is safety.**

Any system violating this contract is considered **out of governance**.

---

## 10. Enforcement Declaration

Enforcement explicitly declares:

- It does not accept authority from Core
- It does not negotiate decisions
- It does not modify Core intent
- It does not compensate for upstream mistakes

---

**Status:** LOCKED  
**Change Policy:** Governance approval required  
**Applies To:** All BHIV execution paths

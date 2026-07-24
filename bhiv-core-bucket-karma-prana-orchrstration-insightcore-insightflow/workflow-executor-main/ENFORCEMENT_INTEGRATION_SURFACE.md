# ENFORCEMENT_INTEGRATION_SURFACE.md

**Task:** BHIV Core ↔ Enforcement ↔ Bucket Discipline Lock  
**Owner:** Raj Prajapati  
**Date:** 29 Jan 2026  
**Status:** LOCKED (Demo-Safe)

---

## 1. Purpose

This document enumerates **every allowed and disallowed integration surface**
around the Enforcement Engine.

Its goal is to prove, unambiguously, that:

- Enforcement is the **only authorization gate**
- Execution cannot bypass Enforcement
- Bucket is **write-only, append-only**
- No hidden feedback loops exist
- Authority, execution, and truth are strictly separated

This document describes **current reality in code**, not intent or roadmap.

---

## 2. Inbound Paths INTO Enforcement (Authoritative Callers)

The Enforcement Engine accepts requests **only** from the following sources.

### 2.1 BHIV Core
- **Role:** Decision authority
- **What Core provides:**
  - `trace_id`
  - `decision`
  - normalized workflow intent
- **What Core CANNOT do:**
  - Execute workflows
  - Modify Enforcement decisions
  - Write to Bucket
- **Contract:**
  - Core may only *request authorization*
  - Enforcement may allow, rewrite, or block

✅ **Allowed**

---

### 2.2 AI Assistant Backend
- **Role:** Workflow signal source
- **Trigger condition:** `decision == "workflow"`
- **Behavior:**
  - Sends workflow payload to Enforcement
  - Awaits enforcement result
- **Restrictions:**
  - Cannot execute side-effects directly
  - Cannot retry enforcement on rejection

✅ **Allowed**

---

### 2.3 AI Being
- **Role:** Specialized workflow origin (no special privileges)
- **Behavior:**
  - Uses the **same Enforcement gateway**
  - Same schema, same determinism rules
- **Restrictions:**
  - No bypass
  - No privileged execution
  - No custom adapters

✅ **Allowed**

---

### 2.4 Gurukul (via Core / Assistant only)
- **Role:** Domain workflow origin
- **Constraint:**
  - Cannot call Enforcement directly
  - Must route via Core or Assistant

⚠️ **Indirect only**

---

## 3. Explicitly DISALLOWED Inbound Paths

The following are **explicitly forbidden** and do not exist in code:

- Bucket → Enforcement
- Executor → Enforcement
- Adapter → Enforcement
- Any UI → Enforcement
- Any external system directly → Enforcement

❌ **Not possible by design**

---

## 4. Outbound Paths FROM Enforcement

### 4.1 Workflow Executor
- **Role:** Executes side-effects *after authorization*
- **Trigger:**
  - Only when Enforcement returns `ALLOW` or `REWRITE`
- **Restrictions:**
  - Executor cannot override enforcement
  - Executor cannot infer missing permissions

✅ **Allowed**

---

### 4.2 BHIV Bucket
- **Role:** Immutable truth store
- **Interaction type:** WRITE-ONLY
- **What is written:**
  - Enforcement decisions
  - Execution telemetry
- **What NEVER happens:**
  - Updates
  - Deletes
  - Reconciliation
  - Reads to influence behavior

✅ **Append-only**

---

## 5. Explicitly DISALLOWED Outbound Paths

- Enforcement → Core (state mutation)
- Enforcement → Adapter (direct execution)
- Enforcement → UI
- Enforcement → Governance mutation

❌ **Not possible**

---

## 6. Authority Boundaries (Non-Negotiable)

| Component     | Authority Level |
|---------------|-----------------|
| BHIV Core     | Decides intent  |
| Enforcement   | Authorizes      |
| Executor      | Executes        |
| Bucket        | Records truth   |

No component may perform another’s role.

---

## 7. Trace ID Discipline

- `trace_id` is **created upstream** (Core / Assistant)
- Enforcement **must propagate it unchanged**
- Executor and Bucket **must record it verbatim**
- No component may regenerate or alter a trace_id

Violation = contract breach.

---

## 8. Hidden Feedback Loop Analysis

The following loops **do not exist**:

- Bucket → Enforcement logic
- Executor → Enforcement retry logic
- Adapter → Core influence
- Enforcement → Governance mutation

All flows are **one-directional**.

---

## 9. Demo Safety Declaration

This integration surface is:

- Deterministic
- Fail-closed
- Pressure-safe
- Demo-safe
- Governance-safe

Any behavior outside this document is a **system violation**.

---

**END OF DOCUMENT**

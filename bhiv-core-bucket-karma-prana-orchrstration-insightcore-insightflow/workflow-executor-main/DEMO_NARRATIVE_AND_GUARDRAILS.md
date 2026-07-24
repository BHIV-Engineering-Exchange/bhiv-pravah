# DEMO_NARRATIVE_AND_GUARDRAILS.md  
**BHIV Core × Enforcement × Workflow Executor × Bucket**

---

## Purpose

This document locks the **exact narrative, scope, and guardrails** for:

- Feb 5 Internal Demo
- Feb 15 Public Demo

Its goal is to **prevent misinterpretation, improvisation, or authority confusion** during live demonstrations.

This document is binding.

---

## What WILL Be Shown Live

### 1. Successful Authorized Workflow

Flow:
BHIV Core → Enforcement → Workflow Executor → Adapter → Bucket

Demonstrates:
- Deterministic authorization
- Single execution path
- Immutable truth recording

---

### 2. Enforcement Blocked Workflow

Flow:
BHIV Core → Enforcement (DENY) → No execution

Demonstrates:
- Enforcement can stop execution
- No side-effects occur
- Clean failure propagation

---

### 3. Adapter Failure (Safe Failure)

Flow:
BHIV Core → Enforcement → Executor → Adapter (FAIL)

Demonstrates:
- Failure is contained
- No retries with side-effects
- Truth is still recorded

---

### 4. Replay Attempt (Same trace_id)

Flow:
Duplicate request with same trace_id

Demonstrates:
- Deterministic handling
- No authority escalation
- No state mutation

---

## What Will NEVER Be Shown Live

- Manual Bucket edits
- Retroactive corrections
- “Fixing” execution after failure
- Backfilling or reconciliation
- Enforcement overrides
- Direct adapter invocation
- Any admin or debug bypass

---

## How to Explain Enforcement Blocks (Scripted)

**Correct framing:**
> “Enforcement protects execution integrity by design.”

**Never say:**
- “It failed”
- “We blocked it manually”
- “We can allow it if needed”

Blocks are **intentional, not errors**.

---

## How to Explain Failures (Scripted)

**Correct framing:**
> “The system failed safely and preserved truth.”

Failures demonstrate strength, not weakness.

---

## Questions That Are Safe to Answer

- Can execution be blocked? → **Yes**
- Can truth be edited? → **No**
- Can execution be forced? → **No**
- Does the system retry automatically? → **No**
- Is behavior deterministic? → **Yes**

---

## Questions That Must Be Deferred

- “Can you add policy X?”
- “Can enforcement be bypassed?”
- “Can you delete a record?”
- “Can you auto-correct failures?”

Response:
> “That would violate our governance model.”

---

## Non-Negotiable Demo Guardrails

- No improvisation
- No “what-if” live coding
- No debug toggles
- No narrative shortcuts

The demo must reflect **exactly what the system is — not what it could be**.

---

## Final Rule

> **If something fails live, do not fix it.  
> Explain why the system behaved correctly.**

That is the demo.

---

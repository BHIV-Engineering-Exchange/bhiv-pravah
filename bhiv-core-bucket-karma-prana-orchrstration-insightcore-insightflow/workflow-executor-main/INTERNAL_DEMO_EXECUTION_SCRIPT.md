# Internal Demo Execution Script

## Purpose

This document defines the **exact execution flows** that will be demonstrated
during the Feb 5 Internal Demo and Feb 15 Public Demo.

Its purpose is to:
- Eliminate ambiguity
- Prevent unsafe live actions
- Ensure deterministic, repeatable demo behavior
- Define hard boundaries for what is NOT shown

No deviations are permitted during live demo.

---

## Demo Principles (Non-Negotiable)

- No manual intervention during execution
- No retries during demo
- No live debugging
- No configuration changes
- No hidden fallbacks
- No mutable state inspection

All outcomes must be explainable via logs and trace IDs only.

---

## Demo Environment

- System: Workflow Executor (Production deployment)
- Enforcement: Enabled, deterministic
- Bucket: Append-only, immutable
- Adapters: WhatsApp, AI, Task
- Logging: Telemetry + Bucket writes enabled
- Trace ID: Always visible and narrated

---

## Demo Flows (WHAT WILL BE SHOWN)

### Flow 1 — Successful Workflow Execution (Happy Path)

**Origin**
- AI Assistant

**Workflow**
- action_type: `ai`
- Prompt: deterministic informational query

**Expected Behavior**
- Decision == workflow
- Enforcement authorizes
- Adapter executes
- Execution result returned
- Telemetry emitted
- Bucket records immutable event

**Narration Focus**
- Trace ID propagation
- Single execution path
- Explicit success response

---

### Flow 2 — Blocked Workflow (Enforcement Rejection)

**Origin**
- AI Assistant

**Workflow**
- Payload intentionally violating policy (safe example)

**Expected Behavior**
- Enforcement returns BLOCK
- No adapter execution
- No side effects
- Bucket records BLOCK event

**Narration Focus**
- Enforcement authority
- Fail-closed behavior
- No execution leakage

---

### Flow 3 — Adapter Failure Handling

**Origin**
- AI Assistant

**Workflow**
- action_type: `task`
- Adapter forced to fail safely

**Expected Behavior**
- Enforcement authorizes
- Adapter fails explicitly
- Execution returns failure
- Telemetry emitted
- Bucket records failure event

**Narration Focus**
- No retries
- No compensation logic
- Explicit failure boundaries

---

### Flow 4 — Replay Determinism (Optional, Internal Only)

**Origin**
- AI Assistant

**Workflow**
- Same payload resent with same trace_id

**Expected Behavior**
- Treated as independent execution
- Deterministic result
- No reconciliation
- Immutable record created

**Narration Focus**
- Stateless execution
- Replay safety

---

## Explicitly NOT Demoed (Hard Red Lines)

The following MUST NOT be triggered live:

- Real WhatsApp messages to external users
- Real email delivery to production inboxes
- High-risk enforcement scenarios
- Governance boundary violations
- Bucket schema rejections
- Load testing or stress scenarios
- Concurrent execution races

---

## Failure Handling During Demo

If a failure occurs:

- The result is narrated as expected behavior
- No retries are attempted
- No configuration changes are made
- Logs and trace IDs are used for explanation

If a system-level failure occurs:

- Demo stops immediately
- Failure is acknowledged
- No recovery attempt is made live

---

## Success Criteria for Demo

The demo is considered successful if:

- All flows execute deterministically
- Trace IDs remain consistent
- Enforcement authority is clear
- No silent failures occur
- Bucket writes are immutable
- No embarrassment scenarios occur

---

## Final Lock

This script is frozen.

Any behavior not described here is out-of-scope
and must not be demonstrated live.

# DEMO_RISK_AND_FALLBACK_PLAN.md

## Purpose
This document defines the known risks, acceptable behaviors,
and hard red lines for the Workflow Executor and Enforcement lane
during live demos.

The objective is to ensure the system fails safely,
predictably, and without authority leakage under pressure.

---

## 1. Known Risks (Observed)

The following risks are known and acknowledged:

- External adapter dependency latency (AI / messaging providers)
- Invalid or malformed workflow payloads from upstream systems
- Adapter-level validation failures
- Cold start delays in hosted environments (Render)

These risks are bounded by deterministic execution
and explicit failure handling.

---

## 2. Acceptable Risks (Demo-Safe)

The following behaviors are acceptable during demo:

- Explicit adapter failure with structured error response
- Workflow rejection due to invalid input
- Unsupported action_type returning deterministic failure
- Replay of the same trace_id resulting in the same outcome class

All acceptable failures must:
- Return a response
- Preserve trace_id
- Emit execution telemetry
- Avoid retries with side effects

---

## 3. Non-Negotiable Red Lines

The demo must be halted immediately if any of the following occur:

- Silent execution failure
- Partial execution without response
- Mutation or overwrite of historical execution records
- Adapter retry causing duplicate side effects
- Execution occurring without decision == "workflow"
- Trace ID mismatch across Core → Executor → Logs

These constitute constitutional violations.

---

## 4. Live Fallback Plan

If an issue occurs during live demo:

- Do NOT retry execution blindly
- Do NOT alter payloads live
- Do NOT suppress failures

Fallback actions:
- Surface the structured failure response
- Explain enforcement or adapter decision
- Switch to a known-good trace_id if needed
- Demonstrate logs and trace consistency

The system is designed to fail visibly,
not recover silently.

---

## Final Statement

The Workflow Executor and Enforcement lane
are demo-safe under failure conditions.

Failures are explicit.
Authority does not leak.
History is immutable.

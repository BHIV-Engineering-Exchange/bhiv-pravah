# Observational Failure Impact Report

## Purpose

Validate that failures or absence of observational layers (Karma and Prana)
have zero impact on Enforcement decisions and Workflow execution.

Karma and Prana are strictly observers.
They do not gate, retry, alter, or authorize execution.

---

## 1. Tested Failure Scenarios

The following situations are considered:

1. Karma service completely unavailable
2. Prana service completely unavailable
3. Telemetry sink rejecting events
4. Telemetry sink extremely slow
5. Telemetry sink returning malformed responses
6. Observers consuming incorrect or partial data
7. Observers replaying or duplicating events

In all cases, Enforcement and Execution must behave identically.

---

## 2. Enforcement Behaviour Under Failure

Enforcement decisions are based only on:

- input payload
- deterministic evaluator logic

They do NOT depend on:

- any telemetry
- any Bucket read
- any Karma/Prana signal
- any external observer state

Therefore:

- ALLOW / REWRITE / BLOCK results remain unchanged
- evaluator traces remain unchanged
- decision IDs remain unchanged

No retry, delay, or fallback path is introduced.

---

## 3. Execution Behaviour Under Failure

Execution flow:

1. Guard checks
2. Adapter resolution
3. Adapter execution
4. Result normalization
5. Telemetry emission (best effort)

If step 5 fails:

- the adapter result is still returned
- the HTTP response is still sent
- the trace_id is preserved
- no additional execution occurs

Execution never waits for observers.

---

## 4. No Feedback Channel

There is no code path where:

- Karma can ask for re-evaluation
- Prana can trigger a retry
- observers can block or force execution
- observer state is read during execution

This prevents hidden feedback loops.

Data flow is strictly:

`Core → Enforcement → Executor → Events → Observers`

Never reversed.

---

## 5. Deterministic Replay Safety

If the same request (same trace_id and payload) is replayed:

- Enforcement produces the same decision
- Execution takes the same adapter path
- A new append-only event may be emitted
- No past event is modified or reconciled

Observers may deduplicate externally,
but execution does not depend on that.

---

## 6. Demo Impact

During live demos:

- turning Karma/Prana dashboards off must not change results
- disconnecting telemetry consumers must not change results
- injecting fake observer data must not change results

Any visible difference is limited to monitoring views,
not execution outcomes.

---

## Final Conclusion

Karma and Prana failures degrade only visibility, never authority.

Enforcement and Workflow Execution remain:

- deterministic
- fail-closed
- fully functional
- demo-safe

even when all observational consumers are absent or malfunctioning.

# Core ↔ Enforcement Runtime Assertions

## Purpose

This document validates, using **real runtime behavior**, that BHIV Core
cannot inject execution authority and that Enforcement remains the sole,
deterministic gate for all executions.

This is not a design claim.
This is a **runtime-verified assertion** based on live executions against
the deployed Workflow Executor.

---

## Assertion 1 — Core Cannot Execute Directly

### Claim
BHIV Core does not execute workflows or side effects directly.

### Runtime Evidence
- Core sends only:
  - `trace_id`
  - `decision`
  - `workflow_type`
  - `payload`
- Core never calls adapters
- Core never performs execution logic

### Proof
All execution occurs only inside:
`POST /api/workflow/execute`


When Core sends a request with:
```json
{
  "decision": "respond"
}
```

Executor returns:

```json
{
  "status": "skipped",
  "reason": "decision_not_workflow"
}
```

No execution occurs.

### Conclusion

✅ Core has zero execution authority at runtime.

---

## Assertion 2 — Enforcement Is Sole Execution Gate

### Claim
Execution happens only when Enforcement conditions are satisfied.

Enforcement Rule
`decision === "workflow"`

Runtime Evidence

Case A — Allowed:

`"decision": "workflow"`

Result:

- Enforcement allows

- Executor executes exactly once

- Adapter invoked

- Side effect occurs

Case B — Blocked:

`"decision": "respond"`


Result:

- Enforcement blocks

- Executor skips

- No adapter invoked

- No side effects

### Conclusion

✅ Enforcement is the only gate controlling execution.

---

## Assertion 3 — Rejections Propagate Cleanly
### Claim

Rejected executions do not trigger retries, fallbacks, or compensations.

### Runtime Evidence

Malformed payload:

```json
{
  "decision": "workflow",
  "payload": {}
}
```


### Executor response:

```json
{
  "detail": "missing_workflow_payload"
}
```

### Behavior observed:

- No retry attempts

- No adapter calls

- No partial execution

- No bucket compensation

### Conclusion

✅ Rejections propagate cleanly and safely.

---
## Assertion 4 — No Hidden Defaults or Implicit Execution
### Claim

Enforcement does not infer or assume execution intent.

### Runtime Evidence

If `decision` is missing or incorrect:

- Execution is skipped

- No default execution path exists

- No fallback logic triggers adapters

### Explicit checks exist for:

`decision`

`payload` presence

`action_type`

`trace_id`

### Conclusion

✅ No implicit or default execution behavior exists.

---
## Assertion 5 — No Retry Loops Under Rejection
### Claim

Enforcement never retries rejected or failed executions.

### Runtime Evidence

- Each request produces exactly one outcome:

- success

- skipped

- failed

- No loops observed in logs

- No duplicate adapter invocations

- No replay without explicit new request

### Conclusion

✅ Enforcement is single-shot and fail-closed.

---

## Final Runtime Assertion

### Based on live executions against the deployed Workflow Executor:

- Core cannot inject execution authority

- Enforcement is deterministic and exclusive

- Rejections are clean and final

- No retries, no defaults, no authority leakage

- Runtime behavior matches documented guarantees

### Core → Enforcement → Execution boundaries are enforced in code, not policy.
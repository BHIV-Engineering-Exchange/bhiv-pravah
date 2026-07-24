# LOCKED EXECUTION CONTRACT — PHASE D

## Request
- trace_id (string, required)
- decision === "workflow"
- data.workflow_type === "workflow"
- data.payload.action_type (string)

## Response
- trace_id
- status: success | failed | skipped
- execution_result.success (boolean)
- execution_result.error_code (if failed)

## Guarantees
- No execution if decision != workflow
- No silent failures
- Deterministic single-path execution
- Trace ID propagated end-to-end

This contract is frozen for Phase D.

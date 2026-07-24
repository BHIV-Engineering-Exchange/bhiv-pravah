# Global Workflow Execution Map

This document defines the ONLY allowed execution interface
for all BHIV products.

---

## Canonical Execution Endpoint

POST /api/workflow/execute

Hosted at:
WORKFLOW_EXECUTOR_BASE_URL (env var)

---

## Universal Request Contract

```json
{
  "trace_id": "string",
  "source_product": "EMS | AI_ASSISTANT | AI_BEING | GURUKUL",
  "decision": "workflow",
  "data": {
    "workflow_type": "workflow",
    "payload": {
      "action_type": "whatsapp | email | ai | task",
      "...": "adapter specific fields"
    }
  }
}
```
## Universal Response Contract

```json
{
  "trace_id": "string",
  "status": "success | failed | skipped",
  "execution_result": {
    "success": true | false,
    "adapter": "string",
    "reference_id": "string | null",
    "error_code": "string | null"
  }
}
```
## Hard Rules

- decision MUST be "workflow"

- No product may bypass Workflow Executor

- No execution without trace_id

- No adapter logic exposed to callers

- Deterministic behavior required

## Adapter Responsibility

- Workflow Executor owns:

- WhatsApp execution

- Email execution

- AI API execution

- Task execution

## Products only REQUEST execution
- They NEVER perform execution

## END OF CONTRACT
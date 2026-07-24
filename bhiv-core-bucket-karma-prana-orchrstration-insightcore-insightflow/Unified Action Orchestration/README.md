## Unified Action Orchestration

This service orchestrates actions received from `/api/assistant`, managing their lifecycle from requested to completed/failed states.

### Lifecycle
Actions transition through: requested → executing → completed/failed, with all state changes logged.

### Commands Emitted
Standardized commands (SEND_MESSAGE, FETCH_MESSAGES, SCHEDULE_MESSAGE) are emitted for execution by external services.

### What it does NOT do
This service does not execute actions directly; it only orchestrates and emits commands for external execution.
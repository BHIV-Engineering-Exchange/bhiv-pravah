# Telemetry Proof

## Telemetry logs
```json
{"event_type":"execution_started","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","timestamp":"2026-05-29T12:00:13Z","details":{"stage":"routing"}}
{"event_type":"execution_completed","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","timestamp":"2026-05-29T12:00:18Z","details":{"result":"observed"}}
{"event_type":"governance_rejection","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","timestamp":"2026-05-29T12:00:05Z","details":{"policy_id":"gov_exec_v1","status":"pending"}}
```

## Observability proof
- All telemetry events include execution_id, trace_id, tenant_id, and timestamp.
- Event types are normalized to the approved set.

## Telemetry stream example
```json
[
  {
    "event_type": "execution_started",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "timestamp": "2026-05-29T12:00:13Z",
    "details": {
      "stage": "routing"
    }
  },
  {
    "event_type": "execution_completed",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "timestamp": "2026-05-29T12:00:18Z",
    "details": {
      "result": "observed"
    }
  }
]
```

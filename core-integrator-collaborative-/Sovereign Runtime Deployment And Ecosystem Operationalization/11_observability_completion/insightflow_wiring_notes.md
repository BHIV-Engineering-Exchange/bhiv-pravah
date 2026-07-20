# InsightFlow Wiring Notes

**Date:** 2026-07-07  
**Status:** PASS (local live emission)

## Call sites added

| Component | File | Event |
|-----------|------|-------|
| CET | `cet_service.py` | `contract.compiled` |
| Sarathi | `sarathi_service.py` | `authority.validated` |
| Gate | `gate_service.py` | `gate.evaluated` |
| BHIV Core | `src/core/gateway.py` | `execution.completed` |
| Integration Bridge | `integration_bridge.py` | `instruction.received` (existing) |

Events append to `bhiv_bucket/insightflow_events.jsonl` via `src/utils/telemetry_writer.py`.

## Live evidence

After `python run_comprehensive_live_tests.py` (trace `comp_ttg_434a5d3954`):

```
GET http://127.0.0.1:8005/bucket/dashboard → 200
insightflow_event_count: 90
insightflow_by_component: {
  "integration_bridge": 73,
  "bhiv_core": 5,
  "cet": 4,
  "sarathi": 4,
  "gate": 4
}
```

## Remaining gap

Creator Core still writes to its own `db/creator_core_telemetry/` path. Centralized query covers bridge + authority stages + BHIV execution; Creator Core events are not yet merged into the dashboard query.

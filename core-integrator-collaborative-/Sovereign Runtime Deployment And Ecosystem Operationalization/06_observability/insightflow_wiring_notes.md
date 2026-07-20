# InsightFlow Wiring Notes

## What was wired

- `integration_bridge.py` calls `make_lineage_event()` and persists to `bhiv_bucket/insightflow_events.jsonl`
- Event type: `instruction.received` with `trace_id`, `workflow_id`, `product_context`

## What remains partial

- CET, Sarathi, Gate, BHIV Core, and Bucket do not yet emit InsightFlow events (only `telemetry_target` labels in some modules)
- No centralized collector service; events are append-only JSONL on disk

## Query example

```bash
# Count events
wc -l bhiv_bucket/insightflow_events.jsonl
```

## Storage decision

JSONL in `bhiv_bucket/` chosen for consistency with artifact storage location. Future: extend Bucket API with `/bucket/telemetry` query endpoint.

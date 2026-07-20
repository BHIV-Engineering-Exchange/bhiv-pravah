# Dashboard Notes

## Minimal observability (current)

No standalone dashboard service deployed. Observability is available via:

| Source | Endpoint / file | Data |
|---|---|---|
| Service health | `/health` on each service | up/down |
| Pipeline health | `:8004/pipeline/health` | component status |
| Bucket stats | `:8005/bucket/stats` | artifact counts, trace count |
| InsightFlow | `bhiv_bucket/insightflow_events.jsonl` | event counts by component |
| Traces | `:8005/bucket/trace/{id}` | per-trace artifacts |

## Recommended next step

Build a read-only FastAPI page at `:8009/dashboard` showing:

- 8-service health grid
- Last 20 traces from bucket index
- InsightFlow event count per component

## Test command

```bash
python test_services.py
curl http://127.0.0.1:8005/bucket/stats
```

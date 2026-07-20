# Observability Dashboard Notes

**Date:** 2026-07-07  
**Status:** PASS (minimal read-only endpoint)

## Endpoint

`GET /bucket/dashboard` on Bucket service (port 8005)

Returns:

- `bucket` — artifact counts by type (all 7 types)
- `recent_traces` — last 10 traces from trace index
- `insightflow_event_count` — events in `bhiv_bucket/insightflow_events.jsonl`
- `insightflow_by_component` — event counts per component

Companion query: `GET /bucket/insightflow?limit=100`

## Live snapshot (2026-07-07)

```
GET http://127.0.0.1:8005/bucket/dashboard → 200
total_artifacts: 255
total_traces: 62
insightflow_event_count: 90
```

## Not built

- No HTML UI / Grafana integration
- No remote-hosted dashboard (local only in this sprint)

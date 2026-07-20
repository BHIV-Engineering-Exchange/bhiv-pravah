# Replay After Recovery Results

**Status:** PASS for completed traces  
**Generated:** 2026-07-07

## Test

Replayed traces after live pipeline runs (services still running):

| Trace ID | Replay status | Bucket status |
|---|---|---|
| `live_test_d61c664e3559` | 200 | 200 |
| `comp_ttv_bd10684a9d` | 200 | 200 |
| `comp_simulation_runtime_40b176773f` | 200 | 200 |

Command:
```bash
curl -H "X-API-Key: prod_shakti_tantra_secret_key_2026" \
  http://127.0.0.1:8004/pipeline/replay/live_test_d61c664e3559
```

## Pass/fail

- **PASS:** Replay reconstructs artifact chain from bucket for completed traces
- **NOT RUN:** Replay after service kill + restart

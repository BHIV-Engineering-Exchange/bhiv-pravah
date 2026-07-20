# Pipeline Wiring Runtime Evidence Packet

**Integration:** CET → Sarathi → Gate → BHIV Core  
**Trace ID:** `live_test_d61c664e3559`  
**Classification:** live-service evidence

## Artifact lineage

| Stage | Artifact ID |
|---|---|
| A1 Instruction | `instruction_734a3545` |
| A2 Blueprint | `blueprint_5508e5e7` |
| A2b Contract (CET) | `contract_9812548f` |
| A2c Authority (Sarathi) | `authority_02e9be57` |
| A2d Gate | `gate_adb48136` |
| A3 Execution | `execution_9ecc8333` |
| A4 Result | `result_a266362b` |

## Replay verification

```
GET /pipeline/replay/live_test_d61c664e3559 → 200 OK
GET /bucket/trace/live_test_d61c664e3559 → 200 OK (4 artifacts)
```

## Health snapshot (2026-07-07)

All 8 services responded on localhost ports 8000–8008.

## Production proof statement

This packet proves the Integration Bridge invokes CET, Sarathi, and Gate as live HTTP services before BHIV Core execution. Gate authorizes only; BHIV Core executes (no double-execution).

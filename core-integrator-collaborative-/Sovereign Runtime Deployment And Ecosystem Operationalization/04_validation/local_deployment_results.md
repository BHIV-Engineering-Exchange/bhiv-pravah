# Local Deployment Results

**Classification:** live-service evidence (not simulation)  
**Generated:** 2026-07-07  
**Command:** `python run_comprehensive_live_tests.py`

## Service health (8/8)

| Service | URL | Status |
|---|---|---|
| Prompt Runner | `:8003/health` | 200 OK |
| Creator Core | `:8000/` | 200 OK |
| BHIV Core | `:8001/system/health` | OK (localhost rate-limit bypass for mesh calls) |
| Integration Bridge | `:8004/pipeline/health` | 200 OK |
| Bucket | `:8005/bucket/stats` | 200 OK |
| CET | `:8006/health` | 200 OK |
| Sarathi | `:8007/health` | 200 OK |
| Gate | `:8008/health` | 200 OK |

## End-to-end pipeline results (4/4 PASS)

| Product | Trace ID | Pipeline | Replay | Bucket |
|---|---|---|---|---|
| TTG | `comp_ttg_2f81022aee` | 200 | 200 | 200 |
| TTV | `comp_ttv_49a28b3bbd` | 200 | 200 | 200 |
| Gurukul | `comp_gurukul_a8535de499` | 200 | 200 | 200 |
| Simulation Runtime | `comp_simulation_runtime_de6b34f42a` | 200 | 200 | 200 |

Each run produced full artifact chain:

```
A1_instruction → A2_blueprint → A2b_contract → A2c_authority → A2d_gate → A3_execution → A4_result
```

## Before baseline (simulation — not live proof)

Command: `python full_tantra_flow_test.py`  
Trace: `inst_tantra_606bdd086cb4`  
Note: in-process simulation only; superseded by live traces above.

## Pass/fail summary

- **PASS:** All 8 services respond on localhost
- **PASS:** Live CET → Sarathi → Gate → BHIV pipeline for all 4 products
- **PASS:** Replay and bucket retrieval for all 4 products
- **PARTIAL:** Bucket stores 4 artifact types; contract/authority/gate not separately persisted

## Raw evidence

`05_evidence_packets/comprehensive_live_test_results.json`

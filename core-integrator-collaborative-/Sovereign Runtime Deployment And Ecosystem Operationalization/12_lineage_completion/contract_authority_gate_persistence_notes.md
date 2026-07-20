# Contract / Authority / Gate Persistence Notes

**Date:** 2026-07-07  
**Status:** PASS (live evidence)

## Change

Extended `bhiv_bucket.py` to treat **contract**, **authority**, and **gate** as first-class artifact types alongside instruction, blueprint, execution, and result.

- Added `ARTIFACT_TYPES` constant (7 types)
- Init creates `contracts/`, `authorities/`, `gates/` directories
- `retrieve_artifact`, `retrieve_by_trace`, and `get_stats` iterate all 7 types

`integration_bridge.py` `ArtifactGraph.update_artifact()` already POSTed these types to `/bucket/store`; the gap was Bucket-side retrieval and stats only counting 4 types.

## Verification

**Command:** `python run_comprehensive_live_tests.py`  
**Result:** 4/4 products passed with `bucket_has_all_7_types: true`

| Product | Trace ID | Bucket types |
|---------|----------|--------------|
| TTG | `comp_ttg_434a5d3954` | 7/7 |
| TTV | `comp_ttv_49093259a5` | 7/7 |
| Gurukul | `comp_gurukul_db1cef24b5` | 7/7 |
| Simulation Runtime | `comp_simulation_runtime_4397308533` | 7/7 |

**Bucket stats after run** (`GET /bucket/stats` → 200):

```json
"by_type": {
  "instruction": 74,
  "blueprint": 71,
  "contract": 16,
  "authority": 16,
  "gate": 16,
  "execution": 31,
  "result": 31
}
```

**Sample trace lookup:** `GET /bucket/trace/comp_ttg_434a5d3954` → 200, 7 artifacts.

## Partial-failure trace

Recovery test with BHIV down stores 5 types (no execution/result): `rec_3b2c0c81b9` → instruction, blueprint, contract, authority, gate only.

# TTG Onboarding

**Trace ID:** `comp_ttg_2f81022aee`  
**Validated:** 2026-07-07 (`run_comprehensive_live_tests.py`)

1. **Prompt Runner participation** — confirmed via `/pipeline/execute` with `product_context=ttg`
2. **Creator Core participation** — blueprint stored in bucket trace chain
3. **Core execution participation** — CET → Sarathi → Gate → BHIV execution all present (A2b..A3)
4. **Bucket persistence** — `/bucket/trace/comp_ttg_2f81022aee` returns 200
5. **InsightFlow telemetry** — integration bridge emits lineage events
6. **Replay capability** — `/pipeline/replay/comp_ttg_2f81022aee` returns 200

# Gurukul Runtime Evidence Packet

**Product:** Gurukul (education)  
**Trace ID:** `comp_gurukul_a8535de499`  
**Classification:** live-service evidence  
**Generated:** 2026-07-07 via `run_comprehensive_live_tests.py`

## Six checklist items

1. **Prompt Runner** — instruction with `product_context: gurukul`, tasks include `create_lesson_plan`
2. **Creator Core** — blueprint with `target_product: education`
3. **Core execution** — full CET → Sarathi → Gate → BHIV chain
4. **Bucket** — `/bucket/trace/comp_gurukul_a8535de499` returns 200
5. **InsightFlow** — bridge lineage events emitted
6. **Replay** — `/pipeline/replay/comp_gurukul_a8535de499` returns 200

## Product output

Gurukul output adapter applied (`lesson_plan`, `assessment`, `metadata`).

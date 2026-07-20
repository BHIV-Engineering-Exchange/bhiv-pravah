# TTG Runtime Evidence Packet

**Product:** Tabletop Game (TTG)  
**Trace ID:** `comp_ttg_2f81022aee`  
**Classification:** live-service evidence  
**Generated:** 2026-07-07 via `run_comprehensive_live_tests.py`

## Six checklist items

1. **Prompt Runner** — instruction with `product_context: ttg`, tasks include `generate_game_blueprint`
2. **Creator Core** — blueprint envelope generated
3. **Core execution** — full CET → Sarathi → Gate → BHIV chain (A2b–A3 present)
4. **Bucket** — trace retrievable at `/bucket/trace/comp_ttg_2f81022aee`
5. **InsightFlow** — bridge emits lineage events (see `bhiv_bucket/insightflow_events.jsonl`)
6. **Replay** — `/pipeline/replay/comp_ttg_2f81022aee` returns 200

## Artifact chain

A1 `instruction_*` → A2 `blueprint_*` → A2b `contract_*` → A2c `authority_*` → A2d `gate_*` → A3 `execution_*` → A4 `result_*`

## Product output

TTG output adapter applied (`game_content`, `gameplay_structure`, `assets`).

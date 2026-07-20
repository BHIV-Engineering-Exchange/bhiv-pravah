# Generalized Product Onboarding Template

**Date:** 2026-07-07  
**Status:** Template (fifth product slot — use for next ecosystem product)

This template generalizes the four completed onboardings (TTG, TTV, Gurukul, Simulation Runtime).

## 1. Adapters

Create under `src/adapters/`:

- `{product}_input_normalizer.py` — normalize product-specific prompt JSON → plain prompt string
- `{product}_output_adapter.py` — transform BHIV execution result → product response shape

Register in `integration_bridge.py`:

```python
self.input_adapters["{product}"] = {Product}InputNormalizer()
self.output_adapters["{product}"] = {Product}OutputAdapter()
```

## 2. Prompt Runner

```bash
curl -X POST http://127.0.0.1:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "<product-specific prompt>", "product_context": "{product}"}'
```

## 3. Pipeline execute

```bash
curl -X POST http://127.0.0.1:8004/pipeline/execute \
  -H "X-API-Key: $AUTH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "<prompt>", "product_context": "{product}"}'
```

## 4. Checklist (all six items)

| # | Check | Pass criteria |
|---|-------|---------------|
| 1 | Prompt Runner | Real instruction in A1 |
| 2 | Creator Core | Blueprint `target_product` correct |
| 3 | CET → Sarathi → Gate → BHIV | Full chain in artifact_chain |
| 4 | Bucket | `/bucket/trace/{id}` returns 7 types |
| 5 | InsightFlow | Event in `/bucket/dashboard` for run |
| 6 | Replay | `/pipeline/replay/{id}` → 200 |

## 5. Evidence packet

Copy `05_evidence_packets/ttg_runtime_evidence_packet.md` structure; replace trace ID and product name.

Add entry to `05_evidence_packets/trace_manifest.json`.

## Reference traces (completed products)

| Product | Trace ID |
|---------|----------|
| TTG | `comp_ttg_434a5d3954` |
| TTV | `comp_ttv_49093259a5` |
| Gurukul | `comp_gurukul_db1cef24b5` |
| Simulation Runtime | `comp_simulation_runtime_4397308533` |

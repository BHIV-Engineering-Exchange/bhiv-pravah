# Integration Map v2

## Live pipeline (post-sprint)

```
Human Prompt
    │
    ▼
Integration Bridge (:8004)
    │
    ├─► Prompt Runner (:8003)          /generate
    ├─► Creator Core (:8000)           /creator-core/generate-blueprint
    ├─► CET (:8006)                    /contract/compile
    ├─► Sarathi (:8007)                /authority/validate
    ├─► Gate (:8008)                   /gate/evaluate  [authorize only]
    ├─► BHIV Core (:8001)              /core           [execute]
    └─► Bucket (:8005)                 /bucket/store, /bucket/trace/{id}
```

## Product adapters (wired in Integration Bridge)

| Product | Input normalizer | Output adapter |
|---|---|---|
| TTG | `ttg_input_normalizer.py` | `ttg_output_adapter.py` |
| TTV | `ttv_input_normalizer.py` | `ttv_output_adapter.py` |
| Gurukul | `gurukul_input_normalizer.py` | `gurukul_output_adapter.py` |
| Simulation Runtime | `simulation_runtime_input_normalizer.py` | `simulation_runtime_output_adapter.py` |

## Evidence

Live trace: `live_test_d61c664e3559` — full A1→A4 chain with A2b–A2d authority stages.

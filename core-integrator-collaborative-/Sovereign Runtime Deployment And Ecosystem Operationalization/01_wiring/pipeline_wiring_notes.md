# Pipeline Wiring Notes

## Implemented wiring changes

- Added CET/Sarathi/Gate URLs and HTTP calls in `integration_bridge.py`.
- Added new runtime phases:
  - Phase 2b: `POST /contract/compile` (CET)
  - Phase 2c: `POST /authority/validate` (Sarathi)
  - Phase 2d: `POST /gate/evaluate` (Gate)
- Artifact chain expanded to:
  - A1 instruction
  - A2 blueprint
  - A2b contract
  - A2c authority
  - A2d gate
  - A3 execution
  - A4 result
- Deterministic hash computation now includes CET contract payload.

## Double-execution conflict resolution

- Selected execution authority: **BHIV Core** (`Gateway.process_request`) remains the single execution engine.
- Gate service now supports authorization-only mode (`execute: false`) and returns ALLOWED/REJECTED without executing modules.
- `src/core/execution_gate.py` updated to return a gate approval object when `execute=False`.

## Pre-wiring proof

Command:
- `rg "8006|8007|8008|cet|sarathi|gate" integration_bridge.py`

Result before wiring:
- No matches (confirmed missing CET/Sarathi/Gate integration in live bridge path).

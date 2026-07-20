# Replayability Proof

## Chain evidence
- replay_demo.json and end_to_end_trace.json show the same execution_id and trace_id across all stages.
- lineage events remain append-only with deterministic hashes.

## Deterministic identifiers
- trace_id: trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R
- execution_id: exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R
- tenant_id: tenant_sampada_001
- lineage_hash: 2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88

## Reconstruction steps
1. Load execution_contract from end_to_end_trace.json.
2. Apply telemetry_events and lineage_events in sequence order.
3. Validate lineage_hash and determinism_fingerprint for replay safety.

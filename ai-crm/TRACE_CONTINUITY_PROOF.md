# Trace Continuity Proof

## Trace continuity logs
```json
{"event":"trace_continuity_ok","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","lineage_hash":"2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88","timestamp":"2026-05-29T12:00:03Z"}
{"event":"trace_continuity_ok","execution_id":"exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R","trace_id":"trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R","tenant_id":"tenant_sampada_001","lineage_hash":"2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88","timestamp":"2026-05-29T12:00:08Z","downstream":"sarathi"}
```

## Rejection examples
```json
{
  "success": false,
  "error": "trace_id_regenerated",
  "message": "Trace ID regeneration detected",
  "details": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "expected_trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "received_trace_id": "trace_9999_bad"
  }
}
{
  "success": false,
  "error": "tenant_lineage_violation",
  "message": "Tenant lineage mismatch",
  "details": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "parent_execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7Q",
    "expected_tenant_id": "tenant_sampada_001",
    "received_tenant_id": "tenant_other_004"
  }
}
{
  "success": false,
  "error": "lineage_hash_mismatch",
  "message": "Lineage hash mismatch",
  "details": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "expected_hash": "2b1b4d2fb55a3a0b2d23c7b1f3c2bba04f3d3bc6e8b1c513a07a1f5c6c7d9a88",
    "received_hash": "0000badlineagehash"
  }
}
```

## Continuity enforcement
- trace_id is immutable across the chain.
- tenant_id remains unchanged for any lineage edge.
- lineage_hash is verified before accepting the execution.
- root_trace_id must match trace_id when provided.

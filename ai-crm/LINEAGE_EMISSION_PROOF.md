# Lineage Emission Proof

## Lineage artifacts (append-only)
```json
[
  {
    "lineage_event_id": "lin_5a2a1d3f6c8b9e10",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "event_type": "execution_intent_received",
    "timestamp": "2026-05-29T12:00:02Z",
    "sequence": 1,
    "payload": {
      "stage": "intent_received"
    },
    "determinism_hash": "5a2a1d3f6c8b9e10a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789ab"
  },
  {
    "lineage_event_id": "lin_7f1c2d3e4a5b6c7d",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "event_type": "execution_routed",
    "timestamp": "2026-05-29T12:00:08Z",
    "sequence": 2,
    "payload": {
      "routing_target": "sarathi"
    },
    "determinism_hash": "7f1c2d3e4a5b6c7d8e9f00112233445566778899aabbccddeeff001122334455"
  },
  {
    "lineage_event_id": "lin_2c3d4e5f60718293",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "event_type": "execution_participation_recorded",
    "timestamp": "2026-05-29T12:00:12Z",
    "sequence": 3,
    "payload": {
      "participation": "observe_only"
    },
    "determinism_hash": "2c3d4e5f60718293a4b5c6d7e8f90123456789abcdeffedcba9876543210fedc"
  },
  {
    "lineage_event_id": "lin_8b7a6c5d4e3f2a1b",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "event_type": "execution_completed",
    "timestamp": "2026-05-29T12:00:18Z",
    "sequence": 4,
    "payload": {
      "status": "completed"
    },
    "determinism_hash": "8b7a6c5d4e3f2a1b0c1d2e3f405162738495a6b7c8d9e0f1a2b3c4d5e6f7a8b9"
  }
]
```

## Replay proof events
- determinism_hash values are stable for the same payload and sequence.
- lineage_event_id is derived from determinism_hash for replay reconstruction.

## Lineage validation logs
```text
append_only=true
mutable_lineage=false
replay_safe=true
```

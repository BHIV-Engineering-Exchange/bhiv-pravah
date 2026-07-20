# Sovereign Routing Proof

## Routing payload example (Sarathi)
```json
{
  "sarathi_version": "1.0",
  "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
  "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
  "tenant_id": "tenant_sampada_001",
  "intent_type": "approve_order",
  "source_system": "tantra",
  "target_system": {
    "system_id": "sarathi",
    "system_type": "routing"
  },
  "parameters": {
    "order_id": "ORD_44821",
    "approval_level": "ops"
  },
  "priority": 3,
  "timestamp": "2026-05-29T12:00:08Z",
  "schema_version": "1.0",
  "actor": {
    "actor_id": "user_4721",
    "actor_type": "user"
  }
}
```

## BHIV-compatible execution envelope
```json
{
  "envelope_version": "1.0",
  "execution": {
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "intent_type": "approve_order",
    "source_system": "tantra",
    "target_system": {
      "system_id": "sarathi",
      "system_type": "routing"
    },
    "parameters": {
      "order_id": "ORD_44821",
      "approval_level": "ops"
    },
    "priority": 3,
    "timestamp": "2026-05-29T12:00:08Z",
    "schema_version": "1.0",
    "actor": {
      "actor_id": "user_4721",
      "actor_type": "user"
    }
  },
  "routing": {
    "sarathi_version": "1.0",
    "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "tenant_id": "tenant_sampada_001",
    "intent_type": "approve_order",
    "source_system": "tantra",
    "target_system": {
      "system_id": "sarathi",
      "system_type": "routing"
    },
    "parameters": {
      "order_id": "ORD_44821",
      "approval_level": "ops"
    },
    "priority": 3,
    "timestamp": "2026-05-29T12:00:08Z",
    "schema_version": "1.0",
    "actor": {
      "actor_id": "user_4721",
      "actor_type": "user"
    }
  },
  "governance": {
    "gated_bridge": {
      "status": "approved",
      "attestation_id": "att_8811",
      "checked_at": "2026-05-29T12:00:06Z",
      "policy_id": "gov_exec_v1",
      "policy_version": "1.0"
    }
  },
  "provenance": {
    "recorded_by": "setu",
    "recorded_at": "2026-05-29T12:00:08Z"
  },
  "replay": {
    "idempotency_key": "idem_44821_ops",
    "sequence": 1,
    "determinism_fingerprint": "f8de74a1f0a9d27d6f3f5cf532b85e90"
  }
}
```

## Governance-safe routing validation
```json
{
  "ok": true,
  "sarathi_payload": "generated",
  "bhiv_envelope": "generated",
  "governance": {
    "gated_bridge": {
      "status": "approved",
      "attestation_id": "att_8811"
    }
  }
}
```

## Governance rejection example
```json
{
  "ok": false,
  "reason": "gated_bridge_not_approved",
  "details": "pending"
}
```

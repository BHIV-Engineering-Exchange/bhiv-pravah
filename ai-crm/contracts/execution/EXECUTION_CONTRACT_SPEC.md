# SETU Execution Contract v1

## Purpose
The execution contract is the canonical, replay-safe envelope for operational intents that SETU may observe and route without becoming an execution authority. It enforces deterministic lineage and tenant isolation while preserving trace continuity for TANTRA participation.

## Required fields
- execution_id: Immutable execution identifier for the operational chain.
- trace_id: Immutable trace identifier; MUST remain constant across the chain.
- source_system: System that emitted the intent.
- actor: Originating identity (user/service/system/agent).
- intent_type: Declarative intent label.
- target_system: Sovereign target descriptor.
- parameters: Intent payload (opaque to SETU).
- priority: Priority rank (0-9).
- timestamp: ISO-8601 timestamp of intent creation.
- schema_version: Contract version ("1.0" for v1).
- tenant_id: Tenant boundary identifier.

## Continuity invariants
- trace_id is immutable across all intents in the chain.
- trace_lineage.root_trace_id, when present, MUST equal trace_id.
- trace_lineage.parent_execution_id MUST reference a prior execution with the same trace_id and tenant_id.
- tenant_id MUST remain constant across lineage.
- lineage_hash MUST be computed from execution_id, trace_id, tenant_id, root_trace_id, parent_trace_id, parent_execution_id.

## Replay-safe metadata
- replay.idempotency_key prevents duplicate handling without mutation.
- replay.sequence ensures deterministic ordering for reconstruction.
- replay.determinism_fingerprint binds payload inputs for replay.

## Tenant-safe lineage
- tenant_id is required and immutable for any derived lineage.
- No cross-tenant reuse of trace_id or execution_id is permitted.

## Provenance metadata
- provenance.recorded_by and provenance.recorded_at capture origin of observation.
- provenance.source_signature and provenance.integrity_hash support tamper-evidence.

## Schema versioning
- schema_version MUST be set to "1.0" for this contract.
- Future versions must be additive and backward compatible or negotiated by policy.

## Minimal example
```json
{
  "execution_id": "exec_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
  "trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
  "source_system": "tantra",
  "actor": {
    "actor_id": "user_4721",
    "actor_type": "user"
  },
  "intent_type": "approve_order",
  "target_system": {
    "system_id": "sarathi"
  },
  "parameters": {
    "order_id": "ORD_44821",
    "approval_level": "ops"
  },
  "priority": 3,
  "timestamp": "2026-05-29T12:00:00Z",
  "schema_version": "1.0",
  "tenant_id": "tenant_sampada_001",
  "trace_lineage": {
    "root_trace_id": "trace_01HXZV4Z0J3R9X6M5K2Q1N8P7R",
    "lineage_hash": "b431d6f3ce1fcae5a8c4e88b34c6886936f4f8c1528d4ef2b2b8c4c5e97bb7c1"
  },
  "provenance": {
    "recorded_by": "setu",
    "recorded_at": "2026-05-29T12:00:00Z",
    "integrity_hash": "7a8f8e7ab1a9cde1a1939436dd8d3332d0d1c01b8d0b2b9c1a50c0b2cc1fcbba"
  },
  "replay": {
    "idempotency_key": "idem_44821_ops",
    "sequence": 1,
    "determinism_fingerprint": "f8de74a1f0a9d27d6f3f5cf532b85e90"
  }
}
```

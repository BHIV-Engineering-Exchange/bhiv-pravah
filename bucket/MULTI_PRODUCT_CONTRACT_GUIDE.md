
# MULTI_PRODUCT_CONTRACT_GUIDE

Version: 1.0
Date: 2026-05-20
Author: Bucket Convergence Sprint — Phase 2

Purpose
-------
This guide defines the contract and operational rules Bucket must enforce so multiple BHIV products can safely store and retrieve artifacts without coupling product logic into Bucket. It focuses on schema, metadata, validation rules, and testing approaches that preserve determinism, trace continuity, and append-only guarantees.

Design Principles
-----------------
- Domain neutrality: Bucket stores artifacts for any product without product-specific logic.
- Minimal, explicit metadata: every artifact carries a small set of required fields to support routing, traceability and validation.
- Contract enforcement: Bucket validates artifact shape and chain invariants but does not interpret product payloads.
- Backwards-compatible: changes must be additive and governed by schema_version.

Required artifact envelope
-------------------------
Bucket accepts a single artifact envelope JSON object. Required top-level fields (server validates):

- `artifact_id` (string): unique identifier supplied by the producer.
- `trace_id` (string): cross-product correlation id — MUST be preserved end-to-end.
- `timestamp_utc` (ISO8601 string): event timestamp produced by the source.
- `schema_version` (string): artifact envelope schema version (e.g., "1.0.0").
- `source_module_id` (string): producer/service id (product namespace + module), e.g. `svacs.perception`.
- `product_namespace` (string): short product token, e.g. `SVACS`, `NICAI`, `NAMAMI`.
- `artifact_type` (string): product-neutral artifact classifier, e.g. `perception`, `signal`, `ingestion`, `metadata`.
- `parent_hash` (string|null): chain parent hash (null for genesis writes). Server enforces parent linkage.
- `payload` (object): product-specific data (Bucket does not inspect semantics).

Minimal JSON envelope example
-----------------------------
{
  "artifact_id": "uuid-or-business-id",
  "trace_id": "e456c3e9-e61a-4e87-ae8e-c7c312255c31",
  "timestamp_utc": "2026-05-20T12:00:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "svacs.perception",
  "product_namespace": "SVACS",
  "artifact_type": "perception",
  "parent_hash": "<last_hash_or_null>",
  "payload": { /* product-specific object */ }
}

JSON Schema (envelope) — canonical rules
----------------------------------------
Use a minimal schema to validate structure (example excerpt):

{
  "$id": "https://example.org/schemas/artifact-envelope.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["artifact_id","trace_id","timestamp_utc","schema_version","source_module_id","product_namespace","artifact_type","payload"],
  "properties": {
    "artifact_id": {"type":"string"},
    "trace_id": {"type":"string"},
    "timestamp_utc": {"type":"string","format":"date-time"},
    "schema_version": {"type":"string"},
    "source_module_id": {"type":"string"},
    "product_namespace": {"type":"string"},
    "artifact_type": {"type":"string"},
    "parent_hash": {"type":["string","null"]},
    "payload": {"type":"object"}
  }
}

Contract enforcement rules (server side)
---------------------------------------
1. Structural validation: reject if envelope does not match the JSON schema for its `schema_version`.
2. Trace preservation: `trace_id` must be exactly stored as provided; any change is a violation.
3. Parent linkage: server computes authoritative artifact hash and validates that provided `parent_hash` matches current chain head (or accepted per-chain policy). If mismatch, return a validation error.
4. Server-computed hashes: ignore client-provided hashes — compute SHA256 over canonical serialization of the artifact envelope (deterministic ordering) plus metadata used by server.
5. Product neutrality: Bucket must not parse or apply product-specific business rules to `payload` — only structural validation is allowed.
6. Schema versioning: support multiple envelope schema versions with backward-compatibility; changes must be additive.

Product namespaces and metadata guidance
--------------------------------------
- `product_namespace`: uppercase token identifying product (single word). Use for ACLs, telemetry tagging, and downstream routing.
- `source_module_id`: dotted module path within the product, e.g., `nicai.collector`, `namami.mapper`.
- `artifact_type`: normalized set of product-neutral types. Maintain a registry (in governance) of allowed `artifact_type` values.

Examples (SVACS / NICAI / Namami)
--------------------------------

1) SVACS perception artifact (example):

{
  "artifact_id":"4ac417c4-...",
  "trace_id":"e456c3e9-...",
  "timestamp_utc":"2026-05-07T06:43:44Z",
  "schema_version":"1.0.0",
  "source_module_id":"svacs.perception",
  "product_namespace":"SVACS",
  "artifact_type":"perception",
  "parent_hash":"f54aac459e...",
  "payload": { "vessel_type":"cargo","confidence_score":0.9073 }
}

2) NICAI ingestion artifact (example):

{
  "artifact_id":"nicai-20260520-0001",
  "trace_id":"nicai-trace-0001",
  "timestamp_utc":"2026-05-20T10:00:00Z",
  "schema_version":"1.0.0",
  "source_module_id":"nicai.collector",
  "product_namespace":"NICAI",
  "artifact_type":"ingestion",
  "parent_hash": null,
  "payload": { "sensor": "lidar", "data": { /* ... */ } }
}

3) Namami / Marine artifact (example):

{
  "artifact_id":"namami-0001",
  "trace_id":"shared-trace-123",
  "timestamp_utc":"2026-05-20T10:12:00Z",
  "schema_version":"1.0.0",
  "source_module_id":"namami.mapper",
  "product_namespace":"NAMAMI",
  "artifact_type":"metadata",
  "parent_hash":"<last_hash>",
  "payload": { "region":"ganga","measurements":{ /* ... */ } }
}

Validation and governance
-------------------------
- Governance registry: maintain a small `artifact_policy` registry (in repo or governance service) listing allowed `product_namespace` tokens, approved `artifact_type`s, and accepted `schema_version`s.
- Validation endpoint: use existing `/governance/validate-schema` and `/governance/validate-artifact` to validate envelopes prior to write.
- Admission control: for protected flows, require `requester_id` and integration approval; Bucket returns a structured error with violation reasons on rejection.

Testing strategy (CI + integration)
----------------------------------
1. Unit tests: schema validation unit tests per `schema_version` with positive and negative cases.
2. Deterministic hashing tests: canonical-serialize a fixture envelope, compute server hash, store it, and assert read-back hash matches stored hash.
3. Trace continuity test: produce an artifact with a `trace_id`, write follow-up artifacts referencing same `trace_id`, read back and assert `trace_id` equality and lineage.
4. Integration smoke: pipeline test that simulates a product flow (SVACS): produce perception artifact → POST to `/bucket/artifact` → GET `/bucket/artifact/{artifact_id}` → validate chain and hash equality.

Replay and audit readiness
-------------------------
- Ensure server stores sufficient metadata for replay (timestamp, source_module_id, artifact_id, trace_id, parent_hash).
- Add an automated `validate-replay` runner that re-computes chain hash over `artifact_log.jsonl` and asserts the chain matches stored `chain_state.json`.

Rollback and compatibility
-------------------------
- Schema evolution must be additive. If removal or incompatible changes are required, create a migration plan and version the schema.
- Never accept a client-provided `hash` as authoritative. Server must compute and publish authoritative `hash` in write responses.

Operational recommendations
-------------------------
- Secrets: remove active credentials from `.env.example`. Use Render/CI environment variables for production secrets and rotate any leaked credentials.
- CORS: tighten `allow_origins` to approved frontends when moving to production.
- Access control: use `requester_id` + integration approvals for writes from other products.

Deliverables for Phase 2
------------------------
- This guide (`MULTI_PRODUCT_CONTRACT_GUIDE.md`) — present file.
- Example artifact fixtures for SVACS, NICAI, Namami in `docs/fixtures/` (produce as next step).
- CI test definitions for schema validation and hashing (add pytest cases referencing fixture files).

Next steps (practical)
----------------------
1. Review and accept this guide with product stakeholders (SVACS, NICAI, Namami).  
2. Create `docs/fixtures/` with 3 example envelopes (SVACS, NICAI, Namami).  
3. Add unit tests that verify deterministic hashing and trace continuity.  
4. Run integration smoke test against staging/deployed instance (coordinate with Testing & SVACS teams).

Restrictions reminder
---------------------
Bucket MUST NOT contain product business logic — all validations must be schema/contract driven and generic.

End of guide.

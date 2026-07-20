# INTEGRATION_MAP

Date: 2026-05-27

Overview
- This map lists systems that produce artifacts into Bucket (upstream) and systems that consume Bucket artifacts or events (downstream). For each, include integration surface, expected envelope placement, and contact.

Upstream (Producers)
- SVACS (Signal / Perception)
  - Endpoint: POST /bucket/artifact
  - Envelope expectations: `artifact_id`, `timestamp_utc`, `schema_version`, `source_module_id`, `artifact_type`, `parent_hash`, `payload` (payload contains product-specific fields and may include `trace_id`).
  - Contact: SVACS Team

- NICAI (AI models)
  - Endpoint: POST /bucket/artifact
  - Envelope expectations: same as contract; prefer `trace_id` top-level when deployed contract permits.
  - Contact: NICAI integration lead

- Sarathi (Enforcement)
  - Endpoint: POST /bucket/artifact
  - Envelope: BHIV v1.0.0 (`product_namespace: SARATHI`, `source_module_id: sarathi.enforcement_adapter`, `artifact_type: enforcement_decision`)
  - Integration guide: `SARATHI_BUCKET_INTEGRATION.md`
  - Notes: Sarathi owns hash verification and receipt posting; Bucket is append-only store + authority hash
  - Contact: Sarathi team / Siddhesh Narkar (Bucket)

- Namami Gange / Marine (Telemetry)
  - Endpoint: POST /bucket/artifact
  - Envelope expectations: ingestion/perception artifact types; domain metadata in `payload`.
  - Contact: Marine integration owner

- Agents & internal producers (AgentRunner, workflows)
  - Endpoint: POST /bucket/artifact
  - Use `source_module_id` to identify origin; supply `trace_id` if available.

Downstream (Consumers)
- InsightFlow (Nupur)
  - Subscription: audit channel or event bus; consume `artifact.created`, `artifact.rejected`, `artifact.playback` events.
  - Expected telemetry: `hash`, `parent_hash`, `artifact_type`, `trace_id` (payload or envelope).

- BHIV Core / Governance
  - Reads via GET /bucket/artifact/{id} and trace queries; validates compliance and gate decisions.

- Monitoring & Audit systems
  - Subscribe to audit middleware; alert on `artifact.rejected` and `verification_result: failed`.

Integration notes
- Authentication: integrate via existing requester identity patterns (use `source_module_id` and constitutional validation channels). Core and privileged operations require governance gate allowances.
- Contract versioning: use `schema_version` for forward compatibility; changes must be additive and gated.
- Test harness: use staging with `BHIV_ARTIFACT_PATH` override to avoid production side-effects.

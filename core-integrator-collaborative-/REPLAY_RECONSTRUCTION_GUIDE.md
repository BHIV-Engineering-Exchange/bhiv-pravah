# Replay & Reconstruction Guide

This document explains how replay and artifact reconstruction work in the BHIV Core-Integrator system.

## Artifact chain

The artifact chain is the sequence of digital artifacts created during a pipeline execution.
The repository uses the following artifact mapping:

- **A1_instruction** — instruction artifact from Prompt Runner
- **A2_blueprint** — blueprint artifact from Creator Core
- **A3_execution** — execution result artifact from BHIV Core
- **A4_result** — final result artifact from the Integration Bridge

The chain is stored in the BHIV Bucket by `trace_id`.

## Storage model

`bhiv_bucket.py` stores artifacts in an append-only local file system structure:

- `bhiv_bucket/instructions/`
- `bhiv_bucket/blueprints/`
- `bhiv_bucket/executions/`
- `bhiv_bucket/results/`
- `bhiv_bucket/traces/`

Each trace file contains:

- `trace_id`
- `created_at`
- `artifact_ids`
- `artifact_types`
- `updated_at`

## Replay modes

### Bucket trace replay

- Primary replay mode uses the bucket trace file.
- The Integration Bridge calls `GET /bucket/trace/{trace_id}`.
- The bucket returns all artifacts associated with that trace.

### Local fallback replay

- If the bucket replay fails, the Integration Bridge may fall back to local artifact graph data stored in memory.
- This fallback is not a durable or distributed replay mode.

### Instruction replay

- BHIV Core exposes `/replay/{instruction_id}` and `/replay/validate/{instruction_id}`.
- These endpoints use the core's internal replay engine if it is initialized.

## Reconstruction flow

1. Start with a `trace_id` or `instruction_id`.
2. Retrieve trace file from `bhiv_bucket/traces/{trace_id}.json`.
3. Retrieve artifacts by ID from the appropriate artifact directories.
4. Reconstruct the chain in order: A1 → A2 → A3 → A4.
5. Validate deterministic hashes if available.

## Determinism validation

The system uses deterministic hash computation in the Integration Bridge:

- `_compute_hash` combines instruction, blueprint, and execution payloads
- SHA-256 is used and truncated to 16 hex characters

Validation works by comparing stored/replayed pipeline hashes against a rerun hash.

## Hash validation

The full TANTRA test harness validates the hash chain by:

- computing `artifact_hash` for each artifact
- verifying `parent_hash` relationships
- comparing the final replay hash to the original output

This is implemented in `full_tantra_flow_test.py`.

## Session replay

Session replay is supported at the BHIV Core layer through the core replay endpoints.

### Key endpoints

- `POST /replay/{instruction_id}` — replay instruction execution
- `GET /replay/validate/{instruction_id}` — validate replay capability
- `GET /replay/statistics` — replay system statistics

## Distributed replay

Distributed replay is not fully implemented as a runtime feature in this repository.
The system reserves replay validation proof and distributed logs under:

- `audit_packets/replay_logs/`

This folder is the intended destination for distributed replay records and audit proofs.

## Known replay limitations

- Bucket replay is not a full re-execution; it reconstructs stored artifacts only.
- Prompt Runner remains a stub: replaying a prompt is not equivalent to replaying a full production prompt generator.
- CET/Sarathi/Gate replay is only simulated in `full_tantra_flow_test.py`.
- Distributed replay is architected but not deployed.
- Trace IDs are generated locally and may not be globally unique outside the local environment.

## Expected replay outputs

A successful trace replay should return:

```json
{
  "status": "success",
  "trace_id": "trace_<id>",
  "artifact_chain": [ ... ],
  "replay_timestamp": "ISO8601",
  "source": "bucket"
}
```

A successful instruction replay should return a `CoreResponse` structure with:

- `status`
- `result`
- `message`

## Reconstruction procedure for a new developer

1. Start Bucket and ensure trace files exist.
2. Query `GET /bucket/trace/{trace_id}`.
3. Verify that `artifact_ids` includes instruction, blueprint, execution, and result.
4. Fetch each artifact via `/bucket/artifact/{artifact_id}`.
5. Compare `trace_id` values across artifacts.
6. Recompute hashes if needed using local hash utilities.
7. Confirm that the final result payload matches the original pipeline output.

## Practical notes

- Use `bhiv_bucket.py` only for artifact storage and retrieval; do not use it as a reconstruction engine.
- If artifacts cannot be found in the bucket, inspect `bhiv_bucket/traces/` for missing references.
- For proof of deterministic replay, rely on `full_tantra_flow_test.py`.
- Preserve the append-only principle: do not modify stored artifact JSON files manually.

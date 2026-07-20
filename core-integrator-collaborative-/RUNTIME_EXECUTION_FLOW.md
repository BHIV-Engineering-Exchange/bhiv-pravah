# Runtime Execution Flow

This document explains the runtime flow for each stage of the BHIV pipeline.
Every stage is defined in sequence from human prompt to replay validation.

## Human Prompt

**Entry point**: user sends a prompt to the Integration Bridge or Prompt Runner.

**Input**
- natural language prompt text
- expected JSON payload for `POST /pipeline/execute` on Integration Bridge:
```json
{
  "prompt": "<user prompt text>"
}
```

**Output**
- user prompt passed to Prompt Runner
- `trace_id` generation begins in Integration Bridge

**Failure conditions**
- missing prompt field
- invalid JSON
- Integration Bridge unreachable

**Validation points**
- minimal syntax validation by `FastAPI`
- health of Integration Bridge via `/pipeline/health`

**Trace behavior**
- `trace_id` is created in Integration Bridge as `trace_<uuid>`
- trace_id is attached to all artifacts

**Artifact creation**
- no artifact yet; this is the pipeline entry.

---

## Prompt Runner

**Role**: Convert the prompt into a structured instruction payload.

**Source**: `prompt-runner01/run_server.py` (FastAPI)

**Input**
- HTTP POST to `/generate`
- payload: `{"prompt": "...", "origin": "creator"}`

**Output**
- structured instruction JSON with extracted intent, module, tasks, and product_context

**Schema**
```json
{
  "prompt": "string",
  "origin": "string",
  "intent": "string",
  "module": "string",
  "tasks": ["string"],
  "output_format": "string",
  "product_context": "string"
}
```

**Failure conditions**
- prompt runner not running
- invalid request payload
- non-200 response to `/generate`

**Validation points**
- `integration_bridge.py` checks response status and raises if `response.raise_for_status()` fails
- `test_services.py` checks `/health`

**Trace behavior**
- instruction artifact becomes A1 in the chain
- stored with `trace_id`

**Artifact creation**
- `ArtifactGraph.create_chain` stores the initial instruction artifact in BHIV Bucket

---

## Creator Core

**Role**: Generate blueprint envelopes from prompt instructions.

**Source**: `creator-core/Core-Integrator-Sprint-1.1/main.py`

**Input**
- HTTP POST to `/creator-core/generate-blueprint`
- payload: instruction JSON from Prompt Runner

**Output**
- `BlueprintEnvelope` object
- blueprint payload and metadata

**Schema**
```json
{
  "instruction_id": "string",
  "origin": "creator_core",
  "intent_type": "string",
  "target_product": "string",
  "payload": { ... },
  "schema_version": "1.0.0",
  "timestamp": "ISO8601"
}
```

**Failure conditions**
- invalid instruction schema
- Creator Core service down
- blueprint generation exception

**Validation points**
- `PromptRunnerInstruction.model_validate` in `creator_core_engine/service.py`
- `BlueprintPayload.model_validate` in `creator_core_engine/generator.py`
- local logging and telemetry emission

**Trace behavior**
- blueprint stored as A2 artifact in BHIV Bucket
- parent trace_id is preserved

**Artifact creation**
- `CreatorCoreService.generate_blueprint()` stores blueprint via `LocalBucketStore.store_blueprint`

---

## BHIV Core

**Role**: Execute blueprints and produce results.

**Source**: `main.py`

**Input**
- HTTP POST to `/core`
- payload: mapped request containing blueprint data and execution intent

**Output**
- `CoreResponse` containing execution status and result data

**Schema**
```json
{
  "status": "string",
  "result": { ... },
  "message": "string"
}
```

**Failure conditions**
- invalid core request
- missing or invalid user identity
- internal execution exceptions
- external dependency failures (database, noopur, video service)

**Validation points**
- `validate_user_request()` in `src/utils/security_hardening.py`
- `validate_config()` during startup in `config/config.py`
- response structure validation in `/core`

**Trace behavior**
- trace continues as artifact A3 when Integration Bridge stores execution result

**Artifact creation**
- execution artifact is stored by `ArtifactGraph.update_artifact` in Integration Bridge

---

## CET

**Role**: Generate a contract that makes blueprint execution deterministic and replay-safe.

**Source**: live service `cet_service.py`, invoked by `integration_bridge.py` via `POST /contract/compile`

**Input**
- blueprint artifact payload

**Output**
- contract artifact with execution plan and constraints

**Schema**
- no canonical file; the test harness uses a contract payload with `contract_id`, `execution_plan`, and `constraints`

**Failure conditions**
- missing contract fields
- contract hash mismatch

**Validation points**
- contract structure checks in the test harness

**Trace behavior**
- contract artifact is linked to the same `trace_id`

**Artifact creation**
- A3/A4 contract in test flow, not in live runtime

---

## Sarathi

**Role**: Authority validation for contract approval.

**Source**: live service `sarathi_service.py`, invoked by `integration_bridge.py` via `POST /authority/validate`

**Output**
- authority decision object

**Failure conditions**
- contract invalidation
- authority decision failure

**Validation points**
- boolean validation checks in Sarathi stage

**Trace behavior**
- decision maintains same `trace_id`

---

## Execution Gate

**Role**: Convert authority decisions into execution permission.

**Source**: live service `gate_service.py`, invoked by `integration_bridge.py` via `POST /gate/evaluate`

**Output**
- gate result that determines execution start

**Failure conditions**
- gate rejects the flow
- missing required contract metadata

**Validation points**
- gate readiness checks in the test harness

---

## Execution

**Role**: Run the approved execution plan and produce execution artifacts.

**Input**
- gate-approved execution payload

**Output**
- execution payload and result

**Failure conditions**
- execution engine errors
- missing blueprint payload

**Validation points**
- successful `POST /core` response

---

## Bucket

**Role**: Store every artifact in an append-only, trace-indexed bucket.

**Source**: `bhiv_bucket.py`

**Input**
- artifact store request payload

**Output**
- storage confirmation with `artifact_id`, path, timestamp

**Schemas**
```json
{
  "artifact_id": "string",
  "artifact_type": "instruction|blueprint|execution|result",
  "trace_id": "string",
  "timestamp": "ISO8601",
  "data": { ... },
  "metadata": {
    "size_bytes": "number",
    "schema_version": "string"
  }
}
```

**Failure conditions**
- disk write failure
- missing trace index
- already existing artifact file path

**Validation points**
- `BHIVBucket.store_artifact()` writes JSON files with consistent metadata
- `retrieve_by_trace()` verifies trace index consistency

**Trace behavior**
- artifacts are grouped by `trace_id`
- the trace file maintains `artifact_ids` and type mapping

**Artifact creation**
- A1 through A4 artifacts are persisted in directories by type

---

## InsightFlow

**Role**: Emit telemetry events for Creator Core operations.

**Source**: `creator-core/Core-Integrator-Sprint-1.1/creator_core_engine/telemetry.py`

**Input**
- telemetry event data from Creator Core

**Output**
- newline-delimited JSON events written to telemetry database path

**Failure conditions**
- file write errors
- missing telemetry directory

**Validation points**
- telemetry file existence and event format

---

## Replay

**Role**: Validate and replay artifact chains from stored traces.

**Source**: `integration_bridge.py`, `main.py`, `full_tantra_flow_test.py`

**Input**
- `trace_id` or `instruction_id`

**Output**
- stored artifacts and replay status

**Failure conditions**
- missing trace artifacts
- bucket unreachable
- incompatible artifact chain

**Validation points**
- `integration_bridge.py` bucket trace retrieval
- hash match check in `full_tantra_flow_test.py`

**Artifact creation**
- replay proof artifacts are created by test harness

---

## Failure and validation summary

### Failure conditions by stage

- Prompt Runner: service offline, invalid prompt input.
- Creator Core: invalid instruction schema, blueprint generation error.
- BHIV Core: security validation failure, execution failure.
- Bucket: storage failure, trace index mismatch.
- Replay: trace not found, hash mismatch.

### Validation points

- `test_services.py` performs service-level health checks.
- `full_tantra_flow_test.py` validates end-to-end trace continuity and hash determinism.
- `config/config.py` performs config validation at BHIV Core startup.
- `creator_core_engine/service.py` validates instruction and blueprint models.
- `integration_bridge.py` validates HTTP responses from upstream services.

### Trace behavior

- Trace ID is created once at pipeline start in Integration Bridge.
- Every artifact stores the same `trace_id`.
- Bucket trace files link artifacts into a single chain.
- Replay uses `trace_id` as the primary reconstruction key.

### Artifact creation behavior

- Instruction: A1 artifact created first.
- Blueprint: A2 artifact created by Creator Core.
- Execution: A3 artifact created after BHIV Core execution.
- Result: A4 artifact created as final pipeline output.
- Trace file: updated after each artifact is stored.

## Runtime notes

- The current codebase is designed for local execution.
- Service-to-service communication is HTTP-based.
- The pipeline uses fixed ports and environment variables configured in `config/services.yml` and `.env` files.

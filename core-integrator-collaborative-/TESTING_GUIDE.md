# Testing & Validation Guide

## Purpose

This guide explains how to test the BHIV Core-Integrator system, what to test, and how to validate replay and integration behavior.

## How to test

### 1. Service health checks

Run:
```bash
python test_services.py
```

This verifies:
- Prompt Runner health
- Creator Core availability
- BHIV Core availability
- Integration Bridge health
- BHIV Bucket health

### 2. Startup validation

Use:
```bash
python start_all.py
```

Expected behavior:
- all services start in dependency order
- health checks pass for each service
- service URLs are displayed

### 3. End-to-end validation

Run the full TANTRA flow test:
```bash
python full_tantra_flow_test.py
```

This validates:
- trace continuity
- deterministic hash generation
- replay safety
- bucket artifact storage

### 4. Creator Core unit tests

Run:
```bash
python -m pytest creator-core/Core-Integrator-Sprint-1.1/tests
```

These tests cover Creator Core service logic, blueprint generation, and data model validation.

### 5. Manual pipeline execution

Use the Integration Bridge endpoint:
```bash
curl -X POST http://127.0.0.1:8004/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a residential building for Mumbai"}'
```

Expected output:
- pipeline status `success`
- `trace_id`
- artifact chain containing A1-A4
- `deterministic_hash`

## What to test

### Service availability

- `Prompt Runner` responds at `/health`
- `Creator Core` responds at `/`
- `BHIV Core` responds at `/`
- `Integration Bridge` responds at `/pipeline/health`
- `BHIV Bucket` responds at `/bucket/stats`

### Pipeline execution

- end-to-end prompt execution through Integration Bridge
- Artifact chain creation in Bucket
- trace ID consistency across artifacts
- final result payload shape and `pipeline_status`

### Replay validation

- replay trace with `GET /pipeline/replay/{trace_id}`
- verify replay returns same artifact chain
- confirm replay status and source
- if available, use BHIV Core `/replay/{instruction_id}` and `/replay/validate/{instruction_id}`

### Configuration validation

- `config/config.py` validates BHIV Core environment
- `config/services.yml` defines service topology and ports
- `.env` and `.env.integration_bridge` values match runtime services

## Expected outputs

### Health check outputs

- `status` should indicate healthy or ok
- health endpoints should return HTTP 200

### Full pipeline output

The gateway should return a JSON payload containing:
- `status`: `success`
- `trace_id`
- `artifact_chain`
- `pipeline_result`
- `timestamp`

### Replay output

Replay should return:
- `status`: `success`
- `trace_id`
- `artifact_chain`
- `replay_timestamp`
- `source`: `bucket` or `local`

## Known failure modes

- **Service unreachable**: a service is not running on the configured host/port
- **Invalid prompt shape**: Prompt Runner or Integration Bridge rejects unexpected JSON
- **Bucket write failure**: disk permission issues or invalid `STORAGE_PATH`
- **Creator Core schema failure**: invalid instruction payload into `PromptRunnerInstruction`
- **BHIV Core execution failure**: invalid core request or missing user validation
- **Replay failure**: missing artifacts or missing trace file

## Replay validation

Replay validation depends on:
- the bucket trace index
- artifact persistence in the bucket
- deterministic hash generation in `integration_bridge.py`

Validation procedure:
1. Execute a pipeline and note `trace_id`
2. Call `GET /pipeline/replay/{trace_id}`
3. Verify artifacts returned match stored bucket files
4. Compare hashes if available

## Distributed validation

This repository includes artifacts and audit directories for distributed validation, but the live distributed replay system is not fully implemented.

Key files:
- `audit_packets/replay_logs/README.md`
- `full_tantra_flow_test.py`

## Integration validation

Validate that services can call each other successfully:
- Integration Bridge → Prompt Runner
- Integration Bridge → Creator Core
- Integration Bridge → BHIV Core
- Integration Bridge → Bucket

Also validate:
- Creator Core telemetry emission to InsightFlow
- BHIV Core replay endpoints
- Bucket artifact retrieval by `artifact_id` and `trace_id`

## Constitutional validation

The major constitutional validation points in this repository are:
- deterministic hash proof generation
- append-only artifact storage
- trace continuity across A1-A4
- replay-safe contract assumptions in `full_tantra_flow_test.py`

When testing, ensure these are preserved and not bypassed by direct artifact mutation.

## Testing commands summary

- `python test_services.py`
- `python start_all.py`
- `python deploy_and_test.py`
- `python full_tantra_flow_test.py`
- `python -m pytest creator-core/Core-Integrator-Sprint-1.1/tests`

## Success criteria

A successful test pass includes:
- all services available
- end-to-end execution completes successfully
- artifacts are persisted in `bhiv_bucket/`
- replay returns consistent artifact chains
- no fatal errors in the logs

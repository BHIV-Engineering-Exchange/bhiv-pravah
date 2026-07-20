# Ecosystem Architecture Audit

## Summary

This audit captures the actual architecture present in the current repository and maps it against the declared TANTRA pipeline. The current repo implements a core integration bridge that orchestrates a limited pipeline, while some conceptual components such as CET, Sarathi, Gate, and InsightFlow appear in simulation/test code rather than in the live orchestration path.

## Actual Runtime Architecture

- **Integration Bridge**: `integration_bridge_v2.py`
  - Orchestrates the pipeline at runtime.
  - Calls `Prompt Runner`, `Creator Core`, `BHIV Core`, and `Bucket` in sequence.
  - Stores artifacts as A1-A4 in the bucket.
  - Performs health checks on all four services.

- **Prompt Runner**: external service expected at `PROMPT_RUNNER_URL` (default `http://127.0.0.1:8003`)
  - The repo currently assumes a separate prompt runner service.
  - Orchestrator references `prompt-runner01/run_server.py` as a local runner stub.

- **Creator Core**: `creator-core/Core-Integrator-Sprint-1.1/main.py`
  - Exposes `/creator-core/generate-blueprint`.
  - Implements internal gateway, history/context APIs, and blueprint generation.

- **BHIV Core**: `main.py`
  - Exposes `/core` for request execution.
  - Contains core gateway, security middleware, memory/db, and health diagnostics.

- **Bucket**: `bhiv_bucket.py`
  - Exposes artifact storage and retrieval endpoints.
  - Used by the bridge to store artifact data for trace reconstruction.

## Declared vs Actual Components

- Declared pipeline includes: `Prompt Runner`, `Creator Core`, `Core Coordination`, `CET`, `Sarathi`, `Gate`, `Execution Layer`, `Bucket`, `InsightFlow`.
- Actual live bridge pipeline currently implements:
  1. Prompt Runner
  2. Creator Core
  3. BHIV Core
  4. Bucket
- `CET`, `Sarathi`, `Gate`, `InsightFlow`, and `Core Coordination` appear to be represented only in test/simulation code (`full_tantra_flow_test.py`) or conceptual documentation.

## Key Observations

- **Service URL configuration** is environment-driven through `config/service_urls.py`.
- **Trace continuity** is built with `trace_id` values in the bridge and artifact graph.
- **Deterministic hash** is computed in `integration_bridge_v2.py` using JSON dumped args.
- **Artifact chain** is explicit for A1-A4, but the repo does not currently include artifact types for contract or gate decisions in the live bridge.

## Immediate risk areas

- There is a potential architecture mismatch between the declared constitutional pipeline and the deployed path.
- The `Prompt Runner` service may be external or stubbed, so a live audit must confirm its actual implementation separately.
- The bridge’s artifact storage uses best-effort bucket writes and will continue even if bucket storage fails.

## Next validation steps

1. Verify actual prompt runner implementation or service contract.
2. Confirm whether `CET`, `Sarathi`, and `Gate` exist in other repo branches or external services.
3. Validate that trace and artifact IDs remain consistent across live execution and replay.
4. Review health-check and failure-handling behavior in the bridge and core services.

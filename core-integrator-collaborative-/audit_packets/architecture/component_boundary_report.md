# Component Boundary Report

## Components included in the current repository

- `integration_bridge_v2.py`
- `creator-core/Core-Integrator-Sprint-1.1/main.py`
- `main.py` (BHIV Core)
- `bhiv_bucket.py`
- `deploy_and_test.py`
- `config/service_urls.py`

## Boundary mapping

### Integration Bridge
- Responsibility: orchestrate full pipeline, call external services, manage artifact chain.
- Boundaries:
  - Input: user prompt
  - Outputs: final pipeline result, trace_id, stored artifacts
  - External calls: Prompt Runner, Creator Core, BHIV Core, Bucket
  - Not responsible for: low-level execution logic, internal contract enforcement, or downstream module behavior.

### Prompt Runner
- Responsibility: convert natural language prompt into structured instruction.
- Boundaries:
  - Input: `prompt`
  - Output: instruction payload
  - External to this repo: the service may be provided outside the repository.

### Creator Core
- Responsibility: accept instruction and generate a blueprint envelope.
- Boundaries:
  - Input: instruction JSON
  - Output: blueprint JSON
  - Exposed endpoint: `/creator-core/generate-blueprint`

### BHIV Core
- Responsibility: execute the blueprint and produce execution results.
- Boundaries:
  - Input: core execution request JSON
  - Output: execution response JSON
  - Includes internal gateway, security validation, and context/history APIs.

### Bucket
- Responsibility: store artifact objects and expose trace retrieval.
- Boundaries:
  - Input: artifact storage requests
  - Output: artifact IDs and trace retrieval data
  - Critical for replay and trace continuity.

## Authority boundaries observed

- The repository enforces service separation via HTTP service endpoints.
- The bridge is an orchestrator, not an execution engine.
- The BHIV Core contains internal validation and security middleware, marking it as the execution authority.
- The Creator Core is limited to blueprint generation.

## Potential boundary leakage

- `integration_bridge_v2.py` builds a `core_request` payload with `module`, `intent`, and `user_id`; this suggests the bridge can influence execution semantics beyond simple orchestration.
- The `full_tantra_flow_test.py` conceptual model includes CET and Sarathi as separate stages, but those stages do not map to actual live service calls in the current bridge code.

## Recommendations for audit progression

- Validate whether the repo intentionally separates constitutional enforcement into a simulation/test layer rather than production runtime.
- Document any non-mapped components as possible hidden or external runtime paths.

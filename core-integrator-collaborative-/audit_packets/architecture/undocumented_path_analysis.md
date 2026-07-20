# Undocumented Path Analysis

## Purpose
Identify runtime or architectural paths that exist in code but are not part of the declared constitutional pipeline, and assess whether they represent hidden execution or governance flow.

## Findings

- `integration_bridge_v2.py` declares a strict four-stage execution path: Prompt Runner → Creator Core → BHIV Core → Bucket.
- `full_tantra_flow_test.py` defines a broader TANTRA flow with additional stages: CET, Sarathi, Gate, Execution, Bucket, InsightFlow, Replay.
- These additional stages currently appear to be implemented only as simulation/test logic, not as real runtime communication paths between services.

## Potential undocumented paths

- **Prompt Runner**: actual service endpoint in repo is assumed external, but orchestrator expects `prompt-runner01/run_server.py` locally. This may indicate a hidden runtime dependency or incomplete repository packaging.
- **CET/Sarathi/Gate**: not present in live orchestration path; could be an undocumented external service or a conceptual layer omitted from production code.
- **InsightFlow**: appears as telemetry/testing stage, but no direct live integration is visible in the bridge or core endpoints.

## Impact

- The declared architecture is broader than the implemented runtime path, which must be documented and reconciled.
- This mismatch creates risk for audit completeness: a live audit must confirm whether CET/Sarathi/Gate are external services or missing from this repository.
- The current repo appears to support a core demonstrator pipeline rather than the full constitutional runtime graph.

## Recommended next validation steps

1. Check if any external service definitions or deployment manifests reference CET/Sarathi/Gate.
2. Validate whether the live prompt runner is provided by a separate repository or runtime environment.
3. Inspect service discovery/configuration for hidden URL mappings or plugin hooks.

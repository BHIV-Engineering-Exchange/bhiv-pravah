# KESHAV Service Contract

## Overview
This document specifies the rigorous service contract provided by the KESHAV Dependency Intelligence capability to its ecosystem consumers. 

## API Contracts

### Endpoints
* **`POST /analyze`**: Executes the complete TANTRA-compliant deterministic pipeline and returns the KESHAV output contract.
* **`GET /health`**: Provides a standard liveness check for the capability container.

## Data Contracts

### Input Contract
KESHAV expects a JSON payload matching the TANTRA input specification.

```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "tasks": [
    { "task_id": "T1", "depends_on": [] },
    { "task_id": "T2", "depends_on": ["T1"] }
  ],
  "constraint_results": [
    { "task_id": "T1", "is_valid": false, "unsatisfied_dependencies": [] },
    { "task_id": "T2", "is_valid": false, "unsatisfied_dependencies": ["T1"] }
  ],
  "propagation_results": [
    { "task_id": "T1", "affected_tasks": ["T2"], "impact_score": 10 },
    { "task_id": "T2", "affected_tasks": [],     "impact_score": 4  }
  ]
}
```

### Output Contract (Success - 200 OK)
On successful analysis, KESHAV guarantees an exact output structure holding diagnostic intelligence.

```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "root_cause": "T1",
  "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
  "impact_score": 10,
  "severity": "HIGH",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Failure Contract (Error - 400 Bad Request)
If the input violates the required structural schema, a deterministic failure payload is returned.

```json
{ 
  "status": "FAIL", 
  "reason": "INVALID_INPUT_CONTRACT", 
  "trace_id": "" 
}
```

## Lifecycle & Versioning

### Versioning Strategy
KESHAV adheres to strict **Semantic Versioning (SemVer)** (MAJOR.MINOR.PATCH):
* **MAJOR**: Breaking changes to the input/output schemas or authority boundaries.
* **MINOR**: Non-breaking capability additions (e.g., new intelligence heuristics that do not modify output shape).
* **PATCH**: Internal deterministic bug fixes and performance optimizations.

### Compatibility Policy
* KESHAV guarantees **backward compatibility** across minor and patch versions.
* Output schemas are append-only. Existing consumers will not break due to omitted fields across compatible versions.

### Breaking Change Policy
* Any breaking change requires a new MAJOR version.
* The previous MAJOR version must be supported throughout a full deprecation window (as mandated by BHIV governance) to allow consumers like Sarathi or SETU to migrate.
* Breaking changes must undergo a fresh Governance Committee (GC) boundary audit.

## Execution Guarantees

### Replay Guarantees
* **10/10 Identical Outputs**: KESHAV guarantees that providing the identical input payload will result in the exact identical output payload, across time, infrastructure, and execution contexts.
* **Trace Continuity**: The `trace_id` provided in the Input Contract is guaranteed to remain fully intact and unmodified in the Output Contract.

### Determinism Guarantees
* **Zero Entropy**: KESHAV relies on no external hidden state, randomization, or side-effects.
* **Fail-Closed Corruption Resistance**: Any unhandled or corrupted state forces a deterministic fallback failure rather than non-deterministic output generation.

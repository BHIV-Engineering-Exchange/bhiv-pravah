# KESHAV CANONICAL ARCHITECTURE
## Phase 2 — Architecture Consolidation

**Service:** KESHAV-4 Propagation Engine
**Canonical Location:** `C:\blackhole\KESHAV-4`
**Owner:** Rajaryan
**Date:** 2026-05-26

---

## For a Fresh Incoming Developer

KESHAV is a **stateless, deterministic dependency propagation engine**. It answers one question:

> "Given a blocked task and a dependency graph, what is the downstream blast radius?"

It takes a graph and a blocked node, runs a Breadth-First Search, and returns a list of impacted tasks with a severity score. That's it. No network calls. No state. No side effects. Pure computation.

---

## Entry Point

```
app/engine.py → PropagationEngine.compute_dependency_output(input_data: dict) → dict
```

This is the **only** public entry point. Everything else is internal.

---

## Execution Chain

```
Input dict ──► PropagationInput.model_validate()  ──► Graph Integrity Checks
                                                            │
                                                   root_cause in graph?
                                                   blocked_task_id in graph?
                                                            │
                                                            ▼
                                                 compute_downstream_path()
                                                   (Deterministic BFS)
                                                            │
                                                            ▼
                                                  Severity Classification
                                                   LOW  (impact < 3)
                                                   MEDIUM (3 ≤ impact < 10)
                                                   HIGH (impact ≥ 10)
                                                            │
                                                            ▼
                                                  Resolution Signal Generation
                                                   UNBLOCK_DEPENDENCY:{root_cause}
                                                            │
                                                            ▼
                                               PropagationOutput.model_dump()
                                                            │
                                                            ▼
                                                      Return dict
```

### Step-by-step:

1. **Input validation** — Pydantic `PropagationInput.model_validate(input_data)`. Fails closed with `PropagationContractViolation("SCHEMA_MISMATCH", ...)` if input doesn't match schema. Schema has `extra="forbid"`.

2. **Graph integrity checks** — Verifies `root_cause` exists as a key in `dependency_graph`. Verifies `blocked_task_id` exists as a key in `dependency_graph`. Fails with `BROKEN_ROOT_CAUSE` or `INVALID_GRAPH`.

3. **BFS traversal** — `compute_downstream_path(blocked_task_id, dependency_graph)`. Uses `visited` set and `queue` list. Neighbors are sorted alphabetically before visiting. No duplicates. Handles cycles safely.

4. **Scoring** — `impact_score = len(impacted_tasks)`. Severity is algebraic: LOW/MEDIUM/HIGH based on thresholds.

5. **Output** — Packaged into Pydantic `PropagationOutput`, serialized via `model_dump()`.

---

## File Map

```
KESHAV-4/
├── app/
│   ├── __init__.py              # Package marker
│   ├── engine.py                # THE engine. Two static methods. 91 lines.
│   └── health.py                # Health check for operational readiness
├── shared_schemas/
│   ├── __init__.py              # Exports schemas
│   └── schemas.py               # PropagationInput, PropagationOutput, PropagationContractViolation
├── shared_tests/
│   ├── test_deep_failures.py    # Gap 8: outage, mismatch, corruption, timeout, replay
│   ├── test_distributed_determinism.py  # Gap 2: cross-process determinism
│   ├── test_edge_cases_and_determinism.py  # Deep chains, cycles, branching, shuffled determinism
│   ├── test_end_to_end_proof.py # E2E: Signal → Propagation → KSML → Bucket
│   ├── test_engine.py           # Core engine validation (7 tests)
│   ├── test_failure_visibility.py  # Fail-closed behavior (5 tests)
│   └── test_live_integration.py # 15 concurrent traces through live TANTRA
├── review-packets/
│   ├── REVIEW_PACKET.md         # Canonical proof document
│   ├── KESHAV_OWNERSHIP_AUDIT.md  # This audit
│   ├── KESHAV_CANONICAL_ARCHITECTURE.md  # This document
│   └── evidence/                # Auto-generated proof artifacts
│       ├── bucket_payload_sample.json
│       ├── execution_excerpt.txt
│       ├── schema_import_proof.txt
│       ├── failure_stack_trace.txt
│       ├── downstream_outage_proof.txt
│       ├── timeout_behavior_proof.txt
│       └── replay_reconstruction_proof.txt
├── deploy/
│   └── topology.yml             # Deployment topology
├── shared_contracts/            # Reserved (empty)
└── shared_traces/               # Reserved (empty)
```

---

## Upstream Layer

**Who calls KESHAV:**

The `text-risk-scoring-service` integration tests import `PropagationEngine` and feed its output into the Sūtradhāra Control Plane via KSML envelopes.

```
Caller → PropagationEngine.compute_dependency_output(input_dict)
       → receives output dict
       → wraps into KSMLInput (ContextSignal with severity → value mapping)
       → invokes invoke_agent(ksml)
```

**Upstream contract:**
- Caller MUST provide a dict matching `PropagationInput` schema
- Caller MUST handle `PropagationContractViolation` exceptions
- KESHAV does NOT validate what the caller does with the output

---

## Downstream Layer

**What KESHAV feeds into:**

KESHAV produces a `PropagationOutput` dict. The integration layer maps this into:

| KESHAV Output Field | KSML Mapping |
|---|---|
| `severity` | `ContextSignal.value` (HIGH=0.9, else=0.5) |
| `resolution_signal` | `metadata.proposed_action` |
| `trace_id` | `KSMLInput.execution_id` |

KESHAV has **NO authority** over what happens downstream. It does not:
- Make enforcement decisions (that's RAJYA)
- Mint trace hashes (that's Sarathi)
- Write to Bucket (that's Layer 5)
- Manage epistemic state (that's DGIC)

---

## Boundary Declarations

### Validation Boundary

| Aspect | Declaration |
|---|---|
| Input validation | Pydantic `PropagationInput` with `extra="forbid"`. `min_length=1` on string fields. `Dict[str, List[str]]` on dependency_graph. |
| Output validation | Pydantic `PropagationOutput` with `extra="forbid"`. `Literal["LOW", "MEDIUM", "HIGH"]` on severity. |
| Error handling | Fail-closed. Three error codes: `SCHEMA_MISMATCH`, `BROKEN_ROOT_CAUSE`, `INVALID_GRAPH`. |
| Invalid input behavior | Exception raised immediately. No partial output. No silent degradation. |

### Execution Boundary

| Aspect | Declaration |
|---|---|
| Computation scope | BFS traversal of in-memory graph. O(V+E) time complexity. |
| Side effects | **NONE.** No file I/O, no network calls, no logging, no print statements. |
| Concurrency safety | Thread-safe and process-safe. All state is local to the function call. |
| Performance bound | 500-node graph completes sub-second (proven in `test_timeout_behavior`). |

### Replay Boundary

| Aspect | Declaration |
|---|---|
| Determinism | Byte-identical output given identical input. Proven across 100 shuffled iterations (in-process), 10 isolated OS processes (cross-process), and 15 concurrent threads (concurrent). |
| Replay method | Re-invoke `compute_dependency_output` with the same input dict. |
| State requirements | None. Engine is stateless. No warm-up, no initialization, no prior context needed. |
| Serialization | Output is `model_dump()` → plain Python dict → JSON-serializable. Proven via serialize/deserialize/re-compute cycle in `test_replay_reconstruction_after_interruption`. |

### Observability Boundary

| Aspect | Declaration |
|---|---|
| Error visibility | All errors raise `PropagationContractViolation` with explicit `.code` and `.message`. |
| Health check | `app/health.py` → `check_health()` → `HealthStatus` with schema integrity, computation, and latency checks. |
| Metrics surface | `impact_score`, `severity`, `impacted_tasks` count available in every output. |
| Trace preservation | `trace_id` and `timestamp` are passed through unchanged. |

### Hidden-State Boundary

| Aspect | Declaration |
|---|---|
| Runtime caches | **NONE.** |
| In-memory persistence | **NONE.** |
| Transient state | **NONE.** Local variables (`visited`, `queue`, `impacted_tasks`) exist only within function scope. |
| Adaptive behavior | **NONE.** Output is strictly deterministic. Engine does not learn or adapt. |
| Class state | **NONE.** Both methods are `@staticmethod`. No `self`, no `cls`, no instance. |

### Authority Boundary

| Category | Scope |
|---|---|
| **Owned** | BFS traversal, graph sorting, impact scoring, severity classification, resolution signal generation, input validation, error code assignment |
| **Not Owned** | Enforcement decisions, epistemic state, trace hash minting, bucket writes, KSML envelope construction |
| **Influence** | Produces `severity` and `resolution_signal` that downstream systems may use to make decisions |
| **Upstream** | Receives input. Full authority to reject malformed input. |
| **Downstream** | Produces output. No authority over consumption. |
| **Execution Rights** | Read-only computation. No writes, no network, no state mutation. |

---

## Schema Definitions

### PropagationInput (owned by KESHAV-4)
```python
class PropagationInput(BaseModel):
    blocked_task_id: str = Field(..., min_length=1)
    root_cause: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    dependency_graph: Dict[str, List[str]]
    model_config = ConfigDict(extra="forbid")
```

### PropagationOutput (owned by KESHAV-4)
```python
class PropagationOutput(BaseModel):
    blocked_task_id: str
    root_cause: str
    impacted_tasks: List[str]
    impact_score: int
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    resolution_signal: str
    trace_id: str
    timestamp: str
    model_config = ConfigDict(extra="forbid")
```

### PropagationContractViolation (owned by KESHAV-4)
```python
class PropagationContractViolation(Exception):
    def __init__(self, code: str, message: str):
        self.code = code        # "SCHEMA_MISMATCH" | "BROKEN_ROOT_CAUSE" | "INVALID_GRAPH"
        self.message = message
```

---

## Integration Surface with text-risk-scoring-service

KESHAV-4 consumes these modules from `text-risk-scoring-service` (via `sys.path` import):

| Module | What KESHAV uses |
|---|---|
| `app.enforcement_schemas` | `KSMLInput`, `ContextSignal`, `SourceSystem` |
| `app.sutradhara_control_plane` | `invoke_agent()` |
| `app.layer3_dgic` | `compute_envelope_hash()` |
| `app.layer5_bucket` | `verify_by_trace_hash()` (in tests only) |

**These are consumed, not owned.** KESHAV-4 does not modify, extend, or fork these modules.

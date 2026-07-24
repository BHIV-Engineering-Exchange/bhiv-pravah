# FULL HANDOVER PACKET
## Phase 8 — Comprehensive KESHAV-4 Handover

**Service:** KESHAV-4 Propagation Engine
**Canonical Owner:** Rajaryan
**Date:** 2026-05-26

This is the definitive handover packet for KESHAV-4. It contains everything required for an incoming intern, a new engineer, or a future maintainer to understand, test, debug, and run KESHAV-4 safely.

---

## 1. System Overview

KESHAV-4 is a **stateless, deterministic dependency propagation engine**. 
It answers one question: *"Given a blocked task and a dependency graph, what is the downstream blast radius?"*

It takes a graph and a blocked node, runs a strict Breadth-First Search (BFS), and returns a list of impacted tasks along with a severity score. It has zero network calls, zero state, and zero configuration files.

---

## 2. File Map

```text
C:\blackhole\KESHAV-4\
├── app/
│   ├── engine.py                  <-- The core computation engine. Start here.
│   └── health.py                  <-- Non-destructive health check.
├── shared_schemas/
│   └── schemas.py                 <-- Pydantic definitions (Input, Output, Errors).
├── shared_tests/
│   ├── _replay_worker.py          <-- Helper for multiprocessing tests.
│   ├── test_adversarial_failures.py <-- Proofs of adversarial resilience (Phase 6).
│   ├── test_deep_failures.py      <-- Proofs of failure visibility and timing.
│   ├── test_distributed_determinism.py <-- Cross-process determinism proof.
│   ├── test_edge_cases_and_determinism.py <-- Core BFS traversal determinism tests.
│   ├── test_end_to_end_proof.py   <-- Integration with TRSS and mocked Bucket.
│   ├── test_engine.py             <-- Basic core functionality tests.
│   ├── test_failure_visibility.py <-- Schema mismatch and validation tests.
│   ├── test_live_integration.py   <-- End-to-end integration mapping proofs.
│   └── test_replay_hardening.py   <-- Restart and interruption proofs (Phase 3).
└── review-packets/
    ├── CONSTITUTIONAL_DECLARATION.md
    ├── FAILURE_HARDENING_PACKET.md
    ├── KESHAV_CANONICAL_ARCHITECTURE.md
    ├── KESHAV_OWNERSHIP_AUDIT.md
    ├── OPERATIONS_READINESS.md
    ├── REVIEW_PACKET.md           <-- The master canonical review document.
    ├── SCHEMA_GOVERNANCE.md
    ├── TESTING_PACKET_FOR_TESTING_DEPARTMENT.md
    └── evidence/                  <-- Auto-generated proofs from test runs.
```

---

## 3. Execution Walkthrough

1. An external pipeline calls `PropagationEngine.compute_dependency_output(input_dict)`.
2. The dictionary is validated against `PropagationInput` using Pydantic. If invalid, it raises `PropagationContractViolation` immediately.
3. KESHAV verifies the `blocked_task_id` and `root_cause` exist as keys in the `dependency_graph`.
4. KESHAV runs `compute_downstream_path()` — a BFS that explicitly sorts neighbors alphabetically to guarantee determinism.
5. KESHAV counts the impacted nodes (`impact_score`).
6. KESHAV assigns `severity` (LOW < 3, MEDIUM < 10, HIGH >= 10).
7. KESHAV generates a `resolution_signal` (`UNBLOCK_DEPENDENCY:root_cause`).
8. KESHAV packs the result into `PropagationOutput`, calls `.model_dump()`, and returns the dictionary.

---

## 4. Contracts

### Valid Input (Must conform exactly to `PropagationInput`):
```json
{
  "blocked_task_id": "T1",
  "root_cause": "RC",
  "trace_id": "abc-123",
  "timestamp": "2026-05-26T12:00:00Z",
  "dependency_graph": {
    "RC": ["T1"],
    "T1": ["T2"]
  }
}
```

### Valid Output (Conforms exactly to `PropagationOutput`):
```json
{
  "blocked_task_id": "T1",
  "root_cause": "RC",
  "impacted_tasks": ["T2"],
  "impact_score": 1,
  "severity": "LOW",
  "resolution_signal": "UNBLOCK_DEPENDENCY:RC",
  "trace_id": "abc-123",
  "timestamp": "2026-05-26T12:00:00Z"
}
```

---

## 5. Frequently Asked Questions (FAQs)

**Q: Where is the database connection string?**
A: There isn't one. KESHAV operates entirely in memory on the data provided in the input dictionary.

**Q: How do I change the severity thresholds?**
A: You don't. The thresholds (LOW < 3, MEDIUM < 10, HIGH >= 10) are intrinsic algebraic rules. Changing them requires a code deployment and updates to tests.

**Q: KESHAV is rejecting a payload with an extra field. Can we make it ignore extra fields?**
A: No. KESHAV uses `extra="forbid"` to strictly prevent schema drift. The upstream system must clean the payload before sending it to KESHAV.

---

## 6. Common Failures & Debug Map

| Failure Code | Meaning | Debug Action |
|---|---|---|
| `SCHEMA_MISMATCH` | Input failed Pydantic validation (wrong type, extra field, missing field). | Inspect the payload against `shared_schemas/schemas.py`. |
| `BROKEN_ROOT_CAUSE` | `root_cause` string is not a key in `dependency_graph`. | Ensure the upstream system provides a graph containing the root cause node. |
| `INVALID_GRAPH` | `blocked_task_id` string is not a key in `dependency_graph`. | Ensure the upstream system provides a graph containing the blocked task. |

---

## 7. How to Run & Test

**To check health:**
```bash
python -m app.health
```

**To run the full test suite (38 tests):**
```bash
pytest shared_tests/ -v --tb=short
```

**To run only adversarial tests:**
```bash
pytest shared_tests/test_adversarial_failures.py -v
```

---

## 8. Safe Extension Guide

**How to extend safely:**
1. If adding a new field to output, add it to `PropagationOutput` in `schemas.py`.
2. Update the integration tests (`test_live_integration.py`, `test_end_to_end_proof.py`) to handle the new field.
3. If extending the graph traversal logic, DO NOT remove the `sorted()` calls. Determinism must be preserved.

---

## 9. What NEVER to Modify (The Non-Negotiables)

1. **NEVER** add `self` or `__init__` state to `PropagationEngine`. It must remain fully stateless.
2. **NEVER** remove `model_config = ConfigDict(extra="forbid")` from the schemas.
3. **NEVER** introduce `requests` or external network calls into `engine.py`.
4. **NEVER** implement heuristic or machine-learning-based severity scoring inside KESHAV.
5. **NEVER** catch `PropagationContractViolation` and return a "fallback" output. Fail closed.


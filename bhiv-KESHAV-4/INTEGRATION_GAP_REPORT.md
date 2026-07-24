# Ecosystem Integration Gap Report
**Phase 5 — Gap Closure Planning**

This report identifies the discrepancies between the validated canonical transfer (`intake/Pritesh_transfer/`) and the currently active operational workspace (`c:\rajaryan\KESHAV-4\`).

## 1. Missing Runtime Wiring
**Classification:** CRITICAL
* **Description:** The current operational workspace is running an outdated FastAPI server (`app/main.py`) that delegates to a `PropagationEngine` (`app/engine.py`). It is completely missing the verified `tantra/pipeline.py` which strictly orchestrates the `SETU/Input → KESHAV → RAJYA → Sarathi → Core → Bucket` flow.
* **Impact:** KESHAV is physically disconnected from the true TANTRA execution chain in the active workspace.

## 2. Missing Core Logic (The 5-Phase Algorithm)
**Classification:** CRITICAL
* **Description:** The canonical `analyzer/` module with its deterministic 5-phase algorithm (`analyze_blockage.py`, `root_cause_tracer.py`, etc.) is missing from the active workspace.
* **Impact:** The deterministic guarantees, BFS graph traversal, and fail-closed validation proven in Phase 2 are not physically present in the root project.

## 3. Disjoint Contracts and Schemas
**Classification:** CRITICAL
* **Description:** The active workspace is tightly coupled to `shared_schemas.schemas` (`PropagationInput`, `PropagationOutput`) using Pydantic validation. The canonical KESHAV architecture strictly requires schema-less dictionaries enforcing the TANTRA contract (`trace_id`, `execution_id`, `root_cause`, `severity`).
* **Impact:** The active workspace violates the "Zero External Schema Authority" constitutional boundary.

## 4. Missing Observability Fields
**Classification:** MAJOR
* **Description:** The canonical `insightflow.py` observability layer is absent. The active workspace uses a generic `app/health.py` and lacks the structured event emission for `EXECUTION` and `FAILURE` states.
* **Impact:** Operational visibility is compromised, and the `OBSERVABILITY_INTEGRITY` claims cannot be met in the active workspace.

## 5. Missing Persistence Paths
**Classification:** CRITICAL
* **Description:** The `tantra/bucket.py` truth layer is completely absent. The current `app/engine.py` just returns HTTP JSON responses. 
* **Impact:** There is no "write-on-success" persistence. The `trace_continuity_proof` and Bucket assertions fail since the Bucket does not exist.

## 6. Missing Replay Links
**Classification:** MAJOR
* **Description:** The active workspace lacks the structural `trace_id` passthrough logic that `analyzer/` and `tantra/` employ. Replay equivalence cannot be guaranteed without the canonical logic.
* **Impact:** Deterministic output reproducibility is broken in the active workspace.

## 7. Outdated Tests
**Classification:** MAJOR
* **Description:** The active workspace runs tests from `shared_tests/` (e.g., `test_api.py`), which validate the obsolete FastAPI structure. The 123 comprehensive tests from Pritesh's `tests/` directory are missing.
* **Impact:** 100% code coverage and constitutional layer contract proofs are not validated against the current root workspace.

## Next Steps for Convergence
To achieve operational convergence, the old `app/`, `shared_schemas/`, and `shared_tests/` structures must be systematically removed and replaced with Pritesh's `analyzer/`, `tantra/`, and `tests/` canonical components, followed by wiring up the `api.py` endpoint correctly.

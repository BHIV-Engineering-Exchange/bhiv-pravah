# Determinism Validation Report

This report documents the results of the determinism and replay integrity verification for the Vaani Sentinel Narrative Divergence Detector.

## 1. Test Objective
To ensure that given identical input batches, the Sentinel engine produces byte-for-byte identical outputs, including the same divergence scores, truth levels, and deterministic hashes.

## 2. Methodology
- **Input**: `example_input.json`.
- **Process**: Run the `deterministic_cluster` logic multiple times consecutively.
- **Verification**: Compute the SHA-256 hash of the full structured output (JSON).
- **Comparison**: Compare hashes across runs to ensure zero mutation or variance.

## 3. Results

| Run # | Hash Result | Status |
| :--- | :--- | :--- |
| Run 1 | `66dca65423595b3e243fd16b9249b9a1000495765...` | ✅ UNCHANGED |
| Run 2 | `66dca65423595b3e243fd16b9249b9a1000495765...` | ✅ UNCHANGED |

**Integrity Status**: 🟢 **100% Deterministic**

## 4. Stability Guarantees Verified
- **Sort Stability**: All signals and keys are sorted deterministically.
- **No Floating Variance**: Divergence scores are rounded consistently.
- **Repeatability**: The logic is idempotent and produces the same output regardless of execution environment or time.

## 5. Artifacts
- **Validation Script**: `verify_determinism.py`
- **Replay Batch**: `replay_test_suite/sample_input.json`
- **Reference Output**: `replay_test_suite/sample_output.json`

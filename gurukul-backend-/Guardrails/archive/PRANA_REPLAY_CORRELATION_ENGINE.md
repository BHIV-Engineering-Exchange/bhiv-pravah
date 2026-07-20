# PRANA Replay Correlation Engine

## 1. Conceptual Engine Setup
To elevate PRANA from an Integrity Sentinel to an Integrity Verifier without granting it execution authority, a **Correlation Engine (PRANA-CORE)** must act strictly as a secondary observer and ledger cross-referencer.

## 2. Verification Responsibilities

### A. Replay Mismatch Detection
PRANA-CORE will evaluate structural determinism by calculating masked hashes. It hashes output states after stripping globally whitelisted volatile fields (e.g., IDs, fresh timestamps). It correlates the normalized "pure" state of the original run against the replay run.

### B. Ledger Drift Detection
The engine queries the sequential ledger and compares chain linkages. By verifying that the `previous_hash` chains align logically through simulated replays, it detects when systems alter state asynchronously or skip transitions.

### C. Output Classification Inconsistency
It references Karma’s truth classifications. If a historically "VALID" event is replayed and evaluated as "MALICIOUS", the engine throws a Class-A Divergence flag without intercepting either system’s process.

## 3. Boundary Constraints
- **Zero Governance Execution**: PRANA-CORE cannot patch mismatches, modify inputs, or roll back databases.
- **Strict Observer Protocol**: It emits divergence telemetry and stops there. Truth is preserved, optics are ignored.

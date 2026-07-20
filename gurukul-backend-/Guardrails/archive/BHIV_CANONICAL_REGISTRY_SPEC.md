# DELIVERABLE 1: BHIV_CANONICAL_REGISTRY_SPEC.md

## 1. System Identifier (system_id) Definitions
The Canonical Registry defines the immutable identifiers for all participating ecosystem nodes.
- `sys_prana_01`: PRANA Integrity Observer & Verifier
- `sys_gurukul_01`: Gurukul Backend Task Pipeline
- `sys_review_ai_01`: Task Review AI Evaluator
- `sys_workflow_01`: Workflow Routing and Assignment Node

## 2. Event Schema Definitions
Events must be strictly structured according to their registry schema mapping:
- `SCHEMA_TASK_SUBMITTED_V1`: Triggered when an entity submits an operational task payload.
- `SCHEMA_REVIEW_OUTPUT_V1`: Triggered when an evaluation outputs a scored payload.
- `SCHEMA_WORKFLOW_ROUTE_V1`: Triggered when tasks transition logistical owners.
- `SCHEMA_PRANA_VALIDATION_V1`: Triggered when PRANA records an observation mismatch.

## 3. Truth Classification Levels (0–4)
The ecosystem enforces a strict deterministic 5-tier classification hierarchy across all outputs.
- **Level 0 (UNCLASSIFIED):** Unverified raw payload ingestion.
- **Level 1 (STRUCTURAL_VALID):** Schema compliance and boundary limits satisfy the contract.
- **Level 2 (LOGIC_VALID):** State transitions conform strictly to the state machine definitions.
- **Level 3 (CONFIRMED_TRUTH):** Cross-referenced verification successful (e.g. Karma verification).
- **Level 4 (MALICIOUS/DIVERGENT):** Proven structural divergence, replay failure, or logic mutation detected.

## 4. Contract Versioning Rules
- **Immutability:** Once a schema version (e.g., `v1.0.0`) is registered, it can never be mutated.
- **Semantic Progression:** Schema extensions require a major/minor version bump (e.g., `v1.1.0`).
- **Deprecation Windows:** Deprecated contracts remain valid for replay but cannot be emitted by active systems.

## 5. Event Ownership Boundaries
- `sys_gurukul_01` exclusively emits `SCHEMA_TASK_SUBMITTED_V1`.
- `sys_review_ai_01` exclusively emits `SCHEMA_REVIEW_OUTPUT_V1`.
- `sys_workflow_01` exclusively emits `SCHEMA_WORKFLOW_ROUTE_V1`.
- `sys_prana_01` exclusively acts as a subscriber to the above, emitting only `SCHEMA_PRANA_VALIDATION_V1`.

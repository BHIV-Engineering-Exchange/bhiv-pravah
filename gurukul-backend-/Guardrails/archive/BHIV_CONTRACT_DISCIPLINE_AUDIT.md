# DELIVERABLE 2: BHIV_CONTRACT_DISCIPLINE_AUDIT.md

## 1. Contract Definitions per System

### A. PRANA (`sys_prana_01`)
- **Input Contract:** Any registered schema (`SCHEMA_*`)
- **Output Contract:** `SCHEMA_PRANA_VALIDATION_V1`
- **Registry Reference:** `registry://prana/validation/v1.0.0`
- **Contract Version:** `v1.0.0`

### B. Gurukul Backend (`sys_gurukul_01`)
- **Input Contract:** Raw Client Payloads, `SCHEMA_WORKFLOW_ROUTE_V1`
- **Output Contract:** `SCHEMA_TASK_SUBMITTED_V1`
- **Registry Reference:** `registry://gurukul/task/v1.0.0`
- **Contract Version:** `v1.0.0`

### C. Task Review AI (`sys_review_ai_01`)
- **Input Contract:** `SCHEMA_TASK_SUBMITTED_V1`
- **Output Contract:** `SCHEMA_REVIEW_OUTPUT_V1`
- **Registry Reference:** `registry://reviewai/eval/v1.0.0`
- **Contract Version:** `v1.0.0`

### D. Workflow Service (`sys_workflow_01`)
- **Input Contract:** `SCHEMA_REVIEW_OUTPUT_V1`, `SCHEMA_TASK_SUBMITTED_V1`
- **Output Contract:** `SCHEMA_WORKFLOW_ROUTE_V1`
- **Registry Reference:** `registry://workflow/route/v1.0.0`
- **Contract Version:** `v1.0.0`

## 2. Identified Violations & Mismatches
- **Schema Mismatches:** Gurukul Backend accepts unstructured raw client payloads without coercing them natively into a registry schema at the initial ingress boundary.
- **Missing Fields:** Review AI output logs frequently fail to reference their source `registry_reference` in standalone output files.
- **Non-Deterministic Outputs:** Workflow Service emits dynamically generated `route_id`s (`uuid4`) and dynamically calculates execution metadata arrays (`datetime.now()`) on ingestion, breaking strict contract adherence.
- **Version Inconsistencies:** PRANA listens for `v1.0.0`, but Gurukul Backend occasionally emits unversioned legacy JSON arrays.

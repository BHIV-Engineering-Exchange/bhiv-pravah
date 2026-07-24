   # KESHAV Intake Report

**Phase 1 — Handover Acceptance & Inventory**
**Incoming Canonical Owner:** Rajaryan

## Assets Received from Pritesh
* `analyzer/` - Core logic containing KESHAV's 5-phase dependency analysis pipeline.
* `tantra/` - TANTRA ecosystem integration layers (`pipeline.py`, `rajya.py`, `sarathi.py`, `core.py`, `bucket.py`, `insightflow.py`).
* `tests/` - 123 passing test cases with 100% coverage.
* `review-packets/` - 20 comprehensive documentation and proof artifacts (including `JOINT_TRANSITION_AUDIT_DOSSIER.md`).
* `api.py`, `metrics.py` - Flask API entry point and Prometheus metrics.
* `Dockerfile`, `docker-compose.yml`, `k8s-deployment.yaml`, `keshav.service` - Production infrastructure code.
* `pyproject.toml`, `Makefile`, `sample_input.json`, `README.md` - Development configurations and docs.

## Assets Received from Kanishk
* **Proof Logs:** `bucket_replay_verification.log`, `cross_layer_audit_report.log`, `distributed_replay_audit.log`, `insightflow_replay_verification.log`.
* **JSON Proofs:** `corruption_injection_output.json`, `replay_reconstruction_proof.json`, `restart_recovery_replay_proof.json`, `system_audit.json`.
* **Duplicate/Nested Codebases:** `KESHAV-4-main/`, `keshavrRedesign-main/`, `Sarathi/`, `deterministic_validation_engine/`, `keshav_validation_engine/`.
* **Documentation:** `docs/`, `review-packets/`.

## Missing Assets
* None identified in Pritesh's handover payload. The canonical transfer is complete. 
* *Note:* The current active workspace `c:\rajaryan\KESHAV-4` has a disjoint structure (`app/`, `shared_schemas/`, `shared_tests/`) compared to Pritesh's final transfer (`analyzer/`, `tantra/`). This is an integration gap that will need resolving in subsequent phases.

## Unknown Assets
* Kanishk's repository contains multiple duplicate, nested, and potentially orphaned code repositories (e.g., `keshavrRedesign-main`, `Sarathi` decoupled from `tantra/`). These were not part of the finalized KESHAV canonical architecture.

## Unverified Claims
* The exact relevance and status of Kanishk's duplicate repositories are unverified as they deviate from the agreed canonical architecture. The `JOINT_TRANSITION_AUDIT_DOSSIER.md` claims that only `analyzer/` and `tantra/` in Pritesh's transfer are the real codebase.

## Ownership Transfer Status
* Complete. Formal joint sign-off is verified by Pritesh, Kanishk, and Rajaryan in `JOINT_TRANSITION_AUDIT_DOSSIER.md` (Section 15).

## INTAKE ACCEPTED

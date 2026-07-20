# 📑 MDU Claims-To-Proof Matrix

**Sprint Compliance Level:** TANTRA-Hardened (Operator-Grade)  
**Verification Target:** Phase 3 Convergence Audit  
**Author:** Soham Kotkar — Sprint Lead & Compliance Owner  

This document serves as our master proof ledger. It maps each operational claim of the hardened **Master Data Universe (MDU) Registry** directly to its corresponding API endpoint, SQL database table, automated unit test, and manual verification evidence.

---

## 1. Claims Matrix (Technical Proofs)

| Functional Claim | Target API Endpoint | Relational Database & Vector DB | Automated Unit Test | Manual Verification Proof |
| :--- | :--- | :--- | :--- | :--- |
| **Live Health Monitoring & Polling** | `GET /api/v1/mdu/health` | SQLite `mdu_datasets` table state & DB latency check | `test_get_mdu_health` | Displayed inside MDU Dashboard top-right bar with active pulse indicator and boundary details. |
| **Fault Resilience & Crash Hardening** | `POST /api/v1/mdu/simulate-failure` | Health toggle memory state | `test_simulate_failure_states` | "Trigger Database Crash" toggle simulates a 500 server error; UI handles it gracefully with alert cards. |
| **Ingressed Datasets & Catalog** | `GET /api/v1/mdu/datasets` | SQLite `mdu_datasets` catalog persistence | `test_get_datasets_list` | Dynamic list cards showing textbooks, chunk counts, versions, and trust scores loaded from DB. |
| **Interactive Ingestion Lineage** | `GET /api/v1/mdu/lineage/{id}` | SQLite `profiles` active user lookup & `mdu_datasets` JSON | `test_get_dataset_lineage` | Click on a dataset loads a complete, beautiful workflow tree with dynamic node state evaluations. |
| **Contract Ingress Guardrails** | `POST /api/v1/mdu/schema-mismatch` | Schema checks: 422 validations & 409 rejections | `test_schema_mismatch_422` & `test_schema_version_409` | Ingress validation simulations block malformed payload schemas. |
| **Authoritative State Reconciliation** | `POST /api/v1/mdu/reconcile` | SQLite `profiles` table preferences query & `mdu_reconciliation_history` | `test_mdu_state_reconciliation_persistence` | Triggering reconciliation scans SQL profiles and logs traces to history. |
| **Schema Lifecycle Transition** | `POST /api/v1/mdu/lifecycle/action` | SQLite `mdu_datasets` status updates | `test_lifecycle_administrative_actions_and_persistence` | Dataset action buttons (Activate, Deprecate, Rollback) execute live in DB and write provenance events. |
| **Cryptographic Provenance logs** | `GET /api/v1/mdu/provenance` | SQLite `mdu_provenance_events` chain | `test_get_provenance_logs_with_chain_verification` & `test_provenance_cryptographic_tamper_detection` | Monospace audit scrollable panel showing operator name, event type, hash, and verification check status. |

---

## 2. Relational Database Schema Snapshots

Verify the database table configurations in SQLite:

### `mdu_datasets`
```sql
CREATE TABLE mdu_datasets (
    id VARCHAR NOT NULL PRIMARY KEY,
    board VARCHAR NOT NULL,
    medium VARCHAR NOT NULL,
    class_standard INTEGER NOT NULL,
    textbook_code VARCHAR NOT NULL,
    canonical_name VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    chunk_count INTEGER NOT NULL,
    trust_score FLOAT NOT NULL,
    onboarding_state VARCHAR NOT NULL,
    last_updated DATETIME,
    lineage_nodes JSON NOT NULL,
    lineage_links JSON NOT NULL
);
```

### `mdu_provenance_events`
```sql
CREATE TABLE mdu_provenance_events (
    id VARCHAR NOT NULL PRIMARY KEY,
    timestamp DATETIME,
    operator VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    dataset VARCHAR NOT NULL,
    hash VARCHAR(64) NOT NULL
);
```

### `mdu_reconciliation_history`
```sql
CREATE TABLE mdu_reconciliation_history (
    id VARCHAR NOT NULL PRIMARY KEY,
    timestamp DATETIME,
    status VARCHAR NOT NULL,
    profile_audit_count INTEGER NOT NULL,
    board_preferences JSON NOT NULL,
    leakage_checks JSON NOT NULL,
    reconciliation_trace JSON NOT NULL
);
```

---

## 3. Automated Test Command Reference

Run the complete test suite to verify all claims are 100% operational:
```bash
pytest backend/tests/test_mdu_registry.py -v
```
All claims are backed by database assertions and cryptographic chain verification.

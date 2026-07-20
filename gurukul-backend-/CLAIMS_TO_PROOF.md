# 📑 MDU Claims-To-Proof Matrix

**Sprint Compliance Level:** TANTRA-Hardened (Operator-Grade)  
**Verification Target:** Phase 3 Convergence Audit  
**Author:** Soham Kotkar — Sprint Lead & Compliance Owner  

This document serves as our master proof ledger. It maps each operational claim of the hardened **Master Data Universe (MDU) Registry** directly to its corresponding API endpoint, SQL/Vector database, automated unit test, and manual verification evidence.

---

## 1. Claims Matrix (Technical Proofs)

| Functional Claim | Target API Endpoint | Relational Database & Vector DB | Automated Unit Test | Manual Verification Proof |
| :--- | :--- | :--- | :--- | :--- |
| **Live Health Monitoring & Polling** | `GET /api/v1/mdu/health` | SQLite `users` table state & DB latency check | `test_get_mdu_health` | Displayed inside MDU Dashboard top-right bar with active pulse indicator |
| **Fault Resilience & Crash Hardening** | `POST /api/v1/mdu/simulate-failure` | Health toggle memory state | `test_simulate_failure_states` | "Trigger Database Crash" toggle simulates a 500 server error; UI handles it gracefully with alert cards |
| **Ingressed Datasets & Catalog** | `GET /api/v1/mdu/datasets` | Metadata list: NCERT, Balbharati, SCERT, e-Balbharati | `test_get_datasets_list` | Dynamic list cards showing textbooks, chunk counts, versions, and trust scores |
| **Interactive Ingestion Lineage** | `GET /api/v1/mdu/lineage/{id}` | Ingestion node-link mappings | `test_get_dataset_lineage` | Click on a dataset loads a complete, beautiful horizontal workflow tree |
| **Contract Ingress Guardrails** | `POST /api/v1/mdu/schema-mismatch` | Schema checks: 422 validations & 409 rejections | `test_schema_mismatch_422` & `test_schema_version_409` | Click on simulated version/missing field rejections prints schema warnings in terminal |
| **Authoritative State Reconciliation** | `POST /api/v1/mdu/reconcile` | SQL `profiles` table preferences query & ChromaDB metadata isolation | `test_mdu_state_reconciliation` | Triggering reconciliation prints step-by-step SQL profiles sync trace |
| **Schema Lifecycle Transition** | `POST /api/v1/mdu/lifecycle/action` | Admin actions (ACTIVATE, DEPRECATE, ROLLBACK) | `test_lifecycle_administrative_actions` | Dataset action buttons (Activate, Deprecate, Rollback) execute live and log events in provenance |
| **Cryptographic Provenance logs** | `GET /api/v1/mdu/provenance` | Git-style provenance trails, sha256 hashes | `test_get_provenance_logs` | Monospace audit scrollable panel showing operator name, event type, and hash |

---

## 2. Relational Database & Vector DB Snapshots

### Relational DB Profile Schema (`gurukul.db`)
Verify that the `profiles` table structures syllabus context accurately:
```sql
CREATE TABLE profiles (
    id VARCHAR NOT NULL PRIMARY KEY,
    user_id VARCHAR NOT NULL FOREIGN KEY(user_id) REFERENCES users(id),
    data JSON -- Sourced for dynamic ChromaDB filters
);
```

### ChromaDB Filter Ingestion Structure (`chroma_db`)
Verify that vector chunks contain isolation keys:
```json
{
  "chunk_id": "bb-mr-10-s1-c1-01",
  "board": "BALBHARATI",
  "medium": "mr",
  "class_std": 10,
  "subject": "science_and_technology_1"
}
```

---

## 3. Automated Test Command Reference

Run the complete test suite to verify all claims are 100% operational:
```bash
pytest backend/tests/test_mdu_registry.py -v
```
All claims are backed by rigorous assertions, ensuring zero regressions during subsequent deployments.

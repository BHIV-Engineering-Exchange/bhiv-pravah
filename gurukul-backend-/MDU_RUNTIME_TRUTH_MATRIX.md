# 🗺️ MDU Runtime Truth Matrix

This matrix maps each MDU Registry claim to its actual backend convergence state, eliminating presentation drift between frontend UI panels and infrastructure backends.

| Feature Area | Sub-Component / Subsystem | Implementation Status | Source-of-Truth / Authority | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Catalog Listing** | Curriculum Datasets | **IMPLEMENTED** | SQLite `mdu_datasets` table | Fetches canonical names, chunk counts, versions, and onboarding states from SQL. |
| **Lifecycle State** | State Transitions | **IMPLEMENTED** | SQLite `mdu_datasets` table | Lifecycle updates (ACTIVATE, DEPRECATE, ROLLBACK) are written to SQLite. |
| **Audit Trails** | Administrative Provenance | **IMPLEMENTED** | SQLite `mdu_provenance_events` | Enforces append-only cryptographic block validation chaining. |
| **Diagnostics** | Health Checks | **PARTIAL** | SQLite ping & DB telemetry | SQLite ping is live; ChromaDB and Pravah check responses are mock-simulated. |
| **Telemetry** | System Performance | **PARTIAL** | Live process stats | Latency checks are live; memory usage and write lock counts are simulated bounds. |
| **State Sync** | Storage Reconciliation | **IMPLEMENTED** | SQLite `profiles` & `mdu_reconciliation_history` | Counts student preferences in SQL profiles and logs traces to reconciliation history. |
| **Lineage** | Graph Nodes | **IMPLEMENTED** | SQLite Profile records | Dynamically computes node status and labels (such as active user count) at query time. |
| **Vector Isolation** | Vector Compliance Checks | **SIMULATED** | Assertions check | Compliance score of 100% is derived from schema assertions rather than real ChromaDB traffic auditing. |

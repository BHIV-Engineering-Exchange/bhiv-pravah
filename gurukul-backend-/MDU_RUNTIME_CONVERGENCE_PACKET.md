# 📊 MDU Runtime Convergence Packet

This document details the architectural specification and implementation evidence of the hardened synchronization pipeline connecting the **Master Data Universe (MDU) Registry** operator interface with the live relational SQLite database of Gurukul.

---

## 1. Relational Database Mapping

All metadata catalog entries, lifecycle states, administrative reconciliation records, and cryptographic provenance trails have transitioned from transient memory stores to persistent SQLite models.

### Models Implemented (`app/models/all_models.py`)

1. **`MduDataset`**: Sourced for the canonical list of textbooks, syllabuses, chunk counts, trust coefficients, onboarding state, and lineage node-link definitions.
2. **`MduProvenanceEvent`**: Cryptographically chained ledger recording operator actions, event descriptions, and sha256 signatures.
3. **`MduReconciliationHistory`**: Append-only log tracking profile audits, syllabus distribution statistics, and data leakage checks.

---

## 2. Cryptographic Provenance Chaining

To ensure tamper-proof operational audit trails, every administrative transition creates a provenance block linked to its predecessor:

$$\text{Hash}_n = \text{SHA256}(\text{Timestamp}_n + \text{Operator}_n + \text{Action}_n + \text{Dataset}_n + \text{Hash}_{n-1})$$

The registry performs **on-the-fly verification** of the entire chain upon loading the operator logs. If any record's payload is tampered with (e.g. modifying SQL logs on disk), the validation check fails for that event and all subsequent events, immediately alerting operators inside the MDU Dashboard.

---

## 3. Dynamic Runtime Lineage Derivation

Lineage nodes are no longer strictly static. They derive their status dynamically:
* **Source Node**: Scans `mdu_datasets` table for chunk counts.
* **Validation Node**: Checked against the active database state (`ACTIVE`, `DRAFT`, `DEPRECATED`).
* **Routing Node**: Dynamically queries the SQLite `profiles` table to calculate the exact number of active student profiles resolved to that syllabus board (e.g., `NCERT (2 Active Profiles resolved)`).

# PRANA Ledger Tamper Threat Model

**Classification:** Sovereign Security Intelligence (CONFIDENTIAL)  
**Status:** DRAFT - Phase 1 Foundation  
**Objective:** Formalize attack vectors targeting the immutability of the PRANA ledger.

## 1. Tampering Scenarios

### 1.1 Row Modification (The "Edit" Attack)
*   **Vector**: Direct SQL update of a committed record (e.g., changing `state='DISTRACTED'` to `state='WORKING'`).
*   **Mechanism**: Database administrator access or SQL injection.
*   **Impact**: Institutional truth is falsified without changing the number of records.
*   **Integrity Barrier**: SHA-256 Hash Chaining.

### 1.2 Row Deletion (The "Memory Hole" Attack)
*   **Vector**: Deletion of individual records from the ledger.
*   **Mechanism**: `DELETE FROM prana_packets WHERE id=...`
*   **Impact**: Negative behaviors are scrubbed from history.
*   **Integrity Barrier**: Deterministic Sequence Anchors (Previous Hash link).

### 1.3 Row Reordering (The "Time Warp" Attack)
*   **Vector**: Swapping the order of records to change the perceived timeline.
*   **Mechanism**: Modifying `received_at` or `client_timestamp`.
*   **Impact**: Logical sequences (e.g., transition from IDLE to WORKING) are decoupled from reality.
*   **Integrity Barrier**: Chronological Hash Linking.

### 1.4 Version Overwrite (The "History Revision" Attack)
*   **Vector**: Overwriting a `review_output` or `next_task` result with a newer, more favorable version without keeping the audit trail.
*   **Mechanism**: Direct primary key overwrite.
*   **Impact**: The most recent truth is the only truth; no forensic audit of the decision path is possible.
*   **Integrity Barrier**: Incremental Versioning + Hash Chaining.

### 1.5 DB File Rewrite (The "Total Repudiation" Attack)
*   **Vector**: Modifying the raw SQLite/Postgres data files on disk.
*   **Mechanism**: OS-level access to the server.
*   **Impact**: Compromise beyond the application layer.
*   **Integrity Barrier**: Off-system Daily Cryptographic Snapshots (Audit Enhancer).

---

## 2. Integrity Requirements

| Requirement | Technical Enforcement |
| :--- | :--- |
| **Non-Repudiation** | Every insert must reference the hash of its predecessor. |
| **Immutability** | Cryptographic hash must cover all sensitive fields, including timestamps. |
| **Auditability** | A single "Break" in the chain must invalidate all subsequent records. |
| **Determinism** | Hashing must not rely on non-deterministic data (e.g., randomized IDs). |

## 3. Residual Risk
While hash-chaining detects tampering, it does not *prevent* it at the OS level. It serves as a **High-Fidelity Alarm** that makes silent corruption computationally impossible.

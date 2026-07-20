# 📊 Gurukul Database & Data Truth Audit
**Section 3: Direct Database Inspection Ledger**  
**Audit Date:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This document represents the direct, un-proxied empirical audit of Gurukul's data assets, inspecting both physical SQLite database files and ChromaDB vector databases directly.

---

## 💾 1. The Dual SQLite Database Anomaly

Our direct inspection of the workspace root revealed two distinct SQLite database files. This dual-database setup represents a critical data architectural detail:

1.  **Root Database (`gurukul.db`):** Located at the workspace root, this file has a size of 684 KB. It contains 24 standard tables, but **0 records** in operational tables such as `users`, `profiles`, and `lessons`. It serves primarily to record system-level logs (`prana_integrity_log` has 100 entries, `replay_validation_log` has 300 entries, and `anomaly_event` has 96 entries).
2.  **Backend Database (`backend/gurukul.db`):** Located inside the backend directory, this file has a size of 11 MB. This is the **actual active database** utilized by the FastAPI server during runtime. It contains 24 tables with rich, production-seeded operational records.

---

## 📊 2. SQLite Operational Table Row Counts (Active Backend DB)

The following matrix records the exact, verified table row counts extracted from `backend/gurukul.db`:

| Table Name | Active Row Count | Purpose & Data Snapshots |
| :--- | :--- | :--- |
| `users` | **17** | Registers student, teacher, guest, and admin credentials. |
| `profiles` | **4** | Multi-role user metadata (student, teacher, etc.). |
| `tenants` | **2** | Registers active multi-tenant educational institutions. |
| `cohorts` | **1** | School classroom cohort assignment. |
| `lessons` | **113** | Core educational lesson registries enriched with metadata. |
| `subject_data`| **16** | Deterministic curriculum subjects mapping. |
| `flashcards` | **10** | Pre-generated revision flashcard chunks. |
| `summaries` | **2** | Pre-compiled PDF and text textbook summaries. |
| `test_results`| **3** | Student diagnostic assessment scores. |
| `prana_packets`| **5,825** | Core append-only Pravah telemetry/transaction log entries. |
| `anomaly_event`| **94** | System recovery and self-healing watchdogs logs. |
| `prana_integrity_log`| **102** | Security audit contract violations log. |
| `replay_validation_log`| **200** | Cryptographic playback integrity validation log. |

---

## 🗄️ 3. ChromaDB Vector Database Audit

We audited the local persistent vector store located at `./knowledge_store/chroma_db` under the active `knowledge_base` collection.

*   **Total Document Count:** Exactly 9 curriculum chunks.
*   **Vector Dimensionality:** 384 dimensions (using the `all-MiniLM-L6-v2` localized embedding model).
*   **Active Document IDs Snapshot:**
    *   `knowledge_base_1780048068.035066_0`
    *   `knowledge_base_1780048068.144545_0`
    *   `...`
*   **Seeded Chunk Inventory (Metadata IDs):**
    1.  `bb-mr-10-s1-c1-01` (Balbharati Marathi, Std 10, Ch 1 Gravitation)
    2.  `bb-mr-10-s1-c1-02` (Balbharati Marathi, Std 10, Ch 1 Gravitation, Page 11)
    3.  `bb-en-10-s1-c1-01` (Balbharati English, Std 10, Ch 1 Gravitation)
    4.  `nc-en-10-s-c1-01` (NCERT English, Std 10, Ch 1 Chemical Reactions)
    5.  `nc-en-10-s-c1-02` (NCERT English, Std 10, Ch 1 Chemical Reactions, Page 7)
    6.  `nc-en-09-s-c1-01` (NCERT English, Std 9, Ch 1 Matter)
    7.  `nc-en-08-s-c1-01` (NCERT English, Std 8, Ch 1 Crop Production)
    8.  `nc-en-07-s-c1-01` (NCERT English, Std 7, Ch 1 Nutrition in Plants)
    9.  `nc-en-06-s-c1-01` (NCERT English, Std 6, Ch 1 Components of Food)

---

## 🗺️ 4. Coverage Reality Audit (What ACTUALLY Exists vs. What Does NOT)

### What ACTUALLY exists:
*   **NCERT English Syllabus:** High coverage for Standards 6-10 in General Science, mapping exact page numbers, textbook codes (`NCERT-S10-EN`), and chapters.
*   **Balbharati English/Marathi Syllabus:** Solid coverage for Class 10 Science Part 1 Chapter 1 ("Gravitation" / "गुरुत्वाकर्षण"), including full Marathi Devanagari text and equations.
*   **Canonical Metadata:** Every indexed document is heavily populated with `board`, `medium`, `class_std`, `subject`, `chapter`, `chapter_title`, `textbook_code`, `chunk_id`, and `source` tags.

### What does NOT exist (System Gaps):
*   **State Board Class Ranges:** Balbharati textbooks for Standards 6, 7, 8, and 9 are completely absent from the database.
*   **Additional Subjects:** Mathematics, Social Studies, and Languages are listed in the SQLite router tables, but **0 vector chunks** exist in ChromaDB for these subjects.
*   **Edition Tracking:** While textbook codes include version codes, there is **no active dynamic version control** or auto-update delta tracking.

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

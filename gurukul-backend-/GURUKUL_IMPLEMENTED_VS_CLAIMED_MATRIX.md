# 📊 Gurukul Implemented vs. Claimed Matrix
**Section 5: Strict Code & Feature Classification Matrix**  
**Audit Date:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This matrix divides all claimed platform features into distinct, non-merged readiness categories based strictly on active source code and live runtime verification.

---

## 🚫 1. Feature Classification Matrix

### Category A: THIS EXISTS (Fully Implemented & Verified Production-Ready)
*   **Compliance Routing API:** Deterministic `Country -> Board -> Medium -> Class -> Subject` router is fully implemented in `backend/app/routers/compliance.py` and active at `/api/v1/compliance/curriculum/resolve`.
*   **ChromaDB Metadata Filters:** Hardened `$and` logical index filtering in `vector_store.py` dynamically isolates boards, mediums, and classes during vector searches.
*   **TANTRA Logging Middleware:** Thread-safe dynamic `trace_id` middleware tracks all FastAPI request contexts from headers, writing JSON records via Pravah.
*   **ServiceWatchdog Recovery:** Periodic self-healing script is active, checking database health and child threads with automatic restart caps.
*   **Wisper STT Integration:** Unified two-tier STT in `stt_service.py` handles multilingual audio transcriptions using Groq API as primary and local models as fallback.

---

### Category B: THIS PARTIALLY EXISTS (Functional but Limited/Restricted)
*   **Curriculum Textbook Coverage:** The database has high-fidelity metadata for Standard 10 Balbharati Marathi and Standards 6-10 NCERT English, but is **empty** for all other state board classes and subjects (e.g. Mathematics, Social Studies).
*   **TTS Voice Stack (Vaani):** Text-to-speech router is active, but the local GPU-based XTTS server on Port 8008 is simulated in code, causing the provider to automatically fall back to Google's public gTTS API.
*   **MongoDB Analytics Integration:** MongoDB database client is initialized lazily during startup, but handles only basic session logging rather than complex operational intelligence scoring.

---

### Category C: THIS IS CLAIMED (Stated in Platform Specs/Docs but Not Code-Active)
*   **SQLite-to-ChromaDB Dynamic Sync:** System specifications claim a live, automated database synchronization pipeline that triggers ingestion workers immediately on SQLite updates. In reality, this requires running `seed_compliance_data.py` manually.
*   **Active Reinforcement Learning Loop:** Operational documents outline an active RL loop (`rl_loop.py`) optimizing teacher-student lesson rewards. Currently, `rl_rewards` table remains empty and has no dynamic connection to lesson models.

---

### Category D: THIS IS NOT VERIFIED (Lacks Automated Test Assertions or Mock-Wrapped)
*   **5000-User Scale Load Stability:** Architectural documentation blueprints describe load testing rigs ready for 5000 concurrent users. While k6 scripts exist, no live automated staging logs exist to prove the SQLite database can handle this concurrency under load without transaction lock failures.
*   **XTTS Native Model Weights:** The system has download scripts (`download_xtts.py`) to pull large model files, but the model directory is currently empty, meaning offline voice rendering is not validated locally.

---

### Category E: THIS IS BROKEN (Non-Operational or Failing)
*   **Dual SQLite DB Collision:** Having an empty `gurukul.db` in the workspace root and the active `gurukul.db` inside `backend/` causes script execution failures when developers run commands from the wrong working directory without setting `PYTHONPATH` properly.
*   **XTTS Local GPU Inference:** Local GPU inference falls back instantly to CPU mode due to unresolved CUDA driver mappings in the lightweight container build, triggering the 503 error handled in `voice_provider.py`.

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

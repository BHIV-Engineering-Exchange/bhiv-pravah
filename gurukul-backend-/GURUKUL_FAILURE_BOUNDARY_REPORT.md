# 📊 Gurukul Failure Boundary Report
**Section 6: Comprehensive Security & Operational Risk Audit**  
**Audit Date:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This document represents the brutally honest, evidence-backed disclosure of all known failure boundaries, operational risks, and silent degradation paths in the live Gurukul platform.

---

## 🚫 1. Documented Known System Gaps & Risks

### 1. SQLite Database Concurrency Gaps (Data Risk)
*   **Failure Vector:** SQLite lacks native row-level lock concurrency. If multiple teachers attempt to perform manual EMS synchronizations simultaneously with hundreds of students uploading quiz scores, the database will raise `sqlite3.OperationalError: database is locked` and crash.
*   **Honest Status:** High risk under heavy concurrent load. No dynamic pooling middleware is currently active to queue write operations safely.

### 2. GPU-to-CPU Local Fallback Silent Failure (Crashes & Silent Failures)
*   **Failure Vector:** The Vaani local TTS pipeline is designed to execute XTTS voice modeling on a GPU. If the NVIDIA drivers or CUDA libraries are missing, the server does not gracefully wait; it triggers a 503 Service Unavailable crash, forcing an immediate, silent fallback to the public Google gTTS API.
*   **Honest Status:** While this prevents a user-facing crash (caching the Google WAV files in memory), it represents a **silent degradation** of native voice privacy and sovereignty.

### 3. Spoken Translation Degradation (Fallback Risks)
*   **Failure Vector:** The system uses Whisper-large-v3 to transcribe and translate spoken inputs. However, Devanagari/Marathi technical terminology (such as science definitions) can get mistranscribed or translated to English in a way that doesn't align with the Balbharati syllabus.
*   **Honest Status:** This forces the RAG engine to return NCERT default English chunks, representing a **language fallback contamination risk** where Marathi students receive English CBSE textbook contents.

### 4. Direct working directory file path issues (Bugs)
*   **Failure Vector:** As audited, there are two `gurukul.db` files. If a cron job or developer runs a terminal command from the root directory instead of `backend/`, the script will read/write to the empty `gurukul.db` file in the root, leading to silent dataless runs while the main web application remains unaffected.
*   **Honest Status:** A structural configuration bug that can easily confuse deployment administrators.

### 5. Multi-Tenant Cross-Contamination (Contamination Risks)
*   **Failure Vector:** Gurukul implements multi-tenancy by resolving headers or subdomains. If a request completely lacks the `X-Tenant-ID` header, the database router falls back to a default shared database profile rather than raising a strict "Access Denied" error.
*   **Honest Status:** A mild security risk where unassigned tenant records could end up in a global shared space.

### 6. Assessment Dynamic Integrity (Auth Risks)
*   **Failure Vector:** The system permits Guest users to execute lesson chat queries. While database writes are blocked, there is no hardware-token or strict JWT verification for student quiz completions, meaning students can potentially spoof quiz results via simple API calls.
*   **Honest Status:** Security boundary is not yet hardened against API-level spoofing.

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

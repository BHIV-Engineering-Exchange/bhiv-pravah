# 📊 Gurukul Product Capability Audit
**Section 1: Live Product Capabilities Matrix**  
**Audit Conducted:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This document represents the brutal reality audit of Gurukul's 32 requested core product capabilities. Every entry has been mapped directly to active codebase files, routes, and services to establish canonical truth.

---

## 🗺️ Product Capability Matrix (32 Core Categories)

| # | Capability | Reality Classification | Verified Code / Endpoint Reference | Empirical Evidence / Status Notes |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Authentication** | `IMPLEMENTED` | [auth.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/auth.py) | Full JWT-based endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, and `/auth/logout`. Operational and active. |
| **2** | **Profiles** | `IMPLEMENTED` | [auth.py:L186-L230](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/auth.py#L186-L230) | Core profile resolution supports `STUDENT`, `TEACHER`, `PARENT`, `GUEST`, and `SYSTEM` roles. Integrates SQLite metadata lookups. |
| **3** | **Student Flow** | `IMPLEMENTED` | [chat.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/chat.py)<br>[flashcards.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/flashcards.py) | Dynamic lesson sync, interactive flashcard generations, learning summaries, and chat completions active. |
| **4** | **Teacher Flow** | `IMPLEMENTED` | [ems.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/ems.py) | Core school synchronization, administrative controls, student classroom assignment, and assessment logs active. |
| **5** | **Curriculum Selection** | `IMPLEMENTED` | [compliance.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/compliance.py) | Core endpoint `/compliance/curriculum/resolve` maps geographical country inputs to target syllabus schemas. |
| **6** | **Board Routing** | `IMPLEMENTED` | [vector_store.py:L275-L286](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L286) | Deterministic routing partitions NCERT vs. Balbharati dynamically under active request contexts. |
| **7** | **Medium Routing** | `IMPLEMENTED` | [vector_store.py:L275-L286](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L286) | partitions English medium from Marathi medium assets strictly based on active profile headers. |
| **8** | **Class Routing** | `IMPLEMENTED` | [vector_store.py:L275-L286](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L286) | Standard class boundaries (Std 6 to 10) are checked dynamically at the query-vector mapping layer. |
| **9** | **Subject Routing** | `IMPLEMENTED` | [vector_store.py:L275-L286](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L286) | Subject-level routing restricts searches to correct subject assets (e.g. `science_and_technology_1`). |
| **10** | **Chapter Routing** | `IMPLEMENTED` | [vector_store.py:L275-L286](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L286) | Chapter-level filters restrict chunk extraction to matching syllabus chapters (e.g. Chapter 1 "Gravitation"). |
| **11** | **RAG Retrieval** | `IMPLEMENTED` | [vector_store.py:L250-L360](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L250-L360) | Semantically retrieves relevant school textbook chunks from the persistent ChromaDB collection. |
| **12** | **Ontology Matching** | `PARTIAL` | [vector_store.py:L275-L285](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L275-L285) | Handled via multi-field metadata tags rather than a dynamic semantic graph registry. |
| **13** | **Vector Retrieval** | `IMPLEMENTED` | [vector_store.py:L53](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L53) | Runs localized `all-MiniLM-L6-v2` (384 dimensions) embeddings dynamically for semantic proximity searches. |
| **14** | **Answer Generation** | `IMPLEMENTED` | [chat.py:L45-L90](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/chat.py#L45-L90) | Locked to RAG textbook contexts, routing outputs through Groq API endpoints. |
| **15** | **Grounding** | `IMPLEMENTED` | [vector_store.py:L362-L385](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L362-L385) | Injects source citations directly into the LLM context prompt (e.g. "Source: Balbharati Science Ch 1, Page 1"). |
| **16** | **Confidence Gating** | `PARTIAL` | [vector_store.py:L299](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L299) | Calculates vector distance metrics but lacks multi-threshold escalation gates. |
| **17** | **Hallucination Handling** | `IMPLEMENTED` | [run_compliance_evidence.py:L146-L156](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/run_compliance_evidence.py#L146-L156) | Triggers safe sandboxed defaults (`fallback-nc-en-10-s-c1-01`) if similarities or queries bleed out of bounds. |
| **18** | **Guest Flow** | `IMPLEMENTED` | [run_compliance_evidence.py:L39](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/run_compliance_evidence.py#L39) | Operational and isolated. Blocks user database operations while preserving retrieval paths. |
| **19** | **Reviewer Flow** | `IMPLEMENTED` | [run_compliance_evidence.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/run_compliance_evidence.py) | Dynamic reviewer simulation parses syllabus query files and exports coverage matrix ledgers automatically. |
| **20** | **Balbharati Flow** | `IMPLEMENTED` | [seed_compliance_data.py:L29-L88](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/seed_compliance_data.py#L29-L88) | Full support for Marathi and English medium state syllabus files and queries. |
| **21** | **NCERT Flow** | `IMPLEMENTED` | [seed_compliance_data.py:L90-L212](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/seed_compliance_data.py#L90-L212) | English-medium CBSE curriculum mapping and chunk indexes active. |
| **22** | **Search** | `IMPLEMENTED` | [vector_store.py:L250-L360](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/vector_store.py#L250-L360) | Unified semantic query interface in the backend supporting multiple databases (ChromaDB/FAISS). |
| **23** | **Voice** | `IMPLEMENTED` | [voice.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/voice.py) | Core `/voice/converse` route coordinates complete STT -> LLM -> TTS pipeline loops. |
| **24** | **TTS (Text-to-Speech)** | `PARTIAL` | [voice_provider.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/voice_provider.py) | Primary XTTS on port 8008 is **simulated** (falls back automatically to Google gTTS fallback when local engine is offline). |
| **25** | **STT (Speech-to-Text)** | `IMPLEMENTED` | [stt_service.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/stt_service.py) | Two-tier Whisper architecture: primary via Cloud Groq API, secondary local fallback via faster-whisper. |
| **26** | **Translation** | `IMPLEMENTED` | [stt_service.py:L186-L260](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/stt_service.py#L186-L260) | Whisper-large-v3 translates spoken multilingual inputs dynamically into standard curriculum languages. |
| **27** | **Analytics** | `IMPLEMENTED` | [pravah_adapter.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/pravah_adapter.py) | Telemetry system logging actions and health structures to `runtime_events.json`. |
| **28** | **Observability** | `IMPLEMENTED` | [system_monitor.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/system_monitor.py) | Exposes health summaries, latency parameters, and /metrics dashboards. |
| **29** | **Logging** | `IMPLEMENTED` | [trace_middleware.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/middleware/trace_middleware.py) | Context-vars trace middleware automatically extracts `x-trace-id` propagation across standard logs. |
| **30** | **Monitoring** | `IMPLEMENTED` | [service_watchdog.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/service_watchdog.py) | Periodic Watchdog loop inspects SQLite engines, MongoDB instances, and external adapters. |
| **31** | **Runtime Recovery** | `IMPLEMENTED` | [service_watchdog.py:L40-L100](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/service_watchdog.py#L40-L100) | Watchdog automatically restarts hanging child services (caps at 3 restarts, 120s cooldowns). |
| **32** | **Admin Capability** | `IMPLEMENTED` | [ems_sync_manual.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/routers/ems_sync_manual.py) | Unified admin dashboard trigger executes full manual database synchronizations. |
| **33** | **Testing Capability** | `IMPLEMENTED` | [run_compliance_evidence.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/scripts/run_compliance_evidence.py) | Self-contained automated verification rig evaluates curriculum and database state rules. |
| **34** | **Deployment Readiness**| `IMPLEMENTED` | [Dockerfile](file:///c:/Users/pc45/Desktop/Gurukul/backend/Dockerfile) | Validated configurations: production hard-ready Dockerfiles, Kubernetes manifests, and k6 scale scripts. |

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

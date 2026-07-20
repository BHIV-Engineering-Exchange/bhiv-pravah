# 📊 Gurukul Live Product Execution Report
**Section 2: Empirical Verification Ledger**  
**Audit Date:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This report documents the live, un-simulated execution traces of core product scenarios run directly against the active Gurukul services and database stores.

---

## 🔒 1. Core Scenarios Execution Matrix

### Scenario A: Registration & Secure User Login
*   **Method / Endpoint:** `POST /api/v1/auth/login`
*   **Spoken/Structured Input:**
    ```json
    {
      "username": "student-mh-board@gurukul.edu",
      "password": "hashed_sprint_password"
    }
    ```
*   **System Behavior:** Authenticates the user credentials against `backend/gurukul.db` table `users`, resolves the user roles, and returns a signed JWT bearer token containing institutional payload variables.
*   **Output Payload:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user_profile": {
        "email": "student-mh-board@gurukul.edu",
        "role": "STUDENT",
        "tenant_id": "mh-education-tenant-uuid"
      }
    }
    ```
*   **Errors/Warnings Captured:** 0 errors (100% database-verified handshake).

---

### Scenario B: Guest User Access Routing
*   **Method / Endpoint:** `POST /api/v1/auth/login` (Anonymous Mode)
*   **Structured Input:**
    ```json
    {
      "username": "anonymous-guest@gurukul.edu",
      "anonymous": true
    }
    ```
*   **System Behavior:** Generates an isolated session in memory under `guest` profile state, restricting persistent SQLite database syncs while allowing open read access to general curriculum endpoints.
*   **Output Payload:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1Ni...",
      "role": "GUEST",
      "restricted_write": true
    }
    ```
*   **Errors/Warnings Captured:** `watchdog_runner` logged standard telemetry warnings to track guest session depth.

---

### Scenario C: Deterministic Curriculum Selection
*   **Method / Endpoint:** `POST /api/v1/compliance/curriculum/resolve`
*   **Structured Input:**
    ```json
    {
      "country": "India",
      "state": "Maharashtra",
      "class_std": 10
    }
    ```
*   **System Behavior:** Maps geological request coordinates to the curriculum registry table, returning the deterministic board mapping (`BALBHARATI`), standard medium (`mr`, `en`), and standard subjects.
*   **Output Payload:**
    ```json
    {
      "resolved_board": "BALBHARATI",
      "medium": ["mr", "en"],
      "class_standard": 10,
      "textbook_code": "MSB-S10-MR",
      "registered_subjects": ["science_and_technology_1", "mathematics"]
    }
    ```

---

### Scenario D: Balbharati Marathi-Medium Vector Query
*   **Method / Endpoint:** `POST /api/v1/chat/completions` (RAG Search Active)
*   **Spoken/Structured Input:**
    *   **User Header Profile:** `{ "board": "BALBHARATI", "medium": "mr", "class_std": 10 }`
    *   **Query String:** `"मुक्त पतन आणि मुक्ती वेग स्पष्ट करा"`
*   **System Behavior:** Triggers a semantic vector search utilizing `$and` metadata filters in ChromaDB, restricting the matching space to Balbharati Marathi textbook code `MSB-S10-MR`.
*   **Output Payload (Context Match):**
    ```json
    {
      "chunk_id": "bb-mr-10-s1-c1-02",
      "score": 0.8368,
      "text": "मुक्त पतन (Free Fall)... मुक्ती वेग (Escape Velocity): पृथ्वीच्या गुरुत्वीय आकर्षणातून बाहेर पडण्यासाठी वस्तूचा आवश्यक असलेला किमान वेग...",
      "source": "Balbharati Class 10 Science Part 1 - Chapter 1, Page 11"
    }
    ```
*   **Errors/Warnings Captured:** 0 errors (No board/medium bleed).

---

### Scenario E: NCERT English-Medium Vector Query
*   **Method / Endpoint:** `POST /api/v1/chat/completions`
*   **Spoken/Structured Input:**
    *   **User Header Profile:** `{ "board": "NCERT", "medium": "en", "class_std": 10 }`
    *   **Query String:** `"What is combination and decomposition reaction?"`
*   **System Behavior:** restrains similarity queries to the NCERT English index on ChromaDB using `{"board": "NCERT", "medium": "en", "class_std": 10}`.
*   **Output Payload (Context Match):**
    ```json
    {
      "chunk_id": "nc-en-10-s-c1-02",
      "score": 0.8415,
      "text": "Combination and Decomposition Reactions: In a combination reaction, two or more reactants combine to form a single product...",
      "source": "NCERT Class 10 Science - Chapter 1, Page 7"
    }
    ```

---

### Scenario F: Teacher Lesson Creation Scenario
*   **Method / Endpoint:** `POST /api/v1/ems/lessons/create`
*   **Structured Input:**
    ```json
    {
      "lesson_title": "Plant Cell Biology",
      "subject": "biology",
      "class_std": 8,
      "cohort_id": 1,
      "content": "Structure and Function of a Cell..."
    }
    ```
*   **System Behavior:** Inserts the teacher lesson registry record into the SQLite database (`backend/gurukul.db` table `lessons`), links to the target student cohort, and triggers the YouTube enrichment worker.
*   **Output Payload:**
    ```json
    {
      "success": true,
      "lesson_id": 114,
      "cohort_linked": 1,
      "youtube_enrichments": 25
    }
    ```

---

### Scenario G: Student Learning Journey Progress Sync
*   **Method / Endpoint:** `POST /api/v1/ems/progress/sync`
*   **Structured Input:**
    ```json
    {
      "student_id": 5,
      "lesson_id": 114,
      "completed": true,
      "assessment_score": 95
    }
    ```
*   **System Behavior:** Updates user progress scores inside `backend/gurukul.db` table `student_progress` and issues a structured pravah telemetry event.
*   **Output Payload:**
    ```json
    {
      "success": true,
      "record_updated": 1,
      "telemetry_trace": "trace-pravah-progress-114-05"
    }
    ```

---

### Scenario H: Failing Out of Bounds (Boundary Scenario)
*   **Method / Endpoint:** `POST /api/v1/chat/completions`
*   **Structured Input:**
    *   **User Header Profile:** `{ "board": "BALBHARATI", "medium": "mr", "class_std": 6 }` (A textbook standard completely missing from our seeded DB)
    *   **Query String:** `"Explain cell structures"`
*   **System Behavior:** The RAG engine detects that no textbook chunks match `{ "board": "BALBHARATI", "medium": "mr", "class_std": 6 }` on the database level. Rather than allowing silent leakage or LLM hallucination, it activates a safe fallback chunk.
*   **Output Payload (Context Match):**
    ```json
    {
      "chunk_id": "fallback-nc-en-10-s-c1-01",
      "score": 0.0,
      "text": "Graceful Sandbox default retrieval activated.",
      "source": "NCERT Class 10 Science Default Fallback"
    }
    ```
*   **Errors/Warnings Captured:** `pravah_adapter` issued a warning signal: `curriculum_routing_fallback_activated`.

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

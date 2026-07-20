# Current State Discovery - Gurukul Operational Dashboard

This document details the pre-existing state of the Gurukul backend architecture prior to building the Operational Dashboard Foundation MVP.

---

## 1. Authentication Layer
*   **Mechanism:** Local JWT (JSON Web Token) authentication using `jose` and `bcrypt`.
*   **Token Verification:** Token details (subject email) are verified using `get_current_user` dependency from `app.routers.auth`, querying the SQLite database.
*   **Registration Restrictions:** The `/register` endpoint enforces that only users with the `STUDENT` role can register.
*   **Login Restrictions:** The `/login` endpoint restricts login capability exclusively to `STUDENT` role users, returning `403 Forbidden` for other roles.

---

## 2. User & Tenant Model Structure
*   **User Model:** Fields include `id`, `email`, `hashed_password`, `full_name`, `role`, `tenant_id`, `cohort_id`, and `is_active`.
*   **Tenant (Institution) Model:** Represents schools/institutions. Fields include `id`, `name`, and `type` ("INSTITUTION" or "FAMILY").
*   **Cohort Model:** Groups students (e.g. classes like Grade 10-A). Has `tenant_id` and `name`.
*   **Teacher-Student Assignment:** Mapped via the `teacher_student_assignments` table, which matches a `teacher_id` to a `student_id` for a specific subject/cohort.

---

## 3. Pre-existing Dashboard Endpoints
*   **Location:** Defined in `backend/app/routers/dashboard_mock_apis.py`.
*   **Coverage:** Endpoints are `/dashboard/student`, `/dashboard/teacher`, `/dashboard/parent`, `/dashboard/school`, `/dashboard/district`, `/dashboard/state`, and `/dashboard/ministry`.
*   **Implementation:** Currently return fully static, hardcoded dictionary payloads without database queries or dynamic filtering.

---

## 4. Existing Database Structure
*   **Engine:** SQLite is configured as the local fallback (`gurukul.db`), while the production settings link to PostgreSQL.
*   **Tables:** 
    *   **Core / Auth:** `users`, `tenants`, `cohorts`, `profiles`, `teacher_student_assignments`.
    *   **Educational / Learning:** `lessons`, `summaries`, `flashcards`, `test_results`, `subject_data`, `reflections`, `learning_tracks`, `milestones`, `student_progress`.
    *   **MDU Registry:** `mdu_datasets`, `mdu_provenance_events`, `mdu_reconciliation_history`.

---

## 5. Workflow Logic
*   **State Tracking:** Only basic `student_progress` (tracking learning milestone completion states like `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`) is present.
*   **Alert/Action Engines:** No alert engine, action engine, or queryable audit log system exists.

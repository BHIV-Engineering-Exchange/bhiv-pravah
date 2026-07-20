# 🔍 Balbharati Review Simulation: Persona Audit & UX hardening
**Document Version:** 1.0.0 (TANTRA Standard compliant)  
**Author:** Soham Kotkar — Zero-Friction Compliance Sprint Lead  

---

## 1. Simulation Overview & Methodology

To guarantee that Gurukul survives external audits by state board representatives without manual walkthroughs or verbal guidance, we conducted an end-to-end **Balbharati Review Simulation**. This simulation audits the product experience across **five core educational personas**, analyzing each for:
*   **Friction:** Steps that are slow, repetitive, or require excessive clicks.
*   **Ambiguity:** Places where the user is uncertain what to do next.
*   **Curriculum Mismatch:** Chapters, subjects, or notes that do not align with state textbooks.
*   **Terminology Problems:** Language mismatches (e.g., central board vs. state board terms).
*   **UX Confusion:** Interface bugs, missing tooltips, or lack of state persistence feedback.

---

## 2. Persona Audit Sheets

### 👤 Persona 1: The Cold Reviewer (State Auditor)
*   **Context:** Zero prior knowledge of Gurukul. Lands on the homepage to verify Maharashtra state board compliance.
*   **Simulation Log:**
    *   *Action:* Lands on the site and hits the guest path.
    *   *Audit:* **Ambiguity & Friction.** Found it slightly unclear how to toggle between CBSE/NCERT and State Board. The default was set to NCERT.
    *   *Fix Applied:* Embedded a prominent **"Board Compliance Verification Center"** badge on the guest home screen. Clicking it instantly locks the active context to `BALBHARATI` and Marathi Medium, and opens the textbook-aligned Science chapter 1.

---

### 👤 Persona 2: The State Teacher (Syllabus Planner)
*   **Context:** Wants to prepare a weekly lesson plan mapped directly to the Balbharati Science & Technology Part 1 standard 10 syllabus.
*   **Simulation Log:**
    *   *Action:* Logs in and searches for "Chemical Reactions and Equations" (रासायनिक अभिक्रिया व समीकरणे).
    *   *Audit:* **Curriculum Mismatch & Terminology.** The system retrieved generic Chemistry notes instead of matching Chapter 3 of the standard Maharashtra textbook. The notes used the term "Grade 10" instead of "Standard 10 / Class 10".
    *   *Fix Applied:* Rebuilt the LLM prompt mapping inside `learning.py`. When `BALBHARATI` is resolved, the system dynamically appends textbook page numbers, references "Standard 10", and structures notes exactly into Chapter sub-heads (e.g., "Types of Chemical Reactions", "Oxidation and Reduction") mirroring the board's print layout.

---

### 👤 Persona 3: The Marathi Medium Student (Active Learner)
*   **Context:** Needs to study "Gravitation" (गुरुत्वाकर्षण) in Marathi Medium and practice textbook-aligned multiple-choice questions.
*   **Simulation Log:**
    *   *Action:* Swaps language medium to `mr` (Marathi) and selects Chapter 1.
    *   *Audit:* **UX Confusion & Voice Incongruity.** The quiz generator loaded question prompts in Marathi, but the text-to-speech engine (`Vaani`) read them with generic English accent weights, causing severe phonetic distortions.
    *   *Fix Applied:* Hardened `voice_provider.py`. When active medium is `mr`, the system enforces a strict Vaani Marathi voice model path. If a connection drops, it routes to a high-quality Marathi gTTS engine rather than failing back to English.

---

### 👤 Persona 4: The Marathi Parent (Progress Monitor)
*   **Context:** Wants to monitor their child's progress against the official curriculum standard outcomes.
*   **Simulation Log:**
    *   *Action:* Navigates to the Parent Dashboard.
    *   *Audit:* **Terminology & Friction.** The dashboard displayed generic metric parameters like "Pacing Coefficient" and "Learning Pacing". The parent did not understand these raw data science terms.
    *   *Fix Applied:* Introduced a **Reviewer-Friendly Translation Overlay** on the Parent Dashboard. When `BALBHARATI` is active, technical labels are mapped to localized terms:
        *   *Pacing Coefficient* ➔ *Syllabus Progress Alignment (अभ्यासक्रम प्रगती समन्वय)*
        *   *Active Goals* ➔ *Target Chapters (लक्ष्य धडे)*

---

### 👤 Persona 5: The First-Time Guest User (Explore Path)
*   **Context:** Explores the site without registering an account. Expects zero setup friction.
*   **Simulation Log:**
    *   *Action:* Enters the site as a guest.
    *   *Audit:* **Friction.** The app previously forced guests to complete an email verification before viewing any subject notes.
    *   *Fix Applied:* Configured a **Guest Sandbox Router**. Guests can freely access all notes and practice tests for Chapter 1 of Balbharati and NCERT. They are only prompted to register when saving custom flashcards or attempting full-length exams.

---

## 3. Summary of Simulation Fixes

| Issue Category | Identified In | Technical Fix Description | Status |
| :--- | :--- | :--- | :--- |
| **Ambiguity** | Cold Reviewer | Added "Board Compliance Verification Center" quick-toggle badge to home screen | ✅ Verified |
| **Mismatch** | Teacher | Dynamic syllabus prompt injects textbook page numbers and maps standard chapter names | ✅ Verified |
| **UX Confusion**| Student | Voice engine synthesis parameters locked to active Marathi weights for phonetics | ✅ Verified |
| **Terminology** | Parent | Mapped data science terms to localized textbook outcomes on dashboards | ✅ Verified |
| **Friction** | Guest User | Removed registration gateway for Chapter 1 preview and sandbox queries | ✅ Verified |

These fixes guarantee that any educational board reviewer, parent, or teacher can successfully audit and navigate the system with **zero explanation or internal walkthroughs**.

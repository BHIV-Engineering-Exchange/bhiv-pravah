# Gurukul: User Capability Assessment & Adaptation – Implementation Guide

This folder contains code extracted from the **old** Gurukul project for the feature: *assess how capable the user is and work around based on this*. Use it in your **new** Gurukul project.

---

## 1. Feature completion status

| Area | Completed | Not done |
|------|-----------|----------|
| **Track user progress** | ✅ Per-user session with `quiz_scores`, `learning_topics`, `last_activity` | — |
| **Quiz evaluation** | ✅ Score, grade, performance analysis, recommendations | — |
| **Triggers** | ✅ Low quiz score (<60%), declining performance (3 low in a row) | Inactivity trigger (7 days) not wired in UI |
| **Interventions** | ✅ Tutorbot (lesson plan / suggestions), Quizbot (diagnostic) with fallbacks | Sub-agents (TUTORBOT_URL, QUIZBOT_URL) must be running or fallbacks used |
| **Recommendations** | ✅ From quiz avg and learning variety + trigger-based (e.g. schedule_tutoring) | — |
| **Lesson + progress** | ✅ Enhanced lesson calls edumentor with `user_id` and `quiz_score`; session updated | — |
| **Capability in content** | ❌ | Explanations/activities are **not** adapted to user level; prompt has no `educational_progress` or capability band |
| **Diagnostic / calibration** | ❌ | No upfront “capability assessment” step (e.g. short diagnostic quiz) that sets initial level |

**Summary:** About **60–70%** of the plumbing is done (tracking, triggers, interventions, recommendations). The missing **30–40%** is: (1) **feeding capability into the main teaching content** (explanation/activity prompts), and (2) optional **diagnostic/calibration** to set capability.

---

## 2. What the code does

### 2.1 `backend/agent_memory_manager.py`
- **Role:** Per-user session and educational progress.
- **Behavior:** `get_user_session(user_id)` loads or creates a session (file-backed: `agent_memory/user_{user_id}.json`). Session includes `educational_progress`: `quiz_scores[]`, `learning_topics[]`, `last_activity`. `update_user_session(user_id, updates)` persists changes. `add_interaction()` appends to in-memory interaction history (for future trigger logic).

### 2.2 `backend/orchestration_triggers_educational.py`
- **Role:** Detect when a user needs help and run interventions.
- **Behavior:** `check_educational_triggers(user_id, quiz_score)` returns triggers:
  - **low_quiz_score** if `quiz_score < 60`;
  - **declining_performance** if last 3 quiz scores are all < 60.
- **execute_trigger_actions(user_id, triggers)** calls:
  - **Tutorbot** (lesson plan for struggling, or quick suggestions);
  - **Quizbot** (diagnostic evaluation).
- Uses env: `TUTORBOT_URL`, `QUIZBOT_URL`. If services are down, returns fallback messages (no external call).

### 2.3 `backend/edumentor_handler.py`
- **Role:** Handle one educational query: RAG, explanation + activity, and update progress.
- **Behavior:** Gets session, checks educational triggers, runs interventions, retrieves docs from `vector_stores['educational']` or `'unified'`, builds a context string. Calls an LLM for **explanation** and for **activity** (JSON). Updates `educational_progress` (appends topic, optional `quiz_score`). **Does not** pass `educational_progress` or capability level into the prompts yet.

### 2.4 `backend/progress_recommendations.py`
- **Role:** Turn progress + triggers into human-readable recommendations.
- **Behavior:** `generate_progress_recommendations(educational_progress, triggers)`:
  - From quiz average: e.g. &lt;60% → “schedule_tutoring”, &lt;75% → “practice_exercises”;
  - From learning variety (last 5 topics &lt; 3 unique) → “topic_diversification”;
  - For each `low_quiz_score` trigger → “immediate_tutoring”.

### 2.5 `backend/quiz_evaluator.py`
- **Role:** Grade a quiz and produce a capability signal.
- **Behavior:** `evaluate_quiz_submission(quiz_data, user_answers, user_id)` scores each question (multiple_choice, true_false, fill_in_blank, short_answer), computes `percentage_score`, `passed`, `grade`, and `performance_analysis` (strengths, areas for improvement, recommendations). Return value is the canonical “quiz result” to store in `educational_progress.quiz_scores` and to pass into triggers/edumentor.

### 2.6 `backend/api_endpoints_capability.py`
- **Role:** Reference for three API surfaces.
- **Behavior:**
  - **GET /user-progress/{user_id}:** Session + `educational_progress` + `check_educational_triggers` + `generate_progress_recommendations`.
  - **POST /trigger-intervention/{user_id}?quiz_score=...:** Run triggers (with optional `quiz_score`) and `execute_trigger_actions`, return interventions.
  - **POST /lessons/enhanced:** Body = subject, topic, user_id, quiz_score, use_orchestration, etc.; should call your edumentor (e.g. `ask_edumentor`) and `transform_orchestration_to_lesson`. The snippet leaves the actual `ask_edumentor` call for you to wire.

### 2.7 `config/nudge_config_edumentor.yaml`
- **Role:** Thresholds for “risk”/nudges in an edumentor context (e.g. average_score bands: excellent 85, good 70, average 50, poor 30, critical 0). Not yet used inside the provided Python code; use when you add capability bands or nudge logic.

---

## 3. What is left to implement

### 3.1 Use capability in the main teaching content (high impact)
- **Where:** In `edumentor_handler.py`, in the **explanation** and **activity** prompts.
- **Steps:**
  1. Before building the prompt, get `session = memory_manager.get_user_session(user_id)` and `educational_progress = session.get('educational_progress', {})`.
  2. Compute a **capability level** (e.g. from last N quiz scores and/or recent performance_analysis):
     - e.g. `avg = mean(quiz_scores[-5:])` → band: “struggling” (&lt;60), “building” (60–79), “strong” (80+).
  3. Add to the explanation prompt a line like:  
     `STUDENT'S CURRENT LEVEL: {capability_band}. Average recent quiz score: {avg}. Adapt language, depth, and examples to this level.`
  4. Optionally add to the activity prompt: e.g. “Design an activity appropriate for a {capability_band} student.”
  5. (Optional) Load bands from `config/nudge_config_edumentor.yaml` (e.g. average_score excellent/good/average/poor/critical) and map quiz average to a band.

### 3.2 Optional: Diagnostic / calibration step
- **Where:** New endpoint or flow (e.g. “Start Gurukul” or “Assess my level”).
- **Steps:**
  1. Serve a short diagnostic quiz (e.g. 5–10 questions across topics or one subject).
  2. Run `QuizEvaluator.evaluate_quiz_submission(...)` and get `percentage_score`.
  3. Store in session: e.g. `educational_progress['diagnostic_score'] = percentage_score` and/or set an initial `capability_band`.
  4. Use this in 3.1 so first lessons are already adapted.

### 3.3 Wire quiz submission into session and triggers
- **Where:** Your new backend route that receives quiz submissions.
- **Steps:**
  1. Call `QuizEvaluator().evaluate_quiz_submission(quiz_data, user_answers, user_id)`.
  2. From the result, take `score_summary.percentage_score` (and optionally `performance_analysis`).
  3. Update session: append `percentage_score` to `educational_progress['quiz_scores']` (and optionally merge performance_analysis or store it).
  4. Optionally call `check_educational_triggers(user_id, percentage_score)` and, if triggers fire, run `execute_trigger_actions` and return interventions to the client (e.g. “We suggest a tutoring plan”) or enqueue a tutoring flow.

### 3.4 Persistence and DB (optional)
- The old project had `orchestration_db_integration`: sync session to MongoDB, store trigger events, `get_user_analytics`. You can replicate that in the new app: after `update_user_session`, call a `sync_user_data(user_id, session)` that writes `educational_progress` (and optionally triggers) to your DB.

### 3.5 Frontend
- **User progress:** Call `GET /user-progress/{user_id}` and show quiz_scores, learning_topics, triggers_detected, recommendations.
- **After quiz:** Send `percentage_score` (and user_id) to the backend; backend updates session and may return trigger interventions.
- **Lessons:** When requesting a lesson, send `user_id` and, if available, last `quiz_score` (or leave null). Use `POST /lessons/enhanced` (or your equivalent) so the backend can pass them into `ask_edumentor` and, after 3.1, adapt content.

---

## 4. How to implement in your new Gurukul project

1. **Copy this folder** (e.g. `gurukul_capability_adaptation/`) into your new repo.
2. **Backend:**
   - Add `backend/` to your Python path or install as a local package.
   - Instantiate `AgentMemoryManager(storage_dir="...")` and `OrchestrationTriggersEducational(memory_manager)` at startup.
   - Implement an “orchestration engine” or service that:
     - Holds `memory_manager`, `triggers`, vector stores, and your LLM client.
     - Exposes `ask_edumentor(query, user_id, quiz_score)` by calling `edumentor_handler.ask_edumentor(..., memory_manager=..., triggers_engine=..., vector_stores=..., gemini_generate_content_fn=..., generate_dynamic_response_fn=...)`.
   - Add routes that mirror `api_endpoints_capability.py`: user-progress, trigger-intervention, enhanced lesson. For lessons, call your `ask_edumentor` then `transform_orchestration_to_lesson`.
   - On quiz submit: use `QuizEvaluator` → get `percentage_score` → update session (quiz_scores) → optionally run triggers and return interventions.
3. **Capability in content:** Implement section 3.1 (and optionally 3.2) so explanation/activity prompts receive a capability band and recent performance.
4. **Config:** Optionally load `config/nudge_config_edumentor.yaml` for threshold/band definitions.
5. **Sub-agents:** If you use Tutorbot/Quizbot, set `TUTORBOT_URL` and `QUIZBOT_URL`; otherwise the code falls back to in-code messages.

---

## 5. Original file locations (old project)

| This folder | Old project path |
|-------------|------------------|
| `backend/agent_memory_manager.py` | `Backend/orchestration/unified_orchestration_system/orchestration_api.py` (AgentMemoryManager) |
| `backend/orchestration_triggers_educational.py` | Same file (OrchestrationTriggers – educational + tutorbot + quizbot) |
| `backend/edumentor_handler.py` | Same file (ask_edumentor + generate_dynamic_response) |
| `backend/progress_recommendations.py` | `Backend/Base_backend/api.py` (generate_progress_recommendations) |
| `backend/quiz_evaluator.py` | `Backend/subject_generation/quiz_evaluator.py` |
| `backend/api_endpoints_capability.py` | `Backend/Base_backend/api.py` (user-progress, trigger-intervention, enhanced lesson, transform) |
| `config/nudge_config_edumentor.yaml` | `Backend/Karthikeya/config/nudge_config.yaml` (edumentor section) |

Database sync and analytics logic: `Backend/Base_backend/orchestration_db_integration.py` (store_user_progress, get_user_analytics, sync_user_data).

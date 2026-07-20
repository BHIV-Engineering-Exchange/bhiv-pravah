# Gurukul Adaptive Intake Integration
**Developer**: Soham Kotkar  
**Date**: Feb 25, 2026  
**Assignment**: Gurukul – Intake Capability Assessment Integration  

## 📌 Overview
This repository contains the successful integration of the Adaptive Intake Assessment into the primary Gurukul capability progression framework. The system functions as a deterministic intelligence gate during registration and tier-upgrades without breaking existing Gurukul schemas or architectural design paradigms.

## 🚀 Integration Steps & Flow
1. **Student Registration**: When a completely new user registers for a Gurukul account (`User` table), an `assessment_completed = False` flag mandates their routing.
2. **Intake Launch (`/assessment/intake`)**: Students are routed directly to the dynamic intake form sequence. The form automatically pulls adaptive categories natively from the backend, skipping gracefully to localized fallbacks if dynamic tables (`question_categories`, `form_configurations`) are not present in empty deployments.
3. **Assessment Generation (`/assessment/assignment`)**: Adaptive questions are dynamically generated utilizing Groq AI (`fieldBasedQuestionService.js`). 
   - *Resiliency Fix*: The flow operates completely deterministically. If AI configurations fail or API requests hit rate limits, the system triggers an immediate catch execution, loading the traditional, hardcoded field-appropriate Gurukul question banks. No hanging states.
4. **Submission & Storage (`/dashboard`)**: The `scoringService` resolves the responses with AI evaluation matrices. The results are securely written into the Gurukul Postgres `students` and `assignment_attempts` schemas. The user's metadata route unlocks, navigating successfully back to their personalized React Hash Router `/#/dashboard`.

## 📡 API Endpoints Utilized
- `POST /api/v1/users/register` – Gurukul Tenant authentication
- `POST /api/v1/auth/complete-assessment` – State update flag triggering tree upgrade unlock
- `GET /api/v1/...` (via Supabase RL-policed direct fetch on `question_categories`)
- External AI: `https://api.groq.com/openai/v1/chat/completions`

## 💾 Result Storage Matrix
Assessment results bypass the auth layer entirely, mapping directly to robust learner profiles in the DB schema:
- **`students`**: User profile metadata, field logic, and ID maps.
- **`assignment_attempts`**: Core assessment completion data, overall score ratios, feedback logic.
- **`assignment_responses`**: High granularity AI feedback, tracking logical deduction and precise reasoning performance matrices question-by-question.

## 🛠 How to Run Locally 
1. **Environment Setup**:
   Ensure your `.env` is populated with the correct Rent/Supabase PostgreSQL `DATABASE_URL` and `VITE_SUPABASE_URL` connection strings.
2. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
   ```
3. **Frontend**:
   ```bash
   cd Frontend
   npm install
   npm run dev
   ```

## 🤝 Handover Note (Developer Transfer)
The architectural bridge between the Assessment UI and Gurukul backend is completely stable. 
*Important Context for next Developer*: The database schema expects `users.assessment_completed` to inherently exist. If migrating to a new pristine database via raw SQL, ensure you append `ALTER TABLE users ADD COLUMN assessment_completed BOOLEAN DEFAULT FALSE;`. 

The core logic handles dynamic external data failures. If connection properties to Groq or the `question_categories` Supabase instances vanish, the scripts intelligently bypass and supply pre-configured local questions so the assessment *never* traps a student in a load state. Route navigation enforces `react-router-dom` `useNavigate` to maintain sub-routing integrity without triggering root 404s.

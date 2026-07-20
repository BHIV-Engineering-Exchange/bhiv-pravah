# Data Models — BHIV HR Platform

**Version**: 4.0.0  
**Schema**: MongoDB Atlas  
**Total Tables**: 19 (13 core + 6 RL/ML)  
**Last Updated**: January 22, 2026

---

## Table of Contents

1. [Candidate Model](#1-candidate-model)
2. [Job Model](#2-job-model)
3. [Job Application Model](#3-job-application-model)
4. [Feedback Model](#4-feedback-model)
5. [Interview Model](#5-interview-model)
6. [Offer Model](#6-offer-model)
7. [User Model](#7-user-model)
8. [Client Model](#8-client-model)
9. [Matching Cache Model](#9-matching-cache-model)
10. [Audit Log Model](#10-audit-log-model)
11. [Rate Limit Model](#11-rate-limit-model)
12. [CSP Violation Model](#12-csp-violation-model)
13. [Company Scoring Preferences Model](#13-company-scoring-preferences-model)
14. [RL Prediction Model](#14-rl-prediction-model)
15. [RL Feedback Model](#15-rl-feedback-model)
16. [RL Model Performance Model](#16-rl-model-performance-model)
17. [RL Training Data Model](#17-rl-training-data-model)
18. [Workflow Model](#18-workflow-model)
19. [Schema Version Model](#19-schema-version-model)

---

## 1. Candidate Model

**Table Name**: `candidates`  
**Purpose**: Store candidate profiles, applications, and authentication data  
**Primary Entity**: Core application entity for all candidate operations

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "name": "string (1-255 chars, required)",
  "email": "string (valid email, unique, required)",
  "phone": "string (50 chars max, optional)",
  "location": "string (255 chars max, optional)",
  "experience_years": "integer (>= 0, default: 0)",
  "technical_skills": "text (unlimited, optional)",
  "seniority_level": "string (100 chars max, optional)",
  "education_level": "string (255 chars max, optional)",
  "resume_path": "string (500 chars max, optional)",
  "password_hash": "string (255 chars, bcrypt hash)",
  "average_score": "decimal(3,2) (0.00-5.00, default: 0.00)",
  "status": "enum (applied|screened|interviewed|offered|hired|rejected, default: applied)",
  "created_at": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier, auto-generated serial primary key
- **name**: Candidate's full name, required for all records
- **email**: Unique email address, used for authentication and communication
- **phone**: Contact phone number, optional, no format validation in DB
- **location**: Geographic location (city, state, country)
- **experience_years**: Total years of professional experience, must be non-negative
- **technical_skills**: Comma-separated or free-text skills list, indexed with GIN for full-text search
- **seniority_level**: Career level (Junior, Mid, Senior, Lead, etc.)
- **education_level**: Highest education qualification
- **resume_path**: File path or URL to uploaded resume/CV
- **password_hash**: Bcrypt-hashed password for candidate portal authentication
- **average_score**: Calculated average of BHIV values feedback (1-5 scale)
- **status**: Current application status in hiring pipeline
- **created_at**: Record creation timestamp, immutable
- **updated_at**: Last modification timestamp, auto-updated by trigger

### Validation Rules

```
- name: NOT NULL, max 255 chars
- email: NOT NULL, UNIQUE, valid email format (enforced in application layer)
- phone: max 50 chars, optional
- location: max 255 chars, optional
- experience_years: >= 0 (CHECK constraint)
- technical_skills: unlimited text, indexed for search
- seniority_level: max 100 chars
- education_level: max 255 chars
- resume_path: max 500 chars
- password_hash: max 255 chars (bcrypt output)
- average_score: 0.00 to 5.00 (CHECK constraint)
- status: must be one of 6 enum values (CHECK constraint)
- created_at: auto-set, immutable
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
UNIQUE: email
NOT NULL: name, email, status, created_at, updated_at
CHECK: experience_years >= 0
CHECK: average_score >= 0 AND average_score <= 5
CHECK: status IN ('applied', 'screened', 'interviewed', 'offered', 'hired', 'rejected')
INDEX: idx_candidates_email (email)
INDEX: idx_candidates_status (status)
INDEX: idx_candidates_location (location)
INDEX: idx_candidates_experience (experience_years)
INDEX: idx_candidates_score (average_score)
INDEX: idx_candidates_skills_gin (to_tsvector('english', technical_skills)) -- Full-text search
INDEX: idx_candidates_created_at (created_at)
TRIGGER: update_candidates_updated_at (auto-update updated_at)
TRIGGER: audit_candidates_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice.johnson@example.com",
  "phone": "+1-555-0101",
  "location": "San Francisco, CA",
  "experience_years": 5,
  "technical_skills": "Python, FastAPI, Docker, PostgreSQL, React, AWS",
  "seniority_level": "Senior",
  "education_level": "Bachelor's in Computer Science",
  "resume_path": "/resumes/alice_johnson_resume.pdf",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2",
  "average_score": 4.60,
  "status": "interviewed",
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-08T15:30:00Z"
}
```

### Edge Cases

1. **Candidate added but no feedback yet** → `average_score` remains 0.00, handle gracefully in UI
2. **Duplicate email in bulk import** → UNIQUE constraint violation, rollback transaction, return error
3. **Status transition validation** → Application layer must enforce valid state transitions (e.g., can't go from 'rejected' to 'hired')
4. **Resume URL expires** → Need periodic validation and refresh logic
5. **Candidate deleted but referenced in feedback/interviews** → Use soft delete pattern or CASCADE constraints
6. **Password hash missing for old records** → Allow login without password check for legacy data, prompt password setup
7. **Skills search with special characters** → GIN index handles full-text search, sanitize input to prevent injection
8. **Negative experience_years** → CHECK constraint prevents, but validate in API layer before insert

### What Breaks If Schema Changes

- **Adding required field without default** → All existing records fail validation, need migration with default values
- **Removing field** → Any code querying that field crashes, need code audit before removal
- **Changing `average_score` type to string** → All numeric comparisons (`average_score > 3.5`) fail
- **Removing email UNIQUE constraint** → Duplicate detection logic breaks, authentication becomes ambiguous
- **Changing status enum values** → Validation logic needs update, existing records may have invalid values
- **Removing GIN index on skills** → Full-text search performance degrades significantly (100x slower)
- **Changing `id` from serial to UUID** → All foreign key references break, need cascading updates
- **Removing `updated_at` trigger** → Timestamp tracking stops working, audit trail incomplete

### Related Models

- **Referenced by**: `feedback.candidate_id`, `interviews.candidate_id`, `offers.candidate_id`, `job_applications.candidate_id`, `matching_cache.candidate_id`, `rl_predictions.candidate_id`, `workflows.candidate_id`
- **References**: None (root entity)

---

## 2. Job Model

**Table Name**: `jobs`  
**Purpose**: Store job postings from clients and HR team  
**Primary Entity**: Core entity for job management and matching

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "title": "string (255 chars, required)",
  "department": "string (255 chars, required)",
  "location": "string (255 chars, required)",
  "experience_level": "string (100 chars, required)",
  "requirements": "text (unlimited, required)",
  "description": "text (unlimited, required)",
  "employment_type": "enum (Full-time|Part-time|Contract|Intern, default: Full-time)",
  "client_id": "string (100 chars, optional, foreign key)",
  "status": "enum (active|paused|closed|draft, default: active)",
  "created_at": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier, auto-generated serial primary key
- **title**: Job title/position name (e.g., "Senior Python Developer")
- **department**: Department or team (e.g., "Engineering", "Marketing")
- **location**: Job location (city, remote, hybrid)
- **experience_level**: Required experience level (entry, mid, senior, lead)
- **requirements**: Detailed job requirements and qualifications
- **description**: Full job description and responsibilities
- **employment_type**: Type of employment contract
- **client_id**: Reference to client who posted the job (NULL for internal HR postings)
- **status**: Current job posting status
- **created_at**: Record creation timestamp
- **updated_at**: Last modification timestamp

### Validation Rules

```
- title: NOT NULL, max 255 chars
- department: NOT NULL, max 255 chars
- location: NOT NULL, max 255 chars
- experience_level: NOT NULL, max 100 chars
- requirements: NOT NULL, unlimited text
- description: NOT NULL, unlimited text
- employment_type: must be one of 4 enum values (CHECK constraint)
- client_id: max 100 chars, optional, must reference existing client
- status: must be one of 4 enum values (CHECK constraint)
- created_at: auto-set, immutable
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: title, department, location, experience_level, requirements, description, status, created_at, updated_at
CHECK: employment_type IN ('Full-time', 'Part-time', 'Contract', 'Intern')
CHECK: status IN ('active', 'paused', 'closed', 'draft')
FOREIGN KEY: client_id REFERENCES clients(client_id) ON DELETE SET NULL
INDEX: idx_jobs_status (status)
INDEX: idx_jobs_client_id (client_id)
INDEX: idx_jobs_department (department)
INDEX: idx_jobs_location (location)
INDEX: idx_jobs_experience_level (experience_level)
INDEX: idx_jobs_created_at (created_at)
TRIGGER: update_jobs_updated_at (auto-update updated_at)
TRIGGER: audit_jobs_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "department": "Engineering",
  "location": "Remote",
  "experience_level": "Senior",
  "requirements": "5+ years Python, FastAPI, PostgreSQL, REST APIs, Docker, Kubernetes",
  "description": "We are looking for a senior Python developer to join our engineering team and build scalable web applications. You will work on microservices architecture, API design, and cloud infrastructure.",
  "employment_type": "Full-time",
  "client_id": "TECH001",
  "status": "active",
  "created_at": "2025-11-15T09:00:00Z",
  "updated_at": "2025-12-01T14:20:00Z"
}
```

### Edge Cases

1. **Client deleted but job still active** → Foreign key ON DELETE SET NULL, `client_id` becomes NULL
2. **Job closed but candidates still applying** → Application layer must check status before allowing applications
3. **Requirements text too long for display** → Truncate in UI, store full text in DB
4. **Location format inconsistency** → "Remote" vs "remote" vs "Work from Home", need normalization
5. **Experience level mismatch** → "Senior" in title but "Mid" in experience_level field
6. **Draft jobs visible to candidates** → Filter by `status = 'active'` in all public queries
7. **Job updated after candidates matched** → Matching cache becomes stale, need re-matching logic

### What Breaks If Schema Changes

- **Adding required field without default** → All existing jobs fail validation
- **Removing `client_id`** → Client portal job management breaks
- **Changing status enum** → Validation logic needs update, queries break
- **Making `client_id` required** → Internal HR jobs (NULL client_id) become invalid
- **Removing indexes** → Search and filtering performance degrades
- **Changing `id` type** → All foreign key references break

### Related Models

- **Referenced by**: `feedback.job_id`, `interviews.job_id`, `offers.job_id`, `job_applications.job_id`, `matching_cache.job_id`, `rl_predictions.job_id`, `workflows.job_id`
- **References**: `clients.client_id` (optional)

---

## 3. Job Application Model

**Table Name**: `job_applications`  
**Purpose**: Track candidate applications to specific jobs  
**Primary Entity**: Junction table linking candidates to jobs

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_id": "integer (required, foreign key)",
  "job_id": "integer (required, foreign key)",
  "cover_letter": "text (unlimited, optional)",
  "status": "enum (applied|reviewed|shortlisted|rejected|withdrawn, default: applied)",
  "applied_date": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier for each application
- **candidate_id**: Reference to candidate who applied
- **job_id**: Reference to job being applied for
- **cover_letter**: Optional cover letter text
- **status**: Current application status
- **applied_date**: When application was submitted
- **updated_at**: Last status change timestamp

### Validation Rules

```
- candidate_id: NOT NULL, must reference existing candidate
- job_id: NOT NULL, must reference existing job
- cover_letter: optional, unlimited text
- status: must be one of 5 enum values (CHECK constraint)
- applied_date: auto-set on insert
- updated_at: auto-updated by trigger
- UNIQUE constraint on (candidate_id, job_id) - one application per candidate per job
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_id, job_id, status, applied_date
UNIQUE: (candidate_id, job_id)
CHECK: status IN ('applied', 'reviewed', 'shortlisted', 'rejected', 'withdrawn')
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
INDEX: idx_job_applications_candidate (candidate_id)
INDEX: idx_job_applications_job (job_id)
INDEX: idx_job_applications_status (status)
INDEX: idx_job_applications_date (applied_date)
TRIGGER: update_job_applications_updated_at (auto-update updated_at)
TRIGGER: audit_job_applications_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "cover_letter": "I am excited to apply for the Senior Python Developer position. With 5 years of experience in Python and FastAPI, I believe I would be a great fit for your team.",
  "status": "shortlisted",
  "applied_date": "2025-12-01T10:30:00Z",
  "updated_at": "2025-12-05T14:20:00Z"
}
```

### Edge Cases

1. **Duplicate application attempt** → UNIQUE constraint violation, return error "Already applied"
2. **Candidate deleted** → CASCADE delete removes all applications
3. **Job deleted** → CASCADE delete removes all applications
4. **Status transition validation** → Can't go from 'rejected' to 'shortlisted' without business logic
5. **Cover letter with special characters** → Store as-is, sanitize on display

### What Breaks If Schema Changes

- **Removing UNIQUE constraint** → Duplicate applications allowed, breaks business logic
- **Changing CASCADE to SET NULL** → Orphaned applications with NULL candidate_id/job_id
- **Adding required field** → All existing applications fail validation
- **Changing status enum** → Validation and filtering logic breaks

### Related Models

- **References**: `candidates.id`, `jobs.id`
- **Referenced by**: None (leaf entity)

---

## 4. Feedback Model

**Table Name**: `feedback`  
**Purpose**: Store BHIV values assessment scores (Integrity, Honesty, Discipline, Hard Work, Gratitude)  
**Primary Entity**: Core feature for values-based candidate evaluation

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_id": "integer (required, foreign key)",
  "job_id": "integer (required, foreign key)",
  "integrity": "integer (1-5, required)",
  "honesty": "integer (1-5, required)",
  "discipline": "integer (1-5, required)",
  "hard_work": "integer (1-5, required)",
  "gratitude": "integer (1-5, required)",
  "average_score": "decimal(3,2) (auto-calculated, generated column)",
  "comments": "text (unlimited, optional)",
  "reviewer_name": "string (255 chars, optional)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each feedback record
- **candidate_id**: Reference to candidate being evaluated
- **job_id**: Reference to job context for evaluation
- **integrity**: Score for integrity value (1-5 scale)
- **honesty**: Score for honesty value (1-5 scale)
- **discipline**: Score for discipline value (1-5 scale)
- **hard_work**: Score for hard work value (1-5 scale)
- **gratitude**: Score for gratitude value (1-5 scale)
- **average_score**: Auto-calculated average of 5 values (GENERATED ALWAYS AS)
- **comments**: Optional text feedback from reviewer
- **reviewer_name**: Name of person who submitted feedback
- **created_at**: Timestamp when feedback was submitted

### Validation Rules

```
- candidate_id: NOT NULL, must reference existing candidate
- job_id: NOT NULL, must reference existing job
- integrity: 1-5 (CHECK constraint)
- honesty: 1-5 (CHECK constraint)
- discipline: 1-5 (CHECK constraint)
- hard_work: 1-5 (CHECK constraint)
- gratitude: 1-5 (CHECK constraint)
- average_score: auto-calculated, cannot be manually set
- comments: optional, unlimited text
- reviewer_name: max 255 chars, optional
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_id, job_id, integrity, honesty, discipline, hard_work, gratitude, created_at
CHECK: integrity >= 1 AND integrity <= 5
CHECK: honesty >= 1 AND honesty <= 5
CHECK: discipline >= 1 AND discipline <= 5
CHECK: hard_work >= 1 AND hard_work <= 5
CHECK: gratitude >= 1 AND gratitude <= 5
GENERATED COLUMN: average_score = (integrity + honesty + discipline + hard_work + gratitude) / 5.0
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
INDEX: idx_feedback_candidate_id (candidate_id)
INDEX: idx_feedback_job_id (job_id)
INDEX: idx_feedback_average_score (average_score)
INDEX: idx_feedback_created_at (created_at)
TRIGGER: audit_feedback_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "integrity": 5,
  "honesty": 5,
  "discipline": 4,
  "hard_work": 5,
  "gratitude": 4,
  "average_score": 4.60,
  "comments": "Excellent candidate with strong values alignment. Demonstrated integrity in all interactions.",
  "reviewer_name": "John Smith, HR Manager",
  "created_at": "2025-12-05T16:45:00Z"
}
```

### Edge Cases

1. **Generated column update attempt** → PostgreSQL rejects manual updates to `average_score`
2. **Candidate deleted** → CASCADE delete removes all feedback
3. **Multiple feedback for same candidate/job** → Allowed, calculate aggregate in queries
4. **Score out of range** → CHECK constraint prevents, but validate in API layer
5. **Missing reviewer_name** → Allowed (NULL), display as "Anonymous" in UI

### What Breaks If Schema Changes

- **Removing generated column** → Need manual calculation in application layer
- **Changing score range to 1-10** → All CHECK constraints need update, existing data may be invalid
- **Making comments required** → All existing records without comments fail validation
- **Removing CASCADE** → Orphaned feedback records when candidates/jobs deleted
- **Changing average calculation formula** → Need migration to recalculate all existing scores

### Related Models

- **References**: `candidates.id`, `jobs.id`
- **Referenced by**: `rl_feedback.prediction_id` (indirectly through predictions)

---

## 5. Interview Model

**Table Name**: `interviews`  
**Purpose**: Schedule and track candidate interviews  
**Primary Entity**: Interview management and scheduling

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_id": "integer (required, foreign key)",
  "job_id": "integer (required, foreign key)",
  "interview_date": "timestamp (required)",
  "interviewer": "string (255 chars, default: 'HR Team')",
  "interview_type": "enum (Technical|HR|Behavioral|Final|Panel, default: Technical)",
  "notes": "text (unlimited, optional)",
  "status": "enum (scheduled|completed|cancelled|rescheduled, default: scheduled)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each interview
- **candidate_id**: Reference to candidate being interviewed
- **job_id**: Reference to job position
- **interview_date**: Scheduled date and time of interview
- **interviewer**: Name of interviewer or interview panel
- **interview_type**: Type/round of interview
- **notes**: Interview notes, feedback, or special instructions
- **status**: Current interview status
- **created_at**: When interview was scheduled

### Validation Rules

```
- candidate_id: NOT NULL, must reference existing candidate
- job_id: NOT NULL, must reference existing job
- interview_date: NOT NULL, must be valid timestamp
- interviewer: max 255 chars, default 'HR Team'
- interview_type: must be one of 5 enum values (CHECK constraint)
- notes: optional, unlimited text
- status: must be one of 4 enum values (CHECK constraint)
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_id, job_id, interview_date, interviewer, interview_type, status, created_at
CHECK: interview_type IN ('Technical', 'HR', 'Behavioral', 'Final', 'Panel')
CHECK: status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
INDEX: idx_interviews_candidate_id (candidate_id)
INDEX: idx_interviews_job_id (job_id)
INDEX: idx_interviews_date (interview_date)
INDEX: idx_interviews_status (status)
INDEX: idx_interviews_type (interview_type)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "interview_date": "2025-12-15T14:00:00Z",
  "interviewer": "Sarah Chen, Engineering Manager",
  "interview_type": "Technical",
  "notes": "Focus on Python, FastAPI, and system design. 1-hour technical round.",
  "status": "scheduled",
  "created_at": "2025-12-08T10:30:00Z"
}
```

### Edge Cases

1. **Past interview_date with 'scheduled' status** → Need background job to auto-update status
2. **Multiple interviews for same candidate/job** → Allowed (multiple rounds)
3. **Interview rescheduled multiple times** → Track in notes or separate rescheduling table
4. **Candidate/job deleted** → CASCADE delete removes interviews
5. **Interviewer name format inconsistency** → No validation, store as-is

### What Breaks If Schema Changes

- **Making interviewer required** → Default value 'HR Team' prevents issues
- **Changing status enum** → Validation logic breaks, need migration
- **Removing CASCADE** → Orphaned interviews when candidates/jobs deleted
- **Adding timezone field** → All existing timestamps need timezone conversion

### Related Models

- **References**: `candidates.id`, `jobs.id`
- **Referenced by**: None (leaf entity)

---

## 6. Offer Model

**Table Name**: `offers`  
**Purpose**: Manage job offers extended to candidates  
**Primary Entity**: Offer management and tracking

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_id": "integer (required, foreign key)",
  "job_id": "integer (required, foreign key)",
  "salary": "decimal(12,2) (required, > 0)",
  "start_date": "date (required)",
  "terms": "text (required)",
  "status": "enum (pending|accepted|rejected|withdrawn|expired, default: pending)",
  "created_at": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier for each offer
- **candidate_id**: Reference to candidate receiving offer
- **job_id**: Reference to job position
- **salary**: Offered annual salary amount
- **start_date**: Proposed start date
- **terms**: Offer terms and conditions
- **status**: Current offer status
- **created_at**: When offer was created
- **updated_at**: Last status change timestamp

### Validation Rules

```
- candidate_id: NOT NULL, must reference existing candidate
- job_id: NOT NULL, must reference existing job
- salary: NOT NULL, must be > 0 (CHECK constraint)
- start_date: NOT NULL, must be valid date
- terms: NOT NULL, unlimited text
- status: must be one of 5 enum values (CHECK constraint)
- created_at: auto-set on insert
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_id, job_id, salary, start_date, terms, status, created_at, updated_at
CHECK: salary > 0
CHECK: status IN ('pending', 'accepted', 'rejected', 'withdrawn', 'expired')
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
INDEX: idx_offers_candidate_id (candidate_id)
INDEX: idx_offers_job_id (job_id)
INDEX: idx_offers_status (status)
INDEX: idx_offers_created_at (created_at)
TRIGGER: update_offers_updated_at (auto-update updated_at)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "salary": 120000.00,
  "start_date": "2026-01-15",
  "terms": "Full-time employment, 120K annual salary, health insurance, 401k matching, 20 days PTO, remote work option.",
  "status": "pending",
  "created_at": "2025-12-10T09:00:00Z",
  "updated_at": "2025-12-10T09:00:00Z"
}
```

### Edge Cases

1. **Negative or zero salary** → CHECK constraint prevents
2. **Start date in the past** → No DB constraint, validate in application layer
3. **Multiple offers to same candidate** → Allowed (different jobs or revised offers)
4. **Offer accepted but candidate doesn't join** → Manual status update needed
5. **Currency not specified** → Assume default currency (USD), add currency field if needed

### What Breaks If Schema Changes

- **Changing salary to integer** → Loses decimal precision, rounding errors
- **Making terms optional** → Legal compliance issues, all offers need terms
- **Removing CHECK on salary** → Allows invalid negative/zero salaries
- **Changing status enum** → Validation and reporting logic breaks

### Related Models

- **References**: `candidates.id`, `jobs.id`
- **Referenced by**: None (leaf entity)

---

## 7. User Model

**Table Name**: `users`  
**Purpose**: Internal HR users with authentication and 2FA support  
**Primary Entity**: HR platform user management

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "username": "string (100 chars, unique, required)",
  "email": "string (255 chars, unique, required)",
  "password_hash": "string (255 chars, required)",
  "totp_secret": "string (32 chars, optional)",
  "is_2fa_enabled": "boolean (default: false)",
  "role": "enum (admin|hr_manager|recruiter|user, default: user)",
  "status": "enum (active|inactive|suspended, default: active)",
  "last_login": "timestamp (optional)",
  "failed_login_attempts": "integer (default: 0)",
  "locked_until": "timestamp (optional)",
  "created_at": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier for each user
- **username**: Unique username for login
- **email**: Unique email address
- **password_hash**: Bcrypt-hashed password
- **totp_secret**: TOTP secret for 2FA (base32 encoded)
- **is_2fa_enabled**: Whether 2FA is enabled for this user
- **role**: User role for permission management
- **status**: Account status
- **last_login**: Last successful login timestamp
- **failed_login_attempts**: Counter for failed login attempts
- **locked_until**: Account lock expiration timestamp
- **created_at**: Account creation timestamp
- **updated_at**: Last modification timestamp

### Validation Rules

```
- username: NOT NULL, UNIQUE, max 100 chars
- email: NOT NULL, UNIQUE, max 255 chars, valid email format
- password_hash: NOT NULL, max 255 chars (bcrypt output)
- totp_secret: max 32 chars, optional
- is_2fa_enabled: boolean, default false
- role: must be one of 4 enum values (CHECK constraint)
- status: must be one of 3 enum values (CHECK constraint)
- last_login: optional timestamp
- failed_login_attempts: integer, default 0
- locked_until: optional timestamp
- created_at: auto-set on insert
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
UNIQUE: username, email
NOT NULL: username, email, password_hash, role, status, created_at, updated_at
CHECK: role IN ('admin', 'hr_manager', 'recruiter', 'user')
CHECK: status IN ('active', 'inactive', 'suspended')
INDEX: idx_users_username (username)
INDEX: idx_users_email (email)
INDEX: idx_users_status (status)
INDEX: idx_users_2fa_enabled (is_2fa_enabled)
INDEX: idx_users_last_login (last_login)
TRIGGER: update_users_updated_at (auto-update updated_at)
TRIGGER: audit_users_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@bhiv.com",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2",
  "totp_secret": "JBSWY3DPEHPK3PXP",
  "is_2fa_enabled": true,
  "role": "admin",
  "status": "active",
  "last_login": "2025-12-09T08:30:00Z",
  "failed_login_attempts": 0,
  "locked_until": null,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-12-09T08:30:00Z"
}
```

### Edge Cases

1. **Account locked (5 failed attempts)** → Set `locked_until` to 30 minutes from now
2. **2FA enabled but totp_secret NULL** → Invalid state, validate before enabling 2FA
3. **User deleted but audit logs reference user_id** → Use soft delete or keep user record
4. **Password hash format changes** → Need migration to rehash all passwords
5. **Role changed while user is logged in** → Need to invalidate existing sessions

### What Breaks If Schema Changes

- **Removing UNIQUE on email** → Duplicate accounts possible, authentication ambiguous
- **Changing role enum** → Permission checks break, need code update
- **Making totp_secret required** → All users without 2FA fail validation
- **Removing failed_login_attempts** → Account lockout logic breaks

### Related Models

- **Referenced by**: `audit_logs.user_id`
- **References**: None

---

## 8. Client Model

**Table Name**: `clients`  
**Purpose**: External client companies with authentication and 2FA  
**Primary Entity**: Client portal user management

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "client_id": "string (100 chars, unique, required)",
  "client_name": "string (255 chars, optional)",
  "company_name": "string (255 chars, required)",
  "password_hash": "string (255 chars, required)",
  "email": "string (255 chars, unique, optional)",
  "phone": "string (20 chars, optional)",
  "totp_secret": "string (255 chars, optional)",
  "two_factor_enabled": "boolean (default: false)",
  "backup_codes": "text (optional)",
  "status": "enum (active|inactive|suspended, default: active)",
  "password_changed_at": "timestamp (default: current_timestamp)",
  "password_history": "text (optional)",
  "failed_login_attempts": "integer (default: 0)",
  "locked_until": "timestamp (optional)",
  "created_at": "timestamp (auto-set on insert)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Auto-increment primary key
- **client_id**: Unique client identifier (e.g., "TECH001")
- **client_name**: Client contact person name
- **company_name**: Company/organization name
- **password_hash**: Bcrypt-hashed password
- **email**: Unique email address
- **phone**: Contact phone number
- **totp_secret**: TOTP secret for 2FA
- **two_factor_enabled**: Whether 2FA is enabled
- **backup_codes**: Encrypted backup codes for 2FA recovery
- **status**: Account status
- **password_changed_at**: Last password change timestamp
- **password_history**: JSON array of previous password hashes
- **failed_login_attempts**: Counter for failed logins
- **locked_until**: Account lock expiration timestamp
- **created_at**: Account creation timestamp
- **updated_at**: Last modification timestamp

### Validation Rules

```
- client_id: NOT NULL, UNIQUE, max 100 chars
- client_name: max 255 chars, optional
- company_name: NOT NULL, max 255 chars
- password_hash: NOT NULL, max 255 chars
- email: UNIQUE, max 255 chars, optional
- phone: max 20 chars, optional
- totp_secret: max 255 chars, optional
- two_factor_enabled: boolean, default false
- backup_codes: text, optional
- status: must be one of 3 enum values (CHECK constraint)
- password_changed_at: timestamp, default current_timestamp
- password_history: text, optional
- failed_login_attempts: integer, default 0
- locked_until: timestamp, optional
- created_at: auto-set on insert
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
UNIQUE: client_id, email
NOT NULL: client_id, company_name, password_hash, status, created_at, updated_at
CHECK: status IN ('active', 'inactive', 'suspended')
INDEX: idx_clients_client_id (client_id)
INDEX: idx_clients_email (email)
INDEX: idx_clients_status (status)
INDEX: idx_clients_2fa_enabled (two_factor_enabled)
TRIGGER: update_clients_updated_at (auto-update updated_at)
TRIGGER: audit_clients_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "client_id": "TECH001",
  "client_name": "John Doe",
  "company_name": "Tech Innovations Inc",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2",
  "email": "contact@techinnovations.com",
  "phone": "+1-555-0100",
  "totp_secret": "JBSWY3DPEHPK3PXP",
  "two_factor_enabled": true,
  "backup_codes": "BACKUP-A1B2C3D4,BACKUP-E5F6G7H8,...",
  "status": "active",
  "password_changed_at": "2025-11-01T10:00:00Z",
  "password_history": "[\"$2b$12$old_hash1\", \"$2b$12$old_hash2\"]",
  "failed_login_attempts": 0,
  "locked_until": null,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-12-09T09:15:00Z"
}
```

### Edge Cases

1. **Client_id format inconsistency** → Enforce format in application layer (e.g., "TECH001")
2. **Email NULL but needed for notifications** → Validate before sending emails
3. **Password history exceeds storage limit** → Keep only last 5 passwords
4. **Backup codes used up** → Prompt to generate new codes
5. **Account locked but client needs urgent access** → Admin override mechanism needed

### What Breaks If Schema Changes

- **Making email required** → All clients without email fail validation
- **Removing client_id UNIQUE** → Duplicate client IDs possible, breaks business logic
- **Changing password_history format** → Need migration to convert existing data
- **Removing two_factor_enabled** → 2FA logic breaks

### Related Models

- **Referenced by**: `jobs.client_id`, `audit_logs.client_id`, `company_scoring_preferences.client_id`, `workflows.client_id`
- **References**: None

---

## 9. Matching Cache Model

**Table Name**: `matching_cache`  
**Purpose**: Cache AI matching results for performance optimization  
**Primary Entity**: AI matching results storage

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "job_id": "integer (required, foreign key)",
  "candidate_id": "integer (required, foreign key)",
  "match_score": "decimal(5,2) (0-100, required)",
  "skills_match_score": "decimal(5,2) (0-100, default: 0)",
  "experience_match_score": "decimal(5,2) (0-100, default: 0)",
  "location_match_score": "decimal(5,2) (0-100, default: 0)",
  "values_alignment_score": "decimal(3,2) (0-5, default: 0)",
  "algorithm_version": "string (50 chars, default: 'v2.0.0')",
  "learning_version": "string (50 chars, default: 'v3.0')",
  "reasoning": "text (optional)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each cached match
- **job_id**: Reference to job being matched
- **candidate_id**: Reference to candidate being matched
- **match_score**: Overall match score (0-100)
- **skills_match_score**: Technical skills match component
- **experience_match_score**: Experience level match component
- **location_match_score**: Location match component
- **values_alignment_score**: BHIV values alignment score
- **algorithm_version**: Version of matching algorithm used
- **learning_version**: Version of learning engine used
- **reasoning**: AI-generated explanation of match score
- **created_at**: When match was calculated

### Validation Rules

```
- job_id: NOT NULL, must reference existing job
- candidate_id: NOT NULL, must reference existing candidate
- match_score: 0-100 (CHECK constraint)
- skills_match_score: 0-100 (CHECK constraint)
- experience_match_score: 0-100 (CHECK constraint)
- location_match_score: 0-100 (CHECK constraint)
- values_alignment_score: 0-5 (CHECK constraint)
- algorithm_version: max 50 chars, default 'v2.0.0'
- learning_version: max 50 chars, default 'v3.0'
- reasoning: optional text
- created_at: auto-set on insert
- UNIQUE constraint on (job_id, candidate_id, algorithm_version)
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: job_id, candidate_id, match_score, created_at
UNIQUE: (job_id, candidate_id, algorithm_version)
CHECK: match_score >= 0 AND match_score <= 100
CHECK: skills_match_score >= 0 AND skills_match_score <= 100
CHECK: experience_match_score >= 0 AND experience_match_score <= 100
CHECK: location_match_score >= 0 AND location_match_score <= 100
CHECK: values_alignment_score >= 0 AND values_alignment_score <= 5
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
INDEX: idx_matching_job_id (job_id)
INDEX: idx_matching_candidate_id (candidate_id)
INDEX: idx_matching_score (match_score)
INDEX: idx_matching_created_at (created_at)
```

### Example Valid Record

```json
{
  "id": 1,
  "job_id": 1,
  "candidate_id": 1,
  "match_score": 87.50,
  "skills_match_score": 90.00,
  "experience_match_score": 85.00,
  "location_match_score": 100.00,
  "values_alignment_score": 4.60,
  "algorithm_version": "v3.0.0-phase3-production",
  "learning_version": "v3.0",
  "reasoning": "Strong match: 90% skills overlap (Python, FastAPI, Docker), 5 years experience matches senior requirement, remote location preference aligned, excellent values scores (4.6/5).",
  "created_at": "2025-12-09T10:15:00Z"
}
```

### Edge Cases

1. **Duplicate match with same algorithm version** → UNIQUE constraint prevents, update existing record
2. **Job/candidate deleted** → CASCADE delete removes cached matches
3. **Algorithm version changes** → New records created, old cache remains for comparison
4. **Score components don't sum to match_score** → Weighted average, not simple sum
5. **Stale cache after candidate profile update** → Need cache invalidation logic

### What Breaks If Schema Changes

- **Removing UNIQUE constraint** → Duplicate cache entries, wasted storage
- **Changing score ranges** → All CHECK constraints need update
- **Removing algorithm_version** → Can't track which algorithm produced results
- **Making reasoning required** → All existing records without reasoning fail

### Related Models

- **References**: `jobs.id`, `candidates.id`
- **Referenced by**: None (cache table)

---

## 10. Audit Log Model

**Table Name**: `audit_logs`  
**Purpose**: Security and compliance audit trail  
**Primary Entity**: System-wide audit logging

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "user_id": "integer (optional, foreign key)",
  "client_id": "string (100 chars, optional, foreign key)",
  "action": "string (100 chars, required)",
  "resource": "string (100 chars, optional)",
  "resource_id": "integer (optional)",
  "ip_address": "inet (optional)",
  "user_agent": "text (optional)",
  "request_method": "string (10 chars, optional)",
  "endpoint": "string (255 chars, optional)",
  "success": "boolean (default: true)",
  "error_message": "text (optional)",
  "details": "jsonb (optional)",
  "timestamp": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each audit log entry
- **user_id**: Reference to internal user (if applicable)
- **client_id**: Reference to client (if applicable)
- **action**: Action performed (e.g., "INSERT", "UPDATE", "DELETE", "LOGIN")
- **resource**: Resource type affected (e.g., "candidates", "jobs")
- **resource_id**: ID of specific resource affected
- **ip_address**: IP address of request origin
- **user_agent**: Browser/client user agent string
- **request_method**: HTTP method (GET, POST, PUT, DELETE)
- **endpoint**: API endpoint accessed
- **success**: Whether action succeeded
- **error_message**: Error message if action failed
- **details**: JSON object with additional context
- **timestamp**: When action occurred

### Validation Rules

```
- user_id: optional, must reference existing user if provided
- client_id: optional, must reference existing client if provided
- action: NOT NULL, max 100 chars
- resource: max 100 chars, optional
- resource_id: integer, optional
- ip_address: valid INET format, optional
- user_agent: text, optional
- request_method: max 10 chars, optional
- endpoint: max 255 chars, optional
- success: boolean, default true
- error_message: text, optional
- details: valid JSONB, optional
- timestamp: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: action, timestamp
FOREIGN KEY: user_id REFERENCES users(id) ON DELETE SET NULL
FOREIGN KEY: client_id REFERENCES clients(client_id) ON DELETE SET NULL
INDEX: idx_audit_user_id (user_id)
INDEX: idx_audit_client_id (client_id)
INDEX: idx_audit_action (action)
INDEX: idx_audit_timestamp (timestamp)
INDEX: idx_audit_ip_address (ip_address)
INDEX: idx_audit_success (success)
```

### Example Valid Record

```json
{
  "id": 1,
  "user_id": 1,
  "client_id": null,
  "action": "UPDATE",
  "resource": "candidates",
  "resource_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "request_method": "PUT",
  "endpoint": "/v1/candidate/profile/1",
  "success": true,
  "error_message": null,
  "details": {
    "old": {"status": "applied"},
    "new": {"status": "interviewed"}
  },
  "timestamp": "2025-12-09T10:30:00Z"
}
```

### Edge Cases

1. **User/client deleted** → Foreign key SET NULL, audit log preserved
2. **Large details JSON** → No size limit, monitor storage usage
3. **High-frequency logging** → Partition table by timestamp for performance
4. **IP address spoofing** → Log as-is, validate in application layer
5. **Automated actions (no user_id/client_id)** → Both NULL, action logged as "system"

### What Breaks If Schema Changes

- **Making user_id required** → System-generated logs fail validation
- **Removing details JSONB** → Lose contextual information for debugging
- **Changing timestamp to date** → Lose time precision for audit trail
- **Removing indexes** → Query performance degrades significantly

### Related Models

- **References**: `users.id`, `clients.client_id`
- **Referenced by**: None (audit table)

---

## 11. Rate Limit Model

**Table Name**: `rate_limits`  
**Purpose**: API rate limiting and throttling  
**Primary Entity**: Rate limit tracking

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "ip_address": "inet (required)",
  "endpoint": "string (255 chars, required)",
  "user_tier": "enum (default|premium|enterprise, default: default)",
  "request_count": "integer (default: 1)",
  "window_start": "timestamp (default: current_timestamp)",
  "blocked_until": "timestamp (optional)"
}
```

### Field Descriptions

- **id**: Unique identifier for each rate limit record
- **ip_address**: IP address being rate limited
- **endpoint**: API endpoint being accessed
- **user_tier**: User tier for tiered rate limiting
- **request_count**: Number of requests in current window
- **window_start**: Start of current rate limit window (1 minute)
- **blocked_until**: Timestamp until which IP is blocked (if exceeded)

### Validation Rules

```
- ip_address: NOT NULL, valid INET format
- endpoint: NOT NULL, max 255 chars
- user_tier: must be one of 3 enum values (CHECK constraint)
- request_count: integer, default 1
- window_start: timestamp, default current_timestamp
- blocked_until: timestamp, optional
- UNIQUE constraint on (ip_address, endpoint)
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: ip_address, endpoint, user_tier, request_count, window_start
UNIQUE: (ip_address, endpoint)
CHECK: user_tier IN ('default', 'premium', 'enterprise')
INDEX: idx_rate_limits_ip_endpoint (ip_address, endpoint)
INDEX: idx_rate_limits_window_start (window_start)
```

### Example Valid Record

```json
{
  "id": 1,
  "ip_address": "192.168.1.100",
  "endpoint": "/v1/candidates/search",
  "user_tier": "default",
  "request_count": 45,
  "window_start": "2025-12-09T10:30:00Z",
  "blocked_until": null
}
```

### Edge Cases

1. **Window expired** → Reset request_count and window_start
2. **IP blocked but window expired** → Clear blocked_until
3. **Endpoint pattern matching** → Exact match only, no wildcards
4. **User tier upgrade** → Update user_tier, reset limits
5. **Distributed system** → Need centralized rate limit store (Redis)

### What Breaks If Schema Changes

- **Removing UNIQUE constraint** → Multiple records per IP/endpoint, incorrect counting
- **Changing user_tier enum** → Validation logic breaks
- **Removing window_start** → Can't determine when to reset counters
- **Making blocked_until required** → All non-blocked IPs fail validation

### Related Models

- **References**: None
- **Referenced by**: None (operational table)

---

## 12. CSP Violation Model

**Table Name**: `csp_violations`  
**Purpose**: Track Content Security Policy violations  
**Primary Entity**: Security monitoring

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "violated_directive": "string (255 chars, required)",
  "blocked_uri": "text (required)",
  "document_uri": "text (required)",
  "ip_address": "inet (optional)",
  "user_agent": "text (optional)",
  "timestamp": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each violation
- **violated_directive**: CSP directive that was violated (e.g., "script-src")
- **blocked_uri**: URI that was blocked
- **document_uri**: Page where violation occurred
- **ip_address**: IP address of client
- **user_agent**: Browser user agent
- **timestamp**: When violation occurred

### Validation Rules

```
- violated_directive: NOT NULL, max 255 chars
- blocked_uri: NOT NULL, text
- document_uri: NOT NULL, text
- ip_address: valid INET format, optional
- user_agent: text, optional
- timestamp: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: violated_directive, blocked_uri, document_uri, timestamp
INDEX: idx_csp_violations_timestamp (timestamp)
INDEX: idx_csp_violations_ip (ip_address)
```

### Example Valid Record

```json
{
  "id": 1,
  "violated_directive": "script-src",
  "blocked_uri": "https://malicious-site.com/script.js",
  "document_uri": "https://bhiv-hr-portal.onrender.com/dashboard",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "timestamp": "2025-12-09T10:45:00Z"
}
```

### Edge Cases

1. **High-frequency violations** → May indicate attack, need alerting
2. **Legitimate violations** → Browser extensions, need whitelist
3. **Large blocked_uri** → No size limit, monitor storage
4. **IP address NULL** → Violation from server-side rendering
5. **Duplicate violations** → No UNIQUE constraint, log all occurrences

### What Breaks If Schema Changes

- **Making ip_address required** → Server-side violations fail
- **Removing timestamp index** → Slow queries for recent violations
- **Changing text fields to varchar** → Long URIs truncated
- **Adding UNIQUE constraint** → Can't log duplicate violations

### Related Models

- **References**: None
- **Referenced by**: None (security monitoring table)

---

## 13. Company Scoring Preferences Model

**Table Name**: `company_scoring_preferences`  
**Purpose**: Phase 3 learning engine - company-specific scoring preferences  
**Primary Entity**: AI learning and personalization

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "client_id": "string (100 chars, foreign key)",
  "scoring_weights": "jsonb (optional)",
  "avg_satisfaction": "decimal(3,2) (optional)",
  "feedback_count": "integer (optional)",
  "preferred_experience": "decimal(5,2) (optional)",
  "updated_at": "timestamp (default: current_timestamp)"
}
```

### Field Descriptions

- **id**: Unique identifier for each preference record
- **client_id**: Reference to client company
- **scoring_weights**: JSON object with custom scoring weights
- **avg_satisfaction**: Average satisfaction score from feedback
- **feedback_count**: Number of feedback submissions
- **preferred_experience**: Preferred years of experience
- **updated_at**: Last update timestamp

### Validation Rules

```
- client_id: optional, must reference existing client if provided
- scoring_weights: valid JSONB, optional
- avg_satisfaction: 0-5 (no CHECK constraint, validate in app)
- feedback_count: integer, optional
- preferred_experience: decimal, optional
- updated_at: timestamp, default current_timestamp
```

### Database Constraints

```sql
PRIMARY KEY: id
FOREIGN KEY: client_id REFERENCES clients(client_id) ON DELETE CASCADE
INDEX: idx_company_scoring_client (client_id)
```

### Example Valid Record

```json
{
  "id": 1,
  "client_id": "TECH001",
  "scoring_weights": {
    "skills": 0.40,
    "experience": 0.30,
    "values": 0.20,
    "location": 0.10
  },
  "avg_satisfaction": 4.50,
  "feedback_count": 25,
  "preferred_experience": 5.00,
  "updated_at": "2025-12-09T11:00:00Z"
}
```

### Edge Cases

1. **Client deleted** → CASCADE delete removes preferences
2. **Scoring weights don't sum to 1.0** → Normalize in application layer
3. **No feedback yet** → feedback_count = 0, avg_satisfaction = NULL
4. **Invalid JSON in scoring_weights** → JSONB validation prevents
5. **Multiple records per client** → No UNIQUE constraint, use latest by updated_at

### What Breaks If Schema Changes

- **Making scoring_weights required** → All clients without preferences fail
- **Removing JSONB type** → Lose flexible weight configuration
- **Adding UNIQUE on client_id** → Can't track preference history
- **Removing CASCADE** → Orphaned preferences when clients deleted

### Related Models

- **References**: `clients.client_id`
- **Referenced by**: None (learning engine table)

---

## 14. RL Prediction Model

**Table Name**: `rl_predictions`  
**Purpose**: Store reinforcement learning predictions and recommendations  
**Primary Entity**: RL agent decision tracking

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_id": "integer (required, foreign key)",
  "job_id": "integer (required, foreign key)",
  "rl_score": "decimal(5,2) (0-100, required)",
  "confidence_level": "decimal(5,2) (0-100, required)",
  "decision_type": "enum (recommend|review|reject, required)",
  "features": "jsonb (required)",
  "model_version": "string (20 chars, required)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each prediction
- **candidate_id**: Reference to candidate being evaluated
- **job_id**: Reference to job being matched
- **rl_score**: RL model prediction score (0-100)
- **confidence_level**: Model confidence in prediction (0-100)
- **decision_type**: Recommended action based on score
- **features**: JSON object with feature values used in prediction
- **model_version**: Version of RL model used
- **created_at**: When prediction was generated

### Validation Rules

```
- candidate_id: NOT NULL, must reference existing candidate
- job_id: NOT NULL, must reference existing job
- rl_score: 0-100 (CHECK constraint)
- confidence_level: 0-100 (CHECK constraint)
- decision_type: must be one of 3 enum values (CHECK constraint)
- features: NOT NULL, valid JSONB
- model_version: NOT NULL, max 20 chars
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_id, job_id, rl_score, confidence_level, decision_type, features, model_version, created_at
CHECK: rl_score >= 0 AND rl_score <= 100
CHECK: confidence_level >= 0 AND confidence_level <= 100
CHECK: decision_type IN ('recommend', 'review', 'reject')
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE CASCADE
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE CASCADE
INDEX: idx_rl_predictions_candidate_job (candidate_id, job_id)
INDEX: idx_rl_predictions_created (created_at)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "rl_score": 87.50,
  "confidence_level": 92.00,
  "decision_type": "recommend",
  "features": {
    "skills_match": 0.90,
    "experience_match": 0.85,
    "values_score": 4.60,
    "location_match": 1.0,
    "previous_feedback": 4.5
  },
  "model_version": "v1.0.0",
  "created_at": "2025-12-09T11:15:00Z"
}
```

### Edge Cases

1. **High score but low confidence** → Flag for manual review
2. **Model version changes** → Track predictions by version for comparison
3. **Features schema changes** → JSONB flexible, but need migration for queries
4. **Candidate/job deleted** → CASCADE delete removes predictions
5. **Multiple predictions for same candidate/job** → Allowed, track over time

### What Breaks If Schema Changes

- **Removing CHECK constraints** → Invalid scores allowed
- **Changing decision_type enum** → Validation logic breaks
- **Making features optional** → Can't reproduce predictions
- **Removing model_version** → Can't track which model produced results

### Related Models

- **References**: `candidates.id`, `jobs.id`
- **Referenced by**: `rl_feedback.prediction_id`

---

## 15. RL Feedback Model

**Table Name**: `rl_feedback`  
**Purpose**: Collect feedback on RL predictions for model improvement  
**Primary Entity**: RL reward signal tracking

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "prediction_id": "integer (optional, foreign key)",
  "feedback_source": "enum (hr|client|candidate|system|workflow_automation, required)",
  "actual_outcome": "enum (hired|rejected|withdrawn|interviewed|shortlisted|pending, required)",
  "feedback_score": "decimal(5,2) (1-5, required)",
  "reward_signal": "decimal(5,2) (required)",
  "feedback_notes": "text (optional)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each feedback record
- **prediction_id**: Reference to RL prediction (optional if direct feedback)
- **feedback_source**: Who provided the feedback
- **actual_outcome**: Actual hiring outcome
- **feedback_score**: Satisfaction score (1-5 scale)
- **reward_signal**: Calculated reward for RL training
- **feedback_notes**: Additional context or comments
- **created_at**: When feedback was submitted

### Validation Rules

```
- prediction_id: optional, must reference existing prediction if provided
- feedback_source: must be one of 5 enum values (CHECK constraint)
- actual_outcome: must be one of 6 enum values (CHECK constraint)
- feedback_score: 1-5 (CHECK constraint)
- reward_signal: decimal, required (can be negative)
- feedback_notes: text, optional
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: feedback_source, actual_outcome, feedback_score, reward_signal, created_at
CHECK: feedback_source IN ('hr', 'client', 'candidate', 'system', 'workflow_automation')
CHECK: actual_outcome IN ('hired', 'rejected', 'withdrawn', 'interviewed', 'shortlisted', 'pending')
CHECK: feedback_score >= 1 AND feedback_score <= 5
FOREIGN KEY: prediction_id REFERENCES rl_predictions(id) ON DELETE CASCADE
INDEX: idx_rl_feedback_prediction (prediction_id)
INDEX: idx_rl_feedback_outcome (actual_outcome, created_at)
```

### Example Valid Record

```json
{
  "id": 1,
  "prediction_id": 1,
  "feedback_source": "hr",
  "actual_outcome": "hired",
  "feedback_score": 5.00,
  "reward_signal": 1.00,
  "feedback_notes": "Excellent candidate, perfect match. Hired within 2 weeks.",
  "created_at": "2025-12-20T15:30:00Z"
}
```

### Edge Cases

1. **Prediction deleted** → CASCADE delete removes feedback
2. **Negative reward signal** → Allowed for poor predictions
3. **Feedback without prediction_id** → Direct feedback, not tied to specific prediction
4. **Multiple feedback for same prediction** → Allowed, use latest or average
5. **Outcome 'pending' with high feedback_score** → Premature feedback, flag for review

### What Breaks If Schema Changes

- **Removing CHECK on feedback_score** → Invalid scores allowed
- **Changing outcome enum** → Validation logic breaks
- **Making prediction_id required** → Direct feedback fails
- **Removing reward_signal** → RL training breaks

### Related Models

- **References**: `rl_predictions.id`
- **Referenced by**: None (feedback table)

---

## 16. RL Model Performance Model

**Table Name**: `rl_model_performance`  
**Purpose**: Track RL model performance metrics over time  
**Primary Entity**: Model evaluation and monitoring

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "model_version": "string (20 chars, required)",
  "accuracy": "decimal(5,4) (0-1, required)",
  "precision_score": "decimal(5,4) (0-1, required)",
  "recall_score": "decimal(5,4) (0-1, required)",
  "f1_score": "decimal(5,4) (0-1, required)",
  "average_reward": "decimal(5,2) (required)",
  "total_predictions": "integer (>= 0, required)",
  "evaluation_date": "timestamp (required)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each performance record
- **model_version**: Version of model being evaluated
- **accuracy**: Overall prediction accuracy (0-1)
- **precision_score**: Precision metric (0-1)
- **recall_score**: Recall metric (0-1)
- **f1_score**: F1 score (harmonic mean of precision/recall)
- **average_reward**: Average reward signal received
- **total_predictions**: Number of predictions evaluated
- **evaluation_date**: When evaluation was performed
- **created_at**: Record creation timestamp

### Validation Rules

```
- model_version: NOT NULL, max 20 chars
- accuracy: 0-1 (CHECK constraint)
- precision_score: 0-1 (CHECK constraint)
- recall_score: 0-1 (CHECK constraint)
- f1_score: 0-1 (CHECK constraint)
- average_reward: decimal, required (can be negative)
- total_predictions: >= 0 (CHECK constraint)
- evaluation_date: NOT NULL
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: model_version, accuracy, precision_score, recall_score, f1_score, average_reward, total_predictions, evaluation_date, created_at
CHECK: accuracy >= 0 AND accuracy <= 1
CHECK: precision_score >= 0 AND precision_score <= 1
CHECK: recall_score >= 0 AND recall_score <= 1
CHECK: f1_score >= 0 AND f1_score <= 1
CHECK: total_predictions >= 0
INDEX: idx_rl_performance_version (model_version)
```

### Example Valid Record

```json
{
  "id": 1,
  "model_version": "v1.0.0",
  "accuracy": 0.8750,
  "precision_score": 0.9000,
  "recall_score": 0.8500,
  "f1_score": 0.8744,
  "average_reward": 0.75,
  "total_predictions": 150,
  "evaluation_date": "2025-12-09T12:00:00Z",
  "created_at": "2025-12-09T12:05:00Z"
}
```

### Edge Cases

1. **Zero predictions** → total_predictions = 0, metrics may be NULL or 0
2. **Negative average_reward** → Model performing poorly, need retraining
3. **Multiple evaluations per version** → Track performance over time
4. **F1 score calculation mismatch** → Validate formula in application layer
5. **Model version not in predictions table** → Orphaned performance record

### What Breaks If Schema Changes

- **Removing CHECK constraints** → Invalid metric values allowed
- **Changing score precision** → Rounding errors in calculations
- **Making evaluation_date optional** → Can't track when evaluation occurred
- **Removing model_version index** → Slow queries for version comparison

### Related Models

- **References**: None (metrics table)
- **Referenced by**: None

---

## 17. RL Training Data Model

**Table Name**: `rl_training_data`  
**Purpose**: Store training data for RL model retraining  
**Primary Entity**: ML training dataset

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "candidate_features": "jsonb (required)",
  "job_features": "jsonb (required)",
  "match_score": "decimal(5,2) (0-100, required)",
  "actual_outcome": "string (50 chars, required)",
  "reward_value": "decimal(5,2) (required)",
  "training_batch": "string (50 chars, optional)",
  "created_at": "timestamp (auto-set on insert)"
}
```

### Field Descriptions

- **id**: Unique identifier for each training record
- **candidate_features**: JSON object with candidate feature values
- **job_features**: JSON object with job feature values
- **match_score**: Predicted match score (0-100)
- **actual_outcome**: Actual hiring outcome
- **reward_value**: Reward signal for this training example
- **training_batch**: Batch identifier for grouped training
- **created_at**: When training data was created

### Validation Rules

```
- candidate_features: NOT NULL, valid JSONB
- job_features: NOT NULL, valid JSONB
- match_score: 0-100 (CHECK constraint)
- actual_outcome: NOT NULL, max 50 chars
- reward_value: decimal, required (can be negative)
- training_batch: max 50 chars, optional
- created_at: auto-set on insert
```

### Database Constraints

```sql
PRIMARY KEY: id
NOT NULL: candidate_features, job_features, match_score, actual_outcome, reward_value, created_at
CHECK: match_score >= 0 AND match_score <= 100
INDEX: idx_rl_training_batch (training_batch)
```

### Example Valid Record

```json
{
  "id": 1,
  "candidate_features": {
    "experience_years": 5,
    "skills_count": 8,
    "values_score": 4.6,
    "education_level": "bachelor"
  },
  "job_features": {
    "experience_required": 5,
    "skills_required": 6,
    "seniority": "senior",
    "department": "engineering"
  },
  "match_score": 87.50,
  "actual_outcome": "hired",
  "reward_value": 1.00,
  "training_batch": "batch_2025_12_09",
  "created_at": "2025-12-09T12:30:00Z"
}
```

### Edge Cases

1. **Features schema evolution** → JSONB flexible, but need consistent keys
2. **Negative reward_value** → Poor match, learn to avoid
3. **Large training dataset** → Partition by training_batch for performance
4. **Duplicate training examples** → No UNIQUE constraint, allowed
5. **Missing features in JSON** → Validate completeness in application layer

### What Breaks If Schema Changes

- **Removing JSONB type** → Lose flexible feature storage
- **Making training_batch required** → All unbatched data fails
- **Changing match_score range** → Need to rescale all training data
- **Removing CHECK constraint** → Invalid scores in training data

### Related Models

- **References**: None (training data table)
- **Referenced by**: None

---

## 18. Workflow Model

**Table Name**: `workflows`  
**Purpose**: Track LangGraph workflow executions  
**Primary Entity**: Workflow automation tracking

### Schema

```json
{
  "id": "integer (auto-increment, primary key)",
  "workflow_id": "string (100 chars, unique, required)",
  "workflow_type": "enum (candidate_application|candidate_shortlisted|interview_scheduled|custom, required)",
  "status": "enum (running|completed|failed|cancelled, default: running)",
  "candidate_id": "integer (optional, foreign key)",
  "job_id": "integer (optional, foreign key)",
  "client_id": "string (100 chars, optional, foreign key)",
  "progress_percentage": "integer (0-100, default: 0)",
  "current_step": "string (255 chars, optional)",
  "total_steps": "integer (default: 1)",
  "input_data": "jsonb (optional)",
  "output_data": "jsonb (optional)",
  "error_message": "text (optional)",
  "started_at": "timestamp (default: current_timestamp)",
  "completed_at": "timestamp (optional)",
  "updated_at": "timestamp (auto-updated on change)"
}
```

### Field Descriptions

- **id**: Unique identifier for each workflow execution
- **workflow_id**: Unique workflow execution ID (e.g., "wf_abc123")
- **workflow_type**: Type of workflow being executed
- **status**: Current workflow status
- **candidate_id**: Reference to candidate (if applicable)
- **job_id**: Reference to job (if applicable)
- **client_id**: Reference to client (if applicable)
- **progress_percentage**: Workflow completion percentage (0-100)
- **current_step**: Name of current workflow step
- **total_steps**: Total number of steps in workflow
- **input_data**: JSON object with workflow input parameters
- **output_data**: JSON object with workflow results
- **error_message**: Error message if workflow failed
- **started_at**: When workflow started
- **completed_at**: When workflow completed (NULL if still running)
- **updated_at**: Last status update timestamp

### Validation Rules

```
- workflow_id: NOT NULL, UNIQUE, max 100 chars
- workflow_type: must be one of 4 enum values (CHECK constraint)
- status: must be one of 4 enum values (CHECK constraint)
- candidate_id: optional, must reference existing candidate if provided
- job_id: optional, must reference existing job if provided
- client_id: optional, must reference existing client if provided
- progress_percentage: 0-100 (CHECK constraint)
- current_step: max 255 chars, optional
- total_steps: integer, default 1
- input_data: valid JSONB, optional
- output_data: valid JSONB, optional
- error_message: text, optional
- started_at: timestamp, default current_timestamp
- completed_at: timestamp, optional
- updated_at: auto-updated by trigger
```

### Database Constraints

```sql
PRIMARY KEY: id
UNIQUE: workflow_id
NOT NULL: workflow_id, workflow_type, status, progress_percentage, total_steps, started_at, updated_at
CHECK: workflow_type IN ('candidate_application', 'candidate_shortlisted', 'interview_scheduled', 'custom')
CHECK: status IN ('running', 'completed', 'failed', 'cancelled')
CHECK: progress_percentage >= 0 AND progress_percentage <= 100
FOREIGN KEY: candidate_id REFERENCES candidates(id) ON DELETE SET NULL
FOREIGN KEY: job_id REFERENCES jobs(id) ON DELETE SET NULL
FOREIGN KEY: client_id REFERENCES clients(client_id) ON DELETE SET NULL
INDEX: idx_workflows_workflow_id (workflow_id)
INDEX: idx_workflows_status (status)
INDEX: idx_workflows_type (workflow_type)
INDEX: idx_workflows_candidate (candidate_id)
INDEX: idx_workflows_job (job_id)
INDEX: idx_workflows_client (client_id)
INDEX: idx_workflows_started_at (started_at)
INDEX: idx_workflows_completed_at (completed_at)
TRIGGER: update_workflows_updated_at (auto-update updated_at)
TRIGGER: audit_workflows_changes (log all changes to audit_logs)
```

### Example Valid Record

```json
{
  "id": 1,
  "workflow_id": "wf_abc123def456",
  "workflow_type": "candidate_application",
  "status": "completed",
  "candidate_id": 1,
  "job_id": 1,
  "client_id": "TECH001",
  "progress_percentage": 100,
  "current_step": "send_confirmation_email",
  "total_steps": 5,
  "input_data": {
    "candidate_email": "alice@example.com",
    "job_title": "Senior Python Developer"
  },
  "output_data": {
    "email_sent": true,
    "notification_sent": true,
    "ai_score": 87.5
  },
  "error_message": null,
  "started_at": "2025-12-09T13:00:00Z",
  "completed_at": "2025-12-09T13:05:00Z",
  "updated_at": "2025-12-09T13:05:00Z"
}
```

### Edge Cases

1. **Workflow stuck in 'running' status** → Need timeout mechanism
2. **Candidate/job/client deleted** → Foreign key SET NULL, workflow continues
3. **Progress percentage > 100** → CHECK constraint prevents
4. **Workflow failed but progress = 100** → Status takes precedence
5. **Large input/output JSON** → No size limit, monitor storage

### What Breaks If Schema Changes

- **Removing UNIQUE on workflow_id** → Duplicate workflow tracking
- **Changing status enum** → Validation logic breaks
- **Making candidate_id required** → Non-candidate workflows fail
- **Removing JSONB fields** → Lose workflow context and results

### Related Models

- **References**: `candidates.id`, `jobs.id`, `clients.client_id`
- **Referenced by**: None (workflow tracking table)

---

## 19. Schema Version Model

**Table Name**: `schema_version`  
**Purpose**: Track database schema versions and migrations  
**Primary Entity**: Schema version control

### Schema

```json
{
  "version": "string (20 chars, primary key)",
  "applied_at": "timestamp (default: current_timestamp)",
  "description": "text (optional)"
}
```

### Field Descriptions

- **version**: Schema version identifier (e.g., "4.3.0")
- **applied_at**: When this version was applied
- **description**: Description of changes in this version

### Validation Rules

```
- version: NOT NULL, PRIMARY KEY, max 20 chars
- applied_at: timestamp, default current_timestamp
- description: text, optional
```

### Database Constraints

```sql
PRIMARY KEY: version
NOT NULL: version, applied_at
```

### Example Valid Record

```json
{
  "version": "4.3.0",
  "applied_at": "2025-12-04T10:00:00Z",
  "description": "Added RL + Feedback Agent tables (Ishan integration)"
}
```

### Edge Cases

1. **Multiple versions applied same day** → Track by applied_at timestamp
2. **Version rollback** → No built-in support, manual migration needed
3. **Version string format inconsistency** → Enforce semantic versioning
4. **Missing description** → Allowed (NULL), but recommended to document

### What Breaks If Schema Changes

- **Removing version table** → Lose migration history
- **Changing version to integer** → Semantic versioning breaks
- **Making description required** → All existing records without description fail

### Related Models

- **References**: None (metadata table)
- **Referenced by**: None

---

## Summary

### Model Statistics

- **Total Models**: 19
- **Core Application Models**: 8 (Candidate, Job, Job Application, Feedback, Interview, Offer, User, Client)
- **AI/ML Models**: 6 (Matching Cache, Company Scoring Preferences, RL Prediction, RL Feedback, RL Model Performance, RL Training Data)
- **Security/Audit Models**: 3 (Audit Log, Rate Limit, CSP Violation)
- **Operational Models**: 2 (Workflow, Schema Version)

### Key Relationships

```
candidates (root)
  ├─> job_applications (candidate_id)
  ├─> feedback (candidate_id)
  ├─> interviews (candidate_id)
  ├─> offers (candidate_id)
  ├─> matching_cache (candidate_id)
  ├─> rl_predictions (candidate_id)
  └─> workflows (candidate_id)

jobs (root)
  ├─> job_applications (job_id)
  ├─> feedback (job_id)
  ├─> interviews (job_id)
  ├─> offers (job_id)
  ├─> matching_cache (job_id)
  ├─> rl_predictions (job_id)
  ├─> workflows (job_id)
  └─> clients (client_id) [optional]

clients (root)
  ├─> jobs (client_id)
  ├─> company_scoring_preferences (client_id)
  ├─> audit_logs (client_id)
  └─> workflows (client_id)

users (root)
  └─> audit_logs (user_id)

rl_predictions
  └─> rl_feedback (prediction_id)
```

### Critical Constraints

1. **UNIQUE Constraints**: 8 tables (candidates.email, users.username, users.email, clients.client_id, clients.email, matching_cache composite, job_applications composite, workflows.workflow_id)
2. **CHECK Constraints**: 15 tables with value range validation
3. **FOREIGN KEY Constraints**: 13 tables with referential integrity
4. **CASCADE DELETE**: 11 relationships (cleanup on parent deletion)
5. **SET NULL**: 5 relationships (preserve child records)
6. **GENERATED COLUMNS**: 1 (feedback.average_score)
7. **TRIGGERS**: 9 tables with auto-update triggers, 7 tables with audit triggers

### Performance Indexes

- **Total Indexes**: 75+
- **Single Column**: 60+
- **Composite**: 5
- **Full-Text (GIN)**: 1 (candidates.technical_skills)
- **JSONB**: 0 (query JSONB fields directly)

### Data Integrity Rules

1. **Email Uniqueness**: Enforced for candidates, users, clients
2. **Score Ranges**: 0-5 for feedback, 0-100 for matching/RL scores
3. **Status Enums**: Enforced for candidates, jobs, interviews, offers, workflows
4. **Non-Negative Values**: experience_years, salary, request_count, total_predictions
5. **Referential Integrity**: All foreign keys validated
6. **Audit Trail**: All critical tables logged to audit_logs

---

**End of Data Models Documentation**


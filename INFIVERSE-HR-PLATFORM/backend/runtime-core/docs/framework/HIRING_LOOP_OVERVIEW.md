# Hiring Loop Overview

**Document Status**: DEMO-READY | REUSABLE | IMPLEMENTED  
**Created**: January 29, 2026  
**Updated**: January 29, 2026  
**Purpose**: Document the core hiring loop for reuse across multiple domains

**Current Implementation Status**: Production-ready hiring loop with 111 operational endpoints, MongoDB Atlas integration

---

## 🔄 Core Hiring Loop Definition

The hiring loop represents the fundamental workflow that transforms a job requirement into a filled position through candidate acquisition, evaluation, and selection. This loop is designed to be domain-agnostic and reusable across different business contexts.

### Loop Definition
```
Job Creation → Candidate Acquisition → Application Processing → Evaluation → Selection → Onboarding
```

### Current Implementation Flow
```
1. POST /v1/jobs (Gateway) → Job created in MongoDB
2. POST /v1/candidate/apply (Gateway) → Application stored
3. GET /v1/match/{job_id}/top (Gateway → Agent) → AI matching
4. POST /v1/feedback (Gateway) → Values assessment
5. POST /v1/interviews (Gateway) → Interview scheduling
6. POST /v1/offers (Gateway) → Offer management
7. LangGraph workflows → Automated notifications
```

---

## 📍 Inputs to the Hiring Loop

### 1. Job Requirements (job_specs)
- **job_id**: Unique identifier for the job opening (MongoDB ObjectId)
- **title**: Position title
- **description**: Detailed job description
- **requirements**: Technical and soft skills requirements
- **department**: Organizational department
- **location**: Work location (remote/hybrid/on-site)
- **experience_level**: Required years of experience
- **salary_range**: Compensation bracket (optional)
- **tenant_id**: Associated tenant/organization (for multi-tenant systems)
- **client_id**: Current implementation uses client_id for tenant context
- **status**: Job status (draft, published, closed)
- **created_at**: Timestamp for job creation

### 2. Candidate Profile (candidate_profile)
- **candidate_id**: Unique identifier for the candidate
- **name**: Full name
- **email**: Contact email
- **phone**: Contact phone
- **skills**: Technical and soft skills
- **experience_years**: Years of relevant experience
- **education**: Educational background
- **resume_text**: Raw resume content
- **values_scores**: Integrity, Honesty, Discipline, Hard Work, Gratitude ratings

### 3. Matching Criteria (matching_config)
- **skills_weight**: Weighting for skills matching (0-1)
- **experience_weight**: Weighting for experience matching (0-1)
- **values_weight**: Weighting for values alignment (0-1)
- **location_weight**: Weighting for location compatibility (0-1)
- **ai_model**: Current AI model in use (Phase 3 semantic engine)
- **fallback_enabled**: Boolean for database fallback when AI unavailable
- **matching_threshold**: Minimum score for positive match (default: 0.7)

---

## 🔄 State Transitions

### 1. Job Created
- **Initial State**: `draft` → `published`
- **Trigger**: Job posting by HR/Recruiter
- **Action**: Job becomes visible to candidates
- **Data Created**: job_id, job_details, status

### 2. Candidate Applied
- **State Transition**: `published` → `applications_received`
- **Trigger**: Candidate submits application
- **Action**: Application record created, candidate profile linked
- **Data Created**: application_id, candidate_job_link, application_date

### 3. Application Screened
- **State Transition**: `applications_received` → `screened`
- **Trigger**: AI-powered screening process
- **Action**: Automated evaluation against job requirements
- **Data Created**: ai_score, skills_match, experience_match, values_alignment

### 4. Application Reviewed
- **State Transition**: `screened` → `under_review` / `rejected`
- **Trigger**: HR/Candidate evaluation
- **Action**: Manual review of AI recommendations
- **Data Created**: reviewer_notes, acceptance_probability

### 5. Candidate Shortlisted
- **State Transition**: `under_review` → `shortlisted`
- **Trigger**: Positive review decision
- **Action**: Candidate moves to interview stage
- **Data Created**: shortlist_date, interview_schedule

### 6. Interview Conducted
- **State Transition**: `shortlisted` → `interviewed`
- **Trigger**: Interview completion
- **Action**: Interview feedback recorded
- **Data Created**: interview_notes, interviewer_ratings

### 7. Decision Made
- **State Transition**: `interviewed` → `offered` / `rejected`
- **Trigger**: Hiring decision
- **Action**: Offer extended or rejection sent
- **Data Created**: decision_reason, offer_details

### 8. Position Filled
- **State Transition**: `offered` → `hired` / `closed`
- **Trigger**: Acceptance or closure
- **Action**: Job status updated, candidate onboarded
- **Data Created**: hire_date, start_date

---

## 🗄️ Database Mutations

### 1. jobs Collection
- **Insert**: When job is created
- **Update**: When job status changes
- **Fields Modified**: status, applications_count, last_updated

### 2. candidates Collection  
- **Insert**: When new candidate applies
- **Update**: When candidate profile updated
- **Fields Modified**: last_applied_job, application_history

### 3. applications Collection
- **Insert**: When candidate applies to job
- **Update**: When application status changes
- **Fields Modified**: status, ai_score, matched_at, reviewed_at

### 4. matching_cache Collection
- **Insert**: When AI matching occurs
- **Update**: When re-matching happens
- **Fields Modified**: match_score, skills_match, experience_match, values_alignment

### 5. interviews Collection
- **Insert**: When interview scheduled
- **Update**: When interview completed
- **Fields Modified**: status, feedback, interviewer_ratings

### 6. feedback Collection
- **Insert**: When feedback submitted
- **Update**: When feedback updated
- **Fields Modified**: ratings, notes, decision_outcome

---

## 📡 Events Emitted

### 1. Job Events
- `job_created`: Emitted when new job is published
- `job_updated`: Emitted when job details change
- `job_closed`: Emitted when position is filled or cancelled

### 2. Application Events
- `candidate_applied`: Emitted when candidate submits application
- `application_screened`: Emitted when AI screening completes
- `application_reviewed`: Emitted when manual review completed
- `application_rejected`: Emitted when application is declined

### 3. Matching Events
- `ai_matching_started`: Emitted when AI processing begins
- `ai_matching_completed`: Emitted when AI scoring finishes
- `candidate_matched`: Emitted when candidate achieves high match score

### 4. Interview Events
- `interview_scheduled`: Emitted when interview is booked
- `interview_completed`: Emitted when interview finishes
- `interview_rescheduled`: Emitted when interview date changes

### 5. Decision Events
- `candidate_shortlisted`: Emitted when candidate advances
- `offer_extended`: Emitted when offer is made
- `candidate_hired`: Emitted when candidate accepts offer

---

## 🔄 Reusable Components

### 1. Job Processor
- **Function**: Manages job lifecycle from creation to closure
- **Inputs**: Job specifications
- **Outputs**: Validated job object
- **Reusable**: Yes - can process any job type

### 2. Candidate Matcher
- **Function**: Matches candidates to jobs using AI/ML
- **Inputs**: Candidate profile, job requirements, matching criteria
- **Outputs**: Match scores and recommendations
- **Reusable**: Yes - works across domains

### 3. Application Manager
- **Function**: Processes candidate applications
- **Inputs**: Application data
- **Outputs**: Application status updates
- **Reusable**: Yes - handles any application type

### 4. Workflow Orchestrator
- **Function**: Coordinates hiring workflow steps
- **Inputs**: Current state, transition rules
- **Outputs**: Next state, actions to perform
- **Reusable**: Yes - orchestrates any workflow

---

## 📋 Configuration Options

### 1. Matching Sensitivity
- **Parameter**: `matching_threshold`
- **Range**: 0.0 - 1.0
- **Default**: 0.7
- **Effect**: Minimum score for positive match

### 2. Workflow Stages
- **Parameter**: `enabled_stages`
- **Options**: ["screening", "evaluation", "interview", "decision"]
- **Effect**: Determines which stages to execute

### 3. Notification Settings
- **Parameter**: `notification_channels`
- **Options**: ["email", "sms", "telegram", "webhook"]
- **Effect**: Which channels to use for notifications

### 4. AI Model Selection
- **Parameter**: `matching_model`
- **Options**: ["basic", "advanced", "custom"]
- **Effect**: Which AI model to use for matching

---

## 🔧 Integration Points

### 1. External ATS Integration
- **API Endpoint**: `/v1/integration/ats/sync`
- **Method**: POST
- **Purpose**: Sync with external applicant tracking systems

### 2. Communication Services
- **API Endpoint**: `/v1/notifications/send`
- **Method**: POST
- **Purpose**: Send automated notifications to candidates

### 3. Background Check Services
- **API Endpoint**: `/v1/integration/background-check`
- **Method**: POST
- **Purpose**: Initiate background verification for selected candidates

### 4. Onboarding System
- **API Endpoint**: `/v1/onboarding/initiate`
- **Method**: POST
- **Purpose**: Start employee onboarding process after hire

---

## 🧪 Testing Scenarios

### 1. Happy Path
- Job created → Multiple candidates apply → Top candidates matched → Selected candidate hired

### 2. Rejection Path
- Job created → Candidates apply → All rejected during screening

### 3. Withdrawal Path
- Candidate applies → Candidate withdraws before decision

### 4. Multiple Job Path
- Same candidate applies to multiple jobs simultaneously

### 5. Parallel Processing
- Multiple jobs open → Multiple candidates applying → AI matching running concurrently

---

## ⚡ Performance Benchmarks

### 1. Processing Times
- Job creation: < 1 second
- Application submission: < 2 seconds
- AI matching: < 5 seconds per candidate
- Workflow transition: < 1 second

### 2. Throughput
- Applications per minute: 100+
- Concurrent matching operations: 50+
- API response time: < 100ms average

---

## 🔒 Security Considerations

### 1. Data Privacy
- Candidate personal information encrypted at rest
- Job details access controlled by tenant isolation
- Audit logs for all data access

### 2. Access Control
- Role-based permissions for workflow stages
- Tenant isolation for multi-tenant deployments
- API rate limiting to prevent abuse

### 3. Data Retention
- Application data retained per compliance requirements
- Temporary data purged automatically
- Audit logs maintained per policy

---

**Document Owner**: BHIV Platform Team  
**Next Review**: February 29, 2026
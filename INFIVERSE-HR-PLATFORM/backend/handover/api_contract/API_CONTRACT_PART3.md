# API Contract — Part 3: Gateway Advanced Features (41-50 of 111)

**Continued from:** [API_CONTRACT_PART2.md](./API_CONTRACT_PART2.md)

**Version:** 4.1.0  
**Last Updated:** January 22, 2026  
**Total Endpoints:** 111 (80 Gateway + 6 Agent + 25 LangGraph)  
**Database:** MongoDB Atlas  
**Analysis Source:** Comprehensive endpoint analysis from services directories

---

## Gateway AI Matching Engine

### 36. GET /v1/match/{job_id}/top

**Purpose:** AI-powered semantic candidate matching via Agent Service

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_top_matches()`

**Timeout:** 60s

**Request:**
```http
GET /v1/match/123/top?limit=10
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "matches": [
    {
      "candidate_id": 45,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "score": 92.5,
      "skills_match": "Python, FastAPI, PostgreSQL",
      "experience_match": "5y - Phase 3 matched",
      "location_match": true,
      "reasoning": "Semantic match: 0.95; Skills: Python, FastAPI, PostgreSQL; Experience: 5y; Location: San Francisco",
      "recommendation_strength": "Strong Match"
    }
  ],
  "top_candidates": [],
  "job_id": 123,
  "limit": 10,
  "total_candidates": 50,
  "algorithm_version": "3.0.0-phase3-production",
  "processing_time": "0.45s",
  "ai_analysis": "Real AI semantic matching via Agent Service",
  "agent_status": "connected"
}
```

**Sequence:**
1. Gateway calls Agent Service POST /match
2. Agent performs Phase 3 semantic matching
3. Results transformed to Gateway format
4. Fallback to database matching if Agent unavailable

**Error Responses:**
- 400 Bad Request: Invalid job_id or limit
- 404 Not Found: Job not found
- 503 Service Unavailable: Agent service down (fallback activated)

**When Called:** HR views top candidates for job

**Database Impact:** SELECT from candidates, jobs collections

---

### 37. POST /v1/match/batch

**Purpose:** Batch AI matching for multiple jobs

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `batch_match_jobs()`

**Timeout:** 120s

**Request:**
```http
POST /v1/match/batch
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "job_ids": [123, 124, 125]
}
```

**Response (200 OK):**
```json
{
  "batch_results": {
    "123": {
      "job_id": 123,
      "matches": [
        {
          "candidate_id": 45,
          "name": "John Doe",
          "email": "john.doe@example.com",
          "score": 92.5,
          "skills_match": "Python, FastAPI",
          "experience_match": "5y - Phase 3 matched",
          "location_match": true,
          "reasoning": "Skills: Python, FastAPI; Experience: 5y; Phase 3 AI semantic analysis",
          "recommendation_strength": "Strong Match"
        }
      ],
      "top_candidates": [],
      "total_candidates": 5,
      "algorithm": "phase3-ai",
      "processing_time": "0.5s",
      "ai_analysis": "Real AI semantic matching via Agent Service"
    }
  },
  "total_jobs_processed": 3,
  "total_candidates_analyzed": 50,
  "algorithm_version": "3.0.0-phase3-production-batch",
  "status": "success",
  "agent_status": "connected"
}
```

**Error Responses:**
- 400 Bad Request: Empty job_ids or > 10 jobs
- 404 Not Found: Jobs not found
- 503 Service Unavailable: Agent service down (fallback activated)

**When Called:** HR compares candidates across multiple jobs

**Database Impact:** SELECT from candidates, jobs collections

---

## Gateway Assessment & Workflow

### 38. POST /v1/feedback

**Purpose:** Submit values assessment feedback for candidate

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `submit_feedback()`

**Timeout:** 15s

**Request:**
```http
POST /v1/feedback
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "integrity": 5,
  "honesty": 5,
  "discipline": 4,
  "hard_work": 5,
  "gratitude": 4,
  "comments": "Excellent candidate with strong values alignment"
}
```

**Response (200 OK):**
```json
{
  "message": "Feedback submitted successfully",
  "feedback_id": 789,
  "candidate_id": 123,
  "job_id": 45,
  "values_scores": {
    "integrity": 5,
    "honesty": 5,
    "discipline": 4,
    "hard_work": 5,
    "gratitude": 4
  },
  "average_score": 4.6,
  "submitted_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid score values (must be 1-5)
- 404 Not Found: Candidate or job not found

**When Called:** HR submits post-interview feedback

**Database Impact:** INSERT into feedback collection

---

### 39. GET /v1/feedback

**Purpose:** Get all feedback records with candidate/job details

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_all_feedback()`

**Timeout:** 15s

**Request:**
```http
GET /v1/feedback
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "feedback": [
    {
      "id": 789,
      "candidate_id": 123,
      "job_id": 45,
      "values_scores": {
        "integrity": 5,
        "honesty": 5,
        "discipline": 4,
        "hard_work": 5,
        "gratitude": 4
      },
      "average_score": 4.6,
      "comments": "Excellent candidate with strong values alignment",
      "created_at": "2026-01-22T13:37:00Z",
      "candidate_name": "John Doe",
      "job_title": "Senior Software Engineer"
    }
  ],
  "count": 1
}
```

**When Called:** HR reviews feedback history

**Database Impact:** SELECT from feedback, candidates, jobs collections with JOIN

---

### 40. GET /v1/interviews

**Purpose:** Get all scheduled interviews

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_interviews()`

**Timeout:** 15s

**Request:**
```http
GET /v1/interviews
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "interviews": [
    {
      "id": 456,
      "candidate_id": 123,
      "job_id": 45,
      "interview_date": "2026-01-29T14:00:00Z",
      "interviewer": "Sarah Johnson",
      "status": "scheduled",
      "candidate_name": "John Doe",
      "job_title": "Senior Software Engineer"
    }
  ],
  "count": 1
}
```

**When Called:** HR views interview schedule

**Database Impact:** SELECT from interviews, candidates, jobs collections with JOIN

---

### 41. POST /v1/interviews

**Purpose:** Schedule new interview

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `schedule_interview()`

**Timeout:** 20s

**Request:**
```http
POST /v1/interviews
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "interview_date": "2026-01-29T14:00:00Z",
  "interviewer": "Sarah Johnson",
  "notes": "Technical interview - focus on system design"
}
```

**Response (200 OK):**
```json
{
  "message": "Interview scheduled successfully",
  "interview_id": 456,
  "candidate_id": 123,
  "job_id": 45,
  "interview_date": "2026-01-29T14:00:00Z",
  "status": "scheduled"
}
```

**Sequence:**
1. Validate candidate and job exist
2. Insert into interviews collection with status='scheduled'
3. Trigger interview.scheduled webhook
4. Send notification to candidate

**Error Responses:**
- 400 Bad Request: Invalid date format
- 404 Not Found: Candidate or job not found
- 500 Internal Server Error: Database error

**When Called:** HR schedules interview

**Database Impact:** INSERT into interviews collection

---

### 42. POST /v1/offers

**Purpose:** Create job offer for candidate

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `create_job_offer()`

**Timeout:** 15s

**Request:**
```http
POST /v1/offers
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "salary": 150000.00,
  "start_date": "2026-02-01",
  "terms": "Full-time, remote, benefits included"
}
```

**Response (200 OK):**
```json
{
  "message": "Job offer created successfully",
  "offer_id": 999,
  "candidate_id": 123,
  "job_id": 45,
  "salary": 150000.00,
  "start_date": "2026-02-01",
  "terms": "Full-time, remote, benefits included",
  "status": "pending",
  "created_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid salary or date
- 404 Not Found: Candidate or job not found

**When Called:** HR extends job offer

**Database Impact:** INSERT into offers collection

---

### 43. GET /v1/offers

**Purpose:** Get all job offers

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_all_offers()`

**Timeout:** 15s

**Request:**
```http
GET /v1/offers
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "offers": [
    {
      "id": 999,
      "candidate_id": 123,
      "job_id": 45,
      "salary": 150000.00,
      "start_date": "2026-02-01",
      "terms": "Full-time, remote, benefits included",
      "status": "pending",
      "created_at": "2026-01-22T13:37:00Z",
      "candidate_name": "John Doe",
      "job_title": "Senior Software Engineer"
    }
  ],
  "count": 1
}
```

**When Called:** HR reviews offer status

**Database Impact:** SELECT from offers, candidates, jobs collections with JOIN

---

## Gateway Client Portal API

### 44. POST /v1/client/register

**Purpose:** Register new client company

**Authentication:** None (public registration)

**Implementation:** `services/gateway/app/main.py` → `client_register()`

**Timeout:** 15s

**Request:**
```http
POST /v1/client/register
Content-Type: application/json

{
  "client_id": "TECH001",
  "company_name": "Tech Innovations Inc",
  "contact_email": "hr@techinnovations.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Client registration successful",
  "client_id": "TECH001",
  "company_name": "Tech Innovations Inc"
}
```

**Sequence:**
1. Check client_id uniqueness
2. Check email uniqueness
3. Hash password with bcrypt
4. Insert into clients collection with status='active'
5. Return success confirmation

**Error Responses:**
- 409 Conflict: Client ID or email already exists
- 400 Bad Request: Invalid input data

**When Called:** New client signs up

**Database Impact:** INSERT into clients collection

---

### 45. POST /v1/client/login

**Purpose:** Client authentication with JWT token generation

**Authentication:** None (public login)

**Implementation:** `services/gateway/app/main.py` → `client_login()`

**Timeout:** 10s

**Request:**
```http
POST /v1/client/login
Content-Type: application/json

{
  "client_id": "TECH001",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Authentication successful",
  "client_id": "TECH001",
  "company_name": "Tech Innovations Inc",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "permissions": [
    "view_jobs",
    "create_jobs",
    "view_candidates",
    "schedule_interviews"
  ]
}
```

**Sequence:**
1. Lookup client by client_id
2. Check account status (active/locked)
3. Verify password with bcrypt
4. Generate JWT token (HS256, 24h expiry, JWT_SECRET_KEY)
5. Reset failed login attempts
6. Return token and permissions

**Error Responses:**
- 401 Unauthorized: Invalid credentials
- 403 Forbidden: Account locked (5 failed attempts)
- 404 Not Found: Client not found

**When Called:** Client logs into portal

**Database Impact:** SELECT from clients collection, UPDATE failed_login_attempts

---

## Summary Table - Part 3

| Endpoint | Method | Category | Purpose | Auth Required | Timeout |
|----------|--------|----------|---------|---------------|---------|
| /v1/match/{job_id}/top | GET | AI Matching | Get top matches | Yes | 60s |
| /v1/match/batch | POST | AI Matching | Batch matching | Yes | 120s |
| /v1/feedback | POST | Assessment | Submit feedback | Yes | 15s |
| /v1/feedback | GET | Assessment | Get feedback | Yes | 15s |
| /v1/interviews | GET | Workflow | List interviews | Yes | 15s |
| /v1/interviews | POST | Workflow | Schedule interview | Yes | 20s |
| /v1/offers | POST | Workflow | Create offer | Yes | 15s |
| /v1/offers | GET | Workflow | List offers | Yes | 15s |
| /v1/client/register | POST | Client Portal | Register client | No | 15s |
| /v1/client/login | POST | Client Portal | Client login | No | 10s |

**Total Endpoints in Part 3:** 10 (36-45 of 111)

---

**Continue to:** [API_CONTRACT_PART4.md](./API_CONTRACT_PART4.md) for Gateway Security & Portals
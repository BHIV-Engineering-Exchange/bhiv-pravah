# API Contract — BHIV HR Platform Gateway API (Part 1)

**Version:** 4.1.0  
**Last Updated:** January 22, 2026  
**Total Endpoints:** 111 (80 Gateway + 6 Agent + 25 LangGraph)  
**Database:** MongoDB Atlas  
**Analysis Source:** Comprehensive endpoint analysis from services directories

---

## Table of Contents

### Part 1: Core Services (1-18 of 111)
1. [Authentication & Standards](#authentication--standards)
2. [Gateway API - Monitoring (3 endpoints)](#gateway-monitoring)
3. [Gateway API - Core API (5 endpoints)](#gateway-core-api) 
4. [Gateway API - AI Integration (2 endpoints)](#gateway-ai-integration)

### Part 2: Gateway Core Features (19-35 of 111)
- Job Management (2 endpoints)
- Candidate Management (6 endpoints)
- Analytics & Statistics (2 endpoints)
- Candidate Portal (2 endpoints)
- RL + Feedback Agent (4 endpoints)
- Recruiter Portal (1 endpoint)

### Part 3: Gateway Advanced Features (36-45 of 111)
- AI Matching Engine (2 endpoints)
- Assessment & Workflow (6 endpoints)
- Client Portal API (2 endpoints)

### Part 4: Gateway Security & Portals (46-80 of 111)
- Security Testing (10 endpoints)
- CSP Management (4 endpoints)
- Two-Factor Authentication (8 endpoints)
- Password Management (6 endpoints)
- Candidate Portal (6 endpoints)

### Part 5: AI Agent & LangGraph Services (81-111 of 111)
- AI Agent API (6 endpoints)
- LangGraph API (25 endpoints)

---

## Authentication & Standards

### Authentication Methods

**1. API Key Authentication (Primary)**
```http
Authorization: Bearer YOUR_API_KEY_HERE
```

**2. Client JWT Token**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**3. Candidate JWT Token**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Base URLs

| Service | Production URL | Local URL |
|---------|---------------|-----------|
| **Gateway** | https://bhiv-hr-gateway-ltg0.onrender.com | http://localhost:8000 |
| **AI Agent** | https://bhiv-hr-agent-nhgg.onrender.com | http://localhost:9000 |
| **LangGraph** | https://bhiv-hr-langgraph.onrender.com | http://localhost:9001 |

### Standard Response Format

**Success Response:**
```json
{
  "status": "success",
  "data": {},
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Detailed error description",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/POST/PUT |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Invalid/missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Rate Limiting

**Dynamic Rate Limits:**
- Default: 60 requests/minute
- Premium: 300 requests/minute
- CPU-based adjustment: 50-150% of base limit

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1702134000
```

### Timeout Configurations

| Operation | Timeout |
|-----------|---------|
| API Requests | 30s |
| Database Operations | 15s |
| External Service Calls | 60s |
| File Uploads | 120s |

---

## Gateway Monitoring

### 1. GET /metrics

**Purpose:** Export Prometheus metrics for monitoring

**Authentication:** None (public monitoring endpoint)

**Implementation:** `services/gateway/app/main.py` → `get_prometheus_metrics()`

**Timeout:** 10s

**Request:**
```http
GET /metrics
```

**Response (200 OK):**
```text
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 1234
http_requests_total{method="POST",endpoint="/v1/jobs"} 567

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 890
http_request_duration_seconds_bucket{le="0.5"} 1150
http_request_duration_seconds_sum 234.5
http_request_duration_seconds_count 1234

# HELP active_connections Active database connections
# TYPE active_connections gauge
active_connections 8
```

**When Called:** Prometheus scrapes metrics every 15s

**Database Impact:** None (system metrics only)

---

### 2. GET /health/detailed

**Purpose:** Detailed health check with system metrics

**Authentication:** None (public health endpoint)

**Implementation:** `services/gateway/app/main.py` → `detailed_health_check()`

**Timeout:** 5s

**Request:**
```http
GET /health/detailed
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "BHIV HR Gateway",
  "version": "4.2.0",
  "timestamp": "2026-01-22T13:37:00Z",
  "uptime_seconds": 86400,
  "database": {
    "status": "connected",
    "pool_size": 10,
    "active_connections": 3,
    "idle_connections": 7
  },
  "dependencies": {
    "agent_service": "healthy",
    "langgraph_service": "healthy",
    "mongodb": "healthy"
  },
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 512,
    "disk_usage": 45.2
  }
}
```

**When Called:** Load balancer health checks, monitoring dashboard

**Database Impact:** None (system metrics only)

---

### 3. GET /metrics/dashboard

**Purpose:** Metrics dashboard data for admin UI

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `metrics_dashboard()`

**Timeout:** 20s

**Request:**
```http
GET /metrics/dashboard
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "performance_summary": {
    "avg_response_time_ms": 45.2,
    "p95_response_time_ms": 120.5,
    "p99_response_time_ms": 250.0,
    "requests_per_minute": 150,
    "error_rate": 0.02
  },
  "business_metrics": {
    "total_candidates": 1234,
    "active_jobs": 45,
    "applications_today": 67,
    "interviews_scheduled": 23
  },
  "system_metrics": {
    "cpu_usage": 25.5,
    "memory_mb": 512,
    "disk_usage_percent": 45.2,
    "active_connections": 8
  },
  "generated_at": "2026-01-22T13:37:00Z"
}
```

**When Called:** Admin dashboard loads metrics

**Database Impact:** Multiple aggregate queries for metrics

---

## Gateway Core API

### 4. GET /openapi.json

**Purpose:** OpenAPI schema for API documentation

**Authentication:** None (public documentation)

**Implementation:** `services/gateway/app/main.py` → `get_openapi()`

**Timeout:** 2s

**Request:**
```http
GET /openapi.json
```

**Response (200 OK):**
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "BHIV HR Platform API Gateway",
    "version": "4.2.0",
    "description": "Enterprise HR Platform with Advanced Security Features"
  },
  "paths": {
    "/health": {
      "get": {
        "summary": "Health Check",
        "responses": {
          "200": {
            "description": "Successful Response"
          }
        }
      }
    }
  }
}
```

**When Called:** API documentation tools, client SDK generation

**Database Impact:** None (static response)

---

### 5. GET /docs

**Purpose:** Interactive API documentation (Swagger UI)

**Authentication:** None (public documentation)

**Implementation:** `services/gateway/app/main.py` → `get_docs()`

**Timeout:** 5s

**Request:**
```http
GET /docs
```

**Response (200 OK):**
```html
<!DOCTYPE html>
<html>
<head>
  <title>BHIV HR Platform API</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
</body>
</html>
```

**When Called:** Developers access API documentation

**Database Impact:** None (static response)

---

### 6. GET /

**Purpose:** API root information and service status

**Authentication:** None (public endpoint)

**Implementation:** `services/gateway/app/main.py` → `read_root()`

**Timeout:** 5s

**Request:**
```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "BHIV HR Platform API Gateway",
  "version": "4.2.0",
  "status": "healthy",
  "endpoints": 80,
  "documentation": "/docs",
  "monitoring": "/metrics",
  "production_url": "https://bhiv-hr-gateway-ltg0.onrender.com",
  "langgraph_integration": "active",
  "ai_workflows": [
    "candidate_applied",
    "shortlisted",
    "interview_scheduled"
  ]
}
```

**Response Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

**When Called:** Service discovery, health check

**Database Impact:** None (static response)

---

### 7. GET /health

**Purpose:** Basic health check endpoint

**Authentication:** None (public health endpoint)

**Implementation:** `services/gateway/app/main.py` → `health_check()`

**Timeout:** 2s

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "BHIV HR Gateway",
  "version": "4.2.0",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Response Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

**When Called:** Load balancer health checks, monitoring systems

**Database Impact:** None (static response)

---

### 8. GET /v1/test-candidates

**Purpose:** Test database connectivity with candidate count

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_candidates_db()`

**Timeout:** 10s

**Request:**
```http
GET /v1/test-candidates
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "database_status": "connected",
  "total_candidates": 1234,
  "test_timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 500 Internal Server Error: Database connection failed

**When Called:** System diagnostics, deployment verification

**Database Impact:** COUNT query on candidates collection

---

## Gateway AI Integration

### 9. POST /api/v1/test-communication

**Purpose:** Test multi-channel communication system (Email, WhatsApp, Telegram)

**Authentication:** Bearer token required

**Implementation:** `services/gateway/routes/ai_integration.py` → `test_communication_system()`

**Timeout:** 30s

**Request:**
```http
POST /api/v1/test-communication
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "test_type": "all_channels",
  "recipient_email": "test@example.com",
  "recipient_phone": "+1234567890",
  "telegram_chat_id": "123456789"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "results": {
    "email": {
      "sent": true,
      "message_id": "msg_abc123",
      "provider": "gmail_smtp"
    },
    "whatsapp": {
      "sent": true,
      "message_sid": "SM1234567890abcdef",
      "provider": "twilio"
    },
    "telegram": {
      "sent": true,
      "message_id": 456789,
      "provider": "telegram_bot_api"
    }
  },
  "test_timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 500 Internal Server Error: Communication service unavailable
- 400 Bad Request: Invalid recipient data

**When Called:** Admin tests notification system

**Database Impact:** None (external service calls only)

---

### 10. POST /api/v1/gemini/analyze

**Purpose:** Analyze candidate profile using Google Gemini AI

**Authentication:** Bearer token required

**Implementation:** `services/gateway/routes/ai_integration.py` → `analyze_with_gemini()`

**Timeout:** 60s

**Request:**
```http
POST /api/v1/gemini/analyze
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "analysis_type": "comprehensive",
  "include_recommendations": true
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "candidate_id": 123,
  "analysis": {
    "skills_assessment": "Strong technical background in Python, FastAPI, and cloud technologies",
    "experience_evaluation": "5+ years of relevant experience with progressive responsibility",
    "cultural_fit": "High alignment with company values",
    "strengths": ["Technical expertise", "Problem-solving", "Communication"],
    "areas_for_development": ["Leadership experience", "Domain knowledge"],
    "overall_score": 85.5,
    "recommendation": "Strong candidate - proceed to interview"
  },
  "ai_model": "gemini-pro",
  "analyzed_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 404 Not Found: Candidate not found
- 503 Service Unavailable: Gemini API unavailable

**When Called:** HR requests AI analysis of candidate

**Database Impact:** SELECT from candidates collection

---

### 11. POST /api/v1/workflow/trigger

**Purpose:** Trigger automated workflow for candidate processing

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `trigger_workflow()`

**Timeout:** 10s

**Request:**
```http
POST /api/v1/workflow/trigger
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "workflow_type": "candidate_application",
  "candidate_id": 123,
  "job_id": 45,
  "trigger_event": "application_submitted"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "workflow_id": "wf_abc123def456",
  "workflow_type": "candidate_application",
  "triggered_at": "2026-01-22T13:37:00Z",
  "estimated_completion": "2026-01-22T13:42:00Z",
  "tracking_url": "/api/v1/workflow/status/wf_abc123def456"
}
```

**Sequence:**
1. Validate input data
2. Create workflow instance in LangGraph
3. Emit workflow.started event
4. Return workflow ID for tracking
5. Execute workflow asynchronously

**Error Responses:**
- 400 Bad Request: Invalid workflow type
- 404 Not Found: Candidate or job not found
- 503 Service Unavailable: LangGraph service down

**When Called:** Candidate submits application, HR triggers manual workflow

**Database Impact:** INSERT into workflows collection

---

### 12. GET /api/v1/workflow/status/{workflow_id}

**Purpose:** Get real-time workflow execution status

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `get_workflow_status()`

**Timeout:** 15s

**Request:**
```http
GET /api/v1/workflow/status/wf_abc123def456
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "workflow_id": "wf_abc123def456",
  "status": "running",
  "progress_percentage": 65,
  "current_step": "ai_matching_analysis",
  "total_steps": 5,
  "steps_completed": [
    "data_validation",
    "initial_screening",
    "ai_matching_analysis"
  ],
  "steps_remaining": [
    "recommendation_generation",
    "notification_dispatch"
  ],
  "started_at": "2026-01-22T13:37:00Z",
  "estimated_completion": "2026-01-22T13:42:00Z",
  "last_updated": "2026-01-22T13:40:00Z"
}
```

**Error Responses:**
- 404 Not Found: Workflow ID not found
- 401 Unauthorized: Invalid API key

**When Called:** Dashboard polls for workflow updates, WebSocket alternative

**Database Impact:** SELECT from workflows collection

---

### 13. GET /api/v1/workflow/list

**Purpose:** List all workflows with filtering options

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `list_workflows()`

**Timeout:** 20s

**Request:**
```http
GET /api/v1/workflow/list?status=running&limit=20&offset=0
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "workflows": [
    {
      "workflow_id": "wf_abc123",
      "workflow_type": "candidate_application",
      "status": "running",
      "candidate_id": 123,
      "job_id": 45,
      "progress_percentage": 65,
      "started_at": "2026-01-22T13:37:00Z"
    },
    {
      "workflow_id": "wf_def456",
      "workflow_type": "interview_scheduling",
      "status": "completed",
      "candidate_id": 124,
      "job_id": 46,
      "progress_percentage": 100,
      "started_at": "2026-01-22T13:30:00Z",
      "completed_at": "2026-01-22T13:35:00Z"
    }
  ],
  "total_count": 2,
  "limit": 20,
  "offset": 0,
  "filters_applied": {
    "status": "running"
  }
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Dashboard loads workflow list, admin monitors system

**Database Impact:** SELECT from workflows collection with filters

---

### 14. GET /api/v1/workflows

**Purpose:** Alternative endpoint to list workflows

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `list_workflows_alt()`

**Timeout:** 20s

**Request:**
```http
GET /api/v1/workflows?status=running&limit=20
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "workflows": [
    {
      "workflow_id": "wf_abc123",
      "workflow_type": "candidate_application",
      "status": "running",
      "candidate_id": 123,
      "job_id": 45,
      "progress_percentage": 65,
      "started_at": "2026-01-22T13:37:00Z"
    }
  ],
  "count": 1
}
```

**When Called:** Alternative workflow listing interface

**Database Impact:** SELECT from workflows collection

---

### 15. GET /api/v1/workflow/health

**Purpose:** Check LangGraph service health and connectivity

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `check_langgraph_health()`

**Timeout:** 10s

**Request:**
```http
GET /api/v1/workflow/health
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "langgraph-orchestrator",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "active_workflows": 5,
  "total_workflows_processed": 1234,
  "database_connection": "connected",
  "last_health_check": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 503 Service Unavailable: LangGraph service down

**When Called:** Gateway startup, periodic health checks

**Database Impact:** Health check with LangGraph service

---

### 16. POST /api/v1/webhooks/candidate-applied

**Purpose:** Webhook triggered when candidate applies for job

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `webhook_candidate_applied()`

**Timeout:** 30s

**Request:**
```http
POST /api/v1/webhooks/candidate-applied
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "application_id": 789,
  "candidate_email": "john.doe@example.com",
  "candidate_phone": "+1234567890",
  "candidate_name": "John Doe",
  "job_title": "Senior Software Engineer",
  "applied_at": "2026-01-22T13:37:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "webhook_processed": true,
  "workflow_triggered": true,
  "workflow_id": "wf_abc123",
  "notifications_sent": ["email", "whatsapp"],
  "processed_at": "2026-01-22T13:37:00Z"
}
```

**Sequence:**
1. Receive webhook payload
2. Validate candidate and job data
3. Trigger LangGraph workflow
4. Send confirmation notifications
5. Return workflow ID

**Error Responses:**
- 400 Bad Request: Invalid payload
- 404 Not Found: Candidate or job not found

**When Called:** Candidate portal submits application

**Database Impact:** Trigger workflow and notification processes

---

### 17. POST /api/v1/webhooks/candidate-shortlisted

**Purpose:** Webhook triggered when candidate is shortlisted

**Authentication:** Bearer token required

**Implementation:** `services/gateway/langgraph_integration.py` → `webhook_candidate_shortlisted()`

**Timeout:** 30s

**Request:**
```http
POST /api/v1/webhooks/candidate-shortlisted
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "shortlisted_by": "hr_manager_001",
  "matching_score": 85.5,
  "shortlisted_at": "2026-01-22T13:37:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "webhook_processed": true,
  "workflow_triggered": true,
  "workflow_id": "wf_def456",
  "notifications_sent": ["email", "whatsapp", "telegram"],
  "next_action": "schedule_interview",
  "processed_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid payload
- 404 Not Found: Candidate or job not found

**When Called:** HR shortlists candidate in portal

**Database Impact:** Trigger workflow and notification processes

---

### 18. POST /api/v1/webhooks/interview-scheduled

**Purpose:** Webhook for when interview is scheduled

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `interview_scheduled_webhook()`

**Timeout:** 30s

**Request:**
```http
POST /api/v1/webhooks/interview-scheduled
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_id": 123,
  "job_id": 45,
  "interview_id": 789,
  "scheduled_time": "2026-01-25T14:00:00Z",
  "interview_type": "technical",
  "interviewer": "tech_lead_001",
  "meeting_link": "https://meet.google.com/abc-defg-hij"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "webhook_processed": true,
  "notifications_sent": ["email", "whatsapp"],
  "calendar_event_created": true,
  "reminders_set": true,
  "processed_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid payload
- 404 Not Found: Candidate, job, or interview not found

**When Called:** Interview coordinator schedules interview

**Database Impact:** Create calendar events and send notifications

---

## Summary Table - Part 1

| Endpoint | Method | Category | Purpose | Auth Required | Timeout |
|----------|--------|----------|---------|---------------|---------|
| /metrics | GET | Monitoring | Prometheus metrics | No | 10s |
| /health/detailed | GET | Monitoring | Detailed health check | No | 5s |
| /metrics/dashboard | GET | Monitoring | Dashboard metrics | Yes | 20s |
| /openapi.json | GET | Core API | OpenAPI schema | No | 2s |
| /docs | GET | Core API | API documentation | No | 5s |
| / | GET | Core API | Service info | No | 5s |
| /health | GET | Core API | Basic health check | No | 2s |
| /v1/test-candidates | GET | Core API | Test database | Yes | 10s |
| /api/v1/test-communication | POST | AI Integration | Test notifications | Yes | 30s |
| /api/v1/gemini/analyze | POST | AI Integration | AI candidate analysis | Yes | 60s |
| /api/v1/workflow/trigger | POST | LangGraph | Trigger workflow | Yes | 10s |
| /api/v1/workflow/status/{workflow_id} | GET | LangGraph | Get workflow status | Yes | 15s |
| /api/v1/workflow/list | GET | LangGraph | List workflows | Yes | 20s |
| /api/v1/workflows | GET | LangGraph | List workflows alt | Yes | 20s |
| /api/v1/workflow/health | GET | LangGraph | Check service health | Yes | 10s |
| /api/v1/webhooks/candidate-applied | POST | LangGraph | Application webhook | Yes | 30s |
| /api/v1/webhooks/candidate-shortlisted | POST | LangGraph | Shortlist webhook | Yes | 30s |
| /api/v1/webhooks/interview-scheduled | POST | LangGraph | Interview scheduled webhook | Yes | 30s |

**Total Endpoints in Part 1:** 18 (1-18 of 111)

---

**Continue to:** [API_CONTRACT_PART2.md](./API_CONTRACT_PART2.md) for Gateway Core Features
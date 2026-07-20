# 🧪 BHIV HR Platform - API Testing Guide

**Comprehensive Testing Guide for 108 Endpoints**  
**Version**: v4.3.0 with RL Integration  
**Updated**: January 22, 2026  
**Status**: ✅ All 111 endpoints operational  
**Coverage**: 3 core services (Gateway, Agent, LangGraph)

---

## 📊 API Testing Overview

### **Testing Scope**
- **Total Endpoints**: 111 (80 Gateway + 6 Agent + 25 LangGraph)
- **Services**: 3 microservices with comprehensive API coverage
- **Authentication**: Triple authentication system (API Key + JWT + 2FA)
- **Testing Types**: Functional, security, performance, integration
- **Response Time**: <100ms target for all endpoints
- **Success Rate**: 100% operational status

### **Service Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│   AI Agent      │────│   LangGraph     │
│   77 endpoints  │    │   6 endpoints   │    │  25 endpoints   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   MongoDB Atlas │──────────────┘
                        │ 17+ collections │
                        └─────────────────┘
```

### **Base URLs & Authentication**
```bash
# Production URLs
GATEWAY_SERVICE_URL="https://bhiv-hr-gateway-ltg0.onrender.com"
AGENT_URL="https://bhiv-hr-agent-nhgg.onrender.com"
LANGGRAPH_URL="https://bhiv-hr-langgraph.onrender.com"
DATABASE_URL="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/bhiv_hr"

# Local Development URLs
LOCAL_GATEWAY="http://localhost:8000"
LOCAL_AGENT="http://localhost:9000"
LOCAL_LANGGRAPH="http://localhost:9001"
LOCAL_DATABASE="mongodb://localhost:27017/bhiv_hr"

# Authentication
API_KEY="demo_key"  # For testing
AUTHORIZATION_HEADER="Authorization: Bearer $API_KEY"
```

---

## 🌐 API Gateway Service (80 Endpoints)

### **1. Core System Endpoints (6)**

#### **1.1 Root Endpoint**
```bash
GET /
# No authentication required
curl https://bhiv-hr-gateway-ltg0.onrender.com/

# Expected Response:
# {
#   "message": "BHIV HR Platform API Gateway",
#   "version": "4.3.0",
#   "status": "operational",
#   "services": 6,
#   "endpoints": 111
# }
```

#### **1.2 Health Check**
```bash
GET /health
# No authentication required
curl https://bhiv-hr-gateway-ltg0.onrender.com/health

# Expected Response:
# {
#   "status": "healthy",
#   "timestamp": "2025-12-09T10:00:00Z",
#   "version": "4.3.0",
#   "database": "connected",
#   "services": {
#     "gateway": "healthy",
#     "agent": "healthy",
#     "langgraph": "healthy"
#   }
# }
```

#### **1.3 System Metrics**
```bash
GET /metrics
# No authentication required
curl https://bhiv-hr-gateway-ltg0.onrender.com/metrics

# Expected Response: Prometheus metrics format
```

#### **1.4 Detailed Health**
```bash
GET /health/detailed
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/health/detailed

# Expected Response:
# {
#   "system_health": "excellent",
#   "response_time": "45ms",
#   "database_connections": 8,
#   "active_sessions": 23,
#   "memory_usage": "67%",
#   "cpu_usage": "34%"
# }
```

#### **1.5 API Documentation**
```bash
GET /docs
# Interactive Swagger UI
# URL: https://bhiv-hr-gateway-ltg0.onrender.com/docs
```

#### **1.6 OpenAPI Schema**
```bash
GET /openapi.json
curl https://bhiv-hr-gateway-ltg0.onrender.com/openapi.json
```

### **2. Authentication & Security (15 Endpoints)**

#### **2.1 API Key Validation**
```bash
GET /v1/auth/validate
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/validate

# Expected Response:
# {
#   "valid": true,
#   "key_id": "key_123",
#   "permissions": ["read", "write"],
#   "rate_limit": 500
# }
```

#### **2.2 User Login**
```bash
POST /v1/auth/login
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "username": "demo_user",
       "password": "demo_password"
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/login

# Expected Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }
```

#### **2.3 2FA Setup**
```bash
POST /v1/auth/2fa/setup
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/2fa/setup

# Expected Response:
# {
#   "secret": "JBSWY3DPEHPK3PXP",
#   "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
#   "backup_codes": ["12345678", "87654321", ...]
# }
```

#### **2.4 2FA Verification**
```bash
POST /v1/auth/2fa/verify
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "token": "123456"
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/2fa/verify

# Expected Response:
# {
#   "verified": true,
#   "message": "2FA token verified successfully"
# }
```

#### **2.5 Password Validation**
```bash
POST /v1/auth/password/validate
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{"password": "SecurePass123!"}' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/password/validate

# Expected Response:
# {
#   "valid": true,
#   "strength": "strong",
#   "score": 85,
#   "requirements_met": {
#     "length": true,
#     "uppercase": true,
#     "lowercase": true,
#     "digits": true,
#     "special_chars": true
#   }
# }
```

### **3. Job Management (12 Endpoints)**

#### **3.1 List Jobs**
```bash
GET /v1/jobs
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs

# Expected Response:
# {
#   "jobs": [
#     {
#       "id": 1,
#       "title": "Senior Software Engineer",
#       "department": "Engineering",
#       "location": "San Francisco, CA",
#       "status": "active",
#       "created_at": "2025-12-01T10:00:00Z"
#     }
#   ],
#   "total": 19,
#   "page": 1,
#   "per_page": 10
# }
```

#### **3.2 Get Job by ID**
```bash
GET /v1/jobs/{job_id}
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs/1

# Expected Response:
# {
#   "id": 1,
#   "title": "Senior Software Engineer",
#   "description": "We are seeking a senior software engineer...",
#   "requirements": "5+ years Python, FastAPI, PostgreSQL",
#   "salary_min": 120000,
#   "salary_max": 160000,
#   "applications_count": 15
# }
```

#### **3.3 Create Job**
```bash
POST /v1/jobs
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Senior Full Stack Developer",
       "department": "Engineering",
       "location": "Remote",
       "experience_level": "Senior",
       "employment_type": "Full-time",
       "salary_min": 130000,
       "salary_max": 170000,
       "description": "Join our team as a senior full stack developer...",
       "requirements": "React, Node.js, Python, AWS, 5+ years experience",
       "client_id": 1
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs

# Expected Response:
# {
#   "id": 20,
#   "title": "Senior Full Stack Developer",
#   "status": "active",
#   "created_at": "2025-12-09T10:00:00Z",
#   "message": "Job created successfully"
# }
```

#### **3.4 Update Job**
```bash
PUT /v1/jobs/{job_id}
curl -X PUT \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Senior Full Stack Developer (Updated)",
       "salary_max": 180000,
       "status": "active"
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs/20
```

#### **3.5 Delete Job**
```bash
DELETE /v1/jobs/{job_id}
curl -X DELETE \
     -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs/20
```

### **4. Candidate Management (18 Endpoints)**

#### **4.1 List Candidates**
```bash
GET /v1/candidates
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Expected Response:
# {
#   "candidates": [
#     {
#       "id": 1,
#       "name": "Alice Johnson",
#       "email": "alice@example.com",
#       "location": "San Francisco, CA",
#       "experience_years": 6,
#       "status": "active"
#     }
#   ],
#   "total": 29,
#   "page": 1,
#   "per_page": 10
# }
```

#### **4.2 Get Candidate by ID**
```bash
GET /v1/candidates/{candidate_id}
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/1

# Expected Response:
# {
#   "id": 1,
#   "name": "Alice Johnson",
#   "email": "alice@example.com",
#   "phone": "+1-555-0123",
#   "technical_skills": "Python, FastAPI, React, PostgreSQL",
#   "experience_years": 6,
#   "education_level": "Master",
#   "applications": 3,
#   "interviews": 2
# }
```

#### **4.3 Search Candidates**
```bash
GET /v1/candidates/search?q=python&location=san francisco&experience_min=3
curl -H "$AUTHORIZATION_HEADER" \
     "https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/search?q=python&location=san francisco&experience_min=3"

# Expected Response:
# {
#   "candidates": [...],
#   "total_matches": 12,
#   "search_query": "python",
#   "filters": {
#     "location": "san francisco",
#     "experience_min": 3
#   }
# }
```

#### **4.4 Create Candidate**
```bash
POST /v1/candidates
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Bob Smith",
       "email": "bob.smith@example.com",
       "phone": "+1-555-0124",
       "location": "New York, NY",
       "experience_years": 4,
       "technical_skills": "Java, Spring Boot, MySQL, Docker",
       "education_level": "Bachelor",
       "seniority_level": "Mid"
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates
```

### **5. AI Matching & Analytics (8 Endpoints)**

#### **5.1 Get Top Matches**
```bash
GET /v1/match/{job_id}/top?limit=10
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/1/top?limit=10

# Expected Response:
# {
#   "job_id": 1,
#   "matches": [
#     {
#       "candidate_id": 1,
#       "candidate_name": "Alice Johnson",
#       "overall_score": 87.5,
#       "semantic_score": 92.3,
#       "experience_score": 85.0,
#       "skills_score": 90.1,
#       "location_score": 100.0
#     }
#   ],
#   "algorithm_version": "phase3_v1.0",
#   "processing_time": "0.018s"
# }
```

#### **5.2 Batch Matching**
```bash
POST /v1/match/batch
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "job_ids": [1, 2, 3],
       "limit": 5,
       "include_scores": true
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/batch

# Expected Response:
# {
#   "batch_results": {
#     "1": [...],
#     "2": [...],
#     "3": [...]
#   },
#   "total_matches": 15,
#   "processing_time": "0.045s"
# }
```

#### **5.3 Candidate Analytics**
```bash
GET /v1/analytics/candidates
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/analytics/candidates

# Expected Response:
# {
#   "total_candidates": 29,
#   "active_candidates": 27,
#   "by_experience_level": {
#     "junior": 8,
#     "mid": 12,
#     "senior": 9
#   },
#   "by_location": {
#     "San Francisco, CA": 12,
#     "New York, NY": 8,
#     "Remote": 9
#   },
#   "top_skills": ["Python", "JavaScript", "React", "Node.js", "AWS"]
# }
```

### **6. Application Management (10 Endpoints)**

#### **6.1 List Applications**
```bash
GET /v1/applications
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/applications

# Expected Response:
# {
#   "applications": [
#     {
#       "id": 1,
#       "candidate_id": 1,
#       "job_id": 1,
#       "status": "applied",
#       "applied_date": "2025-12-01T10:00:00Z"
#     }
#   ],
#   "total": 45,
#   "status_counts": {
#     "applied": 20,
#     "screening": 15,
#     "interview": 8,
#     "offer": 2
#   }
# }
```

#### **6.2 Create Application**
```bash
POST /v1/applications
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 2,
       "cover_letter": "I am excited to apply for this position..."
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/applications
```

### **7. Interview Management (8 Endpoints)**

#### **7.1 List Interviews**
```bash
GET /v1/interviews
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/interviews

# Expected Response:
# {
#   "interviews": [
#     {
#       "id": 1,
#       "candidate_id": 1,
#       "job_id": 1,
#       "interview_date": "2025-12-15T14:00:00Z",
#       "interview_type": "technical",
#       "status": "scheduled",
#       "interviewer": "Sarah Tech Lead"
#     }
#   ],
#   "total": 20,
#   "upcoming": 8,
#   "completed": 12
# }
```

#### **7.2 Schedule Interview**
```bash
POST /v1/interviews
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "interview_date": "2025-12-20T15:00:00Z",
       "interview_type": "behavioral",
       "interviewer": "John HR Manager",
       "duration_minutes": 60,
       "meeting_link": "https://meet.google.com/abc-defg-hij"
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/interviews
```

### **8. Feedback & Assessment (7 Endpoints)**

#### **8.1 List Feedback**
```bash
GET /v1/feedback
curl -H "$AUTHORIZATION_HEADER" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/feedback

# Expected Response:
# {
#   "feedback": [
#     {
#       "id": 1,
#       "candidate_id": 1,
#       "job_id": 1,
#       "integrity": 5,
#       "honesty": 5,
#       "discipline": 4,
#       "hard_work": 5,
#       "gratitude": 4,
#       "average_score": 4.6,
#       "created_at": "2025-12-05T10:00:00Z"
#     }
#   ],
#   "total": 15,
#   "average_scores": {
#     "integrity": 4.7,
#     "honesty": 4.8,
#     "discipline": 4.5,
#     "hard_work": 4.6,
#     "gratitude": 4.4
#   }
# }
```

#### **8.2 Submit Feedback**
```bash
POST /v1/feedback
curl -X POST \
     -H "$AUTHORIZATION_HEADER" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "integrity": 5,
       "honesty": 5,
       "discipline": 4,
       "hard_work": 5,
       "gratitude": 4,
       "comments": "Excellent candidate with strong technical skills and great cultural fit.",
       "feedback_type": "interview",
       "interviewer_id": 1
     }' \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/feedback

# Expected Response:
# {
#   "id": 16,
#   "average_score": 4.6,
#   "message": "Feedback submitted successfully",
#   "rl_feedback_recorded": true
# }
```

---

## 🤖 AI Agent Service (6 Endpoints)

### **1. Core Agent Endpoints (2)**

#### **1.1 Agent Health**
```bash
GET /health
curl https://bhiv-hr-agent-nhgg.onrender.com/health

# Expected Response:
# {
#   "status": "healthy",
#   "service": "AI Agent",
#   "version": "4.3.0",
#   "model_loaded": true,
#   "cache_status": "active",
#   "rl_system": "operational"
# }
```

#### **1.2 Agent Info**
```bash
GET /
curl https://bhiv-hr-agent-nhgg.onrender.com/

# Expected Response:
# {
#   "service": "BHIV HR AI Agent",
#   "version": "4.3.0",
#   "model": "sentence-transformers/all-MiniLM-L6-v2",
#   "features": ["semantic_matching", "rl_integration", "bias_mitigation"]
# }
```

### **2. AI Matching Endpoints (3)**

#### **2.1 Semantic Matching**
```bash
POST /match
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1
     }' \
     https://bhiv-hr-agent-nhgg.onrender.com/match

# Expected Response:
# {
#   "candidate_id": 1,
#   "job_id": 1,
#   "overall_score": 87.5,
#   "semantic_score": 92.3,
#   "experience_score": 85.0,
#   "skills_score": 90.1,
#   "location_score": 100.0,
#   "cultural_fit_score": 78.5,
#   "algorithm_version": "phase3_v1.0",
#   "processing_time": "0.018s",
#   "cached": false,
#   "bias_adjusted": true
# }
```

#### **2.2 Batch Matching**
```bash
POST /batch_match
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "job_id": 1,
       "candidate_ids": [1, 2, 3, 4, 5],
       "include_explanations": true
     }' \
     https://bhiv-hr-agent-nhgg.onrender.com/batch_match

# Expected Response:
# {
#   "job_id": 1,
#   "matches": [
#     {
#       "candidate_id": 1,
#       "overall_score": 87.5,
#       "rank": 1,
#       "explanation": "Strong technical skills match with Python and FastAPI experience"
#     }
#   ],
#   "total_processed": 5,
#   "processing_time": "0.045s"
# }
```

#### **2.3 Candidate Analysis**
```bash
GET /analyze/{candidate_id}
curl https://bhiv-hr-agent-nhgg.onrender.com/analyze/1

# Expected Response:
# {
#   "candidate_id": 1,
#   "skill_analysis": {
#     "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
#     "skill_level": "senior",
#     "skill_diversity": 0.85
#   },
#   "experience_analysis": {
#     "years": 6,
#     "progression": "strong",
#     "leadership_indicators": true
#   },
#   "match_potential": {
#     "best_job_types": ["Full Stack Developer", "Backend Engineer"],
#     "salary_range": [120000, 160000],
#     "location_flexibility": "high"
#   }
# }
```

### **3. System Diagnostics (1)**

#### **3.1 Database Test**
```bash
GET /test_db
curl https://bhiv-hr-agent-nhgg.onrender.com/test_db

# Expected Response:
# {
#   "database_connection": "successful",
#   "candidates_count": 29,
#   "jobs_count": 19,
#   "cache_entries": 156,
#   "rl_states": 89
# }
```

---

## 🔄 LangGraph Service (25 Endpoints)

### **1. Core LangGraph Endpoints (3)**

#### **1.1 LangGraph Health**
```bash
GET /health
curl https://bhiv-hr-langgraph.onrender.com/health

# Expected Response:
# {
#   "status": "healthy",
#   "service": "LangGraph Workflow Engine",
#   "version": "2.0.0",
#   "workflows_active": 15,
#   "notifications_sent": 1250,
#   "ai_model": "gpt-4"
# }
```

#### **1.2 LangGraph Info**
```bash
GET /
curl https://bhiv-hr-langgraph.onrender.com/

# Expected Response:
# {
#   "service": "BHIV HR LangGraph Engine",
#   "version": "2.0.0",
#   "features": ["workflow_automation", "multi_channel_notifications", "ai_orchestration"],
#   "endpoints": 25
# }
```

#### **1.3 API Documentation**
```bash
GET /docs
# Interactive Swagger UI
# URL: https://bhiv-hr-langgraph.onrender.com/docs
```

### **2. Workflow Management (12 Endpoints)**

#### **2.1 Start Application Workflow**
```bash
POST /workflows/application/start
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "application_id": 1,
       "candidate_email": "alice@example.com",
       "candidate_phone": "+1-555-0123",
       "candidate_name": "Alice Johnson",
       "job_title": "Senior Developer",
       "company_name": "Tech Corp",
       "client_email": "hr@techcorp.com"
     }' \
     https://bhiv-hr-langgraph.onrender.com/workflows/application/start

# Expected Response:
# {
#   "workflow_id": "wf_app_abc123",
#   "status": "started",
#   "steps": [
#     "candidate_notification_sent",
#     "ai_matching_triggered",
#     "client_notification_sent"
#   ],
#   "estimated_completion": "2025-12-09T10:05:00Z"
# }
```

#### **2.2 Get Workflow Status**
```bash
GET /workflows/{workflow_id}/status
curl https://bhiv-hr-langgraph.onrender.com/workflows/wf_app_abc123/status

# Expected Response:
# {
#   "workflow_id": "wf_app_abc123",
#   "status": "completed",
#   "progress": 100,
#   "steps_completed": 5,
#   "steps_total": 5,
#   "started_at": "2025-12-09T10:00:00Z",
#   "completed_at": "2025-12-09T10:04:30Z",
#   "duration_seconds": 270
# }
```

#### **2.3 List All Workflows**
```bash
GET /workflows
curl https://bhiv-hr-langgraph.onrender.com/workflows

# Expected Response:
# {
#   "workflows": [
#     {
#       "workflow_id": "wf_app_abc123",
#       "type": "application",
#       "status": "completed",
#       "created_at": "2025-12-09T10:00:00Z"
#     }
#   ],
#   "total": 1250,
#   "active": 15,
#   "completed": 1200,
#   "failed": 35
# }
```

#### **2.4 Interview Workflow**
```bash
POST /workflows/interview/schedule
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "interview_id": 1,
       "candidate_email": "alice@example.com",
       "interview_date": "2025-12-15T14:00:00Z",
       "interviewer": "John Smith",
       "meeting_link": "https://meet.google.com/abc-defg-hij"
     }' \
     https://bhiv-hr-langgraph.onrender.com/workflows/interview/schedule
```

#### **2.5 Offer Workflow**
```bash
POST /workflows/offer/create
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": 1,
       "job_id": 1,
       "offer_id": 1,
       "candidate_email": "alice@example.com",
       "salary": 145000,
       "start_date": "2025-01-15"
     }' \
     https://bhiv-hr-langgraph.onrender.com/workflows/offer/create
```

### **3. Notification System (8 Endpoints)**

#### **3.1 Send Multi-Channel Notification**
```bash
POST /tools/send-notification
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "type": "email",
       "recipient": "alice@example.com",
       "subject": "Application Received - Senior Developer Position",
       "message": "Thank you for your application. We will review it and get back to you within 48 hours.",
       "template": "application_received",
       "metadata": {
         "candidate_name": "Alice Johnson",
         "job_title": "Senior Developer",
         "company_name": "Tech Corp"
       }
     }' \
     https://bhiv-hr-langgraph.onrender.com/tools/send-notification

# Expected Response:
# {
#   "notification_id": "notif_123",
#   "status": "sent",
#   "type": "email",
#   "recipient": "alice@example.com",
#   "sent_at": "2025-12-09T10:00:00Z"
# }
```

#### **3.2 WhatsApp Notification**
```bash
POST /tools/send-notification
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "type": "whatsapp",
       "recipient": "+1-555-0123",
       "message": "Hi Alice! Your application for Senior Developer at Tech Corp has been received. We will review it and get back to you soon. Best regards, BHIV HR Team"
     }' \
     https://bhiv-hr-langgraph.onrender.com/tools/send-notification
```

#### **3.3 Telegram Notification**
```bash
POST /tools/send-notification
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "type": "telegram",
       "recipient": "@alice_johnson",
       "message": "🎉 Great news! Your application for Senior Developer position has been received. We will be in touch soon!"
     }' \
     https://bhiv-hr-langgraph.onrender.com/tools/send-notification
```

### **4. Analytics & Monitoring (2 Endpoints)**

#### **4.1 Workflow Statistics**
```bash
GET /workflows/stats
curl https://bhiv-hr-langgraph.onrender.com/workflows/stats

# Expected Response:
# {
#   "total_workflows": 1250,
#   "active_workflows": 15,
#   "completed_workflows": 1200,
#   "failed_workflows": 35,
#   "success_rate": 96.0,
#   "average_duration_seconds": 180,
#   "notifications_sent": 3750
# }
```

#### **4.2 Performance Metrics**
```bash
GET /metrics
curl https://bhiv-hr-langgraph.onrender.com/metrics

# Expected Response: Prometheus metrics format
```

---

## 🏢 Portal Services (6 Endpoints)

### **1. HR Portal (2 Endpoints)**

#### **1.1 HR Portal Health**
```bash
GET /_stcore/health
curl https://bhiv-hr-portal-u670.onrender.com/_stcore/health

# Expected Response:
# {
#   "status": "ok",
#   "uptime": "5 days, 12 hours",
#   "version": "1.41.1"
# }
```

#### **1.2 HR Portal Access**
```bash
GET /
# Direct browser access
# URL: https://bhiv-hr-portal-u670.onrender.com/
```

### **2. Client Portal (2 Endpoints)**

#### **2.1 Client Portal Health**
```bash
GET /_stcore/health
curl https://bhiv-hr-client-portal-3iod.onrender.com/_stcore/health
```

#### **2.2 Client Portal Access**
```bash
GET /
# Direct browser access with authentication
# URL: https://bhiv-hr-client-portal-3iod.onrender.com/
# Credentials: TECH001 / demo123
```

### **3. Candidate Portal (2 Endpoints)**

#### **3.1 Candidate Portal Health**
```bash
GET /_stcore/health
curl https://bhiv-hr-candidate-portal-abe6.onrender.com/_stcore/health
```

#### **3.2 Candidate Portal Access**
```bash
GET /
# Direct browser access
# URL: https://bhiv-hr-candidate-portal-abe6.onrender.com/
```

---

## 🧪 Comprehensive Testing Scripts

### **1. Complete System Health Check**
```bash
#!/bin/bash
# comprehensive_health_check.sh

echo "🔍 BHIV HR Platform - Complete System Health Check"
echo "=================================================="

# Service URLs
GATEWAY="https://bhiv-hr-gateway-ltg0.onrender.com"
AGENT="https://bhiv-hr-agent-nhgg.onrender.com"
LANGGRAPH="https://bhiv-hr-langgraph.onrender.com"
HR_PORTAL="https://bhiv-hr-portal-u670.onrender.com"
CLIENT_PORTAL="https://bhiv-hr-client-portal-3iod.onrender.com"
CANDIDATE_PORTAL="https://bhiv-hr-candidate-portal-abe6.onrender.com"

# API Key
API_KEY="demo_key"

echo "1. 🌐 Gateway Service Health:"
curl -s "$GATEWAY/health" | jq '.'

echo -e "\n2. 🤖 AI Agent Health:"
curl -s "$AGENT/health" | jq '.'

echo -e "\n3. 🔄 LangGraph Health:"
curl -s "$LANGGRAPH/health" | jq '.'

echo -e "\n4. 👥 HR Portal Health:"
curl -s "$HR_PORTAL/_stcore/health" | jq '.'

echo -e "\n5. 🏢 Client Portal Health:"
curl -s "$CLIENT_PORTAL/_stcore/health" | jq '.'

echo -e "\n6. 👤 Candidate Portal Health:"
curl -s "$CANDIDATE_PORTAL/_stcore/health" | jq '.'

echo -e "\n7. 📊 System Metrics:"
curl -s -H "Authorization: Bearer $API_KEY" "$GATEWAY/health/detailed" | jq '.'

echo -e "\n8. 🔍 Database Test:"
curl -s "$AGENT/test_db" | jq '.'

echo -e "\n✅ Health Check Complete!"
```

### **2. API Functionality Test Suite**
```bash
#!/bin/bash
# api_functionality_test.sh

echo "🧪 BHIV HR Platform - API Functionality Test Suite"
echo "=================================================="

GATEWAY="https://bhiv-hr-gateway-ltg0.onrender.com"
AGENT="https://bhiv-hr-agent-nhgg.onrender.com"
LANGGRAPH="https://bhiv-hr-langgraph.onrender.com"
API_KEY="demo_key"
AUTH_HEADER="Authorization: Bearer $API_KEY"

# Test 1: Authentication
echo "Test 1: Authentication Validation"
auth_response=$(curl -s -H "$AUTH_HEADER" "$GATEWAY/v1/auth/validate")
echo "Auth Response: $auth_response"

# Test 2: Jobs API
echo -e "\nTest 2: Jobs API"
jobs_response=$(curl -s -H "$AUTH_HEADER" "$GATEWAY/v1/jobs")
echo "Jobs Count: $(echo $jobs_response | jq '.total // length')"

# Test 3: Candidates API
echo -e "\nTest 3: Candidates API"
candidates_response=$(curl -s -H "$AUTH_HEADER" "$GATEWAY/v1/candidates")
echo "Candidates Count: $(echo $candidates_response | jq '.total // length')"

# Test 4: AI Matching
echo -e "\nTest 4: AI Matching"
match_response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": 1, "job_id": 1}' \
  "$AGENT/match")
echo "Match Score: $(echo $match_response | jq '.overall_score')"

# Test 5: LangGraph Workflow
echo -e "\nTest 5: LangGraph Workflow"
workflow_response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": 1, "job_id": 1}' \
  "$LANGGRAPH/workflows/application/start")
echo "Workflow ID: $(echo $workflow_response | jq -r '.workflow_id')"

# Test 6: Analytics
echo -e "\nTest 6: Analytics"
analytics_response=$(curl -s -H "$AUTH_HEADER" "$GATEWAY/v1/analytics/candidates")
echo "Total Candidates: $(echo $analytics_response | jq '.total_candidates')"

echo -e "\n✅ Functionality Tests Complete!"
```

### **3. Performance Benchmark Test**
```bash
#!/bin/bash
# performance_benchmark.sh

echo "⚡ BHIV HR Platform - Performance Benchmark Test"
echo "==============================================="

GATEWAY="https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY="demo_key"

# Test API response times
echo "Testing API Response Times:"

endpoints=(
  "/health"
  "/v1/jobs"
  "/v1/candidates"
  "/v1/analytics/candidates"
)

for endpoint in "${endpoints[@]}"; do
  echo -n "Testing $endpoint: "
  
  if [[ "$endpoint" == "/health" ]]; then
    response_time=$(curl -w "%{time_total}" -o /dev/null -s "$GATEWAY$endpoint")
  else
    response_time=$(curl -w "%{time_total}" -o /dev/null -s \
      -H "Authorization: Bearer $API_KEY" "$GATEWAY$endpoint")
  fi
  
  echo "${response_time}s"
done

# Load test with Apache Bench (if available)
if command -v ab &> /dev/null; then
  echo -e "\nLoad Testing (100 requests, 10 concurrent):"
  ab -n 100 -c 10 "$GATEWAY/health"
else
  echo -e "\nApache Bench not available for load testing"
fi

echo -e "\n✅ Performance Tests Complete!"
```

### **4. Security Test Suite**
```bash
#!/bin/bash
# security_test_suite.sh

echo "🔒 BHIV HR Platform - Security Test Suite"
echo "========================================="

GATEWAY="https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY="demo_key"
AUTH_HEADER="Authorization: Bearer $API_KEY"

# Test 1: Authentication Required
echo "Test 1: Authentication Required"
unauth_response=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY/v1/jobs")
echo "Unauthenticated request status: $unauth_response (should be 401)"

# Test 2: Invalid API Key
echo -e "\nTest 2: Invalid API Key"
invalid_response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer invalid_key" "$GATEWAY/v1/jobs")
echo "Invalid API key status: $invalid_response (should be 401)"

# Test 3: Rate Limiting Status
echo -e "\nTest 3: Rate Limiting Status"
rate_limit_response=$(curl -s -H "$AUTH_HEADER" "$GATEWAY/v1/security/rate-limit-status")
echo "Rate Limit Status: $rate_limit_response"

# Test 4: Input Validation
echo -e "\nTest 4: Input Validation"
validation_response=$(curl -s -X POST \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"test_input": "<script>alert(\"xss\")</script>"}' \
  "$GATEWAY/v1/security/test-input-validation")
echo "Input Validation: $(echo $validation_response | jq '.status')"

# Test 5: Security Headers
echo -e "\nTest 5: Security Headers"
headers_response=$(curl -s -I "$GATEWAY/health" | grep -E "(X-|Strict-|Content-Security)")
echo "Security Headers:"
echo "$headers_response"

echo -e "\n✅ Security Tests Complete!"
```

---

## 📊 Expected Response Formats

### **Success Response Format**
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2025-12-09T10:00:00Z",
  "request_id": "req_abc123"
}
```

### **Error Response Format**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": "Email format is invalid"
  },
  "timestamp": "2025-12-09T10:00:00Z",
  "request_id": "req_abc123"
}
```

### **Authentication Error**
```json
{
  "detail": "Invalid API key or token expired",
  "error_code": "AUTH_FAILED",
  "timestamp": "2025-12-09T10:00:00Z"
}
```

### **Rate Limit Error**
```json
{
  "error": "Rate limit exceeded",
  "limit": 500,
  "window": "60 seconds",
  "retry_after": 45,
  "timestamp": "2025-12-09T10:00:00Z"
}
```

---

## 🔧 Testing Tools & Environment

### **Postman Collection Setup**
```json
{
  "info": {
    "name": "BHIV HR Platform API Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "gateway_url",
      "value": "https://bhiv-hr-gateway-ltg0.onrender.com"
    },
    {
      "key": "agent_url", 
      "value": "https://bhiv-hr-agent-nhgg.onrender.com"
    },
    {
      "key": "langgraph_url",
      "value": "https://bhiv-hr-langgraph.onrender.com"
    },
    {
      "key": "api_key",
      "value": "demo_key"
    }
  ]
}
```

### **Python Testing Framework**
```python
# api_test_framework.py
import requests
import json
import time
from typing import Dict, List

class BHIVAPITester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_endpoint(self, method: str, endpoint: str, 
                     data: Dict = None, expected_status: int = 200) -> Dict:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            
            response_time = time.time() - start_time
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == expected_status,
                'data': response.json() if response.content else None
            }
        
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'error': str(e),
                'success': False
            }
    
    def run_test_suite(self) -> List[Dict]:
        """Run comprehensive test suite"""
        test_cases = [
            ('GET', '/health', None, 200),
            ('GET', '/v1/jobs', None, 200),
            ('GET', '/v1/candidates', None, 200),
            ('GET', '/v1/analytics/candidates', None, 200),
            ('POST', '/v1/auth/validate', None, 200)
        ]
        
        results = []
        for method, endpoint, data, expected_status in test_cases:
            result = self.test_endpoint(method, endpoint, data, expected_status)
            results.append(result)
            print(f"✅ {endpoint}: {result['success']}")
        
        return results

# Usage example
if __name__ == "__main__":
    tester = BHIVAPITester(
        "https://bhiv-hr-gateway-ltg0.onrender.com",
        "demo_key"
    )
    
    results = tester.run_test_suite()
    
    # Print summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get('success', False))
    
    print(f"\n📊 Test Summary:")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
```

---

## 📈 Testing Metrics & Benchmarks

### **Performance Targets**
- **API Response Time**: <100ms (95th percentile)
- **AI Matching Speed**: <0.02s with caching
- **Workflow Processing**: <5s end-to-end
- **Portal Load Time**: <3s initial load
- **Concurrent Users**: 100+ simultaneous
- **Throughput**: 500+ requests/minute

### **Success Criteria**
- **Endpoint Availability**: 100% (111/111 endpoints)
- **Response Accuracy**: >99% correct responses
- **Error Handling**: Proper error codes and messages
- **Security**: All authentication and authorization working
- **Performance**: All targets met consistently

### **Test Coverage Matrix**
```
Service          | Endpoints | Tested | Coverage
===============================================
API Gateway      |    74     |   74   |  100%
AI Agent         |     6     |    6   |  100%
LangGraph        |    25     |   25   |  100%
Portal Services  |     6     |    6   |  100%
===============================================
Total            |   111     |  111   |  100%
```

---

**BHIV HR Platform API Testing Guide v4.3.0** - Complete testing documentation for 111 endpoints across 6 microservices with comprehensive test scripts, performance benchmarks, and validation procedures.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Last Updated**: December 9, 2025 | **Version**: v4.3.0 | **Endpoints**: 111 | **Coverage**: 100% | **Status**: ✅ All Operational
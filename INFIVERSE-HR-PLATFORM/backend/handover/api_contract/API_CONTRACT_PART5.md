# API Contract — Part 5: AI Agent & LangGraph Services (86-111 of 111)

**Continued from:** [API_CONTRACT_PART4.md](./API_CONTRACT_PART4.md)

**Version:** 4.1.0  
**Last Updated:** January 22, 2026  
**Total Endpoints:** 111 (80 Gateway + 6 Agent + 25 LangGraph)  
**Database:** MongoDB Atlas  
**Analysis Source:** Comprehensive endpoint analysis from services directories

---

## AI Agent Service (Port 9000)
**Total Endpoints:** 6  
**Base URL:** http://localhost:9000 (Local) | https://bhiv-hr-agent-nhgg.onrender.com (Production)

### 81. GET /

**Purpose:** AI Agent service information

**Authentication:** None (public endpoint)

**Implementation:** `services/agent/app.py` → `read_root()`

**Timeout:** 2s

**Request:**
```http
GET /
```

**Response (200 OK):**
```json
{
  "service": "BHIV AI Agent",
  "version": "3.0.0",
  "endpoints": 6,
  "available_endpoints": {
    "root": "GET / - Service information",
    "health": "GET /health - Service health check",
    "test_db": "GET /test-db - Database connectivity test",
    "match": "POST /match - AI-powered candidate matching",
    "batch_match": "POST /batch-match - Batch AI matching for multiple jobs",
    "analyze": "GET /analyze/{candidate_id} - Detailed candidate analysis"
  }
}
```

**When Called:** Service discovery

**Database Impact:** None (static response)

---

### 82. GET /health

**Purpose:** Health check for AI Agent service

**Authentication:** None (public health endpoint)

**Implementation:** `services/agent/app.py` → `health_check()`

**Timeout:** 5s

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "BHIV AI Agent",
  "version": "3.0.0",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**When Called:** Load balancer health checks

**Database Impact:** None (static response)

---

### 83. GET /test-db

**Purpose:** Test database connectivity

**Authentication:** Bearer token required

**Implementation:** `services/agent/app.py` → `test_database()`

**Timeout:** 10s

**Request:**
```http
GET /test-db
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "status": "success",
  "candidates_count": 1234,
  "samples": [
    {"id": 1, "name": "John Doe"},
    {"id": 2, "name": "Jane Smith"},
    {"id": 3, "name": "Bob Johnson"}
  ]
}
```

**Error Responses:**
- 500 Internal Server Error: Database connection failed

**When Called:** System diagnostics

**Database Impact:** COUNT from candidates collection

---

### 84. POST /match

**Purpose:** AI-powered candidate matching using Phase 3 semantic engine

**Authentication:** Bearer token required

**Implementation:** `services/agent/app.py` → `match_candidates()`

**Timeout:** 60s

**Request:**
```http
POST /match
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "job_id": 123
}
```

**Response (200 OK):**
```json
{
  "job_id": 123,
  "top_candidates": [
    {
      "candidate_id": 45,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "score": 92.5,
      "skills_match": ["Python", "FastAPI", "PostgreSQL"],
      "experience_match": "5y - Phase 3 matched",
      "location_match": true,
      "reasoning": "Semantic match: 0.95; Skills: Python, FastAPI, PostgreSQL; Experience: 5y; Location: San Francisco"
    }
  ],
  "total_candidates": 50,
  "processing_time": 0.45,
  "algorithm_version": "3.0.0-phase3-production",
  "status": "success"
}
```

**Sequence:**
1. Fetch job details from database
2. Fetch all candidates
3. Run Phase 3 semantic matching
4. Calculate similarity scores
5. Rank candidates by score
6. Return top 10 matches

**Error Responses:**
- 404 Not Found: Job not found
- 500 Internal Server Error: Matching failed

**When Called:** Gateway requests AI matching

**Database Impact:** SELECT from jobs, candidates collections

---

### 85. POST /batch-match

**Purpose:** Batch AI matching for multiple jobs

**Authentication:** Bearer token required

**Implementation:** `services/agent/app.py` → `batch_match_jobs()`

**Timeout:** 120s

**Request:**
```http
POST /batch-match
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
          "skills_match": ["Python", "FastAPI"],
          "experience_match": "5y - Phase 3 matched",
          "location_match": true,
          "reasoning": "Skills: Python, FastAPI; Experience: 5y; Phase 3 AI semantic analysis"
        }
      ],
      "total_candidates": 5,
      "algorithm": "batch-production",
      "processing_time": "0.5s"
    }
  },
  "total_jobs_processed": 3,
  "total_candidates_analyzed": 50,
  "algorithm_version": "3.0.0-phase3-production-batch",
  "status": "success",
  "processing_time": "1.2s"
}
```

**Error Responses:**
- 400 Bad Request: Empty job_ids or > 10 jobs
- 404 Not Found: Jobs not found

**When Called:** Gateway requests batch matching

**Database Impact:** SELECT from jobs, candidates collections

---

### 86. GET /analyze/{candidate_id}

**Purpose:** Detailed candidate analysis with skill categorization

**Authentication:** Bearer token required

**Implementation:** `services/agent/app.py` → `analyze_candidate()`

**Timeout:** 60s

**Request:**
```http
GET /analyze/123
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "candidate_id": 123,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "experience_years": 5,
  "seniority_level": "Senior",
  "education_level": "Bachelor of Science in Computer Science",
  "location": "San Francisco, CA",
  "skills_analysis": {
    "Programming": ["python", "java", "javascript"],
    "Web Development": ["react", "node", "django"],
    "Cloud": ["aws", "docker", "kubernetes"],
    "Database": ["sql", "postgresql", "mongodb"]
  },
  "semantic_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
  "total_skills": 10,
  "ai_analysis_enabled": true,
  "analysis_timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 404 Not Found: Candidate not found

**When Called:** HR requests detailed candidate analysis

**Database Impact:** SELECT from candidates collection

---

## LangGraph Service (Port 9001)
**Total Endpoints:** 25  
**Base URL:** http://localhost:9001 (Local) | https://bhiv-hr-langgraph.onrender.com (Production)

**RL Integration Status:** ✅ 8 RL endpoints operational with 100% test pass rate

### 87. GET /

**Purpose:** LangGraph service information

**Authentication:** None (public endpoint)

**Implementation:** `services/langgraph/app/main.py` → `read_root()`

**Timeout:** 2s

**Request:**
```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "BHIV LangGraph Orchestrator",
  "version": "1.0.0",
  "status": "healthy",
  "environment": "production",
  "endpoints": 25,
  "workflow_engine": "active",
  "ai_automation": "enabled"
}
```

**When Called:** Service discovery

**Database Impact:** None (static response)

---

### 88. GET /health

**Purpose:** Health check for LangGraph service

**Authentication:** None (public health endpoint)

**Implementation:** `services/langgraph/app/main.py` → `health_check()`

**Timeout:** 5s

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "langgraph-orchestrator",
  "version": "1.0.0",
  "environment": "production"
}
```

**When Called:** Load balancer health checks

**Database Impact:** None (static response)

---

### 89. POST /workflows/application/start

**Purpose:** Start AI workflow for candidate processing

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `start_application_workflow()`

**Timeout:** 10s

**Request:**
```http
POST /workflows/application/start
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
  "job_description": "Build scalable HR solutions"
}
```

**Response (200 OK):**
```json
{
  "workflow_id": "wf_abc123def456",
  "status": "started",
  "message": "Application workflow started for John Doe",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Sequence:**
1. Generate unique workflow_id
2. Initialize workflow state
3. Execute workflow in background
4. Track in database
5. Return workflow_id for tracking

**Error Responses:**
- 500 Internal Server Error: Workflow initialization failed

**When Called:** Candidate submits application

**Database Impact:** INSERT into workflows collection

---

### 90. GET /workflows/{workflow_id}/status

**Purpose:** Get detailed workflow execution status

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `get_workflow_status()`

**Timeout:** 15s

**Request:**
```http
GET /workflows/wf_abc123def456/status
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "workflow_id": "wf_abc123def456",
  "workflow_type": "candidate_application",
  "status": "running",
  "progress_percentage": 65,
  "current_step": "ai_matching_analysis",
  "total_steps": 5,
  "candidate_id": 123,
  "job_id": 45,
  "input_data": {
    "candidate_name": "John Doe",
    "job_title": "Senior Software Engineer"
  },
  "output_data": {},
  "error_message": null,
  "started_at": "2026-01-22T13:37:00Z",
  "completed_at": null,
  "updated_at": "2026-01-22T13:40:00Z",
  "completed": false,
  "estimated_time_remaining": "2-4 minutes",
  "source": "database"
}
```

**Error Responses:**
- 404 Not Found: Workflow not found

**When Called:** Dashboard polls for workflow updates

**Database Impact:** SELECT from workflows collection

---

### 91. POST /workflows/{workflow_id}/resume

**Purpose:** Resume paused workflow

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `resume_workflow()`

**Timeout:** 10s

**Request:**
```http
POST /workflows/wf_abc123def456/resume
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "workflow_id": "wf_abc123def456",
  "status": "resumed",
  "result": {}
}
```

**When Called:** Admin resumes paused workflow

**Database Impact:** UPDATE workflows collection

---

### 92. GET /workflows

**Purpose:** List all workflows with filtering

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `list_workflows()`

**Timeout:** 20s

**Request:**
```http
GET /workflows?status=running&limit=50
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
      "progress_percentage": 65,
      "candidate_id": 123,
      "job_id": 45,
      "started_at": "2026-01-22T13:37:00Z",
      "completed": false,
      "estimated_time_remaining": "2-4 minutes"
    }
  ],
  "count": 1,
  "filter": "running",
  "limit": 50,
  "tracking_source": "database_with_fallback",
  "status": "operational"
}
```

**When Called:** Dashboard loads workflow list

**Database Impact:** SELECT from workflows collection

---

### 93. GET /workflows/stats

**Purpose:** Workflow statistics and analytics

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `get_workflow_stats()`

**Timeout:** 20s

**Request:**
```http
GET /workflows/stats
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "total_workflows": 1234,
  "active_workflows": 5,
  "completed_workflows": 1200,
  "failed_workflows": 29,
  "average_completion_time": "3-5 minutes",
  "success_rate": "97.2%",
  "database_connection": "connected",
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**When Called:** Admin dashboard loads workflow metrics

**Database Impact:** Multiple COUNT queries on workflows collection

---

### 94. POST /tools/send-notification

**Purpose:** Multi-channel notification system with interactive features

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_notification()`

**Timeout:** 30s

**Request:**
```http
POST /tools/send-notification
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_name": "John Doe",
  "candidate_email": "john.doe@example.com",
  "candidate_phone": "+1234567890",
  "job_title": "Senior Software Engineer",
  "message": "Your application has been received",
  "channels": ["email", "whatsapp"],
  "application_status": "received"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Automated notification sequence completed",
  "candidate_name": "John Doe",
  "job_title": "Senior Software Engineer",
  "sequence_type": "application_received",
  "channels_requested": ["email", "whatsapp"],
  "results": {
    "email": {"sent": true, "message_id": "msg_abc123"},
    "whatsapp": {"sent": true, "message_sid": "SM123"}
  },
  "sent_at": "2026-01-22T13:37:00Z"
}
```

**When Called:** Workflow triggers notification

**Database Impact:** INSERT into notification logs

---

### 95. POST /test/send-email

**Purpose:** Send test email via SMTP or email service provider

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_test_email()`

**Timeout:** 30s

**Request:**
```http
POST /test/send-email
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "to_email": "test@example.com",
  "subject": "Test Email Subject",
  "body": "This is a test email body",
  "from_name": "BHIV HR System",
  "template_id": "welcome_template"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "sent": true,
    "message_id": "msg_abc123",
    "provider": "smtp",
    "delivery_status": "queued"
  },
  "sent_at": "2026-01-22T13:37:00Z",
  "recipient": "test@example.com"
}
```

**Error Responses:**
- 400 Bad Request: Invalid email format
- 401 Unauthorized: Invalid API key

**When Called:** Testing email service configuration

**Database Impact:** INSERT into email_logs collection

---

### 96. POST /test/send-whatsapp

**Purpose:** Send test WhatsApp message via WhatsApp Business API

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_test_whatsapp()`

**Timeout:** 30s

**Request:**
```http
POST /test/send-whatsapp
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "to_phone": "+1234567890",
  "message": "This is a test WhatsApp message",
  "message_type": "text",
  "template_name": "generic_template"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "sent": true,
    "message_sid": "SM123456789",
    "provider": "twilio",
    "delivery_status": "sent"
  },
  "sent_at": "2026-01-22T13:37:00Z",
  "recipient": "+1234567890"
}
```

**Error Responses:**
- 400 Bad Request: Invalid phone format
- 401 Unauthorized: Invalid API key

**When Called:** Testing WhatsApp messaging service

**Database Impact:** INSERT into whatsapp_logs collection

---

### 97. POST /test/send-telegram

**Purpose:** Send test Telegram message via Bot API

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_test_telegram()`

**Timeout:** 30s

**Request:**
```http
POST /test/send-telegram
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "chat_id": "123456789",
  "message": "This is a test Telegram message",
  "parse_mode": "markdown"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "sent": true,
    "message_id": 12345,
    "provider": "telegram_bot_api",
    "delivery_status": "delivered"
  },
  "sent_at": "2026-01-22T13:37:00Z",
  "chat_id": "123456789"
}
```

**Error Responses:**
- 400 Bad Request: Invalid chat ID
- 401 Unauthorized: Invalid API key

**When Called:** Testing Telegram messaging service

**Database Impact:** INSERT into telegram_logs collection

---

### 98. POST /test/send-whatsapp-buttons

**Purpose:** Send WhatsApp message with interactive buttons

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_test_whatsapp_buttons()`

**Timeout:** 30s

**Request:**
```http
POST /test/send-whatsapp-buttons
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "to_phone": "+1234567890",
  "message": "Please select an option:",
  "buttons": [
    {"id": "accept", "title": "Accept"},
    {"id": "decline", "title": "Decline"},
    {"id": "later", "title": "Remind Later"}
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "sent": true,
    "message_sid": "SM987654321",
    "provider": "twilio",
    "delivery_status": "sent",
    "interactive_elements": true
  },
  "sent_at": "2026-01-22T13:37:00Z",
  "recipient": "+1234567890"
}
```

**Error Responses:**
- 400 Bad Request: Invalid phone format or button configuration
- 401 Unauthorized: Invalid API key

**When Called:** Testing WhatsApp interactive features

**Database Impact:** INSERT into whatsapp_logs collection

---

### 99. POST /test/send-automated-sequence

**Purpose:** Send automated sequence of notifications across multiple channels

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_test_automated_sequence()`

**Timeout:** 60s

**Request:**
```http
POST /test/send-automated-sequence
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "recipient": {
    "email": "test@example.com",
    "phone": "+1234567890",
    "chat_id": "123456789"
  },
  "sequence": [
    {"type": "email", "delay_minutes": 0, "template": "initial_notification"},
    {"type": "whatsapp", "delay_minutes": 5, "template": "followup_reminder"},
    {"type": "telegram", "delay_minutes": 10, "template": "final_reminder"}
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "sequence_id": "seq_abc123",
  "status": "initiated",
  "total_messages": 3,
  "channels": ["email", "whatsapp", "telegram"],
  "scheduled_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid recipient or sequence configuration
- 401 Unauthorized: Invalid API key

**When Called:** Testing automated notification sequences

**Database Impact:** INSERT into notification_sequences collection

---

### 100. POST /automation/trigger-workflow

**Purpose:** Trigger automated workflow with notification sequence

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `trigger_workflow_automation()`

**Timeout:** 30s

**Request:**
```http
POST /automation/trigger-workflow
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "workflow_type": "candidate_application",
  "trigger_data": {
    "candidate_id": 123,
    "job_id": 45,
    "candidate_email": "john.doe@example.com",
    "candidate_name": "John Doe",
    "job_title": "Senior Developer"
  },
  "notification_channels": ["email", "whatsapp"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "workflow_id": "wf_def456",
  "status": "triggered",
  "triggered_at": "2026-01-22T13:37:00Z",
  "notification_channels": ["email", "whatsapp"],
  "workflow_type": "candidate_application"
}
```

**Error Responses:**
- 400 Bad Request: Invalid workflow type or data
- 401 Unauthorized: Invalid API key

**When Called:** Triggering automated workflows

**Database Impact:** INSERT into workflows and notification_logs collections

---

### 101. POST /automation/bulk-notifications

**Purpose:** Send bulk notifications to multiple recipients

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `send_bulk_notifications()`

**Timeout:** 120s

**Request:**
```http
POST /automation/bulk-notifications
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "recipients": [
    {"email": "test1@example.com", "phone": "+1234567890"},
    {"email": "test2@example.com", "phone": "+0987654321"}
  ],
  "message_template": "Your application status has been updated",
  "channels": ["email", "whatsapp"],
  "priority": "normal"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "total_recipients": 2,
  "sent_count": 2,
  "failed_count": 0,
  "batch_id": "batch_xyz789",
  "status": "processing",
  "estimated_completion": "2026-01-22T13:40:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid recipients or message format
- 401 Unauthorized: Invalid API key

**When Called:** Sending bulk notifications

**Database Impact:** INSERT into bulk_notification_logs collection

---

### 102. POST /webhook/whatsapp

**Purpose:** Handle incoming WhatsApp webhook events

**Authentication:** Bearer token required (or WhatsApp signature verification)

**Implementation:** `services/langgraph/app/main.py` → `handle_whatsapp_webhook()`

**Timeout:** 30s

**Request:**
```http
POST /webhook/whatsapp
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "123456789",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "+1234567890",
              "phone_number_id": "0987654321"
            },
            "contacts": [
              {
                "profile": {
                  "name": "John Doe"
                },
                "wa_id": "+1234567890"
              }
            ],
            "messages": [
              {
                "from": "+1234567890",
                "id": "wamid.HBgLMTIzNDU2Nzg5MBUCAREY",
                "timestamp": "1684123456",
                "text": {
                  "body": "Hello, I'm interested in the position."
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "event_handled": true,
  "event_type": "message_received",
  "sender_id": "+1234567890",
  "message_id": "wamid.HBgLMTIzNDU2Nzg5MBUCAREY",
  "processed_at": "2026-01-22T13:37:00Z",
  "action_taken": "stored_for_processing"
}
```

**Error Responses:**
- 400 Bad Request: Invalid webhook payload
- 401 Unauthorized: Invalid signature or API key

**When Called:** WhatsApp Business API sends webhook events

**Database Impact:** INSERT into whatsapp_webhook_events collection

---

### 103. POST /rl/predict

**Purpose:** Make Reinforcement Learning-based prediction for candidate-job matching

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_predict()`

**Timeout:** 30s

**Request:**
```http
POST /rl/predict
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "candidate_features": {
    "experience_years": 5,
    "technical_skills": ["Python", "FastAPI", "MongoDB"],
    "soft_skills": ["communication", "leadership"],
    "education_level": "bachelor",
    "location_match": true
  },
  "job_features": {
    "experience_required": 5,
    "required_skills": ["Python", "FastAPI"],
    "preferred_skills": ["MongoDB"],
    "location": "remote",
    "job_type": "full-time"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "prediction_id": "pred_rl_12345",
    "rl_prediction": {
      "rl_score": 87.5,
      "confidence_level": 0.92,
      "decision_type": "recommend",
      "model_version": "v1.0.0"
    },
    "feedback_samples_used": 150,
    "feature_importance": {
      "technical_skills": 0.65,
      "experience_match": 0.25,
      "location_match": 0.10
    }
  },
  "message": "RL prediction completed successfully",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid feature format
- 401 Unauthorized: Invalid API key

**When Called:** AI matching requests RL enhancement

**Database Impact:** INSERT into rl_predictions collection

---

### 104. POST /rl/feedback

**Purpose:** Submit feedback for Reinforcement Learning model improvement

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_submit_feedback()`

**Timeout:** 20s

**Request:**
```http
POST /rl/feedback
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "prediction_id": "pred_rl_12345",
  "candidate_id": 123,
  "job_id": 45,
  "actual_outcome": "hired",
  "feedback_score": 0.9,
  "feedback_source": "hr_manager",
  "feedback_notes": "Excellent candidate, great cultural fit"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "feedback_id": "fb_rl_67890",
    "reward_signal": 0.85,
    "processed_feedback": {
      "actual_outcome": "hired",
      "feedback_score": 0.9,
      "reward_signal": 0.85
    }
  },
  "message": "RL feedback submitted successfully",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid feedback format
- 401 Unauthorized: Invalid API key
- 404 Not Found: Prediction not found

**When Called:** HR provides feedback on matching predictions

**Database Impact:** INSERT into rl_feedback collection

---

### 105. GET /rl/analytics

**Purpose:** Get Reinforcement Learning system analytics and performance metrics

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_get_analytics()`

**Timeout:** 25s

**Request:**
```http
GET /rl/analytics
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "rl_analytics": {
      "total_predictions": 1250,
      "total_feedback": 890,
      "average_accuracy": 0.87,
      "model_performance": {
        "precision": 0.85,
        "recall": 0.82,
        "f1_score": 0.83
      },
      "feedback_rate": 0.71,
      "active_models": ["v1.0.0"],
      "last_training": "2026-01-20T10:00:00Z"
    },
    "system_status": "operational"
  },
  "message": "RL analytics retrieved successfully",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Dashboard analytics, system performance monitoring

**Database Impact:** Aggregation queries on rl_predictions and rl_feedback collections

---

### 106. GET /rl/performance/{model_version}

**Purpose:** Get specific model version performance metrics

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_get_performance_by_version()`

**Timeout:** 20s

**Request:**
```http
GET /rl/performance/v1.0.0
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "model_version": "v1.0.0",
    "performance_metrics": {
      "accuracy": 0.87,
      "precision": 0.85,
      "recall": 0.82,
      "f1_score": 0.83,
      "predictions_made": 1250,
      "feedback_received": 890,
      "average_confidence": 0.88
    },
    "training_data_size": 10000,
    "features_used": 15,
    "model_status": "active"
  },
  "message": "Model performance retrieved successfully",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key
- 404 Not Found: Model version not found

**When Called:** Model performance evaluation

**Database Impact:** SELECT from rl_model_performance collection

---

### 107. GET /rl/history/{candidate_id}

**Purpose:** Get Reinforcement Learning decision history for a candidate

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_get_history()`

**Timeout:** 15s

**Request:**
```http
GET /rl/history/123
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "candidate_id": 123,
    "decision_history": [
      {
        "prediction_id": "pred_rl_101",
        "job_id": 45,
        "job_title": "Senior Developer",
        "rl_score": 0.87,
        "confidence": 0.92,
        "prediction_date": "2026-01-20T10:00:00Z",
        "actual_outcome": "hired",
        "feedback_provided": true
      }
    ],
    "total_decisions": 3,
    "positive_outcomes": 2,
    "negative_outcomes": 1
  },
  "message": "RL history retrieved successfully",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key
- 404 Not Found: Candidate not found

**When Called:** Reviewing candidate's matching history

**Database Impact:** SELECT from rl_predictions collection

---

### 108. POST /rl/retrain

**Purpose:** Trigger Reinforcement Learning model retraining

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_trigger_retrain()`

**Timeout:** 300s (5 minutes)

**Request:**
```http
POST /rl/retrain
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "model_version": "v1.0.1",
  "training_data_filters": {
    "date_range": {"start": "2026-01-01", "end": "2026-01-22"},
    "minimum_feedback": 10
  },
  "hyperparameters": {
    "learning_rate": 0.001,
    "epochs": 50,
    "batch_size": 32
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "retrain_job_id": "rt_98765",
    "status": "initiated",
    "model_version": "v1.0.1",
    "estimated_duration": "300s",
    "training_samples": 150,
    "feedback_samples": 89
  },
  "message": "Model retraining initiated",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid training parameters
- 401 Unauthorized: Invalid API key

**When Called:** Scheduled model retraining or manual trigger

**Database Impact:** INSERT into rl_retrain_jobs collection

---

### 109. GET /rl/performance

**Purpose:** Get overall Reinforcement Learning system performance

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_get_performance()`

**Timeout:** 20s

**Request:**
```http
GET /rl/performance
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "current_metrics": {
    "total_predictions": 1250,
    "accuracy": 0.87,
    "model_version": "v1.0.0",
    "feedback_rate": 0.71,
    "active_learning_cycles": 5,
    "improvement_since_deploy": 0.12
  },
  "monitoring_status": "active",
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Performance monitoring, model evaluation

**Database Impact:** Aggregation queries on rl_predictions and rl_feedback collections

---

### 110. POST /rl/start-monitoring

**Purpose:** Start Reinforcement Learning system monitoring

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/rl_integration/rl_endpoints.py` → `rl_start_monitoring()`

**Timeout:** 10s

**Request:**
```http
POST /rl/start-monitoring
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "monitoring_config": {
    "metrics": ["accuracy", "latency", "feedback_rate"],
    "frequency": "5min",
    "alert_thresholds": {
      "accuracy_drop": 0.05,
      "latency_increase": 2.0
    }
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "monitoring_id": "mon_rl_11223",
    "status": "active",
    "config": {
      "metrics": ["accuracy", "latency", "feedback_rate"],
      "frequency": "5min",
      "alerts_enabled": true
    }
  },
  "message": "RL monitoring started",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid monitoring configuration
- 401 Unauthorized: Invalid API key

**When Called:** Starting RL system monitoring

**Database Impact:** INSERT into rl_monitoring_sessions collection

---

### 111. GET /test-integration

**Purpose:** Integration testing and system validation

**Authentication:** Bearer token required

**Implementation:** `services/langgraph/app/main.py` → `test_integration()`

**Timeout:** 30s

**Request:**
```http
GET /test-integration
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "service": "langgraph-orchestrator",
  "status": "operational",
  "integration_test": "passed",
  "endpoints_available": 25,
  "workflow_engine": "active",
  "rl_engine": "integrated",
  "rl_database": "mongodb",
  "rl_monitoring": "available",
  "database_tracking": "enabled",
  "progress_tracking": "detailed",
  "fallback_support": "enabled",
  "tested_at": "2026-01-22T13:37:00Z"
}
```

**When Called:** System diagnostics, deployment verification

**Database Impact:** Health checks across all integrated services

---

## Summary Table - Part 5

### AI Agent Service (6 endpoints)

| Endpoint | Method | Purpose | Auth Required | Timeout |
|----------|--------|---------|---------------|---------|
| / | GET | Service info | No | 2s |
| /health | GET | Health check | No | 5s |
| /test-db | GET | Test database | Yes | 10s |
| /match | POST | AI matching | Yes | 60s |
| /batch-match | POST | Batch matching | Yes | 120s |
| /analyze/{candidate_id} | GET | Candidate analysis | Yes | 60s |

### LangGraph Service (25 endpoints)

| Category | Endpoints | Auth Required | Timeout |
|----------|-----------|---------------|---------|
| Core API | 2 (/, /health) | No | 2-5s |
| Workflow Management | 2 (start, resume) | Yes | 10s |
| Workflow Monitoring | 3 (status, list, stats) | Yes | 15-20s |
| Communication Tools | 8 (notifications, webhooks) | Yes | 10-30s |
| RL + Feedback Agent | 8 (predict, feedback, analytics) - 100% operational | Yes | 10-30s |
| System Diagnostics | 1 (test-integration) | Yes | 30s |

**Total Endpoints in Part 5:** 31 (81-111 of 111)

---

## 🎉 Complete API Documentation

**Total Endpoints Documented:** 111 of 111 (100%)

### Service Breakdown
- **Gateway API:** 80 endpoints
- **AI Agent API:** 6 endpoints
- **LangGraph API:** 25 endpoints (17 workflow + 8 RL)

### Documentation Parts
- ✅ Part 1: Core Services (17 endpoints)
- ✅ Part 2: Gateway Core Features (18 endpoints)
- ✅ Part 3: Gateway Advanced Features (10 endpoints)
- ✅ Part 4: Gateway Security & Portals (35 endpoints)
- ✅ Part 5: AI Agent & LangGraph Services (31 endpoints)

---

**Back to:** [API_CONTRACT_SUMMARY.md](./API_CONTRACT_SUMMARY.md) for complete overview
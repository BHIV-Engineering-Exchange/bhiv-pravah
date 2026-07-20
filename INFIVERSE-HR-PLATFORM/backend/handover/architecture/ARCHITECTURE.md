# BHIV HR Platform — System Architecture

**Version:** 3.0.0  
**Last Updated:** December 2024  
**Status:** Production Ready

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BHIV HR PLATFORM                                 │
│                    Enterprise AI-Powered Recruiting                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
            │  HR Portal   │ │Client Portal│ │Cand Portal │
            │  (Streamlit) │ │ (Streamlit) │ │(Streamlit) │
            └───────┬──────┘ └─────┬──────┘ └─────┬──────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      API Gateway (FastAPI)     │
                    │  • Authentication (Triple)     │
                    │  • Rate Limiting (Dynamic)     │
                    │  • 80 Endpoints                │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
    ┌───────▼──────┐      ┌────────▼────────┐    ┌───────▼──────┐
    │  AI Agent    │      │   LangGraph     │    │  Database    │
    │  (FastAPI)   │      │  Orchestrator   │    │ MongoDB Atlas│
    │  • Phase 3   │      │  • Workflows    │    │  • 14 Tables │
    │  • Semantic  │      │  • RL Engine    │    │  • 4 RL Tabs │
    │  • 6 Endpts  │      │  • 25 Endpoints │    │  • Schema v4 │
    └──────────────┘      └─────────────────┘    └──────────────┘
```

### Architecture Type
- **Pattern:** Microservices Architecture
- **Communication:** REST APIs + Event-Driven
- **Deployment:** Docker Containers on Render
- **Database:** MongoDB Atlas
- **Total Services:** 6 (3 Portals + 3 Backend Services)
- **Total Endpoints:** 111 (80 Gateway + 6 Agent + 25 LangGraph)

---

## 2. Core Modules

### 2.1 API Gateway Module
**Purpose:** Central entry point for all API requests with authentication and routing

**Key Files:**
- `services/gateway/app/main.py` - Main FastAPI application
- `services/gateway/routes/` - Endpoint route handlers (auth.py, ai_integration.py, rl_routes.py)
- `services/gateway/config.py` - Configuration management
- `services/gateway/monitoring.py` - Prometheus metrics
- `services/gateway/dependencies.py` - Dependency injection
- `services/gateway/langgraph_integration.py` - LangGraph integration
- `services/gateway/Dockerfile` - Container configuration
- `services/gateway/requirements.txt` - Python dependencies

**Endpoints:** 80 total
- Authentication: 4 endpoints
- AI Integration: 2 endpoints
- LangGraph Workflows: 7 endpoints
- RL + Feedback Agent: 4 endpoints
- Monitoring: 3 endpoints
- Core API: 5 endpoints
- Job Management: 2 endpoints
- Candidate Management: 5 endpoints
- Analytics & Statistics: 3 endpoints
- AI Matching Engine: 2 endpoints
- Assessment & Workflow: 6 endpoints
- Client Portal API: 2 endpoints
- Security Testing: 12 endpoints
- CSP Management: 4 endpoints
- Two-Factor Authentication: 8 endpoints
- Password Management: 6 endpoints
- Candidate Portal: 5 endpoints

**Database Tables Used:**
- candidates, jobs, feedback, interviews, offers
- clients, users, matching_cache
- audit_logs, rate_limits, csp_violations

**Authentication:**
- API Key validation
- Client JWT tokens (HS256)
- Candidate JWT tokens (HS256)

**Rate Limiting:**
- Dynamic: 60-500 requests/minute
- CPU-based adjustment
- Per-endpoint granular limits

---

### 2.2 AI Agent Module (Semantic Matching Engine)
**Purpose:** Advanced AI-powered candidate-job matching using Phase 3 semantic analysis

**Key Files:**
- `services/agent/app.py` - Main FastAPI application
- `services/agent/semantic_engine/phase3_engine.py` - Phase 3 AI engine
- `services/agent/config.py` - Configuration
- `services/agent/Dockerfile` - Container configuration
- `services/agent/requirements.txt` - Python dependencies

**Endpoints:** 6 total
- `/` - Service information
- `/health` - Health check
- `/test-db` - Database connectivity test
- `/match` - AI-powered candidate matching
- `/batch-match` - Batch matching for multiple jobs
- `/analyze/{candidate_id}` - Detailed candidate analysis

**AI Capabilities:**
- Sentence transformer embeddings
- Semantic similarity scoring
- Skills categorization
- Experience level matching
- Location matching
- Batch processing (multiple jobs)

**Database Tables Used:**
- candidates, jobs

**Processing:**
- Response time: <0.02s per candidate
- Batch size: 50 candidates/chunk
- Algorithm: Phase 3 Semantic Engine v3.0.0

---

### 2.3 LangGraph Orchestrator Module
**Purpose:** AI-driven workflow automation and multi-channel communication

**Key Files:**
- `services/langgraph/app/main.py` - Main FastAPI application
- `services/langgraph/app/state.py` - Workflow state definitions
- `services/langgraph/app/communication.py` - Multi-channel messaging
- `services/langgraph/app/rl_integration/` - RL engine integration (decision_engine.py, postgres_adapter.py, rl_endpoints.py)
- `services/langgraph/app/database_tracker.py` - Workflow tracking
- `services/langgraph/app/monitoring.py` - Service monitoring
- `services/langgraph/config.py` - Configuration
- `services/langgraph/dependencies.py` - Dependency injection
- `services/langgraph/Dockerfile` - Container configuration
- `services/langgraph/requirements.txt` - Python dependencies

**Endpoints:** 25 total
- **RL + Feedback Agent:** 8 endpoints
  - `/rl/predict` - RL prediction
  - `/rl/feedback` - Submit feedback
  - `/rl/analytics` - Get analytics
  - `/rl/performance/{model_version}` - Get performance
  - `/rl/history/{candidate_id}` - Get history
  - `/rl/retrain` - Trigger retrain
  - `/rl/performance` - Get performance
  - `/rl/start-monitoring` - Start monitoring
- **Core API:** 2 endpoints
  - `/` - Service information
  - `/health` - Health check
- **Workflow Management:** 2 endpoints
  - `/workflows/application/start` - Start workflow
  - `/workflows/{workflow_id}/resume` - Resume workflow
- **Workflow Monitoring:** 3 endpoints
  - `/workflows/{workflow_id}/status` - Get status
  - `/workflows` - List workflows
  - `/workflows/stats` - Get statistics
- **Communication Tools:** 9 endpoints
  - `/tools/send-notification` - Send notification
  - `/test/send-email` - Test email
  - `/test/send-whatsapp` - Test WhatsApp
  - `/test/send-telegram` - Test Telegram
  - `/test/send-whatsapp-buttons` - Test buttons
  - `/test/send-automated-sequence` - Test sequence
  - `/automation/trigger-workflow` - Trigger workflow
  - `/automation/bulk-notifications` - Bulk notifications
  - `/webhook/whatsapp` - WhatsApp webhook
- **System Diagnostics:** 1 endpoint
  - `/test-integration` - Integration testing

**Workflow Capabilities:**
- Candidate application processing
- AI-driven decision making
- Multi-stage workflow execution
- Real-time status tracking
- WebSocket updates

**Communication Channels:**
- Email (Gmail SMTP)
- WhatsApp (Twilio API)
- Telegram (Bot API)
- Interactive buttons (WhatsApp)

**RL Integration:**
- Feedback collection
- Reward signal calculation
- Model performance tracking
- Adaptive learning

**Database Tables Used:**
- workflows
- rl_predictions, rl_feedback
- rl_model_performance, rl_training_data

---

### 2.4 HR Portal Module
**Purpose:** Internal HR dashboard for candidate and job management

**Key Files:**
- `services/portal/app.py` - Main Streamlit application
- `services/portal/auth_manager.py` - Authentication management
- `services/portal/config.py` - Configuration
- `services/portal/Dockerfile` - Container configuration
- `services/portal/requirements.txt` - Python dependencies

**Features:**
- Candidate list view with pagination
- Job posting management
- AI matching results display
- Feedback submission
- Interview scheduling
- Analytics dashboard

**Authentication:**
- Username/password login
- Session management
- Role-based access control

**Database Tables Used:**
- candidates, jobs, feedback, interviews, offers
- users, matching_cache

---

### 2.5 Client Portal Module
**Purpose:** Enterprise client interface for job posting and candidate review

**Key Files:**
- `services/client_portal/app.py` - Main Streamlit application
- `services/client_portal/auth_manager.py` - Authentication management
- `services/client_portal/config.py` - Configuration
- `services/client_portal/Dockerfile` - Container configuration
- `services/client_portal/requirements.txt` - Python dependencies

**Features:**
- Client registration and login
- Job posting creation
- Candidate shortlist review
- Interview scheduling
- Offer management

**Authentication:**
- Client ID + password
- JWT token generation
- Account lockout (5 failed attempts)

**Database Tables Used:**
- clients, jobs, candidates
- interviews, offers

---

### 2.6 Candidate Portal Module
**Purpose:** Job seeker interface for applications and profile management

**Key Files:**
- `services/candidate_portal/app.py` - Main Streamlit application
- `services/candidate_portal/auth_manager.py` - Authentication management
- `services/candidate_portal/config.py` - Configuration
- `services/candidate_portal/Dockerfile` - Container configuration
- `services/candidate_portal/requirements.txt` - Python dependencies

**Features:**
- Candidate registration and login
- Profile management
- Job search and application
- Application status tracking
- Interview notifications

**Authentication:**
- Email + password
- JWT token generation
- Password hashing (bcrypt)

**Database Tables Used:**
- candidates, jobs, job_applications

---

### 2.7 Database Module
**Purpose:** MongoDB Atlas database with comprehensive schema

**Key Files:**
- `services/db/consolidated_schema.sql` - Complete schema v4.3.0
- `services/db/deploy_schema_production.sql` - Production deployment schema
- `services/db/database/migrations/` - Schema migrations
- `services/db/database/migrations/add_rl_tables.sql` - RL tables migration
- `services/db/Dockerfile` - Container configuration
- `services/db/README.md` - Database documentation

**Schema Version:** 4.3.0

**Core Tables (14):**
1. **candidates** - Candidate profiles and information
2. **jobs** - Job postings and requirements
3. **clients** - Enterprise client accounts
4. **users** - HR system users
5. **feedback** - Values-based assessment feedback
6. **interviews** - Interview scheduling and tracking
7. **offers** - Job offer management
8. **matching_cache** - AI matching results cache
9. **audit_logs** - System audit trail
10. **rate_limits** - API rate limiting tracking
11. **csp_violations** - Content Security Policy violations
12. **company_scoring_preferences** - Phase 3 learning preferences
13. **job_applications** - Candidate job applications
14. **workflows** - LangGraph workflow tracking

**RL/ML Tables (4):**
1. **rl_predictions** - RL model predictions
2. **rl_feedback** - Feedback for RL learning
3. **rl_model_performance** - Model performance metrics
4. **rl_training_data** - Training data for RL model **company_scoring_preferences** - Company-specific scoring

**Features:**
- 75+ indexes for performance
- Audit triggers on critical tables
- Generated columns for computed values
- Referential integrity constraints
- Soft delete support

---

## 3. Service Dependencies

### Internal Service Communication

```
┌─────────────┐
│  HR Portal  │──────┐
└─────────────┘      │
                     │
┌─────────────┐      │      ┌──────────────┐
│Client Portal│──────┼─────▶│ API Gateway  │
└─────────────┘      │      └──────┬───────┘
                     │             │
┌─────────────┐      │             │
│Cand Portal  │──────┘             │
└─────────────┘                    │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
            │  AI Agent    │ │LangGraph │ │ Database   │
            │              │ │          │ │            │
            │  • Matching  │ │• Workflow│ │• MongoDB   │
            │  • Analysis  │ │• RL Eng  │ │• Schema v4 │
            └──────────────┘ └──────────┘ └────────────┘
```

### Dependency Flow

**1. Portal → Gateway → Services**
- All portals communicate exclusively through API Gateway
- No direct portal-to-service communication
- Gateway handles authentication and routing

**2. Gateway → AI Agent**
- Matching requests: `POST /match`
- Batch matching: `POST /batch-match`
- Candidate analysis: `GET /analyze/{id}`

**3. Gateway → LangGraph**
- Workflow creation: `POST /workflows/application/start`
- Status tracking: `GET /workflows/{id}/status`
- Notifications: `POST /tools/send-notification`

**4. Gateway → Database**
- Direct SQL queries via SQLAlchemy
- Connection pooling (10 connections)
- Transaction management

**5. AI Agent → Database**
- Read-only candidate and job data
- Connection pooling (2-10 connections)
- Optimized queries for matching

**6. LangGraph → Database**
- Workflow state persistence
- RL feedback storage
- Communication logs

**7. LangGraph → External APIs**
- Twilio (WhatsApp, SMS)
- Gmail SMTP (Email)
- Telegram Bot API

---

## 4. Workflow Pipelines

### 4.1 Candidate Application Flow

```
1. Candidate Registration
   ↓
   Candidate Portal → POST /v1/candidate/register → Gateway
   ↓
   Gateway → Database (INSERT candidates)
   ↓
   Return JWT token

2. Job Application
   ↓
   Candidate Portal → POST /v1/candidate/apply → Gateway
   ↓
   Gateway → Database (INSERT job_applications)
   ↓
   Trigger LangGraph workflow

3. AI Workflow Processing
   ↓
   LangGraph → POST /workflows/application/start
   ↓
   Workflow stages:
   • Screening (0-25%)
   • AI Matching (25-70%)
   • Recommendations (70-90%)
   • Completion (90-100%)
   ↓
   Gateway → POST /match → AI Agent
   ↓
   AI Agent → Semantic analysis → Return score
   ↓
   LangGraph → Update workflow status
   ↓
   LangGraph → Send notifications (Email + WhatsApp)

4. HR Review
   ↓
   HR Portal → GET /v1/candidates → Gateway
   ↓
   Gateway → Database → Return candidates with AI scores
   ↓
   HR reviews and schedules interview

5. Interview Scheduling
   ↓
   HR Portal → POST /v1/interviews → Gateway
   ↓
   Gateway → Database (INSERT interviews)
   ↓
   LangGraph → Send interview notifications

6. Feedback Collection
   ↓
   HR Portal → POST /v1/feedback → Gateway
   ↓
   Gateway → Database (INSERT feedback)
   ↓
   LangGraph → Store RL feedback
   ↓
   RL Engine → Update model
```

### 4.2 Job Posting Flow

```
1. Client Login
   ↓
   Client Portal → POST /v1/client/login → Gateway
   ↓
   Gateway → Database (SELECT clients)
   ↓
   Verify password → Generate JWT token

2. Job Creation
   ↓
   Client Portal → POST /v1/jobs → Gateway
   ↓
   Gateway → Database (INSERT jobs)
   ↓
   Return job_id

3. Candidate Matching
   ↓
   Client Portal → GET /v1/match/{job_id}/top → Gateway
   ↓
   Gateway → POST /match → AI Agent
   ↓
   AI Agent → Semantic matching → Return top candidates
   ↓
   Display in Client Portal

4. Candidate Shortlisting
   ↓
   Client reviews AI recommendations
   ↓
   Client Portal → POST /v1/interviews → Gateway
   ↓
   Schedule interviews with top candidates
```

### 4.3 RL Feedback Loop

```
1. Hiring Decision
   ↓
   HR Portal → POST /v1/feedback → Gateway
   ↓
   Gateway → Database (INSERT feedback)

2. RL Processing
   ↓
   LangGraph → POST /rl/feedback
   ↓
   Calculate reward signal:
   • Hired + High rating = +1.0
   • Rejected + Low rating = -0.5
   ↓
   Store in rl_feedback table

3. Model Update
   ↓
   RL Engine → Fetch feedback history
   ↓
   Update scoring weights
   ↓
   Store in rl_model_performance

4. Improved Matching
   ↓
   Next matching request uses updated model
   ↓
   Better candidate recommendations
```

---

## 5. Event Triggers

### Application Events

| Event | Trigger | Action | Service |
|-------|---------|--------|---------|
| `candidate.registered` | POST /v1/candidate/register | Send welcome email | LangGraph |
| `candidate.applied` | POST /v1/candidate/apply | Start AI workflow | LangGraph |
| `application.screened` | Workflow stage complete | Update status | LangGraph |
| `candidate.matched` | AI matching complete | Notify HR | LangGraph |
| `interview.scheduled` | POST /v1/interviews | Send notifications | LangGraph |
| `feedback.submitted` | POST /v1/feedback | Update RL model | LangGraph |
| `offer.created` | POST /v1/offers | Send offer letter | LangGraph |

### System Events

| Event | Trigger | Action | Service |
|-------|---------|--------|---------|
| `rate_limit.exceeded` | Request count > limit | Return 429 error | Gateway |
| `auth.failed` | Invalid credentials | Log attempt | Gateway |
| `csp.violated` | CSP policy breach | Log violation | Gateway |
| `workflow.failed` | Workflow error | Alert admin | LangGraph |
| `db.connection.lost` | Connection failure | Retry with backoff | All |

---

## 6. Microservice Boundaries

### Clear Separation of Concerns

**Gateway Service:**
- ✅ Authentication and authorization
- ✅ Request routing and validation
- ✅ Rate limiting and security
- ✅ API documentation
- ❌ Business logic
- ❌ AI processing
- ❌ Workflow orchestration

**AI Agent Service:**
- ✅ Semantic matching algorithms
- ✅ Candidate analysis
- ✅ Batch processing
- ❌ Data persistence (read-only)
- ❌ User authentication
- ❌ Workflow management

**LangGraph Service:**
- ✅ Workflow orchestration
- ✅ Multi-channel communication
- ✅ RL engine integration
- ✅ Event processing
- ❌ AI matching logic
- ❌ User authentication

**Portal Services:**
- ✅ User interface
- ✅ Session management
- ✅ Data visualization
- ❌ Business logic (delegated to Gateway)
- ❌ Direct database access
- ❌ AI processing

**Database Service:**
- ✅ Data persistence
- ✅ Schema management
- ✅ Query optimization
- ❌ Business logic
- ❌ API endpoints

---

## 7. Technology Stack

### Backend Services
- **Framework:** FastAPI >=0.104.0, <0.120.0
- **Language:** Python 3.12.7
- **ASGI Server:** Uvicorn
- **Authentication:** JWT (PyJWT), bcrypt
- **Validation:** Pydantic >=2.5.0, <3.0.0

### Frontend Portals
- **Framework:** Streamlit >=1.28.0, <2.0.0
- **Language:** Python 3.12.7
- **UI Components:** Custom Streamlit components

### Database
- **Database:** MongoDB Atlas
- **ORM:** SQLAlchemy >=2.0.23, <2.1.0
- **Connection Pool:** psycopg2-binary >=2.9.7, <3.0.0
- **Migrations:** Alembic

### AI/ML
- **Semantic Engine:** Sentence Transformers
- **RL Framework:** Custom implementation
- **ML Libraries:** scikit-learn, numpy, pandas

### Communication
- **Email:** Gmail SMTP
- **WhatsApp:** Twilio API
- **Telegram:** Bot API
- **SMS:** Twilio API

### Deployment
- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Platform:** Render (Oregon, US West)
- **CI/CD:** Git-based deployment

### Monitoring
- **Metrics:** Prometheus
- **Logging:** Python logging
- **Health Checks:** Custom endpoints

---

## 8. Security Architecture

### Authentication Layers

**Layer 1: API Key (Gateway)**
- Environment variable: `API_KEY_SECRET`
- Bearer token in Authorization header
- Used for service-to-service communication

**Layer 2: Client JWT (Client Portal)**
- Secret: `JWT_SECRET_KEY`
- Algorithm: HS256
- Expiry: 24 hours
- Payload: client_id, company_name

**Layer 3: Candidate JWT (Candidate Portal)**
- Secret: `CANDIDATE_JWT_SECRET_KEY`
- Algorithm: HS256
- Expiry: 24 hours
- Payload: candidate_id, email

### Security Features
- Password hashing: bcrypt with salt
- 2FA: TOTP with QR codes
- Rate limiting: Dynamic 60-500 req/min
- Security headers: CSP, XSS, HSTS
- Input validation: Pydantic models
- SQL injection prevention: Parameterized queries
- Account lockout: 5 failed attempts = 30 min lock

---

## 9. Scalability & Performance

### Current Capacity
- **Concurrent Users:** 100+
- **API Response Time:** <100ms (p95)
- **AI Matching Time:** <0.02s per candidate
- **Database Connections:** 10 per service
- **Uptime:** 99.9%

### Optimization Strategies
- Connection pooling (all services)
- Query result caching (matching_cache table)
- Batch processing (AI Agent)
- Async operations (LangGraph workflows)
- Index optimization (75+ indexes)
- Dynamic rate limiting (CPU-based)

### Scaling Options
- Horizontal: Add more service instances
- Vertical: Increase container resources
- Database: Read replicas for reporting
- Caching: Redis for session/matching cache
- CDN: Static assets delivery

---

## 10. Deployment Architecture

### Production Environment (Render)

```
┌─────────────────────────────────────────────────────┐
│              Render Platform (Oregon)                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Gateway     │  │  AI Agent    │  │ LangGraph │ │
│  │  Container   │  │  Container   │  │ Container │ │
│  │  Port: 8000  │  │  Port: 9000  │  │Port: 9001 │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  HR Portal   │  │Client Portal │  │Cand Portal│ │
│  │  Container   │  │  Container   │  │ Container │ │
│  │  Port: 8501  │  │  Port: 8502  │  │Port: 8503 │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │     MongoDB Atlas (Managed Database)        │   │
│  │     Connection String: DATABASE_URL         │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Service URLs
- Gateway: `bhiv-hr-gateway-ltg0.onrender.com`
- AI Agent: `bhiv-hr-agent-nhgg.onrender.com`
- LangGraph: `bhiv-hr-langgraph.onrender.com`
- HR Portal: `bhiv-hr-portal-u670.onrender.com`
- Client Portal: `bhiv-hr-client-portal-3iod.onrender.com`
- Candidate Portal: `bhiv-hr-candidate-portal-abe6.onrender.com`

### Environment Variables (Per Service)
- `DATABASE_URL` - MongoDB Atlas connection string
- `API_KEY_SECRET` - API authentication key
- `JWT_SECRET_KEY` - Client JWT secret
- `CANDIDATE_JWT_SECRET_KEY` - Candidate JWT secret
- `ENVIRONMENT` - production/development
- `PORT` - Service port number

---

## 11. Data Flow Examples

### Example 1: Candidate Applies for Job

```
1. Candidate fills application form
   ↓
2. POST /v1/candidate/apply
   Headers: Authorization: Bearer <candidate_jwt_secret_key>
   Body: {candidate_id, job_id, cover_letter}
   ↓
3. Gateway validates JWT token
   ↓
4. Gateway inserts into job_applications table
   ↓
5. Gateway triggers LangGraph workflow
   POST /workflows/application/start
   ↓
6. LangGraph creates workflow record
   INSERT INTO workflows
   ↓
7. LangGraph calls AI Agent for matching
   POST /match {job_id, candidate_id}
   ↓
8. AI Agent performs semantic analysis
   - Fetch job requirements
   - Fetch candidate profile
   - Calculate similarity score
   ↓
9. AI Agent returns score (e.g., 87.5)
   ↓
10. LangGraph updates workflow
    UPDATE workflows SET progress=70%
    ↓
11. LangGraph sends notifications
    - Email to candidate (confirmation)
    - WhatsApp to candidate (status)
    - Email to HR (new application)
    ↓
12. LangGraph completes workflow
    UPDATE workflows SET status='completed'
    ↓
13. Response returned to Candidate Portal
    {success: true, application_id: 123}
```

### Example 2: HR Reviews Candidates

```
1. HR logs into HR Portal
   ↓
2. Portal calls GET /v1/candidates
   Headers: Authorization: Bearer <api_key_secret>
   ↓
3. Gateway queries database
   SELECT * FROM candidates ORDER BY created_at DESC
   ↓
4. Gateway returns candidate list
   ↓
5. HR clicks "View AI Matches" for a job
   ↓
6. Portal calls GET /v1/match/{job_id}/top
   ↓
7. Gateway forwards to AI Agent
   POST /match {job_id}
   ↓
8. AI Agent performs batch matching
   - Fetch all candidates
   - Calculate scores for each
   - Sort by score descending
   ↓
9. AI Agent returns top 10 candidates
   [{id: 1, score: 92.3}, {id: 2, score: 88.7}, ...]
   ↓
10. Gateway caches results
    INSERT INTO matching_cache
    ↓
11. Results displayed in HR Portal
    ↓
12. HR selects candidate for interview
    ↓
13. Portal calls POST /v1/interviews
    Body: {candidate_id, job_id, interview_date}
    ↓
14. Gateway inserts interview record
    ↓
15. Gateway triggers LangGraph notification
    ↓
16. LangGraph sends interview invite
    - Email with calendar invite
    - WhatsApp with confirmation buttons
```

---

## 12. Error Handling & Recovery

### Error Handling Strategy

**Gateway Level:**
- Invalid authentication → 401 Unauthorized
- Rate limit exceeded → 429 Too Many Requests
- Validation error → 400 Bad Request
- Resource not found → 404 Not Found
- Server error → 500 Internal Server Error

**Service Level:**
- Database connection failure → Retry with exponential backoff
- External API timeout → Fallback to cached data
- Workflow failure → Log error, alert admin, mark as failed

**Recovery Mechanisms:**
- Connection pooling with health checks
- Automatic retry for transient failures
- Circuit breaker for external APIs
- Graceful degradation (fallback modes)
- Transaction rollback on errors

---

## 13. Monitoring & Observability

### Health Checks
- Gateway: `GET /health`
- AI Agent: `GET /health`
- LangGraph: `GET /health`
- Database: Connection pool status

### Metrics (Prometheus)
- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by status code
- Active connections
- CPU and memory usage
- Workflow completion rate

### Logging
- Application logs: Python logging module
- Access logs: FastAPI middleware
- Error logs: Exception tracking
- Audit logs: Database triggers

---

## Summary

The BHIV HR Platform is a production-ready, enterprise-grade recruiting system built on a microservices architecture. It features:

- **6 independent services** working in harmony
- **89 API endpoints** covering all HR workflows
- **Triple authentication** for maximum security
- **AI-powered matching** with Phase 3 semantic engine
- **RL integration** for continuous improvement
- **Multi-channel communication** (Email, WhatsApp, Telegram)
- **Real-time workflow tracking** with detailed progress
- **99.9% uptime** on free-tier infrastructure

The architecture is designed for scalability, maintainability, and extensibility, with clear service boundaries and well-defined communication patterns.

---

**Document Status:** ✅ Complete  
**Next Steps:** Refer to API Contract documentation for detailed endpoint specifications

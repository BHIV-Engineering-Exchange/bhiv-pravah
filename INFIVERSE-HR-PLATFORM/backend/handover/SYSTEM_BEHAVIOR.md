# SYSTEM_BEHAVIOR.md
**BHIV HR Platform - Critical Handover Documentation**  
**Version**: 4.3.1  
**Updated**: January 22, 2026  
**Database**: MongoDB Atlas (migrated from PostgreSQL)  
**Architecture**: Microservices with 111 endpoints (80 Gateway + 6 Agent + 25 LangGraph)  
**Status**: Production Ready - Zero Dependency Handover  

---

## 🎯 **SYSTEM OVERVIEW**

**BHIV HR Platform** is a **microservices-based enterprise HR platform** with AI-powered candidate matching, reinforcement learning, and comprehensive security features.

### **Architecture Summary**
- **6 Microservices**: Gateway, Agent, LangGraph, Portal, Client Portal, Candidate Portal
- **Database**: MongoDB Atlas (Primary) with 17+ collections
- **Deployment**: Docker containers with dynamic port allocation + Render Cloud
- **Authentication**: Triple authentication (API Key + Client JWT + Candidate JWT)
- **Total Endpoints**: 111 (80 Gateway + 6 Agent + 25 LangGraph)
- **Monitoring**: Integrated Prometheus metrics, health checks, audit logging

---

## 🔄 **CORE SYSTEM BEHAVIORS**

### **1. AUTHENTICATION FLOW**

#### **Triple Authentication System**
```
1. API Key Authentication (Primary)
   - Header: Authorization: Bearer <API_KEY_SECRET>
   - Used for: All API endpoints
   - Validation: Exact match with environment variable

2. Client JWT Authentication
   - Header: Authorization: Bearer <CLIENT_JWT_TOKEN>
   - Used for: Client portal access
   - Secret: JWT_SECRET_KEY
   - Expiry: 24 hours

3. Candidate JWT Authentication
   - Header: Authorization: Bearer <CANDIDATE_JWT_TOKEN>
   - Used for: Candidate portal access
   - Secret: CANDIDATE_JWT_SECRET_KEY
   - Expiry: 24 hours
```

#### **Authentication Behavior**
- **Dual Auth Endpoints**: Accept either API key OR JWT token
- **API Key Priority**: API key checked first, then JWT tokens
- **Fallback Logic**: If API key fails, tries Client JWT, then Candidate JWT
- **Error Response**: 401 "Invalid authentication" if all methods fail

### **2. DATABASE CONNECTION BEHAVIOR**

#### **Connection Management**
```python
# Connection Pool Configuration
pool_size=10
max_overflow=5
pool_timeout=20
pool_recycle=3600
connect_timeout=10
```

#### **Database Behavior**
- **Connection Management**: MongoDB Atlas cluster with auto-failover
- **Connection Pooling**: Atlas connection pool optimization
- **Transaction Management**: Uses MongoDB atomic operations and multi-document transactions
- **Error Handling**: Graceful fallback with detailed error messages in responses
- **Data Model**: Document-based schema with flexible collections

### **3. API ENDPOINT BEHAVIOR**

#### **Gateway Service (Port 8000) - 88 Endpoints**

**Core API Endpoints (5)**
- `GET /` - API root information
- `GET /health` - Health check with security headers
- `GET /docs` - Swagger UI documentation
- `GET /openapi.json` - OpenAPI schema
- `GET /test-candidates` - Database connectivity test

**Job Management (2)**
- `POST /v1/jobs` - Create job posting (requires API key)
- `GET /v1/jobs` - List active jobs (accepts dual auth)

**Candidate Management (5)**
- `GET /v1/candidates` - Get all candidates with pagination
- `GET /v1/candidates/search` - Search candidates with filters
- `GET /v1/candidates/stats` - Real-time statistics for dashboard
- `GET /v1/candidates/job/{job_id}` - Get candidates for specific job
- `GET /v1/candidates/{candidate_id}` - Get specific candidate
- `POST /v1/candidates/bulk` - Bulk upload candidates

**AI Matching Engine (2)**
- `GET /v1/match/{job_id}/top` - AI-powered semantic matching
- `POST /v1/match/batch` - Batch AI matching for multiple jobs

**Assessment & Workflow (5)**
- `POST /v1/feedback` - Submit values assessment
- `GET /v1/feedback` - Get all feedback records
- `POST /v1/interviews` - Schedule interview
- `GET /v1/interviews` - Get all interviews
- `POST /v1/offers` - Create job offer
- `GET /v1/offers` - Get all job offers

**Client Portal API (2)**
- `POST /v1/client/register` - Client registration
- `POST /v1/client/login` - Client authentication

**Candidate Portal (5)**
- `POST /v1/candidate/register` - Candidate registration
- `POST /v1/candidate/login` - Candidate authentication
- `PUT /v1/candidate/profile/{candidate_id}` - Update profile
- `POST /v1/candidate/apply` - Apply for job
- `GET /v1/candidate/applications/{candidate_id}` - Get applications

**Security Testing (11)**
- Rate limiting, input validation, email/phone validation
- Security headers, penetration testing, authentication testing

**CSP Management (4)**
- Content Security Policy violation reporting and management

**Two-Factor Authentication (8)**
- 2FA setup, verification, login, status, disable, backup codes

**Password Management (12)**
- Password validation, generation, policy, strength testing

**Analytics & Statistics (4)**
- Database schema, analytics export, job reports

#### **Agent Service (Port 9000) - 6 Endpoints**

**AI Matching Endpoints**
- `POST /match` - Semantic candidate matching
- `POST /batch-match` - Batch matching for multiple jobs
- `GET /health` - Service health check
- `GET /candidates/{candidate_id}/analysis` - Candidate analysis
- `POST /jobs/{job_id}/requirements` - Job requirements analysis
- `GET /matching/performance` - Matching performance metrics

#### **LangGraph Service (Port 9001) - 25 Endpoints**

**Workflow Automation (25)**
- Candidate application workflows
- Interview scheduling automation
- Multi-channel notifications (Email, WhatsApp, Telegram, SMS)
- Workflow status tracking and monitoring

**RL Integration (8)**
- Reinforcement learning predictions
- Feedback collection and processing
- Model performance tracking
- Training data management

### **4. AI MATCHING BEHAVIOR**

#### **Semantic Matching Flow**
```
1. Gateway receives match request
2. Calls Agent service with job_id and candidate_ids
3. Agent performs semantic analysis using sentence transformers
4. Returns scored candidates with reasoning
5. Gateway transforms response to standard format
6. Fallback to database matching if Agent service fails
```

#### **Matching Algorithm**
- **Phase 3 Semantic Engine**: Uses sentence transformers
- **Scoring Range**: 0-100 (higher is better match)
- **Batch Processing**: 50 candidates per chunk
- **Response Time**: <0.02s for individual matches
- **Fallback Logic**: Database-based matching when AI service unavailable

### **5. RATE LIMITING BEHAVIOR**

#### **Dynamic Rate Limiting**
```python
# Rate Limits by User Tier
"default": {
    "/v1/jobs": 100,
    "/v1/candidates/search": 50,
    "/v1/match": 20,
    "/v1/candidates/bulk": 5,
    "default": 60
},
"premium": {
    "/v1/jobs": 500,
    "/v1/candidates/search": 200,
    "/v1/match": 100,
    "/v1/candidates/bulk": 25,
    "default": 300
}
```

#### **Rate Limiting Logic**
- **CPU-based Adjustment**: Reduces limits by 50% when CPU > 80%
- **Window**: 60 seconds rolling window
- **Headers**: Returns X-RateLimit-Limit and X-RateLimit-Remaining
- **Error Response**: 429 "Rate limit exceeded" with specific limits

### **6. ERROR HANDLING BEHAVIOR**

#### **Standard Error Responses**
```json
{
    "success": false,
    "error": "Descriptive error message",
    "timestamp": "2025-12-22T06:29:29.069844+00:00",
    "additional_context": "..."
}
```

#### **Error Handling Patterns**
- **Database Errors**: Return empty arrays with error field
- **Authentication Errors**: 401 with specific error message
- **Validation Errors**: 400 with detailed validation feedback
- **Service Unavailable**: Graceful fallback with fallback indicators

### **7. SECURITY BEHAVIOR**

#### **Security Headers (Applied to all responses)**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

#### **Input Validation**
- **SQL Injection Protection**: Parameterized queries only
- **XSS Protection**: Input sanitization and CSP headers
- **Email Validation**: Regex pattern validation
- **Phone Validation**: Indian phone number format
- **Length Limits**: Skills (200 chars), Location (100 chars)

### **8. WORKFLOW AUTOMATION BEHAVIOR**

#### **LangGraph Workflows**
```
1. Candidate Application Workflow
   - Triggered on job application
   - Sends notifications to HR and client
   - Updates application status

2. Interview Scheduling Workflow
   - Triggered on interview creation
   - Sends calendar invites
   - Reminder notifications

3. Custom Workflows
   - Configurable workflow types
   - Multi-step automation
   - Error handling and retry logic
```

#### **Notification Channels**
- **Email**: Gmail SMTP integration
- **WhatsApp**: Twilio WhatsApp API
- **Telegram**: Telegram Bot API
- **SMS**: Twilio SMS API

---

## 🔧 **SERVICE DEPENDENCIES**

### **Service Startup Order**
1. **Database** (PostgreSQL) - Must be healthy first
2. **Gateway** - Depends on database health
3. **Agent** - Depends on database health
4. **LangGraph** - Depends on database health
5. **Portals** - Depend on Gateway health

### **Inter-Service Communication**
```
Gateway → Agent: AI matching requests
Gateway → LangGraph: Workflow triggers
Portals → Gateway: All API calls
LangGraph → Gateway: Status updates
```

### **Health Check Dependencies**
- All services have `/health` endpoints
- Health checks include database connectivity
- Docker health checks with retry logic
- Service discovery through environment variables

---

## 📊 **DATA FLOW BEHAVIOR**

### **Candidate Registration Flow**
```
1. Candidate submits registration → Candidate Portal
2. Portal validates input → Gateway API
3. Gateway checks email uniqueness → Database
4. Password hashed with bcrypt → Database storage
5. JWT token generated → Return to candidate
6. Audit log created → Database
```

### **Job Matching Flow**
```
1. Client requests matches → Gateway
2. Gateway calls Agent service → AI analysis
3. Agent performs semantic matching → Scored results
4. Results cached in matching_cache → Database
5. Transformed response → Client
6. Performance metrics logged → Monitoring
```

### **Workflow Automation Flow**
```
1. Event trigger (job application) → Gateway
2. Gateway calls LangGraph → Workflow creation
3. LangGraph processes steps → Multi-channel notifications
4. Status updates → Database workflow table
5. Completion notification → Gateway
6. Audit trail → Database logs
```

---

## 🚨 **CRITICAL BEHAVIORS TO MAINTAIN**

### **1. Authentication Precedence**
- **NEVER** change the order: API Key → Client JWT → Candidate JWT
- **ALWAYS** validate tokens before processing requests
- **MAINTAIN** 24-hour token expiry for security

### **2. Database Transaction Safety**
- **USE** `engine.begin()` for multi-step operations
- **HANDLE** connection failures gracefully
- **MAINTAIN** connection pool settings for performance

### **3. AI Service Fallback**
- **ALWAYS** provide database fallback when Agent service fails
- **MAINTAIN** response format consistency between AI and fallback
- **LOG** service failures for monitoring

### **4. Rate Limiting Enforcement**
- **ENFORCE** rate limits before processing requests
- **ADJUST** limits based on system load
- **RETURN** proper HTTP 429 responses

### **5. Security Header Consistency**
- **APPLY** security headers to ALL responses
- **MAINTAIN** CSP policy strictness
- **VALIDATE** all user inputs

---

## 🔍 **MONITORING & OBSERVABILITY**

### **Health Check Behavior**
- **Response Time**: <100ms for healthy services
- **Database Check**: Included in all service health checks
- **Dependency Check**: Services verify upstream dependencies
- **Status Codes**: 200 (healthy), 503 (unhealthy)

### **Performance Metrics**
- **API Response Time**: <100ms average
- **AI Matching Time**: <0.02s per candidate
- **Database Query Time**: <50ms average
- **Uptime Target**: 99.9%

### **Error Tracking**
- **Audit Logs**: All authentication and data changes
- **Error Logs**: Service failures and exceptions
- **Performance Logs**: Response times and resource usage
- **Security Logs**: Rate limiting and validation failures

---

## 📝 **SYSTEM STATE VERIFICATION**

### **Current Production Status**
- **Services**: 6/6 operational
- **Endpoints**: 111 total (100% functional)
- **Database**: MongoDB Atlas with 17+ collections
- **Uptime**: 99.9%
- **Cost**: $0/month (optimized free tier)
- **Migration**: Successfully migrated from PostgreSQL to MongoDB Atlas (Jan 2026)

### **Data Verification Commands**
```bash
# Test Gateway health
curl http://localhost:8000/health

# Test database connectivity
curl -H "Authorization: Bearer <API_KEY>" http://localhost:8000/test-candidates

# Test AI matching
curl -H "Authorization: Bearer <API_KEY>" http://localhost:8000/v1/match/1/top

# Test authentication
curl -H "Authorization: Bearer <API_KEY>" http://localhost:8000/v1/candidates/stats
```

---

**END OF SYSTEM_BEHAVIOR.md**

*This document captures the complete behavioral specification of the BHIV HR Platform as of December 22, 2025. Any changes to these behaviors must be documented and approved through the change management process.*
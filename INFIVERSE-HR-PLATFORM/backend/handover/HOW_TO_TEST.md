# HOW_TO_TEST.md
**BHIV HR Platform - Complete Testing Walkthrough**  
**Version**: 4.3.1  
**Generated**: December 22, 2025  
**Status**: Zero Dependency Handover - Ready for Vinayak Testing  
**Docker Status**: ✅ All 7 containers verified healthy locally  

---

## 🎯 **PURPOSE**

This document provides **one clean walkthrough** for testing the complete BHIV HR Platform. Designed for **Vinayak** to independently validate all system functionality without requiring original developer assistance.

---

## 📋 **TESTING OVERVIEW**

### **System Status**
- **Services**: 6/6 operational (Gateway, Agent, LangGraph, 3 Portals)
- **Endpoints**: 111 total (88 Gateway + 6 Agent + 25 LangGraph)
- **Database**: MongoDB Atlas (3 collections)
- **Authentication**: Triple auth (API Key + Client JWT + Candidate JWT)
- **Deployment**: Docker + Render Cloud (production ready)
- **Docker Local**: ✅ All 7 containers healthy and operational
- **Last Verified**: December 22, 2025

### **Testing Scope**
- ✅ **Functional Testing**: All 111 endpoints
- ✅ **Integration Testing**: Cross-service communication
- ✅ **Security Testing**: Authentication, authorization, input validation
- ✅ **Performance Testing**: Response times, load handling
- ✅ **User Acceptance Testing**: Portal workflows
- ✅ **Tenant Isolation Testing**: Multi-client data separation

---

## 🚀 **QUICK START (5 Minutes)**

### **Step 1: Environment Setup**
```bash
# Option A: Use Live Production (Recommended - No Setup)
Gateway: https://bhiv-hr-gateway-ltg0.onrender.com
HR Portal: https://bhiv-hr-portal-u670.onrender.com
Client Portal: https://bhiv-hr-client-portal-3iod.onrender.com
Candidate Portal: https://bhiv-hr-candidate-portal-abe6.onrender.com

# Option B: Local Docker (Verified Working)
cd "c:\BHIV HR PLATFORM"
docker-compose -f docker-compose.production.yml up -d
# Wait 30 seconds for initialization
# Verify: docker-compose -f docker-compose.production.yml ps
# Expected: 7 containers all "Up" and "healthy"

# Local URLs:
# Gateway: http://localhost:8000
# Agent: http://localhost:9000  
# LangGraph: http://localhost:9001
# HR Portal: http://localhost:8501
# Client Portal: http://localhost:8502
# Candidate Portal: http://localhost:8503
```

### **Step 2: Verify System Health**
```bash
# Test all services are running
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Expected: All return {"status": "healthy"}
```

### **Step 3: Get API Key**
```bash
# API Key for testing (from config/local.env)
API_KEY_SECRET="prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

# Test API access
curl -H "Authorization: Bearer $API_KEY_SECRET" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/stats
```

### **Step 4: Import Postman Collection**
```bash
# File: handover/postman_collection.json
# Contains all 111 endpoints organized in 23 folders
# Import into Postman and set environment variables
```

---

## 🧪 **COMPREHENSIVE TESTING PROCEDURE**

### **TEST SUITE 1: Core System Validation (15 minutes)**

#### **1.1 Service Health Check**
```bash
# Test all service endpoints
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health  
curl https://bhiv-hr-langgraph.onrender.com/health

# Expected Results:
# Gateway: {"status":"healthy","service":"BHIV HR Gateway","version":"4.3.1"}
# Agent: {"status":"healthy","service":"BHIV AI Agent","version":"4.3.1","rl_integration":"enabled"}
# LangGraph: {"status":"healthy","uptime_seconds":X,"workflows_processed":X}
```

#### **1.2 Database Connectivity**
```bash
# Test database connection
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/test-candidates

# Expected: {"database_status":"connected","total_candidates":X}
```

#### **1.3 API Documentation Access**
```bash
# Verify API docs are accessible
curl https://bhiv-hr-gateway-ltg0.onrender.com/docs
curl https://bhiv-hr-agent-nhgg.onrender.com/docs
curl https://bhiv-hr-langgraph.onrender.com/docs

# Expected: HTML content with Swagger UI
```

**✅ PASS CRITERIA**: All services return healthy status, database connected, docs accessible

---

### **TEST SUITE 2: Authentication & Security (20 minutes)**

#### **2.1 API Key Authentication**
```bash
# Valid API key
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/stats
# Expected: Statistics data

# Invalid API key
curl -H "Authorization: Bearer invalid_key" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/stats
# Expected: 401 Unauthorized
```

#### **2.2 Client JWT Authentication**
```bash
# Client login
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/client/login \
  -H "Content-Type: application/json" \
  -d '{"client_id":"TECH001","password":"demo123"}'

# Expected: {"success":true,"access_token":"JWT_TOKEN","client_id":"TECH001"}
# Save JWT_TOKEN for next tests

# Use client JWT
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs
# Expected: Jobs list for TECH001 client
```

#### **2.3 Security Headers**
```bash
# Test security headers
curl -I https://bhiv-hr-gateway-ltg0.onrender.com/v1/security/test-headers

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: default-src 'self'
```

#### **2.4 Input Validation**
```bash
# Test XSS protection
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/security/test-input-validation \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input_data":"<script>alert(\"xss\")</script>"}'

# Expected: {"validation_result":"BLOCKED","threats_detected":["XSS attempt detected"]}
```

**✅ PASS CRITERIA**: Authentication works, security headers present, input validation blocks attacks

---

### **TEST SUITE 3: Core Business Logic (25 minutes)**

#### **3.1 Job Management**
```bash
# Create job
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Test Engineer",
    "department":"Engineering", 
    "location":"Remote",
    "experience_level":"senior",
    "requirements":"Python, FastAPI, Testing",
    "description":"Test job for validation"
  }'

# Expected: {"message":"Job created successfully","job_id":X}
# Save job_id for next tests

# List jobs
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs

# Expected: {"jobs":[...],"count":X} with created job included
```

#### **3.2 Candidate Management**
```bash
# List candidates
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Expected: {"candidates":[...],"total":X,"count":X}

# Get candidate statistics
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/stats

# Expected: {"total_candidates":X,"active_jobs":X,"recent_matches":X}

# Search candidates
curl -H "Authorization: Bearer $API_KEY" \
  "https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/search?skills=Python"

# Expected: {"candidates":[...],"count":X} with Python developers
```

#### **3.3 AI Matching Engine**
```bash
# Get AI matches for job
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/$JOB_ID/top

# Expected: {
#   "matches":[{
#     "candidate_id":X,
#     "name":"...",
#     "score":85.5,
#     "skills_match":"...",
#     "reasoning":"..."
#   }],
#   "algorithm_version":"phase3_v1.0",
#   "processing_time":"0.45s"
# }

# Batch matching
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/batch \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_ids":['$JOB_ID']}'

# Expected: {"batch_results":{...},"total_jobs_processed":1}
```

**✅ PASS CRITERIA**: Jobs created/listed, candidates retrieved, AI matching returns scored results

---

### **TEST SUITE 4: Workflow Automation (20 minutes)**

#### **4.1 LangGraph Workflow Triggers**
```bash
# Start candidate application workflow
curl -X POST https://bhiv-hr-langgraph.onrender.com/workflows/application/start \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id":1,
    "job_id":'$JOB_ID',
    "client_id":"TECH001"
  }'

# Expected: {"workflow_id":"wf_xxx","status":"running","message":"Workflow started"}
# Save workflow_id for tracking

# Check workflow status
curl https://bhiv-hr-langgraph.onrender.com/workflows/$WORKFLOW_ID/status

# Expected: {
#   "workflow_id":"wf_xxx",
#   "status":"running|completed",
#   "progress_percentage":X,
#   "current_step":"...",
#   "steps_completed":X
# }
```

#### **4.2 Multi-Channel Notifications**
```bash
# Send test notification
curl -X POST https://bhiv-hr-langgraph.onrender.com/tools/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipient":"test@example.com",
    "message":"Test notification from BHIV HR",
    "channels":["email"],
    "template":"candidate_applied"
  }'

# Expected: {"status":"sent","channels_delivered":["email"],"message_id":"msg_xxx"}

# Test WhatsApp notification (if configured)
curl -X POST https://bhiv-hr-langgraph.onrender.com/tools/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipient":"+1234567890",
    "message":"Test WhatsApp from BHIV HR",
    "channels":["whatsapp"],
    "template":"interview_scheduled"
  }'

# Expected: {"status":"sent","channels_delivered":["whatsapp"]}
```

#### **4.3 RL Integration**
```bash
# Test RL prediction
curl -X POST https://bhiv-hr-langgraph.onrender.com/rl/predict \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id":1,
    "job_id":'$JOB_ID',
    "features":{"experience":5,"skills_match":0.8}
  }'

# Expected: {
#   "prediction":0.85,
#   "confidence":0.9,
#   "decision_type":"recommend",
#   "model_version":"v1.0.1"
# }

# Submit RL feedback
curl -X POST https://bhiv-hr-langgraph.onrender.com/rl/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id":1,
    "actual_outcome":"hired",
    "feedback_score":4.5,
    "feedback_source":"hr"
  }'

# Expected: {"status":"feedback_recorded","reward_signal":1.2}
```

**✅ PASS CRITERIA**: Workflows start and track progress, notifications send successfully, RL system responds

---

### **TEST SUITE 5: Portal User Interfaces (25 minutes)**

#### **5.1 HR Portal Testing**
```bash
# Open HR Portal
URL: https://bhiv-hr-portal-u670.onrender.com

# Test Steps:
1. Portal loads without authentication (internal tool)
2. Navigate through all sections:
   - Step 1: Create Jobs ✓
   - Step 2: Upload Candidates ✓  
   - Step 3: AI Matching ✓
   - Step 4: Values Assessment ✓
   - Step 5: Interview Scheduling ✓
   - Step 6: Job Offers ✓
   - Step 7: Export Reports ✓
3. Test job creation form
4. Test candidate upload (CSV)
5. Test AI matching with job selection
6. Test feedback submission
7. Test report export

# Expected: All features work, no errors, data persists
```

#### **5.2 Client Portal Testing**
```bash
# Open Client Portal
URL: https://bhiv-hr-client-portal-3iod.onrender.com

# Test Steps:
1. Login with: TECH001 / demo123
2. Verify dashboard loads with company data
3. Test job management:
   - Create new job posting ✓
   - View existing jobs ✓
   - Edit job details ✓
4. Test candidate review:
   - View matched candidates ✓
   - Review candidate profiles ✓
   - Request AI matching ✓
5. Test interview scheduling
6. Test offer management
7. Logout and verify session ends

# Expected: Full client workflow works, tenant isolation maintained
```

#### **5.3 Candidate Portal Testing**
```bash
# Open Candidate Portal  
URL: https://bhiv-hr-candidate-portal-abe6.onrender.com

# Test Steps:
1. Register new candidate account
2. Login with created credentials
3. Complete profile:
   - Personal information ✓
   - Skills and experience ✓
   - Education details ✓
4. Browse available jobs
5. Apply for jobs with cover letter
6. Track application status
7. Update profile information
8. Logout

# Expected: Complete candidate self-service workflow
```

**✅ PASS CRITERIA**: All portals load, authentication works, core workflows complete successfully

---

### **TEST SUITE 6: Integration & Cross-Service (15 minutes)**

#### **6.1 End-to-End Workflow**
```bash
# Complete hiring flow test
1. Create job via Gateway API ✓
2. Upload candidate via Gateway API ✓  
3. Trigger AI matching via Agent service ✓
4. Start workflow via LangGraph ✓
5. Send notifications via LangGraph ✓
6. Submit feedback via Gateway ✓
7. Create offer via Gateway ✓

# Verify data consistency across all services
```

#### **6.2 Service Communication**
```bash
# Test Gateway → Agent communication
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/1/top

# Verify: Gateway calls Agent service, returns AI results

# Test Gateway → LangGraph communication  
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/api/v1/webhooks/candidate-applied \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":1,"job_id":1}'

# Verify: Gateway triggers LangGraph workflow

# Test LangGraph integration
curl https://bhiv-hr-langgraph.onrender.com/test-integration

# Expected: {"status":"success","services_connected":["gateway","agent","database"]}
```

#### **6.3 Database Consistency**
```bash
# Verify data consistency across services
# Check that all services see same data

# Gateway candidate count
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates/stats

# Agent candidate access
curl https://bhiv-hr-agent-nhgg.onrender.com/test-db

# LangGraph database access
curl https://bhiv-hr-langgraph.onrender.com/health

# Expected: All services report consistent data counts
```

**✅ PASS CRITERIA**: Services communicate properly, data consistency maintained, workflows complete end-to-end

---

### **TEST SUITE 7: Performance & Load Testing (10 minutes)**

#### **7.1 Response Time Testing**
```bash
# Test API response times
time curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Expected: <500ms for list endpoints

time curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/match/1/top

# Expected: <2s for AI matching

time curl https://bhiv-hr-gateway-ltg0.onrender.com/health

# Expected: <100ms for health checks
```

#### **7.2 Concurrent Request Testing**
```bash
# Test concurrent requests (use Postman Runner or script)
# Send 10 concurrent requests to /v1/candidates/stats
# Expected: All requests succeed, no timeouts

# Test rate limiting
# Send 100 requests rapidly to same endpoint
# Expected: Rate limit kicks in at 60 requests/minute
```

#### **7.3 Load Testing**
```bash
# Use Postman Collection Runner:
1. Import postman_collection.json
2. Select "Gateway - Core API" folder
3. Set iterations: 50
4. Set delay: 100ms
5. Run collection

# Expected Results:
# - 0% failure rate
# - Average response time <1s
# - No timeouts or errors
```

**✅ PASS CRITERIA**: Response times within targets, system handles concurrent load, rate limiting works

---

### **TEST SUITE 8: Security & Tenant Isolation (20 minutes)**

#### **8.1 Tenant Isolation Testing**
```bash
# Login as TECH001 client
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/client/login \
  -H "Content-Type: application/json" \
  -d '{"client_id":"TECH001","password":"demo123"}'
# Save JWT as TECH001_TOKEN

# Login as different client (if available)
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/client/login \
  -H "Content-Type: application/json" \
  -d '{"client_id":"STARTUP01","password":"demo123"}'
# Save JWT as STARTUP01_TOKEN

# Test cross-tenant access (should fail)
# Try to access TECH001 jobs with STARTUP01 token
curl -H "Authorization: Bearer $STARTUP01_TOKEN" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs

# Expected: Only see STARTUP01 jobs, not TECH001 jobs
```

#### **8.2 Authorization Testing**
```bash
# Test endpoint access with different auth types

# API Key access (should work for all)
curl -H "Authorization: Bearer $API_KEY" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Client JWT access (should work for client endpoints)
curl -H "Authorization: Bearer $CLIENT_JWT" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs

# No auth access (should fail for protected endpoints)
curl https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates
# Expected: 401 Unauthorized
```

#### **8.3 Input Security Testing**
```bash
# SQL Injection test
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/security/test-input-validation \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input_data":"1; DROP TABLE candidates; --"}'

# Expected: {"validation_result":"BLOCKED","threats_detected":["SQL injection attempt detected"]}

# XSS test
curl -X POST https://bhiv-hr-gateway-ltg0.onrender.com/v1/security/test-input-validation \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input_data":"<img src=x onerror=alert(1)>"}'

# Expected: Input sanitized and blocked
```

**✅ PASS CRITERIA**: Tenant isolation enforced, authorization works correctly, security attacks blocked

---

## 🚨 **CRITICAL VALIDATION POINTS**

### **Must Verify These Work:**
1. ✅ **All 111 endpoints respond** (use Postman collection)
2. ✅ **AI matching returns real scores** (not random numbers)
3. ✅ **Notifications actually send** (check email/WhatsApp delivery)
4. ✅ **Tenant isolation enforced** (clients can't see each other's data)
5. ✅ **Database transactions work** (bulk operations don't leave partial data)
6. ✅ **Error handling graceful** (no system crashes on invalid input)

### **Must Verify These Are Mocked:**
1. ⚠️ **RL training is mocked** (returns fake model versions)
2. ⚠️ **HR user authentication missing** (only API key works)
3. ⚠️ **File uploads not implemented** (resume_path fields exist but no upload)
4. ⚠️ **Advanced AI features limited** (basic matching only)

---

## 📊 **TEST RESULTS TEMPLATE**

### **Test Execution Summary**
```
Executed By: Vinayak
Date: ___________
Environment: Production/Local
Duration: _____ minutes

Test Suite Results:
[ ] Suite 1: Core System (15 min) - PASS/FAIL
[ ] Suite 2: Authentication (20 min) - PASS/FAIL  
[ ] Suite 3: Business Logic (25 min) - PASS/FAIL
[ ] Suite 4: Workflows (20 min) - PASS/FAIL
[ ] Suite 5: Portals (25 min) - PASS/FAIL
[ ] Suite 6: Integration (15 min) - PASS/FAIL
[ ] Suite 7: Performance (10 min) - PASS/FAIL
[ ] Suite 8: Security (20 min) - PASS/FAIL

Overall Result: PASS/FAIL
Critical Issues Found: _____
Recommendations: _____
```

### **Issue Reporting Template**
```
Issue ID: TST-001
Severity: Critical/High/Medium/Low
Component: Gateway/Agent/LangGraph/Portal
Description: _____
Steps to Reproduce: _____
Expected Result: _____
Actual Result: _____
Screenshots/Logs: _____
```

---

## 🎯 **SUCCESS CRITERIA**

### **System Ready for Production If:**
- ✅ All 8 test suites pass
- ✅ No critical security vulnerabilities
- ✅ Performance within acceptable limits
- ✅ All portals functional
- ✅ Tenant isolation enforced
- ✅ Error handling graceful
- ✅ Documentation accurate

### **Escalation Triggers:**
- ❌ Any test suite fails completely
- ❌ Security vulnerabilities found
- ❌ Data corruption detected
- ❌ System crashes or becomes unresponsive
- ❌ Cross-tenant data leakage

---

## 📞 **SUPPORT & ESCALATION**

### **For Testing Issues:**
- **Documentation**: All handover docs in `/handover/` directory
- **API Reference**: https://bhiv-hr-gateway-ltg0.onrender.com/docs
- **Postman Collection**: `handover/postman_collection.json`
- **Known Issues**: `handover/KNOWN_GAPS.md`

### **Escalation Contacts:**
- **Critical Issues**: Shashank (System Architect) - Immediate response
- **Security Issues**: Security Team - 1 hour response
- **Performance Issues**: Backend Team - 2 hours response

---

**END OF HOW_TO_TEST.md**

*This document provides complete testing procedures for independent validation of the BHIV HR Platform. Follow all test suites to ensure system readiness for production use.*


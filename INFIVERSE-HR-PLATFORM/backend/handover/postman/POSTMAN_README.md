# BHIV HR Platform - Postman Testing Suite

## Overview
Complete Postman collection with all **111 endpoints** organized by service with enhanced testing capabilities.

**Files**:
- `postman/postman_collection.json` - Complete endpoint collection
- `postman/bhiv-local-env.json` - Environment variables
- `postman/complete-enhanced-tests.js` - Advanced test scripts (22 tests)
- `postman/enhanced-tests.js` - Basic test scripts (10 tests)
- `postman/README.md` - Setup guide

## Endpoints Breakdown
- **Gateway API**: 88 endpoints (verified)
- **AI Agent API**: 6 endpoints (verified)
- **LangGraph API**: 25 endpoints (documented)

## Collection Structure

### Gateway API (88 endpoints)
1. **GW-Auth** (4): Setup 2FA, Verify 2FA, Login, 2FA Status
2. **GW-AI** (2): Test Communication, Gemini Analyze
3. **GW-Workflows** (7): Trigger, Status, List, Health, 3 Webhooks
4. **GW-RL** (4): Predict, Feedback, Analytics, Performance
5. **GW-Monitor** (3): Metrics, Health Detail, Dashboard
6. **GW-Core** (5): OpenAPI, Docs, Root, Health, Test DB
7. **GW-Jobs** (2): Create, List
8. **GW-Candidates** (6): List, Stats, Search, By Job, By ID, Bulk
9. **GW-Analytics** (4): Analytics Schema, Analytics Export, DB Schema, Job Export
10. **GW-Matching** (2): Top Matches, Batch
11. **GW-Assessment** (6): Submit/Get Feedback, List/Schedule Interviews, Create/List Offers
12. **GW-Client** (2): Register, Login
13. **GW-Security** (12): Rate Limit, Blocked IPs, Input Validation, Email/Phone Validation, Headers, Pentest
14. **GW-CSP** (4): Report, Violations, Policies, Test Policy
15. **GW-2FA** (8): Setup, Verify, Login, Status, Disable, Backup Codes, Test Token, QR Code
16. **GW-Password** (12): Validate, Generate, Policy, Change, Strength, Tips (both /v1/auth/password/ and /v1/password/ versions)
17. **GW-Candidate Portal** (5): Register, Login, Update Profile, Apply, Applications

### AI Agent API (6 endpoints)
1. **Agent-Core** (3): Root, Health, Test DB
2. **Agent-Matching** (3): Match, Batch Match, Analyze

### LangGraph API (25 endpoints)
1. **LangGraph-Core** (2): Root, Health
2. **LangGraph-Workflows** (5): Start, Status, Resume, List, Stats
3. **LangGraph-Notifications** (9): Send, Email, WhatsApp, Telegram, WA Buttons, Auto Sequence, Trigger WF, Bulk, WH WhatsApp
4. **LangGraph-RL** (8): Predict, Feedback, Analytics, Performance, History, Retrain, Perf All, Monitor
5. **LangGraph-Test** (1): Integration

## Step-by-Step Testing Guide

### Step 1: Setup Postman
1. **Download Postman**: Get from https://www.postman.com/downloads/
2. **Install and Open** Postman application
3. **Create Account** (optional but recommended)

### Step 2: Import Collection
1. **Open Postman**
2. **Click File menu** (top left) → **Import...** (Ctrl+O)
   - OR click the **Import** button in the main interface
3. **Select "Upload Files"** tab
4. **Choose file** → Navigate to `handover/postman/postman_collection.json`
5. **Click Import** → Collection appears in left sidebar
6. **Verify**: You should see "BHIV HR Platform - Complete API Collection (111 Endpoints)" in Collections

### Step 3A: Environment Setup - Manual Variables (Recommended)
1. **Click Environments** (left sidebar, gear icon)
2. **Click "+" to create new environment**
3. **Name it**: "BHIV HR Production"
4. **Add these variables for local testing**:
   ```
   Variable Name: gw
   Initial Value: http://localhost:8000
   Current Value: http://localhost:8000
   
   Variable Name: ag  
   Initial Value: http://localhost:9000
   Current Value: http://localhost:9000
   
   Variable Name: lg
   Initial Value: http://localhost:9001
   Current Value: http://localhost:9001
   
   Variable Name: API_KEY_SECRET
   Initial Value: prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o
   Current Value: prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o
   
   Variable Name: api_key_secret
   Initial Value: prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o
   Current Value: prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o
   ```
   **Note**: Add all 40 variables from `bhiv-local-env.json` or use JSON import instead.
5. **Save Environment**
6. **Select Environment** from dropdown (top right corner)

### Step 3B: Environment Setup - Using JSON File Import (Recommended)
1. **Use the provided JSON environment file** (`postman/bhiv-local-env.json`):
   - **File location**: `handover/postman/bhiv-local-env.json`
   - **Contains**: All 47 environment variables from .env file
   - **Pre-configured**: Production values with localhost URLs
   - **TOTP Code**: Current valid code (582299)

2. **Import JSON file to Postman**:
   - **Click Environments** (left sidebar, gear icon)
   - **Click "Import"** button
   - **Select file**: `handover/postman/bhiv-local-env.json`
   - **Postman imports environment** "BHIV HR Local Development" with all variables
   - **Select the environment** from dropdown (top right)

   **✅ Recommended**: This is the fastest method with all variables included!

### Step 3C: Environment Setup - Copy from .env (Alternative)
1. **Create .env file** for reference:
   ```bash
   # Local Development Environment
   gw=http://localhost:8000
   ag=http://localhost:9000
   lg=http://localhost:9001
   api_key_secret=test-api-key
   ```

2. **Manually copy values to Postman**:
   - **Create new environment** (Step 3A method)
   - **Copy values** from .env file to Postman variables
   - **Faster than typing** but requires manual copying

### Step 3D: Local Development Setup
**Docker Commands for Local Testing:**

**1. STOP (keeps database)**
```bash
docker-compose -f docker-compose.production.yml down
```

**2. CLEANUP (Safe - keeps database)**
```bash
# Remove build cache
docker builder prune --all --force

# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Check disk usage
docker system df
```

**3. REBUILD & START**
```bash
docker-compose -f docker-compose.production.yml up -d --build
```

**Verify services are running:**
```bash
curl http://localhost:8000/health  # Gateway
curl http://localhost:9000/health  # Agent  
curl http://localhost:9001/health  # LangGraph
```

**Local Service URLs:**
- **Gateway**: http://localhost:8000
- **Agent**: http://localhost:9000  
- **LangGraph**: http://localhost:9001
- **HR Portal**: http://localhost:8501
- **Client Portal**: http://localhost:8502
- **Candidate Portal**: http://localhost:8503

### Step 4: First Test - Health Check
1. **Expand Collection** → **GW-Core (5)** folder
2. **Click "Health"** request
3. **Verify URL shows**: `{{gw}}/health` (variables auto-populate)
4. **Click Send** button (blue button)
5. **Check Response**:
   - Status: `200 OK`
   - Body: `{"status": "healthy"}`

### Step 5: Test with Authentication
1. **Go to GW-Auth (4)** folder
2. **Click "Login"** request
3. **Check Body tab** → Should show demo credentials
4. **Click Send**
5. **Copy JWT token** from response
6. **Save token**: Add new environment variable `jwt_token`

### Step 7: Enhanced Testing (Optional)
1. **Add Test Scripts** to collection:
   - **Copy content** from `postman/complete-enhanced-tests.js`
   - **Go to Collection** → **Scripts** → **Post-response**
   - **Paste the script** (22 comprehensive tests)
   - **Save collection**

2. **Run Collection with Tests**:
   - **Right-click collection** → **Run collection**
   - **Configure settings**:
     - Iterations: 1
     - Delay: 20000ms (for AI endpoints)
     - Keep variable values: ✅
     - Persist responses: ✅
   - **Run and review** test results

3. **Test Features**:
   - Security validation
   - Performance monitoring
   - Data integrity checks
   - Business logic validation
   - Error handling verification

## Import Instructions
1. Open Postman
2. Click **Import** button
3. Select `postman/postman_collection.json`
4. Import `postman/bhiv-local-env.json` as environment
5. Collection will appear in sidebar with organized folders
6. All 111 endpoints will be ready to use with authentication

## Environment Variables

### Local Development Environment
For **local testing**, use these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `GATEWAY_SERVICE_URL` | http://localhost:8000 | Local Gateway URL |
| `AGENT_SERVICE_URL` | http://localhost:9000 | Local Agent URL |
| `LANGGRAPH_SERVICE_URL` | http://localhost:9001 | Local LangGraph URL |
| `API_KEY_SECRET` | prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o | Production API key |
| `test_totp_code` | 582299 | Current valid TOTP code |
| `client_id` | TECH001 | Demo client ID |
| `client_password` | demo123 | Demo client password |

**✅ Complete Setup**: Import `handover/postman/bhiv-local-env.json` for all 47 variables

### JSON Environment File Template
Use the provided `handover/postman/bhiv-local-env.json` file:
- **47 environment variables** from your .env file
- **Production API keys** and secrets
- **Localhost URLs** for local testing
- **Current TOTP code** (582299)
- **Ready for import** into Postman

**File**: `handover/postman/bhiv-local-env.json`
```json
{
  "id": "bhiv-hr-local-env",
  "name": "BHIV HR Local Development",
  "values": [
    {"key": "GATEWAY_SERVICE_URL", "value": "http://localhost:8000", "enabled": true},
    {"key": "AGENT_SERVICE_URL", "value": "http://localhost:9000", "enabled": true},
    {"key": "LANGGRAPH_SERVICE_URL", "value": "http://localhost:9001", "enabled": true},
    {"key": "API_KEY_SECRET", "value": "prod_api_key_...", "enabled": true, "type": "secret"},
    {"key": "test_totp_code", "value": "582299", "enabled": true},
    // ... 42 more variables
  ]
}
```

### .env File Template (For Reference)
Your project's `.env` file contains all production values:
```bash
# Local Development with Production Values
API_KEY_SECRET=prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o
JWT_SECRET_KEY=prod_jwt_Ova9A8L-OU4uIcAero0v3ZLQRckNr3xBDuO0OXF6uwA
GATEWAY_SERVICE_URL=http://localhost:8000
AGENT_SERVICE_URL=http://localhost:9000
LANGGRAPH_SERVICE_URL=http://localhost:9001
# ... 35 more variables
```

**✅ Use JSON Import**: All variables are pre-configured in `postman/bhiv-local-env.json`

## Authentication Methods

### 1. API Key (Primary)
```
Authorization: Bearer {{API_KEY_SECRET}}
```
Used for most endpoints.

### 2. Client JWT
```
Authorization: Bearer {{client_jwt}}
```
Get token from `/v1/client/login` endpoint.

### 3. Candidate JWT
```
Authorization: Bearer {{candidate_jwt}}
```
Get token from `/v1/candidate/login` endpoint.

### 4. 2FA TOTP
```
{"totp_code": "{{test_totp_code}}"}
```
Current valid code: 582299

## Enhanced Testing Features

### Test Scripts Available
1. **complete-enhanced-tests.js** (22 tests):
   - Core validations (status, response time, JSON)
   - Method-specific validations (GET/POST/PUT/DELETE)
   - Authentication endpoint validation
   - HR platform specific validations
   - AI/ML service validations
   - Security issue detection
   - Performance monitoring
   - Data integrity checks
   - Business logic validation
   - Error handling verification

2. **enhanced-tests.js** (10 tests):
   - Basic security checks
   - Performance monitoring
   - Data validation
   - Error handling

### How to Use Test Scripts
1. **Copy script content** from desired .js file
2. **Go to Collection** → **Scripts** → **Post-response**
3. **Paste the script**
4. **Save collection**
5. **Run collection** to see test results

### Test Results
- **Console logs** show warnings and errors
- **Test tab** shows pass/fail status
- **Performance metrics** logged automatically
- **Security issues** flagged in console

## Quick Start

### Test System Health
1. Run `Gateway - Core API > Health Check`
2. Expected: `{"status": "healthy"}`

### Create Job
1. Run `Gateway - Jobs > Create Job`
2. Note the `job_id` from response

### List Candidates
1. Run `Gateway - Candidates > List Candidates`
2. View all candidates with pagination

### AI Matching
1. Run `Gateway - AI Matching > Get Top Matches`
2. Replace `{job_id}` with actual job ID
3. View AI-ranked candidates

## Endpoint Categories

### Gateway (88)
**Authentication & Security** (32): Auth (4), 2FA (8), Password (12), Security (12)
**Core Operations** (25): Monitor (3), Core (5), Jobs (2), Candidates (6), Analytics (4), Matching (2), Assessment (6)
**Portals** (9): Client (2), Candidate Portal (5), CSP (4)
**Integrations** (18): AI (2), Workflows (7), RL (4)

### Agent (6)
**Service Management** (3): Core endpoints
**AI Matching** (3): Match, Batch, Analyze

### LangGraph (25)
**Orchestration** (7): Core (2), Workflows (5)
**Communication** (9): Multi-channel notifications
**ML/RL** (8): Reinforcement learning
**Testing** (1): Integration test

## Common Use Cases

### 1. Complete Hiring Flow
```
1. POST /v1/jobs - Create job
2. POST /v1/candidates/bulk - Import candidates
3. GET /v1/match/{job_id}/top - Get AI matches
4. POST /v1/interviews - Schedule interview
5. POST /v1/feedback - Submit feedback
6. POST /v1/offers - Extend offer
```

### 2. Client Portal Flow
```
1. POST /v1/client/register - Register company
2. POST /v1/client/login - Get JWT token
3. POST /v1/jobs - Create job posting
4. GET /v1/match/{job_id}/top - View matches
```

### 3. Candidate Portal Flow
```
1. POST /v1/candidate/register - Register account
2. POST /v1/candidate/login - Get JWT token
3. GET /v1/jobs - Browse jobs
4. POST /v1/candidate/apply - Apply for job
5. GET /v1/candidate/applications/{id} - Track status
```

### 4. AI Workflow Automation
```
1. POST /api/v1/webhooks/candidate-applied - Trigger workflow
2. GET /api/v1/workflow/status/{id} - Monitor progress
3. POST /tools/send-notification - Send notifications
```

## Troubleshooting Common Issues

### Issue 1: "Could not get response" (Local Testing)
**Solution**: Check if local services are running
```bash
# Check if Docker containers are running
docker ps

# If services not running, use proper startup sequence:
# 1. STOP (keeps database)
docker-compose -f docker-compose.production.yml down

# 2. CLEANUP (Safe - keeps database)
docker builder prune --all --force
docker container prune -f
docker image prune -a -f

# 3. REBUILD & START
docker-compose -f docker-compose.production.yml up -d --build

# Test health endpoints
curl http://localhost:8000/health  # Gateway
curl http://localhost:9000/health  # Agent
curl http://localhost:9001/health  # LangGraph
```

### Issue 2: "Connection Refused"
**Solution**: Verify correct ports
- Gateway should be on port **8000** (not 9000)
- Agent should be on port **9000** (not 8001)  
- LangGraph should be on port **9001** (not 8002)
- Check `docker-compose.production.yml` for port mappings

### Issue 2: "401 Unauthorized"
**Solution**: Check API key for local environment
1. Use a simple API key like `test-api-key` for local development
2. Update `api_key_secret` variable in your environment
3. Ensure Authorization header is set to `Bearer {{api_key_secret}}`

### Issue 3: "404 Not Found"
**Solution**: Check endpoint URL and local service status
- Verify environment variables point to correct localhost URLs
- Ensure all services are running: `docker ps`
- Check endpoint paths match the text files exactly

### Issue 4: "Port Already in Use"
**Solution**: Proper cleanup and restart
```bash
# 1. STOP all containers (keeps database)
docker-compose -f docker-compose.production.yml down

# 2. Check what's using the ports
netstat -ano | findstr :8000
netstat -ano | findstr :9000
netstat -ano | findstr :9001

# 3. CLEANUP (Safe - keeps database)
docker builder prune --all --force
docker container prune -f
docker image prune -a -f

# 4. REBUILD & START
docker-compose -f docker-compose.production.yml up -d --build
```

## Testing Endpoints

### Security Testing
- Run all endpoints in `Gateway - Security` folder
- Tests XSS, SQL injection, input validation

### Performance Testing
- Use Postman Runner for load testing
- Set iterations: 100+
- Monitor response times

### Integration Testing
- Run `LangGraph - Integration > Test Integration`
- Validates all services connected

## Rate Limits
- Default: 60 requests/minute
- Premium: 300 requests/minute
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## Error Handling
All endpoints return standard format:
```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Detailed description",
  "timestamp": "2024-12-09T13:37:00Z"
}
```

## Verification

After import, verify the collection:
```bash
# Count folders (should be 23)
Gateway: 17 folders
Agent: 2 folders
LangGraph: 5 folders

# Count endpoints (should be 111)
Gateway: 88 endpoints
Agent: 6 endpoints
LangGraph: 25 endpoints
```

## Support
- **Local API Documentation**: http://localhost:8000/docs (Gateway)
- **GitHub**: https://github.com/Shashank-0208/BHIV-HR-PLATFORM
- **Issues**: Create GitHub issue with `[API]` tag

## Version History
- **v4.3.1** (2024-12-22): Enhanced testing suite, 111 endpoints, complete environment setup
- **v4.0.0** (2024-12-18): RL integration complete, advanced test scripts
- **v3.0.0** (2024-12-15): LangGraph workflows, multi-channel notifications
- **v2.0.0** (2024-11-15): LangGraph workflows added
- **v1.0.0** (2024-10-01): Initial release

# ❓ BHIV HR Platform - FAQ & Operations Guide

**Version**: 3.0.0  
**Last Updated**: November 21, 2025  
**Target Audience**: Operations Team, Support Staff, Developers  
**Platform**: Windows + Docker + Render Cloud  
**Status**: ✅ Production Ready

> **2026-06-03 — Demo login archived:** Client ID `TECH001` / password `demo123` is **not** valid on the current production database. Use real accounts on Vercel/Render or local seed (`backend/seed_mongodb.py`). Canonical doc: `docs/DEMO_CREDENTIALS_STATUS.md`.

---

## 📋 Table of Contents

### **Getting Started**
1. [How do I access the platform?](#q1-how-do-i-access-the-platform)
2. [How do I start/stop services locally?](#q2-how-do-i-startstop-services-locally)
3. [What are the demo credentials?](#q3-what-are-the-demo-credentials)
4. [How do I check if services are running?](#q4-how-do-i-check-if-services-are-running)

### **Service Management**
5. [Service won't start - what do I do?](#q5-service-wont-start---what-do-i-do)
6. [How do I restart a single service?](#q6-how-do-i-restart-a-single-service)
7. [How do I view service logs?](#q7-how-do-i-view-service-logs)
8. [Services are slow - how to improve performance?](#q8-services-are-slow---how-to-improve-performance)

### **Database Operations**
9. [How do I connect to the database?](#q9-how-do-i-connect-to-the-database)
10. [How do I backup the database?](#q10-how-do-i-backup-the-database)
11. [How do I restore from backup?](#q11-how-do-i-restore-from-backup)
12. [Database connection errors - how to fix?](#q12-database-connection-errors---how-to-fix)

### **Data Management**
13. [How do I load candidates into the system?](#q13-how-do-i-load-candidates-into-the-system)
14. [How do I create sample jobs?](#q14-how-do-i-create-sample-jobs)
15. [Bulk import fails halfway - what to do?](#q15-bulk-import-fails-halfway---what-to-do)
16. [How do I export candidate data?](#q16-how-do-i-export-candidate-data)

### **AI & Matching**
17. [AI matching not working - how to fix?](#q17-ai-matching-not-working---how-to-fix)
18. [How do I test AI matching manually?](#q18-how-do-i-test-ai-matching-manually)
19. [AI rank stays null - what's wrong?](#q19-ai-rank-stays-null---whats-wrong)
20. [How does the Phase 3 AI engine work?](#q20-how-does-the-phase-3-ai-engine-work)

### **Authentication & Security**
21. [Authentication failing - how to fix?](#q21-authentication-failing---how-to-fix)
22. [How do I get/reset API keys?](#q22-how-do-i-getreset-api-keys)
23. [How do I run security audits?](#q23-how-do-i-run-security-audits)
24. [Rate limiting errors - what to do?](#q24-rate-limiting-errors---what-to-do)

### Portal Issues
25. [Portal not loading - how to fix?](#q25-portal-not-loading---how-to-fix)

### Multi-Tenancy and Scaling
26. [Can this support multiple companies?](#q26-can-this-support-multiple-companies)
27. [Is the system production-ready for multi-tenancy?](#q27-is-the-system-production-ready-for-multi-tenancy)

### Reusability and Framework
28. [Is the hiring loop reusable for other purposes?](#q28-is-the-hiring-loop-reusable-for-other-purposes)
29. [How do I integrate this into my own system?](#q29-how-do-i-integrate-this-into-my-own-system)

### Demo and Presentation
30. [What should I demonstrate in a demo?](#q30-what-should-i-demonstrate-in-a-demo)
31. [What are the known limitations for demos?](#q31-what-are-the-known-limitations-for-demos)
26. [Client portal login fails - what to do?](#q26-client-portal-login-fails---what-to-do)
27. [Dashboard shows stale data - how to refresh?](#q27-dashboard-shows-stale-data---how-to-refresh)
28. [How do I explore portal features?](#q28-how-do-i-explore-portal-features)

### **Communication & Notifications**
29. [WhatsApp messages not sending - how to fix?](#q29-whatsapp-messages-not-sending---how-to-fix)
30. [Email notifications not working - what to do?](#q30-email-notifications-not-working---what-to-do)
31. [How do I test notifications manually?](#q31-how-do-i-test-notifications-manually)
32. [LangGraph workflows not triggering - how to fix?](#q32-langgraph-workflows-not-triggering---how-to-fix)

### **Monitoring & Diagnostics**
33. [How do I monitor system health?](#q33-how-do-i-monitor-system-health)
34. [How do I check system performance?](#q34-how-do-i-check-system-performance)
35. [Where are the logs located?](#q35-where-are-the-logs-located)
36. [How do I use diagnostic tools?](#q36-how-do-i-use-diagnostic-tools)

### **Deployment & Updates**
37. [How do I deploy to production?](#q37-how-do-i-deploy-to-production)
38. [Deployment failed - how to rollback?](#q38-deployment-failed---how-to-rollback)
39. [How do I update dependencies?](#q39-how-do-i-update-dependencies)
40. [How do I apply database migrations?](#q40-how-do-i-apply-database-migrations)

### **Emergency & Troubleshooting**
41. [System completely down - what to do?](#q41-system-completely-down---what-to-do)
42. [Data corruption suspected - immediate steps?](#q42-data-corruption-suspected---immediate-steps)
43. [When should I escalate to Shashank?](#q43-when-should-i-escalate-to-shashank)
44. [How do I report an incident?](#q44-how-do-i-report-an-incident)

---

## 🚀 Getting Started

### Q1: How do I access the platform?

**Answer**: There are three ways to access the BHIV HR Platform:

#### **Option 1: Live Production System (Recommended - No Setup)**
```yaml
Access URLs:
  HR Portal: https://bhiv-hr-portal-u670.onrender.com
  Client Portal: https://bhiv-hr-client-portal-3iod.onrender.com
  Candidate Portal: https://bhiv-hr-candidate-portal-abe6.onrender.com
  API Gateway: https://bhiv-hr-gateway-ltg0.onrender.com/docs
  AI Agent: https://bhiv-hr-agent-nhgg.onrender.com/docs
  LangGraph: https://bhiv-hr-langgraph.onrender.com/docs

Demo Credentials:
  Client Portal: ARCHIVED — see docs/DEMO_CREDENTIALS_STATUS.md (was TECH001 / demo123)
  API Key: Check .env file or contact admin

Status: ✅ All services operational 24/7
Cost: Free to use
Setup Time: 0 minutes
```

#### **Option 2: Local Development (Windows BAT Scripts)**
```bash
# Step 1: First-time setup
setup_first_time.bat

# Step 2: Start all services
start_all_services.bat

# Step 3: Access locally
HR Portal: http://localhost:8501
Client Portal: http://localhost:8502
Candidate Portal: http://localhost:8503
API Gateway: http://localhost:8000/docs

Setup Time: 10 minutes
Requirements: Python 3.12.7, Windows 10/11
```

#### **Option 3: Local Development (Docker)**
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Wait 30 seconds for initialization
sleep 30

# Access locally (same URLs as Option 2)

Setup Time: 5 minutes
Requirements: Docker Desktop, 8GB RAM
```

**Recommendation**: Use live production system for immediate access, local development for testing changes.

---

### Q2: How do I start/stop services locally?

**Answer**: Multiple methods available depending on your setup:

#### **Method 1: Windows BAT Scripts (Easiest)**
```bash
# Start all services
start_all_services.bat
# Opens 6 command windows, one per service
# Wait 60 seconds for initialization

# Check if running
check_services.bat
# Shows status of all services

# Stop all services
stop_all_services.bat
# Closes all service windows and frees ports
```

#### **Method 2: Docker Compose (Recommended)**
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Stop all services
docker-compose -f docker-compose.production.yml down

# Restart specific service
docker-compose -f docker-compose.production.yml restart gateway
```

#### **Method 3: Individual Service (Manual)**
```bash
# Start Gateway
cd services/gateway
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start Agent
cd services/agent
python -m uvicorn app:app --host 0.0.0.0 --port 9000

# Start HR Portal
cd services/portal
streamlit run app.py --server.port 8501

# Stop: Close terminal or press Ctrl+C
```

**Troubleshooting**:
```bash
# If port already in use (Windows)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# If port already in use (Linux/Mac)
lsof -i :8000
kill -9 <PID>
```

---

### Q3: What are the demo credentials?

**Answer**: **Archived (2026-06-03).** The legacy client demo `TECH001` / `demo123` is **not** in the live MongoDB used by Render/Vercel. Do not use it for production or acceptance testing.

- **Production:** Owner-provisioned or registered client/recruiter/admin accounts.
- **Local dev:** Run `backend/seed_mongodb.py` against your dev database, or set `E2E_CLIENT_ID` / `E2E_CLIENT_PASSWORD` for tests.
- **Details:** `docs/DEMO_CREDENTIALS_STATUS.md`

#### **Client Portal Login (historical reference only)**
```yaml
# ARCHIVED — invalid on current production DB
URL: https://bhiv-hr-client-portal-3iod.onrender.com
Username: TECH001   # archived
Password: demo123   # archived
Access Level: Full client access (when seeded locally)
Features: Job posting, candidate review, interview scheduling
```

#### **HR Portal**
```yaml
URL: https://bhiv-hr-portal-u670.onrender.com
Login: No authentication required (internal tool)
Access Level: Full HR access
Features: All HR workflow steps, AI matching, reporting
```

#### **Candidate Portal**
```yaml
URL: https://bhiv-hr-candidate-portal-abe6.onrender.com
Login: Register new account or use existing
Access Level: Candidate access
Features: Job search, application, profile management
```

#### **API Testing**
```bash
# Get API key from .env file
API_KEY_SECRET=<YOUR_API_KEY>

# Test API
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Or use interactive API docs
https://bhiv-hr-gateway-ltg0.onrender.com/docs
```

#### **Database Access (Local)**
```yaml
Host: localhost
Port: 5432
Database: bhiv_hr
Username: bhiv_user
Password: Check .env file (POSTGRES_PASSWORD)

Connection String:
postgresql://bhiv_user:password@localhost:5432/bhiv_hr
```

**Security Note**: Demo credentials are for testing only. Change passwords in production.

---

### Q4: How do I check if services are running?

**Answer**: Multiple methods to verify service health:

#### **Method 1: Quick Health Check Script**
```bash
# Windows
check_services.bat

# Expected output:
# ✅ Gateway: http://localhost:8000 - Healthy
# ✅ Agent: http://localhost:9000 - Healthy
# ✅ LangGraph: http://localhost:9001 - Healthy
# ✅ HR Portal: http://localhost:8501 - Running
# ✅ Client Portal: http://localhost:8502 - Running
# ✅ Candidate Portal: http://localhost:8503 - Running
```

#### **Method 2: Manual Health Checks**
```bash
# Gateway
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"BHIV HR Gateway","version":"4.2.0"}

# Agent
curl http://localhost:9000/health
# Expected: {"status":"healthy","ai_engine":"operational"}

# LangGraph
curl http://localhost:9001/health
# Expected: {"status":"healthy","workflows":"operational"}

# Portals (should return HTTP 200)
curl -I http://localhost:8501
curl -I http://localhost:8502
curl -I http://localhost:8503
```

#### **Method 3: Docker Status**
```bash
# Check all containers
docker-compose -f docker-compose.production.yml ps

# Expected output:
# NAME                STATUS              PORTS
# bhiv-hr-gateway     Up 2 hours         0.0.0.0:8000->8000/tcp
# bhiv-hr-agent       Up 2 hours         0.0.0.0:9000->9000/tcp
# bhiv-hr-langgraph   Up 2 hours         0.0.0.0:9001->9001/tcp
# bhiv-hr-portal      Up 2 hours         0.0.0.0:8501->8501/tcp
# bhiv-hr-db          Up 2 hours         0.0.0.0:5432->5432/tcp

# Check resource usage
docker stats --no-stream
```

#### **Method 4: Production Health Checks**
```bash
# Check production services
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Detailed health check
curl https://bhiv-hr-gateway-ltg0.onrender.com/health/detailed

# Metrics dashboard
curl https://bhiv-hr-gateway-ltg0.onrender.com/metrics/dashboard
```

#### **Method 5: Service Connection Validator**
```bash
# Comprehensive validation
python tools/monitoring/service_connection_validator.py

# Output shows:
# - All service connections
# - Database connectivity
# - API endpoint availability
# - Response times
```

**Troubleshooting**:
- If service shows "Unhealthy": Check logs with `docker-compose logs <service>`
- If service not responding: Restart with `docker-compose restart <service>`
- If port not accessible: Check firewall and port availability

---

## 🔧 Service Management

### Q5: Service won't start - what do I do?

**Answer**: Follow this systematic troubleshooting approach:

#### **Step 1: Identify the Problem**
```bash
# Check which service is failing
docker-compose -f docker-compose.production.yml ps

# Check logs for error messages
docker-compose -f docker-compose.production.yml logs gateway --tail=50
docker-compose -f docker-compose.production.yml logs agent --tail=50
docker-compose -f docker-compose.production.yml logs langgraph --tail=50
```

#### **Step 2: Common Issues & Solutions**

**Issue A: Port Already in Use**
```bash
# Symptoms: "Address already in use" error

# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/Mac - Find and kill process
lsof -i :8000
kill -9 <PID>

# Restart service
docker-compose -f docker-compose.production.yml up -d gateway
```

**Issue B: Database Connection Error**
```bash
# Symptoms: "Connection refused" or "Connection timeout"

# Check if database is running
docker-compose -f docker-compose.production.yml ps db

# Start database if not running
docker-compose -f docker-compose.production.yml up -d db
sleep 10

# Test database connection
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT 1"

# Restart service after database is ready
docker-compose -f docker-compose.production.yml restart gateway
```

**Issue C: Missing Environment Variables**
```bash
# Symptoms: "Environment variable not set" error

# Check .env file exists
ls -la .env  # Linux/Mac
dir .env     # Windows

# Verify required variables
type .env | findstr DATABASE_URL  # Windows
grep DATABASE_URL .env            # Linux/Mac

# If missing, copy from template
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env with correct values
# Then restart services
docker-compose -f docker-compose.production.yml restart
```

**Issue D: Import/Dependency Error**
```bash
# Symptoms: "ModuleNotFoundError" or "ImportError"

# Rebuild container with fresh dependencies
docker-compose -f docker-compose.production.yml build gateway
docker-compose -f docker-compose.production.yml up -d gateway

# Or rebuild all services
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

**Issue E: Out of Memory**
```bash
# Symptoms: Container exits with code 137

# Check memory usage
docker stats --no-stream

# Increase memory limit
docker update --memory=1g bhiv-hr-gateway

# Or restart Docker Desktop to free memory
```

#### **Step 3: Nuclear Option (Fresh Start)**
```bash
# Stop everything
docker-compose -f docker-compose.production.yml down

# Remove volumes (CAUTION: deletes data)
docker-compose -f docker-compose.production.yml down -v

# Clean Docker system
docker system prune -a -f

# Start fresh
docker-compose -f docker-compose.production.yml up -d

# Wait for initialization
sleep 30

# Verify all services
check_services.bat
```

#### **Step 4: Check Service Dependencies**
```yaml
Startup Order (must follow):
  1. Database (db)
  2. Gateway (depends on db)
  3. Agent (depends on db)
  4. LangGraph (depends on db)
  5. Portals (depend on gateway)

# Start in correct order
docker-compose -f docker-compose.production.yml up -d db
sleep 10
docker-compose -f docker-compose.production.yml up -d gateway
sleep 10
docker-compose -f docker-compose.production.yml up -d agent langgraph
sleep 10
docker-compose -f docker-compose.production.yml up -d portal client_portal candidate_portal
```

**When to Escalate**: If service still won't start after all steps, escalate to Shashank with full logs.

---

### Q45: Docker networking issues - services can't communicate?

**Answer**: Troubleshooting Docker network connectivity:

#### **Issue: Services can't reach each other**
```bash
# Check Docker network
docker network ls
docker network inspect bhiv-hr-platform_default

# Verify all services on same network
docker-compose -f docker-compose.production.yml ps

# Test connectivity between services
docker-compose -f docker-compose.production.yml exec gateway ping db
docker-compose -f docker-compose.production.yml exec gateway curl http://agent:9000/health
```

#### **Solution 1: Recreate Network**
```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Remove network
docker network rm bhiv-hr-platform_default

# Restart services (network auto-created)
docker-compose -f docker-compose.production.yml up -d
```

#### **Solution 2: Use Service Names, Not localhost**
```yaml
# WRONG (in Docker)
AGENT_SERVICE_URL=http://localhost:9000

# CORRECT (in Docker)
AGENT_SERVICE_URL=http://agent:9000
```

#### **Solution 3: Check docker-compose.yml Network Config**
```yaml
services:
  gateway:
    networks:
      - bhiv-network
  agent:
    networks:
      - bhiv-network

networks:
  bhiv-network:
    driver: bridge
```

---

### Q46: Port conflicts on Windows - "Address already in use"?

**Answer**: Resolving Windows port conflicts:

#### **Find Process Using Port**
```cmd
# Check port 8000
netstat -ano | findstr :8000

# Output shows PID in last column:
# TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345
```

#### **Kill Process**
```cmd
# Kill by PID
taskkill /PID 12345 /F

# Or kill by name
taskkill /IM python.exe /F
taskkill /IM uvicorn.exe /F
```

#### **Common Port Conflicts**
```cmd
# Port 8000 (Gateway)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Port 27017 (MongoDB Atlas)
netstat -ano | findstr :5432
taskkill /PID <PID> /F

# Port 8501 (HR Portal)
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

#### **Prevent Conflicts**
```bash
# Use stop script before starting
stop_all_services.bat
sleep 5
start_all_services.bat

# Or use Docker (isolated ports)
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

#### **Change Ports if Needed**
```bash
# Edit .env file
GATEWAY_PORT=8080  # Instead of 8000
AGENT_PORT=9090    # Instead of 9000

# Restart services
```

---

### Q47: MongoDB Atlas connection string issues?

**Answer**: Troubleshooting DATABASE_URL format:

#### **Correct Format**
```bash
# Standard format
postgresql://username:password@host:port/database

# Local development
DATABASE_URL=postgresql://bhiv_user:password@localhost:5432/bhiv_hr

# Docker (use service name)
DATABASE_URL=postgresql://bhiv_user:password@db:5432/bhiv_hr

# Production (Render)
DATABASE_URL=postgresql://user:pass@host.render.com:5432/dbname?sslmode=require
```

#### **Common Mistakes**
```bash
# WRONG: Missing protocol
DATABASE_URL=bhiv_user:password@localhost:5432/bhiv_hr

# WRONG: Wrong protocol
DATABASE_URL=postgres://bhiv_user:password@localhost:5432/bhiv_hr

# WRONG: Special characters not encoded
DATABASE_URL=postgresql://user:p@ssw0rd@localhost:5432/db
# Should be: postgresql://user:p%40ssw0rd@localhost:5432/db
```

#### **Test Connection**
```bash
# Using psql
psql "postgresql://bhiv_user:password@localhost:5432/bhiv_hr"

# Using Python
python tools/database/database_url_checker.py

# Using Docker
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT 1"
```

#### **Encode Special Characters**
```python
# Python script to encode password
from urllib.parse import quote_plus

password = "p@ssw0rd!"
encoded = quote_plus(password)
print(f"postgresql://user:{encoded}@localhost:5432/db")
# Output: postgresql://user:p%40ssw0rd%21@localhost:5432/db
```

#### **SSL Mode for Production**
```bash
# Render requires SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Disable SSL for local (not recommended for production)
DATABASE_URL=postgresql://user:pass@localhost:5432/db?sslmode=disable
```

---

### Q48: Render deployment failures - how to debug?

**Answer**: Troubleshooting Render deployment issues:

#### **Check Build Logs**
```bash
# Via Render Dashboard:
# 1. Go to dashboard.render.com
# 2. Select failing service
# 3. Click "Logs" tab
# 4. Look for error messages in build phase
```

#### **Common Deployment Failures**

**Failure 1: Build Timeout**
```bash
# Symptom: "Build exceeded 15 minute timeout"
# Cause: Large dependencies, slow network

# Solution: Optimize requirements.txt
# Remove unused packages
# Use --no-cache-dir flag

# In Dockerfile:
RUN pip install --no-cache-dir -r requirements.txt
```

**Failure 2: Missing Environment Variables**
```bash
# Symptom: "KeyError: 'DATABASE_URL'"
# Cause: Environment variable not set in Render

# Solution:
# 1. Go to Service → Environment
# 2. Add missing variables
# 3. Click "Save Changes"
# 4. Service auto-redeploys
```

**Failure 3: Port Binding Error**
```bash
# Symptom: "Address already in use"
# Cause: Hardcoded port instead of $PORT

# WRONG:
uvicorn app:app --host 0.0.0.0 --port 8000

# CORRECT (Render sets PORT automatically):
import os
port = int(os.getenv("PORT", 8000))
uvicorn app:app --host 0.0.0.0 --port port
```

**Failure 4: Database Connection Timeout**
```bash
# Symptom: "Connection timeout" during startup
# Cause: Database not ready, wrong connection string

# Solution: Add connection retry logic
import time
from sqlalchemy import create_engine

for attempt in range(5):
    try:
        engine = create_engine(DATABASE_URL)
        engine.connect()
        break
    except Exception as e:
        if attempt < 4:
            time.sleep(5)
        else:
            raise
```

**Failure 5: Dependency Conflicts**
```bash
# Symptom: "ERROR: Cannot install package X and Y"
# Cause: Incompatible package versions

# Solution: Pin exact versions in requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23

# Test locally first:
pip install -r requirements.txt
```

#### **Health Check Failures**
```bash
# Symptom: "Service unhealthy" after deployment
# Cause: Health check endpoint not responding

# Verify health endpoint works:
curl https://your-service.onrender.com/health

# Check Render health check settings:
# Path: /health
# Expected Status: 200
# Timeout: 30 seconds
```

#### **Rollback Failed Deployment**
```bash
# Via Render Dashboard:
# 1. Go to Service → Deploys
# 2. Find last successful deployment
# 3. Click "Rollback" button
# 4. Confirm rollback
```

#### **Manual Redeploy**
```bash
# Trigger manual deployment:
# 1. Go to Service → Manual Deploy
# 2. Select branch (usually 'main')
# 3. Click "Deploy Latest Commit"
# 4. Monitor logs for errors
```

#### **Check Service Status**
```bash
# Production health checks:
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Expected response:
{"status": "healthy", "service": "...", "version": "..."}
```

---

### Q6: How do I restart a single service?

**Answer**: Multiple methods depending on your setup:

#### **Method 1: Docker Compose (Recommended)**
```bash
# Restart specific service
docker-compose -f docker-compose.production.yml restart gateway
docker-compose -f docker-compose.production.yml restart agent
docker-compose -f docker-compose.production.yml restart langgraph
docker-compose -f docker-compose.production.yml restart portal
docker-compose -f docker-compose.production.yml restart client_portal
docker-compose -f docker-compose.production.yml restart candidate_portal

# Verify service restarted
docker-compose -f docker-compose.production.yml ps gateway

# Check logs after restart
docker-compose -f docker-compose.production.yml logs -f gateway
```

#### **Method 2: Stop and Start**
```bash
# Stop service
docker-compose -f docker-compose.production.yml stop gateway

# Start service
docker-compose -f docker-compose.production.yml start gateway

# Or combined
docker-compose -f docker-compose.production.yml stop gateway && \
docker-compose -f docker-compose.production.yml start gateway
```

#### **Method 3: Rebuild and Restart (if code changed)**
```bash
# Rebuild specific service
docker-compose -f docker-compose.production.yml build gateway

# Start with new build
docker-compose -f docker-compose.production.yml up -d gateway

# Verify
curl http://localhost:8000/health
```

#### **Method 4: Windows BAT Scripts**
```bash
# Close the specific service window
# Then restart manually:
cd services/gateway
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or restart all services
stop_all_services.bat
start_all_services.bat
```

#### **Method 5: Production (Render)**
```bash
# Via Render Dashboard:
# 1. Go to dashboard.render.com
# 2. Select service (e.g., bhiv-hr-gateway)
# 3. Click "Manual Deploy" → "Deploy Latest Commit"

# Or suspend and resume:
# 1. Click "Suspend"
# 2. Wait 30 seconds
# 3. Click "Resume"
```

**Best Practices**:
- Always check logs after restart
- Verify health endpoint responds
- Test critical functionality
- Monitor for 5 minutes after restart

---

### Q7: How do I view service logs?

**Answer**: Multiple methods to access and analyze logs:

#### **Method 1: Docker Compose Logs**
```bash
# View logs for specific service
docker-compose -f docker-compose.production.yml logs gateway
docker-compose -f docker-compose.production.yml logs agent
docker-compose -f docker-compose.production.yml logs langgraph

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f gateway

# Last 50 lines
docker-compose -f docker-compose.production.yml logs --tail=50 gateway

# All services
docker-compose -f docker-compose.production.yml logs -f

# Since specific time
docker-compose -f docker-compose.production.yml logs --since=1h gateway
docker-compose -f docker-compose.production.yml logs --since="2025-01-21 10:00" gateway
```

#### **Method 2: Search Logs for Errors**
```bash
# Search for errors
docker-compose -f docker-compose.production.yml logs | grep -i error

# Search for specific pattern
docker-compose -f docker-compose.production.yml logs gateway | grep -i "authentication"

# Count errors
docker-compose -f docker-compose.production.yml logs | grep -i error | wc -l

# Export logs to file
docker-compose -f docker-compose.production.yml logs > system_logs_$(date +%Y%m%d).log
```

#### **Method 3: Windows BAT Scripts**
```bash
# Each service runs in its own command window
# Logs are visible in real-time in each window

# To save logs:
# Right-click window title → Edit → Select All
# Right-click → Copy
# Paste into text file
```

#### **Method 4: Production Logs (Render)**
```bash
# Via Render Dashboard:
# 1. Go to dashboard.render.com
# 2. Select service
# 3. Click "Logs" tab
# 4. View real-time logs
# 5. Download logs if needed

# Logs show:
# - Application logs
# - Build logs
# - Deploy logs
# - Error logs
```

#### **Method 5: Log Files (if configured)**
```bash
# Gateway logs
cat logs/gateway.log
tail -f logs/gateway.log

# Application logs
cat logs/bhiv_hr_platform.log
tail -f logs/bhiv_hr_platform.log

# Search log files
grep -i "error" logs/*.log
grep -i "authentication failed" logs/gateway.log
```

#### **Log Analysis Tips**
```bash
# Find most common errors
docker-compose -f docker-compose.production.yml logs | \
  grep -i error | \
  sort | uniq -c | sort -rn | head -10

# Find slow requests (>1 second)
docker-compose -f docker-compose.production.yml logs gateway | \
  grep "response_time" | \
  awk '$NF > 1000'

# Find authentication failures
docker-compose -f docker-compose.production.yml logs gateway | \
  grep -i "401\|unauthorized\|authentication failed"

# Find database errors
docker-compose -f docker-compose.production.yml logs | \
  grep -i "database\|connection refused\|timeout"
```

**Log Locations**:
- Docker logs: In-memory, access via `docker logs`
- Application logs: `logs/` directory
- Production logs: Render Dashboard
- Database logs: `docker-compose logs db`

---

### Q8: Services are slow - how to improve performance?

**Answer**: Systematic approach to diagnose and improve performance:

#### **Step 1: Identify the Bottleneck**
```bash
# Check system resources
docker stats --no-stream

# Look for:
# - CPU usage >80%
# - Memory usage >85%
# - High network I/O

# Test API response time
time curl http://localhost:8000/v1/candidates

# Check database performance
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT query, calls, mean_exec_time, max_exec_time 
  FROM pg_stat_statements 
  ORDER BY mean_exec_time DESC LIMIT 10"
```

#### **Step 2: Quick Fixes**

**Fix A: Restart Services**
```bash
# Often resolves memory leaks and connection issues
docker-compose -f docker-compose.production.yml restart

# Wait for initialization
sleep 30

# Test performance
time curl http://localhost:8000/v1/candidates
```

**Fix B: Database Optimization**
```bash
# Run VACUUM ANALYZE (recommended weekly)
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "VACUUM ANALYZE"

# This:
# - Reclaims storage
# - Updates statistics
# - Improves query planning
# - Takes 1-5 minutes

# Test performance after
time curl http://localhost:8000/v1/candidates
```

**Fix C: Clear Caches**
```bash
# Clear matching cache
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "TRUNCATE TABLE matching_cache"

# Restart services to clear application cache
docker-compose -f docker-compose.production.yml restart gateway agent
```

**Fix D: Check for Long-Running Queries**
```bash
# Find slow queries
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' 
  AND now() - pg_stat_activity.query_start > interval '5 seconds'
  ORDER BY duration DESC"

# Kill slow query if needed
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT pg_terminate_backend(<pid>)"
```

#### **Step 3: Long-term Optimizations**

**Optimization A: Database Indexes**
```bash
# Check index usage
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT schemaname, tablename, indexname, idx_scan 
  FROM pg_stat_user_indexes 
  WHERE idx_scan = 0 
  ORDER BY pg_relation_size(indexrelid) DESC"

# Rebuild indexes if needed
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "REINDEX DATABASE bhiv_hr"
```

**Optimization B: Connection Pool Tuning**
```python
# Edit services/gateway/app/main.py
# Increase pool size if needed
engine = create_engine(
    DATABASE_URL,
    pool_size=15,        # Increase from 10
    max_overflow=10,     # Increase from 5
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**Optimization C: Resource Limits**
```bash
# Increase memory limits
docker update --memory=1g --cpus=1.0 bhiv-hr-gateway
docker update --memory=1g --cpus=1.0 bhiv-hr-agent

# Restart services
docker-compose -f docker-compose.production.yml restart
```

#### **Step 4: Monitor Performance**
```bash
# Continuous monitoring
python tools/monitoring/service_connection_validator.py

# Check metrics
curl http://localhost:8000/metrics

# Performance dashboard
curl http://localhost:8000/metrics/dashboard
```

**Performance Targets**:
- API response time: <100ms
- Database queries: <50ms
- AI matching: <0.02s per candidate
- Portal load time: <2s

**When to Escalate**: If performance doesn't improve after optimizations, escalate with metrics data.

---

## 🗄️ Database Operations

### Q9: How do I connect to the database?

**Answer**: Multiple methods to connect to MongoDB Atlas:

#### **Method 1: Docker Exec (Recommended for Local)**
```bash
# Connect to database
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr

# You'll see MongoDB shell prompt:
# bhiv_hr=#

# Run queries
SELECT COUNT(*) FROM candidates;
SELECT * FROM jobs LIMIT 5;

# Exit
\q
```

#### **Method 2: psql Command Line**
```bash
# Local database
psql -h localhost -p 5432 -U bhiv_user -d bhiv_hr

# Production database (if credentials available)
psql "postgresql://user:pass@host:5432/bhiv_hr?sslmode=require"

# Using DATABASE_URL from .env
psql $DATABASE_URL
```

#### **Method 3: Database Tools (GUI)**
```yaml
DBeaver:
  Host: localhost
  Port: 5432
  Database: bhiv_hr
  Username: bhiv_user
  Password: (from .env file)
  
pgAdmin:
  Same credentials as above
  
DataGrip:
  Same credentials as above
```

#### **Method 4: Python Script**
```python
# Quick database check
python tools/database/database_url_checker.py

# Comprehensive check
python tools/database/precise_db_check.py

# Output shows:
# - Connection status
# - Table counts
# - Schema version
# - Index status
```

#### **Common Database Queries**
```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Count records in all tables
SELECT 'candidates' as table_name, COUNT(*) FROM candidates
UNION ALL
SELECT 'jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'feedback', COUNT(*) FROM feedback
UNION ALL
SELECT 'interviews', COUNT(*) FROM interviews;

-- Check active connections
SELECT count(*), state, application_name 
FROM pg_stat_activity 
GROUP BY state, application_name;

-- Check database size
SELECT pg_size_pretty(pg_database_size('bhiv_hr'));
```

**Troubleshooting**:
- If connection refused: Check database is running
- If authentication failed: Verify credentials in .env
- If timeout: Check network connectivity

---

### Q10: How do I backup the database?

**Answer**: Multiple backup methods for different scenarios:

#### **Method 1: Quick Manual Backup**
```bash
# Create backup with timestamp
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user bhiv_hr > backup_$(date +%Y%m%d_%H%M%S).sql

# Create compressed backup (saves space)
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user bhiv_hr | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables only
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user -t candidates -t jobs bhiv_hr > backup_core_tables.sql

# Backup schema only (no data)
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user --schema-only bhiv_hr > schema_backup.sql
```

#### **Method 2: Automated Backup Script**
```bash
# Create backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bhiv_hr_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.production.yml exec -T db \
  pg_dump -U bhiv_user bhiv_hr | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
EOF

# Make executable
chmod +x scripts/backup_database.sh

# Run backup
bash scripts/backup_database.sh
```

#### **Method 3: Schedule Automated Backups**
```bash
# Windows Task Scheduler
# 1. Open Task Scheduler
# 2. Create Basic Task
# 3. Name: "BHIV HR Database Backup"
# 4. Trigger: Daily at 2:00 AM
# 5. Action: Run scripts/backup_database.sh
# 6. Save

# Linux Cron
# Add to crontab:
crontab -e
# Add line:
0 2 * * * /path/to/scripts/backup_database.sh

# Verify cron job
crontab -l
```

#### **Method 4: Production Backup (Render)**
```yaml
Automatic Backups:
  Frequency: Daily
  Retention: 7 days (free tier)
  Location: Render Dashboard → Database → Backups
  
Manual Backup:
  1. Go to Render Dashboard
  2. Select database service
  3. Click "Backups" tab
  4. Click "Create Backup"
  5. Download backup file
```

#### **Backup Best Practices**
```yaml
Frequency:
  Daily: Automated backups at 2 AM
  Weekly: Full backup on Sunday
  Monthly: Archive backup (keep 3 months)
  Before Changes: Manual backup before major updates

Storage:
  Local: ./backups/ directory
  Cloud: Upload to S3/Google Drive (recommended)
  Offsite: Keep copy in different location

Testing:
  Monthly: Test restore to verify backup integrity
  Quarterly: Full disaster recovery test
```

**Backup Verification**:
```bash
# Check backup file size
ls -lh backups/

# Test backup integrity
gunzip -t backup_20250121_020000.sql.gz

# Quick restore test (to test database)
# See Q11 for restore procedures
```

---

### Q11: How do I restore from backup?

**Answer**: Step-by-step restore procedures:

#### **Method 1: Full Database Restore**
```bash
# IMPORTANT: Stop all services first
docker-compose -f docker-compose.production.yml stop gateway agent langgraph portal client_portal candidate_portal

# Wait for connections to close
sleep 10

# Restore from uncompressed backup
cat backup_20250121_020000.sql | \
  docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr

# Or restore from compressed backup
gunzip -c backup_20250121_020000.sql.gz | \
  docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr

# Restart services
docker-compose -f docker-compose.production.yml start gateway agent langgraph portal client_portal candidate_portal

# Verify data
curl http://localhost:8000/v1/candidates
```

#### **Method 2: Restore to New Database (Safe)**
```bash
# Create new database for testing
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -c "CREATE DATABASE bhiv_hr_restore"

# Restore to new database
cat backup_20250121_020000.sql | \
  docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr_restore

# Verify restore
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr_restore -c "SELECT COUNT(*) FROM candidates"

# If good, swap databases
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -c "
  ALTER DATABASE bhiv_hr RENAME TO bhiv_hr_old;
  ALTER DATABASE bhiv_hr_restore RENAME TO bhiv_hr;"

# Drop old database after verification
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -c "DROP DATABASE bhiv_hr_old"
```

#### **Method 3: Restore Specific Tables**
```bash
# Extract specific table from backup
pg_restore -U bhiv_user -d bhiv_hr -t candidates backup.dump

# Or using MongoDB backup
grep -A 1000 "CREATE TABLE candidates" backup.sql | \
  docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr
```

#### **Method 4: Production Restore (Render)**
```yaml
Via Render Dashboard:
  1. Go to database service
  2. Click "Backups" tab
  3. Select backup to restore
  4. Click "Restore"
  5. Confirm restoration
  6. Wait for completion (5-15 minutes)
  7. Verify data integrity

CAUTION: This will overwrite current database
```

#### **Restore Verification Checklist**
```bash
# 1. Check table counts
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT 'candidates' as table_name, COUNT(*) FROM candidates
  UNION ALL SELECT 'jobs', COUNT(*) FROM jobs
  UNION ALL SELECT 'feedback', COUNT(*) FROM feedback"

# 2. Check recent data
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT MAX(created_at) FROM candidates"

# 3. Test API access
curl http://localhost:8000/v1/candidates

# 4. Test portal access
curl http://localhost:8501

# 5. Run comprehensive check
python tools/database/precise_db_check.py
```

**Emergency Restore Procedure**:
```bash
# If database corrupted:
# 1. Stop all services immediately
# 2. Restore from most recent backup
# 3. Verify data integrity
# 4. Restart services
# 5. Monitor for issues
# 6. Document incident
# 7. ESCALATE TO SHASHANK
```

---

### Q12: Database connection errors - how to fix?

**Answer**: Systematic troubleshooting for database connection issues:

#### **Step 1: Verify Database is Running**
```bash
# Check database container status
docker-compose -f docker-compose.production.yml ps db

# Expected: Status "Up"
# If not running:
docker-compose -f docker-compose.production.yml up -d db
sleep 10
```

#### **Step 2: Test Database Connection**
```bash
# Direct connection test
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT 1"

# Expected output: 1
# If fails: Database not accepting connections

# Check database logs
docker-compose -f docker-compose.production.yml logs db --tail=50
```

#### **Step 3: Verify DATABASE_URL**
```bash
# Check environment variable
type .env | findstr DATABASE_URL  # Windows
grep DATABASE_URL .env            # Linux/Mac

# Correct format:
# postgresql://bhiv_user:password@localhost:5432/bhiv_hr

# Test URL
python tools/database/database_url_checker.py
```

#### **Step 4: Check Connection Pool**
```bash
# Check active connections
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT count(*) as connections, 
         state, 
         application_name 
  FROM pg_stat_activity 
  GROUP BY state, application_name"

# If too many connections (>50):
# Kill idle connections
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'idle' 
  AND state_change < now() - interval '10 minutes'"
```

#### **Step 5: Common Error Solutions**

**Error: "Connection refused"**
```bash
# Database not running
docker-compose -f docker-compose.production.yml up -d db
sleep 10

# Wrong host/port
# Check DATABASE_URL has correct host:port
```

**Error: "Connection timeout"**
```bash
# Network issue or database overloaded
# Restart database
docker-compose -f docker-compose.production.yml restart db
sleep 10

# Check database performance
docker stats bhiv-hr-db
```

**Error: "Too many connections"**
```bash
# Connection pool exhausted
# Kill idle connections (see Step 4)

# Or restart services to reset pools
docker-compose -f docker-compose.production.yml restart gateway agent langgraph
```

**Error: "Authentication failed"**
```bash
# Wrong credentials
# Verify password in .env matches database

# Reset password if needed
docker-compose -f docker-compose.production.yml exec db \
  psql -U postgres -c "ALTER USER bhiv_user PASSWORD 'new_password'"

# Update .env with new password
# Restart services
```

#### **Step 6: Nuclear Option**
```bash
# If nothing works, recreate database
# CAUTION: This deletes all data

# 1. Backup first
bash scripts/backup_database.sh

# 2. Stop services
docker-compose -f docker-compose.production.yml down

# 3. Remove database volume
docker volume rm bhiv-hr-platform_postgres_data

# 4. Start fresh
docker-compose -f docker-compose.production.yml up -d db
sleep 10

# 5. Apply schema
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -f /docker-entrypoint-initdb.d/init.sql

# 6. Restore data
cat backup.sql | docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr

# 7. Start services
docker-compose -f docker-compose.production.yml up -d
```

**Prevention**:
- Monitor connection counts regularly
- Set appropriate connection pool limits
- Run VACUUM ANALYZE weekly
- Keep database updated

---

## 📊 Data Management

### Q13: How do I load candidates into the system?

**Answer**: Multiple methods to add candidates:

#### **Method 1: Extract from Resumes (Automated)**
```bash
# Extract data from 29 sample resumes
cd tools/data
python comprehensive_resume_extractor.py

# This will:
# - Process all PDFs in assets/resumes/
# - Extract name, email, skills, experience
# - Create candidates.csv
# - Ready for bulk import

# Output: data/candidates.csv

# Then load to database
cd ../database
python load_candidates.py --file=../../data/candidates.csv
```

#### **Method 2: Bulk Import via CSV**
```bash
# Prepare CSV file with columns:
# name,email,phone,technical_skills,experience_years,location

# Example CSV:
# John Doe,john@example.com,+1234567890,Python|FastAPI|Docker,5,New York
# Jane Smith,jane@example.com,+1234567891,React|Node.js|AWS,3,San Francisco

# Import via API
curl -X POST http://localhost:8000/v1/candidates/bulk \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -F "file=@candidates.csv"

# Or use load script
python tools/database/load_candidates.py \
  --file=candidates.csv \
  --batch-size=50
```

#### **Method 3: Manual Entry via Portal**
```bash
# 1. Open HR Portal
http://localhost:8501

# 2. Go to "Step 2: Upload Candidates"

# 3. Fill form:
#    - Name
#    - Email
#    - Phone
#    - Skills
#    - Experience
#    - Location

# 4. Click "Add Candidate"

# 5. Verify in candidate list
```

#### **Method 4: API Single Candidate**
```bash
# Create single candidate via API
curl -X POST http://localhost:8000/v1/candidates \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "technical_skills": "Python, FastAPI, Docker",
    "experience_years": 5,
    "location": "New York",
    "education": "BS Computer Science",
    "current_company": "Tech Corp"
  }'

# Response includes candidate_id and ai_rank
```

#### **Method 5: Database Direct Insert**
```bash
# Insert directly into database
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  INSERT INTO candidates (name, email, phone, technical_skills, experience_years, location)
  VALUES ('John Doe', 'john@example.com', '+1234567890', 'Python, FastAPI', 5, 'New York')
  RETURNING id"
```

**Data Validation**:
```yaml
Required Fields:
  - name (string, 2-100 chars)
  - email (valid email format)
  
Optional Fields:
  - phone (E.164 format: +1234567890)
  - technical_skills (comma-separated)
  - experience_years (integer, 0-50)
  - location (string)
  - education (string)
  - current_company (string)

Constraints:
  - Email must be unique
  - Phone must be unique (if provided)
  - Skills required for AI matching
```

**Troubleshooting**:
- Duplicate email: Use different email or update existing
- Invalid format: Check CSV column order
- Import fails: Use smaller batch size (25-50)

---

### Q14: How do I create sample jobs?

**Answer**: Multiple methods to create job postings:

#### **Method 1: Automated Job Creator (Recommended)**
```bash
# Create 19 diverse sample jobs
cd tools/data
python dynamic_job_creator.py

# This creates jobs for:
# - Software Engineer (multiple levels)
# - Data Scientist
# - Product Manager
# - DevOps Engineer
# - UI/UX Designer
# - And more...

# Jobs are automatically inserted into database
# Verify:
curl http://localhost:8000/v1/jobs
```

#### **Method 2: Manual via Client Portal**
```bash
# 1. Open Client Portal
http://localhost:8502

# 2. Login with: TECH001 / demo123

# 3. Go to "Job Management" section

# 4. Click "Create New Job"

# 5. Fill form:
#    - Job Title
#    - Department
#    - Location
#    - Experience Level (entry/mid/senior)
#    - Requirements
#    - Description
#    - Salary Range (optional)

# 6. Click "Post Job"

# 7. Job appears in job list
```

#### **Method 3: API Single Job**
```bash
# Create job via API
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "location": "Remote",
    "experience_level": "senior",
    "requirements": "Python, FastAPI, Docker, AWS, 5+ years experience",
    "description": "Join our team to build scalable microservices",
    "salary_min": 120000,
    "salary_max": 180000,
    "client_id": "TECH001"
  }'

# Response includes job_id
```

#### **Method 4: Database Direct Insert**
```bash
# Insert directly into database
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  INSERT INTO jobs (title, department, location, experience_level, requirements, description, client_id)
  VALUES (
    'Software Engineer',
    'Engineering',
    'San Francisco',
    'mid',
    'Python, FastAPI, MongoDB',
    'Build amazing products',
    'TECH001'
  )
  RETURNING id"
```

#### **Method 5: Bulk Job Import**
```bash
# Create CSV file: jobs.csv
# title,department,location,experience_level,requirements,description,client_id

# Import via script (create if needed)
python tools/data/bulk_import_jobs.py --file=jobs.csv
```

**Job Fields**:
```yaml
Required:
  - title (string)
  - department (string)
  - location (string)
  - experience_level (entry/mid/senior/lead)
  - requirements (string, for AI matching)
  - description (string)
  
Optional:
  - client_id (defaults to TECH001)
  - salary_min (integer)
  - salary_max (integer)
  - remote_allowed (boolean)
  - benefits (string)
```

**Verify Jobs Created**:
```bash
# Check via API
curl http://localhost:8000/v1/jobs

# Check via database
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT id, title, department FROM jobs"

# Check via portal
http://localhost:8501  # HR Portal
http://localhost:8502  # Client Portal
```

---

### Q15: Bulk import fails halfway - what to do?

**Answer**: Troubleshooting and recovery for failed bulk imports:

#### **Step 1: Identify What Failed**
```bash
# Check import logs
tail -100 logs/bulk_import.log

# Check database for partial imports
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT COUNT(*) as imported_count, 
         MAX(created_at) as last_import 
  FROM candidates 
  WHERE created_at > NOW() - INTERVAL '1 hour'"

# Check for errors in service logs
docker-compose -f docker-compose.production.yml logs gateway | grep -i "bulk\|import"
```

#### **Step 2: Common Causes & Solutions**

**Cause A: Duplicate Emails**
```bash
# Find duplicates in CSV
cat candidates.csv | cut -d',' -f2 | sort | uniq -d

# Solution: Remove duplicates from CSV
# Or use --skip-existing flag
python tools/database/load_candidates.py \
  --file=candidates.csv \
  --skip-existing
```

**Cause B: Timeout (Large File)**
```bash
# Solution: Use smaller batch size
python tools/database/load_candidates.py \
  --file=candidates.csv \
  --batch-size=25  # Reduce from default 50

# Or split CSV into smaller files
split -l 50 candidates.csv candidates_batch_
# Then import each batch separately
```

**Cause C: Invalid Data Format**
```bash
# Check CSV format
head -5 candidates.csv

# Correct format:
# name,email,phone,technical_skills,experience_years,location

# Solution: Fix CSV formatting
# - Remove special characters
# - Ensure proper escaping
# - Check column count matches
```

**Cause D: Memory Overflow**
```bash
# Solution: Increase memory limit
docker update --memory=2g bhiv-hr-gateway

# Restart service
docker-compose -f docker-compose.production.yml restart gateway

# Retry import
```

#### **Step 3: Clean Up Partial Import**
```bash
# Option 1: Keep partial import, import remaining
# Identify last successful candidate
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT email FROM candidates 
  ORDER BY created_at DESC LIMIT 1"

# Remove imported rows from CSV
# Then import remaining rows

# Option 2: Rollback partial import
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  DELETE FROM candidates 
  WHERE created_at > '2025-01-21 10:00:00' 
  AND status='pending'"

# Then retry full import
```

#### **Step 4: Retry with Error Handling**
```bash
# Use robust import script
python tools/database/load_candidates.py \
  --file=candidates.csv \
  --batch-size=25 \
  --on-error=skip \
  --log-errors

# This will:
# - Process in small batches
# - Skip rows with errors
# - Log all errors to file
# - Continue processing
# - Report success/failure count

# Check error log
cat logs/import_errors.log
```

#### **Step 5: Verify Import**
```bash
# Check total count
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT COUNT(*) FROM candidates"

# Check recent imports
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT id, name, email, created_at 
  FROM candidates 
  WHERE created_at > NOW() - INTERVAL '1 hour' 
  ORDER BY created_at DESC 
  LIMIT 10"

# Verify via API
curl http://localhost:8000/v1/candidates
```

**Best Practices**:
- Test with small sample first (10-20 rows)
- Use batch size of 25-50 for large imports
- Validate CSV format before import
- Keep backup before bulk operations
- Monitor logs during import

---

### Q16: How do I export candidate data?

**Answer**: Multiple export methods for different use cases:

#### **Method 1: Export via HR Portal**
```bash
# 1. Open HR Portal
http://localhost:8501

# 2. Go to "Step 7: Export Reports"

# 3. Select export type:
#    - All Candidates
#    - Shortlisted Candidates
#    - Candidates by Job
#    - Complete Assessment Report

# 4. Click "Export to CSV"

# 5. File downloads automatically

# Export includes:
# - Candidate details
# - AI scores
# - Values assessment
# - Interview status
# - Recommendations
```

#### **Method 2: Export via API**
```bash
# Export all candidates
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/v1/candidates > candidates.json

# Export specific job candidates
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/v1/candidates/job/1 > job1_candidates.json

# Export with filters
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  "http://localhost:8000/v1/candidates/search?status=active&min_experience=3" \
  > filtered_candidates.json

# Export job report as CSV
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/v1/reports/job/1/export.csv > job1_report.csv
```

#### **Method 3: Database Export**
```bash
# Export to CSV
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  COPY (
    SELECT id, name, email, phone, technical_skills, 
           experience_years, location, ai_rank, status
    FROM candidates
    WHERE status='active'
  ) TO STDOUT WITH CSV HEADER" > candidates_export.csv

# Export with joins (complete data)
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  COPY (
    SELECT c.name, c.email, c.technical_skills, c.ai_rank,
           j.title as job_title, f.overall_score as values_score,
           i.status as interview_status
    FROM candidates c
    LEFT JOIN job_applications ja ON c.id = ja.candidate_id
    LEFT JOIN jobs j ON ja.job_id = j.id
    LEFT JOIN feedback f ON c.id = f.candidate_id
    LEFT JOIN interviews i ON c.id = i.candidate_id
    WHERE c.status='active'
  ) TO STDOUT WITH CSV HEADER" > complete_export.csv
```

#### **Method 4: Automated Export Script**
```bash
# Create export script
cat > scripts/export_candidates.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
EXPORT_DIR="./exports"
mkdir -p $EXPORT_DIR

# Export candidates
docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user -d bhiv_hr -c "
  COPY candidates TO STDOUT WITH CSV HEADER" \
  > $EXPORT_DIR/candidates_$DATE.csv

# Export jobs
docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user -d bhiv_hr -c "
  COPY jobs TO STDOUT WITH CSV HEADER" \
  > $EXPORT_DIR/jobs_$DATE.csv

echo "Exports created in $EXPORT_DIR"
EOF

chmod +x scripts/export_candidates.sh
bash scripts/export_candidates.sh
```

#### **Method 5: Excel Export (with formatting)**
```python
# Create Python script: export_to_excel.py
import pandas as pd
import psycopg2
from openpyxl import Workbook

# Connect to database
conn = psycopg2.connect("postgresql://bhiv_user:password@localhost:5432/bhiv_hr")

# Query data
df = pd.read_sql("SELECT * FROM candidates WHERE status='active'", conn)

# Export to Excel with formatting
with pd.ExcelWriter('candidates_export.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Candidates', index=False)
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Candidates']
    for column in worksheet.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        worksheet.column_dimensions[column[0].column_letter].width = max_length + 2

print("Excel export created: candidates_export.xlsx")
```

**Export Formats**:
- CSV: Simple, universal compatibility
- JSON: API responses, programmatic use
- Excel: Formatted reports with multiple sheets
- PDF: Final reports (via portal)

**Data Privacy**:
- Mask sensitive data (phone, email) if needed
- Follow GDPR/data protection regulations
- Secure export files
- Delete exports after use

---

## 🤖 AI & Matching

### Q17: AI matching not working - how to fix?

**Answer**: Systematic troubleshooting for AI matching issues:

#### **Step 1: Verify Agent Service**
```bash
# Check Agent service health
curl http://localhost:9000/health

# Expected: {"status":"healthy","ai_engine":"operational"}

# If not healthy, check logs
docker-compose -f docker-compose.production.yml logs agent --tail=50

# Restart if needed
docker-compose -f docker-compose.production.yml restart agent
sleep 10
```

#### **Step 2: Test Database Connection from Agent**
```bash
# Test database connectivity
curl http://localhost:9000/test-db

# Expected: {"status":"connected","candidates_count":X}

# If fails, check DATABASE_URL in Agent service
docker-compose -f docker-compose.production.yml exec agent \
  env | grep DATABASE_URL
```

#### **Step 3: Verify Candidate Has Skills**
```bash
# AI matching requires technical_skills field
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT id, name, technical_skills 
  FROM candidates 
  WHERE id=1"

# If technical_skills is NULL or empty:
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE candidates 
  SET technical_skills = 'General Skills' 
  WHERE technical_skills IS NULL OR technical_skills = ''"
```

#### **Step 4: Manually Trigger Matching**
```bash
# Trigger matching for specific job
curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer <YOUR_API_KEY>"

# Expected response with candidate matches and scores

# Check matching cache
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT * FROM matching_cache 
  WHERE job_id=1 
  ORDER BY match_score DESC 
  LIMIT 5"
```

#### **Step 5: Check Phase 3 Engine**
```bash
# Verify Phase 3 engine loaded
docker-compose -f docker-compose.production.yml logs agent | grep -i "phase3"

# Expected: "Phase 3 Semantic Engine initialized"

# If not loaded, Agent falls back to database matching
# This is expected behavior and still works
```

#### **Common Issues**:

**Issue: AI rank stays null**
```bash
# Cause: Candidate created before Agent service started
# Solution: Trigger matching manually
curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer <YOUR_API_KEY>"
```

**Issue: Matching returns empty results**
```bash
# Cause: No candidates match job requirements
# Solution: Check job requirements and candidate skills
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT id, title, requirements FROM jobs WHERE id=1"
```

**Issue: Matching is slow (>5 seconds)**
```bash
# Cause: Large candidate pool or resource constraints
# Solution: Use batch matching with smaller chunks
curl -X POST http://localhost:8000/v1/match/batch \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1], "limit": 10}'
```

---

### Q18: How do I test AI matching manually?

**Answer**: Step-by-step manual testing procedures:

#### **Method 1: Via API (Recommended)**
```bash
# Set API key
export API_KEY_SECRET="<YOUR_API_KEY>"

# Test single job matching
curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer $API_KEY_SECRET" \
  -H "Content-Type: application/json"

# Expected response:
{
  "job_id": 1,
  "top_candidates": [
    {
      "candidate_id": 5,
      "match_score": 87.5,
      "skills_match": 0.92,
      "experience_match": 0.85,
      "location_match": 1.0
    }
  ],
  "algorithm_version": "phase3_v1.0",
  "processing_time": "0.45s"
}

# Test batch matching
curl -X POST http://localhost:8000/v1/match/batch \
  -H "Authorization: Bearer $API_KEY_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1, 2, 3], "limit": 10}'
```

#### **Method 2: Via HR Portal**
```bash
# 1. Open HR Portal
http://localhost:8501

# 2. Go to "Step 4: AI Shortlist"

# 3. Select job from dropdown

# 4. Click "Run AI Matching"

# 5. View results:
#    - Top candidates with scores
#    - Skills match breakdown
#    - Experience match
#    - Location match

# 6. Export results if needed
```

#### **Method 3: Direct Agent Service**
```bash
# Test Agent service directly
curl -X POST http://localhost:9000/match \
  -H "Content-Type: application/json" \
  -d '{"job_id": 1}'

# Test batch matching
curl -X POST http://localhost:9000/batch-match \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1, 2, 3]}'

# Analyze specific candidate
curl http://localhost:9000/analyze/1
```

#### **Method 4: Check Matching Cache**
```bash
# View cached matches
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT job_id, candidate_id, match_score, 
         skills_match, experience_match, location_match,
         created_at
  FROM matching_cache 
  WHERE job_id=1 
  ORDER BY match_score DESC 
  LIMIT 10"

# Clear cache to force fresh matching
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  TRUNCATE TABLE matching_cache"
```

#### **Method 5: Analysis Tools**
```bash
# Use analysis tools
cd tools/analysis
python gateway_endpoint_analysis.py

# Shows all available endpoints including matching

# Count endpoints
python count_all_endpoints.py
# Output: 89 total (74 Gateway + 6 Agent + 9 LangGraph)
```

**Performance Testing**:
```bash
# Test response time
time curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer $API_KEY_SECRET"

# Expected: <1 second for single job
# Expected: <5 seconds for batch of 10 jobs

# Load testing (if needed)
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/match/1/top \
    -H "Authorization: Bearer $API_KEY_SECRET" &
done
wait
```

---

### Q19: AI rank stays null - what's wrong?

**Answer**: Troubleshooting null AI ranks:

#### **Root Causes**:
1. Candidate has no technical_skills
2. Agent service not running
3. Matching not triggered yet
4. Database connection issue

#### **Solution 1: Check Technical Skills**
```bash
# Verify candidate has skills
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT id, name, technical_skills, ai_rank 
  FROM candidates 
  WHERE ai_rank IS NULL 
  LIMIT 10"

# If technical_skills is NULL:
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE candidates 
  SET technical_skills = 'General' 
  WHERE technical_skills IS NULL OR technical_skills = ''"

# Trigger matching
curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer <YOUR_API_KEY>"
```

#### **Solution 2: Verify Agent Service**
```bash
# Check Agent is running
curl http://localhost:9000/health

# If not running:
docker-compose -f docker-compose.production.yml up -d agent
sleep 10

# Verify Phase 3 engine loaded
docker-compose -f docker-compose.production.yml logs agent | grep -i "phase3"
```

#### **Solution 3: Manually Trigger Matching**
```bash
# Trigger matching for all jobs
for job_id in {1..5}; do
  curl -X POST http://localhost:8000/v1/match/$job_id/top \
    -H "Authorization: Bearer <YOUR_API_KEY>"
  sleep 2
done

# Verify ai_rank updated
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT id, name, ai_rank, updated_at 
  FROM candidates 
  WHERE ai_rank IS NOT NULL 
  ORDER BY updated_at DESC 
  LIMIT 10"
```

#### **Solution 4: Check Gateway-Agent Connection**
```bash
# Verify Gateway can reach Agent
docker-compose -f docker-compose.production.yml exec gateway \
  curl http://agent:9000/health

# If fails, check AGENT_SERVICE_URL
docker-compose -f docker-compose.production.yml exec gateway \
  env | grep AGENT_SERVICE_URL

# Should be: http://agent:9000 (Docker) or http://localhost:9000 (local)
```

#### **Solution 5: Database Fallback**
```bash
# If Agent unavailable, Gateway uses database matching
# This is expected behavior

# Check Gateway logs for fallback
docker-compose -f docker-compose.production.yml logs gateway | \
  grep -i "fallback\|agent unavailable"

# Database matching still provides ai_rank
# Just uses simpler algorithm
```

**Prevention**:
- Ensure technical_skills populated for all candidates
- Keep Agent service running
- Monitor Agent service health
- Trigger matching after bulk imports

---

### Q20: How does the Phase 3 AI engine work?

**Answer**: Overview of the Phase 3 semantic matching engine:

#### **Architecture**:
```yaml
Phase 3 Components:
  1. Semantic Engine: Sentence transformers for text understanding
  2. Advanced Matcher: Multi-factor scoring algorithm
  3. Batch Processor: Efficient bulk matching (50 candidates/chunk)
  4. Learning Engine: Feedback-based optimization
  5. Job Matcher: Semantic job-candidate matching

Technology Stack:
  - Sentence Transformers: all-MiniLM-L6-v2 model
  - scikit-learn: ML predictions
  - NumPy/Pandas: Data processing
  - MongoDB Atlas: Data storage and caching
```

#### **Matching Algorithm**:
```python
# Simplified matching logic
def calculate_match_score(candidate, job):
    # 1. Skills Match (40% weight)
    skills_score = semantic_similarity(
        candidate.technical_skills,
        job.requirements
    )
    
    # 2. Experience Match (30% weight)
    exp_score = experience_match(
        candidate.experience_years,
        job.required_experience
    )
    
    # 3. Location Match (20% weight)
    location_score = location_match(
        candidate.location,
        job.location
    )
    
    # 4. Education Match (10% weight)
    edu_score = education_match(
        candidate.education,
        job.education_requirement
    )
    
    # Weighted average
    final_score = (
        skills_score * 0.4 +
        exp_score * 0.3 +
        location_score * 0.2 +
        edu_score * 0.1
    ) * 100
    
    return final_score
```

#### **Performance Characteristics**:
```yaml
Speed:
  - Single candidate: <0.02 seconds
  - Batch (50 candidates): <1 second
  - Full database (1000 candidates): <20 seconds

Accuracy:
  - Skills matching: 92% semantic accuracy
  - Experience matching: 95% accuracy
  - Overall matching: 88% accuracy vs manual review

Caching:
  - Results cached in matching_cache table
  - Cache TTL: 24 hours
  - Automatic cache invalidation on data changes
```

#### **Fallback Mechanism**:
```yaml
Primary: Phase 3 Semantic Engine
  - Uses sentence transformers
  - Advanced multi-factor scoring
  - Real-time processing

Fallback: Database Matching
  - Activated if Agent service unavailable
  - Uses MongoDB Atlas text search
  - Simpler keyword matching
  - Still provides ai_rank

Behavior:
  - Automatic fallback (no manual intervention)
  - Logs fallback events
  - Returns to Phase 3 when Agent recovers
```

#### **Monitoring**:
```bash
# Check which engine is active
docker-compose -f docker-compose.production.yml logs agent | \
  grep -i "phase3\|semantic engine"

# Check matching performance
curl http://localhost:8000/metrics | grep -i "match"

# View recent matches
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT job_id, COUNT(*) as matches, 
         AVG(match_score) as avg_score,
         MAX(created_at) as last_match
  FROM matching_cache 
  GROUP BY job_id"
```

**Future Enhancements**:
- Reinforcement learning integration (RL tables ready)
- Company-specific scoring preferences
- Adaptive learning from feedback
- Multi-language support

---

## 🔒 Authentication & Security

### Q21: Authentication failing - how to fix?

**Answer**: Comprehensive authentication troubleshooting:

#### **Step 1: Identify Authentication Type**
```yaml
Three Authentication Systems:
  1. API Key: Bearer token for API access
  2. Client JWT: Client portal login
  3. Candidate JWT: Candidate portal login
```

#### **Issue A: API Key Authentication**
```bash
# Test API key
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/v1/candidates

# If 401 Unauthorized:

# Check API key format (must be Bearer token)
# Correct: Authorization: Bearer <YOUR_API_KEY>
# Wrong: X-API-Key: <YOUR_API_KEY>

# Verify API key exists
python tools/security/get_all_api_keys.py

# Check environment variable
type .env | findstr API_KEY_SECRET  # Windows
grep API_KEY_SECRET .env            # Linux/Mac

# Test with known good key
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/health
```

#### **Issue B: Client Portal Login**
```bash
# Test client authentication
curl -X POST http://localhost:8000/v1/client/login \
  -H "Content-Type: application/json" \
  -d '{"client_id": "TECH001", "password": "demo123"}'

# Expected: JWT token in response

# If fails:

# Check client exists in database
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT client_id, company_name, is_active 
  FROM clients 
  WHERE client_id='TECH001'"

# Reset password if needed
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients 
  SET password_hash = crypt('demo123', gen_salt('bf')) 
  WHERE client_id='TECH001'"

# Fix authentication
python tools/utilities/fix_portal_auth.py
```

#### **Issue C: JWT Token Validation**
```bash
# Check JWT secrets match across services
type .env | findstr JWT_SECRET_KEY  # Windows
grep JWT_SECRET_KEY .env            # Linux/Mac

# Verify all services use same secret
docker-compose -f docker-compose.production.yml exec gateway \
  env | grep JWT_SECRET_KEY
docker-compose -f docker-compose.production.yml exec client_portal \
  env | grep JWT_SECRET_KEY

# If mismatch, update .env and restart
docker-compose -f docker-compose.production.yml restart
```

#### **Issue D: Token Expired**
```bash
# JWT tokens expire after 24 hours (default)
# Solution: Login again to get new token

# Or increase token expiration (in code)
# services/gateway/routes/auth.py
# exp = datetime.utcnow() + timedelta(days=7)  # 7 days instead of 1
```

#### **Quick Fix: Reset All Authentication**
```bash
# Run authentication fix script
python tools/utilities/fix_auth_simple.py

# This will:
# - Reset API keys
# - Fix JWT configuration
# - Update portal authentication
# - Restart services

# Verify
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/health
```

---

### Q22: How do I get/reset API keys?

**Answer**: API key management procedures:

#### **Method 1: Get All API Keys**
```bash
# List all API keys
python tools/security/get_all_api_keys.py

# Output shows:
# - API key value
# - Associated client/user
# - Creation date
# - Last used timestamp
```

#### **Method 2: Get from Environment**
```bash
# Check .env file
type .env | findstr API_KEY_SECRET  # Windows
grep API_KEY_SECRET .env            # Linux/Mac

# This is the master API key for testing
```

#### **Method 3: Get from Database**
```bash
# Query database for API keys
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT client_id, api_key_secret, created_at 
  FROM clients 
  WHERE api_key_secret IS NOT NULL"
```

#### **Method 4: Generate New API Key**
```bash
# Generate for specific client
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients 
  SET api_key_secret = gen_random_uuid() 
  WHERE client_id='TECH001' 
  RETURNING api_key_secret"

# Or via API (if endpoint exists)
curl -X POST http://localhost:8000/v1/auth/generate-key \
  -H "Authorization: Bearer <ADMIN_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "TECH001", "description": "New API Key"}'
```

#### **Method 5: Reset Master API Key**
```bash
# Generate new master key
NEW_KEY=$(openssl rand -hex 32)

# Update .env file
# API_KEY_SECRET=$NEW_KEY

# Restart all services
docker-compose -f docker-compose.production.yml restart

# Update Render environment variables (production)
# 1. Go to Render Dashboard
# 2. Select each service
# 3. Environment → Edit
# 4. Update API_KEY_SECRET
# 5. Save (auto-redeploys)
```

#### **Security Best Practices**:
```yaml
API Key Management:
  - Rotate keys every 90 days
  - Use different keys for different environments
  - Never commit keys to Git
  - Store keys in secure vault
  - Monitor key usage
  - Revoke unused keys

Key Format:
  - Length: 32+ characters
  - Type: UUID or random hex
  - Storage: Hashed in database (if possible)
  - Transmission: HTTPS only
```

#### **Revoke API Key**:
```bash
# Revoke specific key
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients 
  SET api_key_secret = NULL 
  WHERE client_id='TECH001'"

# Or mark as inactive
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients 
  SET is_active = FALSE 
  WHERE client_id='TECH001'"
```

---

### Q23: How do I run security audits?

**Answer**: Comprehensive security audit procedures:

#### **Method 1: Automated Security Audit**
```bash
# Run complete security audit
python tools/security/security_audit_checker.py

# Output includes:
# - Password strength analysis
# - JWT configuration check
# - API key rotation status
# - Rate limiting verification
# - HTTPS enforcement
# - CSP headers check
# - MongoDB injection vulnerabilities
# - XSS protection status

# Generates report with:
# - Critical issues (fix immediately)
# - High priority (fix within 24 hours)
# - Medium priority (fix within week)
# - Low priority (fix when possible)
# - Recommendations
```

#### **Method 2: Check for Exposed Secrets**
```bash
# Scan codebase for exposed keys
python tools/utilities/find_exposed_keys.py

# Scans for:
# - API keys
# - Passwords
# - JWT secrets
# - Database URLs
# - Private keys
# - Tokens

# Check specific files
python tools/security/check_api_keys.py

# Output shows:
# ✅ No exposed keys found
# ❌ Found exposed key in file.py line 42
```

#### **Method 3: Security Endpoint Testing**
```bash
# Test rate limiting
curl http://localhost:8000/v1/security/rate-limit-status

# Test input validation
curl -X POST http://localhost:8000/v1/security/test-input-validation \
  -H "Content-Type: application/json" \
  -d '{"input_data": "<script>alert(\"test\")</script>"}'

# Expected: Input sanitized, XSS prevented

# Test security headers
curl -I http://localhost:8000/v1/security/security-headers-test

# Check for:
# - Content-Security-Policy
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security

# Check blocked IPs
curl http://localhost:8000/v1/security/blocked-ips

# Check CSP violations
curl http://localhost:8000/v1/security/csp-violations
```

#### **Method 4: Database Security Check**
```bash
# Check for weak passwords
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT client_id, company_name 
  FROM clients 
  WHERE password_hash IS NULL 
  OR LENGTH(password_hash) < 60"

# Check for inactive accounts with access
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT client_id, is_active, last_login 
  FROM clients 
  WHERE is_active = FALSE 
  AND api_key_secret IS NOT NULL"

# Check audit logs for suspicious activity
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT action, user_id, ip_address, created_at 
  FROM audit_logs 
  WHERE action IN ('login_failed', 'unauthorized_access') 
  AND created_at > NOW() - INTERVAL '24 hours' 
  ORDER BY created_at DESC"
```

#### **Method 5: Penetration Testing**
```bash
# Run penetration test endpoints
curl http://localhost:8000/v1/security/penetration-test-endpoints

# Tests:
# - MongoDB injection attempts
# - XSS attacks
# - CSRF protection
# - Authentication bypass
# - Authorization bypass
# - Rate limit bypass

# Review results and fix vulnerabilities
```

#### **Security Audit Checklist**:
```yaml
Weekly Checks:
  - [ ] Run security audit script
  - [ ] Check for exposed secrets
  - [ ] Review audit logs
  - [ ] Check failed login attempts
  - [ ] Verify rate limiting working

Monthly Checks:
  - [ ] Rotate API keys
  - [ ] Update dependencies
  - [ ] Review user access
  - [ ] Test backup restore
  - [ ] Penetration testing

Quarterly Checks:
  - [ ] Full security audit
  - [ ] Update passwords
  - [ ] Review security policies
  - [ ] Disaster recovery test
  - [ ] Compliance review
```

---

### Q24: Rate limiting errors - what to do?

**Answer**: Understanding and resolving rate limit issues:

#### **Understanding Rate Limits**:
```yaml
Default Limits:
  - Default tier: 60 requests/minute
  - Premium tier: 300 requests/minute
  - Admin tier: 500 requests/minute

Dynamic Adjustment:
  - CPU < 30%: Increase limits by 50%
  - CPU > 80%: Decrease limits by 50%
  - Adjusts every minute

Per-Endpoint Limits:
  - Health checks: Unlimited
  - Read operations: Standard limits
  - Write operations: 50% of standard
  - Bulk operations: 25% of standard
```

#### **Check Current Rate Limit Status**:
```bash
# Check your current limit
curl http://localhost:8000/v1/security/rate-limit-status

# Response shows:
{
  "current_limit": 60,
  "requests_made": 45,
  "requests_remaining": 15,
  "reset_time": "2025-01-21T10:15:00Z",
  "tier": "default"
}
```

#### **Solution 1: Wait for Reset**:
```bash
# Rate limits reset every minute
# Wait 60 seconds and retry

# Implement exponential backoff
for i in {1..5}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $API_KEY_SECRET" \
    http://localhost:8000/v1/candidates)
  
  if [ "$response" = "429" ]; then
    echo "Rate limited, waiting $((2**i)) seconds..."
    sleep $((2**i))
  else
    echo "Success!"
    break
  fi
done
```

#### **Solution 2: Reduce Request Frequency**:
```bash
# Instead of rapid requests:
for i in {1..100}; do
  curl http://localhost:8000/v1/candidates
done

# Space out requests:
for i in {1..100}; do
  curl http://localhost:8000/v1/candidates
  sleep 1  # Wait 1 second between requests
done
```

#### **Solution 3: Use Batch Endpoints**:
```bash
# Instead of multiple single requests:
curl http://localhost:8000/v1/candidates/1
curl http://localhost:8000/v1/candidates/2
curl http://localhost:8000/v1/candidates/3

# Use batch endpoint:
curl -X POST http://localhost:8000/v1/candidates/batch \
  -H "Authorization: Bearer $API_KEY_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"ids": [1, 2, 3]}'
```

#### **Solution 4: Request Higher Tier**:
```bash
# Contact admin to upgrade tier
# Or modify rate limits in code (development only)

# services/gateway/app/main.py
RATE_LIMITS = {
    "default": {
        "default": 120,  # Increase from 60
        "write": 60,
        "bulk": 30
    }
}
```

#### **Solution 5: Check System Resources**:
```bash
# High CPU triggers lower limits
docker stats --no-stream

# If CPU > 80%, optimize or scale up
# Restart services to free resources
docker-compose -f docker-compose.production.yml restart
```

#### **Monitoring Rate Limits**:
```bash
# Check blocked requests
curl http://localhost:8000/v1/security/blocked-ips

# View rate limit metrics
curl http://localhost:8000/metrics | grep rate_limit

# Check logs for rate limit events
docker-compose -f docker-compose.production.yml logs gateway | \
  grep -i "rate limit"
```

**Best Practices**:
- Implement retry logic with exponential backoff
- Cache responses when possible
- Use batch endpoints for multiple items
- Monitor your request patterns
- Request tier upgrade if consistently hitting limits


### Q26: Can this support multiple companies?

**Answer**: Yes, the system is designed with multi-tenancy in mind, though currently operating in single-tenant mode:

**Current State**:
- ✅ Multi-tenant framework fully implemented in runtime-core
- ✅ Tenant resolution service with JWT and header-based resolution
- ✅ Tenant isolation middleware ready for activation
- ❌ Not currently enforced (operating as single-tenant)

**Activation Requirements**:
1. Database schema updates (add tenant_id to all collections)
2. Query modifications (filter all queries by tenant_id)
3. Configuration changes (enable tenant isolation flags)
4. Testing (validate cross-tenant data separation)

**Timeline**: 2-3 weeks for full multi-tenant activation.

---

### Q27: Is the system production-ready for multi-tenancy?

**Answer**: The framework is production-ready but requires activation:

**Ready Components**:
- ✅ Complete tenancy service in runtime-core
- ✅ Tenant resolution from JWT tokens
- ✅ Cross-tenant access validation
- ✅ Tenant-aware query filtering functions
- ✅ Integration with audit logging

**Activation Steps Required**:
1. Enable tenant isolation in configuration
2. Add tenant_id fields to all MongoDB collections
3. Update all database queries to include tenant filtering
4. Test tenant isolation with multiple tenant data
5. Deploy with multi-tenant configuration

**Risk Level**: Medium (well-tested framework, requires deployment changes)

---

### Q28: Is the hiring loop reusable for other purposes?

**Answer**: Yes, the hiring loop is specifically designed for reuse across different domains:

**Reusable Components**:
- Job/Requirement processing (adaptable to any requirement type)
- Candidate/Entity matching (works with any entity type)
- Application/Request workflow (generic request processing)
- Evaluation/Review process (applicable to any assessment)
- Decision-making workflow (domain-agnostic logic)

**Adaptation Examples**:
- CRM: Lead qualification → Proposal → Approval → Onboarding
- ERP: Purchase request → Approval → Procurement → Receipt
- Project Management: Task creation → Assignment → Review → Completion

**Implementation**: Use the same workflow engine with domain-specific adapters.

---

### Q29: How do I integrate this into my own system?

**Answer**: Integration follows a standardized adapter pattern:

**Integration Methods**:

1. **API Integration** (Recommended):
   - Use REST API endpoints for data exchange
   - Implement webhook callbacks for event notifications
   - Leverage OAuth/JWT for secure authentication

2. **SDK Integration**:
   - Import core workflow engines directly
   - Use domain adapters to map your data structures
   - Implement callback interfaces for custom logic

3. **Database Integration**:
   - Direct MongoDB access with proper tenant isolation
   - Use provided schema definitions
   - Implement proper data synchronization

**Steps**:
1. Identify your domain entities that map to our concepts
2. Create adapter classes for data transformation
3. Configure tenant isolation if needed
4. Implement authentication integration
5. Test with sample data
6. Deploy with monitoring

**Documentation**: See FRAMEWORK_HANDOVER.md for detailed integration guides.

---

### Q30: What should I demonstrate in a demo?

**Answer**: Focus on these key capabilities during demonstrations:

**Primary Demo Flow**:
1. Job creation and posting (show ease of use)
2. Candidate application process (highlight UX)
3. AI-powered matching (emphasize speed and accuracy)
4. Values assessment integration (differentiator)
5. Multi-channel notifications (automation benefits)

**Key Metrics to Highlight**:
- AI matching speed: <0.02s per candidate
- Multi-channel notifications: Email, WhatsApp, Telegram
- Values-based assessment: 5-dimension evaluation
- Workflow automation: From application to decision

**Demo Duration**: 15-20 minutes maximum

**Materials**: Use the DEMO_RUNBOOK.md for step-by-step instructions.

---

### Q31: What are the known limitations for demos?

**Answer**: Be transparent about current limitations:

**Technical Limitations**:
- Operating in single-tenant mode (multi-tenant framework ready but not activated)
- AI model performance may vary with small datasets
- Third-party service dependencies (email/SMS providers)
- Demo data may not reflect production volumes

**Functional Limitations**:
- Advanced reporting features still in development
- Some integration points are mocked/placeholder
- Reinforcement learning feedback loops still learning

**Operational Limitations**:
- Requires stable internet connection
- Dependent on third-party API availability
- Performance may vary during peak usage

**Mitigation**: Always have backup scenarios and pre-recorded examples ready.

---

## 📝 Document Information

**Document Version**: 3.0.0  
**Last Updated**: November 21, 2025  
**Next Review**: February 21, 2026  
**Owner**: Operations Team  
**Approver**: Shashank Mishra

**Related Documents**:
- [RUNBOOK.md](RUNBOOK.md) - Complete operational procedures
- [Quick Start Guide](../docs/guides/QUICK_START_GUIDE.md)
- [Troubleshooting Guide](../docs/guides/TROUBLESHOOTING_GUIDE.md)
- [API Documentation](../docs/api/API_DOCUMENTATION.md)
- [Security Audit](../docs/security/SECURITY_AUDIT.md)

---

**BHIV HR Platform FAQ & Operations Guide** - Comprehensive Q&A for common operations, troubleshooting, and system management.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Status**: ✅ Production Ready | **Services**: 6/6 Live | **Questions Covered**: 44 | **Uptime**: 99.9%

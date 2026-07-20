# 🚀 BHIV HR Platform - Operational Runbook

**Version**: 4.3.1  
**Last Updated**: January 22, 2026  
**Target Audience**: Operations Team, DevOps, System Administrators  
**Platform**: Windows + Docker + Render Cloud + MongoDB Atlas  
**Database**: MongoDB Atlas (Primary)  
**Architecture**: Microservices (111 endpoints)  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites & Requirements](#prerequisites--requirements)
3. [System Startup Procedures](#system-startup-procedures)
4. [System Shutdown Procedures](#system-shutdown-procedures)
5. [Service Management](#service-management)
6. [Database Operations](#database-operations)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Backup & Recovery](#backup--recovery)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Emergency Procedures](#emergency-procedures)
12. [Maintenance Tasks](#maintenance-tasks)
13. [Security Operations](#security-operations)
14. [Deployment Procedures](#deployment-procedures)
15. [Contact & Escalation](#contact--escalation)

---

## 🌐 System Overview

### **Architecture Summary**
- **Type**: Microservices Architecture
- **Services**: 6 services + MongoDB Atlas database
- **Deployment**: Docker containers (local) + Render cloud (production)
- **Total Endpoints**: 111 (80 Gateway + 6 Agent + 25 LangGraph)
- **Database**: MongoDB Atlas (Primary) with 17+ collections

### **Service Inventory**

| Service | Port | Technology | Status | Production URL |
|---------|------|------------|--------|----------------|
| Gateway | 8000 | FastAPI 4.2.0 | ✅ Live | bhiv-hr-gateway-ltg0.onrender.com |
| Agent | 9000 | FastAPI 4.2.0 | ✅ Live | bhiv-hr-agent-nhgg.onrender.com |
| LangGraph | 9001 | FastAPI 4.2.0 | ✅ Live | bhiv-hr-langgraph.onrender.com |
| HR Portal | 8501 | Streamlit 1.41.1 | ✅ Live | bhiv-hr-portal-u670.onrender.com |
| Client Portal | 8502 | Streamlit 1.41.1 | ✅ Live | bhiv-hr-client-portal-3iod.onrender.com |
| Candidate Portal | 8503 | Streamlit 1.41.1 | ✅ Live | bhiv-hr-candidate-portal-abe6.onrender.com |
| Database | 27017 | MongoDB Atlas | ✅ Live | Cluster URL |

### **Key Metrics**
- **Uptime Target**: 99.9%
- **API Response Time**: <100ms average
- **AI Matching Speed**: <0.02s per candidate
- **Database Query Time**: <50ms typical
- **Monthly Cost**: $0 (free tier optimization)

---

## 📋 Prerequisites & Requirements

### **System Requirements**

#### **Local Development**
```yaml
Hardware:
  CPU: 4+ cores (8+ recommended)
  RAM: 8GB minimum (16GB recommended)
  Disk: 50GB free space minimum
  Network: Stable internet connection

Software:
  OS: Windows 10/11, Ubuntu 20.04+, macOS 12+
  Docker: 20.10+ with Docker Compose
  Python: 3.12.7 (for BAT scripts)
  Git: 2.30+
  MongoDB Client: 4.4+ (optional, for direct DB access)
```

#### **Production Environment**
```yaml
Platform: Render Cloud (Oregon, US West)
Services: 6 web services + 1 MongoDB Atlas cluster
Tier: Free tier (optimized for zero cost)
SSL: Automatic HTTPS certificates
CDN: Global content delivery
```

### **Port Requirements**

```bash
# Check port availability (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :5432

# Check port availability (Linux/Mac)
lsof -i :8000  # Gateway
lsof -i :9000  # Agent
lsof -i :9001  # LangGraph
lsof -i :8501  # HR Portal
lsof -i :8502  # Client Portal
lsof -i :8503  # Candidate Portal
lsof -i :27017  # MongoDB Atlas

# Kill process if port is in use (Windows)
taskkill /PID <process_id> /F

# Kill process if port is in use (Linux/Mac)
kill -9 <PID>
```

### **Environment Variables**

#### **Required Variables**
```bash
# Database Configuration
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/bhiv_hr

# Authentication Secrets
API_KEY_SECRET=<YOUR_API_KEY>
JWT_SECRET_KEY=<YOUR_JWT_SECRET>
CANDIDATE_JWT_SECRET_KEY=<YOUR_CANDIDATE_JWT_SECRET>

# Service URLs (Local)
GATEWAY_SERVICE_URL=http://localhost:8000
AGENT_SERVICE_URL=http://localhost:9000
LANGGRAPH_SERVICE_URL=http://localhost:9001

# Service URLs (Production)
GATEWAY_SERVICE_URL=https://bhiv-hr-gateway-ltg0.onrender.com
AGENT_SERVICE_URL=https://bhiv-hr-agent-nhgg.onrender.com
LANGGRAPH_SERVICE_URL=https://bhiv-hr-langgraph.onrender.com
```

#### **Optional Variables (for full functionality)**
```bash
# Communication Services
TWILIO_ACCOUNT_SID=<TWILIO_SID>
TWILIO_AUTH_TOKEN=<TWILIO_TOKEN>
TWILIO_WHATSAPP_NUMBER=+14155238886
GMAIL_EMAIL=<GMAIL_EMAIL>
GMAIL_APP_PASSWORD=<GMAIL_APP_PASSWORD>
TELEGRAM_BOT_TOKEN=<TELEGRAM_TOKEN>

# AI Services
GEMINI_API_KEY=<GEMINI_KEY>
OPENAI_API_KEY=<OPENAI_KEY>

# System Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHON_VERSION=3.12.7
```

### **Secrets Verification**

```bash
# Windows
type .env | findstr API_KEY_SECRET
type .env | findstr DATABASE_URL

# Linux/Mac
grep API_KEY_SECRET .env
grep DATABASE_URL .env

# Verify all required secrets exist
python tools/monitoring/configuration_validator.py
```

---

## 🚀 System Startup Procedures

### **Option 1: Windows BAT Scripts (Recommended for Local)**

#### **First-Time Setup**
```bash
# Step 1: Run first-time setup
setup_first_time.bat

# This will:
# - Check Python installation
# - Create .env from template
# - Create virtual environment
# - Guide through configuration
```

#### **Start All Services**
```bash
# Step 2: Start all services
start_all_services.bat

# This will:
# - Activate virtual environment
# - Install dependencies
# - Start all 6 services in separate windows
# - Display service URLs

# Wait 60 seconds for all services to initialize
```

#### **Verify Services**
```bash
# Step 3: Check service health
check_services.bat

# Expected output:
# ✅ Gateway: http://localhost:8000 - Healthy
# ✅ Agent: http://localhost:9000 - Healthy
# ✅ LangGraph: http://localhost:9001 - Healthy
# ✅ HR Portal: http://localhost:8501 - Running
# ✅ Client Portal: http://localhost:8502 - Running
# ✅ Candidate Portal: http://localhost:8503 - Running
```

### **Option 2: Docker Compose (Production-like Environment)**

#### **Startup Order (Critical)**
```
Database → Gateway → Agent → LangGraph → Portals
```

#### **Full System Startup**
```bash
# Step 1: Start database first
# MongoDB Atlas is managed by cloud provider
# Verify MongoDB connection
python test_mongodb_atlas.py
# Expected: Connection successful

# Step 2: Start Gateway service
docker-compose -f docker-compose.production.yml up -d gateway
sleep 10

# Verify Gateway health
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"BHIV HR Gateway"}

# Step 3: Start Agent and LangGraph services
docker-compose -f docker-compose.production.yml up -d agent langgraph
sleep 10

# Verify services
curl http://localhost:9000/health
curl http://localhost:9001/health

# Step 4: Start all portal services
docker-compose -f docker-compose.production.yml up -d portal client_portal candidate_portal
sleep 15

# Step 5: Final verification
docker-compose -f docker-compose.production.yml ps
```

#### **Quick Start (All at Once)**
```bash
# Start all services together
docker-compose -f docker-compose.production.yml up -d

# Wait for initialization
sleep 30

# Check all services
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### **Health Check Verification**

```bash
# Gateway Service
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl http://localhost:8000/metrics

# Agent Service
curl http://localhost:9000/health
curl http://localhost:9000/test-db

# LangGraph Service
curl http://localhost:9001/health

# Portal Services (should return HTML)
curl -I http://localhost:8501
curl -I http://localhost:8502
curl -I http://localhost:8503

# Database Connection
# MongoDB Atlas connection test
python test_mongodb_atlas.py
```

### **Production Startup (Render)**

```bash
# Production services auto-start on Render
# Manual restart if needed:
# MongoDB Atlas auto-managed - no manual restart required

# Option 1: Via Render Dashboard
# 1. Go to dashboard.render.com
# 2. Select service
# 3. Click "Manual Deploy" → "Deploy Latest Commit"

# Option 2: Via API (if configured)
curl -X POST https://api.render.com/v1/services/{service_id}/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY"

# Check production health
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health
```

---

## 🛑 System Shutdown Procedures

### **Graceful Shutdown (Windows BAT Scripts)**

```bash
# Stop all services gracefully
stop_all_services.bat

# This will:
# - Close all service windows
# - Kill all Python processes
# - Free all ports
# - Clean shutdown
```

### **Graceful Shutdown (Docker Compose)**

```bash
# Step 1: Stop portal services first (no data loss risk)
docker-compose -f docker-compose.production.yml stop portal client_portal candidate_portal
sleep 5

# Step 2: Stop LangGraph and Agent services
docker-compose -f docker-compose.production.yml stop langgraph agent
sleep 5

# Step 3: Stop Gateway service
docker-compose -f docker-compose.production.yml stop gateway
sleep 5

# Step 4: Stop database last (ensure all connections closed)
docker-compose -f docker-compose.production.yml stop db
sleep 5

# Verify all stopped
docker-compose -f docker-compose.production.yml ps
```

### **Quick Shutdown (All Services)**

```bash
# Stop all services at once
docker-compose -f docker-compose.production.yml down

# Stop and remove volumes (CAUTION: deletes data)
# MongoDB Atlas data persists - no volume removal needed

# Stop with timeout (force after 30 seconds)
docker-compose -f docker-compose.production.yml down -t 30
```

### **Emergency Shutdown**

```bash
# Force kill all containers
docker-compose -f docker-compose.production.yml kill

# Remove all containers
docker-compose -f docker-compose.production.yml rm -f

# Clean up everything
docker system prune -a --volumes -f
```

### **Production Shutdown (Render)**

```bash
# Production services should NOT be manually stopped
# Render manages service lifecycle automatically

# To temporarily disable a service:
# 1. Go to Render Dashboard
# 2. Select service
# 3. Suspend service (not recommended for production)

# Services auto-sleep after 15 minutes of inactivity (free tier)
# They wake up automatically on first request (30-60 second delay)
# MongoDB Atlas is always available
```

---

## 🔄 Service Management

### **Individual Service Operations**

#### **Restart Single Service**
```bash
# Windows BAT Scripts
# Close the specific service window and restart:
cd services/gateway
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker Compose
docker-compose -f docker-compose.production.yml restart gateway
docker-compose -f docker-compose.production.yml restart agent
docker-compose -f docker-compose.production.yml restart langgraph
docker-compose -f docker-compose.production.yml restart portal
```

#### **View Service Logs**
```bash
# Docker Compose - Real-time logs
docker-compose -f docker-compose.production.yml logs -f gateway
docker-compose -f docker-compose.production.yml logs -f agent
docker-compose -f docker-compose.production.yml logs -f langgraph

# Docker Compose - Last 50 lines
docker-compose -f docker-compose.production.yml logs --tail=50 gateway

# Docker Compose - All services
docker-compose -f docker-compose.production.yml logs -f

# Production (Render) - Via Dashboard
# Go to dashboard.render.com → Select service → Logs tab
```

#### **Service Status Check**
```bash
# Docker Compose
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

# Production status
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
```

### **Service Dependencies**

```yaml
Dependency Chain:
  MongoDB Atlas (cloud-managed)
    ↓
  Gateway (depends on MongoDB)
    ↓
  Agent (depends on MongoDB)
  LangGraph (depends on MongoDB)
    ↓
  Portals (depend on Gateway)

Restart Order:
  1. MongoDB Atlas (verify connectivity)
  2. Gateway
  3. Agent + LangGraph (parallel)
  4. Portals (parallel)
```

### **Rolling Restart (Zero Downtime)**

```bash
# Not applicable for local development
# For production on Render:
# 1. Deploy new version to staging first
# 2. Test thoroughly
# 3. Deploy to production (Render handles rolling update)
# 4. Monitor health checks during deployment
```

---

## 🗄️ Database Operations

### **Database Connection**

```bash
# Connect to local database
# MongoDB Atlas connection
python test_mongodb_atlas.py

# Connect to production database (if credentials available)
# MongoDB Atlas connection via MongoDB Compass or CLI
# Connection string: mongodb+srv://user:pass@cluster.mongodb.net/bhiv_hr

# Using database tools
python tools/database/database_url_checker.py
```

### **Database Health Checks**

```bash
# Check database is running
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT 1"

# Check database size
# MongoDB Atlas size monitoring via dashboard
# Or use MongoDB Compass for detailed metrics

# Check table counts
# MongoDB Atlas collection sizes
# Use MongoDB Compass or Atlas dashboard for collection metrics

# Check active connections
# MongoDB Atlas connection monitoring
# View in Atlas dashboard or use MongoDB monitoring tools

# Comprehensive database check
python tools/database/precise_db_check.py
```

### **Database Schema Management**

```bash
# Check current schema version
# MongoDB Atlas schema version tracking
# Use MongoDB schema validation or version collection

# List all tables
# MongoDB Atlas collections
# Use MongoDB Compass or Atlas UI to view collections

# Describe specific table
# MongoDB Atlas collection schema
# Use MongoDB Compass to inspect collection structure

# Check indexes
# MongoDB Atlas indexes
# View in Atlas dashboard or use db.collection.getIndexes()

# Deploy schema updates
python tools/database/database_sync_manager.py

# Deploy workflow schema
python tools/database/deploy_workflow_schema.py
```

### **Data Management**

```bash
# Load candidates from CSV
python tools/database/load_candidates.py --file=data/candidates.csv

# Extract resumes
python tools/data/comprehensive_resume_extractor.py

# Create sample jobs
python tools/data/dynamic_job_creator.py

# Sync database
python tools/database/database_sync_manager.py
```

---

## 📊 Monitoring & Health Checks

### **Automated Health Monitoring**

```bash
# Run continuous health checks (Windows)
# Create scheduled task to run every minute:
check_services.bat

# Run continuous health checks (Linux/Mac)
while true; do
  curl -s http://localhost:8000/health | jq
  curl -s http://localhost:9000/health | jq
  curl -s http://localhost:9001/health | jq
  sleep 60
done

# Service connection validator
python tools/monitoring/service_connection_validator.py

# Auto-sync watcher (monitors file changes)
python tools/monitoring/auto_sync_watcher.py
```

### **Health Check Endpoints**

```bash
# Gateway Health Checks
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"BHIV HR Gateway","version":"4.2.0"}

curl http://localhost:8000/health/detailed
# Response: Detailed health with database, services, memory, CPU

curl http://localhost:8000/metrics
# Response: Prometheus metrics

curl http://localhost:8000/metrics/dashboard
# Response: HTML dashboard with real-time metrics

# Agent Health Checks
curl http://localhost:9000/health
curl http://localhost:9000/test-db

# LangGraph Health Checks
curl http://localhost:9001/health

# Production Health Checks
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health
```

### **Performance Monitoring**

```bash
# System resource usage
docker stats --no-stream

# Service-specific metrics
curl http://localhost:8000/metrics | grep -E "request_count|response_time|error_rate"

# Database performance
# MongoDB Atlas performance monitoring
# Use Atlas Performance Advisor or MongoDB profiler

# API response time testing
time curl http://localhost:8000/v1/candidates

# Load testing (if needed)
# ab -n 1000 -c 10 http://localhost:8000/health
```

### **Log Monitoring**

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Search for errors
docker-compose -f docker-compose.production.yml logs | grep -i error

# Search for specific patterns
docker-compose -f docker-compose.production.yml logs gateway | grep -i "authentication"

# Export logs to file
docker-compose -f docker-compose.production.yml logs > system_logs_$(date +%Y%m%d).log

# Production logs
# Access via Render Dashboard → Service → Logs
```

---

## 💾 Backup & Recovery

### **Database Backup**

#### **Manual Backup**
```bash
# Create backup
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user bhiv_hr > backup_$(date +%Y%m%d_%H%M%S).sql

# Create compressed backup
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user bhiv_hr | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user -t candidates -t jobs bhiv_hr > backup_core_tables.sql

# Backup schema only
docker-compose -f docker-compose.production.yml exec db \
  pg_dump -U bhiv_user --schema-only bhiv_hr > schema_backup.sql
```

#### **Automated Backup Script**
```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bhiv_hr_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
docker-compose -f docker-compose.production.yml exec -T db \
  pg_dump -U bhiv_user bhiv_hr | gzip > $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

#### **Schedule Automated Backups**
```bash
# Windows Task Scheduler
# 1. Open Task Scheduler
# 2. Create Basic Task
# 3. Trigger: Daily at 2:00 AM
# 4. Action: Run scripts/backup_database.sh
# 5. Save

# MongoDB Atlas provides automated backups
# Configure via Atlas dashboard: Backup → Cloud Backup
```

### **Database Restore**

#### **Full Restore**
```bash
# Stop all services first
docker-compose -f docker-compose.production.yml stop gateway agent langgraph portal client_portal candidate_portal

# Restore from backup
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

#### **Point-in-Time Recovery**
```bash
# Restore to specific point (if WAL archiving enabled)
# This requires PostgreSQL WAL archiving configuration

# 1. Stop database
docker-compose -f docker-compose.production.yml stop db

# 2. Restore base backup
# 3. Apply WAL files up to desired point
# 4. Start database

# Note: WAL archiving not configured by default
# Contact database administrator for setup
```

### **Production Backup (Render)**

```bash
# MongoDB Atlas automated backups (7-30 days retention)
# Access via Atlas Dashboard:
# 1. Go to Cluster → Backup
# 2. View snapshots or create manual backup
# 3. Restore from any snapshot point-in-time

# Manual backup via mongodump
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/bhiv_hr" --out=backup
```

---

## ⚡ Performance Optimization

### **Database Optimization**

#### **Vacuum and Analyze**
```bash
# MongoDB Atlas auto-optimization
# No manual VACUUM needed - Atlas handles optimization

# Vacuum specific table
# MongoDB Atlas collection optimization
# Use Atlas Performance Advisor for recommendations

# Full vacuum (requires more time and locks)
# MongoDB Atlas compaction
# Use Atlas dashboard to compact collections if needed
```

#### **Index Management**
```bash
# List all indexes
# MongoDB Atlas indexes
# View in Atlas dashboard or use db.collection.getIndexes()

# Check index usage
# MongoDB Atlas index usage statistics
# Use Atlas Performance Advisor or db.collection.stats()

# Rebuild indexes (if needed)
# MongoDB Atlas index rebuild
# Drop and recreate indexes via Atlas dashboard if needed
```

#### **Query Optimization**
```bash
# Find slow queries
# MongoDB Atlas slow query analysis
# Use Atlas Performance Advisor or MongoDB profiler

# Explain query plan
# MongoDB Atlas query analysis
# Use Atlas Performance Advisor or explain() method
```

### **Application Performance**

#### **Connection Pool Optimization**
```python
# Current configuration in services/gateway/app/main.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # Increase if needed
    max_overflow=5,      # Increase if needed
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### **Caching Strategy**
```bash
# Clear application cache
curl -X POST http://localhost:8000/admin/clear-cache

# Check cache hit rate
curl http://localhost:8000/metrics | grep cache_hit_rate
```

### **Resource Monitoring**
```bash
# Monitor Docker resource usage
docker stats

# Set resource limits (if needed)
docker update --memory=1g --cpus=1.0 bhiv-hr-gateway
docker update --memory=1g --cpus=1.0 bhiv-hr-agent
```

---

## 🔧 Troubleshooting Guide

### **Common Issues & Solutions**

#### **Issue 1: Service Won't Start**

**Symptoms:**
- Container exits immediately
- "Port already in use" error
- "Connection refused" errors

**Diagnostic Steps:**
```bash
# Check if port is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Check container logs
docker-compose -f docker-compose.production.yml logs gateway --tail=50

# Check environment variables
docker-compose -f docker-compose.production.yml exec gateway env | grep DATABASE_URL
```

**Solutions:**
```bash
# Solution 1: Kill process using port
taskkill /PID <process_id> /F  # Windows
kill -9 <PID>                   # Linux/Mac

# Solution 2: Restart with fresh state
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Solution 3: Check .env file
type .env  # Windows
cat .env   # Linux/Mac
# Ensure all required variables are set

# Solution 4: Rebuild container
docker-compose -f docker-compose.production.yml build gateway
docker-compose -f docker-compose.production.yml up -d gateway
```

#### **Issue 2: Database Connection Failures**

**Symptoms:**
- "Connection refused" errors
- "Connection timeout" errors
- Services can't reach database

**Diagnostic Steps:**
```bash
# Check if database is running
docker-compose -f docker-compose.production.yml ps db

# Check database logs
docker-compose -f docker-compose.production.yml logs db --tail=50

# Test database connection
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "SELECT 1"

# Check connection count
# MongoDB Atlas connection monitoring
# View in Atlas dashboard
```

**Solutions:**
```bash
# Solution 1: Restart database
# MongoDB Atlas restart not needed - cloud managed
sleep 10

# Solution 2: Check DATABASE_URL format
# Correct format: mongodb+srv://user:pass@cluster.mongodb.net/dbname

# Solution 3: Clear connection pool
docker-compose -f docker-compose.production.yml restart gateway agent langgraph

# Solution 4: Check for long-running queries
# MongoDB Atlas long-running operations
# Use Atlas dashboard or db.currentOp()

# Kill long-running query if needed
# MongoDB Atlas operation termination
# Use Atlas dashboard or db.killOp(<opid>)
```

#### **Issue 3: Authentication Failures**

**Symptoms:**
- 401 Unauthorized errors
- "Invalid API key" messages
- JWT token validation failures

**Diagnostic Steps:**
```bash
# Test API key
curl -H "Authorization: Bearer <YOUR_API_KEY>" \
  http://localhost:8000/v1/candidates

# Check API keys in database
python tools/security/get_all_api_keys.py

# Verify JWT secrets match
type .env | findstr JWT_SECRET_KEY  # Windows
grep JWT_SECRET_KEY .env            # Linux/Mac
# Also check MONGODB_URI for database connection
```

**Solutions:**
```bash
# Solution 1: Verify API key format
# Should be: Bearer <YOUR_API_KEY>

# Solution 2: Check environment variables
docker-compose -f docker-compose.production.yml exec gateway \
  env | grep API_KEY_SECRET

# Solution 3: Fix authentication
python tools/utilities/fix_auth_simple.py

# Solution 4: Fix portal authentication
python tools/utilities/fix_portal_auth.py

# Solution 5: Generate new API key
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients SET api_key_secret = gen_random_uuid() 
  WHERE client_id='TECH001' RETURNING api_key_secret"
```

#### **Issue 4: AI Matching Not Working**

**Symptoms:**
- AI rank stays null
- Matching returns empty results
- Timeout errors on matching

**Diagnostic Steps:**
```bash
# Check Agent service health
curl http://localhost:9000/health

# Check Agent logs
docker-compose -f docker-compose.production.yml logs agent --tail=50

# Test database connection from Agent
curl http://localhost:9000/test-db

# Check if Phase 3 engine loaded
docker-compose -f docker-compose.production.yml logs agent | grep -i "ai\|matching"
```

**Solutions:**
```bash
# Solution 1: Restart Agent service
docker-compose -f docker-compose.production.yml restart agent
sleep 10
curl http://localhost:9000/health

# Solution 2: Check candidate has skills
# MongoDB Atlas candidate data check
# Use MongoDB Compass or db.candidates.findOne({id: 1})

# Solution 3: Manually trigger matching
curl -X POST http://localhost:8000/v1/match/1/top \
  -H "Authorization: Bearer <YOUR_API_KEY>"

# Solution 4: Clear matching cache
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "TRUNCATE TABLE matching_cache"
```

#### **Issue 5: Portal Not Loading**

**Symptoms:**
- Portal shows loading screen indefinitely
- Streamlit errors
- Connection timeouts

**Diagnostic Steps:**
```bash
# Check portal status
curl -I http://localhost:8501

# Check portal logs
docker-compose -f docker-compose.production.yml logs portal --tail=50

# Check if Gateway is accessible from portal
docker-compose -f docker-compose.production.yml exec portal \
  curl http://gateway:8000/health
```

**Solutions:**
```bash
# Solution 1: Clear browser cache
# Press Ctrl+Shift+R (hard refresh)
# Or use incognito mode

# Solution 2: Restart portal
docker-compose -f docker-compose.production.yml restart portal
sleep 15

# Solution 3: Check GATEWAY_SERVICE_URL
docker-compose -f docker-compose.production.yml exec portal \
  env | grep GATEWAY_SERVICE_URL

# Solution 4: Rebuild portal
docker-compose -f docker-compose.production.yml build portal
docker-compose -f docker-compose.production.yml up -d portal
```

#### **Issue 6: Notifications Not Sending**

**Symptoms:**
- WhatsApp messages not delivered
- Emails not received
- Workflow status shows failed

**Diagnostic Steps:**
```bash
# Check LangGraph service
curl http://localhost:9001/health

# Check LangGraph logs
docker-compose -f docker-compose.production.yml logs langgraph | grep -i "notification\|twilio\|email"

# Check workflow status
# MongoDB Atlas workflow status check
# Use db.workflows.find({status: "failed"}).sort({created_at: -1}).limit(10)
```

**Solutions:**
```bash
# Solution 1: Test notification manually
python tools/utilities/send_test_messages.py --channel=whatsapp --to="+15551234567"

# Solution 2: Check credentials
type .env | findstr TWILIO  # Windows
grep TWILIO .env            # Linux/Mac
# Also check GMAIL_, TELEGRAM_ credentials

# Solution 3: Restart LangGraph
docker-compose -f docker-compose.production.yml restart langgraph

# Solution 4: Test direct notification
curl -X POST http://localhost:9001/tools/send-notification \
  -H "Content-Type: application/json" \
  -d '{"channel":"whatsapp","to":"+15551234567","message":"Test"}'

# Solution 5: WhatsApp diagnostics
python tools/utilities/whatsapp_diagnostic.py
```

#### **Issue 7: Slow Performance**

**Symptoms:**
- API responses >2 seconds
- Dashboard loading slowly
- Database queries timing out

**Diagnostic Steps:**
```bash
# Check system resources
docker stats --no-stream

# Check API response time
time curl http://localhost:8000/v1/candidates

# Check database performance
# MongoDB Atlas performance monitoring
# Use Atlas Performance Advisor or profiler

# Check for missing indexes
python tools/database/precise_db_check.py
```

**Solutions:**
```bash
# Solution 1: Run VACUUM ANALYZE
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "VACUUM ANALYZE"

# Solution 2: Restart services
docker-compose -f docker-compose.production.yml restart

# Solution 3: Clear caches
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "TRUNCATE TABLE matching_cache"

# Solution 4: Check for long-running queries
# MongoDB Atlas long-running operations
# Use Atlas dashboard or db.currentOp()
```

### **Diagnostic Tools**

```bash
# Analysis Tools
python tools/analysis/count_all_endpoints.py
python tools/analysis/gateway_endpoint_analysis.py
python tools/analysis/dependency_analysis.py

# Database Tools
python tools/database/database_url_checker.py
python tools/database/precise_db_check.py
python tools/database/database_sync_manager.py

# Monitoring Tools
python tools/monitoring/service_connection_validator.py
python tools/monitoring/configuration_validator.py
python tools/monitoring/check_file_usage.py

# Security Tools
python tools/security/check_api_keys.py
python tools/security/get_all_api_keys.py
python tools/security/security_audit_checker.py

# Portal Tools
python tools/portal/simple_portal_explorer.py
python tools/portal/comprehensive_portal_explorer.py
```

---

## 🚨 Emergency Procedures

### **Emergency Response Plan**

#### **Severity Levels**

| Level | Description | Response Time | Action |
|-------|-------------|---------------|--------|
| **Critical** | System down, data loss | Immediate | All hands on deck |
| **High** | Service degraded, affecting users | 15 minutes | Senior team member |
| **Medium** | Feature broken, workaround available | 1 hour | Assigned developer |
| **Low** | Minor issue, no user impact | Next business day | Regular workflow |

#### **Emergency Contacts**

```yaml
Primary Contact:
  Name: Ishan Shirode
  Role: Lead Backend Engineer
  Contact: [Team communication channel]
  Availability: 24/7 for Critical issues

Secondary Contact:
  Name: Operations Team Lead
  Role: Team Lead
  Contact: [Team communication channel]
  Availability: Business hours

Escalation Path:
  1. Operations Team Member (first responder)
  2. Team Lead (if not resolved in 15 minutes)
  3. Ishan Shirode (if Critical or not resolved in 1 hour)
  4. Management (if downtime >30 minutes)
```

### **Emergency Scenario: Complete System Failure**

#### **Immediate Actions (First 5 Minutes)**

```bash
# Step 1: Assess impact
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Step 2: Check Render platform status
# Visit: https://status.render.com

# Step 3: Notify team
# Post in #hr-platform-incidents Slack channel:
# "🚨 INCIDENT: [Service] down. Investigating. ETA: [time]"

# Step 4: Quick restart attempt
# Via Render Dashboard:
# - Go to each service
# - Click "Manual Deploy" → "Deploy Latest Commit"

# Step 5: Monitor restart
# Watch logs in Render Dashboard
# Test health endpoints every 30 seconds
```

#### **Recovery Actions (5-30 Minutes)**

```bash
# If quick restart failed:

# Step 1: Check recent deployments
# Render Dashboard → Service → Deploys
# Identify last successful deployment

# Step 2: Rollback if needed
# Click "Rollback" on last working deployment

# Step 3: Check environment variables
# Render Dashboard → Service → Environment
# Verify all required variables are set

# Step 4: Check database
# Render Dashboard → Database → Metrics
# Verify database is accessible

# Step 5: Check logs for errors
# Look for patterns:
# - "Connection refused"
# - "Out of memory"
# - "Port already in use"
# - "Environment variable not set"

# Step 6: If database issue suspected
# Render Dashboard → Database → Backups
# Consider restore if corruption suspected
```

#### **Communication Protocol**

```yaml
Initial Notification (within 5 minutes):
  Channel: #hr-platform-incidents
  Message: "🚨 INCIDENT: [Description]. Status: Investigating. ETA: [time]"
  
Updates (every 15 minutes):
  Channel: #hr-platform-incidents
  Message: "📊 UPDATE: [Progress]. Next step: [action]. ETA: [time]"
  
Resolution:
  Channel: #hr-platform-incidents
  Message: "✅ RESOLVED: [Summary]. Root cause: [cause]. Prevention: [steps]"
  
Post-Mortem (within 24 hours):
  Document: handover/incidents/YYYY-MM-DD-incident-report.md
  Include: Timeline, root cause, resolution, prevention measures
```

### **Emergency Scenario: Database Corruption**

```bash
# CRITICAL: Stop all services immediately
docker-compose -f docker-compose.production.yml down

# Step 1: Assess damage
docker-compose -f docker-compose.production.yml up -d db
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT pg_database.datname, 
         pg_size_pretty(pg_database_size(pg_database.datname)) 
  FROM pg_database"

# Step 2: Check for corruption
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT * FROM pg_stat_database WHERE datname='bhiv_hr'"

# Step 3: Restore from backup
# Use most recent backup
gunzip -c backups/bhiv_hr_latest.sql.gz | \
  docker-compose -f docker-compose.production.yml exec -T db \
  psql -U bhiv_user bhiv_hr

# Step 4: Verify data integrity
python tools/database/precise_db_check.py

# Step 5: Restart services
docker-compose -f docker-compose.production.yml up -d

# Step 6: Verify system health
curl http://localhost:8000/health
curl http://localhost:8000/v1/candidates

# ESCALATE IMMEDIATELY TO ISHAN SHIRODE
```

### **Emergency Scenario: Security Breach**

```bash
# IMMEDIATE ACTIONS:

# Step 1: Isolate affected service
docker-compose -f docker-compose.production.yml stop <affected_service>

# Step 2: Change all credentials
# Update .env file with new credentials
# Restart services with new credentials

# Step 3: Check for exposed secrets
python tools/utilities/find_exposed_keys.py

# Step 4: Audit recent access
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT * FROM audit_logs 
  WHERE created_at > NOW() - INTERVAL '24 hours' 
  ORDER BY created_at DESC"

# Step 5: Run security audit
python tools/security/security_audit_checker.py

# Step 6: Check for unauthorized changes
git log --since="24 hours ago" --all

# ESCALATE IMMEDIATELY TO ISHAN SHIRODE AND SECURITY TEAM
```

---

## 🔄 Maintenance Tasks

### **Daily Maintenance**

```bash
# Morning Health Check (9:00 AM)
check_services.bat  # Windows
# Or
python tools/monitoring/service_connection_validator.py

# Check production health
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Check error logs
docker-compose -f docker-compose.production.yml logs --since=24h | grep -i error

# Check database connections
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT count(*) as connections FROM pg_stat_activity"
```

### **Weekly Maintenance**

```bash
# Sunday 2:00 AM - Automated via Task Scheduler/Cron

# 1. Database backup
bash scripts/backup_database.sh

# 2. Database optimization
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "VACUUM ANALYZE"

# 3. Clear old logs (keep last 30 days)
find logs/ -name "*.log" -mtime +30 -delete

# 4. Check disk space
df -h

# 5. Update dependencies (if needed)
# Review and apply security updates

# 6. Performance review
python tools/analysis/dependency_analysis.py
```

### **Monthly Maintenance**

```bash
# First Sunday of month - 2:00 AM

# 1. Full database backup
bash scripts/backup_database.sh

# 2. Security audit
python tools/security/security_audit_checker.py

# 3. Check for exposed secrets
python tools/utilities/find_exposed_keys.py

# 4. Review API keys
python tools/security/get_all_api_keys.py

# 5. Database statistics
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  SELECT schemaname, tablename, 
         pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
         n_live_tup as row_count
  FROM pg_tables 
  JOIN pg_stat_user_tables USING (schemaname, tablename)
  WHERE schemaname = 'public' 
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC"

# 6. Review and rotate credentials (every 90 days)
# Update API keys, JWT secrets, database passwords

# 7. Test backup restore
# Restore to test environment and verify
```

### **Quarterly Maintenance**

```bash
# First Sunday of quarter - 2:00 AM

# 1. Full system audit
python tools/security/security_audit_checker.py

# 2. Dependency updates
# Review and update all Python packages
pip list --outdated

# 3. Database schema review
python tools/database/precise_db_check.py

# 4. Performance benchmarking
# Run load tests and compare with baseline

# 5. Documentation review
# Update all documentation with recent changes

# 6. Disaster recovery test
# Test full system restore from backup

# 7. Security penetration testing
# Run security tests on all endpoints
```

---

## 🔒 Security Operations

### **Security Monitoring**

```bash
# Daily security checks
python tools/security/check_api_keys.py
python tools/security/security_audit_checker.py

# Check for failed login attempts
# MongoDB Atlas audit logs
# Use Atlas dashboard or db.audit_logs.find()

# Check rate limiting status
curl http://localhost:8000/v1/security/rate-limit-status

# Check blocked IPs
curl http://localhost:8000/v1/security/blocked-ips

# Check CSP violations
curl http://localhost:8000/v1/security/csp-violations
```

### **Credential Management**

```bash
# Rotate API keys (every 90 days)
docker-compose -f docker-compose.production.yml exec db \
  psql -U bhiv_user -d bhiv_hr -c "
  UPDATE clients SET api_key_secret = gen_random_uuid() 
  WHERE client_id='TECH001' RETURNING api_key_secret"

# Update JWT secrets
# 1. Generate new secret: openssl rand -hex 32
# 2. Update .env file
# 3. Restart all services
docker-compose -f docker-compose.production.yml restart

# Update database password
# 1. Change password in MongoDB Atlas
# 2. Update MONGODB_URI in .env
# 3. Restart all services
```

### **Security Incident Response**

```bash
# If security incident detected:

# 1. Isolate affected service
docker-compose -f docker-compose.production.yml stop <service>

# 2. Collect evidence
docker-compose -f docker-compose.production.yml logs <service> > incident_logs.txt

# 3. Check audit logs
# MongoDB Atlas audit logs
# Export from Atlas dashboard or use db.audit_logs.find()

# 4. Change all credentials
# 5. Run security audit
python tools/security/security_audit_checker.py

# 6. Document incident
# Create incident report in handover/incidents/

# 7. Notify security team
# ESCALATE IMMEDIATELY TO ISHAN SHIRODE
```

---

## 🚀 Deployment Procedures

### **Local Deployment**

```bash
# Step 1: Pull latest code
git pull origin main

# Step 2: Update dependencies
pip install -r requirements.txt

# Step 3: Run database migrations
python tools/database/database_sync_manager.py

# Step 4: Restart services
docker-compose -f docker-compose.production.yml restart

# Step 5: Verify deployment
check_services.bat
curl http://localhost:8000/health
```

### **Production Deployment (Render)**

```bash
# Automatic deployment on git push to main branch

# Step 1: Test locally first
docker-compose -f docker-compose.production.yml up -d
# Run all tests
python tests/run_all_tests.py

# Step 2: Commit and push
git add .
git commit -m "Description of changes"
git push origin main

# Step 3: Monitor deployment
# Render Dashboard → Service → Logs
# Watch for successful deployment message

# Step 4: Verify production
curl https://bhiv-hr-gateway-ltg0.onrender.com/health
curl https://bhiv-hr-agent-nhgg.onrender.com/health
curl https://bhiv-hr-langgraph.onrender.com/health

# Step 5: Test critical endpoints
curl -H "Authorization: Bearer <API_KEY_SECRET>" \
  https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates

# Step 6: Monitor for errors
# Check Render logs for 15 minutes after deployment
```

### **Rollback Procedure**

```bash
# If deployment fails:

# Option 1: Rollback via Render Dashboard
# 1. Go to Service → Deploys
# 2. Find last successful deployment
# 3. Click "Rollback"

# Option 2: Rollback via Git
git revert HEAD
git push origin main
# Render will auto-deploy previous version

# Option 3: Manual rollback
git reset --hard <previous_commit_hash>
git push -f origin main
# CAUTION: Force push, use only in emergencies
```

---

## 📞 Contact & Escalation

### **Escalation Matrix**

| Issue Type | Severity | Response Time | Contact |
|------------|----------|---------------|---------|
| System Down | Critical | Immediate | Shashank Mishra |
| Data Loss | Critical | Immediate | Shashank Mishra |
| Security Breach | Critical | Immediate | Shashank + Security Team |
| Service Degraded | High | 15 minutes | Team Lead |
| Feature Broken | Medium | 1 hour | Assigned Developer |
| Minor Bug | Low | Next business day | Regular workflow |

### **Contact Information**

```yaml
Primary Contact:
  Name: Ishan Shirode
  Role: Lead Backend Engineer
  Contact: Team communication channel
  GitHub: @ishan-shirode
  Availability: 24/7 for Critical issues

Operations Team:
  Channel: #hr-platform-ops
  Response: Business hours (9 AM - 6 PM)
  
Incident Channel:
  Channel: #hr-platform-incidents
  Purpose: Real-time incident communication
  
Documentation:
  GitHub: https://github.com/Shashank-0208/BHIV-HR-PLATFORM
  Render: https://dashboard.render.com
```

### **When to Escalate**

```yaml
Immediate Escalation (Contact Ishan Shirode):
  - Production system completely down
  - Database corruption or data loss
  - Security breach detected
  - Multiple services failing
  - Unknown critical errors

15-Minute Escalation (Contact Team Lead):
  - Service degraded but operational
  - Performance issues affecting users
  - Authentication problems
  - Network/infrastructure issues

1-Hour Escalation (Contact Developer):
  - Feature not working as expected
  - Non-critical bugs
  - Configuration issues
  - Documentation updates needed

No Escalation Needed:
  - Minor UI issues
  - Documentation typos
  - Feature requests
  - General questions
```

### **Incident Reporting**

```yaml
What to Include in Incident Report:
  - Timestamp of incident
  - Services affected
  - User impact (number of users, severity)
  - Error messages and logs
  - Steps already attempted
  - System metrics (CPU, memory, disk)
  - Last known good state
  - Current status

Where to Report:
  - Slack: #hr-platform-incidents
  - GitHub: Create issue with [URGENT] tag
  - Email: For critical issues only

Follow-up:
  - Post-mortem document within 24 hours
  - Root cause analysis
  - Prevention measures
  - Documentation updates
```

---

## 📚 Quick Reference

### **Essential Commands**

```bash
# Start System
start_all_services.bat                    # Windows
docker-compose -f docker-compose.production.yml up -d  # Docker

# Stop System
stop_all_services.bat                     # Windows
docker-compose -f docker-compose.production.yml down   # Docker

# Check Health
check_services.bat                        # Windows
curl http://localhost:8000/health         # API

# View Logs
docker-compose -f docker-compose.production.yml logs -f

# Database Backup
bash scripts/backup_database.sh

# Database Restore
cat backup.sql | docker-compose -f docker-compose.production.yml exec -T db psql -U bhiv_user bhiv_hr

# Restart Service
docker-compose -f docker-compose.production.yml restart gateway
```

### **Important URLs**

```yaml
Local Development:
  Gateway API: http://localhost:8000/docs
  Agent API: http://localhost:9000/docs
  LangGraph API: http://localhost:9001/docs
  HR Portal: http://localhost:8501
  Client Portal: http://localhost:8502
  Candidate Portal: http://localhost:8503

Production:
  Gateway API: https://bhiv-hr-gateway-ltg0.onrender.com/docs
  Agent API: https://bhiv-hr-agent-nhgg.onrender.com/docs
  LangGraph API: https://bhiv-hr-langgraph.onrender.com/docs
  HR Portal: https://bhiv-hr-portal-u670.onrender.com
  Client Portal: https://bhiv-hr-client-portal-3iod.onrender.com
  Candidate Portal: https://bhiv-hr-candidate-portal-abe6.onrender.com

Management:
  Render Dashboard: https://dashboard.render.com
  GitHub Repository: https://github.com/Shashank-0208/BHIV-HR-PLATFORM
```

### **Demo Credentials**

```yaml
Client Portal:
  Username: TECH001
  Password: demo123

API Testing:
  API Key: Check .env file or database
  Format: Bearer <YOUR_API_KEY>

Database:
  Cluster: MongoDB Atlas
  Database: bhiv_hr
  Connection: mongodb+srv://
```

---

## 📝 Document Information

**Document Version**: 4.3.1  
**Last Updated**: January 22, 2026  
**Next Review**: April 22, 2026  
**Owner**: Operations Team  
**Approver**: Ishan Shirode

**Change Log**:
- v3.0.0 (Nov 21, 2025): Complete rewrite with comprehensive procedures
- v2.0.0 (Nov 15, 2025): Added production deployment procedures
- v1.0.0 (Nov 1, 2025): Initial version

**Related Documents**:
- [Quick Start Guide](../docs/guides/QUICK_START_GUIDE.md)
- [Troubleshooting Guide](../docs/guides/TROUBLESHOOTING_GUIDE.md)
- [FAQ Operations](FAQ.md)
- [Deployment Guide](../docs/guides/DEPLOYMENT_GUIDE.md)
- [Security Audit](../docs/security/SECURITY_AUDIT.md)

---

**BHIV HR Platform Operational Runbook** - Complete operational procedures for system management, maintenance, and emergency response.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Status**: ✅ Production Ready | **Services**: 6/6 Live | **Uptime**: 99.9% | **Cost**: $0/month

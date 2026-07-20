# 🚀 BHIV HR Platform - Complete Deployment Guide

**Enterprise AI-Powered Recruiting Platform Deployment**  
**Version**: v4.3.0 with Complete RL Integration  
**Updated**: January 22, 2026  
**Status**: ✅ Production Ready  
**Services**: 3/3 Core Services Operational | **Cost**: $0/month | **Uptime**: 99.9% | **Database**: MongoDB Atlas

---

## 📊 Current Production Status

### **Live System Overview**
- **Platform**: Three-Port Architecture (8000/Gateway, 9000/Agent, 9001/LangGraph)
- **Services**: 3 core microservices fully operational
- **Database**: MongoDB Atlas with 17+ collections (fully migrated from PostgreSQL)
- **Total Endpoints**: 111 (80 Gateway + 6 Agent + 25 LangGraph)
- **Performance**: <100ms API response, <0.02s AI matching
- **Security**: Triple authentication with 2FA support

### **Service Status Dashboard**
| Service | Port | URL | Status | Endpoints |
|---------|------|-----|--------|-----------|
| **API Gateway** | 8000 | http://localhost:8000/docs | ✅ Live | 77 |
| **AI Agent** | 9000 | http://localhost:9000/docs | ✅ Live | 6 |
| **LangGraph** | 9001 | http://localhost:9001/docs | ✅ Live | 25 |

**Demo Access**: Username: `demo_user` | Password: `demo_password` | Client: `TECH001` / `demo123`

---

## 🎯 Deployment Options

### **Option 1: Use Local Development System (Recommended)**
**Best for**: Testing, evaluation, immediate use  
**Time**: 5 minutes  
**Cost**: Free

1. **Access Local Platform**
   - Visit API Documentation at http://localhost:8000/docs
   - Test all 111 endpoints locally
   - Real-time AI matching and workflow automation

2. **Get API Access**
   - API Key available in .env file
   - All 111 endpoints ready for testing
   - Three-port architecture (8000, 9000, 9001)

### **Option 2: Local Development Setup**
**Best for**: Development, customization, learning  
**Time**: 15-30 minutes  
**Requirements**: Docker, Git, 4GB RAM

### **Option 3: Cloud Deployment (Render)**
**Best for**: Production deployment, scaling  
**Time**: 45-60 minutes  
**Cost**: Free tier available

---

## 💻 Local Development Deployment

### **Prerequisites**
```bash
# Required software
- Docker Desktop 4.0+
- Git 2.30+
- Python 3.12.7
- 4GB RAM minimum
- 10GB disk space
```

### **Quick Start (5 Minutes)**
```bash
# 1. Clone repository
git clone https://github.com/Shashank-0208/BHIV-HR-PLATFORM.git
cd BHIV-HR-Platform

# 2. Setup environment
cp .env.example .env
# Edit .env with your credentials (optional for local testing)

# 3. Start all services
docker-compose -f docker-compose.production.yml up -d

# 4. Verify deployment
curl http://localhost:8000/health
```

### **Detailed Local Setup**

#### **Step 1: Environment Configuration**
```bash
# Create environment file
cat > .env << EOF
# Database Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr

# API Configuration
API_KEY_SECRET=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# AI Configuration (Optional)
OPENAI_API_KEY=your-openai-key-here

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
```

#### **Step 2: Database Setup**
```bash
# MongoDB Atlas is cloud-hosted - no local initialization required
# Ensure your MongoDB Atlas cluster is configured and accessible

# Verify MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb+srv://username:password@cluster.mongodb.net/'); print('MongoDB connected successfully')"
```

#### **Step 3: Service Deployment**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### **Step 4: Verification**
```bash
# Test API Gateway (77 endpoints)
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Test AI Agent (6 endpoints)
curl http://localhost:9000/health
curl http://localhost:9000/docs

# Test LangGraph (25 endpoints)
curl http://localhost:9001/health
curl http://localhost:9001/docs

# Test Database Connectivity
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/test-candidates
```

### **Local Service URLs**
- **API Gateway**: http://localhost:8000/docs (77 endpoints)
- **AI Agent**: http://localhost:9000/docs (6 endpoints)
- **LangGraph**: http://localhost:9001/docs (25 endpoints)
- **Database**: MongoDB Atlas (cloud-hosted)

---

## ☁️ Cloud Deployment (Render)

### **Prerequisites**
- GitHub account with repository access
- Render account (free tier available)
- MongoDB Atlas account (free tier available)

### **Step 1: Database Deployment**

#### **Setup MongoDB Atlas**
1. **Create MongoDB Atlas Account**
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create free account or login

2. **Create Cluster**
   - Create new cluster (M0 Sandbox - Free tier)
   - Select AWS provider, Oregon region
   - Name: `bhiv-hr-cluster`

3. **Configure Database**
   - Create database user with read/write permissions
   - Add IP whitelist (0.0.0.0/0 for development)
   - Get connection string from Connect dialog

4. **Collections Setup**
   - MongoDB Atlas creates collections automatically
   - 17+ collections for HR platform data
   - No manual schema initialization required
   ```

### **Step 2: Service Deployment**

#### **Deploy API Gateway**
1. **Create Web Service**
   - Repository: `https://github.com/Shashank-0208/BHIV-HR-PLATFORM`
   - Root Directory: `services/gateway`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   ```
   DATABASE_URL=postgresql://bhiv_user:password@hostname/bhiv_hr
   API_KEY_SECRET=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   ENVIRONMENT=production
   ```

#### **Deploy AI Agent**
1. **Create Web Service**
   - Root Directory: `services/agent`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   ```
   DATABASE_URL=postgresql://bhiv_user:password@hostname/bhiv_hr
   OPENAI_API_KEY=your-openai-key
   GATEWAY_SERVICE_URL=https://your-gateway-url.onrender.com
   ```

#### **Deploy LangGraph Service**
1. **Create Web Service**
   - Root Directory: `services/langgraph`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   ```
   DATABASE_URL=postgresql://bhiv_user:password@hostname/bhiv_hr
   GATEWAY_SERVICE_URL=https://your-gateway-url.onrender.com
   OPENAI_API_KEY=your-openai-key
   ```

#### **Deploy Portal Services**

**HR Portal:**
```
Root Directory: services/portal
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

**Client Portal:**
```
Root Directory: services/client_portal
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

**Candidate Portal:**
```
Root Directory: services/candidate_portal
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

### **Step 3: Service Integration**

#### **Update Service URLs**
After all services are deployed, update environment variables:

```bash
# Gateway Service
AGENT_SERVICE_URL=https://your-agent-url.onrender.com
LANGGRAPH_URL=https://your-langgraph-url.onrender.com

# Portal Services
GATEWAY_SERVICE_URL=https://your-gateway-url.onrender.com
API_BASE_URL=https://your-gateway-url.onrender.com
```

---

## 🔧 Advanced Configuration

### **Environment Variables Reference**

#### **Database Configuration**
```bash
DATABASE_URL=postgresql://user:password@host:port/database
POSTGRES_DB=bhiv_hr
POSTGRES_USER=bhiv_user
POSTGRES_PASSWORD=secure_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

#### **Security Configuration**
```bash
API_KEY_SECRET=your-256-bit-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
BCRYPT_ROUNDS=12
```

#### **AI Configuration**
```bash
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
SEMANTIC_MODEL=sentence-transformers/all-MiniLM-L6-v2
BATCH_SIZE=50
CACHE_TTL=3600
```

#### **LangGraph Configuration**
```bash
LANGGRAPH_API_KEY=your-langgraph-key
WORKFLOW_TIMEOUT=300
MAX_RETRIES=3
NOTIFICATION_CHANNELS=email,whatsapp,telegram
```

#### **Performance Configuration**
```bash
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=30
RATE_LIMIT=500
CACHE_SIZE=1000
```

### **Docker Configuration**

#### **Production Docker Compose (MongoDB Atlas)**
```yaml
version: '3.8'
services:
  gateway:
    build: ./services/gateway
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr
      - AGENT_SERVICE_URL=http://agent:9000
      - LANGGRAPH_URL=http://langgraph:9001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  agent:
    build: ./services/agent
    ports:
      - "9000:9000"
    environment:
      - MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr
      - GATEWAY_SERVICE_URL=http://gateway:8000

  langgraph:
    build: ./services/langgraph
    ports:
      - "9001:9001"
    environment:
      - MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr
      - GATEWAY_SERVICE_URL=http://gateway:8000
```

---

## ✅ Verification & Testing

### **Automated Verification Script**
```bash
#!/bin/bash
# verify_deployment.sh

echo "🔍 BHIV HR Platform Deployment Verification"
echo "=========================================="

# Check service health
services=(
    "http://localhost:8000/health"
    "http://localhost:9000/health"
    "http://localhost:9001/health"
)

for service in "${services[@]}"; do
    echo "Checking $service..."
    if curl -f -s "$service" > /dev/null; then
        echo "✅ Service healthy"
    else
        echo "❌ Service unhealthy"
    fi
done

# Test API endpoints
echo "🧪 Testing API Endpoints..."
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:8000/v1/jobs" | jq '.total'

# Test AI matching
echo "🤖 Testing AI Matching..."
curl -X POST -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:9000/match" \
     -d '{"candidate_id": 1, "job_id": 1}' | jq '.score'

# Test LangGraph workflow
echo "🔄 Testing LangGraph Workflow..."
curl -X POST -H "Content-Type: application/json" \
     "http://localhost:9001/workflows/test" \
     -d '{"test": true}' | jq '.status'

echo "✅ Verification Complete"
```

### **Manual Testing Checklist**

#### **API Gateway (77 endpoints)**
```bash
# Health check
curl http://localhost:8000/health

# API Documentation
curl http://localhost:8000/docs

# Test candidates endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/candidates

# Test jobs endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/jobs
```

#### **AI Agent (6 endpoints)**
```bash
# Health check
curl http://localhost:9000/health

# API Documentation
curl http://localhost:9000/docs

# Test matching endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:9000/match
```

#### **LangGraph (25 endpoints)**
```bash
# Health check
curl http://localhost:9001/health

# API Documentation
curl http://localhost:9001/docs

# Test workflow endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:9001/workflows/test
```

#### **Database Connectivity**
```bash
# Test MongoDB connection through Gateway
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/test-candidates

# Expected response: {"status": "success", "message": "Database connected"}
```

### **Performance Testing**
```bash
# Load testing with Apache Bench
ab -n 100 -c 10 https://bhiv-hr-gateway-ltg0.onrender.com/health

# Expected results:
# - Requests per second: >50
# - Time per request: <100ms
# - Failed requests: 0
```

---

## 🔒 Security Configuration

### **SSL/TLS Setup**
```bash
# Render automatically provides SSL certificates
# Verify SSL configuration
curl -I https://bhiv-hr-gateway-ltg0.onrender.com/
# Expected: HTTP/2 200 with security headers
```

### **API Key Management**
```bash
# Generate secure API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment variables
API_KEY_SECRET=your-generated-key
```

### **Database Security**
```sql
-- Create read-only user for monitoring
CREATE USER bhiv_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE bhiv_hr TO bhiv_readonly;
GRANT USAGE ON SCHEMA public TO bhiv_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bhiv_readonly;
```

---

## 📊 Monitoring & Maintenance

### **Health Monitoring**
```bash
# Service health check script
#!/bin/bash
services=(
    "gateway:https://bhiv-hr-gateway-ltg0.onrender.com/health"
    "agent:https://bhiv-hr-agent-nhgg.onrender.com/health"
    "langgraph:https://bhiv-hr-langgraph.onrender.com/health"
)

for service in "${services[@]}"; do
    name=${service%%:*}
    url=${service#*:}
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name: Healthy"
    else
        echo "❌ $name: Unhealthy"
        # Send alert notification
    fi
done
```

### **Performance Monitoring**
```bash
# Database performance
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# API performance
curl -w "@curl-format.txt" -o /dev/null -s https://bhiv-hr-gateway-ltg0.onrender.com/v1/jobs
```

### **Log Management**
```bash
# View service logs (Render dashboard)
# Or use CLI tools for local deployment
docker-compose -f docker-compose.production.yml logs -f gateway
docker-compose -f docker-compose.production.yml logs -f agent
```

---

## 🚨 Troubleshooting

### **Common Issues & Solutions**

#### **Database Connection Issues**
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT version();"

# Common fixes:
# 1. Verify DATABASE_URL format
# 2. Check firewall settings
# 3. Ensure database is running
# 4. Verify credentials
```

#### **Service Startup Issues**
```bash
# Check service logs
docker-compose logs service_name

# Common fixes:
# 1. Verify environment variables
# 2. Check port conflicts
# 3. Ensure dependencies are running
# 4. Verify Docker image builds
```

#### **API Authentication Issues**
```bash
# Test API key
curl -H "Authorization: Bearer your_api_key" \
     https://bhiv-hr-gateway-ltg0.onrender.com/v1/auth/verify

# Common fixes:
# 1. Verify API key format
# 2. Check JWT secret configuration
# 3. Ensure proper headers
# 4. Verify token expiration
```

#### **Performance Issues**
```bash
# Check resource usage
docker stats

# Common fixes:
# 1. Increase memory allocation
# 2. Optimize database queries
# 3. Enable caching
# 4. Scale services horizontally
```

### **Emergency Recovery**
```bash
# Quick service restart
docker-compose -f docker-compose.production.yml restart

# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Service rollback (Render)
# Use Render dashboard to rollback to previous deployment
```

---

## 📈 Scaling & Optimization

### **Horizontal Scaling**
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  gateway:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
  
  agent:
    deploy:
      replicas: 2
    ports:
      - "8010-8011:8001"
```

### **Performance Optimization**
```bash
# Database optimization
psql $DATABASE_URL -c "
-- Update statistics
ANALYZE;

-- Rebuild indexes
REINDEX DATABASE bhiv_hr;

-- Vacuum for space reclamation
VACUUM ANALYZE;
"

# Application optimization
# 1. Enable Redis caching
# 2. Implement connection pooling
# 3. Use CDN for static assets
# 4. Enable gzip compression
```

### **Cost Optimization**
```bash
# Render free tier limits:
# - 750 hours/month per service
# - 0.1 CPU, 512MB RAM
# - 100GB bandwidth

# Optimization strategies:
# 1. Use sleep schedules for non-critical services
# 2. Implement efficient caching
# 3. Optimize database queries
# 4. Use compression for API responses
```

---

## 🎯 Success Criteria

### **Deployment Success Checklist**
- ✅ **All 6 services operational** (Gateway, Agent, LangGraph, 3 Portals)
- ✅ **All 111 endpoints functional** (80+6+25)
- ✅ **Database schema v4.3.0** with 19 tables (13 core + 6 RL)
- ✅ **Authentication working** (API keys, JWT, 2FA)
- ✅ **AI matching operational** (<0.02s response time)
- ✅ **LangGraph workflows** creating and processing
- ✅ **RL system active** (Q-learning, feedback integration)
- ✅ **Notifications working** (Email, WhatsApp, Telegram)
- ✅ **Performance targets met** (<100ms API, 99.9% uptime)
- ✅ **Security measures active** (Rate limiting, audit logging)

### **Performance Benchmarks**
- **API Response Time**: <100ms (95th percentile)
- **AI Matching Speed**: <0.02s with caching
- **Database Query Time**: <50ms average
- **Service Uptime**: >99.9%
- **Concurrent Users**: 100+ supported
- **Throughput**: 500+ requests/minute

### **Production Readiness**
- **Monitoring**: Health checks, performance metrics
- **Backup**: Automated daily database backups
- **Security**: SSL/TLS, authentication, rate limiting
- **Scalability**: Horizontal scaling ready
- **Documentation**: Complete API and deployment docs
- **Testing**: 100% endpoint coverage

---

## 📞 Support & Resources

### **Quick Links**
- **Live API**: [bhiv-hr-gateway-ltg0.onrender.com/docs](https://bhiv-hr-gateway-ltg0.onrender.com/docs)
- **HR Portal**: [bhiv-hr-portal-u670.onrender.com](https://bhiv-hr-portal-u670.onrender.com/)
- **Client Portal**: [bhiv-hr-client-portal-3iod.onrender.com](https://bhiv-hr-client-portal-3iod.onrender.com/)
- **GitHub**: [BHIV-HR-Platform Repository](https://github.com/Shashank-0208/BHIV-HR-PLATFORM)

### **Documentation**
- [Quick Start Guide](QUICK_START_GUIDE.md)
- [API Documentation](../api/API_DOCUMENTATION.md)
- [Database Documentation](../database/DATABASE_DOCUMENTATION.md)
- [Security Audit](../security/SECURITY_AUDIT.md)

### **Demo Credentials**
- **API Key**: Available in Render dashboard
- **HR Portal**: `demo_user` / `demo_password`
- **Client Portal**: `TECH001` / `demo123`
- **Database**: Read-only access for testing

---

**BHIV HR Platform Deployment Guide v4.3.0** - Complete deployment instructions for enterprise AI-powered recruiting platform with 6 microservices, 111 endpoints, and production-grade security.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Last Updated**: December 9, 2025 | **Version**: v4.3.0 | **Services**: 6/6 Live | **Status**: ✅ Production Ready
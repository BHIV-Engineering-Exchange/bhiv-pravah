# Sovereign Deployment Readiness Guide

**Document Status**: PRODUCTION-READY | SOVEREIGN-CAPABLE | FACTUAL
**Updated**: January 29, 2026
**Current System**: MongoDB Atlas migration complete, 111 endpoints operational

## Required Environment Variables

### Core Configuration
- `DATABASE_URL` or `MONGODB_URI` - MongoDB Atlas connection string
- `MONGODB_DB_NAME` - Database name (default: bhiv_hr)
- `JWT_SECRET_KEY` - Client JWT token signing secret
- `CANDIDATE_JWT_SECRET_KEY` - Candidate JWT token signing secret
- `API_KEY_SECRET` - System-level API key authentication
- `TENANT_ISOLATION_ENABLED` - Enable/disable tenant isolation (true/false)

### Optional AI/RL Services
- `GEMINI_API_KEY` - Google Gemini API for AI matching
- `TWILIO_ACCOUNT_SID` - Twilio integration for SMS/WhatsApp
- `TWILIO_AUTH_TOKEN` - Twilio authentication
- `GMAIL_USER` / `GMAIL_PASSWORD` - Email service configuration
- `TELEGRAM_BOT_TOKEN` - Telegram bot integration

### Regional Compliance
- `REGION` - Deployment region (KSA/UAE/IN/Global)
- `DATA_RESIDENCY_REQUIRED` - Enforce data residency rules (true/false)
- `ENCRYPTION_AT_REST` - Enable encryption at rest (true/false)

## Current Deployment Status

### ✅ Production Ready Components
- **Database**: MongoDB Atlas with auto-scaling and backup
- **Authentication**: Triple authentication system (API Key + Client JWT + Candidate JWT)
- **Microservices**: 6 services operational (Gateway, Agent, LangGraph, 3 Portals)
- **Endpoints**: 111 total endpoints (80 Gateway + 6 Agent + 25 LangGraph)
- **Security**: Rate limiting, input validation, audit logging implemented

### ⚠️ Configuration Notes
- **Single-Tenant Mode**: Currently operating as single-tenant system
- **Multi-Tenant Ready**: Framework exists but requires tenant_id filtering in queries
- **Sovereign Deployment**: Can be deployed in KSA/UAE with proper regional configuration

## Deployment Steps

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd backend/runtime-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Set MongoDB Atlas connection
# Configure authentication secrets
# Enable tenant isolation if needed
```

### 3. Database Setup
```bash
# MongoDB Atlas auto-creates collections
# No manual schema creation required
# Collections created on first write operation
```

### 4. Service Startup
```bash
# Start main application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use Docker
docker-compose up --build
```

### 5. Health Verification
```bash
# Check service health
curl http://localhost:8000/health

# Verify authentication
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/v1/candidates/stats
```

## Regional Deployment Guidelines

### KSA (Kingdom of Saudi Arabia)
- **Data Residency**: All data must remain within KSA borders
- **Encryption**: AES-256 encryption at rest required
- **Compliance**: GCC data protection regulations
- **Configuration**: Set `REGION=KSA` and `DATA_RESIDENCY_REQUIRED=true`

### UAE (United Arab Emirates)
- **Data Residency**: Data must remain within UAE
- **Encryption**: Government-approved encryption standards
- **Compliance**: UAE data protection laws
- **Configuration**: Set `REGION=UAE` and `DATA_RESIDENCY_REQUIRED=true`

### India
- **Data Residency**: DPDPA compliance requirements
- **Encryption**: Standard encryption protocols
- **Compliance**: Digital Personal Data Protection Act
- **Configuration**: Set `REGION=IN`

## Sovereign Cloud Deployment

### Infrastructure Requirements
- **Compute**: Minimum 2 vCPUs, 4GB RAM
- **Storage**: 50GB SSD minimum
- **Network**: 100Mbps bandwidth minimum
- **Backup**: Daily automated backups with 30-day retention

### Security Hardening
- **Network**: Firewall rules restricting access
- **Authentication**: Multi-factor authentication for admin access
- **Monitoring**: Real-time security monitoring
- **Compliance**: Regular security audits

## No External Dependencies

### ✅ Self-Contained Components
- Authentication system (built-in)
- Database (MongoDB Atlas)
- API gateway (FastAPI)
- Workflow engine (LangGraph)
- Audit logging (built-in)

### 🔌 Optional Integrations
- AI services (Google Gemini - optional)
- Communication services (Twilio, Gmail - optional)
- External systems (Artha, Karya - optional adapters)

## Migration from Current Setup

### From PostgreSQL (Legacy)
- **Status**: Migration to MongoDB Atlas complete
- **Data**: All data migrated to MongoDB collections
- **Schema**: Document-based schema with flexible collections
- **Performance**: Improved with Atlas auto-scaling

### From Local Development
- **Environment**: Production environment variables required
- **Security**: Proper secret management needed
- **Monitoring**: Production monitoring setup required

---

**Document Owner**: BHIV Platform Team  
**Last Updated**: January 29, 2026  
**Next Review**: February 15, 2026

*This deployment guide reflects the current production-ready state of the BHIV HR Platform with MongoDB Atlas integration and sovereign deployment capabilities.*
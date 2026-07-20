# BHIV HR Platform - Handover Documentation

**Status**: Production Ready - Updated January 22, 2026
**Database**: MongoDB Atlas (Primary) - Successfully migrated from PostgreSQL
**Architecture**: Microservices with 111 endpoints across 6 services
**Deployment**: Docker + Render Cloud + MongoDB Atlas

## 📁 Directory Structure

```
handover/
├── README.md                           # This documentation file
├── START_HERE.md                       # Primary entry point for developers
├── FAQ.md                             # Comprehensive troubleshooting guide
├── RUNBOOK.md                         # Operational procedures and maintenance
├── SYSTEM_BEHAVIOR.md                 # System architecture and behavior specs
├── TENANT_ASSUMPTIONS.md              # Multi-tenant architecture design
├── ROLE_MATRIX.md                     # Team roles and responsibilities
├── DEMO_RUNBOOK.md                    # Demo procedures and safe demonstration
├── QA_CHECKLIST.md                    # Quality assurance testing checklist
├── HOW_TO_TEST.md                     # Testing procedures and validation
├── ISOLATION_CHECKLIST.md             # Tenant isolation validation checklist
├── KNOWN_GAPS.md                      # Documented known gaps and limitations
├── READ_THIS_FIRST.md                 # Initial handover instructions
├── generate_totp.py                   # TOTP generation utility
├── test_all_endpoints.py              # Comprehensive API endpoint testing
├── api_contract/                      # API contract documentation
│   ├── AGENT_SERVICE.md               # Agent service API contracts
│   ├── CANDIDATE_PORTAL.md            # Candidate portal API contracts
│   ├── CLIENT_PORTAL.md               # Client portal API contracts
│   ├── GATEWAY_SERVICE.md             # Gateway service API contracts
│   ├── LANGGRAPH_SERVICE.md           # LangGraph service API contracts
│   └── PORTAL_SERVICE.md              # Portal service API contracts
├── architecture/                      # Architecture documentation
│   └── MICROSERVICE_ARCHITECTURE.md   # Microservice architecture overview
├── integration_maps/                  # Integration mapping documentation
│   └── SERVICE_INTEGRATION_MAP.md     # Service integration mappings
├── issues/                            # Issue tracking and resolution
│   └── ISSUE_RESOLUTION_GUIDE.md      # Issue resolution procedures
├── postman/                           # Postman collection and testing
│   ├── postman_collection.json        # Main Postman collection
│   ├── complete-enhanced-tests.js     # Enhanced test scripts
│   ├── POSTMAN_README.md              # Postman usage documentation
│   └── test_results.json              # Test execution results
└── video/                             # Video documentation
    └── SYSTEM_OVERVIEW_VIDEO.md       # System overview video documentation
```

## 🎯 Purpose and Scope

This directory contains comprehensive handover documentation for the BHIV HR Platform, designed to facilitate smooth transitions for new team members and provide operational guidance for existing team members. The documentation covers:

- System architecture and design decisions
- Operational procedures and maintenance guidelines
- Troubleshooting guides and known issues
- API contracts and integration specifications
- Testing procedures and validation checklists
- Role assignments and responsibilities

## 🔧 Current System Status

### 🏗️ **System Architecture Overview**

**Microservice Architecture Active**:
* ✅ **API Gateway** (Port 8000) - 80 endpoints (core APIs, job management, candidate workflows)
* ✅ **AI Agent** (Port 9000) - 6 endpoints (semantic matching, AI analysis)
* ✅ **LangGraph** (Port 9001) - 25 endpoints (workflows, RL integration, notifications)
* ✅ **MongoDB Atlas** - Primary database (17+ collections, fully migrated)
* ✅ **Portals** - Client Portal (8502), Candidate Portal (8503), HR Portal (8501)

### 📊 **System Status Dashboard**

| Component | Status | Details |
|-----------|--------|---------|
| **RL Integration** | ✅ COMPLETE | Fully integrated in LangGraph - see `/rl/` endpoints |
| **AI Brain Wiring** | ✅ COMPLETE | Integrated with LangGraph workflows |
| **Database** | ✅ MIGRATED | MongoDB Atlas (17+ collections) |
| **Authentication** | ✅ WORKING | API keys, JWT, 2FA all functional |
| **Runtime-Core** | ⚠️ LEGACY | Reference implementation only (not in production) |
| **API Coverage** | ✅ 111/111 | All endpoints functional and tested |
| **Security** | ✅ ENFORCED | RBAC, rate limiting, input validation |

## 📚 Essential Documentation Files

| File | Purpose | Priority |
|------|---------|----------|
| `START_HERE.md` | Primary entry point for developers | ⭐⭐⭐ |
| `FAQ.md` | Comprehensive troubleshooting guide | ⭐⭐⭐ |
| `RUNBOOK.md` | Operational procedures and maintenance | ⭐⭐⭐ |
| `ROLE_MATRIX.md` | Team roles and responsibilities | ⭐⭐⭐ |
| `SYSTEM_BEHAVIOR.md` | System architecture and behavior | ⭐⭐⭐ |
| `TENANT_ASSUMPTIONS.md` | Multi-tenant architecture | ⭐⭐⭐ |
| `postman/POSTMAN_README.md` | API testing and validation | ⭐⭐⭐ |

## 🧪 Testing and Validation

| File | Purpose | Status |
|------|---------|--------|
| `test_all_endpoints.py` | Comprehensive API testing (111 endpoints) | ✅ Active |
| `postman/postman_collection.json` | Postman test collection | ✅ Active |
| `postman/complete-enhanced-tests.js` | Advanced API validation | ✅ Active |
| `../test_mongodb_atlas.py` | Database connectivity test | ✅ Active |

## 🚀 Getting Started

1. **Start Here**: Begin with `START_HERE.md` for the primary developer onboarding guide
2. **Learn Operations**: Read `FAQ.md` for comprehensive troubleshooting procedures
3. **Understand Roles**: Review `ROLE_MATRIX.md` for team responsibilities
4. **Study Architecture**: Examine `SYSTEM_BEHAVIOR.md` and `TENANT_ASSUMPTIONS.md`
5. **Validate System**: Run `test_all_endpoints.py` to confirm system functionality
6. **Explore APIs**: Use Swagger UI at `http://localhost:8000/docs` for API exploration

## 🆘 Support and Contacts

For critical issues, refer to `FAQ.md` and `RUNBOOK.md` for escalation procedures and contact information. For general questions about this documentation, consult the team lead or designated system owner.
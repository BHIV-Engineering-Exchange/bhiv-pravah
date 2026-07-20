# TENANT_ASSUMPTIONS.md
**BHIV HR Platform - Tenant Architecture & Assumptions**  
**Version**: 4.3.1  
**Updated**: January 22, 2026  
**Database**: MongoDB Atlas (migrated from PostgreSQL)  
**Architecture**: Microservices with 111 endpoints  
**Status**: Multi-Tenant Ready - Zero Dependency Handover  

---

## 🏢 **TENANT ARCHITECTURE OVERVIEW**

**BHIV HR Platform** operates as a **multi-tenant SaaS platform** where each client company represents a separate tenant with isolated data and controlled access.

### **Tenant Model**
- **Tenant Type**: Client-based tenancy
- **Isolation Level**: Data isolation with shared application layer
- **Tenant Identifier**: `client_id` (string, unique per tenant)
- **Tenant Storage**: Single database with tenant-aware queries

---

## 🔐 **TENANT ISOLATION ASSUMPTIONS**

### **1. CLIENT TENANT STRUCTURE**

#### **Tenant Definition**
```javascript
// Each client is a separate tenant in MongoDB Atlas
db.clients.insertOne({
    _id: ObjectId(),           // MongoDB generated ID
    client_id: "STRING",       // Tenant identifier
    company_name: "STRING",    // Tenant display name
    password_hash: "STRING",   // Bcrypt hashed password
    email: "STRING",           // Contact email
    status: "active",          // Tenant status
    created_at: ISODate()      // Creation timestamp
});
```

#### **Current Tenant Data**
```
TECH001     - Tech Innovations Inc (Active)
STARTUP01   - Startup Ventures LLC (Active)  
ENTERPRISE01 - Enterprise Solutions Corp (Active)
```

### **2. DATA ISOLATION ASSUMPTIONS**

#### **Tenant-Aware Tables**
```javascript
// Jobs are tenant-scoped
jobs.client_id → clients.client_id

// Candidates are shared across tenants (job seekers)
candidates.* → Global pool, accessible by all tenants

// Applications link candidates to tenant jobs
applications.job_id → jobs._id (tenant-scoped)
applications.candidate_id → candidates._id (global)

// Feedback is tenant-scoped through job relationship
feedback.job_id → jobs._id (tenant-scoped)

// Interviews are tenant-scoped through job relationship
interviews.job_id → jobs._id (tenant-scoped)

// Offers are tenant-scoped through job relationship
offers.job_id → jobs._id (tenant-scoped)
```

#### **Shared vs Tenant-Scoped Data**

**TENANT-SCOPED (Isolated per client)**
- Jobs (`jobs.client_id`)
- Job Applications (via job relationship)
- Interviews (via job relationship)
- Offers (via job relationship)
- Feedback (via job relationship)
- Workflows (via `workflows.client_id`)

**SHARED ACROSS TENANTS**
- Candidates (global talent pool)
- Users (internal HR staff)
- System configuration
- Audit logs (with tenant context)
- Matching cache (with tenant context)

### **3. TENANT ACCESS CONTROL**

#### **Authentication Assumptions**

**Client JWT Token Structure**
```json
{
    "client_id": "TECH001",
    "company_name": "Tech Innovations Inc",
    "exp": 1640995200,
    "permissions": ["view_jobs", "create_jobs", "view_candidates", "schedule_interviews"]
}
```

**Access Control Rules**
```
1. Clients can ONLY access their own jobs
2. Clients can view ALL candidates (shared pool)
3. Clients can ONLY see applications to their jobs
4. Clients can ONLY schedule interviews for their jobs
5. Clients can ONLY make offers for their jobs
```

#### **Query Filtering Assumptions**

**Automatic Tenant Filtering**
```javascript
// Jobs query (tenant-scoped)
db.jobs.find({ client_id: "CLIENT_ID", status: "active" })

// Applications query (tenant-scoped via job)
db.applications.aggregate([
  { $lookup: { from: "jobs", localField: "job_id", foreignField: "_id", as: "job" } },
  { $lookup: { from: "candidates", localField: "candidate_id", foreignField: "_id", as: "candidate" } },
  { $match: { "job.client_id": "CLIENT_ID" } },
  { $project: { "candidate.name": 1, "job": 1, "status": 1, "applied_at": 1 } }
])

// Candidates query (shared - no filtering)
db.candidates.find({ status: "active" })
```

---

## 🚫 **TENANT ISOLATION BOUNDARIES**

### **WHAT EXISTS (Implemented)**

#### **1. Client Authentication**
- ✅ Client-specific JWT tokens with `client_id`
- ✅ Client registration and login endpoints
- ✅ Password hashing and security for client accounts
- ✅ Client status management (active/inactive/suspended)

#### **2. Data Scoping**
- ✅ Jobs are scoped to `client_id`
- ✅ Job applications link to tenant jobs
- ✅ Interviews and offers are tenant-scoped via jobs
- ✅ Workflows include `client_id` for tenant context

#### **3. Access Control**
- ✅ Dual authentication (API key OR client JWT)
- ✅ Client portal with tenant-specific views
- ✅ Job creation restricted to authenticated clients
- ✅ Application viewing restricted to job owners

### **WHAT DOES NOT EXIST (Limitations)**

#### **1. Automatic Tenant Filtering**
- ❌ **No middleware** for automatic tenant context injection
- ❌ **No query interceptors** to auto-add client_id filters
- ❌ **Manual filtering** required in each endpoint
- ❌ **No tenant validation** on cross-tenant data access

#### **2. Tenant Administration**
- ❌ **No tenant provisioning** workflow
- ❌ **No tenant configuration** management
- ❌ **No tenant usage metrics** or billing
- ❌ **No tenant backup/restore** capabilities

#### **3. Advanced Isolation**
- ❌ **No database-level** row-level security (RLS)
- ❌ **No schema-per-tenant** isolation
- ❌ **No tenant-specific** rate limiting
- ❌ **No tenant resource** quotas or limits

#### **4. Tenant Security**
- ❌ **No tenant-specific** encryption keys
- ❌ **No tenant audit** trail separation
- ❌ **No tenant-specific** CSP policies
- ❌ **No cross-tenant** access prevention validation

---

## ⚠️ **CRITICAL TENANT ASSUMPTIONS**

### **1. SHARED CANDIDATE POOL ASSUMPTION**

**Assumption**: All candidates are shared across all tenants
```
RATIONALE: Job seekers should be discoverable by all companies
IMPLICATION: Candidates can apply to multiple tenant jobs
RISK: No candidate data isolation between tenants
```

**Implementation Reality**
```sql
-- Candidates table has NO client_id column
-- All tenants can see all candidates
-- Candidate applications create tenant relationships
```

### **2. MANUAL TENANT FILTERING ASSUMPTION**

**Assumption**: Developers manually add tenant filtering to queries
```
CURRENT STATE: Each endpoint manually checks client_id
RISK: Forgotten filters could leak tenant data
EXAMPLE: Missing WHERE client_id = :client_id in job queries
```

**Critical Code Patterns**
```python
# CORRECT - Tenant-aware job query
job_doc = await db.jobs.find_one({"client_id": client_id, "status": "active"})

# INCORRECT - Could leak cross-tenant data
db.jobs.find_one({"status": "active"})  # Missing client_id filter
```

### **3. CLIENT JWT TRUST ASSUMPTION**

**Assumption**: Client JWT tokens are trusted for tenant identification
```
TRUST MODEL: JWT client_id claim determines tenant context
VALIDATION: JWT signature verification only
RISK: Compromised JWT could access wrong tenant data
```

**Token Validation Flow**
```python
# Current implementation trusts JWT client_id
payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
client_id = payload.get("client_id")  # Used for tenant context

# Triple authentication system
# - API Key authentication (system level)
# - Client JWT (client authentication)
# - Candidate JWT (candidate authentication)
```

### **4. NO CROSS-TENANT VALIDATION ASSUMPTION**

**Assumption**: Application logic prevents cross-tenant access
```
CURRENT STATE: No systematic validation of tenant boundaries
EXAMPLE: No check if job_id belongs to authenticated client
RISK: Malicious requests could access other tenant data
```

---

## 🔧 **TENANT CONFIGURATION**

### **Environment Variables**
```bash
# Client authentication
JWT_SECRET_KEY=<client_jwt_secret>
CANDIDATE_JWT_SECRET_KEY=<candidate_jwt_secret>

# No tenant-specific configuration exists
# All tenants share same environment settings
```

### **Database Configuration**
```yaml
# MongoDB Atlas configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=bhiv_hr
# Tenant context included in all documents
# Shared connection pool with automatic scaling
# Per-tenant read/write optimization via Atlas
# Collection-level security policies
# Triple authentication system: API Key + Client JWT + Candidate JWT
# 111 operational endpoints across 6 services
# Production-ready single-tenant system with multi-tenant framework ready
```

### **MongoDB Atlas Integration**
- **Shared Cluster**: All tenants use same Atlas cluster
- **Tenant Context**: `client_id` field in relevant documents
- **Query Optimization**: Tenant-aware indexing and aggregation
- **Performance**: Atlas handles connection pooling and optimization

### **Service Configuration**
```yaml
# All services are tenant-agnostic
# No tenant-specific service instances
# Shared infrastructure for all tenants
```

---

## 📊 **TENANT DATA PATTERNS**

### **Current Tenant Usage**
```javascript
// Tenant job distribution in MongoDB
db.jobs.aggregate([
  { $group: { _id: "$client_id", job_count: { $sum: 1 } } }
])

// Expected results:
// TECH001: 2-3 jobs
// STARTUP01: 1-2 jobs  
// ENTERPRISE01: 1-2 jobs

// MongoDB Atlas metrics via dashboard
// Real-time monitoring of tenant resource usage
```

### **Tenant Relationship Mapping**
```
TECH001 (Tech Innovations Inc)
├── Jobs: Senior Python Developer, Data Scientist, Product Manager
├── Applications: Via job_applications table
├── Interviews: Via interviews table (job relationship)
└── Offers: Via offers table (job relationship)

STARTUP01 (Startup Ventures)
├── Jobs: Frontend Developer
├── Applications: Via job_applications table
└── Related data via job relationships

ENTERPRISE01 (Enterprise Solutions)
├── Jobs: DevOps Engineer
├── Applications: Via job_applications table
└── Related data via job relationships
```

---

## 🚨 **TENANT SECURITY RISKS**

### **HIGH RISK - Data Leakage**
```
RISK: Missing client_id filters in queries
IMPACT: Cross-tenant data exposure
MITIGATION: Code review for all tenant-scoped queries
```

### **MEDIUM RISK - JWT Compromise**
```
RISK: Stolen JWT tokens accessing wrong tenant
IMPACT: Unauthorized tenant access
MITIGATION: Short token expiry (24 hours)
```

### **LOW RISK - Shared Infrastructure**
```
RISK: Resource contention between tenants
IMPACT: Performance degradation
MITIGATION: Rate limiting and monitoring
```

---

## 🔍 **TENANT VALIDATION CHECKLIST**

### **Before Any Tenant-Scoped Operation**
```python
# 1. Verify client authentication
auth = get_auth()  # Returns client_id from JWT

# 2. Validate tenant exists and is active
client_query = text("SELECT status FROM clients WHERE client_id = :client_id")
client_status = connection.execute(client_query, {"client_id": auth["client_id"]})

# 3. Add tenant filter to all queries
job_query = text("SELECT * FROM jobs WHERE client_id = :client_id")
jobs = connection.execute(job_query, {"client_id": auth["client_id"]})

# 4. Validate cross-references belong to tenant
if job_id:
    ownership_query = text("SELECT client_id FROM jobs WHERE id = :job_id")
    job_owner = connection.execute(ownership_query, {"job_id": job_id})
    if job_owner.client_id != auth["client_id"]:
        raise HTTPException(403, "Access denied")
```

---

## 📝 **TENANT ASSUMPTIONS SUMMARY**

### **SAFE ASSUMPTIONS (Rely on these)**
1. **Client JWT contains valid client_id** for tenant identification
2. **Jobs table has client_id** for tenant scoping
3. **Candidates are shared** across all tenants
4. **Related data is tenant-scoped** via job relationships
5. **Manual filtering is required** for tenant isolation

### **UNSAFE ASSUMPTIONS (Do not rely on these)**
1. ❌ Automatic tenant filtering in queries
2. ❌ Cross-tenant access prevention
3. ❌ Tenant-specific configuration
4. ❌ Database-level tenant isolation
5. ❌ Tenant resource limits or quotas

### **UNKNOWN/UNTESTED ASSUMPTIONS**
1. ❓ Behavior with invalid client_id in JWT
2. ❓ Performance with large tenant datasets
3. ❓ Tenant data migration procedures
4. ❓ Tenant deletion and cleanup
5. ❓ Multi-tenant backup and restore

---

## 🎯 **TENANT HANDOVER REQUIREMENTS**

### **For Ishan Shirode (Backend)**
- **MUST** validate client_id in all tenant-scoped queries
- **MUST** add tenant context to new endpoints
- **MUST** test cross-tenant access prevention

### **For Nikhil (Frontend)**
- **MUST** include client JWT in all API calls
- **MUST** handle tenant-specific UI contexts
- **MUST** validate tenant permissions in UI

### **For Vinayak (Testing)**
- **MUST** test tenant isolation boundaries
- **MUST** verify cross-tenant access prevention
- **MUST** validate tenant data scoping

---

**END OF TENANT_ASSUMPTIONS.md**

*This document defines the complete tenant architecture and assumptions for the BHIV HR Platform. Any tenant-related development must follow these patterns and validate these assumptions.*


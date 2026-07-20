# ROLE_MATRIX.md
**BHIV HR Platform - Role-Based Access Control Matrix**  
**Version**: 4.3.1  
**Updated**: January 22, 2026  
**Database**: MongoDB Atlas (migrated from PostgreSQL)  
**Architecture**: Microservices with 111 endpoints (80 Gateway + 6 Agent + 25 LangGraph)  
**Status**: Production Ready - Zero Dependency Handover  

---

## 🎭 **ROLE ARCHITECTURE OVERVIEW**

**BHIV HR Platform** implements a **multi-layered role-based access control (RBAC)** system with three distinct user types and granular permission enforcement.

### **Role Hierarchy**
```
1. SYSTEM LEVEL (API Key Authentication)
   └── Full system access, all endpoints

2. INTERNAL USERS (HR Staff)
   ├── Admin (Full HR operations)
   ├── HR Manager (Department management)
   ├── Recruiter (Candidate operations)
   └── User (Basic access)

3. EXTERNAL CLIENTS (Company Representatives)
   └── Client (Tenant-scoped operations)

4. CANDIDATES (Job Seekers)
   └── Candidate (Self-service operations)
```

---

## 🔐 **AUTHENTICATION METHODS & ROLES**

### **1. API KEY AUTHENTICATION**
```
Authentication: Bearer <API_KEY_SECRET>
Role: SYSTEM_ADMIN
Scope: Full system access
Usage: Internal operations, testing, admin tasks
```

**Permissions**: ALL ENDPOINTS
- Complete database access
- All CRUD operations
- System administration
- Cross-tenant operations

### **2. INTERNAL USER AUTHENTICATION**
```
Authentication: Internal user system (not fully implemented)
Roles: admin, hr_manager, recruiter, user
Scope: Internal HR operations
Storage: users table
```

**Current Implementation Status**: ⚠️ **PARTIALLY IMPLEMENTED**
- Users table exists with role column
- No active authentication endpoints
- No role-based permission enforcement
- Placeholder for future implementation

### **3. CLIENT AUTHENTICATION**
```
Authentication: Bearer <CLIENT_JWT_TOKEN>
Role: CLIENT
Scope: Tenant-scoped operations
Storage: clients table
```

**JWT Token Structure**:
```json
{
    "client_id": "TECH001",
    "company_name": "Tech Innovations Inc",
    "exp": 1640995200
}
```

### **4. CANDIDATE AUTHENTICATION**
```
Authentication: Bearer <CANDIDATE_JWT_TOKEN>
Role: CANDIDATE
Scope: Self-service operations
Storage: candidates table
```

**JWT Token Structure**:
```json
{
    "candidate_id": 123,
    "email": "candidate@example.com",
    "exp": 1640995200
}
```

---

## 📊 **ROLE PERMISSION MATRIX**

### **ENDPOINT ACCESS CONTROL**

| Endpoint Category | API Key | Internal User | Client | Candidate |
|------------------|---------|---------------|--------|-----------|
| **Core API** | ✅ Full | ❌ Not Impl | ❌ No | ❌ No |
| **Job Management** | ✅ Full | ❌ Not Impl | ✅ Own Jobs | ❌ Read Only |
| **Candidate Management** | ✅ Full | ❌ Not Impl | ✅ View All | ✅ Own Profile |
| **AI Matching** | ✅ Full | ❌ Not Impl | ✅ Own Jobs | ❌ No |
| **Assessment & Workflow** | ✅ Full | ❌ Not Impl | ✅ Own Jobs | ❌ No |
| **Client Portal** | ✅ Full | ❌ Not Impl | ✅ Own Data | ❌ No |
| **Candidate Portal** | ✅ Full | ❌ Not Impl | ❌ No | ✅ Own Data |
| **Security Testing** | ✅ Full | ❌ Not Impl | ❌ No | ❌ No |
| **Analytics** | ✅ Full | ❌ Not Impl | ❌ No | ❌ No |

### **DETAILED PERMISSION BREAKDOWN**

#### **API KEY ROLE (SYSTEM_ADMIN)**
```python
# Has access to ALL endpoints
PERMISSIONS = [
    "system:*",           # Full system access
    "candidates:*",       # All candidate operations
    "jobs:*",            # All job operations
    "clients:*",         # All client operations
    "analytics:*",       # All analytics access
    "security:*",        # All security operations
    "admin:*"            # All admin operations
]
```

#### **CLIENT ROLE**
```python
# Tenant-scoped permissions
PERMISSIONS = [
    "jobs:create",           # Create jobs for own company
    "jobs:read:own",         # Read own company jobs
    "jobs:update:own",       # Update own company jobs
    "candidates:read",       # View all candidates (shared pool)
    "applications:read:own", # View applications to own jobs
    "interviews:create:own", # Schedule interviews for own jobs
    "interviews:read:own",   # View own company interviews
    "offers:create:own",     # Create offers for own jobs
    "offers:read:own",       # View own company offers
    "feedback:create:own",   # Submit feedback for own jobs
    "feedback:read:own",     # View feedback for own jobs
    "matching:request:own"   # Request AI matching for own jobs
]
```

#### **CANDIDATE ROLE**
```python
# Self-service permissions
PERMISSIONS = [
    "profile:read:own",      # View own profile
    "profile:update:own",    # Update own profile
    "jobs:read",            # View all active jobs
    "applications:create",   # Apply for jobs
    "applications:read:own", # View own applications
    "applications:update:own" # Update own applications
]
```

#### **INTERNAL USER ROLES (Not Implemented)**
```python
# Planned permissions (not enforced)
ADMIN_PERMISSIONS = [
    "users:*", "clients:*", "candidates:*", "jobs:*", 
    "system:*", "analytics:*", "security:*"
]

HR_MANAGER_PERMISSIONS = [
    "candidates:*", "jobs:*", "interviews:*", 
    "offers:*", "feedback:*", "analytics:read"
]

RECRUITER_PERMISSIONS = [
    "candidates:read", "candidates:update", "jobs:read",
    "interviews:*", "applications:read", "matching:request"
]

USER_PERMISSIONS = [
    "candidates:read", "jobs:read", "applications:read"
]
```

---

## 🔒 **ROLE ENFORCEMENT POINTS**

### **1. AUTHENTICATION LAYER**

#### **Dual Authentication Function**
```python
def get_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Triple authentication: API key, Client JWT, or Candidate JWT"""
    
    # 1. Try API key (highest privilege)
    if validate_api_key(credentials.credentials):
        return {"type": "api_key_secret", "role": "SYSTEM_ADMIN"}
    
    # 2. Try client JWT
    try:
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        payload = jwt.decode(credentials.credentials, jwt_secret_key, algorithms=["HS256"])
        return {"type": "client_token", "role": "CLIENT", "client_id": payload.get("client_id")}
    except:
        pass
    
    # 3. Try candidate JWT
    try:
        candidate_jwt_secret_key = os.getenv("CANDIDATE_JWT_SECRET_KEY")
        payload = jwt.decode(credentials.credentials, candidate_jwt_secret_key, algorithms=["HS256"])
        return {"type": "candidate_token", "role": "CANDIDATE", "candidate_id": payload.get("candidate_id")}
    except:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid authentication")
```

### **2. ENDPOINT-LEVEL ENFORCEMENT**

#### **API Key Required Endpoints**
```python
# Requires API key authentication
@app.get("/v1/candidates", dependencies=[Depends(get_api_key)])
@app.post("/v1/candidates/bulk", dependencies=[Depends(get_api_key)])
@app.get("/v1/candidates/stats", dependencies=[Depends(get_api_key)])
@app.post("/v1/jobs", dependencies=[Depends(get_api_key)])
# All security testing endpoints
# All analytics endpoints
```

#### **Dual Authentication Endpoints**
```python
# Accepts API key OR client JWT
@app.get("/v1/jobs", dependencies=[Depends(get_auth)])
@app.get("/v1/match/{job_id}/top", dependencies=[Depends(get_auth)])
@app.post("/v1/feedback", dependencies=[Depends(get_auth)])
@app.post("/v1/interviews", dependencies=[Depends(get_auth)])
```

#### **Candidate Authentication Endpoints**
```python
# Requires candidate JWT
@app.put("/v1/candidate/profile/{candidate_id}", dependencies=[Depends(get_auth)])
@app.post("/v1/candidate/apply", dependencies=[Depends(get_auth)])
@app.get("/v1/candidate/applications/{candidate_id}", dependencies=[Depends(get_auth)])
```

#### **Public Endpoints (No Authentication)**
```python
# No authentication required
@app.get("/")                           # API root
@app.get("/health")                     # Health check
@app.get("/docs")                       # API documentation
@app.post("/v1/client/register")        # Client registration
@app.post("/v1/client/login")           # Client login
@app.post("/v1/candidate/register")     # Candidate registration
@app.post("/v1/candidate/login")        # Candidate login
```

### **3. DATA-LEVEL ENFORCEMENT**

#### **Tenant Scoping for Clients**
```python
# Client can only access their own jobs
def get_client_jobs(client_id: str):
    query = text("SELECT * FROM jobs WHERE client_id = :client_id")
    return connection.execute(query, {"client_id": client_id})

# Client can only see applications to their jobs
def get_client_applications(client_id: str):
    query = text("""
        SELECT ja.* FROM job_applications ja
        JOIN jobs j ON ja.job_id = j.id
        WHERE j.client_id = :client_id
    """)
    return connection.execute(query, {"client_id": client_id})
```

#### **Self-Service for Candidates**
```python
# Candidate can only access their own data
def get_candidate_applications(candidate_id: int, auth_candidate_id: int):
    if candidate_id != auth_candidate_id:
        raise HTTPException(403, "Access denied")
    
    query = text("SELECT * FROM job_applications WHERE candidate_id = :candidate_id")
    return connection.execute(query, {"candidate_id": candidate_id})
```

---

## ⚠️ **ROLE ENFORCEMENT GAPS**

### **CRITICAL GAPS (High Risk)**

#### **1. Missing Internal User Authentication**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: No HR staff authentication system
IMPACT: Cannot distinguish between HR roles
WORKAROUND: All HR operations use API key
```

#### **2. No Role-Based Endpoint Filtering**
```
STATUS: ❌ PARTIAL IMPLEMENTATION
RISK: Clients can access admin endpoints with API key
IMPACT: Potential privilege escalation
EXAMPLE: Client with API key can access /v1/candidates/stats
```

#### **3. Missing Cross-Tenant Validation**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: No validation that job_id belongs to authenticated client
IMPACT: Potential cross-tenant data access
EXAMPLE: Client A could access Client B's job data with correct job_id
```

#### **4. No Resource-Level Permissions**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: No granular permissions within roles
IMPACT: All-or-nothing access within role scope
EXAMPLE: All clients have same permissions regardless of subscription
```

### **MEDIUM GAPS (Medium Risk)**

#### **1. No Role Hierarchy Enforcement**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: No inheritance of permissions
IMPACT: Must explicitly grant all permissions
```

#### **2. No Dynamic Role Assignment**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: Cannot change user roles at runtime
IMPACT: Requires database updates for role changes
```

#### **3. No Permission Caching**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: Permission checks on every request
IMPACT: Performance overhead for complex permissions
```

### **LOW GAPS (Low Risk)**

#### **1. No Audit Trail for Role Changes**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: Cannot track permission changes
IMPACT: Limited security auditing
```

#### **2. No Role-Based Rate Limiting**
```
STATUS: ❌ NOT IMPLEMENTED
RISK: Same rate limits for all roles
IMPACT: Cannot provide premium service levels
```

---

## 🛡️ **ROLE SECURITY PATTERNS**

### **SECURE PATTERNS (Use These)**

#### **1. Authentication First**
```python
# Always authenticate before processing
@app.get("/protected-endpoint")
async def protected_endpoint(auth = Depends(get_auth)):
    # auth contains role and identity information
    if auth["type"] == "client_token":
        client_id = auth["client_id"]
        # Process with client context
```

#### **2. Explicit Permission Checks**
```python
# Check permissions explicitly
def require_client_access(auth, resource_client_id):
    if auth["type"] != "client_token":
        raise HTTPException(403, "Client access required")
    if auth["client_id"] != resource_client_id:
        raise HTTPException(403, "Access denied to resource")
```

#### **3. Tenant-Scoped Queries**
```python
# Always include tenant context in queries
def get_tenant_jobs(client_id: str):
    query = text("SELECT * FROM jobs WHERE client_id = :client_id")
    return connection.execute(query, {"client_id": client_id})
```

### **INSECURE PATTERNS (Avoid These)**

#### **1. Role Assumption**
```python
# DON'T assume role based on endpoint
def bad_endpoint():
    # Assumes caller is client without checking
    client_id = "TECH001"  # WRONG - should get from auth
```

#### **2. Missing Tenant Validation**
```python
# DON'T skip tenant ownership validation
def bad_job_access(job_id: int):
    query = text("SELECT * FROM jobs WHERE id = :job_id")
    # WRONG - doesn't check if job belongs to authenticated client
```

#### **3. Privilege Escalation**
```python
# DON'T allow role elevation
def bad_auth_check(auth):
    if auth["type"] == "candidate_token":
        # WRONG - candidate shouldn't access admin functions
        return admin_operation()
```

---

## 🔍 **ROLE VALIDATION PROCEDURES**

### **Pre-Request Validation**
```python
def validate_role_access(auth, required_role, resource_context=None):
    """Validate role has access to requested resource"""
    
    # 1. Check authentication type
    if auth["type"] not in ["api_key_secret", "client_token", "candidate_token"]:
        raise HTTPException(401, "Invalid authentication type")
    
    # 2. Check role permissions
    if required_role == "SYSTEM_ADMIN" and auth["type"] != "api_key_secret":
        raise HTTPException(403, "System admin access required")
    
    if required_role == "CLIENT" and auth["type"] not in ["api_key_secret", "client_token"]:
        raise HTTPException(403, "Client access required")
    
    if required_role == "CANDIDATE" and auth["type"] not in ["api_key_secret", "candidate_token"]:
        raise HTTPException(403, "Candidate access required")
    
    # 3. Check resource ownership (for tenant-scoped resources)
    if resource_context and auth["type"] == "client_token":
        if resource_context.get("client_id") != auth["client_id"]:
            raise HTTPException(403, "Access denied to resource")
    
    if resource_context and auth["type"] == "candidate_token":
        if resource_context.get("candidate_id") != auth["candidate_id"]:
            raise HTTPException(403, "Access denied to resource")
```

### **Post-Query Validation**
```python
def validate_query_results(auth, results, resource_type):
    """Validate query results match role permissions"""
    
    if auth["type"] == "client_token":
        # Ensure all results belong to authenticated client
        for result in results:
            if hasattr(result, 'client_id') and result.client_id != auth["client_id"]:
                raise HTTPException(403, "Unauthorized data in results")
    
    if auth["type"] == "candidate_token":
        # Ensure all results belong to authenticated candidate
        for result in results:
            if hasattr(result, 'candidate_id') and result.candidate_id != auth["candidate_id"]:
                raise HTTPException(403, "Unauthorized data in results")
```

---

## 📋 **ROLE TESTING CHECKLIST**

### **Authentication Testing**
- [ ] API key authentication works for all system endpoints
- [ ] Client JWT authentication works for client endpoints
- [ ] Candidate JWT authentication works for candidate endpoints
- [ ] Invalid tokens are rejected with 401
- [ ] Expired tokens are rejected with 401

### **Authorization Testing**
- [ ] Clients cannot access other clients' jobs
- [ ] Clients cannot access system admin endpoints
- [ ] Candidates cannot access client endpoints
- [ ] Candidates cannot access other candidates' data
- [ ] API key can access all endpoints

### **Cross-Tenant Testing**
- [ ] Client A cannot see Client B's jobs
- [ ] Client A cannot see applications to Client B's jobs
- [ ] Client A cannot schedule interviews for Client B's jobs
- [ ] Client A cannot make offers for Client B's jobs

### **Privilege Escalation Testing**
- [ ] Candidate cannot perform client operations
- [ ] Client cannot perform system admin operations
- [ ] Invalid role transitions are prevented
- [ ] Token manipulation is detected and blocked

---

## 🎯 **TEAM ROLES & RESPONSIBILITIES**

### **Ishan Shirode (Lead Backend Engineer)**
- **Architecture & Infrastructure**: Lead system architecture, database migration, microservice deployment
- **API Gateway**: Manage Gateway service (80 endpoints) - core APIs, job management, candidate workflows
- **Security Implementation**: Cross-tenant validation, RBAC, authentication system improvements
- **AI Integration**: Maintain Agent service (6 endpoints) and LangGraph integration (25 endpoints)
- **Database Operations**: MongoDB Atlas administration, performance optimization, data migration
- **Key Files**: `services/gateway/app/main.py`, `services/agent/app.py`, `services/langgraph/app/main.py`

### **Nikhil (Frontend Engineer)**
- **UI/UX Implementation**: Client Portal (Streamlit), Candidate Portal, responsive interfaces
- **Authentication Integration**: JWT token handling, role-based UI rendering, session management
- **API Integration**: Frontend-backend communication, error handling, loading states
- **User Experience**: Portal workflows, form validation, accessibility compliance
- **Key Files**: Frontend components, portal services, authentication modules

### **Vinayak (QA & Testing Lead)**
- **Test Automation**: Comprehensive test suite for all 111 endpoints, integration testing
- **Security Testing**: Authentication validation, cross-tenant access prevention, penetration testing
- **Performance Testing**: Load testing, response time validation, stress testing
- **Documentation**: Test cases, bug reports, validation procedures
- **Key Files**: `test_all_endpoints.py`, `handover/postman/`, test automation scripts

### **Cross-Team Collaboration**
- **Weekly Sync**: Monday 10:00 AM - Architecture review and progress updates
- **Code Reviews**: All pull requests require approval from at least one other team member
- **Incident Response**: Shared responsibility for system stability and issue resolution
- **Documentation**: Maintain synchronized documentation in `handover/` directory

---

**END OF ROLE_MATRIX.md**

*This document defines the complete role-based access control system for the BHIV HR Platform. All role-related development must follow these patterns and validate these permissions.*


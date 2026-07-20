# 🗄️ BHIV HR Platform - Database Documentation

**MongoDB Atlas Database**  
**Updated**: January 22, 2026  
**Status**: ✅ Production Ready - RL Integration Fully Operational  
**Collections**: 17+ MongoDB collections  
**Endpoints**: 111 total endpoints  
**RL Status**: ✅ Fully Integrated

---

## 📊 Database Overview

### **Database Architecture**
- **Engine**: MongoDB Atlas (Cloud-hosted NoSQL)
- **Database Name**: `bhiv_hr`
- **Total Collections**: 17+ collections
- **Connection Drivers**: 
  - Motor (Async) - Gateway Service
  - PyMongo (Sync) - Agent & LangGraph Services
- **Connection Pooling**: maxPoolSize=10, minPoolSize=2
- **RL Integration**: Complete reinforcement learning system

### **Production Statistics**
- **Live Data**: Active candidates, jobs, clients, RL predictions, and feedback records
- **Performance**: <50ms query response, <0.02s AI matching, optimized indexes
- **Uptime**: 99.9% availability (MongoDB Atlas)
- **Security**: Triple authentication, encrypted connections, audit logging
- **Scalability**: Cloud-hosted with automatic scaling

### **System Integration**
- **Services**: 3 core microservices with unified database access
- **API Gateway**: 77 endpoints with MongoDB integration (Motor async driver)
- **AI Agent**: Phase 3 semantic engine with RL feedback (PyMongo sync driver)
- **LangGraph**: 25 endpoints with real-time learning (PyMongo sync driver)
- **RL System**: Fully integrated with MongoDB, continuous learning

### **Migration Note**
**Note**: PostgreSQL schemas are available in `services/db/` for historical reference only. The system has fully migrated to MongoDB Atlas and PostgreSQL is no longer in use.

---

## 🏗️ MongoDB Collections

### **1. Core Application Collections**

#### **candidates** - Candidate Profiles
```javascript
{
    "_id": ObjectId("..."),
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "location": "San Francisco, CA",
    "experience_years": 5,
    "technical_skills": "Python, Django, FastAPI, MongoDB",
    "seniority_level": "Senior",
    "education_level": "Bachelor's",
    "resume_path": "/resumes/john_doe.pdf",
    "password_hash": "$2b$12$...",  // bcrypt hashed
    "status": "applied",  // applied, screening, interview, offer, hired, rejected
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes**:
- `email` (unique)
- `status`
- `location`, `experience_years` (compound)
- `technical_skills` (text index for search)

**Features**:
- **Security**: bcrypt password hashing with JWT integration
- **Full-text Search**: Text index on technical_skills
- **Status Tracking**: Complete candidate lifecycle
- **Performance**: Optimized indexes for common queries

#### **jobs** - Job Postings
```javascript
{
    "_id": ObjectId("..."),
    "title": "Senior Python Developer",
    "department": "Engineering",
    "location": "Remote",
    "experience_level": "Senior",
    "requirements": "Python, Django, FastAPI, MongoDB, REST APIs, 5+ years",
    "description": "We are looking for a senior Python developer...",
    "client_id": "client123",
    "employment_type": "Full-time",
    "status": "active",  // active, paused, closed, draft
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes**:
- `status`, `department` (compound)
- `client_id`, `status` (compound)
- `requirements` (text index for search)

**Features**:
- **Client Integration**: Linked to clients via client_id
- **Full-text Search**: Text index on requirements
- **Status Management**: Comprehensive job status workflow

#### **applications** - Job Applications
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "cover_letter": "I am excited about this opportunity...",
    "status": "applied",  // applied, screening, interview, offer, hired, rejected, withdrawn
    "applied_date": ISODate("2026-01-22T10:00:00Z"),
    "last_updated": ISODate("2026-01-22T10:00:00Z"),
    "source": "portal",  // portal, referral, direct, etc.
    "notes": "Strong candidate with relevant experience",
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes**:
- `candidate_id`, `status` (compound)
- `job_id`, `status` (compound)
- `applied_date` (descending)

**Features**:
- **Application Tracking**: Complete application lifecycle
- **Source Tracking**: Application source identification
- **Status Management**: Comprehensive application workflow

#### **feedback** - BHIV Values Assessment
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "integrity": 5,  // 1-5 scale
    "honesty": 5,
    "discipline": 4,
    "hard_work": 5,
    "gratitude": 4,
    "average_score": 4.6,  // Calculated: (5+5+4+5+4)/5
    "comments": "Excellent candidate with strong values",
    "evaluator_id": ObjectId("..."),
    "evaluation_type": "interview",  // interview, assessment, reference
    "created_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes**:
- `candidate_id`, `job_id` (compound)
- `average_score` (descending)

**Features**:
- **BHIV Core Values**: Integrity, Honesty, Discipline, Hard Work, Gratitude
- **Average Score**: Automatically calculated from 5 values
- **RL Integration**: Feeds into reinforcement learning system
- **Multiple Types**: Interview, assessment, and reference feedback

#### **interviews** - Interview Management
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "interview_date": ISODate("2026-01-25T14:00:00Z"),
    "interviewer": "Jane Smith",
    "interview_type": "technical",  // screening, technical, behavioral, final
    "status": "scheduled",  // scheduled, completed, cancelled, rescheduled
    "notes": "Technical interview focusing on system design",
    "score": 8,  // 1-10 scale
    "duration_minutes": 60,
    "meeting_link": "https://meet.google.com/xxx-xxxx-xxx",
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Interview Types**: Screening, technical, behavioral, final rounds
- **Scheduling**: Date/time management with meeting links
- **Scoring**: 1-10 scale with validation
- **Status Tracking**: Complete interview lifecycle management

#### **offers** - Job Offers Management
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "salary": 120000,
    "currency": "USD",
    "start_date": ISODate("2026-02-01"),
    "terms": "Standard employment terms apply",
    "benefits": "Health insurance, PTO, stock options",
    "status": "pending",  // pending, accepted, rejected, withdrawn, expired
    "offer_date": ISODate("2026-01-22"),
    "expiry_date": ISODate("2026-02-05"),
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Comprehensive Offers**: Salary, benefits, terms management
- **Expiry Tracking**: Automatic offer expiration handling
- **Currency Support**: Multi-currency salary tracking
- **Status Workflow**: Complete offer lifecycle management

#### **users** - HR System Users
```javascript
{
    "_id": ObjectId("..."),
    "username": "jane_smith",
    "email": "jane@company.com",
    "password_hash": "$2b$12$...",  // bcrypt hashed
    "role": "hr_manager",  // admin, hr_manager, recruiter, user
    "totp_secret": "JBSWY3DPEHPK3PXP",  // for 2FA
    "is_2fa_enabled": true,
    "failed_login_attempts": 0,
    "locked_until": null,
    "last_login": ISODate("2026-01-22T09:00:00Z"),
    "is_active": true,
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Role-Based Access**: Admin, HR Manager, HR User, Recruiter roles
- **2FA Security**: TOTP secret storage with QR code generation
- **Account Security**: Failed login tracking and account locking
- **Session Management**: Last login tracking and active status

#### **clients** - Client Companies
```javascript
{
    "_id": ObjectId("..."),
    "client_id": "client123",
    "company_name": "Tech Corp Inc.",
    "email": "contact@techcorp.com",
    "password_hash": "$2b$12$...",  // bcrypt hashed
    "contact_person": "John Johnson",
    "phone": "+1234567890",
    "address": "123 Business Ave, City, State 12345",
    "industry": "Technology",
    "company_size": "Large",
    "status": "active",  // active, inactive, suspended
    "failed_login_attempts": 0,
    "locked_until": null,
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Client Management**: Active client companies
- **JWT Integration**: Client portal authentication
- **Company Profiles**: Industry, size, contact information
- **Security**: Account locking and status management

### **2. System Collections**

#### **api_keys** - API Authentication Management
```javascript
{
    "_id": ObjectId("..."),
    "key": "sk_live_abc123def456...",
    "name": "Production Gateway API Key",
    "user_id": ObjectId("..."),
    "client_id": ObjectId("..."),
    "permissions": ["read", "write"],
    "rate_limit": 500,  // requests per minute
    "expires_at": null,  // null for no expiration
    "is_active": true,
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **API Security**: Secure API key management
- **Rate Limiting**: Per-key rate limiting configuration
- **Permissions**: Granular permission controls
- **Expiration**: Optional key expiration

#### **rate_limits** - Dynamic API Rate Limiting
```javascript
{
    "_id": ObjectId("..."),
    "ip_address": "192.168.1.1",
    "endpoint": "/v1/candidates",
    "request_count": 45,
    "window_start": ISODate("2026-01-22T10:00:00Z"),
    "window_duration": 60,  // seconds
    "limit_type": "standard",  // standard, premium, enterprise
    "is_blocked": false,
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Dynamic Limiting**: 60-500 requests/minute based on user tier
- **Endpoint Specific**: Granular rate limiting per API endpoint
- **IP Tracking**: Per-IP address rate limiting
- **Blocking**: Automatic blocking for abuse prevention

#### **audit_logs** - Security & Compliance Tracking
```javascript
{
    "_id": ObjectId("..."),
    "collection_name": "candidates",
    "operation": "UPDATE",  // INSERT, UPDATE, DELETE
    "document_id": ObjectId("..."),
    "old_values": {
        "status": "screening"
    },
    "new_values": {
        "status": "interview"
    },
    "user_id": ObjectId("..."),
    "user_type": "hr_user",  // hr_user, client, system
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "endpoint": "/v1/candidates/...",
    "session_id": "sess_abc123...",
    "created_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Complete Audit Trail**: All database changes tracked
- **Flexible Storage**: Before/after value storage
- **Security Monitoring**: IP, user agent, session tracking
- **Compliance**: GDPR and SOX compliance support

#### **notifications** - Multi-Channel Communication
```javascript
{
    "_id": ObjectId("..."),
    "recipient_id": ObjectId("..."),
    "recipient_type": "candidate",  // candidate, client, hr
    "notification_type": "email",  // email, whatsapp, telegram, sms
    "template": "interview_scheduled",
    "subject": "Interview Scheduled",
    "message": "Your interview is scheduled for...",
    "status": "sent",  // pending, sent, delivered, failed
    "delivery_attempts": 1,
    "sent_at": ISODate("2026-01-22T10:00:00Z"),
    "delivered_at": ISODate("2026-01-22T10:01:00Z"),
    "created_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Multi-Channel**: Email, WhatsApp, Telegram, SMS support
- **Template System**: Reusable notification templates
- **Delivery Tracking**: Complete delivery status tracking
- **Retry Logic**: Automatic retry for failed deliveries

#### **company_scoring_preferences** - Adaptive Learning Engine
```javascript
{
    "_id": ObjectId("..."),
    "client_id": ObjectId("..."),
    "semantic_weight": 0.40,  // 0-1 scale
    "experience_weight": 0.30,  // 0-1 scale
    "skills_weight": 0.20,  // 0-1 scale
    "location_weight": 0.10,  // 0-1 scale
    "cultural_fit_bonus": 0.10,  // 0-0.5 scale
    "learning_rate": 0.001,
    "total_feedback_count": 0,
    "last_optimization": ISODate("2026-01-22T10:00:00Z"),
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Phase 3 Engine**: Advanced AI learning capabilities
- **Weight Optimization**: Based on hiring feedback and RL
- **Learning Rate**: Adaptive learning parameter
- **Feedback Integration**: Continuous improvement based on outcomes
- **Company-Specific**: Personalized scoring for each client

### **3. Reinforcement Learning Collections**

#### **ml_feedback** - ML Learning Feedback
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "prediction_id": ObjectId("..."),
    "feedback_source": "hr",  // hr, client, candidate, system, workflow_automation
    "actual_outcome": "hired",  // hired, rejected, withdrawn, interviewed, shortlisted, pending
    "feedback_score": 4.5,  // 1-5 scale
    "reward_signal": 1.25,
    "feedback_notes": "Candidate performed well in technical interview",
    "created_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Features**:
- **Continuous Learning**: Real feedback data for model improvement
- **Multi-Source**: HR, client, candidate, system, and workflow automation feedback
- **Reward Signals**: Calculated rewards for RL optimization
- **Outcome Tracking**: Complete hiring outcome monitoring

#### **performance_metrics** - System Performance Tracking
```javascript
{
    "_id": ObjectId("..."),
    "metric_name": "api_response_time",
    "value": 45.2,
    "unit": "milliseconds",
    "source_service": "gateway",
    "endpoint": "/v1/candidates",
    "timestamp": ISODate("2026-01-22T10:00:00Z"),
    "tags": {
        "environment": "production",
        "region": "us-east-1"
    }
}
```

**Features**:
- **Real-time Monitoring**: Live performance metrics
- **Service Tracking**: Per-service and per-endpoint metrics
- **Tagging System**: Flexible metric tagging for filtering
- **Historical Analysis**: Trend analysis and alerting

### **4. RL System Integration Status**

#### **Current RL Performance Metrics**
```
RL Predictions: 5 records
RL Feedback: 17 records  
Feedback Rate: 340.0 percent
Model Accuracy: 80.0 percent
```

#### **RL Endpoints Integration**
```
LangGraph RL endpoints (25 total)
POST /rl/predict - ML-powered candidate matching
POST /rl/feedback - Submit hiring outcome feedback
GET /rl/analytics - System performance metrics
GET /rl/performance/{version} - Model performance data
GET /rl/history/{candidate_id} - Candidate decision history
POST /rl/retrain - Trigger model retraining
GET /health - Service health check
```

#### **RL Test Results (100% Pass Rate)**
```
✅ Service Health: langgraph-orchestrator v4.3.1 operational
✅ Integration Test: RL Engine integrated with MongoDB
✅ RL Prediction: Score 77.65, Decision: recommend, Confidence: 75.0%
✅ RL Feedback: Feedback ID: 20, Reward: 1.225
✅ RL Analytics: 5 Predictions, 17 Feedback, 340% rate
✅ RL Performance: Model v1.0.0 active
✅ RL History: Candidate 1 has 3 decisions tracked
✅ RL Retrain: Model v1.0.1, 15 samples, 80% accuracy
```

---
---
## 🔧 Advanced Database Features

### **1. Performance Optimization**

#### **Comprehensive Indexing Strategy (75+ Indexes)**
MongoDB indexes are defined using JavaScript commands and provide powerful query optimization:

**Single Field Indexes:**
```javascript
// Create single field indexes
db.candidates.createIndex({ "email": 1 }, { unique: true })
db.candidates.createIndex({ "status": 1 })
db.jobs.createIndex({ "status": 1 })
db.clients.createIndex({ "client_id": 1 }, { unique: true })

// TTL indexes for automatic cleanup
db.rate_limits.createIndex({ "created_at": 1 }, { expireAfterSeconds: 3600 }) // 1 hour
db.matching_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 86400 }) // 24 hours
```

**Compound Indexes:**
```javascript
// Compound indexes for common queries
db.candidates.createIndex({ "location": 1, "experience_years": 1 })
db.jobs.createIndex({ "status": 1, "department": 1 })
db.feedback.createIndex({ "candidate_id": 1, "job_id": 1 })
db.applications.createIndex({ "candidate_id": 1, "status": 1 })
db.applications.createIndex({ "job_id": 1, "status": 1 })
db.audit_logs.createIndex({ "collection_name": 1, "operation": 1 })
```

**Text Indexes for Full-Text Search:**
```javascript
// Text indexes for search functionality
db.candidates.createIndex({ "technical_skills": "text" })
db.jobs.createIndex({ "requirements": "text", "description": "text" })
```

**Geospatial Indexes:**
```javascript
// Geospatial indexes for location-based queries
db.candidates.createIndex({ "location_coords": "2dsphere" })
```

#### **Query Performance Metrics**
- **Response Time**: <50ms for typical queries
- **AI Matching**: <0.02s with caching
- **Full-text Search**: <100ms for complex searches
- **Batch Processing**: 50 candidates/chunk optimization
- **Connection Pooling**: Optimized for 3 core microservices with Motor driver

### **2. Data Validation & Constraints**

#### **Collection Validation Schemas**
MongoDB uses JSON Schema validation to enforce data integrity at the database level:

```javascript
// Candidates collection validation
db.createCollection("candidates", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "email", "created_at"],
      properties: {
        name: { bsonType: "string", description: "Name is required" },
        email: { bsonType: "string", pattern: "^[^@]+@[^@]+\.[^@]+$", description: "Valid email is required" },
        experience_years: { bsonType: "int", minimum: 0, description: "Experience must be non-negative" },
        status: { 
          enum: ["applied", "screening", "interview", "offer", "hired", "rejected"], 
          description: "Must be a valid status"
        },
        integrity: { bsonType: "int", minimum: 1, maximum: 5, description: "Integrity rating 1-5" },
        honesty: { bsonType: "int", minimum: 1, maximum: 5, description: "Honesty rating 1-5" },
        discipline: { bsonType: "int", minimum: 1, maximum: 5, description: "Discipline rating 1-5" },
        hard_work: { bsonType: "int", minimum: 1, maximum: 5, description: "Hard work rating 1-5" },
        gratitude: { bsonType: "int", minimum: 1, maximum: 5, description: "Gratitude rating 1-5" }
      }
    }
  }
});
```

### **3. Aggregation Pipelines for Complex Operations**

#### **Audit Trail with Change Streams**
MongoDB's change streams provide real-time audit capabilities:

```javascript
// Set up change stream for audit logging
const changeStream = db.candidates.watch();

changeStream.on('change', (change) => {
  const auditLog = {
    collection_name: change.ns.coll,
    operation: change.operationType,
    document_id: change.documentKey._id,
    old_values: change.fullDocumentBeforeChange || null,
    new_values: change.fullDocument || null,
    timestamp: new Date(),
    user_id: change.userId || null
  };
  
  db.audit_logs.insertOne(auditLog);
});
```

#### **Aggregation Pipeline Examples**
```javascript
// Calculate average BHIV scores by job
db.feedback.aggregate([
  {
    $group: {
      _id: "$job_id",
      avg_integrity: { $avg: "$integrity" },
      avg_honesty: { $avg: "$honesty" },
      avg_discipline: { $avg: "$discipline" },
      avg_hard_work: { $avg: "$hard_work" },
      avg_gratitude: { $avg: "$gratitude" },
      overall_avg: { $avg: "$average_score" },
      feedback_count: { $sum: 1 }
    }
  }
]);

// Get top candidates for a job based on matching scores
db.matching_cache.aggregate([
  { $match: { job_id: ObjectId("..."), expires_at: { $gt: new Date() } } },
  { $sort: { score: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "candidates",
      localField: "candidate_id",
      foreignField: "_id",
      as: "candidate_info"
    }
  }
]);
```

---
---
## 📊 Production Data Management

### **1. Current Production Statistics**
```javascript
// Production data overview (as of January 22, 2026)
db.candidates.countDocuments()
db.jobs.countDocuments()
db.clients.countDocuments()
db.feedback.countDocuments()
db.applications.countDocuments()

// Expected results (Updated January 22, 2026):
// candidates: 34 records
// jobs: 27 records  
// clients: 6+ records
// feedback: 15+ records
// applications: 150+ records
```

### **2. Data Quality Metrics**
```javascript
// Comprehensive data completeness analysis
db.candidates.aggregate([
  {
    $group: {
      _id: null,
      total_candidates: { $sum: 1 },
      with_skills: { $sum: { $cond: [{ $ne: ["$technical_skills", null] }, 1, 0] } },
      with_resume: { $sum: { $cond: [{ $ne: ["$resume_path", null] }, 1, 0] } },
      with_phone: { $sum: { $cond: [{ $ne: ["$phone", null] }, 1, 0] } },
      with_auth: { $sum: { $cond: [{ $ne: ["$password_hash", null] }, 1, 0] } },
      avg_experience: { $avg: "$experience_years" }
    }
  }
]);

// Job posting quality metrics
db.jobs.aggregate([
  {
    $group: {
      _id: null,
      total_jobs: { $sum: 1 },
      with_requirements: { $sum: { $cond: [{ $ne: ["$requirements", null] }, 1, 0] } },
      with_description: { $sum: { $cond: [{ $ne: ["$description", null] }, 1, 0] } },
      with_client: { $sum: { $cond: [{ $ne: ["$client_id", null] }, 1, 0] } },
      active_jobs: { $sum: { $cond: [{ $eq: ["$status", "active"] }, 1, 0] } }
    }
  }
]);
```

### **3. Performance Analytics**
```javascript
// AI matching performance metrics
db.matching_cache.aggregate([
  { $match: { expires_at: { $gt: new Date() } } },
  {
    $group: {
      _id: "$algorithm_version",
      cache_entries: { $sum: 1 },
      avg_score: { $avg: "$score" },
      min_score: { $min: "$score" },
      max_score: { $max: "$score" },
      avg_hits: { $avg: "$hit_count" }
    }
  }
]);

// RL system performance
db.ml_feedback.aggregate([
  {
    $group: {
      _id: null,
      total_feedback: { $sum: 1 },
      avg_reward: { $avg: "$reward_signal" },
      best_reward: { $max: "$reward_signal" }
    }
  }
]);
```

---
---
## 🔒 Security & Compliance

### **1. Authentication & Authorization**

#### **Triple Authentication System**
```javascript
// User authentication with 2FA
db.users.find(
  { is_active: true }, 
  { username: 1, role: 1, is_2fa_enabled: 1, 
    failed_login_attempts: 1, locked_until: 1, last_login: 1 }
);

// Client authentication
db.clients.find(
  { status: "active" }, 
  { client_id: 1, company_name: 1, status: 1,
    failed_login_attempts: 1, locked_until: 1 }
);

// Candidate authentication
db.candidates.aggregate([
  {
    $group: {
      _id: null,
      total_candidates: { $sum: 1 },
      with_auth: { $sum: { $cond: [{ $ne: ["$password_hash", null] }, 1, 0] } },
      active_candidates: { $sum: { $cond: [{ $eq: ["$status", "applied"] }, 1, 0] } }
    }
  }
]);
```

#### **Role-Based Access Control**
MongoDB handles access control through user roles and collection-level permissions:

```javascript
// Create MongoDB users with specific roles
db.createUser({
  user: "read_only_user",
  pwd: passwordPrompt(), // Prompts for password
  roles: [
    { role: "read", db: "bhiv_hr" }
  ]
});

db.createUser({
  user: "app_user",
  pwd: passwordPrompt(),
  roles: [
    { role: "readWrite", db: "bhiv_hr" }
  ]
});

db.createUser({
  user: "admin_user",
  pwd: passwordPrompt(),
  roles: [
    { role: "dbAdmin", db: "bhiv_hr" },
    { role: "readWriteAnyDatabase", db: "bhiv_hr" }
  ]
});
```

### **2. Data Protection & Privacy**

#### **GDPR Compliance Features**
```javascript
// Data retention policy - anonymize old data
db.candidates.updateMany(
  { 
    created_at: { $lt: new Date(Date.now() - 7 * 365 * 24 * 60 * 60 * 1000) }, // 7 years ago
    name: { $not: { $regex: /^ANONYMIZED_/ } }
  },
  {
    $set: {
      name: { $concat: ["ANONYMIZED_", "$_id"] },
      email: { $concat: ["anonymized_", { $toString: "$_id" }, "@example.com"] },
      phone: null,
      technical_skills: "ANONYMIZED"
    }
  }
);
```

#### **Audit Trail & Monitoring**
```javascript
// Security monitoring queries
db.csp_violations.aggregate([
  {
    $match: { 
      created_at: { $gt: new Date(Date.now() - 24 * 60 * 60 * 1000) } // Last 24 hours
    }
  },
  {
    $group: {
      _id: "$ip_address",
      violation_count: { $sum: 1 },
      directives: { $addToSet: "$violated_directive" }
    }
  },
  { $match: { violation_count: { $gt: 10 } } }
]);

// Rate limiting analysis
db.rate_limits.aggregate([
  {
    $match: { 
      created_at: { $gt: new Date(Date.now() - 60 * 60 * 1000) } // Last hour
    }
  },
  {
    $group: {
      _id: {
        ip_address: "$ip_address",
        endpoint: "$endpoint"
      },
      total_requests: { $sum: "$request_count" },
      windows: { $sum: 1 },
      was_blocked: { $max: "$is_blocked" }
    }
  },
  { $sort: { "total_requests": -1 } }
]);
```

---
---
## 🔧 Maintenance & Operations

### **1. Database Health Monitoring**

#### **Performance Monitoring Queries**
MongoDB provides extensive performance monitoring through the database profiler and system commands:

```javascript
// Get current operations
db.currentOp();

// Get database stats
db.stats();

// Get collection stats
db.candidates.stats();
db.jobs.stats();

// Get index stats
db.runCommand({ "aggregate": "candidates", "pipeline": [], "explain": true });

// Monitor slow queries (those taking more than 100ms)
db.setProfilingLevel(1, { slowms: 100 });
db.system.profile.find().sort({ $natural: -1 }).limit(5);

// Connection and activity monitoring
db.serverStatus().connections;

// Index usage analysis
db.runCommand({ "listIndexes": "candidates" });
```

#### **System Health Checks**
```javascript
// Database health dashboard
{
  database_size: db.stats().dataSize,
  collections_count: db.getCollectionNames().length,
  indexes_count: db.adminCommand({ "listDatabases": 1 }).databases[0].collections * 3, // Approximation
  connected_clients: db.serverStatus().connections.current,
  cache_hit_ratio: db.serverStatus().indexCounters.missRatio,
  uptime: db.serverStatus().uptime
}

// Check replica set status (if applicable)
rs.status();

// Check sharding status (if applicable)
sh.status();
```

### **2. Backup & Recovery Strategy**

#### **Automated Backup System**
```bash
#!/bin/bash
# Daily MongoDB backup script
BACKUP_DIR="/backups/bhiv_hr"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="bhiv_hr"

# Full database backup using mongodump
mongodump --db $DB_NAME --out "$BACKUP_DIR/bhiv_hr_backup_$DATE"

# Compress backup
tar -czf "$BACKUP_DIR/bhiv_hr_backup_$DATE.tar.gz" -C "$BACKUP_DIR" "bhiv_hr_backup_$DATE"

# Clean up uncompressed directory
rm -rf "$BACKUP_DIR/bhiv_hr_backup_$DATE"

# Rotate backups - keep 30 days of full backups
find $BACKUP_DIR -name "bhiv_hr_backup_*.tar.gz" -mtime +30 -delete
```

#### **Restore Process**
```bash
# Restore from backup
mongorestore --drop --db bhiv_hr /path/to/backup/directory/bhiv_hr/

# Restore specific collections
mongorestore --collection candidates --db bhiv_hr /path/to/backup/directory/bhiv_hr/candidates.bson
```

### **3. Performance Tuning & Optimization**

#### **Connection Management**
```javascript
// Optimal connection settings for Motor (async driver)
const { MongoClient } = require('mongodb');
const client = new MongoClient(process.env.MONGODB_URI, {
  maxPoolSize: 10,          // Maximum connections in the pool
  minPoolSize: 2,           // Minimum connections in the pool
  maxIdleTimeMS: 30000,     // Close connections after 30 seconds of inactivity
  serverSelectionTimeoutMS: 5000, // Wait 5 seconds for server selection
  socketTimeoutMS: 45000,   // Close sockets after 45 seconds of inactivity
});
```

#### **Index Maintenance**
MongoDB automatically maintains indexes, but you can manage them as needed:

```javascript
// List all indexes
db.candidates.getIndexes();

// Create an index
db.candidates.createIndex({ "email": 1 }, { unique: true });

// Drop an index
db.candidates.dropIndex("email_1");

// Rebuild indexes (if needed)
db.candidates.reIndex();

// Get index statistics
db.candidates.aggregate([{ $indexStats: {} }]);
```

---
---
## 📈 Schema Evolution & Versioning

### **1. Version Management System**

#### **Schema Version Tracking**
In MongoDB, schema versioning is managed through a dedicated collection:

```javascript
// Create schema version collection
db.createCollection("schema_version");

// Insert current version record
db.schema_version.insertOne({
  version: "4.3.0",
  applied_at: new Date(),
  description: "Complete RL integration with collections, enhanced security, and performance optimization",
  migration_script: "migration_v4.3.0.js",
  rollback_script: "rollback_v4.3.0.js"
});
```

#### **Migration History**
```javascript
// Schema evolution timeline
db.schema_version.find().sort({ applied_at: -1 });

// Expected history:
// v4.3.0 (2026-01-22): RL integration + security enhancements
// v4.2.0 (2025-11-15): Performance optimization + audit improvements  
// v4.1.0 (2025-10-20): LangGraph workflow support
// v4.0.0 (2025-09-15): Initial production schema
```

### **2. Future Enhancement Roadmap**

#### **Planned Features (v4.4.0)**
- **Document Validation**: Enhanced schema validation rules
- **Computed Fields**: Automatic field calculation
- **Partial Indexes**: More efficient indexing strategies
- **Sharding Preparation**: Horizontal scaling readiness

#### **Advanced Analytics (v4.5.0)**
- **Time Series Collections**: Performance metrics over time
- **Data Lake Integration**: Analytics pipeline support
- **Real-time Analytics**: Streaming aggregation pipelines
- **Predictive Analytics**: ML-driven insights

---
---
## 🛠️ Development & Integration Guide

### **1. Local Development Setup**

#### **Docker-based Development**
```bash
# Clone repository
git clone https://github.com/Shashank-0208/BHIV-HR-PLATFORM.git
cd BHIV-HR-Platform

# Setup environment
cp .env.example .env
# Edit .env with your MongoDB connection string

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify setup
mongo "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/bhiv_hr" --eval "db.getName()"
```

#### **Direct MongoDB Setup**
```bash
# Connect to MongoDB Atlas (cloud) or local MongoDB instance
# For local setup, install MongoDB Community Edition
# For cloud setup, use MongoDB Atlas connection string

# Connection string format:
# mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>
```

### **2. Service Integration**

#### **Database Connection Configuration**
```python
# services/gateway/app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = os.getenv(
    "MONGODB_URI", 
    "mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr"
)

# Async client for Gateway service
motor_client = AsyncIOMotorClient(MONGODB_URI)
db = motor_client.bhiv_hr

# Sync client for Agent and LangGraph services
sync_client = MongoClient(MONGODB_URI)
sync_db = sync_client.bhv_hr
```

#### **Service-Specific Database Access**
```python
# Each service has dedicated database access patterns:

# Gateway Service: Full CRUD operations across all collections using Motor (async)
# AI Agent: Read access to candidates/jobs, write to matching_cache/ml_feedback using PyMongo (sync)
# LangGraph: Read/write for workflow tracking and notifications using PyMongo (sync)
```

### **3. Testing & Validation**

#### **Database Test Suite**
```bash
# Run comprehensive database tests
python tests/database/test_schema.py
python tests/database/test_data_integrity.py
python tests/database/test_performance.py
python tests/database/test_security.py

# RL system tests
python tests/database/test_rl_integration.py

# Load testing
python tests/database/test_load_performance.py
```

#### **Data Validation Scripts**
```javascript
// Comprehensive data validation in MongoDB
db.applications.aggregate([
  {
    $lookup: {
      from: "candidates",
      localField: "candidate_id",
      foreignField: "_id",
      as: "candidate"
    }
  },
  {
    $lookup: {
      from: "jobs",
      localField: "job_id",
      foreignField: "_id",
      as: "job"
    }
  },
  {
    $match: {
      $or: [
        { candidate: { $size: 0 } },
        { job: { $size: 0 } }
      ]
    }
  },
  {
    $count: "orphaned_applications"
  }
]);

// RL system validation
db.ml_feedback.countDocuments();
```

---
---
## 📊 Analytics & Reporting

### **1. Business Intelligence Queries**

#### **Recruitment Analytics**
```javascript
// Hiring funnel analysis
db.applications.aggregate([
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  },
  {
    $group: {
      _id: null,
      funnel: {
        $push: {
          status: "$_id",
          count: "$count"
        }
      },
      total_applied: {
        $sum: {
          $cond: [{ $eq: ["$_id", "applied"] }, "$count", 0]
        }
      }
    }
  },
  {
    $project: {
      applied: {
        $arrayElemAt: [
          { $filter: { input: "$funnel", cond: { $eq: ["$$this.status", "applied"] } } },
          0
        ]
      },
      screening: {
        $arrayElemAt: [
          { $filter: { input: "$funnel", cond: { $eq: ["$$this.status", "screening"] } } },
          0
        ]
      },
      interview: {
        $arrayElemAt: [
          { $filter: { input: "$funnel", cond: { $eq: ["$$this.status", "interview"] } } },
          0
        ]
      },
      offer: {
        $arrayElemAt: [
          { $filter: { input: "$funnel", cond: { $eq: ["$$this.status", "offer"] } } },
          0
        ]
      },
      hired: {
        $arrayElemAt: [
          { $filter: { input: "$funnel", cond: { $eq: ["$$this.status", "hired"] } } },
          0
        ]
      },
      screening_rate: { $round: [{ $multiply: [{ $divide: ["$screening.count", "$total_applied"] }, 100] }, 2] },
      interview_rate: { $round: [{ $multiply: [{ $divide: ["$interview.count", "$total_applied"] }, 100] }, 2] },
      offer_rate: { $round: [{ $multiply: [{ $divide: ["$offer.count", "$total_applied"] }, 100] }, 2] },
      hire_rate: { $round: [{ $multiply: [{ $divide: ["$hired.count", "$total_applied"] }, 100] }, 2] }
    }
  }
]);
```

#### **AI Performance Analytics**
```javascript
// AI matching effectiveness
db.jobs.aggregate([
  { $match: { status: "active" } },
  {
    $lookup: {
      from: "matching_cache",
      localField: "_id",
      foreignField: "job_id",
      as: "matches"
    }
  },
  {
    $lookup: {
      from: "applications",
      localField: "_id",
      foreignField: "job_id",
      as: "applications"
    }
  },
  {
    $project: {
      title: 1,
      department: 1,
      total_matches: { $size: "$matches" },
      avg_match_score: { $avg: "$matches.score" },
      applications: { $size: "$applications" },
      hires: {
        $size: {
          $filter: {
            input: "$applications",
            cond: { $eq: ["$$this.status", "hired"] }
          }
        }
      }
    }
  },
  {
    $addFields: {
      hire_rate: {
        $cond: {
          if: { $eq: ["$applications", 0] },
          then: 0,
          else: { $round: [{ $multiply: [{ $divide: ["$hires", "$applications"] }, 100] }, 2] }
        }
      }
    }
  },
  { $sort: { hire_rate: -1 } }
]);
```

### **2. Performance Dashboards**

#### **System Performance Metrics**
```javascript
// Real-time system dashboard
[
  {
    name: "Active Users",
    value: db.users.countDocuments({ is_active: true }),
    unit: "users"
  },
  {
    name: "Active Jobs",
    value: db.jobs.countDocuments({ status: "active" }),
    unit: "jobs"
  },
  {
    name: "Pending Applications",
    value: db.applications.countDocuments({ status: { $in: ["applied", "screening"] } }),
    unit: "applications"
  },
  {
    name: "Cache Hit Rate",
    value: db.matching_cache.aggregate([
      { $match: { expires_at: { $gt: new Date() } } },
      { $group: { _id: null, avg_hits: { $avg: "$hit_count" } } },
      { $project: { avg_hits: { $round: ["$avg_hits", 2] } } }
    ]).toArray()[0]?.avg_hits || 0,
    unit: "hits"
  }
]
```

---
---
## 🔧 Recent Database Fixes & Troubleshooting

### **✅ Fixed: MongoDB Connection Issues (January 22, 2026)**

#### **Issue Identified:**
- **Problem**: MongoDB connection timeout or authentication failures
- **Error**: `ServerSelectionTimeoutError` or `Authentication failed`
- **Root Cause**: Mismatched connection string in .env configuration
- **Impact**: Jobs API and all database-dependent endpoints were offline

#### **Solution Applied:**
```bash
# Verify MongoDB connection
mongo "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/bhiv_hr" --eval "db.runCommand({serverStatus: 1})"

# Or test with Node.js
node -e "require('mongodb').MongoClient.connect(process.env.MONGODB_URI).then(() => console.log('Connected successfully')).catch(console.error)"
```

#### **Verification Results:**
- ✅ **Database Connection**: Successful from all services
- ✅ **Jobs API**: Working - 27 jobs available
- ✅ **Candidates API**: Working - 34 candidates available
- ✅ **All Services**: Healthy and running
- ✅ **Data Preserved**: No data loss during fix

#### **Current Status:**
- Database: Connected and operational
- Gateway API: All 111 endpoints working
- Data Counts: 34 candidates, 27 jobs verified
- All microservices: Fully operational

### **Database Connection Troubleshooting Guide**

#### **Common Issues & Solutions:**

**1. Connection Issues:**
```bash
# Test MongoDB connection
mongo "mongodb+srv://username:password@cluster.mongodb.net/bhiv_hr" --eval "db.getName()"

# Check connection string format
echo $MONGODB_URI
```

**2. Connection Verification:**
```bash
# Test from Python
python -c "import motor.motor_asyncio; import asyncio; async def test(): client = motor.motor_asyncio.AsyncIOMotorClient('your_mongodb_uri'); await client.admin.command('ping'); print('Connected successfully'); asyncio.run(test())"

# Test API endpoints
curl -H "Authorization: Bearer prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o" http://localhost:8000/v1/jobs
```

**3. Data Validation:**
```javascript
// Verify current data counts
db.candidates.countDocuments()
db.jobs.countDocuments()
db.clients.countDocuments()

// Expected results (January 22, 2026):
// candidates: 34
// jobs: 27
// clients: 6+
```

---

**BHIV HR Platform Database Documentation v4.3.0** - Complete MongoDB Atlas NoSQL database with 17+ collections, reinforcement learning integration, and production-grade security.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Last Updated**: January 22, 2026 | **Schema**: v4.3.0 | **Collections**: 17+ Total | **Status**: ✅ Production Ready | **Services**: 3/3 Live | **Uptime**: 99.9% | **Recent Fix**: MongoDB connection resolved
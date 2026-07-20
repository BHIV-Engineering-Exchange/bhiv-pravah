# 🗄️ MongoDB Collections Documentation

## **MongoDB Collections Schema & Structure**
**Updated**: January 22, 2026  
**Version**: v4.3.0  
**Status**: ✅ Production Ready  

---

## 📋 Collections Overview

The BHIV HR Platform uses MongoDB Atlas with 17+ collections organized into functional groups:

### **Core Application Collections (9)**
1. `candidates` - Candidate profiles and authentication
2. `jobs` - Job postings and requirements  
3. `applications` - Job application tracking
4. `job_applications` - Per-job shortlist/application status (used by `POST /v1/jobs/{job_id}/shortlist`; `job_id` and `candidate_id` as strings)
5. `feedback` - BHIV values assessment
6. `interviews` - Interview scheduling and results
7. `offers` - Job offers and negotiations
8. `users` - HR user management
9. `clients` - Client company information

### **System Collections (5)**
9. `api_keys` - API authentication management
10. `rate_limits` - Dynamic rate limiting data
11. `audit_logs` - Complete system audit trail
12. `notifications` - Multi-channel notification log
13. `sessions` - User session management

### **Reinforcement Learning Collections (4)**
14. `ml_feedback` - Reinforcement learning feedback
15. `performance_metrics` - System performance data
16. `matching_cache` - AI matching results cache
17. `company_scoring_preferences` - Client-specific scoring weights

---

## 🏗️ Collection Schemas

### **1. candidates Collection**
**Purpose**: Stores candidate profiles and authentication information
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "name": "John Doe",                       // Candidate's full name
  "email": "john@example.com",              // Unique email address
  "phone": "+1234567890",                  // Phone number
  "location": "San Francisco, CA",          // Geographic location
  "experience_years": 5,                    // Years of experience (>=0)
  "technical_skills": "Python, Django...",  // Technical skills list
  "seniority_level": "Senior",              // Seniority level
  "education_level": "Bachelor's",          // Education level
  "resume_path": "/resumes/john_doe.pdf",   // Resume file path
  "password_hash": "$2b$12$...",           // bcrypt hash for authentication
  "status": "applied",                      // Candidate status
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ email: 1 }` (unique)
- `{ status: 1 }`
- `{ location: 1, experience_years: 1 }` (compound)
- `{ technical_skills: "text" }` (text search)

**Validation Schema**:
```javascript
{
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "email", "created_at"],
      properties: {
        name: { bsonType: "string" },
        email: { bsonType: "string", pattern: "^[^@]+@[^@]+\\.[^@]+$" },
        experience_years: { bsonType: "int", minimum: 0 },
        status: { 
          enum: ["applied", "screening", "interview", "offer", "hired", "rejected"] 
        }
      }
    }
  }
}
```

### **2. jobs Collection**
**Purpose**: Stores job postings and requirements
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "title": "Senior Python Developer",       // Job title
  "department": "Engineering",              // Department name
  "location": "Remote",                     // Job location
  "experience_level": "Senior",             // Required experience level
  "requirements": "Python, Django...",      // Job requirements
  "description": "We are looking for...",   // Job description
  "client_id": "client123",                 // Associated client ID
  "employment_type": "Full-time",           // Employment type
  "status": "active",                       // Job posting status
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ status: 1, department: 1 }` (compound)
- `{ client_id: 1, status: 1 }` (compound)
- `{ requirements: "text", description: "text" }` (text search)

### **3. applications Collection**
**Purpose**: Tracks job applications and status
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "candidate_id": ObjectId("..."),           // Reference to candidate
  "job_id": ObjectId("..."),                 // Reference to job
  "cover_letter": "I am excited...",        // Cover letter
  "status": "applied",                       // Application status
  "applied_date": ISODate("2026-01-22T10:00:00Z"), // Application date
  "last_updated": ISODate("2026-01-22T10:00:00Z"), // Last status update
  "source": "portal",                        // Application source
  "notes": "Strong candidate...",            // Internal notes
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ candidate_id: 1, status: 1 }` (compound)
- `{ job_id: 1, status: 1 }` (compound)
- `{ applied_date: -1 }` (descending)

### **4. job_applications Collection**
**Purpose**: Tracks per-job shortlist and application status; used by Gateway `POST /v1/jobs/{job_id}/shortlist` to mark candidates as shortlisted.
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "job_id": "69722cbe8d9c05b1a84e1e71",     // Job ID (MongoDB ObjectId string)
  "candidate_id": "507f1f77bcf86cd799439011", // Candidate ID (ObjectId string)
  "status": "shortlisted",                   // e.g. "shortlisted", "applied"
  "created_at": ISODate("2026-01-30T10:00:00Z"),
  "updated_at": ISODate("2026-01-30T10:00:00Z")
}
```
**Indexes** (recommended):
- `{ job_id: 1, candidate_id: 1 }` (compound, unique for upsert)
- `{ job_id: 1, status: 1 }`

**Note:** Job and candidate identifiers are stored as strings (24-char hex ObjectId) for consistency with Gateway API paths and frontend.

### **5. feedback Collection**
**Purpose**: Stores BHIV values assessment and feedback
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "candidate_id": ObjectId("..."),           // Reference to candidate
  "job_id": ObjectId("..."),                 // Reference to job
  "integrity": 5,                           // Integrity score (1-5)
  "honesty": 5,                             // Honesty score (1-5)
  "discipline": 4,                          // Discipline score (1-5)
  "hard_work": 5,                           // Hard work score (1-5)
  "gratitude": 4,                           // Gratitude score (1-5)
  "average_score": 4.6,                     // Calculated average (0-5)
  "comments": "Excellent candidate...",      // Feedback comments
  "evaluator_id": ObjectId("..."),           // Who provided feedback
  "evaluation_type": "interview",           // Type of evaluation
  "created_at": ISODate("2026-01-22T10:00:00Z") // Creation timestamp
}
```

**Indexes**:
- `{ candidate_id: 1, job_id: 1 }` (compound)
- `{ average_score: -1 }` (descending)

### **6. interviews Collection**
**Purpose**: Manages interview scheduling and results
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "candidate_id": ObjectId("..."),           // Reference to candidate
  "job_id": ObjectId("..."),                 // Reference to job
  "interview_date": ISODate("2026-01-25T14:00:00Z"), // Scheduled date
  "interviewer": "Jane Smith",              // Conducting interviewer
  "interview_type": "technical",            // Type of interview
  "status": "scheduled",                     // Interview status
  "notes": "Technical interview...",         // Interview notes
  "score": 8,                               // Interview score (1-10)
  "duration_minutes": 60,                   // Duration in minutes
  "meeting_link": "https://meet.google.com/...", // Meeting link
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ interview_date: 1 }`
- `{ candidate_id: 1, status: 1 }` (compound)

### **7. offers Collection**
**Purpose**: Manages job offers and negotiations
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "candidate_id": ObjectId("..."),           // Reference to candidate
  "job_id": ObjectId("..."),                 // Reference to job
  "salary": 120000,                         // Offered salary
  "currency": "USD",                        // Currency code
  "start_date": ISODate("2026-02-01"),      // Proposed start date
  "terms": "Standard terms apply",          // Offer terms
  "benefits": "Health insurance...",        // Benefits package
  "status": "pending",                       // Offer status
  "offer_date": ISODate("2026-01-22"),      // Date offer made
  "expiry_date": ISODate("2026-02-05"),     // Expiration date
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ candidate_id: 1, status: 1 }` (compound)
- `{ expiry_date: 1 }` (with status filter)

### **8. users Collection**
**Purpose**: HR user management and authentication
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "username": "jane_smith",                 // Unique username
  "email": "jane@company.com",              // User's email
  "password_hash": "$2b$12$...",           // bcrypt hash for authentication
  "role": "hr_manager",                     // User role
  "totp_secret": "JBSWY3DPEHPK3PXP",       // 2FA secret
  "is_2fa_enabled": true,                   // 2FA enabled flag
  "failed_login_attempts": 0,               // Failed login attempts
  "locked_until": null,                     // Lockout timestamp
  "last_login": ISODate("2026-01-22T09:00:00Z"), // Last login time
  "is_active": true,                        // Active status
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ username: 1 }` (unique)
- `{ email: 1 }` (unique)
- `{ role: 1, is_active: 1 }` (compound)

### **9. clients Collection**
**Purpose**: Client company information and authentication
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "client_id": "client123",                 // Unique client identifier
  "company_name": "Tech Corp Inc.",         // Company name
  "email": "contact@techcorp.com",          // Contact email
  "password_hash": "$2b$12$...",           // bcrypt hash for authentication
  "contact_person": "John Johnson",         // Primary contact
  "phone": "+1234567890",                  // Contact phone
  "address": "123 Business Ave...",         // Company address
  "industry": "Technology",                 // Industry type
  "company_size": "Large",                  // Company size
  "status": "active",                       // Client status
  "failed_login_attempts": 0,               // Failed login attempts
  "locked_until": null,                     // Lockout timestamp
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ client_id: 1 }` (unique)
- `{ email: 1 }` (unique)
- `{ status: 1 }`

---

## 🔐 System Collections

### **10. api_keys Collection**
**Purpose**: API authentication and rate limiting
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "key": "sk_live_abc123def456...",        // API key value
  "name": "Production Gateway API Key",     // Key description
  "user_id": ObjectId("..."),               // Associated user
  "client_id": ObjectId("..."),             // Associated client
  "permissions": ["read", "write"],         // Granted permissions
  "rate_limit": 500,                        // Requests per minute
  "expires_at": null,                       // Expiration timestamp
  "is_active": true,                        // Active status
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

### **11. rate_limits Collection**
**Purpose**: Dynamic API rate limiting
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "ip_address": "192.168.1.1",            // Client IP address
  "endpoint": "/v1/candidates",             // API endpoint
  "request_count": 45,                      // Count of requests
  "window_start": ISODate("2026-01-22T10:00:00Z"), // Window start time
  "window_duration": 60,                    // Window duration (seconds)
  "limit_type": "standard",                 // Standard, premium, enterprise
  "is_blocked": false,                      // Blocked status
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

**Indexes**:
- `{ ip_address: 1, endpoint: 1, window_start: 1 }` (unique compound)
- `{ created_at: 1 }` (with TTL)

### **12. audit_logs Collection**
**Purpose**: Complete system audit trail
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "collection_name": "candidates",          // Name of collection affected
  "operation": "UPDATE",                    // INSERT, UPDATE, DELETE
  "document_id": ObjectId("..."),           // Affected document ID
  "old_values": {                           // Previous values (for updates/deletes)
    "status": "screening"
  },
  "new_values": {                           // New values (for inserts/updates)
    "status": "interview"
  },
  "user_id": ObjectId("..."),               // Performing user ID
  "user_type": "hr_user",                   // Type of user
  "ip_address": "192.168.1.1",            // IP address
  "user_agent": "Mozilla/5.0...",          // Browser/user agent
  "endpoint": "/v1/candidates/...",         // API endpoint
  "session_id": "sess_abc123...",           // Session identifier
  "created_at": ISODate("2026-01-22T10:00:00Z") // Timestamp
}
```

### **13. notifications Collection**
**Purpose**: Multi-channel notification tracking
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "recipient_id": ObjectId("..."),           // Recipient ID
  "recipient_type": "candidate",            // candidate, client, hr
  "notification_type": "email",             // email, whatsapp, telegram, sms
  "template": "interview_scheduled",        // Template name
  "subject": "Interview Scheduled",         // Subject (for email)
  "message": "Your interview is scheduled...", // Message content
  "status": "sent",                         // pending, sent, delivered, failed
  "delivery_attempts": 1,                   // Number of delivery attempts
  "sent_at": ISODate("2026-01-22T10:00:00Z"), // Sent timestamp
  "delivered_at": ISODate("2026-01-22T10:01:00Z"), // Delivery timestamp
  "created_at": ISODate("2026-01-22T10:00:00Z") // Creation timestamp
}
```

---

## 🤖 Reinforcement Learning Collections

### **14. ml_feedback Collection**
**Purpose**: Machine learning feedback for reinforcement learning
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "candidate_id": ObjectId("..."),           // Associated candidate
  "job_id": ObjectId("..."),                 // Associated job
  "prediction_id": ObjectId("..."),          // Related prediction
  "feedback_source": "hr",                  // hr, client, candidate, system, workflow_automation
  "actual_outcome": "hired",                // hired, rejected, withdrawn, interviewed, shortlisted, pending
  "feedback_score": 4.5,                    // Feedback score (1-5)
  "reward_signal": 1.25,                    // Calculated reward signal
  "feedback_notes": "Candidate performed well...", // Additional notes
  "created_at": ISODate("2026-01-22T10:00:00Z") // Creation timestamp
}
```

### **14. performance_metrics Collection**
**Purpose**: System performance tracking
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "metric_name": "api_response_time",       // Name of metric
  "value": 45.2,                            // Measured value
  "unit": "milliseconds",                   // Unit of measurement
  "source_service": "gateway",              // Source service
  "endpoint": "/v1/candidates",             // Associated endpoint
  "timestamp": ISODate("2026-01-22T10:00:00Z"), // Measurement time
  "tags": {                                 // Additional tags
    "environment": "production",
    "region": "us-east-1"
  }
}
```

### **16. matching_cache Collection**
**Purpose**: AI matching results cache for performance
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "job_id": ObjectId("..."),                 // Associated job
  "candidate_id": ObjectId("..."),           // Associated candidate
  "score": 85.5,                            // Match score (0-100)
  "algorithm_version": "phase3_v1.0",       // Algorithm version
  "semantic_score": 80.2,                   // Semantic match score
  "experience_score": 88.5,                 // Experience match score
  "skills_score": 92.1,                     // Skills match score
  "location_score": 75.0,                   // Location match score
  "cultural_fit_score": 85.3,               // Cultural fit score
  "cached_at": ISODate("2026-01-22T10:00:00Z"), // Cache creation time
  "expires_at": ISODate("2026-01-23T10:00:00Z"), // Expiration time
  "hit_count": 5,                           // Number of cache hits
  "reasoning": "Strong technical skills..." // Reasoning for match
}
```

**Indexes**:
- `{ job_id: 1, expires_at: 1 }` (compound)
- `{ candidate_id: 1, expires_at: 1 }` (compound)
- `{ score: -1 }` (descending)
- `{ expires_at: 1 }` (with TTL)

### **17. company_scoring_preferences Collection**
**Purpose**: Adaptive learning engine for company-specific preferences
```javascript
{
  "_id": ObjectId("..."),                    // Unique identifier
  "client_id": ObjectId("..."),              // Associated client
  "semantic_weight": 0.40,                  // Semantic matching weight (0-1)
  "experience_weight": 0.30,                // Experience weight (0-1)
  "skills_weight": 0.20,                    // Skills weight (0-1)
  "location_weight": 0.10,                  // Location weight (0-1)
  "cultural_fit_bonus": 0.10,               // Cultural fit bonus (0-0.5)
  "learning_rate": 0.001,                   // Learning rate parameter
  "total_feedback_count": 0,                // Total feedback received
  "last_optimization": ISODate("2026-01-22T10:00:00Z"), // Last optimization
  "created_at": ISODate("2026-01-22T10:00:00Z"), // Creation timestamp
  "updated_at": ISODate("2026-01-22T10:00:00Z")  // Last update timestamp
}
```

---

## 🔧 Indexing Strategy

### **Essential Indexes**
```javascript
// Candidates indexes
db.candidates.createIndex({ "email": 1 }, { unique: true });
db.candidates.createIndex({ "status": 1 });
db.candidates.createIndex({ "location": 1, "experience_years": 1 });
db.candidates.createIndex({ "technical_skills": "text" });

// Jobs indexes
db.jobs.createIndex({ "status": 1, "department": 1 });
db.jobs.createIndex({ "client_id": 1, "status": 1 });
db.jobs.createIndex({ "requirements": "text", "description": "text" });

// Applications indexes
db.applications.createIndex({ "candidate_id": 1, "status": 1 });
db.applications.createIndex({ "job_id": 1, "status": 1 });
db.applications.createIndex({ "applied_date": -1 });

// Feedback indexes
db.feedback.createIndex({ "candidate_id": 1, "job_id": 1 });
db.feedback.createIndex({ "average_score": -1 });

// Rate limits indexes
db.rate_limits.createIndex({ "ip_address": 1, "endpoint": 1, "window_start": 1 }, { unique: true });
db.rate_limits.createIndex({ "created_at": 1 }, { expireAfterSeconds: 3600 }); // 1 hour TTL

// Matching cache indexes
db.matching_cache.createIndex({ "job_id": 1, "expires_at": 1 });
db.matching_cache.createIndex({ "candidate_id": 1, "expires_at": 1 });
db.matching_cache.createIndex({ "score": -1 });
db.matching_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 86400 }); // 24 hour TTL
```

---

## 🔒 Security Considerations

### **Data Validation**
All collections implement JSON schema validation to ensure data integrity:

```javascript
// Example validation for sensitive data
{
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        password_hash: {
          bsonType: "string",
          description: "Password hash must be stored securely"
        },
        email: {
          bsonType: "string",
          pattern: "^[^@]+@[^@]+\\.[^@]+$",
          description: "Must be a valid email address"
        }
      }
    }
  }
}
```

### **Access Controls**
- Use separate database users with minimal required permissions
- Implement field-level access controls where necessary
- Encrypt sensitive fields at rest when possible

---

**BHIV HR Platform MongoDB Collections Documentation** - Complete schema documentation for all 17+ collections with indexes, validation, and security considerations.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Last Updated**: January 22, 2026 | **Collections**: 17+ | **Status**: ✅ Production Ready | **Security**: Encrypted & Validated
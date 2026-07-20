# Known Issues & Limitations — BHIV HR Platform

**Version**: 4.3.1  
**Last Updated**: January 22, 2026  
**Status**: Production System with Known Issues Documented

**Service Distribution**: 80 Gateway, 6 Agent, 25 LangGraph (Total: 111 endpoints)
**Database**: MongoDB Atlas (Previously PostgreSQL)

---

## Table of Contents

1. [Critical Issues](#critical-issues)
2. [High Priority Issues](#high-priority-issues)
3. [Medium Priority Issues](#medium-priority-issues)
4. [Low Priority Issues](#low-priority-issues)
5. [Deprecated Code](#deprecated-code-do-not-use)
6. [Code That MUST NOT Be Changed](#code-that-must-not-be-changed)
7. [Incomplete Functions](#incomplete-functions)
8. [Performance Bottlenecks](#performance-bottlenecks)
9. [Security Concerns](#security-concerns)
10. [Known Limitations](#known-limitations)
11. [Action Items Summary](#action-items-summary)

---

## Critical Issues

### ISSUE-001: MongoDB Connection Pool Management on Long-Running Operations

**Severity**: Critical  
**Status**: Active (Workaround available)  
**Reported By**: System monitoring  
**Reported Date**: 2025-11-20

**Description**:
After 8+ hours of continuous operation, MongoDB connections aren't properly managed in some error paths, eventually affecting new queries. System performance degrades when connection pool exhausted.

**Root Cause**:
In `services/gateway/app/main.py`, MongoDB connections not properly closed in exception handlers. Connection pool configured with `maxPoolSize=10, minPoolSize=2`.

```python
# PROBLEMATIC CODE in main.py (multiple locations)
client = get_mongo_client()
db = client['bhiv_hr']
# If exception occurs here, connection may not be properly released
result = db.collection.find(query)
```

**Affected Components**:
- All Gateway API endpoints using database
- Long-running batch operations
- Concurrent request handling

**Workaround**:
1. Restart Gateway service every 6 hours using cron:
   ```bash
   0 */6 * * * docker restart bhiv-hr-gateway
   ```
2. Monitor connection count:
   ```javascript
   // MongoDB connection monitoring
   db.serverStatus().connections
   ```

**Permanent Fix (Recommended)**:
Update all database operations to use proper context managers:
```python
# CORRECT PATTERN
def get_mongo_client():
    mongodb_uri = os.getenv("DATABASE_URL")
    return MongoClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        minPoolSize=2,
        connectTimeoutMS=10000,
        socketTimeoutMS=20000,
    )

# Always use try-finally to ensure connection closure
try:
    client = get_mongo_client()
    db = client['bhiv_hr']
    result = db.collection.find(query)
    # Process results
except Exception as e:
    log_error("database_error", str(e))
finally:
    if 'client' in locals():
        client.close()
```

**Next Steps**:
1. Audit all database operations in Gateway service
2. Add connection pool monitoring to Prometheus metrics
3. Implement automatic connection cleanup on pool exhaustion
4. Test with 24-hour load test

**Estimated Fix Time**: 4-6 hours  
**Priority**: P0 - Must fix before scaling beyond 100 concurrent users

---

### ISSUE-002: Agent Service Fallback Matching Has Low Accuracy

**Severity**: Critical  
**Status**: Active (Affects user experience)  
**Reported By**: Production monitoring  
**Reported Date**: 2025-11-25

**Description**:
When AI Agent service is unavailable or times out, Gateway falls back to basic keyword matching which produces poor quality results (accuracy ~40% vs 85% for AI matching).

**Root Cause**:
Fallback matching in `services/gateway/app/main.py` (lines 1150-1250) uses simple keyword search without semantic understanding:

```python
# FALLBACK MATCHING - LOW ACCURACY
skill_match_count = sum(1 for skill in ['python', 'java', 'javascript'] 
                      if skill in candidate_skills and skill in job_requirements)
base_score = 60 + (skill_match_count * 10)
```

**Affected Components**:
- `GET /v1/match/{job_id}/top` endpoint
- `POST /v1/match/batch` endpoint
- HR Portal candidate recommendations

**Impact**:
- Users see irrelevant candidate recommendations
- Hiring decisions based on inaccurate scores
- Reduced trust in AI matching system

**Workaround**:
1. Monitor Agent service uptime (currently 99.5%)
2. Alert HR team when fallback mode activated
3. Manual review of all matches during fallback periods

**Permanent Fix (In Progress)**:
1. Implement local lightweight semantic model in Gateway
2. Cache recent AI matching results for similar jobs
3. Improve fallback algorithm with TF-IDF scoring
4. Add confidence score to indicate fallback mode

**Next Steps**:
1. Deploy lightweight sentence transformer model to Gateway
2. Implement result caching with 24-hour TTL
3. Add "Low Confidence" badge in UI during fallback
4. Set up Agent service redundancy (2 instances)

**Estimated Fix Time**: 2-3 days  
**Priority**: P0 - Affects core product value

---

### ISSUE-003: LangGraph Notification Failures Not Retried

**Severity**: Critical  
**Status**: Active (Data loss risk)  
**Reported By**: User reports  
**Reported Date**: 2025-12-01

**Description**:
When email/WhatsApp/Telegram notifications fail in LangGraph workflows, they are not automatically retried. Candidates miss critical communications (interview invites, offer letters).

**Root Cause**:
`services/langgraph/app/communication.py` lacks retry logic for failed notifications:

```python
# NO RETRY LOGIC
try:
    send_email(to, subject, body)
except Exception as e:
    logger.error(f"Email failed: {e}")
    # Notification lost - no retry, no queue
```

**Affected Components**:
- All LangGraph workflows (candidate_application, candidate_shortlisted, interview_scheduled)
- Email notifications (Gmail SMTP)
- WhatsApp notifications (Twilio API)
- Telegram notifications (Bot API)

**Impact**:
- Candidates miss interview invitations
- Offer letters not delivered
- Poor candidate experience
- Potential legal issues (missed communications)

**Workaround**:
1. Manual verification of notification delivery
2. HR team follows up via phone for critical notifications
3. Monitor `workflows` table for failed status

**Permanent Fix (Recommended)**:
Implement exponential backoff retry with dead letter queue:

```python
# RECOMMENDED PATTERN
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def send_email_with_retry(to, subject, body):
    try:
        send_email(to, subject, body)
        log_notification_success(to, "email")
    except Exception as e:
        log_notification_failure(to, "email", str(e))
        if attempt == 3:
            # Move to dead letter queue for manual review
            store_failed_notification(to, subject, body, "email")
        raise
```

**Next Steps**:
1. Install `tenacity` library for retry logic
2. Implement retry decorator for all notification functions
3. Create `failed_notifications` table for DLQ
4. Add admin UI to manually retry failed notifications
5. Set up alerting for high failure rates

**Estimated Fix Time**: 1 day  
**Priority**: P0 - Critical user experience issue

---

## High Priority Issues

### ISSUE-004: Rate Limiting Not Enforced on All Endpoints

**Severity**: High  
**Status**: Active (Security risk)  
**Reported By**: Security audit  
**Reported Date**: 2025-11-28

**Description**:
Rate limiting middleware in Gateway only applies to specific endpoints. Some endpoints (health, docs, openapi.json) are unprotected, allowing potential DDoS attacks.

**Root Cause**:
Rate limiting middleware in `services/gateway/app/main.py` (lines 130-180) doesn't exclude health endpoints from rate limiting, but also doesn't apply to all endpoints uniformly.

**Affected Components**:
- `/health` endpoint (unlimited requests)
- `/docs` endpoint (unlimited requests)
- `/openapi.json` endpoint (unlimited requests)
- All endpoints without explicit rate limit configuration

**Impact**:
- Potential DDoS attack vector
- Service degradation under high load
- Increased infrastructure costs

**Workaround**:
1. Use Cloudflare or AWS WAF for external rate limiting
2. Monitor request rates manually
3. Block suspicious IPs at firewall level

**Permanent Fix**:
```python
# RECOMMENDED: Apply rate limiting to all endpoints with exceptions
RATE_LIMIT_EXEMPT_PATHS = ["/health", "/metrics"]

async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in RATE_LIMIT_EXEMPT_PATHS:
        return await call_next(request)
    
    # Apply rate limiting logic
    # ... existing code ...
```

**Next Steps**:
1. Define rate limits for all endpoint categories
2. Implement IP-based rate limiting with Redis
3. Add rate limit headers to all responses
4. Set up monitoring for rate limit violations

**Estimated Fix Time**: 4 hours  
**Priority**: P1 - Security issue

---

### ISSUE-005: Bulk Candidate Import Lacks Transaction Management

**Severity**: High  
**Status**: Active (Data consistency risk)  
**Reported By**: QA testing  
**Reported Date**: 2025-12-03

**Description**:
`POST /v1/candidates/bulk` endpoint processes candidates one-by-one without proper transaction management. If import fails halfway, partial data is committed, leaving database in inconsistent state.

**Root Cause**:
In `services/gateway/app/main.py` (lines 650-750), bulk import uses `engine.begin()` but continues on individual errors:

```python
# PROBLEMATIC: Partial commits on error
with engine.begin() as connection:
    for candidate in candidates.candidates:
        try:
            connection.execute(insert_query, candidate_data)
            inserted_count += 1
        except Exception as e:
            errors.append(str(e))
            continue  # Continues processing, previous inserts committed
```

**Affected Components**:
- `POST /v1/candidates/bulk` endpoint
- HR Portal bulk import feature
- Data integrity

**Impact**:
- Partial imports create orphaned records
- Duplicate detection fails on retry
- Data cleanup required after failed imports

**Workaround**:
1. Import in small batches (10-20 candidates)
2. Manually verify import completion
3. Clean up partial imports before retry

**Permanent Fix**:
```python
# RECOMMENDED: All-or-nothing transaction
with engine.begin() as connection:
    try:
        for candidate in candidates.candidates:
            # Validate all first
            validate_candidate(candidate)
        
        # Then insert all
        for candidate in candidates.candidates:
            connection.execute(insert_query, candidate_data)
            inserted_count += 1
        
        # Commit only if all succeed
        return {"status": "success", "inserted": inserted_count}
    except Exception as e:
        # Rollback all on any error
        raise HTTPException(status_code=400, detail=str(e))
```

**Next Steps**:
1. Implement pre-validation phase
2. Add rollback on any error
3. Provide detailed error report before import
4. Add dry-run mode for validation

**Estimated Fix Time**: 3 hours  
**Priority**: P1 - Data integrity issue

---

### ISSUE-006: Missing Input Validation on Candidate Profile Updates

**Severity**: High  
**Status**: Active (Security risk)  
**Reported By**: Security audit  
**Reported Date**: 2025-12-05

**Description**:
`PUT /v1/candidate/profile/{candidate_id}` endpoint lacks comprehensive input validation. Malicious input can cause SQL injection or XSS attacks.

**Root Cause**:
In `services/gateway/app/main.py` (lines 1800-1900), dynamic SQL query construction without proper sanitization:

```python
# VULNERABLE CODE
update_fields = []
if profile_data.name:
    update_fields.append("name = :name")  # OK - parameterized
    
# But dynamic query construction is risky
query = text(f"UPDATE candidates SET {', '.join(update_fields)} WHERE id = :candidate_id")
```

**Affected Components**:
- `PUT /v1/candidate/profile/{candidate_id}` endpoint
- Candidate Portal profile update feature

**Impact**:
- Potential SQL injection
- XSS attacks via stored data
- Data corruption

**Workaround**:
1. Manual review of all profile updates
2. Input sanitization at frontend
3. Database-level constraints

**Permanent Fix**:
```python
# RECOMMENDED: Strict validation
from pydantic import validator, constr

class CandidateProfileUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    phone: Optional[constr(regex=r'^\+?[1-9]\d{1,14}$')] = None
    technical_skills: Optional[constr(max_length=1000)] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v and not v.replace(' ', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters')
        return v
    
    @validator('technical_skills')
    def sanitize_skills(cls, v):
        if v:
            # Remove HTML tags, SQL keywords
            v = re.sub(r'<[^>]+>', '', v)
            v = re.sub(r'\b(DROP|DELETE|INSERT|UPDATE|SELECT)\b', '', v, flags=re.IGNORECASE)
        return v
```

**Next Steps**:
1. Add Pydantic validators to all input models
2. Implement HTML sanitization library
3. Add SQL injection detection
4. Run security penetration tests

**Estimated Fix Time**: 6 hours  
**Priority**: P1 - Security vulnerability

---

## Medium Priority Issues

### ISSUE-007: Workflow Status Not Updated on External Service Failures

**Severity**: Medium  
**Status**: Active (Monitoring issue)  
**Reported By**: Operations team  
**Reported Date**: 2025-12-06

**Description**:
When external services (Twilio, Gmail, Telegram) fail, workflow status in `workflows` table remains "running" instead of "failed". Makes debugging difficult.

**Root Cause**:
`services/langgraph/app/main.py` doesn't update workflow status on external API failures.

**Affected Components**:
- All LangGraph workflows
- Workflow monitoring dashboard

**Workaround**:
1. Manual status updates via database
2. Monitor external service logs separately

**Permanent Fix**:
Add proper error handling and status updates:
```python
try:
    send_notification(...)
except ExternalServiceError as e:
    update_workflow_status(workflow_id, "failed", error_message=str(e))
    raise
```

**Estimated Fix Time**: 2 hours  
**Priority**: P2

---

### ISSUE-008: AI Agent Phase 3 Engine Fallback Not Logged

**Severity**: Medium  
**Status**: Active (Observability issue)  
**Reported By**: Development team  
**Reported Date**: 2025-12-07

**Description**:
When Phase 3 semantic engine is unavailable, Agent service falls back to basic matching without logging the fallback event. Makes debugging accuracy issues difficult.

**Root Cause**:
`services/agent/app.py` (lines 200-400) silently falls back without metrics.

**Affected Components**:
- AI Agent matching accuracy
- Performance monitoring

**Workaround**:
1. Check Agent service logs manually
2. Compare match scores (fallback scores are lower)

**Permanent Fix**:
```python
if not PHASE3_AVAILABLE:
    logger.warning("Phase 3 engine unavailable, using fallback matching")
    metrics.increment("agent.fallback_matching_used")
    # Add fallback indicator to response
    response["algorithm_version"] += "-fallback"
```

**Estimated Fix Time**: 1 hour  
**Priority**: P2

---

## Low Priority Issues

### ISSUE-009: Dashboard Statistics Query Performance Degradation

**Severity**: Low  
**Status**: Active (Performance issue)  
**Reported By**: Performance monitoring  
**Reported Date**: 2025-12-08

**Description**:
`GET /v1/candidates/stats` endpoint becomes slow (>2s) when database has >10,000 candidates. Query scans entire collection without proper indexes.

**Root Cause**:
In `services/gateway/app/main.py` (lines 550-650), statistics query lacks optimized indexes:

```javascript
// SLOW QUERY
db.candidates.countDocuments({ created_at: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } })
```

**Affected Components**:
- HR Portal dashboard
- Analytics endpoints

**Impact**:
- Slow dashboard load times
- Increased database load

**Workaround**:
1. Cache statistics for 5 minutes
2. Run statistics query asynchronously

**Permanent Fix**:
```javascript
// Add index for date-based queries
db.candidates.createIndex({ "created_at": 1 })

// Use aggregation pipeline for statistics
db.candidates.aggregate([
  {
    $match: {
      created_at: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
    }
  },
  {
    $group: {
      _id: null,
      total: { $sum: 1 },
      new_this_week: { $sum: 1 }
    }
  }
])

// Create TTL index for automatic cleanup
db.candidates.createIndex({ "created_at": 1 }, { expireAfterSeconds: 2592000 }) // 30 days
```

**Estimated Fix Time**: 2 hours  
**Priority**: P3

---

## Deprecated Code (DO NOT USE)

### Module: `old_ranking_engine.py` (DEPRECATED)

**Location**: Previously in `services/agent/`  
**Status**: Removed  
**Reason**: Replaced by Phase 3 Semantic Engine  
**Last Used**: 2025-10-15  
**Removal Date**: Already removed  
**Migration Path**: All imports changed to `semantic_engine/phase3_engine.py`

**Action**: No action needed - already migrated

---

### Function: `simple_keyword_match()` (DEPRECATED)

**Location**: `services/gateway/app/main.py` (commented out)  
**Status**: Deprecated but still in code  
**Reason**: Replaced by AI Agent semantic matching  
**Last Used**: 2025-11-01  
**Migration Path**: Use `POST /match` endpoint to AI Agent service

**Action**: Remove commented code in next cleanup sprint

---

## Code That MUST NOT Be Changed

### File: `services/gateway/app/main.py` — Core Gateway Service

**Why**: Central routing for all API requests, changes can break entire system  
**Last Modified**: 2025-12-05  
**Critical Sections**:
- Authentication middleware (lines 300-400)
- Rate limiting middleware (lines 130-180)
- MongoDB connection management (lines 420-450)

**If you MUST change**:
1. Create feature branch
2. Test on staging for 48 hours minimum
3. Run full test suite (111 endpoints)
4. Have rollback plan ready
5. Deploy during low-traffic window

---

### File: `services/agent/semantic_engine/phase3_engine.py` — AI Matching Core

**Why**: Production ML model, any bug loses matching accuracy  
**Last Modified**: 2025-11-20  
**Protection**:
- Versioned model files (don't overwrite)
- All changes require ML expert review
- A/B testing required before full deployment

**If you MUST change**:
1. Create new model version (v3.1.0)
2. Deploy alongside existing model
3. A/B test with 10% traffic for 1 week
4. Monitor accuracy metrics
5. Rollback if accuracy drops >5%

---

### Database Schema: MongoDB Collections — Production Schema

**Why**: Schema changes require careful migration planning  
**Last Modified**: 2025-12-04  
**Critical Collections**:
- `candidates` - 19 indexes, referenced by 7 collections
- `jobs` - 6 indexes, referenced by 6 collections
- `feedback` - Computed field (average_score)

**If you MUST change**:
1. Create migration script with rollback
2. Test on copy of production data
3. Schedule maintenance window
4. Backup database before migration
5. Monitor for 24 hours after migration

---

## Incomplete Functions

### Function: `batch_fallback_matching()` — Limited Functionality

**Location**: `services/gateway/app/main.py` (lines 1250-1350)  
**Status**: 60% complete  
**Missing**:
- Proper semantic analysis
- Confidence scoring
- Result caching

**What Works**: Basic keyword matching for batch jobs  
**What Doesn't Work**: Accurate scoring, semantic understanding

**Usage**: Avoid using for production matching, only for fallback  
**ETA for Completion**: 2025-12-20

---

### Function: `send_telegram_notification()` — Partial Implementation

**Location**: `services/langgraph/app/communication.py`  
**Status**: 70% complete  
**Missing**:
- Rich message formatting
- Inline buttons
- File attachments

**What Works**: Basic text messages  
**What Doesn't Work**: Interactive messages, media

**Usage**: Only for simple text notifications  
**ETA for Completion**: 2026-01-15

---

## Performance Bottlenecks

### 1. AI Matching for Large Candidate Pools

**Issue**: Matching 1000+ candidates against single job takes 5-10 seconds  
**Location**: `services/agent/app.py` (match endpoint)  
**Impact**: Slow response times for large databases

**Optimization Needed**:
- Implement candidate pre-filtering
- Use batch processing with chunking
- Cache frequent job-candidate pairs
- Add pagination to results

**Priority**: P2  
**Estimated Improvement**: 5-10s → 1-2s

---

### 2. Bulk Import Processing

**Issue**: Importing 500 candidates takes 30-60 seconds  
**Location**: `services/gateway/app/main.py` (bulk endpoint)  
**Impact**: Poor user experience, timeout risks

**Optimization Needed**:
- Parallel processing with thread pool
- Batch database inserts (100 at a time)
- Async processing with job queue
- Progress updates via WebSocket

**Priority**: P2  
**Estimated Improvement**: 30-60s → 5-10s

---

### 3. Dashboard Statistics Queries

**Issue**: Statistics endpoint slow with >10K candidates (2-5s)  
**Location**: `services/gateway/app/main.py` (stats endpoint)  
**Impact**: Slow dashboard load

**Optimization Needed**:
- Add database indexes
- Implement result caching (5 min TTL)
- Use materialized views
- Pre-calculate statistics

**Priority**: P3  
**Estimated Improvement**: 2-5s → 0.1-0.3s

---

## Security Concerns

### SEC-001: Missing API Rate Limiting on Critical Endpoints

**Severity**: High  
**Status**: Partially implemented  
**Risk**: DDoS attacks, resource exhaustion

**Missing Protection**:
- `/health` endpoint (unlimited)
- `/docs` endpoint (unlimited)
- Bulk operations (weak limits)

**Recommendation**:
- Implement Redis-based rate limiting
- Add IP-based blocking
- Set up Cloudflare protection

**Timeline**: Before production scaling  
**Priority**: P1

---

### SEC-002: Weak Password Policy Enforcement

**Severity**: Medium  
**Status**: Active  
**Risk**: Account compromise

**Current Policy**:
- Minimum 8 characters
- No complexity requirements enforced at database level
- No password expiry
- No breach detection

**Recommendation**:
```python
# Enforce strong password policy
PASSWORD_POLICY = {
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True,
    "max_age_days": 90,
    "history_count": 5,
    "check_breach_database": True
}
```

**Timeline**: Q1 2026  
**Priority**: P2

---

### SEC-003: Missing Input Sanitization on File Uploads

**Severity**: High  
**Status**: Not implemented  
**Risk**: Malware uploads, XSS attacks

**Current State**:
- Resume URLs not validated
- No file type checking
- No malware scanning

**Recommendation**:
- Implement file type validation
- Add ClamAV malware scanning
- Sandbox file processing
- Use signed URLs with expiry

**Timeline**: Before enabling file uploads  
**Priority**: P1

---

## Known Limitations

### LIM-001: Maximum 10 Jobs in Batch Matching

**Limitation**: Batch matching endpoint limited to 10 jobs per request  
**Reason**: Performance and timeout constraints  
**Workaround**: Split large batches into multiple requests  
**Future**: Implement async batch processing with job queue

---

### LIM-002: WhatsApp Rate Limit (100 messages/hour)

**Limitation**: Twilio WhatsApp API limits to 100 messages/hour  
**Reason**: External API constraint  
**Workaround**: Queue messages and spread over time  
**Future**: Upgrade to Twilio Business tier (higher limits)

---

### LIM-003: AI Matching Limited to 1000 Candidates

**Limitation**: Phase 3 engine processes max 1000 candidates per job  
**Reason**: Memory and performance constraints  
**Workaround**: Pre-filter candidates before matching  
**Future**: Implement distributed matching with worker pool

---

### LIM-004: No Real-time Collaboration Features

**Limitation**: Multiple HR users can't collaborate on same candidate simultaneously  
**Reason**: Not implemented yet  
**Workaround**: Manual coordination between team members  
**Future**: Implement WebSocket-based real-time updates

---

### LIM-005: Single Database Instance (No Replication)

**Limitation**: No database replication or failover  
**Reason**: Cost optimization for free tier  
**Risk**: Single point of failure  
**Workaround**: Daily backups to S3  
**Future**: Implement MongoDB replica set when scaling

---

## Action Items Summary

### Immediate (P0 - This Week)

| Issue | Owner | Deadline | Status |
|-------|-------|----------|--------|
| ISSUE-001: Connection pool leaks | Backend Team | 2025-12-13 | In Progress |
| ISSUE-002: Fallback matching accuracy | AI Team | 2025-12-15 | Planned |
| ISSUE-003: Notification retry logic | LangGraph Team | 2025-12-12 | In Progress |

### Short Term (P1 - This Month)

| Issue | Owner | Deadline | Status |
|-------|-------|----------|--------|
| ISSUE-004: Rate limiting gaps | Security Team | 2025-12-20 | Planned |
| ISSUE-005: Bulk import transactions | Backend Team | 2025-12-18 | Planned |
| ISSUE-006: Input validation | Security Team | 2025-12-22 | Planned |
| SEC-001: API rate limiting | Security Team | 2025-12-25 | Planned |
| SEC-003: File upload security | Security Team | 2025-12-30 | Planned |

### Medium Term (P2 - Next Quarter)

| Issue | Owner | Deadline | Status |
|-------|-------|----------|--------|
| ISSUE-007: Workflow status updates | LangGraph Team | 2026-01-15 | Backlog |
| ISSUE-008: Fallback logging | AI Team | 2026-01-20 | Backlog |
| Performance optimization | Backend Team | 2026-02-01 | Backlog |
| SEC-002: Password policy | Security Team | 2026-02-15 | Backlog |

### Long Term (P3 - Future)

| Issue | Owner | Deadline | Status |
|-------|-------|----------|--------|
| ISSUE-009: Statistics performance | Backend Team | 2026-03-01 | Backlog |
| Real-time collaboration | Frontend Team | 2026-Q2 | Planned |
| Database replication | Infrastructure | 2026-Q2 | Planned |

---

## Escalation Contacts

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Critical Production Issue | Shashank (System Architect) | Immediate |
| Security Vulnerability | Security Team Lead | 1 hour |
| Database Issues | DBA Team | 2 hours |
| AI/ML Issues | AI Team Lead | 4 hours |
| Infrastructure Issues | DevOps Team | 2 hours |

**Emergency Contact**: [Shashank] - Phone: [REDACTED] - Slack: @shashank-mishra

---

**Last Review Date**: December 9, 2025  
**Next Review Date**: December 23, 2025  
**Document Owner**: Shashank Mishra (System Architect)


# BHIV Core ↔ Bucket: Formal Service Contract

**Parties**: BHIV Core (coordinator system) and BHIV Bucket (storage custodian)  
**Effective Date**: January 26, 2026  
**Validity Period**: 12 months (expires January 26, 2027)  
**Status**: ACTIVE  

---

## SECTION 1: Contract Purpose

This contract defines the ONE AND ONLY allowed relationship between BHIV Core and BHIV Bucket.

**Contract Statement**: "BHIV Core agrees to act exclusively as a coordinator. BHIV Bucket agrees to own all data mutations and provenance decisions."

---

## SECTION 2: Input Channels (What Core May Send)

### Channel A: Artifact Write
**Endpoint**: POST /bucket/artifacts/write

**Allowed Request Body**:
```json
{
  "artifact_id": "string (required)",
  "data": "bytes/string (required)",
  "metadata": {
    "source": "string",
    "created_by": "string",
    "tags": ["array of strings (optional)"]
  },
  "urgency": "normal|high (optional, default: normal)"
}
```

**Constraints**:
- Maximum payload: 50 KB
- Required fields: artifact_id, data, metadata
- Unknown fields: REJECTED
- Rate limit: 50 requests/minute per Core instance
- Allowed urgency values: "normal", "high" only

**Response (Success)**:
```json
{
  "success": true,
  "artifact_id": "string",
  "timestamp": "ISO8601",
  "message": "Artifact written successfully"
}
```

**Response (Failure)**:
```json
{
  "success": false,
  "error": "string",
  "request_id": "string",
  "timestamp": "ISO8601"
}
```

---

### Channel B: Artifact Read
**Endpoint**: POST /bucket/artifacts/read

**Allowed Request Body**:
```json
{
  "artifact_id": "string (required)",
  "include_history": "boolean (optional, default: false)",
  "include_provenance": "boolean (optional, default: false)"
}
```

**Constraints**:
- Maximum payload: 5 KB
- Required fields: artifact_id
- Unknown fields: REJECTED
- Rate limit: 200 requests/minute
- Maximum response size: 100 MB

**Response (Success)**:
```json
{
  "artifact_id": "string",
  "data": "bytes/string",
  "metadata": {},
  "provenance": {
    "created_at": "ISO8601",
    "created_by": "string"
  },
  "timestamp": "ISO8601"
}
```

---

### Channel C: Query/Search
**Endpoint**: POST /bucket/artifacts/query

**Allowed Request Body**:
```json
{
  "query": "string (required)",
  "filters": {
    "tags": ["array of strings (optional)"],
    "created_after": "ISO8601 (optional)",
    "created_before": "ISO8601 (optional)"
  },
  "limit": "integer 1-1000 (optional, default: 100)",
  "offset": "integer >= 0 (optional, default: 0)"
}
```

**Constraints**:
- Maximum payload: 10 KB
- Required fields: query
- Unknown fields: REJECTED
- Rate limit: 100 requests/minute
- Maximum results: 1000 per query

---

### Channel D: Audit Log Read
**Endpoint**: POST /bucket/audit/read

**Allowed Request Body**:
```json
{
  "request_type": "string (required: all|by_user|by_artifact|by_date)",
  "start_time": "ISO8601 (optional)",
  "end_time": "ISO8601 (optional)",
  "limit": "integer 1-10000 (optional, default: 1000)"
}
```

**Constraints**:
- Maximum payload: 5 KB
- Required fields: request_type
- Unknown fields: REJECTED
- Rate limit: 30 requests/minute
- Maximum time range: 365 days

---

### Channel E: Notification Subscribe
**Mechanism**: WebSocket connection  
**URL**: wss://bucket/api/notifications

**Subscribe Request**:
```json
{
  "action": "subscribe",
  "event_types": ["artifact_created", "artifact_accessed", "quota_exceeded"]
}
```

**Event Format (Async)**:
```json
{
  "event_type": "string",
  "timestamp": "ISO8601",
  "artifact_id": "string (if applicable)",
  "data": {}
}
```

**Guarantees**:
- Events delivered in order
- At-least-once semantics (may be duplicated, must deduplicate by timestamp + event_id)
- Reconnection: Client responsible for reconnecting on disconnect

---

## SECTION 3: Output Channels (What Core Receives)

### Response Guarantee 1: Write Confirmation
- Status Code: 200 OK or 201 Created
- Required Fields: success, artifact_id, timestamp
- Maximum Size: 1 KB
- Timing: Within 100ms of write completion

### Response Guarantee 2: Read Response
- Status Code: 200 OK
- Required Fields: artifact_id, data, timestamp
- Maximum Size: 100 MB
- Timing: Within 500ms of request
- No caching: Every read returns current state

### Response Guarantee 3: Query Results
- Status Code: 200 OK
- Required Fields: results, total_count, timestamp
- Maximum Size: 50 MB
- Timing: Within 1 second of query
- Consistency: Snapshot-consistent (point-in-time)

### Response Guarantee 4: Audit Response
- Status Code: 200 OK
- Required Fields: audit_entries, total_entries, timestamp
- Maximum Size: 10 MB
- Timing: Within 1 second
- Guarantee: Complete historical record (nothing hidden)

### Response Guarantee 5: Error Response
- Status Code: 400, 401, 403, 404, 429, or 500
- Required Fields: error, message, request_id, timestamp
- Maximum Size: 2 KB
- Guarantee: Clear, actionable error messages

---

## SECTION 4: Explicit Non-Capabilities

**Core explicitly cannot request these operations:**

### Non-Capability 1: Mutation
- **Core Cannot Request**: "Please modify artifact X to have value Y"
- **Bucket Response**: "Mutation is not an allowed operation"
- **HTTP Code**: 403 Forbidden
- **Why**: Bucket owns all mutations; Core can only write new artifacts

### Non-Capability 2: Deletion
- **Core Cannot Request**: "Please delete artifact X"
- **Bucket Response**: "Deletion is not permitted"
- **HTTP Code**: 403 Forbidden
- **Why**: Provenance requires complete history

### Non-Capability 3: Schema Changes
- **Core Cannot Request**: "Add a new column to the schema"
- **Bucket Response**: "Schema changes are not allowed"
- **HTTP Code**: 403 Forbidden
- **Why**: Schema governance is exclusively Bucket's authority

### Non-Capability 4: Priority Escalation
- **Core Cannot Request**: "Mark this as critical/urgent"
- **Bucket Response**: "Priority decisions require human authorization"
- **HTTP Code**: 403 Forbidden
- **Why**: Only humans decide urgency levels

### Non-Capability 5: Hidden Operations
- **Core Cannot Request**: "Run this check without logging"
- **Bucket Response**: "All operations must be auditable"
- **HTTP Code**: 403 Forbidden
- **Why**: Full auditability is non-negotiable

### Non-Capability 6: Permission Changes
- **Core Cannot Request**: "Grant me admin access"
- **Bucket Response**: "Permissions are fixed at deployment"
- **HTTP Code**: 403 Forbidden
- **Why**: Permissions cannot change at runtime

---

## SECTION 5: No Hidden Read/Write Authority

**Explicit guarantee**: Core has NO hidden channels to Bucket data.

- ✅ All data access goes through documented APIs only
- ✅ No back-channel access permitted
- ✅ No direct database access to Bucket tables
- ✅ No secret bypass mechanisms
- ✅ All operations are logged in audit trail

**Technical Enforcement**:
- Bucket enforces API-only access at the database layer
- Direct table access will be denied (database-level authentication)
- Any unauthorized access attempt triggers security alert

---

## SECTION 6: Failure Scenarios

### Scenario 1: What if Core violates the contract?

**Detection**:
- Boundary enforcer detects violation in middleware layer
- Violation logged with request ID and timestamp
- Pattern analysis initiated (3 similar violations = escalation)

**Immediate Response**:
- Request rejected with 403 Forbidden
- Error message returned to Core
- Audit log entry created

**Escalation** (if pattern detected):
- Alert sent to Bucket Owner
- Service review initiated
- Potential temporary halt of Core requests

**Resolution**:
- Human investigation determines root cause
- Code review of Core system
- If architectural mismatch: formal amendment required
- If bug: Core fixed and re-tested before resuming

### Scenario 2: What if Bucket violates the contract?

**Detection**:
- Core detects unexpected behavior or error
- Audit log shows unauthorized operation
- Monitoring system flags anomaly

**Immediate Response**:
- Core halts interaction with Bucket
- Alert sent to Bucket Owner
- Investigation initiated

**Escalation**:
- All 5 stakeholders notified
- Emergency review meeting
- Potential rollback of recent changes

**Resolution**:
- Root cause analysis
- Code audit of Bucket changes
- Formal review before resuming

---

## SECTION 7: Contract Amendments

**How to change this contract**:

1. **Proposal Phase**: Stakeholder identifies needed change
2. **Review Phase**: All 5 stakeholders review proposed amendment
3. **Approval Phase**: All 5 stakeholders must approve (100% consensus)
4. **Implementation Phase**: Code changes made to reflect new terms
5. **Testing Phase**: Full test suite run to validate new terms
6. **Certification Phase**: All 5 stakeholders sign updated contract
7. **Deployment Phase**: Changes deployed to production

**No unilateral changes allowed**: Both parties must agree.

---

## Stakeholder Sign-Offs

| Party | Role | Sign-Off | Date |
|-------|------|----------|------|
| BHIV Bucket | Ashmit Pandey (Owner) | ✅ Approved | Jan 26, 2026 |
| BHIV Bucket | Nilesh Vishwakarma (Backend) | ⏳ Pending | |
| BHIV Core | Raj Prajapati (Executor) | ⏳ Pending | |
| BHIV Core | Akanksha Parab (Operational) | ⏳ Pending | |
| Strategic | Vijay Dhawan (Governance) | ⏳ Pending | |

---

## Contract History

- **Jan 26, 2026**: Version 1.0 created (ACTIVE status)

---

**Document Version**: 1.0 (ACTIVE)  
**Next Review**: January 26, 2027

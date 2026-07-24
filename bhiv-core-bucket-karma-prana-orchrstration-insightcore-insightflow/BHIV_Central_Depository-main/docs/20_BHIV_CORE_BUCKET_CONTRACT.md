# BHIV Core-Bucket Contract
## Formal Service Contract Between Core and Bucket

**Contract Version**: 1.0  
**Effective Date**: January 28, 2025  
**Parties**: BHIV Core (Client) ↔ BHIV Bucket (Service Provider)  
**Authority**: Ashmit Pandey (Primary Owner)  
**Validity**: 12 months (renewable)

---

## Contract Definition

### Parties

**Party A: BHIV Core**
- Role: AI orchestration and coordination layer
- Responsibilities: Manage agent execution, maintain context, coordinate workflows
- Authority: Read artifacts, submit write requests, receive notifications

**Party B: BHIV Bucket**
- Role: Data custodianship and storage layer
- Responsibilities: Store artifacts, enforce provenance, maintain audit trails
- Authority: Accept/reject writes, enforce retention, manage storage

### Validity
- **Start Date**: January 28, 2025
- **End Date**: January 28, 2026
- **Renewal**: Automatic unless terminated by Owner
- **Termination**: Requires 90-day notice + Owner approval

### Amendment Process
1. Submit formal amendment proposal
2. Advisor reviews for governance impact
3. 30-day comment period
4. Owner approves/rejects
5. Implementation with 60-day transition

---

## Input Channels Core May Send

### Channel 1: artifact_write
**Purpose**: Submit new artifacts for storage

**Schema**:
```json
{
  "channel": "artifact_write",
  "artifact_id": "string (required, unique)",
  "content": "object (required)",
  "metadata": {
    "product": "string (required)",
    "created_by": "string (required)",
    "retention_days": "integer (optional, default: 90)",
    "tags": "array (optional)"
  }
}
```

**Validation Rules**:
- artifact_id must be unique
- product must be one of: ai_assistant, ai_avatar, gurukul, enforcement
- content must be valid JSON
- retention_days must be between 1 and 2555 (7 years)

**Response**:
```json
{
  "status": "success",
  "artifact_id": "artifact_123",
  "stored_at": "2025-01-28T10:30:00Z",
  "retention_until": "2025-04-28T10:30:00Z"
}
```

**Error Response**:
```json
{
  "status": "error",
  "error_code": "DUPLICATE_ARTIFACT_ID",
  "message": "Artifact ID already exists"
}
```

---

### Channel 2: artifact_read
**Purpose**: Retrieve stored artifacts

**Schema**:
```json
{
  "channel": "artifact_read",
  "artifact_id": "string (required)",
  "product": "string (required)"
}
```

**Validation Rules**:
- artifact_id must exist
- product must match artifact's product
- No cross-product reads allowed

**Response**:
```json
{
  "status": "success",
  "artifact_id": "artifact_123",
  "content": {...},
  "metadata": {...},
  "created_at": "2025-01-28T10:30:00Z"
}
```

**Error Response**:
```json
{
  "status": "error",
  "error_code": "ARTIFACT_NOT_FOUND",
  "message": "Artifact does not exist or access denied"
}
```

---

### Channel 3: metadata_query
**Purpose**: Search artifacts by metadata

**Schema**:
```json
{
  "channel": "metadata_query",
  "product": "string (required)",
  "filters": {
    "created_after": "datetime (optional)",
    "created_before": "datetime (optional)",
    "tags": "array (optional)",
    "limit": "integer (optional, default: 100, max: 1000)"
  }
}
```

**Validation Rules**:
- product must be specified (no cross-product queries)
- limit cannot exceed 1000
- Date ranges must be valid

**Response**:
```json
{
  "status": "success",
  "artifacts": [
    {
      "artifact_id": "artifact_123",
      "metadata": {...},
      "created_at": "2025-01-28T10:30:00Z"
    }
  ],
  "total": 42,
  "returned": 100
}
```

---

### Channel 4: audit_append
**Purpose**: Append audit log entries

**Schema**:
```json
{
  "channel": "audit_append",
  "event_type": "string (required)",
  "product": "string (required)",
  "details": "object (required)",
  "severity": "string (optional, default: INFO)"
}
```

**Validation Rules**:
- event_type must be one of: read, write, query, error, escalation
- severity must be one of: INFO, WARNING, ERROR, CRITICAL
- details must be valid JSON

**Response**:
```json
{
  "status": "success",
  "audit_id": "audit_456",
  "logged_at": "2025-01-28T10:30:00Z"
}
```

---

## Output Channels Core May Receive

### Channel 1: write_confirmation
**Purpose**: Confirm successful artifact write

**Schema**:
```json
{
  "channel": "write_confirmation",
  "artifact_id": "string",
  "status": "success",
  "stored_at": "datetime",
  "retention_until": "datetime",
  "storage_location": "string"
}
```

---

### Channel 2: read_response
**Purpose**: Return requested artifact data

**Schema**:
```json
{
  "channel": "read_response",
  "artifact_id": "string",
  "content": "object",
  "metadata": "object",
  "created_at": "datetime",
  "accessed_at": "datetime"
}
```

---

### Channel 3: query_results
**Purpose**: Return query results

**Schema**:
```json
{
  "channel": "query_results",
  "artifacts": "array",
  "total": "integer",
  "returned": "integer",
  "query_time_ms": "integer"
}
```

---

### Channel 4: error_message
**Purpose**: Communicate errors to Core

**Schema**:
```json
{
  "channel": "error_message",
  "error_code": "string",
  "message": "string",
  "details": "object (optional)",
  "retry_after": "integer (optional, seconds)"
}
```

**Error Codes**:
- `DUPLICATE_ARTIFACT_ID`: Artifact ID already exists
- `ARTIFACT_NOT_FOUND`: Artifact does not exist
- `UNAUTHORIZED_ACCESS`: Cross-product access attempt
- `QUOTA_EXCEEDED`: Product storage quota exceeded
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `VALIDATION_FAILED`: Input validation failed
- `GOVERNANCE_VIOLATION`: Request violates governance rules

---

### Channel 5: audit_log
**Purpose**: Provide audit trail entries

**Schema**:
```json
{
  "channel": "audit_log",
  "audit_id": "string",
  "event_type": "string",
  "timestamp": "datetime",
  "product": "string",
  "details": "object"
}
```

---

## Explicit Non-Capabilities

Core **CANNOT** do the following, even if requested:

### 1. Mutate Artifacts ❌
**Request**: `{"action": "update_artifact", "artifact_id": "123", "new_content": {...}}`  
**Response**: `{"error": "IMMUTABLE_ARTIFACT", "message": "Artifacts cannot be modified"}`

### 2. Delete Artifacts ❌
**Request**: `{"action": "delete_artifact", "artifact_id": "123"}`  
**Response**: `{"error": "UNAUTHORIZED_DELETION", "message": "Deletion requires Owner approval"}`

### 3. Change Schema ❌
**Request**: `{"action": "add_field", "field_name": "custom"}`  
**Response**: `{"error": "SCHEMA_LOCKED", "message": "Schema changes require Owner approval"}`

### 4. Bypass Validation ❌
**Request**: `{"action": "write_artifact", "bypass_validation": true}`  
**Response**: `{"error": "VALIDATION_REQUIRED", "message": "Validation cannot be bypassed"}`

### 5. Cross-Product Access ❌
**Request**: `{"action": "read_artifact", "product": "gurukul", "requesting_product": "ai_assistant"}`  
**Response**: `{"error": "UNAUTHORIZED_ACCESS", "message": "Cross-product access denied"}`

### 6. Priority Queue Access ❌
**Request**: `{"action": "write_artifact", "priority": "urgent"}`  
**Response**: `{"error": "NO_PRIORITY_BYPASS", "message": "All requests processed in order"}`

---

## Guarantees & Liabilities

### What Bucket Guarantees

**1. Data Integrity**
- ✅ All writes are atomic
- ✅ No data corruption
- ✅ Checksums validated
- **SLA**: 99.99% integrity

**2. Availability**
- ✅ 99.9% uptime
- ✅ <5 second response time
- ✅ Graceful degradation
- **SLA**: 99.9% availability

**3. Audit Trail**
- ✅ All operations logged
- ✅ Immutable audit logs
- ✅ 7-year retention
- **SLA**: 100% audit coverage

**4. Isolation**
- ✅ Product namespace separation
- ✅ No cross-product leakage
- ✅ Independent quotas
- **SLA**: 100% isolation

**5. Retention**
- ✅ Retention policies enforced
- ✅ Automated cleanup
- ✅ Legal hold support
- **SLA**: 100% compliance

### What Bucket Does NOT Guarantee

**1. Performance Under Abuse**
- ❌ If Core exceeds rate limits, performance may degrade
- **Mitigation**: Rate limiting enforced

**2. Infinite Storage**
- ❌ Storage is limited to 1TB total
- **Mitigation**: Quota enforcement per product

**3. Instant Writes**
- ❌ Writes may be queued during high load
- **Mitigation**: Queue status provided

**4. Backward Compatibility Forever**
- ❌ API may evolve with 90-day deprecation notice
- **Mitigation**: Versioned API endpoints

---

## Failure Handling

### If Core Violates Contract

**Scenario**: Core attempts prohibited action

**Response**:
1. Reject request immediately
2. Log violation with details
3. Return error response
4. Escalate if repeated (>3 violations/hour)

**Example**:
```json
{
  "violation_type": "attempted_mutation",
  "timestamp": "2025-01-28T10:30:00Z",
  "action_taken": "REJECTED",
  "escalation": "ADVISOR_NOTIFIED"
}
```

### If Bucket Violates Contract

**Scenario**: Bucket fails to provide guaranteed service

**Response**:
1. Core logs service failure
2. Core escalates to Executor
3. Executor investigates root cause
4. Owner decides on remediation

**Example**:
```json
{
  "service_failure": "write_timeout",
  "timestamp": "2025-01-28T10:30:00Z",
  "sla_violated": "5_second_response_time",
  "escalation": "EXECUTOR_NOTIFIED"
}
```

---

## API Reference

### Endpoint 1: Write Artifact
```
POST /bucket/artifact/write
Content-Type: application/json

{
  "artifact_id": "artifact_123",
  "content": {...},
  "metadata": {
    "product": "ai_assistant",
    "created_by": "core",
    "retention_days": 90
  }
}

Response 200:
{
  "status": "success",
  "artifact_id": "artifact_123",
  "stored_at": "2025-01-28T10:30:00Z"
}
```

### Endpoint 2: Read Artifact
```
GET /bucket/artifact/read?artifact_id=artifact_123&product=ai_assistant

Response 200:
{
  "status": "success",
  "artifact_id": "artifact_123",
  "content": {...},
  "metadata": {...}
}
```

### Endpoint 3: Query Metadata
```
POST /bucket/artifact/query
Content-Type: application/json

{
  "product": "ai_assistant",
  "filters": {
    "created_after": "2025-01-01T00:00:00Z",
    "limit": 100
  }
}

Response 200:
{
  "status": "success",
  "artifacts": [...],
  "total": 42
}
```

### Endpoint 4: Append Audit Log
```
POST /bucket/audit/append
Content-Type: application/json

{
  "event_type": "read",
  "product": "ai_assistant",
  "details": {...}
}

Response 200:
{
  "status": "success",
  "audit_id": "audit_456"
}
```

---

## Sign-Offs

**Primary Owner (Contract Authority)**  
Ashmit Pandey - _________________ Date: _______

**Strategic Advisor (Governance Authority)**  
Vijay Dhawan - _________________ Date: _______

**Executor (Operational Authority)**  
Akanksha Parab - _________________ Date: _______

**Backend Lead (Technical Authority)**  
Nilesh Vishwakarma - _________________ Date: _______

---

## Contract Statement

**"This contract defines the formal service relationship between BHIV Core and BHIV Bucket. All interactions must conform to documented input/output channels. Violations will be rejected and escalated."**

---

**Contract Status**: ACTIVE  
**Next Review**: January 28, 2026  
**Modification Requires**: Owner approval + 30-day notice

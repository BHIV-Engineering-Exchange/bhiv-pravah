# Core Violation Handling: What Happens When Core Breaks the Contract

**Purpose**: Document detection, response, and escalation for Core violations.

**Status**: ACTIVE  
**Date**: January 26, 2026  

---

## SECTION 1: Violation Detection

### How Bucket Detects Violations

**Layer 1: API Validation** (Immediate, <1ms)
- Endpoint whitelist check
- Method validation (POST vs GET, etc.)
- Payload structure validation
- Unknown field detection

**Layer 2: Contract Validation** (Immediate, <5ms)
- Required field presence
- Payload size limits
- Rate limit checking
- Type validation

**Layer 3: Boundary Enforcement** (Immediate, <10ms)
- Forbidden operation detection
- Mutation attempt detection
- Schema change detection
- Provenance tampering detection

**Layer 4: Pattern Analysis** (Continuous)
- Violation frequency tracking
- Endpoint targeting patterns
- Timing analysis (clustered vs spread)
- Behavioral anomalies

**Layer 5: Escalation Thresholds** (Real-time)
- Critical violations: Immediate
- 5+ high violations in 1 hour: Escalate
- Same endpoint 10+ times: Escalate
- 3+ mutation attempts: Escalate

---

## SECTION 2: Violation Types

### Type A: Unauthorized Endpoint Access
- **What Core tried**: Accessing /bucket/schema/migrate
- **Detection**: API validation layer
- **Response**: 403 Forbidden
- **Escalation**: No (single violation is benign)

**Example Log Entry**:
```json
{
  "timestamp": "2026-01-26T14:30:00Z",
  "violation_type": "unauthorized_endpoint",
  "severity": "low",
  "request_id": "req-abc123",
  "endpoint": "/bucket/schema/migrate",
  "reason": "Endpoint not in allowed list",
  "escalated": false
}
```

### Type B: Forbidden Operation
- **What Core tried**: Including "mutate" keyword in payload
- **Detection**: Boundary enforcer
- **Response**: 403 Forbidden
- **Escalation**: If repeated (3+), escalate

**Example**:
```json
{
  "timestamp": "2026-01-26T14:32:00Z",
  "violation_type": "forbidden_operation",
  "severity": "high",
  "request_id": "req-def456",
  "endpoint": "/bucket/artifacts/write",
  "reason": "Payload contains forbidden keyword: 'mutate'",
  "escalated": false
}
```

### Type C: Payload Exceeds Limit
- **What Core tried**: Sending 100KB artifact (limit: 50KB)
- **Detection**: Payload validation layer
- **Response**: 413 Payload Too Large
- **Escalation**: No (accidental, not malicious)

### Type D: Missing Required Field
- **What Core tried**: POST without "artifact_id" field
- **Detection**: Contract validation layer
- **Response**: 400 Bad Request
- **Escalation**: No (likely a bug, not malicious)

### Type E: Mutation Attempt
- **What Core tried**: Request with operation: "update"
- **Detection**: Forbidden operation detection
- **Response**: 403 Forbidden
- **Escalation**: Yes if repeated (3+ in 60 min)

**Example**:
```json
{
  "timestamp": "2026-01-26T14:40:00Z",
  "violation_type": "mutation_attempt",
  "severity": "high",
  "request_id": "req-mno345",
  "endpoint": "/bucket/artifacts/write",
  "reason": "Mutation attempts violate Core contract",
  "escalated": false
}
```

### Type F: Schema Change Attempt
- **What Core tried**: POST /bucket/schema/alter
- **Detection**: API validation + boundary check
- **Response**: 403 Forbidden
- **Escalation**: Yes (always, first attempt)

**Example**:
```json
{
  "timestamp": "2026-01-26T14:42:00Z",
  "violation_type": "schema_change_attempt",
  "severity": "critical",
  "request_id": "req-pqr678",
  "endpoint": "/bucket/schema/alter",
  "reason": "Core attempted schema modification (prohibited)",
  "escalated": true
}
```

### Type G: Provenance Tampering
- **What Core tried**: Request to modify artifact history
- **Detection**: Boundary enforcement
- **Response**: 403 Forbidden
- **Escalation**: Yes (always, critical)

**Example**:
```json
{
  "timestamp": "2026-01-26T14:45:00Z",
  "violation_type": "provenance_rewrite_attempt",
  "severity": "critical",
  "request_id": "req-stu901",
  "endpoint": "/bucket/provenance/update",
  "reason": "Core attempted to modify provenance (forbidden)",
  "escalated": true
}
```

### Type H: Rate Limit Exceeded
- **What Core tried**: 200 requests in 1 minute (limit: 100)
- **Detection**: Rate limit checker
- **Response**: 429 Too Many Requests
- **Escalation**: No (if single source), Yes (if coordinated pattern)

---

## SECTION 3: Immediate Response (What Bucket Does)

### Step 1: Request Rejection

**HTTP 403 Forbidden**:
```json
{
  "error": "Constitutional Violation Detected",
  "error_code": "mutation_attempt",
  "message": "Core attempted prohibited mutation operation",
  "request_id": "req-mno345",
  "timestamp": "2026-01-26T14:40:05Z",
  "action": "Request rejected. Violation logged and tracked.",
  "support_contact": "core-support@bhiv.ai"
}
```

### Step 2: Violation Logging
```json
{
  "timestamp": "2026-01-26T14:40:05Z",
  "request_id": "req-mno345",
  "violation_type": "mutation_attempt",
  "severity": "high",
  "endpoint": "/bucket/artifacts/write",
  "reason": "Mutation attempts violate Core contract",
  "logged_by": "core_boundary_enforcer.py",
  "audit_entry": true,
  "escalation_ready": false
}
```

### Step 3: Pattern Tracking

**Violation Pattern Analysis (Last 60 minutes)**:
- Total violations: 2
- High severity: 2
- Mutation attempts: 2
- Same endpoint: 2
- Threshold for escalation: 3 mutations
- Status: BEING TRACKED (1 more = escalate)

---

## SECTION 4: Escalation (What Happens Next)

### Escalation Trigger #1: Critical Violation

**IMMEDIATE ESCALATION**

- **Violation Type**: schema_change_attempt
- **Severity**: CRITICAL
- **Reason**: Core attempted schema modification

**Who is notified**:
- Ashmit Pandey (Bucket Owner) - IMMEDIATE
- Vijay Dhawan (Strategic Advisor) - IMMEDIATE
- Nilesh Vishwakarma (Backend) - IMMEDIATE

**Notification Content**:
- Violation details
- Request ID
- Timestamp
- Recommended actions
- Audit log excerpt

**Action Required**: YES  
**Urgency**: CRITICAL  
**Timeline**: Respond within 1 hour

### Escalation Trigger #2: Pattern Detection

**ESCALATION ON PATTERN**

- **Pattern Detected**: 3 mutation attempts in 45 minutes
- **Severity**: HIGH
- **Risk Level**: Potential coordinated attack

**Who is notified**:
- Ashmit Pandey (Bucket Owner)
- Raj Prajapati (Executor/Workflow)
- Akanksha Parab (Operations)

**Escalation Threshold**:
- ✅ Reached: 3 mutations (threshold met)
- Scope: Last 60 minutes
- Pattern Type: Repeated endpoint targeting

**Action Required**: YES  
**Urgency**: HIGH  
**Timeline**: Respond within 4 hours

### Escalation Trigger #3: Rate Limit Abuse

**ESCALATION ON ABUSE**

- **Pattern Detected**: 10 violations on same endpoint in 30 minutes
- **Severity**: MEDIUM
- **Risk Level**: Potential DoS or system probe

**Who is notified**:
- Akanksha Parab (Operations)
- Nilesh Vishwakarma (Backend)

**Investigation Checklist**:
- [ ] Is this Core version mismatch?
- [ ] Is this a bug in Core (retry loop)?
- [ ] Is this an intentional probe?
- [ ] Is Core under attack / compromised?

**Action Required**: YES  
**Urgency**: MEDIUM  
**Timeline**: Investigate within 8 hours

---

## SECTION 5: Failure Scenarios

### Scenario 1: Accidental Bug in Core

**What Happened**:
- Core v2.1 has a retry loop bug causing 5 mutation attempts

**Detection**:
- Violation 1: Logged
- Violation 2: Logged
- Violation 3: Pattern detected → Escalate

**Escalation**:
- Bucket Owner notified
- Core team contacted
- Root cause: Retry loop in error handler

**Resolution**:
- Core v2.1 patched (retry fixed)
- Core redeployed
- Escalation cleared
- No Bucket changes needed

### Scenario 2: Architectural Mismatch

**What Happened**:
- New Core feature assumes mutation capability
- Core sends mutation request
- Bucket rejects it

**Detection**:
- Violation: Mutation attempt
- Severity: HIGH
- Escalation: YES

**Root Cause**:
- Core team misunderstood contract
- Expected mutation to be allowed
- Implemented feature assuming it

**Resolution**:
- Formal review meeting (all 5 stakeholders)
- Decision: Bucket adds limited mutation capability OR
- Decision: Core redesigns feature to not need mutations
- Contract amended if needed
- Both teams agree on solution

### Scenario 3: Attempted Security Breach

**What Happened**:
- External attacker compromises Core
- Attempts to delete all Bucket artifacts

**Detection**:
- Violation: Deletion attempt
- Severity: CRITICAL
- Escalation: IMMEDIATE

**Response**:
- Bucket Owner notified (URGENT)
- All stakeholders alerted
- Investigation initiated
- Bucket operations continue (unaffected)
- Core isolation considered

**Actions**:
- Audit trail examined (full history available)
- No artifacts deleted (Bucket refused)
- Core compromise identified
- Core redeployed from clean backup
- Security review conducted

---

## SECTION 6: Governance Reinforcement

### Post-Violation Actions

**For Accidental Violations** (bugs, misunderstandings):
1. Root cause analysis
2. Core code review
3. Test case added to prevent regression
4. Team training if needed
5. Resume normal operation

**For Architectural Mismatches**:
1. Formal design review
2. All 5 stakeholders participate
3. Contract amendment if needed
4. Code changes by both teams
5. Full integration testing
6. Resume operation with new agreement

**For Security Incidents**:
1. Incident investigation
2. Security audit
3. Compromise assessment
4. System hardening
5. Monitoring enhanced
6. Post-incident review

---

## SECTION 7: Monitoring & Prevention

### Continuous Monitoring

**Metrics to Track**:
- Violation frequency (target: 0/month)
- Escalation frequency (target: 0/month)
- Violation types (early warning signs)
- Rate limit hits (sign of issues)
- Endpoint access patterns (anomaly detection)

### Prevention Measures

**For Core Team**:
- Test suite validates contract compliance
- Contract validation happens in CI/CD
- Deployment blocked if violations detected
- Code reviews check boundary compliance
- Runtime validation is final safety net

**For Bucket Team**:
- Boundary enforcement cannot be disabled
- Violations automatically escalated
- Audit trail is immutable
- Monitoring is 24/7
- Response procedures are documented

---

## SECTION 8: Escalation Contact Tree

| Level | Time | Who | Email | Phone |
|-------|------|-----|-------|-------|
| L1 Immediate | Now | Ashmit Pandey | ashmit@bhiv.ai | 📞 |
| L1 Immediate | Now | Vijay Dhawan | vijay@bhiv.ai | 📞 |
| L2 (30min) | +30m | Nilesh Vishwakarma | nilesh@bhiv.ai | 📞 |
| L2 (30min) | +30min | Raj Prajapati | raj@bhiv.ai | 📞 |
| L3 (1hr) | +1h | Security Team | security@bhiv.ai | 📞 |

**Protocol**: Start at L1, add L2 if no response within 30 minutes.

---

**Document Version**: 1.0 (ACTIVE)  
**Next Review**: January 26, 2027

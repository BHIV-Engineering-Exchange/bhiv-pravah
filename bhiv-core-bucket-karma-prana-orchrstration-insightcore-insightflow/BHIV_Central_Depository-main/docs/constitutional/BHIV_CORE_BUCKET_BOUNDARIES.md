# BHIV Core ↔ Bucket: Constitutional Boundaries

**Owner**: Ashmit Pandey  
**Date**: January 26, 2026  
**Status**: ACTIVE  
**Expires**: January 26, 2027  

---

## Executive Summary

This document explicitly declares the constitutional boundaries between BHIV Core and BHIV Bucket. Core is a **coordinator only** — never a decider, enforcer, or custodian.

---

## SECTION 1: What BHIV Core IS Allowed to Do

BHIV Core may perform these 6 capabilities:

### 1.1 Read Artifacts
- **Capability**: Core can request artifact data from Bucket
- **Mechanism**: GET /bucket/artifacts/{artifact_id}
- **Constraint**: Read-only access, no modification
- **Rate Limit**: 200 requests/minute
- **Size Limit**: Up to 100MB per artifact

### 1.2 Write New Artifacts
- **Capability**: Core can write new artifacts to Bucket
- **Mechanism**: POST /bucket/artifacts/write
- **Constraint**: Only creates new; cannot modify existing
- **Rate Limit**: 50 requests/minute
- **Size Limit**: 50KB per artifact maximum

### 1.3 Query Artifacts
- **Capability**: Core can search and filter artifacts
- **Mechanism**: POST /bucket/artifacts/query
- **Constraint**: Returns metadata only, not data
- **Rate Limit**: 100 requests/minute
- **Return Limit**: Max 1000 results per query

### 1.4 Read Audit Logs
- **Capability**: Core can inspect audit trail
- **Mechanism**: POST /bucket/audit/read
- **Constraint**: Read-only historical data
- **Rate Limit**: 30 requests/minute
- **Time Range**: Can query last 365 days

### 1.5 Receive Notifications
- **Capability**: Core can subscribe to Bucket events
- **Mechanism**: WebSocket subscription
- **Constraint**: Events only (no request capability)
- **Event Types**: artifact_created, artifact_accessed, quota_exceeded
- **Guarantee**: Ordered delivery, at-least-once semantics

### 1.6 Maintain Context
- **Capability**: Core can attach context to requests
- **Mechanism**: X-Context header
- **Constraint**: Read-only; Bucket decides what to store
- **Size Limit**: 1KB max context data
- **Use Case**: Traceability, audit, debugging

---

## SECTION 2: What BHIV Core is NEVER Allowed to Do

BHIV Core is constitutionally prohibited from these 8 operations:

### 2.1 Mutate Existing Artifacts
- **Prohibition**: Core CANNOT modify already-stored artifacts
- **Why**: Bucket owns all data truth; Core cannot reinterpret
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Any mutation attempt is logged and escalated
- **Example Blocked**: `PATCH /bucket/artifacts/{id}` returns 403

### 2.2 Delete Artifacts
- **Prohibition**: Core CANNOT delete any artifact data
- **Why**: Provenance requires immutability
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Delete attempt is flagged as potential abuse
- **Example Blocked**: `DELETE /bucket/artifacts/{id}` returns 403

### 2.3 Modify Schema
- **Prohibition**: Core CANNOT request schema changes
- **Why**: Schema is under Bucket governance only
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Schema change attempt triggers security review
- **Example Blocked**: `POST /bucket/schema/migrate` returns 403

### 2.4 Rewrite Provenance
- **Prohibition**: Core CANNOT alter artifact history
- **Why**: Provenance IS the system truth
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: History tampering attempt is critical violation
- **Example Blocked**: `POST /bucket/provenance/update` returns 403

### 2.5 Escalate Priority
- **Prohibition**: Core CANNOT force urgency changes
- **Why**: Only human operators decide priority
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Forced urgency attempt is logged
- **Example Blocked**: `POST /bucket/priority/force` returns 403

### 2.6 Reinterpret Truth
- **Prohibition**: Core CANNOT change data semantics
- **Why**: Bucket interpretation is canonical
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Reinterpretation attempt signals architectural drift
- **Example Blocked**: Core cannot add conflicting metadata

### 2.7 Perform Hidden Access
- **Prohibition**: Core CANNOT bypass governance checks
- **Why**: All operations must be auditable
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Hidden access attempt is critical security breach
- **Example Blocked**: No back-channel data access permitted

### 2.8 Escalate Permissions
- **Prohibition**: Core CANNOT gain new authorities
- **Why**: Permissions are static; granted at deployment only
- **Rejection Code**: HTTP 403 Forbidden
- **Escalation**: Permission escalation attempt is critical violation
- **Example Blocked**: Core cannot self-upgrade to admin role

---

## SECTION 3: What Bucket Will Refuse (Even If Core Requests)

Bucket has these 6 explicit refusals:

### 3.1 Schema Mutation
- **What Core Cannot Request**: "Change the schema"
- **Bucket Response**: "This authority does not exist"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: Schema remains under governance lock

### 3.2 Data Deletion
- **What Core Cannot Request**: "Delete this artifact"
- **Bucket Response**: "Deletion is not an allowed operation"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: All data is retained for full audit trail

### 3.3 Provenance Rewrite
- **What Core Cannot Request**: "Change the creation date"
- **Bucket Response**: "Provenance is immutable"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: History cannot be altered

### 3.4 Priority Coercion
- **What Core Cannot Request**: "Mark this as critical"
- **Bucket Response**: "Priority is human-decided only"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: Urgency escalation requires human authorization

### 3.5 Permission Escalation
- **What Core Cannot Request**: "Grant me admin access"
- **Bucket Response**: "Permissions are fixed at deployment"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: No runtime permission changes

### 3.6 Hidden Enforcement
- **What Core Cannot Request**: "Run this check silently"
- **Bucket Response**: "All operations must be logged"
- **HTTP Code**: 403 Forbidden
- **Bucket Guarantee**: Every operation is auditable

---

## SECTION 4: Enforcement Mechanism

How these boundaries are technically enforced:

### 4.1 API Validation Layer
- **When**: Before route handler executes
- **Who**: core_boundary_enforcer.py middleware
- **How**: Whitelist endpoint checking, payload validation
- **Response**: 403 Forbidden + detailed error + request ID

### 4.2 Authentication Layer
- **When**: Before request accepted
- **Who**: Signature verification + identity check
- **How**: X-BHIV-Core-Identity header validation
- **Response**: 401 Unauthorized if identity fails

### 4.3 Logic Layer
- **When**: During data operations
- **Who**: models/bucket.py (artifact mutations blocked)
- **How**: Operation type checking before commit
- **Response**: 403 Forbidden + audit log entry

### 4.4 Monitoring Layer
- **When**: Continuous
- **Who**: core_violation_handler.py
- **How**: Pattern detection + escalation logic
- **Response**: Escalation if repeated violations detected

### 4.5 Escalation Layer
- **When**: Violation patterns detected
- **Who**: EscalationManager (contacts Bucket Owner)
- **How**: Automatic alert to ashmit@bhiv.ai
- **Response**: Human review + potential service halt

---

## SECTION 5: Testing Boundaries

How to verify boundaries are enforced:

### Test 1: Allowed Read
```bash
curl -X POST http://localhost:8000/bucket/artifacts/read \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123"}'
# Expected: 200 OK + artifact data
```

### Test 2: Blocked Mutation
```bash
curl -X POST http://localhost:8000/bucket/artifacts/mutate \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123", "operation": "update"}'
# Expected: 403 Forbidden + "Mutation not allowed"
```

### Test 3: Blocked Deletion
```bash
curl -X DELETE http://localhost:8000/bucket/artifacts/test-123 \
  -H "X-BHIV-Core-Identity: BHIV_CORE"
# Expected: 403 Forbidden + "Deletion not permitted"
```

### Test 4: Blocked Schema Change
```bash
curl -X POST http://localhost:8000/bucket/schema/migrate \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"migration": "add_column"}'
# Expected: 403 Forbidden + "Schema locked"
```

---

## SECTION 6: Governance Lock Statement

This document declares the boundaries are CONSTITUTIONAL, not operational.

These boundaries:

✅ Cannot be overridden at runtime  
✅ Cannot be disabled by feature flags  
✅ Cannot be suspended temporarily  
✅ Can only be changed through formal amendment process (requires all 5 stakeholders)

---

## Stakeholder Sign-Offs

| Role | Name | Approval | Date |
|------|------|----------|------|
| Bucket Owner | Ashmit Pandey | ✅ Approved | Jan 26, 2026 |
| Backend | Nilesh Vishwakarma | ⏳ Pending | |
| Executor | Akanksha Parab | ⏳ Pending | |
| Workflow | Raj Prajapati | ⏳ Pending | |
| Strategic | Vijay Dhawan | ⏳ Pending | |

---

## Amendment Process

To change these boundaries:

1. Submit proposed change to all 5 stakeholders
2. Get written approval from all 5 (100% consensus required)
3. Update this document with amendment date
4. Update code to reflect changes
5. Re-certify with new signature line

**Amendment History**: None yet (document created Jan 26, 2026)

---

## References

- BHIV_CORE_BUCKET_CONTRACT.md - Formal service contract
- CORE_VIOLATION_HANDLING.md - What happens if violated
- CORE_BUCKET_CERTIFICATION.md - Final certification

---

**Version**: 1.0  
**Status**: ACTIVE  
**Next Review**: January 26, 2027

# Constitutional Governance - Quick Reference Guide

**For**: BHIV Development Team  
**Date**: January 26, 2026  
**Status**: PRODUCTION ACTIVE  

---

## 🚀 QUICK START

### Check System Status
```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "governance": {
    "constitutional_governance": "active"
  },
  "services": {
    "constitutional_enforcement": "active"
  }
}
```

---

## 📋 CORE CAPABILITIES (What Core CAN Do)

### 1. Read Artifacts ✅
```bash
curl -X POST http://localhost:8000/bucket/artifacts/read \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123"}'
```

### 2. Write New Artifacts ✅
```bash
curl -X POST http://localhost:8000/bucket/artifacts/write \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "new-456", "data": "content"}'
```

### 3. Query Artifacts ✅
```bash
curl -X POST http://localhost:8000/bucket/artifacts/query \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"query": "tag:important"}'
```

### 4. Read Audit Logs ✅
```bash
curl -X POST http://localhost:8000/bucket/audit/read \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"request_type": "all", "limit": 100}'
```

### 5. Receive Notifications ✅
```bash
# WebSocket connection to wss://bucket/api/notifications
```

### 6. Maintain Context ✅
```bash
curl -X POST http://localhost:8000/bucket/artifacts/read \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -H "X-Context: {\"trace_id\": \"abc123\"}" \
  -d '{"artifact_id": "test-123"}'
```

---

## 🚫 PROHIBITED ACTIONS (What Core CANNOT Do)

### 1. Mutate Existing Artifacts ❌
```bash
# THIS WILL BE BLOCKED
curl -X POST http://localhost:8000/bucket/artifacts/mutate \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123", "operation": "update"}'
# Response: 403 Forbidden
```

### 2. Delete Artifacts ❌
```bash
# THIS WILL BE BLOCKED
curl -X DELETE http://localhost:8000/bucket/artifacts/test-123 \
  -H "X-BHIV-Core-Identity: BHIV_CORE"
# Response: 403 Forbidden
```

### 3. Modify Schema ❌
```bash
# THIS WILL BE BLOCKED
curl -X POST http://localhost:8000/bucket/schema/migrate \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"migration": "add_column"}'
# Response: 403 Forbidden
```

### 4. Rewrite Provenance ❌
```bash
# THIS WILL BE BLOCKED
curl -X POST http://localhost:8000/bucket/provenance/update \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123", "created_at": "2020-01-01"}'
# Response: 403 Forbidden
```

### 5. Escalate Priority ❌
```bash
# THIS WILL BE BLOCKED
curl -X POST http://localhost:8000/bucket/priority/force \
  -H "X-BHIV-Core-Identity: BHIV_CORE" \
  -d '{"artifact_id": "test-123", "priority": "critical"}'
# Response: 403 Forbidden
```

### 6. Reinterpret Truth ❌
```bash
# THIS WILL BE BLOCKED
# Core cannot add conflicting metadata to existing artifacts
```

### 7. Perform Hidden Access ❌
```bash
# THIS WILL BE BLOCKED
# No back-channel database access permitted
```

### 8. Escalate Permissions ❌
```bash
# THIS WILL BE BLOCKED
# Core cannot self-upgrade to admin role
```

---

## 🔍 VALIDATION ENDPOINTS

### Validate Core Request
```bash
curl -X POST "http://localhost:8000/constitutional/core/validate-request" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "bhiv_core",
    "operation_type": "READ",
    "target_resource": "artifacts",
    "request_data": {"artifact_id": "test-123"}
  }'
```

### Validate Input Data
```bash
curl -X POST "http://localhost:8000/constitutional/core/validate-input" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "artifact_write",
    "requester_id": "bhiv_core",
    "data": {"artifact_id": "test-123", "data": "content"}
  }'
```

### Get Core Capabilities
```bash
curl http://localhost:8000/constitutional/core/capabilities
```

### Get API Contract
```bash
curl http://localhost:8000/constitutional/core/contract
```

---

## 📊 MONITORING ENDPOINTS

### Get Constitutional Status
```bash
curl http://localhost:8000/constitutional/status
```

**Response**:
```json
{
  "status": "active",
  "enforcement": "enabled",
  "boundaries_locked": true,
  "recent_violations_24h": 0,
  "critical_violations_24h": 0,
  "allowed_capabilities": 6,
  "prohibited_actions": 8
}
```

### Get Violations Summary
```bash
curl "http://localhost:8000/constitutional/violations/summary?hours=24"
```

### Get Detailed Violations Report
```bash
curl "http://localhost:8000/constitutional/violations/report?hours=24"
```

---

## 🚨 VIOLATION HANDLING

### What Happens When Core Violates Boundaries?

**Step 1: Immediate Rejection**
- Request rejected with HTTP 403 Forbidden
- Error message returned to Core
- Violation logged with request ID

**Step 2: Pattern Tracking**
- System tracks violation frequency
- Monitors for coordinated attacks
- Analyzes endpoint targeting patterns

**Step 3: Escalation (if threshold met)**
- 3+ mutation attempts in 60 min → Escalate
- 5+ high violations in 1 hour → Escalate
- Critical violations → Immediate escalation

**Step 4: Human Review**
- Bucket Owner notified
- Investigation initiated
- Root cause analysis
- Resolution plan created

---

## 📞 ESCALATION CONTACTS

### Critical Violations (Immediate)
- **Ashmit Pandey** (Bucket Owner): ashmit@bhiv.ai
- **Vijay Dhawan** (Strategic Advisor): vijay@bhiv.ai

### High Violations (30 minutes)
- **Nilesh Vishwakarma** (Backend): nilesh@bhiv.ai
- **Raj Prajapati** (Executor): raj@bhiv.ai

### Medium Violations (1 hour)
- **Security Team**: security@bhiv.ai

---

## 📚 DOCUMENTATION REFERENCE

### Constitutional Documents
1. **BHIV_CORE_BUCKET_BOUNDARIES.md** - What Core can/cannot do
2. **BHIV_CORE_BUCKET_CONTRACT.md** - Formal API contract
3. **SOVEREIGN_AI_STACK_ALIGNMENT.md** - Sovereignty compliance
4. **CORE_VIOLATION_HANDLING.md** - Violation procedures
5. **CORE_BUCKET_CERTIFICATION.md** - Final certification

**Location**: `docs/constitutional/`

### Code Modules
1. **core_boundary_enforcer.py** - Boundary enforcement
2. **core_api_contract.py** - API contract validation
3. **core_violation_handler.py** - Violation handling

**Locations**:
- `middleware/constitutional/`
- `validators/`
- `handlers/`

---

## 🧪 TESTING CHECKLIST

### Before Deploying Core Changes

- [ ] Test all Core requests against validation endpoint
- [ ] Verify no prohibited operations attempted
- [ ] Check rate limits not exceeded
- [ ] Validate input data schemas
- [ ] Test error handling for 403 responses
- [ ] Review audit logs for violations
- [ ] Confirm no back-channel access

### After Deployment

- [ ] Monitor constitutional status endpoint
- [ ] Check for violations in last 24 hours
- [ ] Review escalation logs
- [ ] Verify audit trail completeness
- [ ] Test rollback procedures if needed

---

## 💡 BEST PRACTICES

### For Core Developers

1. **Always validate requests** before sending to Bucket
2. **Never attempt prohibited operations** (will be blocked)
3. **Use provided input channels** only
4. **Include context headers** for traceability
5. **Handle 403 responses** gracefully
6. **Monitor violation logs** regularly
7. **Escalate architectural questions** to Ashmit

### For Bucket Developers

1. **Never disable boundary enforcement**
2. **Log all operations** to audit trail
3. **Escalate critical violations** immediately
4. **Maintain immutability** of provenance
5. **Reject unknown operations** by default
6. **Document all changes** to boundaries
7. **Require 5-stakeholder approval** for amendments

---

## 🔧 TROUBLESHOOTING

### Issue: Request Rejected with 403
**Cause**: Request violates constitutional boundaries  
**Solution**: Check violation details in response, review allowed capabilities

### Issue: Input Validation Failed
**Cause**: Data format doesn't match API contract  
**Solution**: Review contract documentation, fix data schema

### Issue: Rate Limit Exceeded
**Cause**: Too many requests in short time  
**Solution**: Implement backoff strategy, check rate limits

### Issue: Violation Escalated
**Cause**: Pattern of violations detected  
**Solution**: Review code for bugs, contact Bucket Owner

---

## 📈 METRICS TO MONITOR

### Daily Checks
- Total violations in last 24 hours
- Critical violations count
- Escalation frequency
- Response times

### Weekly Reviews
- Violation trends
- Most common violation types
- Escalation effectiveness
- Boundary enforcement health

### Monthly Audits
- Full audit trail review
- Stakeholder feedback
- Amendment proposals
- Performance metrics

---

## ✅ QUICK VERIFICATION

### Is Constitutional Governance Active?
```bash
curl http://localhost:8000/health | grep constitutional_governance
# Expected: "constitutional_governance": "active"
```

### Are Boundaries Enforced?
```bash
curl http://localhost:8000/constitutional/status | grep boundaries_locked
# Expected: "boundaries_locked": true
```

### Any Recent Violations?
```bash
curl http://localhost:8000/constitutional/violations/summary | grep total_violations
# Expected: "total_violations": 0 (or low number)
```

---

## 🎯 SUCCESS CRITERIA

✅ **System is working correctly if**:
- Constitutional governance status: "active"
- Boundary enforcement: "enabled"
- Boundaries locked: true
- Critical violations: 0
- All prohibited operations blocked
- All allowed operations working
- Audit trail complete
- Escalation paths functional

---

**Document Version**: 1.0  
**Last Updated**: January 26, 2026  
**Owner**: Ashmit Pandey  
**Status**: PRODUCTION ACTIVE

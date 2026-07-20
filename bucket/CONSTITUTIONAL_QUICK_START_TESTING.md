# QUICK START GUIDE - Constitutional Governance Testing
## Test Your Implementation in 5 Minutes

**Date**: January 26, 2025  
**Status**: Ready for Testing

---

## ⚡ IMMEDIATE TESTING (5 Minutes)

### Step 1: Start the Server (30 seconds)

```bash
cd BHIV_Central_Depository-main
python main.py
```

**Expected Output**:
```
INFO: Connected to Redis at localhost:6379
INFO: Successfully connected to MongoDB
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### Step 2: Test Health Check (10 seconds)

```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "bucket_version": "1.0.0",
  "governance": {
    "gate_active": true,
    "constitutional_governance": "active"
  },
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "constitutional_enforcement": "active"
  }
}
```

✅ **Success Indicator**: Look for `"constitutional_governance": "active"`

---

### Step 3: Test Core Capabilities (30 seconds)

```bash
curl http://localhost:8000/constitutional/core/capabilities
```

**Expected Response**:
```json
{
  "allowed_capabilities": [
    "READ",
    "WRITE",
    "QUERY",
    "AUDIT",
    "RETENTION",
    "VERIFY"
  ],
  "prohibited_actions": [
    "MUTATE",
    "DELETE",
    "SCHEMA_CHANGE",
    "PRIORITY_OVERRIDE",
    "HIDDEN_ACCESS",
    "EXECUTOR_CONTROL",
    "BEHAVIORAL_PRESSURE",
    "DECISION_AUTHORITY"
  ],
  "enforcement": "automatic",
  "reference": "docs/constitutional/BHIV_CORE_BUCKET_BOUNDARIES.md"
}
```

✅ **Success Indicator**: 6 allowed capabilities, 8 prohibited actions

---

### Step 4: Test Allowed Operation (30 seconds)

```bash
curl -X POST "http://localhost:8000/constitutional/core/validate-request" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "bhiv_core",
    "operation_type": "READ",
    "target_resource": "artifact_123",
    "request_data": {"artifact_id": "artifact_123"}
  }'
```

**Expected Response**:
```json
{
  "allowed": true,
  "message": "Request validated successfully",
  "validation_result": {
    "allowed": true,
    "violations": []
  }
}
```

✅ **Success Indicator**: `"allowed": true`

---

### Step 5: Test Prohibited Operation (30 seconds)

```bash
curl -X POST "http://localhost:8000/constitutional/core/validate-request" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "bhiv_core",
    "operation_type": "MUTATE",
    "target_resource": "artifact_123",
    "request_data": {"artifact_id": "artifact_123", "new_content": "modified"}
  }'
```

**Expected Response**:
```json
{
  "detail": {
    "message": "Request violates constitutional boundaries",
    "violations": [
      {
        "type": "prohibited_action",
        "severity": "critical",
        "action": "MUTATE"
      }
    ],
    "allowed": false
  }
}
```

✅ **Success Indicator**: HTTP 403 Forbidden, violation logged

---

### Step 6: Test Constitutional Status (30 seconds)

```bash
curl http://localhost:8000/constitutional/status
```

**Expected Response**:
```json
{
  "status": "active",
  "enforcement": "enabled",
  "boundaries_locked": true,
  "recent_violations_24h": 1,
  "critical_violations_24h": 1,
  "allowed_capabilities": 6,
  "prohibited_actions": 8,
  "input_channels": 4,
  "output_channels": 5,
  "certification": "constitutional_governance_active"
}
```

✅ **Success Indicator**: `"enforcement": "enabled"`, `"boundaries_locked": true"`

---

### Step 7: Test API Contract (30 seconds)

```bash
curl http://localhost:8000/constitutional/core/contract
```

**Expected Response**:
```json
{
  "input_channels": [
    "artifact_write",
    "artifact_read",
    "metadata_query",
    "audit_append"
  ],
  "output_channels": [
    "write_confirmation",
    "read_response",
    "query_results",
    "error_message",
    "audit_log"
  ],
  "contract_version": "1.0",
  "enforcement": "automatic"
}
```

✅ **Success Indicator**: 4 input channels, 5 output channels

---

### Step 8: Test Violation Summary (30 seconds)

```bash
curl "http://localhost:8000/constitutional/violations/summary?hours=24"
```

**Expected Response**:
```json
{
  "period_hours": 24,
  "boundary_violations": {
    "total_violations": 1,
    "critical_count": 1,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  },
  "detailed_report": {
    "violations": [
      {
        "violation_type": "prohibited_action",
        "severity": "critical",
        "timestamp": "2025-01-26T10:30:00Z"
      }
    ]
  },
  "status": "critical"
}
```

✅ **Success Indicator**: Violation from Step 5 is logged

---

## 🎯 SUCCESS CRITERIA

After completing all 8 steps, you should have:

- [x] Server running on port 8000
- [x] Health check shows constitutional governance active
- [x] Core capabilities endpoint returns 6 allowed + 8 prohibited
- [x] Allowed operation (READ) succeeds
- [x] Prohibited operation (MUTATE) is blocked with 403
- [x] Constitutional status shows enforcement enabled
- [x] API contract shows 4 input + 5 output channels
- [x] Violation summary shows the blocked MUTATE attempt

---

## 🚨 TROUBLESHOOTING

### Issue 1: Server Won't Start
**Error**: `Address already in use`

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Then restart
python main.py
```

---

### Issue 2: Import Errors
**Error**: `ModuleNotFoundError: No module named 'middleware.constitutional'`

**Solution**:
```bash
# Verify files exist
dir middleware\constitutional\core_boundary_enforcer.py
dir validators\core_api_contract.py
dir handlers\core_violation_handler.py

# Verify __init__.py files exist
dir middleware\constitutional\__init__.py
dir validators\__init__.py
dir handlers\__init__.py
```

---

### Issue 3: Endpoints Return 404
**Error**: `404 Not Found` for constitutional endpoints

**Solution**:
1. Check server logs for startup errors
2. Verify main.py has constitutional endpoints (lines 2800-3100)
3. Restart server after any code changes

---

### Issue 4: Health Check Shows Inactive
**Error**: `"constitutional_governance": "inactive"`

**Solution**:
1. Check imports in main.py (lines 106-108)
2. Verify modules are properly initialized
3. Check server logs for import errors

---

## 📊 PERFORMANCE BENCHMARKS

Expected performance for constitutional endpoints:

| Endpoint | Expected Latency | Max Latency |
|----------|-----------------|-------------|
| `/constitutional/core/capabilities` | <10ms | <50ms |
| `/constitutional/core/validate-request` | <20ms | <100ms |
| `/constitutional/core/contract` | <10ms | <50ms |
| `/constitutional/status` | <15ms | <75ms |
| `/constitutional/violations/summary` | <30ms | <150ms |

---

## 🔍 VERIFICATION CHECKLIST

After testing, verify:

- [ ] All 8 test commands executed successfully
- [ ] Health check shows constitutional governance active
- [ ] Allowed operations succeed (200 OK)
- [ ] Prohibited operations blocked (403 Forbidden)
- [ ] Violations are logged and retrievable
- [ ] No errors in server logs
- [ ] Performance within expected ranges
- [ ] Existing endpoints still working

---

## 📞 NEXT STEPS

### If All Tests Pass ✅
1. Proceed to load testing (100 concurrent requests)
2. Review EXECUTION_ACTION_PLAN.md for next tasks
3. Begin populating document templates
4. Schedule stakeholder sign-off sessions

### If Tests Fail ❌
1. Check troubleshooting section above
2. Review server logs for detailed errors
3. Verify file structure matches expected layout
4. Contact: Nilesh Vishwakarma (Backend Lead)
5. Escalate to: Ashmit Pandey (Primary Owner)

---

## 🎉 SUCCESS MESSAGE

If all 8 tests pass, you should see:

```
✅ Constitutional Governance System: OPERATIONAL
✅ Boundary Enforcement: ACTIVE
✅ API Contract Validation: ENABLED
✅ Violation Handling: AUTOMATED
✅ Escalation Paths: CONFIGURED
✅ System Status: PRODUCTION READY
```

**Congratulations! Your constitutional governance framework is fully operational.**

---

## 📖 ADDITIONAL RESOURCES

- **Full Implementation Guide**: `COMPLETE_IMPLEMENTATION_GUIDE.md`
- **Code Details**: `CODE_IMPLEMENTATION_GUIDE.md`
- **Execution Plan**: `EXECUTION_ACTION_PLAN.md`
- **Boundaries Document**: `docs/19_BHIV_CORE_BUCKET_BOUNDARIES.md`
- **Contract Document**: `docs/20_BHIV_CORE_BUCKET_CONTRACT.md`
- **Complete Summary**: `CONSTITUTIONAL_IMPLEMENTATION_COMPLETE.md`

---

**Testing Time**: 5 minutes  
**Status**: Ready to Execute  
**Next Action**: Run Step 1 and proceed through all 8 steps

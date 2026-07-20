# 🧪 THREAT HANDLING TESTING GUIDE

**Quick Reference for Testing Comprehensive Threat Detection & Escalation**

---

## QUICK START

All threat handling endpoints are now live and integrated with the existing system. They work alongside all 73+ existing governance endpoints without breaking any functionality.

**Base URL:** `http://localhost:8000`

---

## TEST SCENARIOS

### ✅ TEST 1: Storage Exhaustion Warning

**Scenario:** Check storage at 95% capacity (WARNING level)

```bash
curl -X POST "http://localhost:8000/governance/threats/check-storage-exhaustion?used_gb=950&total_gb=1000"
```

**Expected Response:**
```json
{
  "threat_id": "T1_STORAGE_EXHAUSTION",
  "capacity_status": {
    "status": "WARNING",
    "usage_percent": 95.0,
    "action_required": "PLAN_EXPANSION",
    "escalation_path": "Ops_Team",
    "response_timeline": "6_HOURS"
  },
  "escalation_required": true
}
```

---

### ✅ TEST 2: Storage Exhaustion Critical

**Scenario:** Check storage at 99.5% capacity (CRITICAL level)

```bash
curl -X POST "http://localhost:8000/governance/threats/check-storage-exhaustion?used_gb=995&total_gb=1000"
```

**Expected Response:**
```json
{
  "capacity_status": {
    "status": "CRITICAL",
    "action_required": "HALT_WRITES",
    "escalation_path": "Ashmit_Pandey_and_Ops",
    "response_timeline": "IMMEDIATE"
  }
}
```

---

### ✅ TEST 3: Executor Override Detection (BLOCKED)

**Scenario:** Executor attempts unauthorized action

```bash
curl -X POST "http://localhost:8000/governance/threats/check-executor-override?actor=akanksha_parab&requested_action=modify_schema&governance_scope=false"
```

**Expected Response:** `403 Forbidden`
```json
{
  "detail": {
    "threat": {
      "threat_id": "T5_EXECUTOR_OVERRIDE",
      "level": "critical",
      "escalation": "Vijay_Dhawan",
      "action": "BLOCK_AND_ESCALATE"
    },
    "message": "Operation blocked - executor authority violation",
    "escalation_required": true
  }
}
```

---

### ✅ TEST 4: Executor Within Scope (ALLOWED)

**Scenario:** Executor performs authorized action

```bash
curl -X POST "http://localhost:8000/governance/threats/check-executor-override?actor=akanksha_parab&requested_action=approve_write&governance_scope=true"
```

**Expected Response:** `200 OK`
```json
{
  "allowed": true,
  "actor": "akanksha_parab",
  "is_executor": true,
  "within_scope": true
}
```

---

### ✅ TEST 5: AI Escalation Attempt (BLOCKED)

**Scenario:** AI tries to read data (unauthorized)

```bash
curl -X POST "http://localhost:8000/governance/threats/check-ai-escalation?actor=ai_assistant&requested_operation=READ"
```

**Expected Response:** `403 Forbidden`
```json
{
  "detail": {
    "threat": {
      "threat_id": "T6_AI_ESCALATION",
      "level": "critical",
      "description": "AI actor ai_assistant requested unauthorized operation: READ",
      "escalation": "Vijay_Dhawan"
    },
    "escalation_required": true
  }
}
```

---

### ✅ TEST 6: AI Write Operation (ALLOWED)

**Scenario:** AI performs authorized write

```bash
curl -X POST "http://localhost:8000/governance/threats/check-ai-escalation?actor=ai_assistant&requested_operation=WRITE"
```

**Expected Response:** `200 OK`
```json
{
  "allowed": true,
  "actor": "ai_assistant",
  "is_ai_actor": true,
  "operation": "WRITE"
}
```

---

### ✅ TEST 7: Audit Tampering Detection (CRITICAL)

**Scenario:** Attempt to delete audit logs

```bash
curl -X POST "http://localhost:8000/governance/threats/check-audit-tampering?operation_type=DELETE&target_type=audit_log&actor=admin"
```

**Expected Response:** `403 Forbidden`
```json
{
  "detail": {
    "threat": {
      "threat_id": "T8_AUDIT_TAMPERING",
      "level": "critical",
      "escalation": "CEO",
      "action": "HALT_AND_INVESTIGATE"
    },
    "message": "CRITICAL: Audit tampering attempt detected",
    "severity": "MAXIMUM"
  }
}
```

---

### ✅ TEST 8: Cross-Product Leak Detection (BLOCKED)

**Scenario:** Product A tries to access Product B data

```bash
curl -X POST "http://localhost:8000/governance/threats/check-cross-product-leak?product_id=ai_assistant&requested_product_data=gurukul&artifact_type=content"
```

**Expected Response:** `403 Forbidden`
```json
{
  "detail": {
    "threat": {
      "threat_id": "T9_CROSS_PRODUCT_LEAK",
      "level": "critical",
      "description": "Product ai_assistant attempted to access gurukul data",
      "escalation": "Security_Team"
    }
  }
}
```

---

### ✅ TEST 9: Same Product Access (ALLOWED)

**Scenario:** Product accesses its own data

```bash
curl -X POST "http://localhost:8000/governance/threats/check-cross-product-leak?product_id=ai_assistant&requested_product_data=ai_assistant&artifact_type=conversation"
```

**Expected Response:** `200 OK`
```json
{
  "allowed": true,
  "product_id": "ai_assistant",
  "isolation_maintained": true
}
```

---

### ✅ TEST 10: Comprehensive Threat Scan

**Scenario:** Scan data with full context

```bash
curl -X POST "http://localhost:8000/governance/threats/scan-with-context" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "owner_id": "user123",
      "timestamp": "2026-01-19T10:00:00Z",
      "product_id": "ai_assistant",
      "artifact_type": "conversation"
    },
    "actor": "ai_assistant",
    "operation_type": "CREATE",
    "target_type": "artifact",
    "override_attempted": false
  }'
```

**Expected Response:** `200 OK`
```json
{
  "threats_detected": 0,
  "has_critical_threats": false,
  "threats": [],
  "action": "ALLOW_WITH_MONITORING",
  "escalation_required": false
}
```

---

### ✅ TEST 11: Get Escalation Matrix

**Scenario:** View all threat escalation paths

```bash
curl "http://localhost:8000/governance/threats/escalation-matrix"
```

**Expected Response:** Complete escalation matrix with 10 threats

---

### ✅ TEST 12: Get Certification Status

**Scenario:** Check threat model certification

```bash
curl "http://localhost:8000/governance/threats/certification-status"
```

**Expected Response:**
```json
{
  "certification": "PRODUCTION_READY",
  "total_threats_identified": 10,
  "automated_detection": "ALL_THREATS",
  "automated_escalation": "ALL_THREATS",
  "status": "CERTIFIED_FOR_PRODUCTION"
}
```

---

## INTEGRATION TESTS

### Test with Existing Endpoints

**Verify backward compatibility:**

```bash
# 1. Health check still works
curl "http://localhost:8000/health"

# 2. Agents still work
curl "http://localhost:8000/agents"

# 3. Baskets still work
curl "http://localhost:8000/baskets"

# 4. Governance gate still works
curl "http://localhost:8000/governance/gate/status"

# 5. Audit middleware still works
curl "http://localhost:8000/audit/recent?limit=10"
```

**All should return 200 OK with expected data.**

---

## POSTMAN COLLECTION

### Import these requests into Postman:

**Collection Name:** "Threat Handling Tests"

**Requests:**
1. Storage Warning (95%)
2. Storage Critical (99%)
3. Executor Override Blocked
4. Executor Allowed
5. AI Escalation Blocked
6. AI Write Allowed
7. Audit Tampering Blocked
8. Cross-Product Blocked
9. Same Product Allowed
10. Comprehensive Scan
11. Escalation Matrix
12. Certification Status

---

## EXPECTED BEHAVIOR

### ✅ Successful Operations
- Return `200 OK`
- Include `"allowed": true`
- No escalation required

### 🚫 Blocked Operations
- Return `403 Forbidden`
- Include threat details
- Include escalation path
- Logged in audit trail

### ⚠️ Warning Operations
- Return `200 OK`
- Include warning status
- Include escalation timeline
- Monitoring triggered

---

## AUDIT TRAIL VERIFICATION

After running tests, check audit logs:

```bash
# Get recent audit operations
curl "http://localhost:8000/audit/recent?limit=20"

# Get failed operations (should include blocked threats)
curl "http://localhost:8000/audit/failed?limit=10"
```

**Expected:** All blocked operations logged with:
- `"status": "blocked"`
- Threat ID in error message
- Actor information
- Timestamp

---

## PERFORMANCE VALIDATION

All threat checks should complete in:
- **< 50ms** for simple checks (executor, AI, cross-product)
- **< 100ms** for storage checks
- **< 200ms** for comprehensive scans

Test with:
```bash
time curl "http://localhost:8000/governance/threats/check-ai-escalation?actor=ai_assistant&requested_operation=READ"
```

---

## TROUBLESHOOTING

### Issue: 500 Internal Server Error
**Solution:** Check server logs in `logs/application.log`

### Issue: Audit middleware not logging
**Solution:** Verify MongoDB connection in health check

### Issue: Threats not detected
**Solution:** Verify threat_validator.py is loaded correctly

### Issue: Escalation not triggered
**Solution:** Check audit_middleware.py for log entries

---

## SUCCESS CRITERIA

✅ All 12 test scenarios pass  
✅ Blocked operations return 403  
✅ Allowed operations return 200  
✅ Audit trail captures all operations  
✅ Escalation paths are correct  
✅ Performance < 200ms  
✅ No breaking changes to existing endpoints  
✅ Health check shows all services active

---

## NEXT STEPS

1. **Run all 12 tests** to verify functionality
2. **Check audit logs** to verify logging
3. **Test integration** with existing endpoints
4. **Verify performance** meets targets
5. **Review escalation matrix** for completeness

**Status:** ✅ Ready for production testing

# 🚀 THREAT HANDLING QUICK REFERENCE

**One-Page Guide for Developers**

---

## ENDPOINTS AT A GLANCE

### Storage Checks
```bash
POST /governance/threats/check-storage-exhaustion?used_gb=950&total_gb=1000
```
**Returns:** Capacity status with escalation path

### Executor Validation
```bash
POST /governance/threats/check-executor-override?actor=akanksha_parab&requested_action=approve_write&governance_scope=true
```
**Returns:** 200 OK (allowed) or 403 Forbidden (blocked)

### AI Permission Check
```bash
POST /governance/threats/check-ai-escalation?actor=ai_assistant&requested_operation=WRITE
```
**Returns:** 200 OK (allowed) or 403 Forbidden (blocked)

### Audit Protection
```bash
POST /governance/threats/check-audit-tampering?operation_type=DELETE&target_type=audit_log&actor=admin
```
**Returns:** 403 Forbidden (always blocked)

### Product Isolation
```bash
POST /governance/threats/check-cross-product-leak?product_id=ai_assistant&requested_product_data=ai_assistant&artifact_type=conversation
```
**Returns:** 200 OK (same product) or 403 Forbidden (different product)

### Comprehensive Scan
```bash
POST /governance/threats/scan-with-context
Content-Type: application/json

{
  "data": {...},
  "actor": "user123",
  "operation_type": "CREATE"
}
```
**Returns:** All detected threats with escalation paths

### Information
```bash
GET /governance/threats/escalation-matrix
GET /governance/threats/certification-status
```

---

## RESPONSE CODES

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Allowed | Proceed with operation |
| 403 | Blocked | Log, escalate, halt |
| 500 | Error | Check logs, retry |

---

## THREAT LEVELS

| Level | Action | Escalation |
|-------|--------|------------|
| CRITICAL | HALT | Immediate |
| HIGH | BLOCK | 1-6 hours |
| MEDIUM | MONITOR | 24-48 hours |

---

## ESCALATION PATHS

```
Storage → Ops Team → Ashmit
Executor → Vijay Dhawan
AI → Vijay Dhawan
Audit → CEO
Cross-Product → Security Team
```

---

## QUICK TESTS

```bash
# Test 1: Storage warning
curl -X POST "http://localhost:8000/governance/threats/check-storage-exhaustion?used_gb=950&total_gb=1000"

# Test 2: AI escalation (blocked)
curl -X POST "http://localhost:8000/governance/threats/check-ai-escalation?actor=ai_assistant&requested_operation=READ"

# Test 3: Get escalation matrix
curl "http://localhost:8000/governance/threats/escalation-matrix"
```

---

## INTEGRATION EXAMPLE

```python
import requests

def safe_write_artifact(data, actor):
    # Check threats first
    response = requests.post(
        "http://localhost:8000/governance/threats/scan-with-context",
        json={
            "data": data,
            "actor": actor,
            "operation_type": "CREATE"
        }
    )
    
    if response.status_code == 403:
        # Critical threat detected
        log_and_escalate(response.json())
        return False
    
    # Safe to proceed
    write_to_bucket(data)
    return True
```

---

## COMMON PATTERNS

### Before Large Write
```python
check_storage_exhaustion(current_usage)
```

### Before AI Operation
```python
check_ai_escalation(actor, operation)
```

### Before Cross-Product Access
```python
check_cross_product_leak(source_product, target_product)
```

### After Any Operation
```python
log_to_audit_trail(operation_details)
```

---

## MONITORING

**Watch for:**
- Storage > 90%
- Repeated 403 responses
- Critical threats detected
- Escalation frequency

**Alert on:**
- Storage > 99%
- Audit tampering attempts
- AI escalation attempts
- Cross-product violations

---

## TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| 500 error | Check `logs/application.log` |
| Audit not logging | Verify MongoDB connection |
| Threats not detected | Check threat_validator.py |
| Performance slow | Check response times < 200ms |

---

## DOCUMENTATION

- **Full Threat Model:** `docs/17_governance_failure_handling.md`
- **Testing Guide:** `docs/THREAT_HANDLING_TESTING_GUIDE.md`
- **Implementation:** `docs/THREAT_IMPLEMENTATION_COMPLETE.md`

---

## SUPPORT

- **Operational:** Ops Team
- **Governance:** Vijay Dhawan
- **Critical:** CEO
- **Owner:** Ashmit Pandey

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** January 19, 2026

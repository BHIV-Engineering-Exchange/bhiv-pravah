# Constitutional Governance - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Step 1: Verify Installation
```bash
# Check if modules are loaded
curl http://localhost:8000/constitutional/status
```

**Expected Response:**
```json
{
  "status": "active",
  "enforcement": "enabled",
  "boundaries_locked": true,
  "allowed_capabilities": 6,
  "prohibited_actions": 8
}
```

### Step 2: Test Core Request Validation
```bash
# Valid request
curl -X POST "http://localhost:8000/constitutional/core/validate-request" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "bhiv_core",
    "operation_type": "READ",
    "target_resource": "artifacts",
    "request_data": {"artifact_id": "test"}
  }'
```

### Step 3: View Capabilities
```bash
curl http://localhost:8000/constitutional/core/capabilities
```

---

## 📖 Common Use Cases

### Use Case 1: Validate Before Writing
```python
import requests

# Before writing to Bucket, validate the request
response = requests.post(
    "http://localhost:8000/constitutional/core/validate-request",
    json={
        "requester_id": "bhiv_core",
        "operation_type": "WRITE",
        "target_resource": "artifacts",
        "request_data": {
            "artifact_type": "model_checkpoint",
            "product_id": "AI_Avatar",
            "data": {"version": "1.0"}
        }
    }
)

if response.json()["allowed"]:
    # Proceed with write
    pass
else:
    # Handle violation
    print(f"Blocked: {response.json()['violations']}")
```

### Use Case 2: Monitor Violations
```python
# Check for violations in last 24 hours
response = requests.get(
    "http://localhost:8000/constitutional/violations/summary?hours=24"
)

summary = response.json()
if summary["boundary_violations"]["critical_count"] > 0:
    # Alert team
    print(f"CRITICAL: {summary['boundary_violations']['critical_count']} violations")
```

### Use Case 3: Validate Input Data
```python
# Validate input data format
response = requests.post(
    "http://localhost:8000/constitutional/core/validate-input",
    params={
        "channel": "artifact_write",
        "requester_id": "bhiv_core"
    },
    json={
        "artifact_type": "model_checkpoint",
        "product_id": "AI_Avatar",
        "data": {"version": "1.0"}
    }
)

if response.json()["valid"]:
    # Data format is correct
    pass
```

---

## 🔍 Monitoring Dashboard

### Daily Checks
```bash
# 1. Check system status
curl http://localhost:8000/constitutional/status

# 2. Check violations (last 24h)
curl http://localhost:8000/constitutional/violations/summary?hours=24

# 3. Check detailed report
curl http://localhost:8000/constitutional/violations/report?hours=24
```

### Weekly Review
```bash
# Get 7-day violation report
curl http://localhost:8000/constitutional/violations/report?hours=168
```

---

## ⚠️ Troubleshooting

### Problem: Request Blocked
**Symptom:** Getting 403 Forbidden
**Solution:**
1. Check requester_id starts with "bhiv_core"
2. Verify operation_type is allowed (READ/WRITE/QUERY/etc)
3. Check for prohibited actions in request_data
4. Review violation details in response

### Problem: Validation Fails
**Symptom:** Input validation returns errors
**Solution:**
1. Check channel name is correct
2. Verify all required fields are present
3. Check data types match schema
4. Review API contract: `GET /constitutional/core/contract`

### Problem: Too Many Violations
**Symptom:** High violation count
**Solution:**
1. Review violation report for patterns
2. Check if Core is attempting unauthorized operations
3. Verify Core is using correct API channels
4. Escalate to appropriate team based on severity

---

## 📚 API Reference

### Validation Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/constitutional/core/validate-request` | POST | Validate Core request |
| `/constitutional/core/validate-input` | POST | Validate input data |
| `/constitutional/core/validate-output` | POST | Validate output data |

### Information Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/constitutional/core/capabilities` | GET | Get allowed capabilities |
| `/constitutional/core/contract` | GET | Get API contract |
| `/constitutional/status` | GET | Get system status |

### Monitoring Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/constitutional/violations/summary` | GET | Get violation summary |
| `/constitutional/violations/report` | GET | Get detailed report |
| `/constitutional/violations/handle` | POST | Manually handle violation |

---

## 🎯 Best Practices

### For Developers
1. **Always validate before operations**
   - Validate requests before sending to Bucket
   - Check capabilities before attempting operations
   - Handle violations gracefully

2. **Use correct channels**
   - artifact_write for writing artifacts
   - metadata_query for querying
   - audit_append for audit entries
   - retention_request for retention operations

3. **Monitor violations**
   - Check violation summary daily
   - Investigate patterns
   - Fix root causes

### For Operations
1. **Daily monitoring**
   - Check `/constitutional/status` every morning
   - Review violation summary
   - Respond to escalations

2. **Weekly reviews**
   - Analyze 7-day violation trends
   - Identify recurring issues
   - Update documentation

3. **Incident response**
   - CRITICAL violations: Immediate response
   - HIGH violations: 1-hour response
   - MEDIUM violations: 6-hour response
   - LOW violations: 24-hour response

---

## 🔐 Security Notes

### Allowed Operations
- ✅ READ artifacts
- ✅ WRITE artifacts
- ✅ QUERY metadata
- ✅ APPEND audit logs
- ✅ REQUEST retention
- ✅ VERIFY provenance

### Prohibited Operations
- ❌ MUTATE schema
- ❌ DELETE artifacts
- ❌ HIDE operations
- ❌ BYPASS governance
- ❌ MODIFY audit logs
- ❌ CROSS-PRODUCT access
- ❌ DIRECT database access
- ❌ OVERRIDE retention

---

## 📞 Support

### For Questions
- Check `/constitutional/core/contract` for API details
- Review `/constitutional/core/capabilities` for allowed operations
- Check violation reports for patterns

### For Issues
- CRITICAL violations → Escalate to Owner immediately
- HIGH violations → Escalate to Advisor within 1 hour
- MEDIUM violations → Escalate to Executor within 6 hours
- LOW violations → Log for Ops Team review

### For Changes
- Boundary changes require all stakeholder approval
- No emergency overrides allowed
- All changes must go through governance gate

---

## ✅ Success Checklist

- [ ] Constitutional status shows "active"
- [ ] Can validate Core requests successfully
- [ ] Can view capabilities and contract
- [ ] Can monitor violations
- [ ] Team knows escalation procedures
- [ ] Daily monitoring in place
- [ ] Incident response procedures documented

---

**Status:** READY FOR PRODUCTION ✅

For detailed information, see: `CONSTITUTIONAL_GOVERNANCE_IMPLEMENTATION.md`

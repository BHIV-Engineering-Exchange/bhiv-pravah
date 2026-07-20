# 🚀 CERTIFICATION FEATURES - QUICK START GUIDE

**Document:** CERTIFICATION_QUICK_START.md  
**Status:** ACTIVE  
**Last Updated:** January 2026

---

## 📋 OVERVIEW

This guide provides a quick start for using the new enterprise certification features in BHIV Bucket v1.0.0.

---

## 🎯 NEW FEATURES

### 1. Threat Detection
**Endpoint:** `/governance/threats`  
**Purpose:** Detect security threats in data before storage

### 2. Scale Limits Enforcement
**Endpoint:** `/governance/scale`  
**Purpose:** Enforce capacity limits and prevent overload

### 3. Immutable Audit Trail
**Endpoint:** `/audit`  
**Purpose:** Track all operations with immutable audit logs

---

## ⚡ QUICK TESTS

### Test 1: Check System Health (with Certification)
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "bucket_version": "1.0.0",
  "governance": {
    "gate_active": true,
    "approved_integrations": 0,
    "certification": "enterprise_ready",
    "certification_date": "2026-01-19"
  },
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "audit_middleware": "active"
  }
}
```

---

### Test 2: Scan Data for Threats
```bash
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "user_123",
    "product_id": "AI_Assistant",
    "artifact_type": "metadata"
  }'
```

**Expected Response:**
```json
{
  "threats_detected": 0,
  "has_critical_threats": false,
  "threats": [],
  "recommendation": "ALLOW"
}
```

---

### Test 3: Validate Operation Scale
```bash
curl -X POST "http://localhost:8000/governance/scale/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "write",
    "data_size": 1000000,
    "frequency": 100
  }'
```

**Expected Response:**
```json
{
  "valid": true,
  "message": "Operation within scale limits"
}
```

---

### Test 4: Create Audit Entry
```bash
curl -X POST "http://localhost:8000/audit/log" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "CREATE",
    "artifact_id": "test_123",
    "requester_id": "user_123",
    "integration_id": "test_integration",
    "status": "success"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "audit_id": "audit_entry_1",
  "message": "Audit entry created successfully"
}
```

---

### Test 5: Get All Threats
```bash
curl http://localhost:8000/governance/threats
```

**Expected Response:**
```json
{
  "threats": [...],
  "total_threats": 10,
  "reference": "docs/14_bucket_threat_model.md"
}
```

---

### Test 6: Get Scale Limits
```bash
curl http://localhost:8000/governance/scale/limits
```

**Expected Response:**
```json
{
  "scale_limits": {
    "storage": {
      "max_total_gb": 1000,
      "max_artifact_size": 16777216
    },
    "write_performance": {
      "max_throughput_per_sec": 1000
    }
  },
  "reference": "docs/15_scale_readiness.md"
}
```

---

### Test 7: Check Limit Proximity
```bash
curl "http://localhost:8000/governance/scale/proximity/artifacts_per_product?current_value=1000000"
```

**Expected Response:**
```json
{
  "limit_name": "artifacts_per_product",
  "current_value": 1000000,
  "limit_value": 10000000,
  "usage_ratio": 0.1,
  "usage_percent": 10.0,
  "status": "HEALTHY"
}
```

---

### Test 8: Get Artifact Audit History
```bash
curl "http://localhost:8000/audit/artifact/test_123"
```

**Expected Response:**
```json
{
  "artifact_id": "test_123",
  "history": [...],
  "count": 1
}
```

---

## 📚 DOCUMENTATION REFERENCE

### Certification Documents
1. **Document 14:** `docs/14_bucket_threat_model.md` - Threat Model
2. **Document 15:** `docs/15_scale_readiness.md` - Scale Limits
3. **Document 16:** `docs/16_multi_product_compatibility.md` - Product Compatibility
4. **Document 17:** `docs/17_governance_failure_handling.md` - Failure Handling
5. **Document 18:** `docs/18_bucket_enterprise_certification.md` - Enterprise Certification

### Test Guides
1. **THREAT_VALIDATOR_TEST_GUIDE.md** - Threat detection testing
2. **SCALE_LIMITS_TEST_GUIDE.md** - Scale limits testing
3. **AUDIT_MIDDLEWARE_TEST_GUIDE.md** - Audit trail testing

### Code Modules
1. **utils/threat_validator.py** - Threat detection implementation
2. **config/scale_limits.py** - Scale limits configuration
3. **middleware/audit_middleware.py** - Audit trail implementation
4. **governance/governance_gate.py** - Integrated governance gate

---

## 🎯 COMMON USE CASES

### Use Case 1: Validate Integration Request
```bash
# Step 1: Scan for threats
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{"owner_id": "user_123", "product_id": "AI_Assistant"}'

# Step 2: Validate scale
curl -X POST "http://localhost:8000/governance/scale/validate" \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "write", "data_size": 1000000, "frequency": 100}'

# Step 3: Create audit entry
curl -X POST "http://localhost:8000/audit/log" \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "CREATE", "artifact_id": "test_123", "requester_id": "user_123", "integration_id": "AI_Assistant", "status": "success"}'
```

---

### Use Case 2: Monitor System Health
```bash
# Check overall health
curl http://localhost:8000/health

# Check scale limits proximity
curl "http://localhost:8000/governance/scale/proximity/artifacts_per_product?current_value=5000000"

# Get recent failed operations
curl "http://localhost:8000/audit/failed?limit=10"
```

---

### Use Case 3: Investigate Artifact History
```bash
# Get artifact history
curl "http://localhost:8000/audit/artifact/artifact_123"

# Validate immutability
curl -X POST "http://localhost:8000/audit/validate-immutability/artifact_123"

# Get user activities
curl "http://localhost:8000/audit/user/user_123"
```

---

## ✅ VERIFICATION CHECKLIST

After starting the system, verify:

- [ ] Health endpoint shows `certification: "enterprise_ready"`
- [ ] Threat detection returns 10 threats
- [ ] Scale limits are configured
- [ ] Audit middleware is active
- [ ] All test scenarios pass
- [ ] Documentation is accessible

---

## 🚨 TROUBLESHOOTING

### Issue: Threat validator not working
**Solution:** Check `utils/threat_validator.py` is imported in `governance/governance_gate.py`

### Issue: Scale limits not enforced
**Solution:** Verify `config/scale_limits.py` exists and is imported

### Issue: Audit entries not created
**Solution:** Check MongoDB connection and `middleware/audit_middleware.py` initialization

### Issue: Endpoints return 404
**Solution:** Restart server to load new endpoints: `python main.py`

---

## 📞 SUPPORT

For issues or questions:
1. Check test guides for detailed scenarios
2. Review certification documents for specifications
3. Verify all modules are imported correctly
4. Check logs for detailed error messages

---

**END OF QUICK START GUIDE**

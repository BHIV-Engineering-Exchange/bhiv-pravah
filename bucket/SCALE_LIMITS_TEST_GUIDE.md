# 📈 SCALE LIMITS TEST GUIDE

**Document:** SCALE_LIMITS_TEST_GUIDE.md  
**Status:** ACTIVE  
**Owner:** Ashmit Pandey  
**Last Updated:** January 2026

---

## 📋 OVERVIEW

This guide provides comprehensive testing procedures for BHIV Bucket Scale Limits, which implement capacity management from Document 15 (Scale Readiness).

---

## 🧪 TEST SCENARIOS

### Test 1: Get All Scale Limits
**Purpose:** Verify all scale limits are configured

```bash
curl http://localhost:8000/governance/scale/limits
```

**Expected Response:**
```json
{
  "scale_limits": {
    "storage": {
      "max_total_gb": 1000,
      "max_artifact_size": 16777216,
      "warning_threshold": 0.90,
      "critical_threshold": 0.99
    },
    "write_performance": {
      "max_throughput_per_sec": 1000,
      "safe_throughput_per_sec": 500,
      "max_concurrent": 100,
      "safe_concurrent": 50
    },
    ...
  },
  "performance_targets": {
    "write_latency_p99_ms": 100,
    "read_latency_p99_ms": 50,
    ...
  }
}
```

---

### Test 2: Validate Operation Within Limits
**Purpose:** Verify operation within safe limits is accepted

```bash
curl -X POST "http://localhost:8000/governance/scale/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "write",
    "data_size": 1048576,
    "frequency": 100
  }'
```

**Expected Response:**
```json
{
  "valid": true,
  "message": "Operation within scale limits",
  "operation_type": "write",
  "data_size": 1048576,
  "frequency": 100
}
```

---

### Test 3: Detect Size Limit Violation
**Purpose:** Verify oversized artifacts are rejected

```bash
curl -X POST "http://localhost:8000/governance/scale/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "write",
    "data_size": 20000000,
    "frequency": 1
  }'
```

**Expected Response:**
```json
{
  "message": "Operation exceeds scale limits",
  "error": "Data size 20000000 exceeds limit of 16777216",
  "operation_type": "write",
  "data_size": 20000000,
  "frequency": 1
}
```

---

### Test 4: Detect Frequency Limit Violation
**Purpose:** Verify excessive write frequency is rejected

```bash
curl -X POST "http://localhost:8000/governance/scale/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "write",
    "data_size": 1000,
    "frequency": 1500
  }'
```

**Expected Response:**
```json
{
  "message": "Operation exceeds scale limits",
  "error": "Write frequency 1500/sec exceeds limit of 1000/sec",
  "operation_type": "write",
  "data_size": 1000,
  "frequency": 1500
}
```

---

### Test 5: Check Limit Proximity (Healthy)
**Purpose:** Verify healthy usage reporting

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
  "remaining": 9000000,
  "status": "HEALTHY"
}
```

---

### Test 6: Check Limit Proximity (Warning)
**Purpose:** Verify warning threshold detection

```bash
curl "http://localhost:8000/governance/scale/proximity/artifacts_per_product?current_value=8000000"
```

**Expected Response:**
```json
{
  "limit_name": "artifacts_per_product",
  "current_value": 8000000,
  "limit_value": 10000000,
  "usage_ratio": 0.8,
  "usage_percent": 80.0,
  "remaining": 2000000,
  "status": "WARNING"
}
```

---

### Test 7: Check Limit Proximity (Critical)
**Purpose:** Verify critical threshold detection

```bash
curl "http://localhost:8000/governance/scale/proximity/artifacts_per_product?current_value=9500000"
```

**Expected Response:**
```json
{
  "limit_name": "artifacts_per_product",
  "current_value": 9500000,
  "limit_value": 10000000,
  "usage_ratio": 0.95,
  "usage_percent": 95.0,
  "remaining": 500000,
  "status": "CRITICAL"
}
```

---

### Test 8: Get What Scales Safely
**Purpose:** Verify scaling behavior documentation

```bash
curl http://localhost:8000/governance/scale/what-scales
```

**Expected Response:**
```json
{
  "scales_safely": [
    "Number of artifact types (unlimited)",
    "Number of products (up to 100)",
    "Number of teams (up to 1000)",
    "Artifact count per product (up to 10M)",
    "Audit log retention (7 years unlimited entries)"
  ],
  "does_not_scale": [
    "Real-time queries across all products",
    "Distributed read-heavy operations (>100 reads/sec)",
    "Multi-region replication",
    "Full-text search",
    "Real-time analytics"
  ],
  "never_assume": [
    "Eventual consistency without bounds",
    "Automatic schema migrations",
    "Backfill on failure",
    "Infinite storage",
    "Zero-downtime upgrades"
  ]
}
```

---

## 🔧 PYTHON TESTING

### Test Script
```python
import requests

BASE_URL = "http://localhost:8000"

def test_scale_limits():
    # Test 1: Get all limits
    response = requests.get(f"{BASE_URL}/governance/scale/limits")
    assert response.status_code == 200
    data = response.json()
    assert "scale_limits" in data
    assert "performance_targets" in data
    print("✅ Test 1 passed: Scale limits retrieved")
    
    # Test 2: Validate safe operation
    safe_op = {
        "operation_type": "write",
        "data_size": 1000000,
        "frequency": 100
    }
    response = requests.post(f"{BASE_URL}/governance/scale/validate", json=safe_op)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True
    print("✅ Test 2 passed: Safe operation accepted")
    
    # Test 3: Detect size violation
    oversized_op = {
        "operation_type": "write",
        "data_size": 20000000,
        "frequency": 1
    }
    response = requests.post(f"{BASE_URL}/governance/scale/validate", json=oversized_op)
    assert response.status_code == 400
    print("✅ Test 3 passed: Oversized operation rejected")
    
    # Test 4: Check proximity (healthy)
    response = requests.get(
        f"{BASE_URL}/governance/scale/proximity/artifacts_per_product",
        params={"current_value": 1000000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    print("✅ Test 4 passed: Healthy usage detected")
    
    # Test 5: Check proximity (critical)
    response = requests.get(
        f"{BASE_URL}/governance/scale/proximity/artifacts_per_product",
        params={"current_value": 9500000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CRITICAL"
    print("✅ Test 5 passed: Critical usage detected")
    
    print("\n🎉 All scale limits tests passed!")

if __name__ == "__main__":
    test_scale_limits()
```

---

## ✅ VALIDATION CHECKLIST

- [ ] All scale limits are configured
- [ ] Safe operations are accepted
- [ ] Oversized artifacts are rejected
- [ ] Excessive frequency is rejected
- [ ] Healthy usage is reported correctly
- [ ] Warning threshold triggers at 70%
- [ ] Critical threshold triggers at 90%
- [ ] What scales/doesn't scale is documented

---

## 📊 EXPECTED LIMITS

### Storage Limits
- **Max Total Storage:** 1TB (1000GB)
- **Max Artifact Size:** 16MB
- **Warning Threshold:** 90% capacity
- **Critical Threshold:** 99% capacity

### Write Performance
- **Max Throughput:** 1000 writes/sec
- **Safe Throughput:** 500 writes/sec
- **Max Concurrent:** 100 writers
- **Safe Concurrent:** 50 writers

### Read Performance
- **Max Throughput:** 100 reads/sec
- **Safe Throughput:** 50 reads/sec
- **Max Concurrent:** 50 readers
- **Safe Concurrent:** 20 readers

### Artifacts
- **Max Per Product:** 10M artifacts
- **Max Total:** 100M artifacts
- **Warning Per Product:** 7M artifacts

---

## 🚨 TROUBLESHOOTING

### Issue: Limits not enforced
**Solution:** Ensure scale_limits.py is imported in governance_gate.py

### Issue: False rejections
**Solution:** Verify data_size calculation is correct

### Issue: Missing limits
**Solution:** Check ScaleLimits class has all required constants

---

**END OF SCALE LIMITS TEST GUIDE**

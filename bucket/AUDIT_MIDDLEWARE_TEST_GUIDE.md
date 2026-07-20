# 🔒 AUDIT MIDDLEWARE TEST GUIDE

**Document:** AUDIT_MIDDLEWARE_TEST_GUIDE.md  
**Status:** ACTIVE  
**Owner:** Ashmit Pandey  
**Last Updated:** January 2026

---

## 📋 OVERVIEW

This guide provides comprehensive testing procedures for BHIV Bucket Audit Middleware, which implements immutable audit trails from Document 14 (Threat Model).

---

## 🧪 TEST SCENARIOS

### Test 1: Get Artifact Audit History
**Purpose:** Verify complete audit trail retrieval

```bash
curl "http://localhost:8000/audit/artifact/test_artifact_123?limit=100"
```

**Expected Response:**
```json
{
  "artifact_id": "test_artifact_123",
  "history": [
    {
      "_id": "audit_entry_1",
      "timestamp": "2026-01-20T10:00:00Z",
      "operation_type": "CREATE",
      "artifact_id": "test_artifact_123",
      "requester_id": "user_123",
      "integration_id": "AI_Assistant",
      "status": "success",
      "immutable": true
    }
  ],
  "count": 1
}
```

---

### Test 2: Get User Activities
**Purpose:** Verify user activity tracking

```bash
curl "http://localhost:8000/audit/user/user_123?limit=100"
```

**Expected Response:**
```json
{
  "requester_id": "user_123",
  "activities": [
    {
      "_id": "audit_entry_1",
      "timestamp": "2026-01-20T10:00:00Z",
      "operation_type": "CREATE",
      "artifact_id": "test_artifact_123",
      "status": "success"
    },
    {
      "_id": "audit_entry_2",
      "timestamp": "2026-01-20T10:05:00Z",
      "operation_type": "READ",
      "artifact_id": "test_artifact_456",
      "status": "success"
    }
  ],
  "count": 2
}
```

---

### Test 3: Get Recent Operations
**Purpose:** Verify recent operations tracking

```bash
curl "http://localhost:8000/audit/recent?limit=100"
```

**Expected Response:**
```json
{
  "operations": [
    {
      "_id": "audit_entry_3",
      "timestamp": "2026-01-20T10:10:00Z",
      "operation_type": "UPDATE",
      "artifact_id": "test_artifact_789",
      "requester_id": "user_456",
      "status": "success"
    }
  ],
  "count": 1,
  "filter": null
}
```

---

### Test 4: Get Recent Operations (Filtered)
**Purpose:** Verify operation type filtering

```bash
curl "http://localhost:8000/audit/recent?limit=100&operation_type=CREATE"
```

**Expected Response:**
```json
{
  "operations": [
    {
      "_id": "audit_entry_1",
      "timestamp": "2026-01-20T10:00:00Z",
      "operation_type": "CREATE",
      "artifact_id": "test_artifact_123",
      "status": "success"
    }
  ],
  "count": 1,
  "filter": {"operation_type": "CREATE"}
}
```

---

### Test 5: Get Failed Operations
**Purpose:** Verify failure tracking for incident response

```bash
curl "http://localhost:8000/audit/failed?limit=100"
```

**Expected Response:**
```json
{
  "failed_operations": [
    {
      "_id": "audit_entry_4",
      "timestamp": "2026-01-20T10:15:00Z",
      "operation_type": "UPDATE",
      "artifact_id": "test_artifact_999",
      "requester_id": "user_789",
      "status": "failure",
      "error_message": "Artifact not found"
    }
  ],
  "count": 1,
  "severity": "normal"
}
```

---

### Test 6: Validate Artifact Immutability (Pass)
**Purpose:** Verify immutable artifacts are validated correctly

```bash
curl -X POST "http://localhost:8000/audit/validate-immutability/test_artifact_123"
```

**Expected Response:**
```json
{
  "artifact_id": "test_artifact_123",
  "is_immutable": true,
  "status": "valid"
}
```

---

### Test 7: Validate Artifact Immutability (Fail)
**Purpose:** Verify modified artifacts are detected

```bash
curl -X POST "http://localhost:8000/audit/validate-immutability/modified_artifact_456"
```

**Expected Response:**
```json
{
  "artifact_id": "modified_artifact_456",
  "is_immutable": false,
  "status": "violation_detected"
}
```

---

### Test 8: Create Manual Audit Log
**Purpose:** Verify manual audit entry creation

```bash
curl -X POST "http://localhost:8000/audit/log" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "CREATE",
    "artifact_id": "manual_test_123",
    "requester_id": "test_user",
    "integration_id": "test_integration",
    "status": "success"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "audit_id": "audit_entry_5",
  "message": "Audit entry created successfully"
}
```

---

### Test 9: Create Audit Log with Error
**Purpose:** Verify error logging

```bash
curl -X POST "http://localhost:8000/audit/log" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "UPDATE",
    "artifact_id": "error_test_456",
    "requester_id": "test_user",
    "integration_id": "test_integration",
    "status": "failure",
    "error_message": "Permission denied"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "audit_id": "audit_entry_6",
  "message": "Audit entry created successfully"
}
```

---

### Test 10: Audit Service Unavailable
**Purpose:** Verify graceful handling when MongoDB unavailable

```bash
# Stop MongoDB, then:
curl -X POST "http://localhost:8000/audit/log" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "CREATE",
    "artifact_id": "test_789",
    "requester_id": "test_user",
    "integration_id": "test_integration"
  }'
```

**Expected Response:**
```json
{
  "detail": "Audit service unavailable"
}
```

---

## 🔧 PYTHON TESTING

### Test Script
```python
import requests

BASE_URL = "http://localhost:8000"

def test_audit_middleware():
    # Test 1: Create audit entry
    audit_data = {
        "operation_type": "CREATE",
        "artifact_id": "test_artifact_123",
        "requester_id": "test_user",
        "integration_id": "test_integration",
        "status": "success"
    }
    response = requests.post(f"{BASE_URL}/audit/log", json=audit_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    audit_id = data["audit_id"]
    print(f"✅ Test 1 passed: Audit entry created ({audit_id})")
    
    # Test 2: Get artifact history
    response = requests.get(f"{BASE_URL}/audit/artifact/test_artifact_123")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    print("✅ Test 2 passed: Artifact history retrieved")
    
    # Test 3: Get user activities
    response = requests.get(f"{BASE_URL}/audit/user/test_user")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    print("✅ Test 3 passed: User activities retrieved")
    
    # Test 4: Get recent operations
    response = requests.get(f"{BASE_URL}/audit/recent")
    assert response.status_code == 200
    data = response.json()
    assert "operations" in data
    print("✅ Test 4 passed: Recent operations retrieved")
    
    # Test 5: Validate immutability
    response = requests.post(f"{BASE_URL}/audit/validate-immutability/test_artifact_123")
    assert response.status_code == 200
    data = response.json()
    assert data["is_immutable"] == True
    print("✅ Test 5 passed: Immutability validated")
    
    print("\n🎉 All audit middleware tests passed!")

if __name__ == "__main__":
    test_audit_middleware()
```

---

## ✅ VALIDATION CHECKLIST

- [ ] Audit entries are created successfully
- [ ] Artifact history is complete
- [ ] User activities are tracked
- [ ] Recent operations are retrievable
- [ ] Failed operations are logged
- [ ] Immutability validation works
- [ ] Manual audit entries can be created
- [ ] Error logging works correctly
- [ ] Graceful handling when MongoDB unavailable

---

## 📊 EXPECTED BEHAVIOR

### Immutable Artifact Classes
- `audit_entry` - Cannot be updated or deleted
- `model_checkpoint` - Cannot be updated or deleted
- `metadata` - Cannot be updated or deleted
- `iteration_history` - Cannot be updated or deleted
- `event_history` - Cannot be updated or deleted

### Audit Entry Fields
- `timestamp` - UTC timestamp (server-generated)
- `operation_type` - CREATE, READ, UPDATE, DELETE
- `artifact_id` - ID of artifact
- `requester_id` - User/system performing operation
- `integration_id` - Integration making request
- `status` - success, failure, blocked
- `data_before` - State before operation (optional)
- `data_after` - State after operation (optional)
- `error_message` - Error details (if failed)
- `immutable` - Always true
- `audit_version` - Version 1.0

---

## 🚨 TROUBLESHOOTING

### Issue: Audit entries not created
**Solution:** Check MongoDB connection, verify audit_middleware is initialized

### Issue: History incomplete
**Solution:** Verify all operations go through audit middleware

### Issue: Immutability validation fails
**Solution:** Check audit trail for UPDATE/DELETE operations

### Issue: Service unavailable
**Solution:** Verify MongoDB is running and accessible

---

**END OF AUDIT MIDDLEWARE TEST GUIDE**

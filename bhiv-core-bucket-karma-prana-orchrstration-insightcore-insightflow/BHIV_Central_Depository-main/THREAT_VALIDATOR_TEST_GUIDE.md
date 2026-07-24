# 🛡️ THREAT VALIDATOR TEST GUIDE

**Document:** THREAT_VALIDATOR_TEST_GUIDE.md  
**Status:** ACTIVE  
**Owner:** Ashmit Pandey  
**Last Updated:** January 2026

---

## 📋 OVERVIEW

This guide provides comprehensive testing procedures for the BHIV Bucket Threat Validator, which implements threat detection patterns from Document 14 (Threat Model).

---

## 🧪 TEST SCENARIOS

### Test 1: Get All Threats
**Purpose:** Verify all 10 threats are registered

```bash
curl http://localhost:8000/governance/threats
```

**Expected Response:**
```json
{
  "threats": [
    {
      "threat_id": "T1_STORAGE_EXHAUSTION",
      "severity": "HIGH",
      "description": "Storage exhaustion attack",
      "patterns": ["rapid_writes", "large_artifacts", "metadata_explosion"]
    },
    ...
  ],
  "total_threats": 10
}
```

---

### Test 2: Get Specific Threat Details
**Purpose:** Retrieve details for a specific threat

```bash
curl http://localhost:8000/governance/threats/T2_METADATA_POISONING
```

**Expected Response:**
```json
{
  "threat_id": "T2_METADATA_POISONING",
  "severity": "CRITICAL",
  "description": "False provenance metadata",
  "patterns": ["forged_owner", "backdated_timestamp", "invalid_integration"]
}
```

---

### Test 3: Scan for Threats (Clean Data)
**Purpose:** Verify clean data passes threat scan

```bash
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "valid_owner_123",
    "product_id": "AI_Assistant",
    "artifact_type": "metadata",
    "timestamp": "2026-01-20T10:00:00Z"
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

### Test 4: Detect Metadata Poisoning
**Purpose:** Verify forged owner_id is detected

```bash
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "",
    "product_id": "AI_Assistant",
    "artifact_type": "metadata"
  }'
```

**Expected Response:**
```json
{
  "threats_detected": 1,
  "has_critical_threats": true,
  "threats": [
    {
      "threat_id": "T2_METADATA_POISONING",
      "name": "Metadata Poisoning",
      "level": "critical",
      "pattern_matched": "forged_owner",
      "description": "Invalid or forged owner_id detected"
    }
  ],
  "recommendation": "BLOCK"
}
```

---

### Test 5: Detect Backdated Timestamp
**Purpose:** Verify backdated timestamps are caught

```bash
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "valid_owner_123",
    "timestamp": "2020-01-01T00:00:00Z"
  }'
```

**Expected Response:**
```json
{
  "threats_detected": 1,
  "has_critical_threats": true,
  "threats": [
    {
      "threat_id": "T2_METADATA_POISONING",
      "name": "Backdated Timestamp",
      "level": "critical",
      "pattern_matched": "backdated_timestamp"
    }
  ],
  "recommendation": "BLOCK"
}
```

---

### Test 6: Detect Large Artifact Warning
**Purpose:** Verify large artifacts trigger warning

```bash
curl -X POST "http://localhost:8000/governance/threats/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "valid_owner_123",
    "large_data": "'$(python -c 'print("x" * 11000000)')''"
  }'
```

**Expected Response:**
```json
{
  "threats_detected": 1,
  "has_critical_threats": false,
  "threats": [
    {
      "threat_id": "T1_STORAGE_EXHAUSTION",
      "name": "Large Artifact Warning",
      "level": "medium",
      "pattern_matched": "large_artifacts"
    }
  ],
  "recommendation": "ALLOW"
}
```

---

### Test 7: Find Threats by Pattern
**Purpose:** Search threats by detection pattern

```bash
curl "http://localhost:8000/governance/threats/pattern/forged_owner"
```

**Expected Response:**
```json
{
  "pattern": "forged_owner",
  "matching_threats": [
    {
      "threat_id": "T2_METADATA_POISONING",
      "severity": "CRITICAL",
      "description": "False provenance metadata",
      "pattern": "forged_owner"
    }
  ],
  "count": 1
}
```

---

## 🔧 PYTHON TESTING

### Test Script
```python
import requests

BASE_URL = "http://localhost:8000"

def test_threat_validator():
    # Test 1: Get all threats
    response = requests.get(f"{BASE_URL}/governance/threats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_threats"] == 10
    print("✅ Test 1 passed: All threats retrieved")
    
    # Test 2: Scan clean data
    clean_data = {
        "owner_id": "valid_owner_123",
        "product_id": "AI_Assistant",
        "artifact_type": "metadata"
    }
    response = requests.post(f"{BASE_URL}/governance/threats/scan", json=clean_data)
    assert response.status_code == 200
    data = response.json()
    assert data["threats_detected"] == 0
    print("✅ Test 2 passed: Clean data accepted")
    
    # Test 3: Detect metadata poisoning
    poisoned_data = {
        "owner_id": "",
        "product_id": "AI_Assistant"
    }
    response = requests.post(f"{BASE_URL}/governance/threats/scan", json=poisoned_data)
    assert response.status_code == 200
    data = response.json()
    assert data["has_critical_threats"] == True
    print("✅ Test 3 passed: Metadata poisoning detected")
    
    print("\n🎉 All threat validator tests passed!")

if __name__ == "__main__":
    test_threat_validator()
```

---

## ✅ VALIDATION CHECKLIST

- [ ] All 10 threats are registered
- [ ] Clean data passes threat scan
- [ ] Forged owner_id is detected
- [ ] Backdated timestamps are caught
- [ ] Large artifacts trigger warnings
- [ ] Pattern search works correctly
- [ ] Critical threats block operations
- [ ] Non-critical threats allow with warning

---

## 📊 EXPECTED RESULTS

### Threat Detection Summary
- **T1 (Storage Exhaustion):** Detects large artifacts (>10MB)
- **T2 (Metadata Poisoning):** Detects invalid owner_id, backdated timestamps
- **T3 (Schema Evolution):** Detects suspicious nested structures
- **T7 (Cross-Product):** Detects product/artifact mismatches
- **All Others:** Documented but require integration-specific detection

---

## 🚨 TROUBLESHOOTING

### Issue: Threats not detected
**Solution:** Ensure threat_validator.py is imported correctly in governance_gate.py

### Issue: False positives
**Solution:** Adjust detection thresholds in threat_validator.py

### Issue: Missing threats
**Solution:** Verify all 10 threats are defined in THREATS dictionary

---

**END OF THREAT VALIDATOR TEST GUIDE**

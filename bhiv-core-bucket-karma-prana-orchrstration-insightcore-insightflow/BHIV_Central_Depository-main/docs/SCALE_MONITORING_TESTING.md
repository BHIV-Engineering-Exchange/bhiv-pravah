# 🧪 SCALE MONITORING TESTING GUIDE

**Quick Reference for Testing Scale Readiness Implementation**

---

## ✅ QUICK VERIFICATION (Copy-Paste Ready)

### 1. Check Scale Status Dashboard
```bash
curl http://localhost:8000/metrics/scale-status
```

**Expected Response:**
```json
{
  "timestamp": "2026-01-19T...",
  "concurrent_writes": {"current": 0, "limit": 100, "status": "GREEN"},
  "storage": {"status": "HEALTHY", "usage_percent": 0},
  "write_throughput": {"current_writes_per_sec": 0, "status": "GREEN"},
  "query_performance": {"p99_ms": 0, "sla_status": "NO_DATA"}
}
```

### 2. Check Storage Capacity (Simulate 75% Usage)
```bash
curl "http://localhost:8000/metrics/storage-capacity?used_gb=750"
```

**Expected Response:**
```json
{
  "status": "WARNING",
  "usage_percent": 75.0,
  "used_gb": 750,
  "total_gb": 1000,
  "free_gb": 250,
  "action_required": "PLAN_EXPANSION",
  "escalation_path": "Ops_Team",
  "response_timeline": "6_HOURS"
}
```

### 3. Check Storage Capacity (Simulate 95% Usage - Critical)
```bash
curl "http://localhost:8000/metrics/storage-capacity?used_gb=950"
```

**Expected Response:**
```json
{
  "status": "CRITICAL",
  "usage_percent": 95.0,
  "action_required": "HALT_WRITES",
  "escalation_path": "Ashmit_Pandey_and_Ops",
  "response_timeline": "IMMEDIATE"
}
```

### 4. Get Scale Certification
```bash
curl http://localhost:8000/governance/scale/certification
```

### 5. Check What Scales Safely
```bash
curl http://localhost:8000/governance/scale/what-scales-safely
```

### 6. Check What Does NOT Scale
```bash
curl http://localhost:8000/governance/scale/what-does-not-scale
```

### 7. Check Never Assume List
```bash
curl http://localhost:8000/governance/scale/never-assume
```

### 8. Get Scale Thresholds
```bash
curl http://localhost:8000/governance/scale/thresholds
```

### 9. Check Active Alerts
```bash
curl http://localhost:8000/metrics/alerts
```

### 10. Validate Scale Operation
```bash
curl -X POST "http://localhost:8000/governance/scale/validate?operation_type=write&data_size=10485760&frequency=50"
```

---

## 🎯 COMPREHENSIVE TEST SCENARIOS

### Scenario 1: Normal Operations (All Green)
```bash
# Check status - should be all GREEN
curl http://localhost:8000/metrics/scale-status

# Verify no alerts
curl http://localhost:8000/metrics/alerts
```

**Expected:** All metrics GREEN, no alerts

### Scenario 2: Storage Warning (70% capacity)
```bash
# Simulate 70% storage usage
curl "http://localhost:8000/metrics/storage-capacity?used_gb=700"
```

**Expected:**
- Status: WARNING
- Escalation: Ops_Team
- Timeline: 6_HOURS
- Action: PLAN_EXPANSION

### Scenario 3: Storage Critical (99% capacity)
```bash
# Simulate 99% storage usage
curl "http://localhost:8000/metrics/storage-capacity?used_gb=990"
```

**Expected:**
- Status: CRITICAL
- Escalation: Ashmit_Pandey_and_Ops
- Timeline: IMMEDIATE
- Action: HALT_WRITES

### Scenario 4: Validate Large Artifact
```bash
# Try to validate 600 MB artifact (exceeds 500 MB limit)
curl -X POST "http://localhost:8000/governance/scale/validate?operation_type=write&data_size=629145600&frequency=1"
```

**Expected:** 400 error - exceeds artifact size limit

### Scenario 5: Validate High Write Rate
```bash
# Try to validate 1500 writes/sec (exceeds 1000 limit)
curl -X POST "http://localhost:8000/governance/scale/validate?operation_type=write&data_size=1048576&frequency=1500"
```

**Expected:** 400 error - exceeds write throughput limit

### Scenario 6: Check Limit Proximity
```bash
# Check how close to concurrent writes limit
curl "http://localhost:8000/governance/scale/proximity/concurrent_writes?current_value=85"
```

**Expected:**
- Status: CRITICAL (85/100 = 85%)
- Remaining: 15 writers

---

## 🔍 INTEGRATION WITH EXISTING ENDPOINTS

### Verify Backward Compatibility

**1. Health Check Still Works:**
```bash
curl http://localhost:8000/health
```

**2. Agents Still Work:**
```bash
curl http://localhost:8000/agents
```

**3. Baskets Still Work:**
```bash
curl http://localhost:8000/baskets
```

**4. Run Basket Still Works:**
```bash
curl -X POST http://localhost:8000/run-basket \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "working_test"}'
```

**5. Governance Endpoints Still Work:**
```bash
curl http://localhost:8000/governance/info
curl http://localhost:8000/governance/threats
curl http://localhost:8000/governance/gate/status
```

---

## 📊 POSTMAN COLLECTION

### Import These Requests:

**Collection Name:** Scale Monitoring Tests

**Request 1: Scale Status Dashboard**
- Method: GET
- URL: `http://localhost:8000/metrics/scale-status`

**Request 2: Storage Warning Test**
- Method: GET
- URL: `http://localhost:8000/metrics/storage-capacity?used_gb=750`

**Request 3: Storage Critical Test**
- Method: GET
- URL: `http://localhost:8000/metrics/storage-capacity?used_gb=990`

**Request 4: Scale Certification**
- Method: GET
- URL: `http://localhost:8000/governance/scale/certification`

**Request 5: What Scales Safely**
- Method: GET
- URL: `http://localhost:8000/governance/scale/what-scales-safely`

**Request 6: What Does NOT Scale**
- Method: GET
- URL: `http://localhost:8000/governance/scale/what-does-not-scale`

**Request 7: Never Assume**
- Method: GET
- URL: `http://localhost:8000/governance/scale/never-assume`

**Request 8: Scale Thresholds**
- Method: GET
- URL: `http://localhost:8000/governance/scale/thresholds`

**Request 9: Active Alerts**
- Method: GET
- URL: `http://localhost:8000/metrics/alerts`

**Request 10: Validate Operation**
- Method: POST
- URL: `http://localhost:8000/governance/scale/validate?operation_type=write&data_size=10485760&frequency=50`

---

## ✅ SUCCESS CRITERIA

After running all tests, verify:

- ✅ All endpoints return 200 OK (except validation failures)
- ✅ Storage thresholds trigger correct escalation paths
- ✅ Scale certification shows ENTERPRISE_SCALE_READY
- ✅ All existing endpoints still work (backward compatibility)
- ✅ Alerts are generated for threshold breaches
- ✅ Graceful degradation messages are clear

---

## 🚨 EXPECTED ALERTS

### Storage at 70%
```json
{
  "type": "STORAGE_CAPACITY",
  "severity": "WARNING",
  "message": "Storage at 70.0%",
  "escalation_path": "Ops_Team",
  "response_timeline": "6_HOURS"
}
```

### Storage at 99%
```json
{
  "type": "STORAGE_CAPACITY",
  "severity": "CRITICAL",
  "message": "Storage at 99.0%",
  "escalation_path": "Ashmit_Pandey_and_Ops",
  "response_timeline": "IMMEDIATE"
}
```

### Concurrent Writes at 80
```json
{
  "type": "CONCURRENT_WRITES",
  "severity": "ORANGE",
  "message": "CONCURRENT_WRITES_APPROACHING_LIMIT"
}
```

---

## 📝 TESTING CHECKLIST

- [ ] Scale status dashboard returns complete metrics
- [ ] Storage capacity thresholds work (70%, 90%, 99%)
- [ ] Concurrent writes tracking works
- [ ] Query performance metrics work
- [ ] Alerts are generated correctly
- [ ] Escalation paths are defined
- [ ] Scale certification is ENTERPRISE_SCALE_READY
- [ ] What scales safely list is complete
- [ ] What does NOT scale list is complete
- [ ] Never assume list is complete
- [ ] All existing endpoints still work
- [ ] No breaking changes detected

---

**END OF TESTING GUIDE**

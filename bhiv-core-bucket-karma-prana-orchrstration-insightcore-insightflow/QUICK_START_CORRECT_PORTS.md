# 🚀 Quick Start Guide - Correct Port Allocation

## ⚠️ IMPORTANT: Port Allocation

```
Karma:             Port 8000
Bucket:            Port 8001
Core:              Port 8002
Workflow Executor: Port 8003
```

**NO PORT CONFLICTS** - Each service has its own port!

---

## 🔧 Start Services (Correct Order)

### Terminal 1: Karma (Port 8000)
```bash
cd karma_chain_v2-main
python main.py
```
✅ Wait for: "Application startup complete"  
✅ Verify: http://localhost:8000/health

### Terminal 2: Bucket (Port 8001)
```bash
cd BHIV_Central_Depository-main
python main.py
```
✅ Wait for: "Application startup complete"  
✅ Verify: http://localhost:8001/health

### Terminal 3: Core (Port 8002)
```bash
cd v1-BHIV_CORE-main
python mcp_bridge.py
```
✅ Wait for: "Uvicorn running on http://0.0.0.0:8002"  
✅ Verify: http://localhost:8002/health

### Terminal 4: Workflow Executor (Port 8003)
```bash
cd workflow-executor-main
uvicorn main:app --host 0.0.0.0 --port 8003
```
**OR use the startup script:**
```bash
cd workflow-executor-main
start_workflow_executor.bat
```
✅ Wait for: "Application startup complete"  
✅ Verify: http://localhost:8003/healthz

---

## ✅ Verify Integration

```bash
# Run port verification test
python test_port_verification.py
```

**Expected**: 6/6 tests passing (100%)

---

## 🔍 Quick Health Check

```bash
# Check all services
curl http://localhost:8000/health  # Karma
curl http://localhost:8001/health  # Bucket
curl http://localhost:8002/health  # Core
curl http://localhost:8003/healthz # Workflow Executor
```

All should return `{"status": "healthy"}` or `{"status": "ok"}`

---

## 🎯 Test Workflow Execution

```bash
curl -X POST "http://localhost:8003/api/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "test_123",
    "decision": "workflow",
    "data": {
      "workflow_type": "workflow",
      "payload": {
        "action_type": "task",
        "user_id": "test_user",
        "title": "Test Task"
      }
    }
  }'
```

**Expected**: `{"trace_id": "test_123", "status": "success", ...}`

---

## 🐛 Troubleshooting

### Issue: Port already in use
**Solution**: 
```bash
# Windows
netstat -ano | findstr :8003
taskkill /PID <PID> /F

# Then restart Workflow Executor on port 8003
```

### Issue: Workflow Executor on wrong port
**Solution**:
```bash
# Always specify port 8003
uvicorn main:app --host 0.0.0.0 --port 8003
```

### Issue: Services can't communicate
**Solution**: Verify all services are running on correct ports:
```bash
python test_port_verification.py
```

---

## 📊 Port Allocation Reference

| Service            | Port | Health Check                    |
|--------------------|------|---------------------------------|
| Karma              | 8000 | http://localhost:8000/health    |
| Bucket             | 8001 | http://localhost:8001/health    |
| Core               | 8002 | http://localhost:8002/health    |
| Workflow Executor  | 8003 | http://localhost:8003/healthz   |

---

## ✅ Success Indicators

- [x] All 4 services start without errors
- [x] Each service on its own port (no conflicts)
- [x] All health checks return healthy
- [x] Workflow execution works
- [x] Events logged in Bucket
- [x] Behavior tracked in Karma
- [x] test_port_verification.py passes 6/6 tests

---

**Status**: ✅ Port allocation corrected - No conflicts!

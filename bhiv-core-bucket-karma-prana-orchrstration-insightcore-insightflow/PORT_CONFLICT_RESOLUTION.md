# 🚨 PORT CONFLICT RESOLUTION

## Current Problem
Workflow Executor is running on port 8000 (Karma's port), showing Workflow endpoints instead of Karma endpoints.

## Root Cause
Multiple instances of Workflow Executor were started on port 8000 instead of port 8003.

---

## ✅ SOLUTION (Follow These Steps)

### Step 1: Stop ALL Services
Run the cleanup script:
```bash
CLEANUP_AND_RESTART.bat
```

OR manually close all terminal windows running:
- Karma (python main.py)
- Bucket (python main.py)
- Core (python mcp_bridge.py)
- Workflow Executor (python main.py or uvicorn)

### Step 2: Verify Ports Are Free
```bash
netstat -ano | findstr ":8000 :8001 :8002 :8003"
```
Should return NOTHING or only TIME_WAIT entries.

### Step 3: Start Services in Correct Order

**Terminal 1 - Karma (Port 8000)**
```bash
cd karma_chain_v2-main
python main.py
```
Wait for: "Application startup complete"

**Terminal 2 - Bucket (Port 8001)**
```bash
cd BHIV_Central_Depository-main
python main.py
```
Wait for: "Application startup complete"

**Terminal 3 - Core (Port 8002)**
```bash
cd v1-BHIV_CORE-main
python mcp_bridge.py
```
Wait for: "Uvicorn running on http://0.0.0.0:8002"

**Terminal 4 - Workflow Executor (Port 8003)**
```bash
cd workflow-executor-main
python main.py
```
Wait for: "Uvicorn running on http://0.0.0.0:8003"

### Step 4: Verify Correct Services
```bash
python verify_services.py
```

This will check each port and tell you which service is actually running.

---

## 🔍 How to Verify Manually

### Check Port 8000 (Should be Karma)
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy"}`

Visit: http://localhost:8000/docs
Expected: Should show "KarmaChain v2" endpoints

### Check Port 8003 (Should be Workflow Executor)
```bash
curl http://localhost:8003/healthz
```
Expected: `{"status": "ok", "service": "workflow-executor"}`

Visit: http://localhost:8003/docs
Expected: Should show "Workflow Executor" endpoints

---

## ⚠️ Common Mistakes to Avoid

❌ Starting Workflow Executor with: `uvicorn main:app --reload`
✅ Always use: `python main.py` OR `uvicorn main:app --port 8003 --reload`

❌ Starting services in wrong order
✅ Always: Karma → Bucket → Core → Workflow

❌ Not waiting for "startup complete" messages
✅ Wait 5-10 seconds between each service

❌ Having multiple terminal windows running the same service
✅ One terminal per service only

---

## 🎯 Expected Final State

```
Port 8000: Karma (KarmaChain v2)
  - Endpoints: /health, /v1/event/, /api/v1/karma/{user_id}
  
Port 8001: Bucket (BHIV Central Depository)
  - Endpoints: /health, /core/events, /bucket/prana/stats
  
Port 8002: Core (BHIV Core)
  - Endpoints: /health, /handle_task, /query-kb
  
Port 8003: Workflow Executor
  - Endpoints: /healthz, /api/workflow/execute
```

---

## 🆘 If Still Not Working

1. Restart your computer (clears all port locks)
2. Check Windows Firewall isn't blocking ports
3. Check antivirus isn't interfering
4. Run `netstat -ano | findstr "8000"` to find rogue processes
5. Manually kill processes: `taskkill /F /PID <process_id>`

---

**After following these steps, port 8000 should show Karma endpoints, not Workflow endpoints!**

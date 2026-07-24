# ✅ PORT 8000 IS NOW FREE - START SERVICES

## What I Just Did:
✅ Killed all Python processes (PIDs: 24732, 25072, 20272)  
✅ Port 8000 is now completely free  
✅ Ready to start services in correct order  

---

## 🚀 START SERVICES NOW

### Option 1: Automated (Recommended)
Double-click this file:
```
START_ALL_SERVICES.bat
```

This will open 4 terminal windows automatically:
- Terminal 1: Karma (Port 8000)
- Terminal 2: Bucket (Port 8001)
- Terminal 3: Core (Port 8002)
- Terminal 4: Workflow (Port 8003)

### Option 2: Manual

**Terminal 1:**
```bash
cd karma_chain_v2-main
python main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 2:**
```bash
cd BHIV_Central_Depository-main
python main.py
```

**Terminal 3:**
```bash
cd v1-BHIV_CORE-main
python mcp_bridge.py
```

**Terminal 4:**
```bash
cd workflow-executor-main
python main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8003`

---

## ✅ VERIFY IT WORKED

### Check Port 8000 (Should be Karma):
Open browser: **http://localhost:8000/docs**

**Expected**: 
```
KarmaChain v2 (Dual-Ledger)
 1.0.0
A modular, portable karma tracking system
```

**NOT**:
```
Workflow Executor  ← If you see this, something went wrong!
```

### Check Port 8003 (Should be Workflow):
Open browser: **http://localhost:8003/docs**

**Expected**:
```
Workflow Executor
 1.0.0
Deterministic execution layer
```

---

## 🎯 Quick Test Commands

```bash
# Should return Karma health
curl http://localhost:8000/health

# Should return Workflow health
curl http://localhost:8003/healthz
```

---

## IF YOU SEE WORKFLOW ON PORT 8000 AGAIN

It means you started Workflow Executor BEFORE Karma. 

**Solution**: Close all terminals and start again in correct order:
1. Karma FIRST (port 8000)
2. Workflow LAST (port 8003)

---

**Port 8000 is free. Now start the services!** 🚀

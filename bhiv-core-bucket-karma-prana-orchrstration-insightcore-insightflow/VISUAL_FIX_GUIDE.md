# 🎯 VISUAL GUIDE - What's Wrong and How to Fix

## CURRENT STATE (WRONG) ❌

```
Port 8000: Workflow Executor ❌ WRONG!
  └─ Shows: "Workflow Executor" at /docs
  └─ Endpoints: /healthz, /api/workflow/execute

Port 8001: Bucket ✅
Port 8002: Core ✅  
Port 8003: (empty or duplicate Workflow) ❌
```

**Problem**: Workflow Executor started on port 8000 instead of 8003

---

## DESIRED STATE (CORRECT) ✅

```
Port 8000: Karma ✅ CORRECT!
  └─ Shows: "KarmaChain v2" at /docs
  └─ Endpoints: /health, /v1/event/, /api/v1/karma/{user_id}

Port 8001: Bucket ✅
  └─ Shows: "BHIV Central Depository" at /docs

Port 8002: Core ✅
  └─ Shows: "BHIV Core" at /docs

Port 8003: Workflow Executor ✅ CORRECT!
  └─ Shows: "Workflow Executor" at /docs
  └─ Endpoints: /healthz, /api/workflow/execute
```

---

## HOW TO FIX (3 STEPS)

### 1️⃣ STOP EVERYTHING

Look at your screen. You have terminal windows open like this:

```
Terminal 1: (.venv) C:\...\workflow-executor-main> uvicorn main:app --reload
            INFO: Uvicorn running on http://127.0.0.1:8000  ← THIS IS THE PROBLEM!

Terminal 2: C:\...\karma_chain_v2-main> python main.py
            (might not be running or failed to start)

Terminal 3: (other services)
```

**ACTION**: 
- Press CTRL+C in Terminal 1 (Workflow Executor)
- Close ALL Python terminal windows
- Open Task Manager → End all "Python" processes

---

### 2️⃣ START KARMA FIRST

Open a **NEW** terminal:

```bash
cd karma_chain_v2-main
python main.py
```

**WAIT FOR THIS MESSAGE**:
```
INFO: Uvicorn running on http://0.0.0.0:8000  ← Port 8000!
INFO: Application startup complete.
```

**VERIFY IN BROWSER**: http://localhost:8000/docs

**YOU SHOULD SEE**:
```
KarmaChain v2 (Dual-Ledger)
 1.0.0
A modular, portable karma tracking system
```

**NOT**:
```
Workflow Executor  ← If you see this, Karma didn't start!
```

---

### 3️⃣ START WORKFLOW EXECUTOR LAST

After Karma is confirmed on port 8000, open another terminal:

```bash
cd workflow-executor-main
python main.py
```

**WAIT FOR THIS MESSAGE**:
```
INFO: Uvicorn running on http://0.0.0.0:8003  ← Port 8003!
```

**VERIFY IN BROWSER**: http://localhost:8003/docs

**YOU SHOULD SEE**:
```
Workflow Executor
 1.0.0
Deterministic execution layer
```

---

## QUICK TEST

After fixing, run these commands:

```bash
# Should show Karma
curl http://localhost:8000/health

# Should show Workflow
curl http://localhost:8003/healthz
```

---

## WHY THIS HAPPENED

You ran this command:
```bash
uvicorn main:app --reload
```

This defaults to port 8000. You should have run:
```bash
python main.py  ← Uses port 8003 automatically
```

OR

```bash
uvicorn main:app --port 8003 --reload  ← Explicit port
```

---

## REMEMBER

✅ **Karma = Port 8000** (starts first)  
✅ **Workflow = Port 8003** (starts last)  
✅ **Always use `python main.py` for Workflow Executor**  
❌ **Never use `uvicorn main:app --reload` without `--port 8003`**

---

**Follow FIX_NOW.md for detailed step-by-step instructions!**

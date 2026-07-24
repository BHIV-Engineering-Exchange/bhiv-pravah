# ⚠️ WORKFLOW EXECUTOR - CORRECT STARTUP

## ❌ WRONG (Uses port 8000 - conflicts with Karma)
```bash
uvicorn main:app --reload
```

## ✅ CORRECT (Uses port 8003)

### Option 1: Python Direct (Easiest)
```bash
python main.py
```

### Option 2: Uvicorn with Port
```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### Option 3: Batch Script
```bash
start_correct_port.bat
```

---

## Verify Correct Port

After starting, you should see:
```
INFO: Uvicorn running on http://0.0.0.0:8003
```

NOT:
```
INFO: Uvicorn running on http://127.0.0.1:8000  ❌ WRONG!
```

---

## Quick Test
```bash
curl http://localhost:8003/healthz
```

Expected response:
```json
{
  "status": "ok",
  "service": "workflow-executor",
  "environment": "development"
}
```

---

## Port Allocation Reference
- 8000 = Karma (Q-learning)
- 8001 = Bucket (Governance)
- 8002 = Core (AI Engine)
- 8003 = Workflow Executor ← YOU ARE HERE

---

**Remember**: ALWAYS specify port 8003 or use `python main.py`

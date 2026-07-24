# 🚀 QUICK START - Correct Port Allocation

## Port Map (MEMORIZE THIS!)
```
8000 → Karma (Q-learning behavioral tracking)
8001 → Bucket (Constitutional governance + audit)
8002 → Core (AI decision engine + RL)
8003 → Workflow (Deterministic execution layer)
```

---

## Startup Commands (Copy-Paste Ready)

### Terminal 1 - Karma
```bash
cd karma_chain_v2-main
python main.py
```
**Wait for**: "Application startup complete"  
**Check**: http://localhost:8000/health

---

### Terminal 2 - Bucket
```bash
cd BHIV_Central_Depository-main
python main.py
```
**Wait for**: "Application startup complete"  
**Check**: http://localhost:8001/health

---

### Terminal 3 - Core
```bash
cd v1-BHIV_CORE-main
python mcp_bridge.py
```
**Wait for**: "Uvicorn running on http://0.0.0.0:8002"  
**Check**: http://localhost:8002/health

---

### Terminal 4 - Workflow Executor
```bash
cd workflow-executor-main
start_correct_port.bat
```
**Wait for**: "Application startup complete"  
**Check**: http://localhost:8003/healthz

---

## One-Line Verification
```bash
curl http://localhost:8000/health && curl http://localhost:8001/health && curl http://localhost:8002/health && curl http://localhost:8003/healthz
```

---

## Integration Test
```bash
python test_port_verification.py
```
**Expected**: 6/6 tests passing (100%)

---

## Common Mistakes (AVOID!)

❌ Starting Workflow Executor with `uvicorn main:app --reload` (uses port 8000)  
✅ Use `start_correct_port.bat` or `uvicorn main:app --port 8003 --reload`

❌ Starting services in wrong order  
✅ Always: Karma → Bucket → Core → Workflow

❌ Not waiting for "startup complete" messages  
✅ Wait 5-10 seconds between each service

---

## Troubleshooting

**Port already in use?**
```bash
# Windows - Find process using port
netstat -ano | findstr "8000"
# Kill process
taskkill /PID <process_id> /F
```

**Service won't start?**
1. Check .env files exist
2. Check MongoDB/Redis credentials
3. Check Python dependencies installed
4. Check no other services on same port

**Integration test fails?**
1. Verify all 4 services running
2. Check health endpoints individually
3. Restart services in correct order
4. Check firewall/antivirus not blocking

---

**Last Updated**: 2026-01-31  
**Status**: Production Ready ✅

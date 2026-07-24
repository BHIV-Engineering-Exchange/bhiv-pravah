# 🚀 Quick Testing Reference Card

## 1️⃣ Start All Services (Copy-Paste Ready)

```bash
# Terminal 1
cd karma_chain_v2-main && python main.py

# Terminal 2
cd BHIV_Central_Depository-main && python main.py

# Terminal 3
cd v1-BHIV_CORE-main && python mcp_bridge.py

# Terminal 4
cd workflow-executor-main && python main.py

# Terminal 5
cd "Unified Action Orchestration" && python action_orchestrator.py

# Terminal 6
cd insightcore-bridgev4x-main && python insight_service.py

# Terminal 7
cd Insight_Flow-main && start_bridge_standalone.bat
```

---

## 2️⃣ Quick Health Check (One Command)

```bash
curl http://localhost:8000/health && curl http://localhost:8001/health && curl http://localhost:8002/health && curl http://localhost:8003/healthz && curl http://localhost:8005/health && curl http://localhost:8006/health
```

---

## 3️⃣ Send Test Task

```bash
curl -X POST http://localhost:8002/handle_task -H "Content-Type: application/json" -d "{\"agent\":\"edumentor_agent\",\"input\":\"What is AI?\",\"input_type\":\"text\"}"
```

---

## 4️⃣ Check Results

```bash
# Bucket events
curl http://localhost:8001/core/events

# Bucket stats
curl http://localhost:8001/core/stats

# Karma data
curl http://localhost:8000/api/v1/karma/system
```

---

## 5️⃣ Send PRANA Packet

```bash
curl -X POST http://localhost:8001/bucket/prana/ingest -H "Content-Type: application/json" -d "{\"user_id\":\"test_user\",\"session_id\":\"session1\",\"lesson_id\":\"lesson1\",\"system_type\":\"gurukul\",\"role\":\"student\",\"timestamp\":\"2026-02-02T10:00:00Z\",\"cognitive_state\":\"DEEP_FOCUS\",\"active_seconds\":4.5,\"idle_seconds\":0.5,\"away_seconds\":0,\"focus_score\":95,\"raw_signals\":{\"mouse_velocity\":150,\"scroll_depth\":75,\"keystroke_count\":45,\"window_focus\":true,\"tab_visible\":true}}"
```

---

## 6️⃣ Check PRANA Results

```bash
# PRANA stats
curl http://localhost:8001/bucket/prana/stats

# User history
curl http://localhost:8001/bucket/prana/user/test_user

# Karma for user
curl http://localhost:8000/api/v1/karma/test_user
```

---

## 7️⃣ Test Security

```bash
python test_insight_security.py
```

---

## 8️⃣ View Logs

```bash
# Core
tail -f v1-BHIV_CORE-main/logs/agent_logs.json

# Bucket
tail -f BHIV_Central_Depository-main/logs/application.log

# Karma
tail -f karma_chain_v2-main/logs/api.log

# UAO
tail -f "Unified Action Orchestration/lifecycle.log"
```

---

## 🎯 Expected Results Summary

| Test | Endpoint | Expected |
|------|----------|----------|
| Health | All services | `{"status": "healthy"}` |
| Task | Core → Bucket | Event in `/core/events` |
| Task | Bucket → Karma | Karma score updated |
| PRANA | Bucket stats | `packets_received > 0` |
| PRANA | User history | Analytics calculated |
| PRANA | Karma | User karma updated |
| Security | Valid request | `ALLOW` |
| Security | Replay | `REPLAY_DETECTED` |

---

## 🔍 Troubleshooting Quick Fixes

**Service won't start:**
```bash
# Check if port is in use
netstat -ano | findstr :8000
netstat -ano | findstr :8001
netstat -ano | findstr :8002
```

**No events in Bucket:**
```bash
# Restart Bucket
cd BHIV_Central_Depository-main
python main.py
```

**Karma not updating:**
```bash
# Check Karma health
curl http://localhost:8000/health

# Check MongoDB connection in logs
tail -f karma_chain_v2-main/logs/api.log
```

---

## ✅ Success Checklist

```
□ All 8 services running
□ All health checks pass
□ Task processed by Core
□ Event visible in Bucket
□ Karma score updated
□ PRANA packet ingested
□ PRANA in Bucket stats
□ User PRANA history shows data
□ Security test passes 4/4
□ Logs showing activity
```

**When all checked: System is working! 🎉**

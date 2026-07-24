# UAO Quick Start Guide

**Port**: 8004  
**Purpose**: Action orchestration & lifecycle management  
**Integration**: Fire-and-forget to Bucket (8001) + Karma (8000)

---

## 🚀 Start UAO

```bash
cd "Unified Action Orchestration"
python action_orchestrator.py
```

✅ **Expected**: `Uvicorn running on http://0.0.0.0:8004`

---

## 🧪 Test UAO

### 1. Send Action Request
```bash
curl -X POST "http://localhost:8004/api/assistant" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "test_001",
    "action_type": "SEND_MESSAGE",
    "payload": {
      "user_id": "user123",
      "to": "+1234567890",
      "text": "Hello from UAO"
    }
  }'
```

✅ **Expected**: `{"status": "accepted", "action_id": "test_001"}`

### 2. Report Execution Result
```bash
curl -X POST "http://localhost:8004/api/execution_result" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "test_001",
    "success": true
  }'
```

✅ **Expected**: `{"status": "updated"}`

### 3. Check Bucket Received Events
```bash
curl http://localhost:8001/core/events | grep unified_action_orchestrator
```

✅ **Expected**: Events with `requester_id: "unified_action_orchestrator"`

---

## 📊 Action Types

- `SEND_MESSAGE` - Send message via communication channel
- `FETCH_MESSAGES` - Retrieve messages from channel
- `SCHEDULE_MESSAGE` - Schedule message for future delivery

---

## 🔄 Action States

1. **requested** - Action received, awaiting execution
2. **executing** - Action in progress
3. **completed** - Action succeeded
4. **failed** - Action failed with error

---

## 🔌 Integration Points

### UAO → Bucket
- **Endpoint**: `POST /core/write-event`
- **Requester**: `unified_action_orchestrator`
- **Timeout**: 2s (fire-and-forget)

### UAO → Karma
- **Endpoint**: `POST /v1/event/`
- **Source**: `unified_action_orchestrator`
- **Timeout**: 2s (fire-and-forget)

---

## 🧪 Run Integration Tests

```bash
python test_uao_integration.py
```

✅ **Expected**: 5/5 tests passing (100%)

---

## 📝 Logs

UAO logs lifecycle events to `lifecycle.log`:
```bash
tail -f "Unified Action Orchestration/lifecycle.log"
```

---

## 🎯 Quick Verification

```bash
# 1. Check UAO is running
curl http://localhost:8004/docs

# 2. Send test action
curl -X POST "http://localhost:8004/api/assistant" \
  -H "Content-Type: application/json" \
  -d '{"action_id":"quick_test","action_type":"SEND_MESSAGE","payload":{"user_id":"test"}}'

# 3. Check Bucket received it
curl http://localhost:8001/core/events?limit=5

# 4. Check logs
tail -n 20 "Unified Action Orchestration/lifecycle.log"
```

---

## ✅ Success Indicators

- ✅ UAO starts on port 8004
- ✅ Actions accepted and state transitions work
- ✅ Commands emitted to logs
- ✅ Bucket receives orchestration events
- ✅ Karma receives behavioral events
- ✅ Fire-and-forget pattern operational

---

**Status**: ✅ **PRODUCTION READY**  
**Documentation**: See `UAO_INTEGRATION_COMPLETE.md` for full details

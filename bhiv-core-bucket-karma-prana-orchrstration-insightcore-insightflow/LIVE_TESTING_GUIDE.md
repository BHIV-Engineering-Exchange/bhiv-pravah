# 🧪 Live End-to-End Testing Guide

**Purpose**: Test complete data flow through all 8 services  
**Duration**: 15-20 minutes  
**Status**: Production Ready Testing

---

## 📋 Prerequisites Checklist

Before starting, ensure all services are running:

```bash
# Terminal 1: Karma (8000)
cd karma_chain_v2-main
python main.py

# Terminal 2: Bucket (8001)
cd BHIV_Central_Depository-main
python main.py

# Terminal 3: Core (8002)
cd v1-BHIV_CORE-main
python mcp_bridge.py

# Terminal 4: Workflow (8003)
cd workflow-executor-main
python main.py

# Terminal 5: UAO (8004)
cd "Unified Action Orchestration"
python action_orchestrator.py

# Terminal 6: Insight Core (8005)
cd insightcore-bridgev4x-main
python insight_service.py

# Terminal 7: Insight Flow Bridge (8006)
cd Insight_Flow-main
start_bridge_standalone.bat
```

---

## 🎯 Test Scenario 1: Core Task Processing Flow

### Step 1: Send a Task to Core

```bash
curl -X POST "http://localhost:8002/handle_task" \
  -H "Content-Type: application/json" \
  -d "{\"agent\": \"edumentor_agent\", \"input\": \"Explain quantum computing in simple terms\", \"input_type\": \"text\"}"
```

**Expected Response** (2-5 seconds):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "agent_output": {
    "response": "Quantum computing is...",
    "status": 200,
    "model": "gpt-4",
    "processing_time": 2.34
  },
  "status": "success"
}
```

**What Happened Behind the Scenes:**
1. ✅ Core received request
2. ✅ RL agent selector chose best agent (UCB algorithm)
3. ✅ Agent executed task
4. ✅ Core logged to MongoDB
5. ✅ Core sent event to Bucket (fire-and-forget)
6. ✅ Bucket forwarded to Karma (async)

---

### Step 2: Verify Data in Bucket

```bash
# Check Core events in Bucket
curl "http://localhost:8001/core/events?limit=5"
```

**Expected Response:**
```json
{
  "events": [
    {
      "timestamp": "2026-02-02T10:30:45.123456Z",
      "requester_id": "bhiv_core",
      "event_type": "agent_result",
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "agent_id": "edumentor_agent",
      "result": {
        "status": 200,
        "processing_time": 2.34
      }
    }
  ],
  "count": 1,
  "showing": 1
}
```

**Verification Points:**
- ✅ Event has correct timestamp
- ✅ Requester is "bhiv_core"
- ✅ Task ID matches your request
- ✅ Agent ID is "edumentor_agent"

---

### Step 3: Check Core Integration Stats

```bash
curl "http://localhost:8001/core/stats"
```

**Expected Response:**
```json
{
  "stats": {
    "total_events": 1,
    "agents_with_context": 1,
    "tracked_agents": ["edumentor_agent"]
  },
  "integration_status": "active"
}
```

**Verification Points:**
- ✅ Total events incremented
- ✅ Agent tracked in list
- ✅ Integration status is "active"

---

### Step 4: Verify Data in Karma

```bash
# Check if Karma received the event
curl "http://localhost:8000/api/v1/karma/system"
```

**Expected Response:**
```json
{
  "user_id": "system",
  "karma_score": 10.0,
  "karma_band": "NEUTRAL",
  "total_actions": 1,
  "recent_actions": [
    {
      "action": "agent_result",
      "timestamp": "2026-02-02T10:30:45Z",
      "reward": 10.0
    }
  ]
}
```

**Verification Points:**
- ✅ Karma score updated
- ✅ Action logged
- ✅ Timestamp matches

---

## 🎯 Test Scenario 2: PRANA Telemetry Flow

### Step 1: Send PRANA Packet to Bucket

```bash
curl -X POST "http://localhost:8001/bucket/prana/ingest" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"test_user_123\",
    \"session_id\": \"session_456\",
    \"lesson_id\": \"lesson_789\",
    \"task_id\": null,
    \"system_type\": \"gurukul\",
    \"role\": \"student\",
    \"timestamp\": \"2026-02-02T10:35:00Z\",
    \"cognitive_state\": \"DEEP_FOCUS\",
    \"active_seconds\": 4.5,
    \"idle_seconds\": 0.5,
    \"away_seconds\": 0.0,
    \"focus_score\": 95,
    \"raw_signals\": {
      \"mouse_velocity\": 150,
      \"scroll_depth\": 75,
      \"keystroke_count\": 45,
      \"window_focus\": true,
      \"tab_visible\": true
    }
  }"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Packet received"
}
```

---

### Step 2: Verify PRANA Data in Bucket

```bash
# Get PRANA statistics
curl "http://localhost:8001/bucket/prana/stats"
```

**Expected Response:**
```json
{
  "stats": {
    "total_packets": 1,
    "unique_users": 1,
    "systems": {
      "gurukul": 1,
      "ems": 0
    },
    "tracked_users": ["test_user_123"]
  },
  "telemetry_status": "active"
}
```

---

### Step 3: Get User PRANA History

```bash
curl "http://localhost:8001/bucket/prana/user/test_user_123"
```

**Expected Response:**
```json
{
  "user_id": "test_user_123",
  "packets": [
    {
      "received_at": "2026-02-02T10:35:01Z",
      "user_id": "test_user_123",
      "cognitive_state": "DEEP_FOCUS",
      "focus_score": 95,
      "active_seconds": 4.5
    }
  ],
  "count": 1,
  "analytics": {
    "average_focus_score": 95.0,
    "state_distribution": {
      "DEEP_FOCUS": 1
    },
    "most_common_state": "DEEP_FOCUS"
  }
}
```

**Verification Points:**
- ✅ User ID matches
- ✅ Cognitive state is "DEEP_FOCUS"
- ✅ Focus score is 95
- ✅ Analytics calculated correctly

---

### Step 4: Verify PRANA Forwarded to Karma

```bash
curl "http://localhost:8000/api/v1/karma/test_user_123"
```

**Expected Response:**
```json
{
  "user_id": "test_user_123",
  "karma_score": 15.0,
  "karma_band": "POSITIVE",
  "total_actions": 1,
  "recent_actions": [
    {
      "action": "cognitive_state_deep_focus",
      "timestamp": "2026-02-02T10:35:01Z",
      "reward": 15.0,
      "metadata": {
        "focus_score": 95,
        "system_type": "gurukul"
      }
    }
  ]
}
```

**Verification Points:**
- ✅ Karma score increased (DEEP_FOCUS = positive karma)
- ✅ Action logged with metadata
- ✅ Karma band is "POSITIVE"

---

## 🎯 Test Scenario 3: Workflow Execution Flow

### Step 1: Execute a Workflow

```bash
curl -X POST "http://localhost:8003/api/workflow/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"trace_id\": \"workflow_test_001\",
    \"decision\": \"workflow\",
    \"data\": {
      \"payload\": {
        \"action_type\": \"task\",
        \"user_id\": \"test_user_456\",
        \"task_data\": {
          \"title\": \"Complete AI assignment\",
          \"description\": \"Finish quantum computing homework\",
          \"due_date\": \"2026-02-10\"
        }
      }
    }
  }"
```

**Expected Response:**
```json
{
  "trace_id": "workflow_test_001",
  "status": "success",
  "execution_result": {
    "success": true,
    "action_type": "task",
    "message": "Task created successfully"
  }
}
```

---

### Step 2: Verify Workflow Event in Bucket

```bash
curl "http://localhost:8001/core/events?limit=10"
```

**Look for workflow event:**
```json
{
  "timestamp": "2026-02-02T10:40:00Z",
  "requester_id": "workflow_executor",
  "event_type": "workflow_execution",
  "trace_id": "workflow_test_001",
  "action_type": "task",
  "status": "success"
}
```

---

### Step 3: Verify in Karma

```bash
curl "http://localhost:8000/api/v1/karma/test_user_456"
```

**Expected Response:**
```json
{
  "user_id": "test_user_456",
  "karma_score": 10.0,
  "recent_actions": [
    {
      "action": "workflow_task",
      "timestamp": "2026-02-02T10:40:00Z",
      "reward": 10.0
    }
  ]
}
```

---

## 🎯 Test Scenario 4: UAO Action Orchestration Flow

### Step 1: Send Action to UAO

```bash
curl -X POST "http://localhost:8004/api/assistant" \
  -H "Content-Type: application/json" \
  -d "{
    \"action_id\": \"action_test_001\",
    \"action_type\": \"SEND_MESSAGE\",
    \"payload\": {
      \"user_id\": \"test_user_789\",
      \"recipient\": \"john@example.com\",
      \"message\": \"Meeting scheduled for tomorrow\"
    }
  }"
```

**Expected Response:**
```json
{
  "status": "accepted",
  "action_id": "action_test_001"
}
```

---

### Step 2: Report Execution Result

```bash
curl -X POST "http://localhost:8004/api/execution_result" \
  -H "Content-Type: application/json" \
  -d "{
    \"action_id\": \"action_test_001\",
    \"success\": true,
    \"error\": null
  }"
```

**Expected Response:**
```json
{
  "status": "updated"
}
```

---

### Step 3: Verify UAO Event in Bucket

```bash
curl "http://localhost:8001/core/events?limit=10"
```

**Look for UAO events:**
```json
[
  {
    "requester_id": "unified_action_orchestrator",
    "event_type": "orchestration_event",
    "action_id": "action_test_001",
    "state": "requested"
  },
  {
    "requester_id": "unified_action_orchestrator",
    "event_type": "orchestration_event",
    "action_id": "action_test_001",
    "state": "executing"
  },
  {
    "requester_id": "unified_action_orchestrator",
    "event_type": "orchestration_event",
    "action_id": "action_test_001",
    "state": "completed"
  }
]
```

**Verification Points:**
- ✅ Three events (requested → executing → completed)
- ✅ Action ID matches
- ✅ State transitions correct

---

### Step 4: Check UAO Lifecycle Log

```bash
# On Windows, check the log file
type "Unified Action Orchestration\lifecycle.log"
```

**Expected Content:**
```
2026-02-02 10:45:00 - STATE=requested: action_test_001
2026-02-02 10:45:00 - STATE=executing: action_test_001
2026-02-02 10:45:05 - STATE=completed: action_test_001
```

---

## 🎯 Test Scenario 5: Security Layer (Insight Core)

### Step 1: Generate JWT Token

```python
# Create test_insight_security.py
import jwt
import time
import uuid
import requests

SECRET_KEY = "demo-secret"

# Generate token
token = jwt.encode({
    "sub": "test_user",
    "iat": int(time.time()),
    "exp": int(time.time()) + 300
}, SECRET_KEY, algorithm="HS256")

# Generate nonce
nonce = f"{uuid.uuid4()}-{int(time.time())}"

# Test request
response = requests.post(
    "http://localhost:8005/ingest",
    json={
        "token": token,
        "nonce": nonce,
        "payload": {"test": "data"}
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run it:
```bash
python test_insight_security.py
```

**Expected Output:**
```
Status: 200
Response: {'decision': 'ALLOW', 'reason': 'OK', 'version': '4.2.0'}
```

---

### Step 2: Test Replay Attack Detection

```python
# Run the same request again (same nonce)
response = requests.post(
    "http://localhost:8005/ingest",
    json={
        "token": token,
        "nonce": nonce,  # Same nonce!
        "payload": {"test": "data"}
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

**Expected Output:**
```
Status: 403
Response: {'decision': 'DENY', 'reason': 'REPLAY_DETECTED', 'version': '4.2.0'}
```

**Verification Points:**
- ✅ First request allowed
- ✅ Second request (replay) denied
- ✅ Nonce stored in replay_store.json

---

### Step 3: Check Replay Store

```bash
type "insightcore-bridgev4x-main\replay_store.json"
```

**Expected Content:**
```json
[
  "a1b2c3d4-e5f6-7890-abcd-1234567890",
  "f1e2d3c4-b5a6-9870-fedc-0987654321"
]
```

---

## 🎯 Test Scenario 6: Complete Integration Verification

### Step 1: Run Complete Integration Test

```bash
python test_complete_integration.py
```

**Expected Output:**
```
========================================
Complete 8-Pillar Integration Test
========================================

[1/8] Testing Karma Health... ✅ PASS
[2/8] Testing Bucket Health... ✅ PASS
[3/8] Testing Core Health... ✅ PASS
[4/8] Testing Workflow Health... ✅ PASS
[5/8] Testing UAO Health... ✅ PASS
[6/8] Testing Insight Core Health... ✅ PASS
[7/8] Testing Insight Flow Bridge Health... ✅ PASS
[8/8] Testing Complete Flow... ✅ PASS

========================================
Result: 8/8 tests passed (100%)
Status: PRODUCTION READY ✅
========================================
```

---

## 📊 Monitoring Dashboard

### Real-Time Monitoring Commands

```bash
# Monitor all services in one view
watch -n 5 '
echo "=== KARMA (8000) ==="
curl -s http://localhost:8000/health | jq .

echo "\n=== BUCKET (8001) ==="
curl -s http://localhost:8001/health | jq .

echo "\n=== CORE (8002) ==="
curl -s http://localhost:8002/health | jq .

echo "\n=== WORKFLOW (8003) ==="
curl -s http://localhost:8003/healthz | jq .

echo "\n=== UAO (8004) ==="
curl -s http://localhost:8004/docs

echo "\n=== INSIGHT (8005) ==="
curl -s http://localhost:8005/health | jq .

echo "\n=== INSIGHT FLOW (8006) ==="
curl -s http://localhost:8006/health | jq .
'
```

---

## 📁 Log File Locations

### Where to Find Logs

```bash
# Core logs
tail -f "v1-BHIV_CORE-main\logs\agent_logs.json"

# Bucket logs
tail -f "BHIV_Central_Depository-main\logs\application.log"

# Karma logs
tail -f "karma_chain_v2-main\logs\api.log"

# UAO logs
tail -f "Unified Action Orchestration\lifecycle.log"

# Workflow logs (console output)
# Check Terminal 4 where workflow is running
```

---

## 🔍 Troubleshooting Guide

### Issue: No events in Bucket

**Check:**
```bash
curl "http://localhost:8001/core/stats"
```

**If events_received = 0:**
1. Verify Core is running (port 8002)
2. Send a test task to Core
3. Check Core logs for errors
4. Verify Bucket is running (port 8001)

---

### Issue: PRANA packets not appearing

**Check:**
```bash
curl "http://localhost:8001/bucket/prana/stats"
```

**If packets_received = 0:**
1. Verify packet format is correct
2. Check Bucket logs for ingestion errors
3. Ensure MongoDB is connected

---

### Issue: Karma not receiving events

**Check:**
```bash
curl "http://localhost:8000/health"
```

**If unhealthy:**
1. Check MongoDB Atlas connection
2. Verify karma_forwarder is running in Bucket
3. Check Karma logs for errors

---

## ✅ Success Criteria

After running all tests, you should see:

- ✅ All 8 services healthy
- ✅ Core events in Bucket (count > 0)
- ✅ PRANA packets in Bucket (count > 0)
- ✅ Karma scores updated for test users
- ✅ Workflow executions logged
- ✅ UAO actions tracked (3 states per action)
- ✅ Insight Core blocking replays
- ✅ All logs showing activity

**Status**: System is fully operational and production-ready! 🎉

---

## 📋 Quick Test Checklist

```
□ All 8 services started
□ Health checks passing
□ Core task processed
□ Event visible in Bucket
□ Event forwarded to Karma
□ PRANA packet ingested
□ PRANA data in Bucket
□ PRANA forwarded to Karma
□ Workflow executed
□ Workflow logged in Bucket
□ UAO action orchestrated
□ UAO lifecycle tracked
□ Insight Core validated request
□ Insight Core blocked replay
□ Complete integration test passed
□ Logs showing activity
```

**When all checked**: System is production ready! ✅

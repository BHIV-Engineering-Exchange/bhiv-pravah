# BHIV Core ↔ Bucket Integration Contract
**Version**: 1.0  
**Date**: January 2026  
**Status**: FROZEN (No changes without Founder approval)

---

## Contract Philosophy

This contract defines the **exact** communication protocol between BHIV Core (the brain) and Bucket (the memory). 

**Core Principles**:
- Core NEVER depends on Bucket for execution
- All writes are fire-and-forget (async, non-blocking)
- All reads are optional with timeout protection
- No circular dependencies
- No schema changes to either system

---

## 1. WRITE OPERATIONS (Core → Bucket)

### 1.1 Generic Event Write

**Endpoint**: `POST /core/write-event`

**Purpose**: Core sends any event to Bucket for storage

**Request Schema**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "string",
    "timestamp": "ISO8601 datetime",
    "agent_id": "string (optional)",
    "task_id": "string (optional)",
    "metadata": {}
  }
}
```

**Example - Generic Event**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "agent_execution",
    "timestamp": "2026-01-25T10:30:00Z",
    "agent_id": "edumentor_agent",
    "task_id": "task_12345",
    "metadata": {
      "input_type": "text",
      "processing_time": 2.5
    }
  }
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "Event received"
}
```

**Failure Behavior**:
- Core continues execution regardless of response
- No retry logic
- Logged at debug level only

---

### 1.2 RL Outcome Write

**Endpoint**: `POST /core/write-event`

**Purpose**: Core sends reinforcement learning outcomes

**Request Schema**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "rl_outcome",
    "agent_id": "string",
    "reward": "float",
    "timestamp": "ISO8601 datetime",
    "metadata": {
      "task_id": "string",
      "processing_time": "float",
      "input_type": "string",
      "tags": ["array of strings"]
    }
  }
}
```

**Example - RL Outcome**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "rl_outcome",
    "agent_id": "knowledge_agent",
    "reward": 0.87,
    "timestamp": "2026-01-25T10:30:00Z",
    "metadata": {
      "task_id": "task_12345",
      "processing_time": 2.5,
      "input_type": "text",
      "tags": ["semantic_search", "vedabase"]
    }
  }
}
```

**Response Schema**: Same as 1.1

**Failure Behavior**: Same as 1.1

---

### 1.3 Agent Result Write

**Endpoint**: `POST /core/write-event`

**Purpose**: Core sends agent execution results

**Request Schema**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "agent_result",
    "task_id": "string",
    "agent_id": "string",
    "timestamp": "ISO8601 datetime",
    "result": {
      "status": "integer",
      "response": "string",
      "processing_time": "float",
      "model": "string (optional)",
      "tokens_used": "integer (optional)"
    }
  }
}
```

**Example - Agent Result**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "agent_result",
    "task_id": "task_12345",
    "agent_id": "edumentor_agent",
    "timestamp": "2026-01-25T10:30:00Z",
    "result": {
      "status": 200,
      "response": "Artificial intelligence is...",
      "processing_time": 2.5,
      "model": "gpt-4",
      "tokens_used": 450
    }
  }
}
```

**Response Schema**: Same as 1.1

**Failure Behavior**: Same as 1.1

---

### 1.4 Error Event Write

**Endpoint**: `POST /core/write-event`

**Purpose**: Core sends error events for audit trail

**Request Schema**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "task_error",
    "task_id": "string",
    "agent_id": "string",
    "timestamp": "ISO8601 datetime",
    "error": "string",
    "input_type": "string"
  }
}
```

**Example - Error Event**:
```json
{
  "requester_id": "bhiv_core",
  "event_data": {
    "event_type": "task_error",
    "task_id": "task_12345",
    "agent_id": "image_agent",
    "timestamp": "2026-01-25T10:30:00Z",
    "error": "Image processing timeout",
    "input_type": "image"
  }
}
```

**Response Schema**: Same as 1.1

**Failure Behavior**: Same as 1.1

---

## 2. READ OPERATIONS (Bucket → Core)

### 2.1 Context Read

**Endpoint**: `GET /core/read-context`

**Purpose**: Core optionally reads historical context for an agent

**Request Parameters**:
```
agent_id: string (required)
requester_id: string (required, must be "bhiv_core")
```

**Example Request**:
```
GET /core/read-context?agent_id=edumentor_agent&requester_id=bhiv_core
```

**Response Schema - Context Found**:
```json
{
  "success": true,
  "context": {
    "agent_id": "edumentor_agent",
    "event_count": 42,
    "last_updated": "2026-01-25T10:30:00Z",
    "recent_event_types": ["agent_result", "rl_outcome"]
  }
}
```

**Response Schema - No Context**:
```json
{
  "success": true,
  "context": null
}
```

**Timeout**: 2 seconds

**Failure Behavior**:
- Core defaults to `null` context
- Core execution continues normally
- No error logged (debug level only)

---

## 3. MONITORING OPERATIONS (Read-Only)

### 3.1 Get Events

**Endpoint**: `GET /core/events`

**Purpose**: View stored Core events (for monitoring/debugging)

**Request Parameters**:
```
limit: integer (optional, default 100, max 1000)
```

**Response Schema**:
```json
{
  "events": [
    {
      "timestamp": "2026-01-25T10:30:00Z",
      "requester_id": "bhiv_core",
      "event_type": "agent_result",
      "agent_id": "edumentor_agent",
      "task_id": "task_12345"
    }
  ],
  "count": 150,
  "showing": 100
}
```

---

### 3.2 Get Statistics

**Endpoint**: `GET /core/stats`

**Purpose**: View integration statistics

**Response Schema**:
```json
{
  "stats": {
    "total_events": 150,
    "agents_with_context": 5,
    "tracked_agents": ["edumentor_agent", "knowledge_agent", "image_agent"]
  },
  "integration_status": "active"
}
```

---

## 4. FAILURE SCENARIOS

### 4.1 Bucket Offline

**Scenario**: Bucket service is not running

**Core Behavior**:
- All write operations fail silently
- All read operations return `null`
- Core continues execution normally
- No user-visible errors

**Example**:
```python
try:
    await bucket_client.write_event(event_data)
except Exception:
    # Silently continue - Core doesn't depend on Bucket
    pass
```

---

### 4.2 Bucket Timeout

**Scenario**: Bucket responds slowly (>2 seconds)

**Core Behavior**:
- Read operations timeout after 2 seconds
- Returns `null` context
- Core continues execution normally

**Implementation**:
```python
timeout = aiohttp.ClientTimeout(total=2.0)
```

---

### 4.3 Invalid Request

**Scenario**: Core sends malformed data

**Bucket Behavior**:
- Returns 400 Bad Request
- Logs error for debugging

**Core Behavior**:
- Catches exception
- Continues execution normally
- Logs at debug level

---

### 4.4 Authentication Failure

**Scenario**: `requester_id` is not "bhiv_core"

**Bucket Behavior**:
- Returns 403 Forbidden
- Rejects request

**Core Behavior**:
- Should never happen (hardcoded)
- If it does, fails silently

---

## 5. INTEGRATION GUARANTEES

### What IS Guaranteed

✅ **Non-blocking writes**: Core never waits for Bucket  
✅ **Timeout protection**: All reads timeout after 2 seconds  
✅ **Graceful degradation**: Core works without Bucket  
✅ **No schema changes**: Both systems unchanged  
✅ **Audit trail**: All events stored permanently  
✅ **Fire-and-forget**: No retry logic needed  

### What is NOT Guaranteed

❌ **Event delivery**: If Bucket is down, events are lost  
❌ **Ordering**: Events may arrive out of order  
❌ **Exactly-once**: Same event may be sent multiple times  
❌ **Real-time sync**: Bucket storage is eventual  
❌ **Context availability**: Reads may return null  

---

## 6. IMPLEMENTATION REFERENCE

### Core Side (bucket_client.py)

**Location**: `v1-BHIV_CORE-main/integration/bucket_client.py`

**Key Methods**:
- `write_event(event_data)` - Generic write
- `write_rl_outcome(agent_id, reward, metadata)` - RL write
- `write_agent_result(task_id, agent_id, result)` - Result write
- `read_context(agent_id)` - Optional read

### Bucket Side (main.py)

**Location**: `BHIV_Central_Depository-main/main.py`

**Key Endpoints**:
- `POST /core/write-event` - Receive events
- `GET /core/read-context` - Provide context
- `GET /core/events` - List events
- `GET /core/stats` - Show statistics

---

## 7. TESTING CONTRACT

### Write Test
```bash
curl -X POST http://localhost:8000/core/write-event \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "bhiv_core",
    "event_data": {
      "event_type": "test",
      "timestamp": "2026-01-25T10:30:00Z"
    }
  }'
```

**Expected**: `{"success": true, "message": "Event received"}`

### Read Test
```bash
curl "http://localhost:8000/core/read-context?agent_id=test_agent&requester_id=bhiv_core"
```

**Expected**: `{"success": true, "context": null}` or context object

### Stats Test
```bash
curl http://localhost:8000/core/stats
```

**Expected**: Statistics object with event counts

---

## 8. CONTRACT CHANGE PROCESS

This contract is **FROZEN**.

Any changes require:
1. Written approval from Founder
2. Version increment
3. Backward compatibility guarantee
4. Migration plan (if needed)

**Current Version**: 1.0  
**Last Updated**: January 2026  
**Next Review**: After Karma integration (Phase 2)

---

## 9. INTEGRATION CHECKLIST

Before deploying:
- [ ] Core writes events successfully
- [ ] Core continues if Bucket is offline
- [ ] Reads timeout after 2 seconds
- [ ] No circular dependencies
- [ ] No schema changes
- [ ] All tests passing
- [ ] Documentation complete

---

**Contract Status**: ✅ ACTIVE  
**Implementation Status**: ✅ COMPLETE  
**Test Status**: ✅ PASSING

# Telemetry & Replay System

## Overview

All engine events emit deterministic telemetry that can be replayed for debugging, testing, and audit trails. No hidden state.

---

## Telemetry Events

### Job Lifecycle Events
| Event | Trigger | Payload |
|-------|---------|---------|
| `JOB_QUEUED` | Job added to queue | `{jobType, userId}` |
| `JOB_DISPATCHED` | Job sent to engine | `{jobType}` |
| `JOB_RUNNING` | Engine starts processing | `{jobType}` |
| `JOB_COMPLETED` | Job finishes successfully | `{jobType, duration}` |
| `JOB_FAILED` | Job fails | `{jobType, error, duration}` |
| `JOB_PROGRESS` | Engine reports progress | `{progress}` |

### Engine-Specific Events
| Event | Trigger | Payload |
|-------|---------|---------|
| `SCENE_LOADED` | BUILD_SCENE completes | `{sceneId, ...}` |
| `ENTITY_SPAWNED` | SPAWN_ENTITY completes | `{entityId, ...}` |
| `ASSETS_LOADED` | LOAD_ASSETS completes | `{assets[]}` |

### Connection Events
| Event | Trigger | Payload |
|-------|---------|---------|
| `ENGINE_CONNECTED` | Engine connects | `{socketId, engineId}` |
| `ENGINE_DISCONNECTED` | Engine disconnects | `{socketId, engineId}` |
| `ENGINE_HEARTBEAT` | Heartbeat received | `{}` |
| `ENGINE_HEARTBEAT_TIMEOUT` | Heartbeat missed | `{}` |

---

## Telemetry Format

```json
{
  "seq": 42,
  "ts": 1738742400000,
  "event": "JOB_COMPLETED",
  "jobId": "job_abc123",
  "engineId": "engine_local_01",
  "userId": "user_xyz",
  "payload": {
    "jobType": "BUILD_SCENE",
    "duration": 3200
  },
  "_replay": true
}
```

### Fields
- `seq`: Monotonic sequence number (deterministic ordering)
- `ts`: Unix timestamp (milliseconds)
- `event`: Event type (see tables above)
- `jobId`: Job identifier (null for non-job events)
- `engineId`: Engine identifier (null for client events)
- `userId`: User identifier (null for system events)
- `payload`: Event-specific data
- `_replay`: Replay flag (always true)

---

## Deterministic Replay

### Replay Strategy
1. **Load telemetry log** → sorted by `seq`
2. **Register handlers** → map event types to functions
3. **Replay events** → execute handlers in sequence order

### Example Replay
```javascript
const { loadTelemetry, replayTelemetry } = require('./engine/engine_telemetry');

const events = loadTelemetry();

replayTelemetry(events, {
  JOB_QUEUED: (e) => console.log(`[${e.seq}] Job queued: ${e.jobId}`),
  JOB_COMPLETED: (e) => console.log(`[${e.seq}] Job done: ${e.jobId} in ${e.payload.duration}ms`),
  JOB_FAILED: (e) => console.error(`[${e.seq}] Job failed: ${e.jobId} - ${e.payload.error}`)
});
```

### Replay Guarantees
✅ **Deterministic ordering** - sequence numbers ensure exact order  
✅ **No hidden state** - all state changes emit telemetry  
✅ **Idempotent** - replaying same log produces same result  
✅ **Complete** - all engine events captured  

---

## No Hidden State

### State Change Coverage
| State Change | Telemetry Event | Location |
|--------------|-----------------|----------|
| Job queued | `JOB_QUEUED` | `jobQueue.js:addJob()` |
| Job dispatched | `JOB_DISPATCHED` | `jobQueue.js:processQueue()` |
| Job running | `JOB_RUNNING` | `jobQueue.js:processQueue()` |
| Job completed | `JOB_COMPLETED` | `jobQueue.js:completeJob()` |
| Job failed | `JOB_FAILED` | `jobQueue.js:failJob()` |
| Scene loaded | `SCENE_LOADED` | `jobQueue.js:completeJob()` |
| Entity spawned | `ENTITY_SPAWNED` | `jobQueue.js:completeJob()` |
| Assets loaded | `ASSETS_LOADED` | `jobQueue.js:completeJob()` |
| Engine connected | `ENGINE_CONNECTED` | `engine_socket.js:connection` |
| Engine disconnected | `ENGINE_DISCONNECTED` | `engine_socket.js:disconnect` |
| Heartbeat | `ENGINE_HEARTBEAT` | `engine_socket.js:engine_heartbeat` |
| Heartbeat timeout | `ENGINE_HEARTBEAT_TIMEOUT` | `engine_socket.js:heartbeatInterval` |

### Verification
```bash
# Count events by type
cat telemetry_samples.json | jq -r '.event' | sort | uniq -c

# Verify sequence continuity
cat telemetry_samples.json | jq '.seq' | awk 'NR>1 && $1!=p+1{print "Gap: "p" -> "$1}{p=$1}'

# Check for missing jobIds
cat telemetry_samples.json | jq 'select(.event | startswith("JOB_")) | select(.jobId == null)'
```

---

## Testing Replay

### Test Case: Job Lifecycle
```javascript
const { clearTelemetry, loadTelemetry } = require('./engine/engine_telemetry');

// Clear previous logs
clearTelemetry();

// Run job
addJob({ jobId: 'test_001', jobType: 'BUILD_SCENE', payload: {} }, onStatus);

// Wait for completion
setTimeout(() => {
  const events = loadTelemetry();
  
  // Verify sequence
  assert(events[0].event === 'JOB_QUEUED');
  assert(events[1].event === 'JOB_DISPATCHED');
  assert(events[2].event === 'JOB_RUNNING');
  assert(events[3].event === 'SCENE_LOADED');
  assert(events[4].event === 'JOB_COMPLETED');
  
  // Verify continuity
  events.forEach((e, i) => assert(e.seq === i + 1));
}, 5000);
```

---

## Integration Points

### jobQueue.js
- Emits: `JOB_QUEUED`, `JOB_DISPATCHED`, `JOB_RUNNING`, `JOB_COMPLETED`, `JOB_FAILED`
- Emits: `SCENE_LOADED`, `ENTITY_SPAWNED`, `ASSETS_LOADED`

### engine_socket.js
- Emits: `ENGINE_CONNECTED`, `ENGINE_DISCONNECTED`, `ENGINE_HEARTBEAT`, `ENGINE_HEARTBEAT_TIMEOUT`
- Emits: `JOB_PROGRESS`, `JOB_COMPLETED`, `JOB_FAILED` (from engine)

### socket.js
- No direct telemetry (delegates to jobQueue)

---

## Frozen Policy

🔒 **Telemetry format is FROZEN** (Feb 5, 2025)

### Allowed Changes
✅ Add new event types (non-breaking)  
✅ Add optional payload fields (non-breaking)  
✅ Bug fixes in replay logic

### Forbidden Changes
❌ Remove/rename event types  
❌ Remove/rename core fields (seq, ts, event, jobId, engineId)  
❌ Change sequence number generation  
❌ Change timestamp format

---

## Compliance Checklist

- [x] All job state changes emit telemetry
- [x] All engine events emit telemetry
- [x] Sequence numbers are monotonic
- [x] Timestamps are Unix milliseconds
- [x] Replay is deterministic
- [x] No hidden state
- [x] Format is frozen
- [x] Testing utilities provided

---

**END OF DOCUMENT**

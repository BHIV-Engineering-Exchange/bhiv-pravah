# Failure Safety & Guards

## Overview
This document defines all failure scenarios and their handling strategies.

**Status:** Production Ready  
**Last Updated:** 2024-02-06

---

## Failure Categories

### 1. Invalid Schema

**Scenario:** User input generates invalid game mode schema

**Detection:**
```javascript
const validation = validateGameMode(gameModeData);
if (!validation.valid) {
  // Handle error
}
```

**Guard Implementation:**
- ✅ Pre-validation before engine dispatch
- ✅ Schema validation against game_mode_schema.json
- ✅ Type checking (string, number, array)
- ✅ Range validation (movement_speed: 1.0-15.0)
- ✅ Enum validation (difficulty: easy/medium/hard)

**Response:**
```json
{
  "success": false,
  "error": "Invalid game mode data",
  "details": [
    "movement_speed must be between 1.0 and 15.0",
    "Invalid difficulty: must be easy, medium, or hard"
  ]
}
```

**UI Behavior:**
- Show error message in red alert box
- Keep user input intact
- Allow retry
- Log error to console

**Code Location:**
- Backend: `backend/ttg_integration/game_mode_mapper.js` (validateGameMode)
- Frontend: `frontend/src/components/TextToGamePanel.jsx` (error state)

---

### 2. Missing Engine

**Scenario:** Engine not connected when job is dispatched

**Detection:**
```javascript
const engineConnected = io.of('/engine').sockets.size > 0;
if (!engineConnected) {
  // Queue job
}
```

**Guard Implementation:**
- ✅ Check engine connection before dispatch
- ✅ Queue jobs if engine offline
- ✅ Auto-dispatch when engine connects
- ✅ Show "waiting for engine" status

**Response:**
```json
{
  "success": true,
  "message": "Engine offline. Job queued.",
  "jobId": "job_1234567890",
  "status": "queued",
  "action": "Will dispatch when engine connects"
}
```

**UI Behavior:**
- Show yellow warning: "⏳ Engine offline - Job queued"
- Display queue position
- Show "Waiting for engine..." animation
- Auto-update when engine connects

**Code Location:**
- Backend: `backend/engine/engine_adapter.js` (connection check)
- Frontend: `frontend/src/components/JobQueuePanel.jsx` (queue status)

---

### 3. Engine Crash

**Scenario:** Engine disconnects during game execution

**Detection:**
```javascript
socket.on('disconnect', () => {
  console.error('Engine disconnected');
  handleEngineCrash();
});
```

**Guard Implementation:**
- ✅ Detect engine disconnect event
- ✅ Mark running jobs as "failed"
- ✅ Save game state before crash
- ✅ Show safe error UI
- ✅ Allow reconnection

**Response:**
```json
{
  "event": "engine:crashed",
  "timestamp": 1708123456789,
  "affected_jobs": ["job_123", "job_456"],
  "game_state": {
    "score": 1250,
    "duration": 45.5,
    "lives": 2
  }
}
```

**UI Behavior:**
- Show red alert: "❌ Engine crashed"
- Display last known score
- Show "Reconnect" button
- Preserve game state
- Disable new game starts until reconnect

**Code Location:**
- Backend: `backend/engine/engine_socket.js` (disconnect handler)
- Frontend: `frontend/src/components/GameTelemetryPanel.jsx` (crash state)

---

### 4. Job Timeout

**Scenario:** Job takes longer than 30 seconds

**Detection:**
```javascript
setTimeout(() => {
  if (job.status === 'running') {
    job.status = 'failed';
    job.error = 'Job timeout after 30 seconds';
  }
}, 30000);
```

**Guard Implementation:**
- ✅ Set 30-second timeout per job
- ✅ Mark job as failed on timeout
- ✅ Notify dashboard
- ✅ Allow retry

**Response:**
```json
{
  "jobId": "job_1234567890",
  "status": "failed",
  "error": "Job timeout after 30 seconds",
  "completedAt": 1708123486789
}
```

**UI Behavior:**
- Show orange warning: "⚠️ Job timeout"
- Show "Retry" button
- Log timeout details
- Continue with next job in queue

**Code Location:**
- Backend: `backend/engine/job_timeout.js`
- Frontend: `frontend/src/components/JobQueuePanel.jsx` (timeout display)

---

### 5. Network Failure

**Scenario:** Socket connection lost

**Detection:**
```javascript
socket.on('connect_error', (error) => {
  console.error('Connection error:', error);
});
```

**Guard Implementation:**
- ✅ Auto-reconnect with exponential backoff
- ✅ Queue events during disconnect
- ✅ Replay events on reconnect
- ✅ Show connection status

**Response:**
- Automatic reconnection attempts
- Max 5 retries with 2s, 4s, 8s, 16s, 32s delays

**UI Behavior:**
- Show yellow banner: "⚠️ Connection lost - Reconnecting..."
- Display retry count
- Show "Reconnected ✅" on success
- Disable actions during disconnect

**Code Location:**
- Frontend: `frontend/src/socket/SocketContext.jsx` (reconnection logic)

---

### 6. Invalid Text Input

**Scenario:** User submits empty or invalid text

**Detection:**
```javascript
if (!text || !text.trim()) {
  return { error: 'Text input is required' };
}
```

**Guard Implementation:**
- ✅ Client-side validation
- ✅ Server-side validation
- ✅ Minimum length check
- ✅ Disable submit button when empty

**Response:**
```json
{
  "success": false,
  "error": "Text input is required"
}
```

**UI Behavior:**
- Disable "Start Game" button when input empty
- Show placeholder text
- Clear error on input change

**Code Location:**
- Frontend: `frontend/src/components/TextToGamePanel.jsx` (validation)
- Backend: `backend/routes/ttgRoutes.js` (validation)

---

### 7. Concurrent Job Limit

**Scenario:** Too many jobs in queue (>10)

**Detection:**
```javascript
if (jobQueue.length >= 10) {
  return { error: 'Job queue full' };
}
```

**Guard Implementation:**
- ✅ Limit queue to 10 jobs
- ✅ Reject new jobs when full
- ✅ Show queue capacity

**Response:**
```json
{
  "success": false,
  "error": "Job queue full (10/10)",
  "message": "Please wait for current jobs to complete"
}
```

**UI Behavior:**
- Show red alert: "❌ Queue full"
- Display queue count: "10/10"
- Disable submit button
- Auto-enable when queue clears

**Code Location:**
- Backend: `backend/jobQueue.js` (queue limit)
- Frontend: `frontend/src/components/JobQueuePanel.jsx` (capacity display)

---

## Error Recovery Strategies

### Automatic Recovery
1. **Socket reconnection** - Auto-retry with backoff
2. **Job retry** - Retry failed jobs once
3. **State persistence** - Save game state to localStorage

### Manual Recovery
1. **Refresh page** - Clear all state
2. **Reconnect button** - Force socket reconnect
3. **Clear queue** - Admin action to clear stuck jobs

---

## Testing Failure Cases

### Test 1: Invalid Schema
```bash
curl -X POST http://localhost:3000/api/ttg/start-game \
  -H "Content-Type: application/json" \
  -d '{"text": ""}'
```
**Expected:** 400 error with validation details

### Test 2: Engine Offline
```bash
# Stop engine, then:
curl -X POST http://localhost:3000/api/ttg/start-game \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a runner game"}'
```
**Expected:** Job queued, status "waiting for engine"

### Test 3: Engine Crash
```bash
# Start game, then kill engine process
```
**Expected:** UI shows "Engine crashed", score preserved

---

## Monitoring & Alerts

### Metrics to Track
- Job failure rate
- Average job duration
- Engine uptime
- Socket reconnection count
- Validation error rate

### Alert Thresholds
- Job failure rate > 10% → Alert
- Engine downtime > 5 minutes → Alert
- Socket reconnects > 5/minute → Alert

---

## Production Checklist

- [x] All validation guards implemented
- [x] Error messages user-friendly
- [x] Retry logic tested
- [x] State persistence working
- [x] Reconnection logic tested
- [x] Timeout handling verified
- [x] Queue limits enforced
- [ ] Error monitoring setup (Day 2d)
- [ ] Alert system configured (Day 2d)

---

**Owner:** Dashboard Team  
**Reviewed By:** TBD  
**Next Review:** Before production deployment

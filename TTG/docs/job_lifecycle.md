# Job Lifecycle Hardening — Strict State Machine

**Date:** Feb 2, 2025  
**Status:** FROZEN after implementation  
**Purpose:** Eliminate silent failures, enforce deterministic job processing

---

## 1. Lifecycle States

### **State Machine**
```
queued → dispatched → running → completed
                            ↘ failed
```

### **State Definitions**

#### `queued`
- Job accepted into queue
- Waiting for processing
- **Transition:** Automatic when queue processes
- **Duration:** 0-4s (depends on queue depth)

#### `dispatched`
- Job sent to engine via `/engine` socket
- Engine acknowledged receipt
- **Transition:** Engine emits `job_ack`
- **Duration:** <100ms (network latency)

#### `running`
- Engine actively processing job
- Progress can be tracked
- **Transition:** Engine emits `job_progress` or `job_complete`
- **Duration:** Variable (engine-dependent)

#### `completed`
- Job finished successfully
- Results available
- **Terminal state** (no further transitions)

#### `failed`
- Job encountered error
- Error reason logged
- **Terminal state** (no further transitions)

---

## 2. State Transition Rules

### **Valid Transitions**
```
queued      → dispatched  ✅
dispatched  → running     ✅
running     → completed   ✅
running     → failed      ✅
```

### **Invalid Transitions (Rejected)**
```
queued      → running     ❌ (must dispatch first)
queued      → completed   ❌ (must run first)
dispatched  → completed   ❌ (must run first)
completed   → *           ❌ (terminal state)
failed      → *           ❌ (terminal state)
```

### **Timeout Rules**
- `queued` → `failed` after 30s (queue stuck)
- `dispatched` → `failed` after 10s (engine not responding)
- `running` → `failed` after 60s (job timeout)

---

## 3. Error Handling

### **No Silent Failures**
Every failure MUST:
1. Transition to `failed` state
2. Log error reason
3. Emit `job_failed` event
4. Record telemetry

### **Failure Categories**

#### **Validation Failures** (Pre-queue)
- Invalid job type
- Missing required payload fields
- Schema validation failure
- **Action:** Reject before queuing

#### **Queue Failures**
- Queue timeout (30s)
- Engine disconnected
- **Action:** Transition to `failed`, emit event

#### **Engine Failures**
- Bad asset reference
- Invalid entity data
- Scene build error
- **Action:** Engine reports failure, transition to `failed`

#### **System Failures**
- Network timeout
- Engine crash
- Out of memory
- **Action:** Detect via heartbeat loss, fail all running jobs

---

## 4. Telemetry Requirements

### **Required Events**
```javascript
// State transitions
JOB_QUEUED      { jobId, jobType, userId, queuedAt }
JOB_DISPATCHED  { jobId, engineId, dispatchedAt }
JOB_RUNNING     { jobId, engineId, startedAt }
JOB_COMPLETED   { jobId, engineId, completedAt, duration }
JOB_FAILED      { jobId, engineId, failedAt, error, duration }

// Progress (optional)
JOB_PROGRESS    { jobId, progress: 0-100 }
```

### **Telemetry Guarantees**
- Every job MUST emit `JOB_QUEUED`
- Every job MUST emit either `JOB_COMPLETED` or `JOB_FAILED`
- No job can complete without telemetry

---

## 5. Job Queue Data Structure

### **Job Object**
```javascript
{
  jobId: "uuid-v4",
  userId: "user_123",
  jobType: "BUILD_SCENE" | "LOAD_ASSETS" | "SPAWN_ENTITY",
  payload: { /* job-specific data */ },
  
  // Lifecycle tracking
  status: "queued" | "dispatched" | "running" | "completed" | "failed",
  
  // Timestamps
  submittedAt: 1738425600000,
  queuedAt: 1738425600000,
  dispatchedAt: 1738425601000,
  startedAt: 1738425601100,
  completedAt: 1738425605000,
  
  // Error tracking
  error: "BAD_ASSET: corrupted_texture.png",
  retryCount: 0,
  
  // Engine tracking
  engineId: "engine_local_01"
}
```

---

## 6. Implementation Checklist

### **Phase 1: State Machine**
- [ ] Add `dispatched` and `running` states
- [ ] Implement state transition validation
- [ ] Add timestamp tracking for all states
- [ ] Reject invalid state transitions

### **Phase 2: Error Handling**
- [ ] Add timeout detection for each state
- [ ] Implement failure reason categorization
- [ ] Ensure all failures emit events
- [ ] Add retry logic (optional)

### **Phase 3: Telemetry**
- [ ] Emit events for all state transitions
- [ ] Add duration tracking
- [ ] Implement replay capability
- [ ] Add job history persistence

### **Phase 4: Engine Integration**
- [ ] Engine acknowledges job receipt (`dispatched`)
- [ ] Engine reports job start (`running`)
- [ ] Engine reports progress (optional)
- [ ] Engine reports completion/failure

---

## 7. Testing Requirements

### **Unit Tests**
- Valid state transitions succeed
- Invalid state transitions rejected
- Timeouts trigger failures
- All failures emit events

### **Integration Tests**
- Full lifecycle: queued → completed
- Failure path: queued → failed
- Engine disconnect handling
- Concurrent job processing

### **Failure Simulation**
- Bad asset reference
- Invalid entity data
- Engine timeout
- Network failure

---

## 8. Backward Compatibility

### **Current State Mapping**
```
"queued"   → queued    ✅ (no change)
"started"  → running   ⚠️  (rename)
"finished" → completed ⚠️  (rename)
"failed"   → failed    ✅ (no change)
```

### **Migration Strategy**
1. Add new states alongside old
2. Emit both old and new events during transition
3. Update frontend to handle new states
4. Remove old states after verification

---

## 9. Success Criteria

- [ ] Zero silent failures
- [ ] All jobs have complete telemetry
- [ ] State transitions are deterministic
- [ ] Failures are categorized and logged
- [ ] Engine integration is bidirectional
- [ ] Job history is replayable

---

**Document Status:** LOCKED  
**Implementation Target:** Day 2a complete

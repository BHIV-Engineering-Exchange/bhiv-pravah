# Day 1 - Core Interface Contract Understanding

**Date:** 2024-01-15  
**Task:** Rudra Parmeshwar — Prompt Runner Core Integration  
**Status:** ✅ COMPLETE

---

## 1. Prompt Runner Output Format

### **Source:** `prompt-runner-main/prompt-to-json-main/agents/compliance_pipeline.py`

### **Complete Output Structure:**

```json
{
  "case_id": "abc12345",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "run_id": "abc12345",
  "city": "Mumbai",
  "status": "COMPLIANT",
  
  "building_parameters": {
    "city": "Mumbai",
    "land_use_zone": "Residential",
    "plot_area_sq_m": 500.0,
    "height_m": 15.0,
    "fsi": 1.5,
    "setback_m": 3.0,
    "building_type": "apartment"
  },
  
  "evaluations": [...],
  "geometry": {...},
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### **4 Key Components Identified:**

| Component | Field Name | Type | Example |
|-----------|-----------|------|---------|
| **Intent JSON** | `building_parameters` | Object | `{ height_m: 15, fsi: 1.5 }` |
| **Execution Schema JSON** | `building_parameters` | Object | Complete building spec |
| **Trace ID** | `trace_id` | UUID v4 | `a1b2c3d4-e5f6-7890-...` |
| **Execution ID** | `case_id` / `run_id` | String | `abc12345` (8-char UUID) |

---

## 2. Backend Analysis

### **A. jobQueue.js**

**Location:** `backend/jobQueue.js`

**Current Job Structure:**
```javascript
{
  jobId: "job_123",
  jobType: "BUILD_SCENE" | "SPAWN_ENTITY" | "START_LOOP" | "END_GAME",
  status: "queued" | "dispatched" | "running" | "completed" | "failed",
  payload: { /* job-specific data */ },
  userId: "user_123",
  engineId: "engine_local_01",
  queuedAt: timestamp,
  dispatchedAt: timestamp,
  startedAt: timestamp,
  completedAt: timestamp,
  retryCount: 0
}
```

**Key Capabilities:**
- ✅ FSM state machine with strict transitions
- ✅ Retry logic (max 2 retries)
- ✅ Event emission via `jobDispatcher`
- ✅ Engine connection handling
- ✅ Telemetry recording
- ✅ Timeout handling
- ✅ Auto-cleanup of stale jobs

**Key Functions:**
- `addJob(job, onStatus, gameplayContract)` - Add job to queue
- `updateJobStatus(jobId, status, data)` - Update job state
- `setEngineConnected(connected)` - Handle engine connection
- `findJobById(jobId)` - Retrieve job
- `jobDispatcher.emit('dispatch_to_engine', {job, gameplayContract})` - Send to engine

### **B. eventBus.js**

**Location:** `backend/eventBus.js`

**Current Action Structure:**
```javascript
{
  type: "inspect" | "interact" | "spam_click",
  userId: "user_123",
  sessionId: "session_456",
  clientTs: timestamp,
  serverTs: timestamp  // added by eventBus
}
```

**Key Capabilities:**
- ✅ Event publishing
- ✅ In-memory log (max 200 events)
- ✅ Action validation
- ✅ Server timestamp enrichment

**Key Functions:**
- `publish(action)` - Publish action event
- `getLog()` - Get recent actions (newest first)

---

## 3. Mapping: Core Execution Schema → Dashboard Job Queue

### **Input Format (What We'll Receive):**

```json
{
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "execution_id": "abc12345",
  "timestamp": 1708123456789,
  "user_id": "user_123",
  
  "intent": {
    "genre": "runner",
    "pacing": "fast",
    "difficulty": "medium",
    "abilities": ["jump"],
    "obstacles": true
  },
  
  "executionSchema": {
    "game_mode": "runner",
    "movement": {
      "speed": 8,
      "jump_height": 5
    },
    "camera": {
      "type": "third_person",
      "distance": 10
    },
    "spawn_rules": {
      "obstacles": 2,
      "frequency": 2
    },
    "score_rules": {
      "distance": 1,
      "collectibles": 0
    },
    "end_conditions": ["collision"],
    "player_params": {
      "jetpack": false,
      "health": 3
    },
    "world_params": {
      "theme": "default"
    },
    "physics": {
      "gravity": -9.8,
      "friction": 0.5,
      "bounce": 0.3,
      "air_resistance": 0.1,
      "collision_force": 1.0
    }
  },
  
  "signature": "hmac_sha256_signature",
  "nonce": "nonce_12345"
}
```

### **Output Format (Jobs in Queue):**

```javascript
// Job 1: BUILD_SCENE
{
  jobId: "job_1_abc12345",
  jobType: "BUILD_SCENE",
  traceId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  executionId: "abc12345",
  userId: "user_123",
  status: "queued",
  payload: {
    sceneId: "scene_runner",
    ambientLight: [0.6, 0.6, 0.6],
    skybox: "default_sky",
    gravity: [0, -9.8, 0]
  },
  queuedAt: 1708123456789
}

// Job 2: SPAWN_ENTITY (Player)
{
  jobId: "job_2_abc12345",
  jobType: "SPAWN_ENTITY",
  traceId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  executionId: "abc12345",
  userId: "user_123",
  status: "queued",
  payload: {
    id: "player_1",
    type: "player",
    transform: {
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      scale: [1, 1, 1]
    },
    material: {
      shader: "standard",
      texture: "player_skin",
      color: [1, 1, 1]
    },
    components: {
      mesh: "player",
      collider: "box",
      script: "runner_controller"
    }
  },
  queuedAt: 1708123456790
}

// Job 3: START_LOOP
{
  jobId: "job_3_abc12345",
  jobType: "START_LOOP",
  traceId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  executionId: "abc12345",
  userId: "user_123",
  status: "queued",
  payload: {
    game_mode: "runner",
    params: {
      movement_speed: 8.0,
      difficulty: "medium",
      spawn_rules: {
        interval: 2.0,
        distance: 10.0
      },
      scoring: {
        points_per_second: 10,
        obstacle_bonus: 50
      },
      end_condition: {
        type: "lives",
        value: 3
      }
    }
  },
  queuedAt: 1708123456791
}
```

### **Mapping Logic:**

```javascript
function mapExecutionSchemaToJobs(executionSchema, traceId, executionId, userId) {
  const jobs = [];
  
  // Job 1: BUILD_SCENE
  jobs.push({
    jobId: `build_${executionId}`,
    jobType: "BUILD_SCENE",
    traceId,
    executionId,
    userId,
    payload: {
      sceneId: `scene_${executionSchema.game_mode}`,
      ambientLight: [0.6, 0.6, 0.6],
      skybox: "default_sky",
      gravity: [0, executionSchema.physics.gravity, 0]
    }
  });
  
  // Job 2: SPAWN_ENTITY (Player)
  jobs.push({
    jobId: `spawn_player_${executionId}`,
    jobType: "SPAWN_ENTITY",
    traceId,
    executionId,
    userId,
    payload: {
      id: "player_1",
      type: "player",
      transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
      material: { shader: "standard", texture: "player_skin", color: [1, 1, 1] },
      components: { mesh: "player", collider: "box", script: "runner_controller" }
    }
  });
  
  // Job 3: START_LOOP
  jobs.push({
    jobId: `start_${executionId}`,
    jobType: "START_LOOP",
    traceId,
    executionId,
    userId,
    payload: {
      game_mode: executionSchema.game_mode,
      params: {
        movement_speed: executionSchema.movement.speed,
        difficulty: "medium",
        spawn_rules: {
          interval: executionSchema.spawn_rules.frequency,
          distance: 10.0
        },
        scoring: {
          points_per_second: executionSchema.score_rules.distance * 10,
          obstacle_bonus: executionSchema.score_rules.collectibles
        },
        end_condition: {
          type: executionSchema.end_conditions[0] === "collision" ? "lives" : "distance",
          value: executionSchema.player_params.health
        }
      }
    }
  });
  
  return jobs;
}
```

---

## 4. Execution Schema Contract

### **Schema Source:**
Using existing `backend/intent-layer/schema/game.schema.json` as base

### **Required Fields:**
- `game_mode` (enum: runner, sidescroller, open_scene)
- `movement` (object: speed, jump_height)
- `camera` (object: type, distance)
- `spawn_rules` (object: obstacles, frequency)
- `score_rules` (object: distance, collectibles)
- `end_conditions` (array)
- `player_params` (object: jetpack, health)
- `world_params` (object: theme)
- `physics` (object: gravity, friction, bounce, air_resistance, collision_force)

### **Wrapper Fields:**
- `trace_id` (string, UUID v4, required)
- `execution_id` (string, 8-char UUID, required)
- `timestamp` (number, epoch ms, required)
- `user_id` (string, required)
- `intent` (object, optional - for telemetry)
- `signature` (string, HMAC-SHA256, required)
- `nonce` (string, required)

---

## 5. Integration Points Identified

### **A. Existing Strengths (Can Reuse):**
- ✅ Job queue with FSM
- ✅ Retry logic
- ✅ Engine connection handling
- ✅ Telemetry recording (`behaviourRecorder.js`)
- ✅ Security layer (`signature.js`, `nonceStore.js`)
- ✅ Event emission

### **B. Gaps (Need to Build):**
- ❌ Core ingestion endpoint (`POST /core/execute`)
- ❌ Execution registry (track executionId → jobs)
- ❌ Bucket writer module
- ❌ Execution dispatcher (schema → jobs)
- ❌ Execution state tracker (`GET /execution/:id`)
- ❌ Demo path removal

---

## 6. Coordination Requirements

### **With Atharva (Engine Lead):**
- Provide `engineExecutionContract.json` format
- Ensure engine consumes START_LOOP payload directly
- Confirm job types: BUILD_SCENE, SPAWN_ENTITY, START_LOOP, END_GAME

### **With Ashmit (Bucket Lead):**
- Get Bucket write interface
- Confirm artifact structure
- Async/append-only requirements

### **With Siddhesh (Prompt Runner Lead):**
- Confirm execution schema format matches game.schema.json
- Verify trace_id and execution_id generation

---

## 7. Day 1 Deliverables

✅ **Studied Prompt Runner output format:**
- Intent JSON: Extracted game features
- Execution Schema JSON: Complete game configuration
- Trace ID: UUID v4 for distributed tracing
- Execution ID: 8-char UUID for execution tracking

✅ **Analyzed backend components:**
- jobQueue.js: FSM, retry, telemetry
- eventBus.js: Event publishing, logging

✅ **Defined mapping:**
- Core Execution Schema → Dashboard Job Queue
- 1 execution schema → 3 jobs (BUILD_SCENE, SPAWN_ENTITY, START_LOOP)

---

## 8. Next Steps (Day 2)

**Create:** `backend/routes/coreExecution.js`
- POST /core/execute endpoint
- Schema validation
- Execution registry storage
- Job queue dispatch

**Blockers:** None identified

**Dependencies:** 
- Bucket write interface (from Ashmit)
- Engine contract confirmation (from Atharva)

---

**Day 1 Status:** ✅ COMPLETE  
**Ready for Day 2:** ✅ YES

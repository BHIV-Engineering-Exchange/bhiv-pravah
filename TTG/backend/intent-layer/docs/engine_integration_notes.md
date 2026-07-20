# Day 2d: Engine Dry Run Integration Notes

**Date:** 2025-02-13  
**Integration:** Intent Compiler → TG Engine (Atharva)  
**Status:** ✅ Ready for Engine Integration

---

## Integration Architecture

```
User Input (Text)
    ↓
Intent Compiler (backend/intent-compiler/)
    ↓
TG Engine Gameplay Contract (JSON)
    ↓
Engine Adapter (backend/engine/engine_adapter.js)
    ↓
Job Queue (backend/engine/engine_job_queue.js)
    ↓
Engine Socket (backend/engine/engine_socket.js)
    ↓
TG Engine (Atharva's OpenGL Engine)
```

---

## Schema Compatibility

### ✅ Output Format

Intent Compiler produces **exact** TG Engine Gameplay Contract:

```json
{
  "meta": {
    "game_title": "string",
    "version": "1.0"
  },
  "gameplay": {
    "game_mode": "infinite_runner | side_scroller | arena_loop",
    "movement_axis": "x | z | free",
    "global_speed": "number",
    "gravity": -9.8,
    "score_metric": "distance | time | collection"
  },
  "camera": {
    "mode": "follow_third_person | fixed_ortho | top_down",
    "offset": [0, 5, -10],
    "look_at_offset": [0, 0, 0]
  },
  "player": {
    "start_pos": [0, 0, 0],
    "abilities": {
      "jump_force": "number (optional)",
      "lane_switch_speed": "number (optional)",
      "dash_speed": "number (optional)"
    },
    "mesh_id": "cube"
  },
  "entities": [
    {
      "id": "string",
      "type": "obstacle | pickup | decoration",
      "mesh_id": "string",
      "spawn_rule": {
        "spawn_rate": "number",
        "lane_distribution": "random | all | center",
        "y_offset": "number"
      },
      "collision_effect": "game_over | score_add | none"
    }
  ]
}
```

### ✅ No Modifications Needed

Schema is sent to engine **without any changes**.

---

## Integration Test Results

### Test 1: Schema Validation

```bash
cd backend/engine
node test_new_schema.js
```

**Result:**
```
✅ Intent compiler works
✅ Schema validation works
✅ Engine adapter works
✅ Job generation works
✅ Multiple game modes work
```

### Test 2: Job Dispatch

**Flow:**
1. User: "Make a fast runner with jump"
2. Compiler: Generates schema
3. Job Queue: Creates START_GAME job
4. Socket: Sends to engine namespace `/engine`

**Job Format:**
```json
{
  "jobId": "uuid",
  "jobType": "START_GAME",
  "gameplayContract": { /* full schema */ },
  "payload": { /* full schema */ }
}
```

---

## API Endpoints

### POST /api/ttg/compile

**Purpose:** Compile text to schema (preview only)

**Request:**
```json
{
  "text": "Make a fast runner with jump"
}
```

**Response:**
```json
{
  "success": true,
  "intent": {
    "genre": "runner",
    "pacing": "fast",
    "abilities": ["jump"],
    ...
  },
  "schema": { /* TG Engine Gameplay Contract */ },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  }
}
```

### POST /api/ttg/start-game

**Purpose:** Compile and send to engine

**Request:**
```json
{
  "text": "Make a fast runner with jump"
}
```

**Response:**
```json
{
  "success": true,
  "intent": { /* extracted intent */ },
  "schema": { /* compiled schema */ },
  "jobs": [
    {
      "jobId": "uuid",
      "jobType": "START_GAME",
      "payload": { /* schema */ }
    }
  ],
  "message": "Game started successfully"
}
```

---

## Socket Communication

### Engine Namespace: `/engine`

**Events Sent to Engine:**

1. **job:dispatch**
   ```json
   {
     "jobId": "uuid",
     "jobType": "START_GAME",
     "gameplayContract": { /* schema */ }
   }
   ```

**Events Received from Engine:**

1. **job_started**
2. **job_progress**
3. **job_completed**
4. **job_failed**
5. **telemetry** (fps, score, lives)
6. **game:started**
7. **game:ended**

---

## Mismatches Fixed (Our Side)

### Issue 1: Old Schema Format
**Problem:** Engine adapter used old BHIV schema  
**Fix:** Updated to TG Engine Gameplay Contract  
**File:** `backend/engine/engine_adapter.js`

### Issue 2: Job Types
**Problem:** Used BUILD_SCENE, SPAWN_ENTITY jobs  
**Fix:** Changed to START_GAME job  
**File:** `backend/engine/engine_job_queue.js`

### Issue 3: Socket Payload
**Problem:** Sent `worldSpec` field  
**Fix:** Changed to `gameplayContract` field  
**File:** `backend/engine/engine_socket.js`

### Issue 4: Validator
**Problem:** Validated against old schema  
**Fix:** Updated to validate new schema  
**File:** `backend/engine/world_spec_validator.js`

---

## Engine Requirements (Atharva's Side)

### ✅ What Engine Must Accept

1. **Job Type:** `START_GAME`
2. **Payload Field:** `gameplayContract` (not `worldSpec`)
3. **Schema:** TG Engine Gameplay Contract (exact format above)

### ✅ What Engine Must Parse

- `gameplay.game_mode` → Initialize game loop
- `gameplay.movement_axis` → Set player movement
- `gameplay.global_speed` → Set world scroll speed
- `player.abilities` → Enable player controls
- `entities[]` → Spawn obstacles/pickups
- `camera.mode` → Set camera behavior

### ✅ What Engine Must Send Back

- `job_started` - When game initializes
- `job_completed` - When game loads
- `telemetry` - Real-time game stats
- `game:ended` - When game finishes

---

## Testing Checklist

### ✅ Our Side (Complete)

- [x] Intent compiler produces valid schema
- [x] Schema passes validation
- [x] Job queue creates START_GAME job
- [x] Socket sends to `/engine` namespace
- [x] Payload contains `gameplayContract`
- [x] No modifications to schema
- [x] All game modes supported
- [x] All abilities supported
- [x] All entity types supported

### ⏳ Engine Side (Pending Atharva)

- [ ] Engine accepts START_GAME job
- [ ] Engine parses gameplayContract
- [ ] Engine initializes game from schema
- [ ] Engine sends telemetry back
- [ ] Engine handles all game modes
- [ ] Engine handles all abilities
- [ ] Engine spawns entities correctly

---

## Demo Flow

### Step 1: User Input
```
User types: "Make a fast runner with jump and obstacles"
```

### Step 2: Compilation
```
POST /api/ttg/compile
→ Returns schema preview
```

### Step 3: Send to Engine
```
POST /api/ttg/start-game
→ Creates START_GAME job
→ Dispatches to engine via socket
```

### Step 4: Engine Response
```
Engine receives job
→ Parses gameplayContract
→ Initializes game
→ Sends job_started event
→ Sends telemetry updates
```

### Step 5: Game Running
```
Engine runs game loop
→ Spawns obstacles
→ Handles player jump
→ Sends real-time telemetry
→ Dashboard displays stats
```

---

## Sample Schemas for Testing

### Test 1: Minimal Runner
```json
{
  "meta": { "game_title": "Runner", "version": "1.0" },
  "gameplay": {
    "game_mode": "infinite_runner",
    "movement_axis": "z",
    "global_speed": 5.0,
    "gravity": -9.8,
    "score_metric": "distance"
  },
  "camera": {
    "mode": "follow_third_person",
    "offset": [0, 5, -10],
    "look_at_offset": [0, 0, 0]
  },
  "player": {
    "start_pos": [0, 0, 0],
    "abilities": {},
    "mesh_id": "cube"
  },
  "entities": []
}
```

### Test 2: Complete Runner
```json
{
  "meta": { "game_title": "Complete Runner", "version": "1.0" },
  "gameplay": {
    "game_mode": "infinite_runner",
    "movement_axis": "z",
    "global_speed": 8.0,
    "gravity": -9.8,
    "score_metric": "distance"
  },
  "camera": {
    "mode": "follow_third_person",
    "offset": [0, 5, -10],
    "look_at_offset": [0, 0, 0]
  },
  "player": {
    "start_pos": [0, 0, 0],
    "abilities": {
      "jump_force": 5.0,
      "dash_speed": 10.0
    },
    "mesh_id": "cube"
  },
  "entities": [
    {
      "id": "obstacle_1",
      "type": "obstacle",
      "mesh_id": "cube",
      "spawn_rule": {
        "spawn_rate": 2.0,
        "lane_distribution": "random",
        "y_offset": 0
      },
      "collision_effect": "game_over"
    },
    {
      "id": "pickup_1",
      "type": "pickup",
      "mesh_id": "sphere",
      "spawn_rule": {
        "spawn_rate": 1.0,
        "lane_distribution": "random",
        "y_offset": 1.0
      },
      "collision_effect": "score_add"
    }
  ]
}
```

---

## Next Steps

### For Atharva (Engine Developer)

1. Update engine to accept `START_GAME` job type
2. Parse `gameplayContract` field from job payload
3. Initialize game from schema fields
4. Send telemetry events back to dashboard
5. Test with sample schemas above

### For Integration Testing

1. Start backend: `npm start` (port 3000)
2. Start frontend: `npm run dev` (port 5173)
3. Start Atharva's engine (connect to `/engine` namespace)
4. Test with demo prompts
5. Verify telemetry flow

---

**Status:** ✅ Ready for Engine Integration  
**Blocker:** Waiting for Atharva's engine to accept new schema  
**ETA:** Pending Atharva's timeline

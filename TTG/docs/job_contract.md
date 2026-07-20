# Engine Job Dispatch Contract

## Overview
This document defines the exact job payload formats expected by Atharva's OpenGL engine.

**Contract Version:** 1.0  
**Status:** FROZEN  
**Breaking Changes:** Forbidden

---

## Job Types

### 1. BUILD_SCENE

**Purpose:** Initialize game scene with lighting and environment

**Payload Structure:**
```json
{
  "jobId": "build_1234567890",
  "jobType": "BUILD_SCENE",
  "payload": {
    "sceneId": "scene_runner",
    "ambientLight": [0.6, 0.6, 0.6],
    "skybox": "default_sky",
    "gravity": [0, -9.8, 0]
  }
}
```

**Field Requirements:**
- `sceneId` (string, required) - Unique scene identifier
- `ambientLight` (array[3], required) - RGB values 0.0-1.0
- `skybox` (string, required) - Skybox asset name
- `gravity` (array[3], required) - Gravity vector [x, y, z]

---

### 2. SPAWN_ENTITY

**Purpose:** Create entities (player, obstacles, NPCs) in the scene

**Payload Structure:**
```json
{
  "jobId": "spawn_1234567890",
  "jobType": "SPAWN_ENTITY",
  "payload": {
    "id": "player_1",
    "type": "player",
    "transform": {
      "position": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1]
    },
    "material": {
      "shader": "standard",
      "texture": "player_skin",
      "color": [1, 1, 1]
    },
    "components": {
      "mesh": "player",
      "collider": "box",
      "script": "runner_controller"
    }
  }
}
```

**Field Requirements:**
- `id` (string, required) - Unique entity identifier
- `type` (enum, required) - "player" | "npc" | "object"
- `transform` (object, required) - Position, rotation, scale
- `material` (object, required) - Shader, texture, color
- `components` (object, required) - Mesh, collider, script

---

### 3. START_LOOP

**Purpose:** Begin game loop execution

**Payload Structure:**
```json
{
  "jobId": "start_1234567890",
  "jobType": "START_LOOP",
  "payload": {
    "game_mode": "runner",
    "params": {
      "movement_speed": 8.0,
      "difficulty": "medium",
      "spawn_rules": {
        "interval": 2.0,
        "distance": 10.0
      },
      "scoring": {
        "points_per_second": 10,
        "obstacle_bonus": 50
      },
      "end_condition": {
        "type": "lives",
        "value": 3
      }
    }
  }
}
```

**Field Requirements:**
- `game_mode` (enum, required) - "runner" | "side_scroller"
- `params` (object, required) - Game parameters
  - `movement_speed` (number, required) - 1.0 to 15.0
  - `difficulty` (enum, required) - "easy" | "medium" | "hard"
  - `spawn_rules` (object, required) - Obstacle spawning
  - `scoring` (object, required) - Point calculation
  - `end_condition` (object, required) - Win/lose condition

---

### 4. END_GAME

**Purpose:** Stop game loop and cleanup

**Payload Structure:**
```json
{
  "jobId": "end_1234567890",
  "jobType": "END_GAME",
  "payload": {
    "reason": "player_death",
    "final_score": 1250,
    "duration": 125.5
  }
}
```

**Field Requirements:**
- `reason` (enum, required) - "player_death" | "goal_reached" | "time_up" | "manual_stop"
- `final_score` (number, required) - Final score value
- `duration` (number, required) - Game duration in seconds

---

## Job Lifecycle States

```
queued → dispatched → running → completed
                              ↘ failed
```

**State Definitions:**
- `queued` - Job created, waiting for dispatch
- `dispatched` - Sent to engine, awaiting acknowledgment
- `running` - Engine executing job
- `completed` - Job finished successfully
- `failed` - Job encountered error

---

## Dispatch Flow

### Text-to-Game Pipeline

```
User Text Input
    ↓
Text-to-Game Mode Mapper
    ↓
Game Mode Validation
    ↓
Engine Schema Conversion
    ↓
Job Creation (BUILD_SCENE + SPAWN_ENTITY + START_LOOP)
    ↓
Job Queue
    ↓
Engine Dispatch
    ↓
Telemetry Feedback
```

---

## Example: Complete Game Start Sequence

### Step 1: Build Scene
```json
{
  "jobId": "build_1708123456789",
  "jobType": "BUILD_SCENE",
  "status": "queued",
  "submittedAt": 1708123456789,
  "payload": {
    "sceneId": "scene_runner",
    "ambientLight": [0.6, 0.6, 0.6],
    "skybox": "default_sky",
    "gravity": [0, -9.8, 0]
  }
}
```

### Step 2: Spawn Player
```json
{
  "jobId": "spawn_1708123456790",
  "jobType": "SPAWN_ENTITY",
  "status": "queued",
  "submittedAt": 1708123456790,
  "payload": {
    "id": "player_1",
    "type": "player",
    "transform": {
      "position": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1]
    },
    "material": {
      "shader": "standard",
      "texture": "player_skin",
      "color": [1, 1, 1]
    },
    "components": {
      "mesh": "player",
      "collider": "box",
      "script": "runner_controller"
    }
  }
}
```

### Step 3: Spawn Obstacles
```json
{
  "jobId": "spawn_1708123456791",
  "jobType": "SPAWN_ENTITY",
  "status": "queued",
  "submittedAt": 1708123456791,
  "payload": {
    "id": "obstacle_1",
    "type": "object",
    "transform": {
      "position": [10, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 2, 1]
    },
    "material": {
      "shader": "standard",
      "texture": "rock",
      "color": [0.5, 0.5, 0.5]
    },
    "components": {
      "mesh": "cube",
      "collider": "box",
      "script": ""
    }
  }
}
```

### Step 4: Start Game Loop
```json
{
  "jobId": "start_1708123456792",
  "jobType": "START_LOOP",
  "status": "queued",
  "submittedAt": 1708123456792,
  "payload": {
    "game_mode": "runner",
    "params": {
      "movement_speed": 8.0,
      "difficulty": "medium",
      "spawn_rules": {
        "interval": 2.0,
        "distance": 10.0
      },
      "scoring": {
        "points_per_second": 10,
        "obstacle_bonus": 50
      },
      "end_condition": {
        "type": "lives",
        "value": 3
      }
    }
  }
}
```

---

## Error Handling

### Invalid Payload
```json
{
  "success": false,
  "error": "Invalid job payload",
  "details": [
    "Missing required field: sceneId",
    "Invalid ambientLight: must be array of 3 numbers"
  ]
}
```

### Engine Offline
```json
{
  "success": false,
  "error": "Engine not connected",
  "action": "Job queued, will dispatch when engine connects"
}
```

### Job Timeout
```json
{
  "jobId": "build_1708123456789",
  "status": "failed",
  "error": "Job timeout after 30 seconds",
  "completedAt": 1708123486789
}
```

---

## Validation Rules

### Pre-Dispatch Validation
1. ✅ Job payload matches schema
2. ✅ All required fields present
3. ✅ Field types correct
4. ✅ Enum values valid
5. ✅ Array lengths correct
6. ✅ Number ranges valid

### Post-Dispatch Validation
1. ✅ Engine acknowledgment received
2. ✅ Job state transitions valid
3. ✅ Timeout monitoring active
4. ✅ Error handling ready

---

## Integration Checklist

- [ ] Engine implements all 4 job types
- [ ] Engine sends acknowledgment on job receipt
- [ ] Engine updates job status (running → completed/failed)
- [ ] Engine sends telemetry during START_LOOP
- [ ] Engine handles END_GAME cleanup
- [ ] Dashboard displays job queue status
- [ ] Dashboard shows telemetry data
- [ ] Error states handled gracefully

---



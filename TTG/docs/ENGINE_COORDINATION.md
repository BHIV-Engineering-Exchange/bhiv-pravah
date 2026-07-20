# Engine Coordination Document

**To:** Atharva Sharma (Engine Runtime Lead)  
**From:** Rudra Parmeshwar (Dashboard/Backend Lead)  
**Date:** 2024-01-15  
**Subject:** Engine Execution Contract v2.0

---

## Purpose

This document defines the **exact contract** your C++ engine must consume for TTG execution pipeline.

---

## Contract File

**Location:** `backend/engineExecutionContract.json`

This is the **single source of truth** for engine input format.

---

## What You Receive

Your engine will receive execution contracts via Socket.IO on the `/engine` namespace.

### Event: `dispatch_job`

**Payload Structure:**

```json
{
  "job": {
    "jobId": "start_exec_001",
    "jobType": "START_LOOP",
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "executionId": "exec_001",
    "payload": {
      "game_mode": "runner",
      "params": { ... }
    }
  },
  "gameplayContract": {
    "execution_id": "exec_001",
    "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "game_mode": "runner",
    "scene": { ... },
    "entities": [ ... ],
    "physics": { ... },
    "movement": { ... },
    "camera": { ... },
    "spawn_rules": { ... },
    "scoring": { ... },
    "player_params": { ... }
  }
}
```

---

## Complete Engine Contract Format

```json
{
  "execution_id": "exec_001",
  "trace_id": "uuid-v4-string",
  "game_mode": "runner | sidescroller | open_scene",
  
  "scene": {
    "scene_id": "scene_runner",
    "ambient_light": [0.6, 0.6, 0.6],
    "skybox": "default_sky"
  },
  
  "entities": [
    {
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
  ],
  
  "physics": {
    "gravity": [0, -9.8, 0],
    "friction": 0.5,
    "bounce": 0.3,
    "air_resistance": 0.1,
    "collision_force": 1.0
  },
  
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
    "frequency": 2,
    "distance": 10
  },
  
  "scoring": {
    "rules": {
      "distance": 1,
      "collectibles": 0,
      "time": 0
    },
    "end_conditions": ["collision"]
  },
  
  "player_params": {
    "health": 3,
    "jetpack": false
  }
}
```

---

## Field Descriptions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `execution_id` | string | Unique execution identifier |
| `trace_id` | string | Distributed trace ID (UUID v4) |
| `game_mode` | enum | "runner", "sidescroller", or "open_scene" |
| `entities` | array | Entity spawn instructions |
| `physics` | object | Physics parameters |
| `scoring` | object | Score calculation rules |

### Scene Configuration

| Field | Type | Description |
|-------|------|-------------|
| `scene.scene_id` | string | Scene identifier |
| `scene.ambient_light` | [r,g,b] | RGB values 0.0-1.0 |
| `scene.skybox` | string | Skybox asset name |

### Entity Spawn Instructions

Each entity has:
- `id` - Unique identifier
- `type` - "player", "npc", "object", "obstacle"
- `transform` - Position, rotation, scale (all [x,y,z])
- `material` - Shader, texture, color
- `components` - Mesh, collider, script

### Physics Parameters

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `gravity` | [x,y,z] | -20 to 0 | Gravity vector |
| `friction` | number | 0-1 | Surface friction |
| `bounce` | number | 0-1 | Bounciness |
| `air_resistance` | number | 0-1 | Air drag |
| `collision_force` | number | 0.1-2 | Impact multiplier |

### Movement Parameters

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `speed` | number | 1-15 | Movement speed |
| `jump_height` | number | 0-10 | Jump force |

### Spawn Rules

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `obstacles` | number | 0-10 | Obstacle types |
| `frequency` | number | 0.5-10 | Spawn interval (seconds) |
| `distance` | number | 5-50 | Distance between spawns |

### Scoring Rules

| Field | Type | Description |
|-------|------|-------------|
| `rules.distance` | number | Points per distance unit |
| `rules.collectibles` | number | Points per collectible |
| `rules.time` | number | Points per second |
| `end_conditions` | array | Win/lose conditions |

---

## What You Must Do

### 1. Consume Contract Directly

**DO:**
- ✅ Read `gameplayContract` from job payload
- ✅ Use values exactly as provided
- ✅ Apply physics parameters directly
- ✅ Spawn entities as specified

**DON'T:**
- ❌ Interpret or modify values
- ❌ Add default logic
- ❌ Skip fields
- ❌ Transform data

### 2. Acknowledge Jobs

When you receive a job, emit:

```javascript
socket.emit('job_ack', {
  jobId: job.jobId,
  status: 'running'
});
```

### 3. Report Progress

During execution, emit:

```javascript
socket.emit('job_progress', {
  jobId: job.jobId,
  progress: 0.5  // 0.0 to 1.0
});
```

### 4. Report Completion

When job completes:

```javascript
socket.emit('job_complete', {
  jobId: job.jobId,
  status: 'completed',
  result: { ... }
});
```

### 5. Report Failures

If job fails:

```javascript
socket.emit('job_failed', {
  jobId: job.jobId,
  error: 'Error message'
});
```

---

## Job Types

You will receive 3 job types per execution:

### 1. BUILD_SCENE
- Setup scene
- Apply ambient light
- Load skybox
- Set gravity

### 2. SPAWN_ENTITY
- Spawn entities (player, obstacles)
- Apply transforms
- Apply materials
- Attach components

### 3. START_LOOP
- Start game loop
- Apply movement parameters
- Enable spawn rules
- Track scoring

---

## Example Flow

```
1. Receive BUILD_SCENE job
   → Setup scene with ambient_light, skybox, gravity
   → Emit job_ack
   → Emit job_complete

2. Receive SPAWN_ENTITY job
   → Spawn player at position [0,0,0]
   → Apply material and components
   → Emit job_ack
   → Emit job_complete

3. Receive START_LOOP job
   → Start game loop with movement_speed=8
   → Enable obstacle spawning (frequency=2s)
   → Track score (distance=1 point per unit)
   → Emit job_ack
   → Game runs...
   → Emit job_complete when game ends
```

---

## Testing

### Test Contract

Use this for testing:

```json
{
  "execution_id": "test_001",
  "trace_id": "test-trace-001",
  "game_mode": "runner",
  "scene": {
    "scene_id": "scene_runner",
    "ambient_light": [0.6, 0.6, 0.6],
    "skybox": "default_sky"
  },
  "entities": [
    {
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
  ],
  "physics": {
    "gravity": [0, -9.8, 0],
    "friction": 0.5,
    "bounce": 0.3,
    "air_resistance": 0.1,
    "collision_force": 1.0
  },
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
    "frequency": 2,
    "distance": 10
  },
  "scoring": {
    "rules": {
      "distance": 1,
      "collectibles": 0,
      "time": 0
    },
    "end_conditions": ["collision"]
  },
  "player_params": {
    "health": 3,
    "jetpack": false
  }
}
```

---

## Integration Checklist

- [ ] Engine reads `gameplayContract` from job payload
- [ ] Engine applies physics parameters exactly
- [ ] Engine spawns entities as specified
- [ ] Engine emits `job_ack` on job receipt
- [ ] Engine emits `job_complete` on completion
- [ ] Engine emits `job_failed` on errors
- [ ] Engine handles all 3 job types (BUILD_SCENE, SPAWN_ENTITY, START_LOOP)
- [ ] Engine remains deterministic (no interpretation logic)

---

## Questions?

Contact: Rudra Parmeshwar  
File: `backend/engineExecutionContract.json`  
Test: `backend/test_engine_contract.js`

---

**This contract is FROZEN. No changes without coordination.**

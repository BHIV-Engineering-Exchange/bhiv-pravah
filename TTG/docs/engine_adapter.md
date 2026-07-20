# Engine Adapter Contract v1.0


## Overview

This document defines the contract between the Real-Time Micro-Bridge backend and the TG Engine (OpenGL runtime). It specifies the exact data format, socket events, and lifecycle states for job execution.

---

## 1. Job Transport Format

### 1.1 Outbound Job (Backend → Engine)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "BUILD_SCENE" | "LOAD_ASSETS" | "SPAWN_ENTITY",
  "world_spec": {
    "schema_version": "1.0",
    "world": {
      "id": "world_forest_01",
      "name": "Dark Forest",
      "gravity": [0, -9.8, 0]
    },
    "scene": {
      "id": "forest_scene",
      "ambientLight": [0.4, 0.6, 0.4],
      "skybox": "forest_sky"
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
          "texture": "player_armor",
          "color": [1, 1, 1]
        },
        "components": {
          "mesh": "player",
          "collider": "box",
          "script": "player_controller"
        }
      }
    ],
    "quests": []
  },
  "payload": {
    "sceneId": "forest_scene",
    "ambientLight": [0.4, 0.6, 0.4],
    "skybox": "forest_sky"
  },
  "execution_params": {
    "priority": "normal",
    "timeout_ms": 300000
  },
  "submitted_at": 1738425600000,
  "user_id": "user_123"
}
```

### 1.2 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string (UUID v4) | Yes | Unique job identifier |
| `job_type` | enum | Yes | One of: BUILD_SCENE, LOAD_ASSETS, SPAWN_ENTITY |
| `world_spec` | object | Yes | Complete world specification (see engine_schema.json) |
| `payload` | object | Yes | Job-specific data extracted from world_spec |
| `execution_params` | object | Yes | Execution hints (priority, timeout) |
| `submitted_at` | number | Yes | Unix timestamp (ms) when job was created |
| `user_id` | string | Yes | User who submitted the job |

---

## 2. Job Types & Payloads

### 2.1 BUILD_SCENE

Creates the scene environment (lighting, skybox).

**Payload:**
```json
{
  "sceneId": "forest_scene",
  "ambientLight": [0.4, 0.6, 0.4],
  "skybox": "forest_sky"
}
```

### 2.2 LOAD_ASSETS

Loads required meshes and textures.

**Payload:**
```json
{
  "assets": ["player", "wolf", "player_armor", "wolf_fur", "forest_sky"]
}
```

### 2.3 SPAWN_ENTITY

Instantiates an entity in the world.

**Payload:**
```json
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
    "texture": "player_armor",
    "color": [1, 1, 1]
  },
  "components": {
    "mesh": "player",
    "collider": "box",
    "script": "player_controller"
  }
}
```

---

## 3. Lifecycle States

Jobs follow a strict state machine:

```
queued → dispatched → running → completed
                              → failed
```

### State Definitions

| State | Description | Terminal |
|-------|-------------|----------|
| `queued` | Job added to queue, waiting for dispatch | No |
| `dispatched` | Job sent to engine, awaiting acknowledgment | No |
| `running` | Engine actively processing job | No |
| `completed` | Job finished successfully | Yes |
| `failed` | Job encountered error | Yes |

### Valid Transitions

- `queued` → `dispatched`, `failed`
- `dispatched` → `running`, `failed`
- `running` → `completed`, `failed`
- `completed` → (none)
- `failed` → (none)

---

## 4. Inbound Telemetry (Engine → Backend)

### 4.1 Job Started

```json
{
  "event": "job_started",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1738425601000
}
```

### 4.2 Job Progress

```json
{
  "event": "job_progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": 45,
  "timestamp": 1738425603000
}
```

**Note:** `progress` is 0-100 integer.

### 4.3 Job Completed

```json
{
  "event": "job_completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "entities_spawned": 2,
    "render_time_ms": 2340
  },
  "timestamp": 1738425605000
}
```

### 4.4 Job Failed

```json
{
  "event": "job_failed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "ASSET_NOT_FOUND",
  "details": "Texture 'wolf_fur' not found in asset registry",
  "timestamp": 1738425605000
}
```

### 4.5 Error Codes

| Code | Description |
|------|-------------|
| `ASSET_NOT_FOUND` | Required asset missing |
| `INVALID_ENTITY` | Entity data malformed |
| `SCENE_BUILD_FAILED` | Scene creation error |
| `TIMEOUT` | Job exceeded timeout |
| `ENGINE_ERROR` | Internal engine error |

---

## 5. Socket Events

### 5.1 Connection

**Namespace:** `/engine`  
**Authentication:** JWT in `auth.token` (handshake)

### 5.2 Outbound Events (Backend → Engine)

| Event | Payload | Description |
|-------|---------|-------------|
| `engine_job` | Job object | Dispatch job to engine |
| `ready_ack` | `{ status, ts }` | Acknowledge engine ready |
| `heartbeat_ack` | `{ ts }` | Acknowledge heartbeat |

### 5.3 Inbound Events (Engine → Backend)

| Event | Payload | Description |
|-------|---------|-------------|
| `engine_ready` | (none) | Engine connected and ready |
| `engine_heartbeat` | (none) | Liveness check (every 5s) |
| `job_started` | Telemetry object | Job execution began |
| `job_progress` | Telemetry object | Progress update |
| `job_completed` | Telemetry object | Job finished successfully |
| `job_failed` | Telemetry object | Job encountered error |

---

## 6. Execution Parameters

```json
{
  "priority": "normal" | "high" | "low",
  "timeout_ms": 300000
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `priority` | enum | "normal" | Job priority (future use) |
| `timeout_ms` | number | 300000 | Max execution time (5 minutes) |

---

## 7. Example Flow

### Successful Job Execution

```
1. Backend: emit("engine_job", { job_id: "abc123", ... })
2. Engine:  emit("job_started", { job_id: "abc123", ... })
3. Engine:  emit("job_progress", { job_id: "abc123", progress: 50 })
4. Engine:  emit("job_completed", { job_id: "abc123", result: {...} })
5. Backend: Update job status to "completed"
```

### Failed Job Execution

```
1. Backend: emit("engine_job", { job_id: "abc123", ... })
2. Engine:  emit("job_started", { job_id: "abc123", ... })
3. Engine:  emit("job_failed", { job_id: "abc123", error: "ASSET_NOT_FOUND" })
4. Backend: Update job status to "failed"
```

---

## 8. Security

All engine messages use existing security layer:

- **JWT Authentication:** Socket handshake
- **HMAC Signatures:** `job_status` messages (if required)
- **Nonce Protection:** Replay prevention
- **Heartbeat:** 5s interval, 10s timeout

See `docs/engine_security.md` for details.

---

## 9. Telemetry Integration

Engine telemetry is normalized into existing telemetry system:

- **Append-only logging:** `telemetry_samples.json`
- **Sequence numbers:** Deterministic replay
- **Event types:** `JOB_STARTED`, `JOB_PROGRESS`, `JOB_COMPLETED`, `JOB_FAILED`

**Critical:** Telemetry is **observability only**. It does NOT control execution authority.

---



## 10. Validation

Jobs are validated against `engine_schema.json` before dispatch:

```javascript
const validateWorldSpec = require('./world_spec_validator');

try {
  validateWorldSpec(worldSpec);
  // Proceed with dispatch
} catch (err) {
  // Reject job
}
```

---

## Appendix A: Complete Job Example

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "BUILD_SCENE",
  "world_spec": {
    "schema_version": "1.0",
    "world": {
      "id": "world_forest_01",
      "name": "Dark Forest",
      "gravity": [0, -9.8, 0]
    },
    "scene": {
      "id": "forest_scene",
      "ambientLight": [0.4, 0.6, 0.4],
      "skybox": "forest_sky"
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
          "texture": "player_armor",
          "color": [1, 1, 1]
        },
        "components": {
          "mesh": "player",
          "collider": "box",
          "script": "player_controller"
        }
      }
    ],
    "quests": []
  },
  "payload": {
    "sceneId": "forest_scene",
    "ambientLight": [0.4, 0.6, 0.4],
    "skybox": "forest_sky"
  },
  "execution_params": {
    "priority": "normal",
    "timeout_ms": 300000
  },
  "submitted_at": 1738425600000,
  "user_id": "user_123"
}
```


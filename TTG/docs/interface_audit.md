# Interface Audit — Current System State

**Audit Date:** Feb 1, 2025  
**Purpose:** Document all data formats, event schemas, and job payloads before engine hardening

---

## 1. Socket Events (Client → Server)

### 1.1 Authentication
**Event:** `connection` (handshake)  
**Auth Method:** JWT in query params  
**Payload:** N/A (handled by middleware)

### 1.2 Presence Updates
**Event:** `presence`  
**Payload:**
```json
"active" | "idle" | "disconnected"
```

### 1.3 User Actions
**Event:** `action`  
**Payload:**
```json
{
  "type": "click" | "inspect" | "interact" | "spam_click",
  "payload": { /* action-specific data */ },
  "ts": 1738425600000,
  "nonce": "abc123",
  "sig": "hmac_signature_here"
}
```
**Security:** HMAC signature + nonce validation required

### 1.4 Agent Heartbeat
**Event:** `agent_heartbeat`  
**Payload:**
```json
{
  "agentId": "HintAgent",
  "ts": 1738425600000,
  "nonce": "xyz789",
  "sig": "hmac_signature_here"
}
```

### 1.5 World Generation (DUAL FORMAT — NEEDS FIXING)
**Event:** `generate_world`  

**Format A (Legacy Cube):**
```json
{
  "config": {
    "color": "#66ffdd",
    "size": 1.5
  },
  "submittedAt": 1738425600000
}
```

**Format B (Engine Schema):**
```json
{
  "config": {
    "schema_version": "1.0",
    "world": { "id": "world_001", "name": "Demo", "gravity": [0, -9.8, 0] },
    "scene": { "id": "scene_main", "ambientLight": [1, 1, 1], "skybox": "default" },
    "entities": [
      {
        "id": "cube_01",
        "type": "object",
        "transform": { "position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1] },
        "material": { "shader": "standard", "texture": "none", "color": [1, 1, 1] },
        "components": { "mesh": "cube", "collider": "box" }
      }
    ],
    "quests": []
  },
  "submittedAt": 1738425600000
}
```

**⚠️ PROBLEM:** Two formats handled by inline check (`isCubeConfig`). Needs adapter layer.

---

## 2. Socket Events (Server → Client)

### 2.1 Authentication Context
**Event:** `auth_context`  
**Payload:**
```json
{
  "userId": "user_123",
  "role": "user" | "admin",
  "isSimulated": false
}
```

### 2.2 Agent Nonces
**Event:** `agent_nonce`  
**Payload:**
```json
{
  "HintAgent": "nonce_abc",
  "NavAgent": "nonce_def",
  "PredictAgent": "nonce_ghi",
  "RuleAgent": "nonce_jkl"
}
```

### 2.3 Presence Updates
**Event:** `presence_update`  
**Payload:**
```json
{
  "user_123": {
    "userId": "user_123",
    "role": "user",
    "device": "desktop",
    "socketId": "socket_abc",
    "state": "active",
    "connectedAt": 1738425600000,
    "lastActiveAt": 1738425600000
  }
}
```

### 2.4 Agent Updates
**Event:** `agent_update`  
**Payload:**
```json
{
  "agentId": "HintAgent",
  "state": "triggered",
  "reason": "spam_detected",
  "message": "Slow down! Try inspecting instead.",
  "ts": 1738425600000
}
```

### 2.5 Job Status
**Event:** `job_status`  
**Payload:**
```json
{
  "jobId": "batch123:BUILD_SCENE",
  "jobType": "BUILD_SCENE",
  "status": "queued" | "started" | "finished" | "failed",
  "error": "BAD_ASSET: corrupted_texture.png",
  "submittedAt": 1738425600000,
  "userId": "user_123"
}
```

### 2.6 Cube Update (Legacy)
**Event:** `cube_update`  
**Payload:**
```json
{
  "color": "#66ffdd",
  "size": 1.5
}
```
**⚠️ PROBLEM:** Should use engine schema format

### 2.7 Engine Job Finished
**Event:** `engine_job_finished`  
**Payload:**
```json
{
  "jobType": "BUILD_SCENE",
  "jobId": "batch123:BUILD_SCENE",
  "finishedAt": 1738425600000
}
```

### 2.8 Engine Job Failed
**Event:** `engine_job_failed`  
**Payload:**
```json
{
  "jobType": "SPAWN_ENTITY",
  "jobId": "batch123:SPAWN_ENTITY",
  "error": "INVALID_ENTITY: missing transform",
  "failedAt": 1738425600000
}
```

---

## 3. Engine Socket Events (`/engine` namespace)

### 3.1 Engine Connection
**Event:** `connection`  
**Auth:** JWT verification via `verifyEngineJWT()`  
**Payload:** N/A

### 3.2 Engine Heartbeat
**Event:** `engine_heartbeat`  
**Payload:** Empty (timestamp tracked server-side)  
**Timeout:** 10s (disconnect if no heartbeat)

### 3.3 Engine Ready
**Event:** `engine_ready`  
**Payload:** Empty  
**Response:** Server sends all pending jobs via `engine_job` event

### 3.4 Engine Job Dispatch
**Event:** `engine_job` (server → engine)  
**Payload:**
```json
{
  "jobId": "uuid-v4",
  "userId": "user_123",
  "jobType": "BUILD_SCENE" | "LOAD_ASSETS" | "SPAWN_ENTITY",
  "payload": {
    // Job-specific data (see section 4)
  },
  "submittedAt": 1738425600000
}
```

### 3.5 Engine Status Report
**Event:** `engine_status` (engine → server)  
**Payload:**
```json
{
  "nonce": "engine_nonce_123",
  "sig": "hmac_signature",
  "payload": {
    "jobId": "uuid-v4",
    "jobType": "BUILD_SCENE",
    "status": "completed" | "failed"
  }
}
```
**Security:** Signature + nonce validation required

---

## 4. Job Queue Payloads

### 4.1 CUBE_PREVIEW (Legacy)
```json
{
  "jobId": "batch123:CUBE_PREVIEW",
  "userId": "user_123",
  "jobType": "CUBE_PREVIEW",
  "payload": {
    "color": "#66ffdd",
    "size": 1.5
  },
  "submittedAt": 1738425600000
}
```
**⚠️ PROBLEM:** Not engine-compatible

### 4.2 BUILD_SCENE
```json
{
  "jobId": "uuid-v4",
  "jobType": "BUILD_SCENE",
  "payload": {
    "sceneId": "forest_scene",
    "ambientLight": [0.4, 0.6, 0.4],
    "skybox": "forest_sky"
  }
}
```

### 4.3 LOAD_ASSETS
```json
{
  "jobId": "uuid-v4",
  "jobType": "LOAD_ASSETS",
  "payload": {
    "assets": ["player", "player_armor", "wolf", "wolf_fur"]
  }
}
```

### 4.4 SPAWN_ENTITY
```json
{
  "jobId": "uuid-v4",
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
      "texture": "player_armor",
      "color": [1, 1, 1]
    },
    "components": {
      "mesh": "player",
      "collider": "box",
      "script": "player_controller"
    }
  }
}
```

---

## 5. Engine Schema (v1.0)

**File:** `backend/engine/schema/engine_schema.schema.json`  
**Validation:** AJV strict mode

**Required Fields:**
- `schema_version` (string)
- `world` (object: id, name, gravity)
- `scene` (object: id, ambientLight, skybox)
- `entities` (array, minItems: 1)
  - Each entity: id, type, transform, material, components
- `quests` (array, optional but must be present)

**No optional fields allowed in entities.**

---

## 6. Preview Logic (Three.js)

**Component:** `frontend/src/components/CubePreview.jsx`

**Current Input:**
```json
{
  "color": "#66ffdd",
  "size": 1.5
}
```

**Current Behavior:**
- Creates `THREE.BoxGeometry(size, size, size)`
- Sets `material.color.set(color)`

**⚠️ PROBLEM:** Does not consume engine schema. Needs adapter.

---

## 7. Issues Identified

### 7.1 Dual Format Problem
- `generate_world` accepts both legacy cube format and engine schema
- Inline check (`isCubeConfig`) is fragile
- Three.js preview uses different format than engine

**Solution:** Create adapter layer to normalize all inputs to engine schema

### 7.2 Job Lifecycle Ambiguity
- Current states: `queued`, `started`, `finished`, `failed`
- Missing: `dispatched`, `running`
- No explicit state machine

**Solution:** Implement strict lifecycle with state transitions

### 7.3 Preview Mismatch
- Three.js preview uses `{color, size}`
- Engine expects full entity spec
- Visual preview ≠ engine reality

**Solution:** Update CubePreview to consume engine schema

### 7.4 Job Type Inconsistency
- `job_payload_samples.json` shows `SPAWN_ENTITIES` (plural)
- `engine_job_queue.js` generates `SPAWN_ENTITY` (singular)

**Solution:** Standardize to `SPAWN_ENTITY` (singular)

---

## 8. Recommendations

### Priority 1 (Day 1)
1. ✅ Create adapter layer (`engine_adapter.js`)
2. ✅ Update CubePreview to use engine schema
3. ✅ Remove dual format handling in `socket.js`

### Priority 2 (Day 2)
4. Add `dispatched` and `running` states to job lifecycle
5. Implement state machine for job transitions
6. Add lifecycle validation

### Priority 3 (Day 3)
7. Add telemetry for all state transitions
8. Implement replay mechanism
9. Add failure simulation tests

---

**Audit Completed By:** Rudra Parmeshwar  
**Next Steps:** Implement adapter layer (Day 1c)

# Engine Capability Map

**Version:** 1.0  
**Last Updated:** 2025-01-26  
**Target Engine:** TG Engine (Atharva's Runtime)

---

## Overview

This document defines the capabilities, constraints, and safe operating limits of the TG Engine runtime. Use this map for automated validation before job dispatch.

---

## Supported Job Types

### High-Level Jobs (Gameplay Contract)

| Job Type | Description | Required Payload Fields | Status |
|----------|-------------|------------------------|--------|
| `START_GAME` | Initialize game with gameplay contract | `game_mode`, `movement`, `camera`, `spawn_rules`, `score_rules`, `end_conditions` | ✅ Supported |
| `STOP_GAME` | End game session | `reason`, `final_score`, `duration` | ✅ Supported |
| `UPDATE_CONFIG` | Update game configuration at runtime | Any valid config fields | ✅ Supported |

### Low-Level Jobs (Engine Operations)

| Job Type | Description | Required Payload Fields | Status |
|----------|-------------|------------------------|--------|
| `BUILD_SCENE` | Create game scene with environment | `sceneId` | ✅ Supported |
| `SPAWN_ENTITY` | Spawn single entity | `id`, `type` | ✅ Supported |
| `SPAWN_ENTITIES` | Spawn multiple entities (batch) | `id`, `type` | ✅ Supported |
| `START_LOOP` | Start game loop | `game_mode`, `params` | ✅ Supported |
| `LOAD_ASSETS` | Load assets into memory | `assets` (array) | ✅ Supported |
| `MOVE_ENTITY` | Move entity to position | `id`, `position` | ✅ Supported |
| `UPDATE_PROPERTY` | Update entity property | `id`, `property`, `value` | ✅ Supported |
| `DELETE_ENTITY` | Remove entity from scene | `id` | ✅ Supported |
| `EMIT_EVENT` | Emit custom event | `event`, `data` | ✅ Supported |

---

## Supported Entity Properties

### Transform Properties

| Property | Type | Format | Range | Description |
|----------|------|--------|-------|-------------|
| `position` | Array | `[x, y, z]` | `[-1000, 1000]` per axis | Entity position in world space |
| `rotation` | Array | `[x, y, z]` | `[0, 360]` degrees | Euler angles rotation |
| `scale` | Array | `[x, y, z]` | `[0.1, 10]` per axis | Entity scale multiplier |

### Gameplay Properties

| Property | Type | Range | Default | Description |
|----------|------|-------|---------|-------------|
| `health` | Number | `[1, 100]` | `3` | Entity health/lives |
| `speed` | Number | `[1, 15]` | `5` | Movement speed |
| `jump_height` | Number | `[0, 10]` | `3` | Jump force/height |
| `score` | Number | `[0, ∞]` | `0` | Player score |
| `velocity` | Array `[x, y, z]` | `[-50, 50]` per axis | `[0, 0, 0]` | Entity velocity vector |

### Physics Properties

| Property | Type | Range | Default | Description |
|----------|------|-------|---------|-------------|
| `gravity` | Number | `[-20, 0]` | `-9.8` | Gravity force (negative = downward) |
| `friction` | Number | `[0, 1]` | `0.5` | Surface friction coefficient |
| `bounce` | Number | `[0, 1]` | `0.3` | Restitution/bounciness |
| `air_resistance` | Number | `[0, 1]` | `0.1` | Air drag coefficient |
| `collision_force` | Number | `[0.1, 2]` | `1.0` | Collision impact multiplier |

### Material Properties

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `shader` | String | `standard`, `unlit`, `pbr` | Shader type |
| `texture` | String | Asset name | Texture identifier |
| `color` | Array | `[r, g, b]` (0-1) | RGB color values |

### Component Properties

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `mesh` | String | Asset name | 3D mesh identifier |
| `collider` | String | `box`, `sphere`, `capsule`, `mesh` | Collider type |
| `script` | String | Script name | Behavior script identifier |

---

## Supported Transform Operations

### Absolute Positioning
```json
{
  "position": [10, 0, 5],
  "rotation": [0, 90, 0],
  "scale": [1, 1, 1]
}
```

### Relative Movement (Delta)
```json
{
  "position": "+[1, 0, 0]",
  "rotation": "+[0, 5, 0]"
}
```

### Velocity-Based Movement
```json
{
  "velocity": [2, 0, 0]
}
```

---

## Game Modes

| Mode | Description | Camera Default | Movement Type |
|------|-------------|----------------|---------------|
| `runner` | Endless runner | `third_person` | Forward auto-scroll |
| `sidescroller` | 2D side-scrolling | `side_view` | Left/right + jump |
| `open_scene` | Free exploration | `third_person` | Full 3D movement |

---

## Camera Types

| Type | Description | Distance Range | Use Case |
|------|-------------|----------------|----------|
| `third_person` | Behind player | `[5, 20]` | Runner, exploration |
| `side_view` | 2D side camera | `[8, 15]` | Sidescroller |
| `top_down` | Overhead view | `[10, 30]` | Strategy, puzzle |

---

## Spawn Rules

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `obstacles` | Number | `[0, 10]` | `2` | Number of obstacle types |
| `frequency` | Number | `[0.5, 10]` seconds | `2` | Spawn interval |
| `distance` | Number | `[5, 50]` units | `10` | Spawn distance from player |

---

## Score Rules

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `distance` | Number | `[0, 10]` | `1` | Points per distance unit |
| `collectibles` | Number | `[0, 100]` | `10` | Points per collectible |

---

## End Conditions

| Condition | Description | Parameters |
|-----------|-------------|------------|
| `collision` | Game ends on collision | None |
| `time_limit` | Game ends after time | `duration_ms` |
| `distance_goal` | Game ends at distance | `target_distance` |
| `score_goal` | Game ends at score | `target_score` |

---

## Safe Job Limits

### Queue Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max concurrent jobs | `1` | Jobs process sequentially |
| Max queued jobs | `100` | Queue capacity |
| Max retries per job | `2` | Retry attempts on failure |
| Job timeout | `15000ms` | Max execution time per job |
| Stale job threshold | `120000ms` | Auto-cleanup after 2 minutes |

### Entity Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max entities per scene | `1000` | Total entity count |
| Max spawns per batch | `50` | Entities per SPAWN_ENTITIES job |
| Max assets per load | `100` | Assets per LOAD_ASSETS job |

### Performance Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max scene complexity | `Medium` | Polygon/draw call budget |
| Max physics objects | `200` | Active physics bodies |
| Target frame rate | `60 FPS` | Rendering target |

---

## Validation Rules

### Entity ID Validation
- **Pattern:** `^[a-zA-Z0-9_-]+$`
- **Min length:** 1
- **Max length:** 64
- **Examples:** `player_1`, `obstacle-rock`, `coin_01`

### Scene ID Validation
- **Pattern:** `^[a-z0-9_]+$`
- **Min length:** 1
- **Max length:** 32
- **Examples:** `scene_runner`, `forest_level_01`

### Asset Name Validation
- **Pattern:** `^[a-zA-Z0-9_]+$`
- **Min length:** 1
- **Max length:** 64
- **Examples:** `player_armor`, `wolf_fur`, `rock_texture`

---

## Job State Machine

```
queued → dispatched → running → completed
                              ↘ failed
```

### Valid Transitions
- `queued` → `dispatched`, `failed`
- `dispatched` → `running`, `failed`, `queued` (retry)
- `running` → `completed`, `failed`, `queued` (retry)
- `completed` → (terminal)
- `failed` → (terminal)

---

## Error Codes

| Code | Description | Retry? |
|------|-------------|--------|
| `TIMEOUT` | Job exceeded timeout | ✅ Yes |
| `ENGINE_DISCONNECTED` | Engine connection lost | ✅ Yes |
| `INVALID_PAYLOAD` | Malformed job payload | ❌ No |
| `ASSET_NOT_FOUND` | Required asset missing | ❌ No |
| `ENTITY_NOT_FOUND` | Target entity doesn't exist | ❌ No |
| `SCENE_NOT_LOADED` | Scene not initialized | ✅ Yes |
| `VALIDATION_FAILED` | Contract validation failed | ❌ No |

---

## Security Constraints

### Prototype Pollution Protection
- Reject contracts with `__proto__`, `constructor`, `prototype` keys
- Sanitize all input objects before processing

### Numeric Range Enforcement
- All numeric properties must be within documented ranges
- NaN, Infinity, -Infinity are rejected
- Floating point precision: 6 decimal places

### String Sanitization
- Entity IDs: alphanumeric + underscore/dash only
- No special characters in identifiers
- Max string length: 256 characters

---

## Integration Points

### Input: Intent Layer → Execution Dispatcher
- **Format:** TG Engine Gameplay Contract
- **Validation:** JSON Schema + Contract Validator
- **Security:** HMAC signature + nonce verification

### Output: Execution Dispatcher → TG Engine
- **Format:** Engine Job Stream
- **Transport:** Socket.IO `/engine` namespace
- **Protocol:** Job dispatch → status updates → completion

### Storage: Execution Traces → Bucket
- **Format:** Execution Trace Schema
- **Location:** `backend/bucket_artifacts/`
- **Retention:** Configurable (default: 7 days)

---

## Usage Example

### Pre-Dispatch Validation
```javascript
const { validateContract } = require('./validation/contract_validator');

// Validate job before dispatch
const result = validateContract(job);
if (!result.valid) {
  console.error('Contract rejected:', result.errors);
  return;
}

// Check against capability limits
if (job.payload.movement?.speed > 15) {
  console.error('Speed exceeds safe limit (15)');
  return;
}

// Dispatch to engine
dispatchToEngine(job);
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-26 | Initial capability map |

---

## Notes

- This capability map is based on the current TG Engine implementation
- Limits are conservative to ensure stability
- Contact Atharva Sharma for engine runtime updates
- Update this document when engine capabilities change

---

**Maintained by:** Execution Layer Team  
**Engine Owner:** Atharva Sharma (TG Engine Runtime)

# Engine Schema Validation Notes — v1.0 FROZEN

**Schema File:** `backend/engine/engine_schema.json`  
**Freeze Date:** Feb 5, 2025  
**Status:** LOCKED — No breaking changes allowed

---

## 1. Schema Philosophy

### 1.1 Zero Ambiguity
- Every field has explicit type, format, and constraints
- No "string" without pattern or length constraints
- No optional fields in critical paths
- No implicit defaults

### 1.2 Engine-Agnostic
- All identifiers are symbolic (not file paths)
- Engine resolves `mesh: "cube"` → `assets/cube.obj`
- Control plane never touches asset loading

### 1.3 Deterministic
- No timestamps in world data (only in job metadata)
- No random values without explicit seeds
- Stable entity ordering
- Reproducible from JSON alone

---

## 2. Field-by-Field Validation

### 2.1 schema_version
```json
"schema_version": "1.0"
```
- **Type:** string (const)
- **Value:** Must be exactly `"1.0"`
- **Purpose:** Version lock for compatibility tracking
- **Breaking changes:** Forbidden. Use v2.0 for new schema.

---

### 2.2 world

#### world.id
```json
"id": "world_forest_01"
```
- **Type:** string
- **Pattern:** `^world_[a-z0-9_]+$`
- **Examples:** `world_forest_01`, `world_demo`, `world_test_arena`
- **Invalid:** `World1`, `forest`, `world-demo` (no hyphens)

#### world.name
```json
"name": "Dark Forest"
```
- **Type:** string
- **Length:** 1-64 characters
- **Purpose:** Human-readable label (UI display)
- **Examples:** `"Dark Forest"`, `"Tutorial Arena"`, `"PvP Zone"`

#### world.gravity
```json
"gravity": [0, -9.8, 0]
```
- **Type:** array of 3 numbers
- **Format:** `[x, y, z]`
- **Standard:** `[0, -9.8, 0]` (Earth gravity)
- **Custom:** `[0, -3.7, 0]` (Mars), `[0, 0, 0]` (space)

---

### 2.3 scene

#### scene.id
```json
"id": "scene_main"
```
- **Type:** string
- **Pattern:** `^scene_[a-z0-9_]+$`
- **Examples:** `scene_main`, `scene_forest`, `scene_boss_arena`

#### scene.ambientLight
```json
"ambientLight": [0.4, 0.6, 0.4]
```
- **Type:** array of 3 numbers
- **Range:** 0.0 - 1.0 per channel
- **Format:** `[r, g, b]`
- **Examples:** 
  - `[1, 1, 1]` — bright white
  - `[0.4, 0.6, 0.4]` — greenish forest
  - `[0.1, 0.1, 0.2]` — dark blue night

#### scene.skybox
```json
"skybox": "forest_sky"
```
- **Type:** string (symbolic identifier)
- **Min length:** 1
- **Examples:** `"forest_sky"`, `"desert_sky"`, `"none"`
- **Engine resolves:** `"forest_sky"` → `assets/skyboxes/forest/`

---

### 2.4 entities

**Minimum:** 1 entity required  
**Maximum:** No limit (performance is engine concern)

#### entity.id
```json
"id": "player_1"
```
- **Type:** string
- **Pattern:** `^[a-z0-9_]+$`
- **Uniqueness:** Must be unique within entities array
- **Examples:** `player_1`, `wolf_01`, `tree_oak_05`

#### entity.type
```json
"type": "player"
```
- **Type:** string (enum)
- **Values:** `"player"`, `"npc"`, `"object"`
- **Purpose:** Semantic categorization for engine systems
- **No custom types allowed**

---

### 2.5 transform

#### position
```json
"position": [0, 0, 0]
```
- **Type:** array of 3 numbers
- **Format:** `[x, y, z]` in world space
- **Units:** Engine-defined (typically meters)

#### rotation
```json
"rotation": [0, 0, 0]
```
- **Type:** array of 3 numbers
- **Format:** `[x, y, z]` Euler angles in **radians**
- **Not degrees:** `[0, 1.57, 0]` = 90° Y-axis rotation
- **Range:** Typically 0 to 2π, but no hard limit

#### scale
```json
"scale": [1, 1, 1]
```
- **Type:** array of 3 numbers
- **Format:** `[x, y, z]` scale factors
- **Constraint:** Must be > 0 (exclusiveMinimum)
- **Invalid:** `[0, 1, 1]`, `[-1, 1, 1]`
- **Uniform scale:** `[2, 2, 2]` doubles size

---

### 2.6 material

#### shader
```json
"shader": "standard"
```
- **Type:** string (symbolic)
- **Min length:** 1
- **Examples:** `"standard"`, `"unlit"`, `"pbr"`, `"toon"`
- **Engine resolves:** Shader program lookup

#### texture
```json
"texture": "player_armor"
```
- **Type:** string (symbolic)
- **Min length:** 1
- **Special value:** `"none"` for untextured materials
- **Examples:** `"player_armor"`, `"wood_oak"`, `"none"`

#### color
```json
"color": [1, 1, 1]
```
- **Type:** array of 3 numbers
- **Range:** 0.0 - 1.0 per channel
- **Format:** `[r, g, b]`
- **Purpose:** Base color / tint
- **Examples:**
  - `[1, 1, 1]` — white (no tint)
  - `[1, 0, 0]` — red
  - `[0.4, 1, 0.87]` — cyan (#66ffdd in 0-1 range)

**Hex to RGB conversion:**
```
#66ffdd → [0x66/255, 0xff/255, 0xdd/255] → [0.4, 1.0, 0.867]
```

---

### 2.7 components

#### mesh
```json
"mesh": "cube"
```
- **Type:** string (symbolic)
- **Min length:** 1
- **Examples:** `"cube"`, `"sphere"`, `"player"`, `"wolf"`
- **Engine resolves:** Mesh asset lookup

#### collider
```json
"collider": "box"
```
- **Type:** string (enum)
- **Values:** `"box"`, `"sphere"`, `"none"`
- **Purpose:** Physics collision shape
- **No custom colliders**

#### script (optional)
```json
"script": "player_controller"
```
- **Type:** string
- **Default:** `""` (empty string if no script)
- **Examples:** `"player_controller"`, `"hostile_ai"`, `""`
- **Purpose:** Behavior hook (future use)

---

### 2.8 quests

**Can be empty array:** `[]`

#### quest.id
```json
"id": "quest_defeat_wolf"
```
- **Type:** string
- **Pattern:** `^quest_[a-z0-9_]+$`
- **Examples:** `quest_defeat_wolf`, `quest_collect_herbs`

#### quest.triggerEntity
```json
"triggerEntity": "wolf_1"
```
- **Type:** string
- **Purpose:** References entity.id
- **Validation:** Should exist in entities array (not enforced by schema)

#### quest.goal
```json
"goal": "defeat"
```
- **Type:** string
- **Min length:** 1
- **Examples:** `"defeat"`, `"collect"`, `"reach_location"`

---

### 2.9 jobs (NEW)

**Purpose:** Track job lifecycle for engine integration

#### jobId
```json
"jobId": "abc123:BUILD_SCENE"
```
- **Type:** string
- **Format:** Free-form (UUID or batch:type)
- **Examples:** `"uuid-v4"`, `"batch123:BUILD_SCENE"`

#### jobType
```json
"jobType": "BUILD_SCENE"
```
- **Type:** string (enum)
- **Values:** `"BUILD_SCENE"`, `"LOAD_ASSETS"`, `"SPAWN_ENTITY"`
- **FROZEN:** No new job types without schema v2.0

#### status
```json
"status": "queued"
```
- **Type:** string (enum)
- **Values:** `"queued"`, `"dispatched"`, `"running"`, `"completed"`, `"failed"`
- **State machine:**
  ```
  queued → dispatched → running → completed
                              ↘ failed
  ```

#### Timestamps
- **submittedAt:** Required (Unix ms)
- **dispatchedAt:** Optional (set when dispatched to engine)
- **completedAt:** Optional (set when completed/failed)

#### error
```json
"error": "BAD_ASSET: corrupted_texture.png"
```
- **Type:** string
- **Required when:** status = "failed"
- **Format:** Free-form error message

---

## 3. Validation Rules

### 3.1 Structural Rules
1. All required fields must be present
2. No additional properties allowed (`additionalProperties: false`)
3. Arrays must meet min/max item constraints
4. Enums must match exactly (case-sensitive)

### 3.2 Semantic Rules
1. Entity IDs must be unique within entities array
2. Quest triggerEntity should reference valid entity.id
3. Job status transitions must follow state machine
4. Timestamps must be monotonically increasing

### 3.3 Engine Contract Rules
1. All symbolic identifiers (mesh, texture, shader) are engine's responsibility
2. Control plane never validates asset existence
3. Engine must reject invalid symbolic references
4. Engine must handle missing assets gracefully

---

## 4. Validation Implementation

**File:** `backend/engine/world_spec_validator.js`  
**Library:** AJV (JSON Schema validator)  
**Mode:** Strict (no type coercion)

```javascript
const Ajv = require("ajv");
const schema = require("./schema/engine_schema.schema.json");

const ajv = new Ajv({ allErrors: true, strict: true });
const validate = ajv.compile(schema);

function validateWorldSpec(data) {
  const valid = validate(data);
  if (!valid) {
    throw new Error(
      "World spec validation failed: " +
      JSON.stringify(validate.errors, null, 2)
    );
  }
  return data;
}
```

---

## 5. Common Validation Errors

### 5.1 Missing Required Field
```
Error: data must have required property 'jobs'
```
**Fix:** Add `"jobs": []` to root object

### 5.2 Invalid Pattern
```
Error: data.world.id must match pattern "^world_[a-z0-9_]+$"
```
**Fix:** Change `"World1"` → `"world_1"`

### 5.3 Out of Range
```
Error: data.scene.ambientLight[0] must be <= 1
```
**Fix:** Change `[1.5, 1, 1]` → `[1, 1, 1]`

### 5.4 Invalid Enum
```
Error: data.entities[0].type must be equal to one of: player, npc, object
```
**Fix:** Change `"enemy"` → `"npc"`

### 5.5 Scale Zero or Negative
```
Error: data.entities[0].transform.scale[0] must be > 0
```
**Fix:** Change `[0, 1, 1]` → `[1, 1, 1]`

---

## 6. Breaking vs Non-Breaking Changes

### ✅ Allowed (Non-Breaking)
- Adding new optional fields with defaults
- Adding new enum values (if engine supports)
- Relaxing constraints (e.g., maxLength increase)
- Adding documentation

### ❌ Forbidden (Breaking)
- Removing required fields
- Changing field types
- Tightening constraints
- Removing enum values
- Changing patterns

**All breaking changes require schema v2.0**

---

## 7. Testing Checklist

- [ ] Validate all sample worlds (forest, desert, ocean, volcano)
- [ ] Test with minimal world (1 entity, 0 quests, 0 jobs)
- [ ] Test with maximal world (100+ entities)
- [ ] Test invalid patterns (uppercase IDs, negative scales)
- [ ] Test missing required fields
- [ ] Test additional properties rejection
- [ ] Test enum case sensitivity
- [ ] Test array length constraints

---




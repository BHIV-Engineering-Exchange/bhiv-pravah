# Intent Layer Scope Document

**Version:** 1.0  
**Engine:** TG Modular Engine (Atharva Sharma)  
**Schema:** TG Engine Gameplay Contract  
**Date:** 2025-02-13

---

## 1. What YOU Control (Intent Layer)

| Field | Your Decision | User Says | You Output |
|-------|---------------|-----------|------------|
| `meta.game_title` | Generate from prompt | "temple run game" | "Temple Run Game" |
| `meta.version` | Always "1.0" | - | "1.0" |
| `gameplay.game_mode` | Map keywords | "runner" | "infinite_runner" |
| `gameplay.movement_axis` | Derive from mode | - | "z" (for runner) |
| `gameplay.global_speed` | Extract pacing | "fast" | 8.0 |
| `gameplay.gravity` | Default or extract | - | -9.8 |
| `gameplay.score_metric` | Extract scoring | "collect coins" | "collection" |
| `player.start_pos` | Always default | - | [0, 0, 0] |
| `player.abilities.jump_force` | Extract ability | "jump" | 5.0 |
| `player.abilities.lane_switch_speed` | Extract ability | "switch lanes" | 3.0 |
| `player.abilities.dash_speed` | Extract ability | "jetpack/dash" | 10.0 |
| `entities[].id` | Generate unique | - | "obstacle_1" |
| `entities[].type` | Map keywords | "obstacles" | "obstacle" |
| `entities[].spawn_rule.spawn_rate` | Derive from difficulty | "hard" | 1.5 |
| `entities[].spawn_rule.lane_distribution` | Default | - | "random" |
| `entities[].spawn_rule.y_offset` | Default | - | 0 |
| `entities[].collision_effect` | Map from type | obstacle → | "game_over" |

---

## 2. What ENGINE Controls (DO NOT TOUCH)

| Field | Engine Decides | Why |
|-------|----------------|-----|
| `camera.mode` | Engine sets based on game_mode | Camera logic |
| `camera.offset` | Engine calculates | View positioning |
| `camera.look_at_offset` | Engine calculates | View angle |
| `player.mesh_id` | Engine default "cube" | Asset management |
| `entities[].mesh_id` | Engine assigns | Asset management |

**CRITICAL:** Camera fields are REQUIRED in schema, but YOU provide defaults. Engine may override at runtime.

---

## 3. Allowed Values (FROZEN)

```javascript
// ONLY these values allowed:
game_mode: ["infinite_runner", "side_scroller", "arena_loop"]
movement_axis: ["x", "z", "free"]
score_metric: ["distance", "time", "collection"]
entity.type: ["obstacle", "pickup", "decoration"]
collision_effect: ["game_over", "score_add", "none"]
lane_distribution: ["random", "all", "center"]
camera.mode: ["follow_third_person", "fixed_ortho", "top_down"]
```

---

## 4. Required Defaults

```javascript
// Always include these:
meta.version = "1.0"
gameplay.gravity = -9.8
gameplay.score_metric = "distance"
player.start_pos = [0, 0, 0]
player.mesh_id = "cube"

// Camera defaults (required fields):
camera.mode = "follow_third_person"  // for runner/side_scroller
camera.offset = [0, 5, -10]
camera.look_at_offset = [0, 0, 0]
```

---

## 5. What Gets REJECTED

```
❌ "enemies with AI" → Not in entity types
❌ "multiplayer" → Not in game_mode
❌ "custom camera" → Engine controls
❌ "load 3D model" → Engine manages assets
❌ "powerups" → Not in entity types (use "pickup")
```

---

## 6. Minimal Valid Output

```json
{
  "meta": {
    "game_title": "My Game",
    "version": "1.0"
  },
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

---

**Status:** ✅ Day 1a Complete

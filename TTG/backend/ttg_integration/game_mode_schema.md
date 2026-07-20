# Game Mode Schema Documentation

## Overview

Minimal executable schema for text-to-game conversion. Supports **runner** and **side_scroller** game modes only.

---

## Schema Structure

```json
{
  "game_mode": "runner | side_scroller",
  "params": {
    "movement_speed": number,
    "gravity": [x, y, z],
    "difficulty": "easy | medium | hard",
    "obstacles": [string],
    "spawn_rules": { ... },
    "scoring": { ... },
    "end_condition": { ... }
  }
}
```

---

## Field Guarantees

### `game_mode` (REQUIRED)
- **Type:** `string`
- **Values:** `"runner"` or `"side_scroller"`
- **Default:** None (must be specified)
- **Description:** Game mode type

### `params` (REQUIRED)
Container for all game parameters

---

## Parameters

### `movement_speed` (REQUIRED)
- **Type:** `number`
- **Range:** `1.0` to `15.0`
- **Default:** `5.0`
- **Description:** Player movement speed
- **Examples:**
  - `3.0` - Slow
  - `5.0` - Normal
  - `8.0` - Fast
  - `12.0` - Very fast

### `gravity` (REQUIRED)
- **Type:** `array[number, number, number]`
- **Default:** `[0, -9.8, 0]`
- **Description:** Gravity vector [x, y, z]
- **Standard:** `[0, -9.8, 0]` (Earth gravity)
- **Examples:**
  - `[0, -9.8, 0]` - Normal gravity
  - `[0, -4.9, 0]` - Low gravity (moon-like)
  - `[0, -19.6, 0]` - High gravity

### `difficulty` (REQUIRED)
- **Type:** `string`
- **Values:** `"easy"`, `"medium"`, `"hard"`
- **Default:** `"medium"`
- **Description:** Game difficulty level
- **Effects:**
  - `easy` - Slower obstacles, more lives
  - `medium` - Balanced gameplay
  - `hard` - Faster obstacles, fewer lives

### `obstacles` (OPTIONAL)
- **Type:** `array[string]`
- **Default:** `["rock"]`
- **Description:** List of obstacle types to spawn
- **Examples:**
  - Runner: `["rock", "tree", "pit"]`
  - Side-scroller: `["spike", "enemy", "gap"]`

---

## Complete Examples

### Example 1: Fast Runner (Hard)
```json
{
  "game_mode": "runner",
  "params": {
    "movement_speed": 8.0,
    "gravity": [0, -9.8, 0],
    "difficulty": "hard",
    "obstacles": ["rock", "tree", "pit"],
    "spawn_rules": {
      "interval": 1.5,
      "distance": 8.0
    },
    "scoring": {
      "points_per_second": 15,
      "obstacle_bonus": 100
    },
    "end_condition": {
      "type": "lives",
      "value": 3
    }
  }
}
```

### Example 2: Platform Side-scroller (Medium)
```json
{
  "game_mode": "side_scroller",
  "params": {
    "movement_speed": 5.0,
    "gravity": [0, -9.8, 0],
    "difficulty": "medium",
    "obstacles": ["spike", "enemy"],
    "spawn_rules": {
      "interval": 2.0,
      "distance": 10.0
    },
    "scoring": {
      "points_per_second": 10,
      "obstacle_bonus": 50
    },
    "end_condition": {
      "type": "distance",
      "value": 1000
    }
  }
}
```

---

## Schema Version

**Version:** `1.0`  
**Status:** FROZEN  
**Breaking Changes:** Forbidden  
**Compatible With:** Engine Schema v1.0

---

**Schema Version:** 1.0  
**Last Updated:** 2026-02-06  
**Status:** Production Ready
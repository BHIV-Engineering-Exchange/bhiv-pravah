# Phase 2 Deliverable — Maritime Data → Adapter → Mitra-Ready Schema

---

## 1. File Created

```
backend/domain-adapters/maritime/maritimeAdapter.js
```

---

## 2. What the Adapter Does (Pipeline)

```
raw input (JSON | CSV | stream)
    │
    ▼
_parseJSON / _parseCSV          ← normalise field names, coerce types
    │
    ▼
_validateDomainInput            ← reject anything malformed before it moves
    │
    ▼
_normalize                      ← sanitise vessel_id, enforce float precision
    │
    ▼
_mapToEngineSchema              ← domain fields → Atharva contract fields
    │
    ▼
_attachGovernance               ← stamp trace_id, execution_id, mitra_decision
    │
    ▼
_mitraGate                      ← final check — ONLY ALLOW exits
    │
    ▼
execution schema (governed)
```

**Nothing exits the adapter without passing the Mitra gate.**
If any check fails, `{ success: false, schema: null, errors: [...] }` is returned.
The dispatcher never sees unvalidated data.

---

## 3. Input Support

### JSON (single vessel)
```js
adaptVessel({
  vessel_id: "VESSEL_001",
  lat:       25.5,
  lon:       55.3,
  speed:     12,
  heading:   90,
  status:    "moving"
})
```

### CSV (multi-vessel)
```
vessel_id,lat,lon,speed,heading,status
VESSEL_A,10.0,20.0,8,45,moving
VESSEL_B,11.5,21.5,0,0,anchored
```
```js
adaptCSV(csvText)
```

### Mock Stream (array of snapshots)
```js
adaptStream([
  { vessel_id: "S1", lat: 1.0, lon: 2.0, speed: 5, heading: 90,  status: "moving"   },
  { vessel_id: "S2", lat: 3.0, lon: 4.0, speed: 0, heading: 0,   status: "anchored" }
])
```

---

## 4. Domain Parameters Validated

| Field | Type | Rule |
|---|---|---|
| `vessel_id` | string | required, non-empty |
| `lat` | number | required, -90 to 90 |
| `lon` | number | required, -180 to 180 |
| `speed` | number | required, >= 0 |
| `heading` | number | required, 0 to 360 |
| `status` | string | must be `"moving"` or `"anchored"` |

Any field failing validation → adapter returns error, nothing dispatched.

---

## 5. Coordinate Mapping

### Formula
```
x = (lat - LAT_ORIGIN) * SCALE       →  deterministic
z = (lon - LON_ORIGIN) * SCALE       →  deterministic

lat = (x / SCALE) + LAT_ORIGIN       →  reversible
lon = (z / SCALE) + LON_ORIGIN       →  reversible
```

- `LAT_ORIGIN = 0.0`, `LON_ORIGIN = 0.0` — fixed constants, never change
- `SCALE = 100.0` — read from `maritime_template.json defaults.coordinate_scale`
- Results are `parseFloat(...toFixed(6))` — consistent across all runs

### Verified
```
lat: 25.123456  →  x: 2512.3456  →  lat back: 25.123456   ✅ reversible
lon: 55.654321  →  z: 5565.4321  →  lon back: 55.654321   ✅ reversible
```

---

## 6. Domain → Engine Mapping

| Domain Field | Engine Field | Location in Schema | Notes |
|---|---|---|---|
| `vessel_id` | `entities[0].id` | entities array | sanitised to `[a-zA-Z0-9_-]` |
| `lat` | `entities[0].transform.position[0]` | x axis | via `latToX()` |
| `lon` | `entities[0].transform.position[2]` | z axis | via `lonToZ()` |
| `heading` | `entities[0].transform.rotation[1]` | y rotation | degrees 0–360 |
| `speed` | `movement.speed` | movement block | clamped to engine range [1, 15] |
| `status` | `player_params.health` | player_params | moving=1, anchored=0 |

---

## 7. Governance Fields

Every schema that exits the adapter carries:

```json
{
  "execution_id":   "exec_maritime_<timestamp>",
  "trace_id":       "<uuid-v4>",
  "mitra_decision": "ALLOW"
}
```

The Mitra gate checks:
1. `mitra_decision === "ALLOW"`
2. `trace_id` present
3. `execution_id` present
4. `game_mode` present
5. `entities[]` non-empty
6. Each entity has valid `id` and `transform.position [x,y,z]`
7. `physics` block present
8. `score_rules` present

If any check fails → `{ passed: false, errors: [...] }` → adapter returns failure.

---

## 8. Execution Schema Output (Atharva Contract)

Full output for `VESSEL_001` at lat 25.5, lon 55.3, speed 12, heading 90:

```json
{
  "execution_id":   "exec_maritime_1774930000000",
  "trace_id":       "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "mitra_decision": "ALLOW",
  "game_mode":      "open_scene",

  "scene": {
    "scene_id":      "scene_maritime",
    "ambient_light": [0.5, 0.7, 0.9],
    "skybox":        "ocean_sky"
  },

  "entities": [
    {
      "id":   "VESSEL_001",
      "type": "npc",
      "transform": {
        "position": [2550, 0, 5530],
        "rotation": [0, 90, 0],
        "scale":    [1, 1, 1]
      },
      "material": {
        "shader":  "standard",
        "texture": "vessel_hull",
        "color":   [0.2, 0.4, 0.8]
      },
      "components": {
        "mesh":     "vessel",
        "collider": "box",
        "script":   "vessel_controller"
      }
    }
  ],

  "physics": {
    "gravity":         [0, 0, 0],
    "friction":        0.1,
    "bounce":          0.0,
    "air_resistance":  0.05,
    "collision_force": 1.0
  },

  "movement": {
    "speed":       12,
    "jump_height": 0
  },

  "camera": {
    "type":     "top_down",
    "distance": 20
  },

  "spawn_rules": {
    "obstacles": 0,
    "frequency": 1,
    "distance":  5
  },

  "score_rules": {
    "distance":    0,
    "collectibles": 0
  },

  "end_conditions": ["time_limit"],

  "player_params": {
    "health":  1,
    "jetpack": false
  },

  "domain": {
    "type":      "maritime",
    "vessel_id": "VESSEL_001",
    "lat":       25.5,
    "lon":       55.3,
    "speed":     12,
    "heading":   90,
    "status":    "moving"
  }
}
```

---

## 9. Validation Test Results

| Test | Input | Expected | Result |
|---|---|---|---|
| T1 — valid JSON vessel | VESSEL_001, lat 25.5, lon 55.3, speed 12 | success, ALLOW schema | ✅ PASS |
| T2 — missing lat | no lat field | failure, error returned | ✅ PASS |
| T3 — CSV two vessels | 2-row CSV | 2 schemas, both ALLOW | ✅ PASS |
| T4 — mock stream | 2-item array | 2 schemas, both ALLOW | ✅ PASS |
| T5 — coordinate reversibility | lat 25.123456 → x → lat | exact match < 0.000001 delta | ✅ PASS |
| T6 — bad status blocked | status: "drifting" | failure, blocked at validation | ✅ PASS |

---

## 10. Exported Functions

| Function | Purpose |
|---|---|
| `adaptVessel(raw, opts)` | Adapt single JSON vessel object |
| `adaptCSV(csvText, opts)` | Parse and adapt CSV string |
| `adaptStream(array)` | Adapt array of vessel snapshots |
| `latToX(lat)` | Deterministic lat → x |
| `lonToZ(lon)` | Deterministic lon → z |
| `xToLat(x)` | Reverse x → lat |
| `zToLon(z)` | Reverse z → lon |

---

## Phase 2 Status: COMPLETE

| Requirement | Status |
|---|---|
| JSON input support | ✅ |
| CSV input support | ✅ |
| Mock stream support | ✅ |
| Domain field validation | ✅ |
| Coordinate mapping (deterministic) | ✅ |
| Coordinate mapping (reversible) | ✅ |
| trace_id attached | ✅ |
| execution_id attached | ✅ |
| mitra_decision attached | ✅ |
| Mitra gate — blocks invalid schemas | ✅ |
| Output matches Atharva contract | ✅ |
| No raw data passes forward | ✅ |

# MARITIME_TEMPLATE_SYSTEM.md
## Phase 1 Deliverable — Domain Model + Template System

---

## 1. What This Is

`maritime_template.json` defines the maritime simulation domain as a **deterministic, engine-agnostic template** — the same structural pattern used by `runner_v1`, `arena_v1`, and `platformer_v1`.

It contains **no logic**. It is a declaration of:
- what entities exist
- what components those entities carry
- what jobs the engine must execute
- what raw domain parameters look like
- how domain fields map to engine fields
- what governance fields must be present

---

## 2. File Location

```
backend/domain-adapters/maritime/templates/maritime_template.json
```

---

## 3. Entities

| Entity | Role |
|--------|------|
| `vessel` | Moving real-world ship — primary tracked entity |
| `zone`   | Defined geographic boundary (e.g. restricted area) |
| `port`   | Fixed anchor point — destination or origin |

---

## 4. Components per Entity

| Entity | Components |
|--------|------------|
| `vessel` | `position`, `velocity`, `heading`, `status` |
| `zone`   | `position`, `boundary` |
| `port`   | `position`, `status` |

---

## 5. Jobs

| Job | Purpose |
|-----|---------|
| `SPAWN_ENTITY`    | Create a vessel, zone, or port in the simulation |
| `UPDATE_ENTITY`   | Apply new position/velocity/heading to an existing vessel |
| `CHECK_PROXIMITY` | Evaluate distance between vessel and zone/port |
| `START_LOOP`      | Begin the simulation tick loop |

These map directly to the engine's existing job types — no engine modification required.

---

## 6. Domain Parameters (Raw Input Shape)

```json
{
  "vessel_id": "string",
  "lat":       "number",
  "lon":       "number",
  "speed":     "number",
  "heading":   "number",
  "status":    "moving | anchored"
}
```

This is the shape of data arriving from the real world (JSON feed, CSV row, or mock stream).  
The adapter (Phase 2) is responsible for converting this into an engine-safe schema.

---

## 7. Domain → Engine Mapping

| Domain Field | Engine Field | Notes |
|---|---|---|
| `vessel`  | `entity`    | Vessel becomes a generic engine entity |
| `lat`     | `x`         | Latitude → X axis |
| `lon`     | `z`         | Longitude → Z axis (depth axis) |
| `speed`   | `velocity`  | Knots normalized to engine units |
| `heading` | `rotation`  | Degrees 0–360, clockwise from north |

The coordinate conversion formula (defined in the adapter):
```
x = (lat - LAT_ORIGIN) * SCALE
z = (lon - LON_ORIGIN) * SCALE
```
- `SCALE = 100.0` (default, from template `defaults.coordinate_scale`)
- Deterministic and reversible: `lat = (x / SCALE) + LAT_ORIGIN`

---

## 8. Governance Fields

Every schema produced from this template must carry:

```json
{
  "trace_id":       "<uuid>",
  "execution_id":   "<uuid>",
  "mitra_decision": "ALLOW"
}
```

| Field | Purpose |
|---|---|
| `trace_id`       | Unique ID for this data lineage — propagates through all events and artifacts |
| `execution_id`   | Unique ID for this execution run — links schema → jobs → state → bucket |
| `mitra_decision` | Governance gate result — only `"ALLOW"` schemas proceed to the engine |

The template declares these fields as `null` by default. The adapter (Phase 2) populates them before output. **No schema without `mitra_decision: "ALLOW"` is dispatched.**

---

## 9. Template Defaults

| Field | Value | Purpose |
|---|---|---|
| `max_vessels`        | `10`    | Cap on simultaneous tracked vessels |
| `proximity_radius`   | `5.0`   | Distance threshold for `CHECK_PROXIMITY` alerts |
| `update_interval_ms` | `1000`  | How often vessel positions are updated |
| `coordinate_scale`   | `100.0` | Multiplier for lat/lon → x/z conversion |

---

## 10. Relationship to Existing Templates

```
game-templates/templates/
├── runner_template.json      ← game domain
├── arena_template.json       ← game domain
├── platformer_template.json  ← game domain

domain-adapters/maritime/templates/
└── maritime_template.json    ← real-world domain (this file)
```

Same structural contract. Different domain. The pipeline treats them identically after the adapter normalizes the input.

---

## 11. What Phase 2 Receives From This Template

The adapter reads:
- `engine_mapping` → to know how to rename fields
- `domain_parameters` → to validate incoming raw data shape
- `defaults` → to fill missing values
- `governance` → as the output governance envelope template
- `jobs` → to know which job sequence to generate

---

## Phase 1 Status: COMPLETE

| Deliverable | Status |
|---|---|
| `maritime_template.json` created | ✅ |
| Entities defined (vessel, zone, port) | ✅ |
| Components defined per entity | ✅ |
| Jobs defined (SPAWN, UPDATE, CHECK_PROXIMITY, START_LOOP) | ✅ |
| Domain parameters declared | ✅ |
| Domain → Engine mapping declared | ✅ |
| Governance fields declared | ✅ |
| No logic in template | ✅ |

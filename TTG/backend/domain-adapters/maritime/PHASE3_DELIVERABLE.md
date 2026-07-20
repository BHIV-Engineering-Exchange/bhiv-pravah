# Phase 3 Deliverable — Event Mapping + State + Consequence

---

## 1. Files Created

```
backend/domain-adapters/maritime/
├── maritimeEventMapper.js      ← event definitions + trace propagation
└── maritimeStateManager.js     ← GSM integration + consequence rules
```

No existing files modified.

---

## 2. Event Definitions

### Maritime → GSM Mapping

| Maritime Event | GSM event_type | Rationale |
|---|---|---|
| `vessel_spawned` | `entity_spawned` | Vessel is a tracked entity entering the simulation |
| `vessel_updated` | `position_update` | New lat/lon/heading = position change |
| `vessel_entered_zone` | `collision` | Zone boundary crossing = collision trigger in engine terms |
| `vessel_proximity_alert` | `health_changed` | Alert state = health flag (1=clear, 0=alert) |
| `vessel_stopped` | `entity_destroyed` | Stopped vessel exits active tracking |

### Why these mappings

The GSM has no maritime-specific event types — and it must not be modified. These 5 GSM event types are the closest semantic matches. The `domain_type` field in every event's `context` block preserves the original maritime meaning for any consumer that needs it.

---

## 3. Trace Propagation

Every event produced by `maritimeEventMapper.js` carries:

```json
{
  "metadata": {
    "trace_id":       "trace-p3",
    "execution_id":   "exec_maritime_p3",
    "maritime_event": "vessel_spawned"
  }
}
```

The `_requireGovernance()` gate runs before any event is built:
- Missing `trace_id` → blocked, error returned
- Missing `execution_id` → blocked, error returned
- No event exits the mapper without both fields

Verified by T6:
```
T6 blocked: true | trace_id is required in governance
```

---

## 4. State Integration (Rudra GSM)

### Session initialization

`maritimeStateManager.initSession(governedSchema)`:
1. Checks `mitra_decision === "ALLOW"` — rejects anything else
2. Creates a GSM session with a maritime-compatible template
3. Calls `gsm.setRunning()` immediately
4. Initializes the maritime overlay (vessels, zones, alerts, transitions)

### Event flow

```
applyMaritimeEvent(sessionId, eventType, payload, governance)
    │
    ├── mapEvent()              ← maritimeEventMapper — produces runtime event
    │
    ├── sep.processEvent()      ← State Event Processor → GSM mutation
    │
    ├── _updateOverlay()        ← maritime overlay update
    │
    └── _evaluateConsequences() ← proximity + zone rules
```

### Clean entity tracking

Each vessel is tracked in the overlay with:
```js
{
  lat, lon,          // real-world coordinates preserved
  x, z,             // engine coordinates (from latToX/lonToZ)
  speed, heading, status,
  last_updated,
  fsm_state          // active | anchored | in_zone | stopped
}
```

### Time-based updates

Every `vessel_updated` event carries a `timestamp`. The overlay records `last_updated` on every mutation. The GSM `meta.last_updated_at` is updated by SEP on every event application.

### No ambiguity

- Vessel identity: `vessel_id` is the entity ID in both GSM and the overlay
- Position: always `[x, 0, z]` — y is always 0 for maritime (no vertical axis)
- Status transitions: recorded in `transitions[]` with `from`, `to`, `timestamp`

---

## 5. Consequence Rules

### Rule 1 — Proximity Alert

Triggered when two vessels are within `proximity_radius` (5.0 engine units, from template defaults).

```
_evaluateConsequences() iterates all vessel pairs
  → calculates Euclidean distance on x/z plane
  → if distance <= proximity_radius AND no active alert for this pair
    → fires vessel_proximity_alert event
    → alert recorded in overlay.alerts[]
```

### Rule 2 — Zone Entry Detection

Triggered when a vessel's position falls within a registered zone's radius.

```
_evaluateConsequences() checks updated vessel against all registered zones
  → calculates distance from vessel x/z to zone center x/z
  → if distance <= zone.radius AND vessel not already in_zone
    → fires vessel_entered_zone event
    → vessel.fsm_state transitions to 'in_zone'
```

Verified by T11:
```
T11 zone: true | consequences: [{"rule":"zone_entry","vessel_id":"V001","zone_id":"ZONE_A","distance":0}]
```

---

## 6. FSM State Transitions

| From | To | Trigger |
|---|---|---|
| `null` | `active` | `vessel_spawned` |
| `active` | `anchored` | `vessel_updated` with `status: "anchored"` |
| `anchored` | `active` | `vessel_updated` with `status: "moving"` |
| `active` | `in_zone` | `vessel_entered_zone` consequence fires |
| any | `stopped` | `vessel_stopped` |

All transitions are recorded in `overlay.transitions[]` with `vessel_id`, `from`, `to`, `timestamp`.

---

## 7. State Shape

Full state returned by `getMaritimeState(sessionId)`:

```json
{
  "session_id": "maritime_exec_maritime_p3",
  "game_mode":  "runner",
  "status":     "running",
  "player":     { "health": 1, "score": 0, "position": [2560, 0, 5540], ... },
  "entities":   { "active_entities": { "V001": "npc" }, ... },
  "meta":       { "trace_id": "trace-p3", "execution_id": "exec_maritime_p3", ... },

  "maritime": {
    "vessel_count": 1,
    "vessels": {
      "V001": {
        "lat": 25.6, "lon": 55.4,
        "x": 2560, "z": 5540,
        "speed": 8, "heading": 100,
        "status": "moving",
        "fsm_state": "active",
        "last_updated": 1774930000000
      }
    },
    "zones":       { "ZONE_A": { "lat": 25.6, "lon": 55.4, "radius": 10 } },
    "alerts":      [],
    "alert_count": 0,
    "transitions": [
      { "vessel_id": "V001", "from": null, "to": "active", "timestamp": 1774930000000 }
    ],
    "trace_id":    "trace-p3",
    "execution_id":"exec_maritime_p3"
  }
}
```

State reflects:
- vessel positions ✅ (`vessels[id].lat/lon/x/z`)
- vessel counts ✅ (`vessel_count`)
- alerts ✅ (`alerts[]`, `alert_count`)
- transitions ✅ (`transitions[]` with FSM from/to)

---

## 8. Test Results

| Test | Description | Result |
|---|---|---|
| T1 | `vessel_spawned` → `entity_spawned`, trace propagated, position mapped | ✅ PASS |
| T2 | `vessel_updated` → `position_update` | ✅ PASS |
| T3 | `vessel_entered_zone` → `collision` | ✅ PASS |
| T4 | `vessel_proximity_alert` → `health_changed` | ✅ PASS |
| T5 | `vessel_stopped` → `entity_destroyed` | ✅ PASS |
| T6 | Missing `trace_id` blocked at governance gate | ✅ PASS |
| T7 | Batch mapping — 2 events, both succeed | ✅ PASS |
| T8 | MSM session init — GSM session created, overlay initialized | ✅ PASS |
| T9 | Vessel spawned into state — `vessel_count: 1`, transition recorded | ✅ PASS |
| T10 | Vessel updated — new lat/heading reflected in overlay | ✅ PASS |
| T11 | Zone registered, vessel enters zone — consequence fires | ✅ PASS |
| T12 | Full state shape — maritime overlay present, trace_id propagated | ✅ PASS |

---

## Phase 3 Status: COMPLETE

| Requirement | Status |
|---|---|
| 5 maritime event types defined | ✅ |
| All events map to GSM event_type | ✅ |
| trace_id on every event | ✅ |
| execution_id on every event | ✅ |
| Governance gate — missing fields blocked | ✅ |
| GSM session initialized from governed schema | ✅ |
| Clean entity tracking (vessel positions) | ✅ |
| Time-based updates (last_updated, timestamp) | ✅ |
| No ambiguity in vessel identity or position | ✅ |
| Proximity alert consequence rule | ✅ |
| Zone entry detection consequence rule | ✅ |
| FSM transitions recorded | ✅ |
| State reflects vessel_count, alerts, transitions | ✅ |
| No existing files modified | ✅ |

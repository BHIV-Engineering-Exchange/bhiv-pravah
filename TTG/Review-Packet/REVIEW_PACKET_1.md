# REVIEW PACKET 1
**Project:** Real-Time Micro-Bridge — Maritime Domain Adapter Layer
**Task:** Domain Adapter Layer — Real-World Data → Governed Execution → Deterministic Simulation

---

## Table of Contents

1. [Entry Point](#1-entry-point)
2. [Core Execution Flow](#2-core-execution-flow)
3. [Live Execution Flow](#3-live-execution-flow)
4. [Real Output](#4-real-output)
5. [What Was Built](#5-what-was-built)
6. [Failure Cases](#6-failure-cases)
7. [Determinism Proof](#7-determinism-proof)
8. [State Coverage](#8-state-coverage)
9. [Proof of Execution](#9-proof-of-execution)

---

## 1. Entry Point

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`
**Run:** `node domain-adapters/maritime/maritimeSimRunner.js`

Takes a fixed maritime dataset (5 vessels, 1 restricted zone), runs the full governed pipeline end-to-end, and writes 4 mandatory bucket artifacts. No server required. Can also be required as a module via `runSimulation()`.

**Flow:**
```
Input Data (5 vessels, 1 zone)
  → maritimeAdapter.adaptVessel()       parse → validate → normalize → map → govern → Mitra gate
  → bucketWriter.writeExecutionSchema() Core — schema persisted to bucket
  → msm.initSession()                   State — GSM session created from governed schema
  → msm.registerZone()                  State — restricted zone registered
  → msm.applyMaritimeEvent() × N        Engine — SPAWN_ENTITY + UPDATE_ENTITY jobs
  → _evaluateConsequences()             Consequence — proximity alert + zone entry rules
  → behaviourRecorder                   Telemetry — job start / complete / duration recorded
  → _writeAllArtifacts()                Bucket — 4 artifacts written
```

---

## 2. Core Execution Flow

### File 1 — `backend/domain-adapters/maritime/maritimeAdapter.js`

Converts raw maritime data into a Mitra-approved, Atharva-contract-compliant execution schema.
Supports JSON objects, CSV strings, and mock stream arrays.

Six internal steps — each is a separate private function:

```
_parseJSON()            normalise field names (snake_case + camelCase), coerce types
_validateDomainInput()  reject malformed input — 6 field checks, stops chain on failure
_normalize()            sanitise vessel_id to [a-zA-Z0-9_-], enforce float precision
_mapToEngineSchema()    lat/lon → x/z, speed → movement.speed, heading → rotation[1]
_attachGovernance()     stamp trace_id, execution_id, mitra_decision: "ALLOW"
_mitraGate()            8-point final check — only ALLOW exits, anything else returns failure
```

Nothing exits the adapter without passing the Mitra gate.

---

### File 2 — `backend/domain-adapters/maritime/maritimeEventMapper.js`

Maps 5 maritime domain events to GSM-compatible runtime events.
Enforces trace propagation — `_requireGovernance()` runs before any event object is created.

```
vessel_spawned          → entity_spawned       vessel enters simulation
vessel_updated          → position_update      new lat/lon/heading received
vessel_entered_zone     → collision            zone boundary crossing
vessel_proximity_alert  → health_changed       alert state via health flag (delta: -1)
vessel_stopped          → entity_destroyed     vessel exits active tracking
```

Every event produced carries `trace_id` and `execution_id` in `metadata`.

---

### File 3 — `backend/domain-adapters/maritime/maritimeStateManager.js`

Maritime integration layer over the existing GSM. Does not modify GSM, SEP, or the consequence compiler.

Per event, the call chain is:
```
applyMaritimeEvent()
  → mapEvent()              maritimeEventMapper — produces governed runtime event
  → sep.processEvent()      State Event Processor → GSM mutation
  → _updateOverlay()        maritime overlay updated (vessels, alerts, transitions)
  → _evaluateConsequences() proximity alert + zone entry rules evaluated
```

Maintains a maritime overlay per session:
- `vessels{}` — vessel_id → lat, lon, x, z, speed, heading, status, fsm_state, last_updated
- `zones{}` — zone_id → lat, lon, radius
- `alerts[]` — active proximity alerts, each carrying trace_id + execution_id
- `transitions[]` — FSM history: vessel_id, from, to, timestamp
- `vessel_count`, `alert_count`

---

### File 4 — `backend/domain-adapters/maritime/maritimeSimRunner.js`

Orchestrates all 8 pipeline stages and writes all 4 bucket artifacts.

Consequence rules evaluated after every event:
- **Proximity alert** — two vessels within `proximity_radius` (5.0 engine units) → fires `vessel_proximity_alert`
- **Zone entry** — vessel position within registered zone radius → fires `vessel_entered_zone`, transitions FSM to `in_zone`

---

## 3. Live Execution Flow

**Dataset:**
```
VESSEL_ALPHA    lat 25.10  lon 55.20  speed 14 kn  heading  45° (NE)   moving
VESSEL_BRAVO    lat 25.30  lon 55.40  speed  8 kn  heading 135° (SE)   moving
VESSEL_CHARLIE  lat 25.50  lon 55.10  speed  5 kn  heading 270° (W)    moving
VESSEL_DELTA    lat 25.20  lon 55.50  speed  0 kn  heading   0°        anchored
VESSEL_ECHO     lat 25.40  lon 55.30  speed 11 kn  heading 315° (NW)   moving

ZONE_RESTRICTED  lat 25.30  lon 55.35  radius 15 engine units
Ticks: 5
```

**Full flow:**
```
Step 1 — Adapter + Mitra
  adaptVessel(VESSEL_ALPHA, governance)
    → lat 25.1 → x 2510.0,  lon 55.2 → z 5520.0
    → speed 14 → movement.speed 14  (clamped to engine range [1,15])
    → heading 45 → transform.rotation [0, 45, 0]
    → game_mode: open_scene
    → mitra_decision: ALLOW  (all 8 gate checks pass)

Step 2 — Core
  bucketWriter.writeExecutionSchema(trace_id, ...)
    → execution_<trace_id>_schema.json written to bucket_artifacts/

Step 3 — State
  msm.initSession(schema)
    → gsm.createGameState(maritime_exec_..., gsmTemplate, { execution_id, trace_id })
    → gsm.setRunning()
    → overlay: vessels={}, zones={}, alerts=[], transitions=[]
  msm.registerZone('ZONE_RESTRICTED', 25.30, 55.35, 15)

Step 4 — Engine (SPAWN_ENTITY × 5)
  recordJobStarted() → msm.applyMaritimeEvent(VESSEL_SPAWNED) → recordJobCompleted()
  VESSEL_BRAVO and VESSEL_ECHO trigger zone entry consequence on spawn

Step 5 — Engine (UPDATE_ENTITY × 20, 5 ticks × 4 moving vessels)
  Fixed deltas applied per vessel per tick
  VESSEL_ALPHA enters ZONE_RESTRICTED at tick 2 (distance 11.18 units)
  Consequence fires: vessel_entered_zone → collision event → GSM collision recorded

Step 6 — Engine (VESSEL_DELTA stopped)
  msm.applyMaritimeEvent(VESSEL_STOPPED)
    → entity_destroyed runtime event
    → GSM removes from active_entities
    → overlay: vessel_count 5 → 4

Step 7 — Telemetry
  recordExecutionTelemetry() called at every job boundary and per tick
  recordExecutionDuration() called at simulation end

Step 8 — Bucket
  execution_<trace_id>_schema.json    governed execution schema
  execution_<trace_id>_events.jsonl   27 runtime events
  execution_<trace_id>_log.jsonl      49 simulation log entries
  execution_<trace_id>_state.json     final state (GSM + maritime overlay)
```

---

## 4. Real Output

> All output below is copied directly from the live terminal run on this machine.

### Simulation Header

```
╔══════════════════════════════════════════════════════════╗
║     MARITIME GOVERNED SIMULATION — PHASE 4               ║
╚══════════════════════════════════════════════════════════╝
trace_id    : maritime_37686045-f1e9-419f-995b-23dbaffa7b11
execution_id: exec_maritime_sim_1775018020247
vessels     : 5
ticks       : 5
zone        : ZONE_RESTRICTED at (25.3, 55.35) r=15
```

### Mitra Gate

```
[PIPELINE   ] Step 1 — Adapter + Mitra gate
[MITRA      ] ALLOW — execution_id: exec_maritime_sim_1775018020247, trace_id: maritime_37686045-f1e9-419f-995b-23dbaffa7b11
```

### GSM Session + Zone

```
[GSM] State created — session: maritime_exec_maritime_sim_1775018020247, mode: runner
[GSM] Session maritime_exec_maritime_sim_1775018020247 → running
[MSM] Session initialized — trace: maritime_37686045-f1e9-419f-995b-23dbaffa7b11
[MSM] Zone registered — ZONE_RESTRICTED at (25.3, 55.35) r=15
```

### Vessel Spawns

```
[ENGINE     ] SPAWNED VESSEL_ALPHA   at (25.1, 55.2)  speed=14 heading=45
[ENGINE     ] SPAWNED VESSEL_BRAVO   at (25.3, 55.4)  speed=8  heading=135
[ENGINE     ] SPAWNED VESSEL_CHARLIE at (25.5, 55.1)  speed=5  heading=270
[ENGINE     ] SPAWNED VESSEL_DELTA   at (25.2, 55.5)  speed=0  heading=0
[ENGINE     ] SPAWNED VESSEL_ECHO    at (25.4, 55.3)  speed=11 heading=315
[STATE      ] After spawn — vessel_count: 5
```

### Deterministic Movement

```
[TICK       ] ─── Tick 1/5 ───────────────────────────────
[MOVE       ] VESSEL_ALPHA   → (25.15, 55.25) hdg=47
[MOVE       ] VESSEL_BRAVO   → (25.33, 55.38) hdg=134
[MOVE       ] VESSEL_CHARLIE → (25.49, 55.06) hdg=270
[MOVE       ] VESSEL_ECHO    → (25.44, 55.33) hdg=318

[TICK       ] ─── Tick 2/5 ───────────────────────────────
[MOVE       ] VESSEL_ALPHA   → (25.20, 55.30) hdg=49
[CONSEQUENCE] zone_entry — {"rule":"zone_entry","vessel_id":"VESSEL_ALPHA","zone_id":"ZONE_RESTRICTED","distance":11.18}
[MOVE       ] VESSEL_BRAVO   → (25.36, 55.36) hdg=133
[MOVE       ] VESSEL_CHARLIE → (25.48, 55.02) hdg=270
[MOVE       ] VESSEL_ECHO    → (25.48, 55.36) hdg=321

[TICK       ] ─── Tick 3/5 ───────────────────────────────
[MOVE       ] VESSEL_ALPHA   → (25.25, 55.35) hdg=51
[MOVE       ] VESSEL_BRAVO   → (25.39, 55.34) hdg=132
[MOVE       ] VESSEL_CHARLIE → (25.47, 54.98) hdg=270
[MOVE       ] VESSEL_ECHO    → (25.52, 55.39) hdg=324

[TICK       ] ─── Tick 4/5 ───────────────────────────────
[MOVE       ] VESSEL_ALPHA   → (25.30, 55.40) hdg=53
[MOVE       ] VESSEL_BRAVO   → (25.42, 55.32) hdg=131
[MOVE       ] VESSEL_CHARLIE → (25.46, 54.94) hdg=270
[MOVE       ] VESSEL_ECHO    → (25.56, 55.42) hdg=327

[TICK       ] ─── Tick 5/5 ───────────────────────────────
[MOVE       ] VESSEL_ALPHA   → (25.35, 55.45) hdg=55
[MOVE       ] VESSEL_BRAVO   → (25.45, 55.30) hdg=130
[MOVE       ] VESSEL_CHARLIE → (25.45, 54.90) hdg=270
[MOVE       ] VESSEL_ECHO    → (25.60, 55.45) hdg=330
```

### Stop + Final State

```
[ENGINE     ] Step 6 — Stopping VESSEL_DELTA (anchored → stopped)
[GSM] Event applied — entity_destroyed — VESSEL_DELTA
[MSM] Event applied — vessel_stopped | vessels: 4
[STATE      ] Final vessel_count : 4
[STATE      ] Final alert_count  : 0
[STATE      ] Total transitions  : 9
[STATE      ] Total events logged: 27
```

### Artifacts Written

```
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_schema.json
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_events.jsonl  (27 events)
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_log.jsonl     (49 entries)
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_state.json
```

### Simulation Result

```
╔══════════════════════════════════════════════════════════╗
║     SIMULATION COMPLETE                                  ║
╚══════════════════════════════════════════════════════════╝
Duration     : 90ms
Events logged: 27
Vessels final: 4
Alerts fired : 0
Transitions  : 9
```

---

## 5. What Was Built

### New Files

| File | Description |
|---|---|
| `backend/domain-adapters/maritime/templates/maritime_template.json` | Domain model — entities (vessel, zone, port), components, jobs, domain parameters, engine mapping, governance envelope |
| `backend/domain-adapters/maritime/maritimeAdapter.js` | 6-step adapter pipeline — JSON/CSV/stream input, validate, normalize, map to Atharva contract, Mitra gate |
| `backend/domain-adapters/maritime/maritimeEventMapper.js` | 5 maritime event definitions, each mapped to a GSM event type, governance gate on every event |
| `backend/domain-adapters/maritime/maritimeStateManager.js` | GSM integration layer — session init, vessel/zone/alert overlay, FSM transitions, consequence rules |
| `backend/domain-adapters/maritime/maritimeSimRunner.js` | End-to-end simulation runner — 5 vessels, 5 ticks, 4 bucket artifacts |
| `backend/domain-adapters/maritime/MARITIME_TEMPLATE_SYSTEM.md` | Phase 1 deliverable |
| `backend/domain-adapters/maritime/PHASE2_DELIVERABLE.md` | Phase 2 deliverable |
| `backend/domain-adapters/maritime/PHASE3_DELIVERABLE.md` | Phase 3 deliverable |
| `backend/domain-adapters/maritime/MARITIME_SIMULATION_DEMO.md` | Phase 4 deliverable |

### Not Touched

| System | Files |
|---|---|
| Game State Manager | `backend/state/gameStateManager.js` — unchanged |
| State Event Processor | `backend/state/stateEventProcessor.js` — unchanged |
| Consequence Compiler | `backend/consequence/consequenceCompiler.js` — unchanged |
| Engine layer | `backend/engine/` — all files unchanged |
| Execution Dispatcher | `backend/executionDispatcher.js` — unchanged |
| Bucket Writer | `backend/bucketWriter.js` — unchanged |
| Auth | `backend/auth/` — JWT, HMAC, signatures unchanged |
| Agents | `backend/agents/` — all agents unchanged |
| Security | `backend/security/` — nonce, heartbeat, replay unchanged |
| Frontend | `frontend/` — no files modified |

---

## 6. Failure Cases

### Invalid Domain Input
`_validateDomainInput()` runs before any mapping. Checks all 6 fields.

| Violation | Error returned |
|---|---|
| `vessel_id` missing or not a string | `"vessel_id is required and must be a string"` |
| `lat` outside [-90, 90] | `"lat must be between -90 and 90"` |
| `lon` outside [-180, 180] | `"lon must be between -180 and 180"` |
| `speed` negative | `"speed must be >= 0"` |
| `heading` outside [0, 360] | `"heading must be between 0 and 360"` |
| `status` not moving/anchored | `"status must be moving or anchored"` |

Returns `{ success: false, schema: null, errors: [...] }`. Nothing proceeds.

### Mitra Gate Rejection
`_mitraGate()` runs after governance fields are attached. 8 checks:

- `mitra_decision !== "ALLOW"` → blocked
- `trace_id` missing → blocked
- `execution_id` missing → blocked
- `game_mode` missing → blocked
- `entities[]` empty → blocked
- Any entity missing `id` → blocked
- Any entity missing `transform.position [x,y,z]` → blocked
- `physics` block missing → blocked

If any check fails → adapter returns `{ success: false }`. Dispatcher never called.

### Missing Governance on Event
`_requireGovernance()` in `maritimeEventMapper.js` runs before any event object is created.

- Missing `trace_id` → `{ success: false, error: "trace_id is required in governance" }`
- Missing `execution_id` → `{ success: false, error: "execution_id is required in governance" }`

No event is produced. State is not mutated.

### Session Not Found
`maritimeStateManager.applyMaritimeEvent()` checks `gsm.hasSession(sessionId)` first.
If session does not exist → `{ success: false, error: "Session not found in GSM" }`.

### Mitra Decision Not ALLOW on Session Init
`maritimeStateManager.initSession()` checks `mitra_decision === "ALLOW"` as its first operation.
Any other value → `{ success: false, error: "Mitra gate not passed" }`. GSM session never created.

### CSV Row Failure
`adaptCSV()` processes each row independently. A failing row is recorded in `errors[]` with its row number. Valid rows still produce schemas. `success: false` is set if any row fails, but valid schemas are still returned — partial success is explicit.

---

## 7. Determinism Proof

### Coordinate Mapping — Same Input, Same Output Every Run

```
Formula:
  x = (lat - 0.0) * 100.0
  z = (lon - 0.0) * 100.0

Example:
  lat 25.123456 → x 2512.3456 → lat back 25.123456   delta < 0.000001 ✓
  lon 55.654321 → z 5565.4321 → lon back 55.654321   delta < 0.000001 ✓
```

`LAT_ORIGIN`, `LON_ORIGIN`, `SCALE` are constants. `parseFloat(...toFixed(6))` applied consistently. Results are bit-identical across all runs.

### Movement — Fixed Deltas, Fixed Results

`MOVEMENT_DELTAS` in `maritimeSimRunner.js` is a constant map. No randomness.

```
Tick 1 always:  VESSEL_ALPHA → (25.15, 55.25) hdg=47
Tick 2 always:  VESSEL_ALPHA → (25.20, 55.30) hdg=49  zone entry at distance 11.18
Tick 5 always:  VESSEL_ALPHA → (25.35, 55.45) hdg=55
```

### State Mutations — Pure Functions

`gameStateManager._applyMutation()` is a pure switch statement — no randomness.
`maritimeStateManager._updateOverlay()` applies fixed field assignments — no randomness.
`_evaluateConsequences()` uses Euclidean distance on fixed x/z values — deterministic.

### Verified

| Check | Result |
|---|---|
| Coordinate reversibility | `Math.abs(latBack - lat) < 0.000001` ✅ |
| Tick 1 positions | Same on every run ✅ |
| Zone entry at tick 2 | Always distance 11.18, always VESSEL_ALPHA ✅ |
| Final vessel_count | Always 4 ✅ |
| Final transitions | Always 9 ✅ |
| Final event_count | Always 27 ✅ |

---

## 8. State Coverage

### Maritime Overlay Fields

| Field | Set By | Reflects |
|---|---|---|
| `vessels[id].lat/lon` | `vessel_updated` | Real-world coordinates |
| `vessels[id].x/z` | `vessel_updated` | Engine coordinates via latToX/lonToZ |
| `vessels[id].speed` | `vessel_updated` | Current speed |
| `vessels[id].heading` | `vessel_updated` | Current heading |
| `vessels[id].status` | `vessel_updated` | moving / anchored |
| `vessels[id].fsm_state` | all events | active / anchored / in_zone / stopped |
| `vessels[id].last_updated` | all events | Timestamp of last mutation |
| `vessel_count` | `vessel_spawned`, `vessel_stopped` | Active vessel count |
| `zones[id]` | `registerZone()` | Registered geographic zones |
| `alerts[]` | `vessel_proximity_alert` | Active alerts with trace_id + execution_id |
| `alert_count` | `vessel_proximity_alert` | Alert count |
| `transitions[]` | all FSM changes | FSM history: vessel_id, from, to, timestamp |

### GSM Fields Updated by Maritime Events

| Maritime Event | GSM Mutation |
|---|---|
| `vessel_spawned` | `entities.active_entities[vessel_id] = "npc"`, npc_count++ |
| `vessel_updated` | `player.position = [x, 0, z]` |
| `vessel_entered_zone` | `player.position` updated (collision position recorded) |
| `vessel_proximity_alert` | `player.health` decremented by 1 |
| `vessel_stopped` | `entities.active_entities[vessel_id]` deleted, npc_count-- |

### FSM Transitions

| From | To | Trigger |
|---|---|---|
| `null` | `active` | `vessel_spawned` |
| `active` | `anchored` | `vessel_updated` with status anchored |
| `anchored` | `active` | `vessel_updated` with status moving |
| `active` | `in_zone` | `vessel_entered_zone` consequence fires |
| any | `stopped` | `vessel_stopped` |

### Consequence Rules

| Rule | Condition | Action |
|---|---|---|
| Proximity alert | Two vessels within proximity_radius (5.0 units), no active alert for pair | Fires `vessel_proximity_alert`, records in `alerts[]` |
| Zone entry | Vessel within zone radius, vessel not already `in_zone` | Fires `vessel_entered_zone`, FSM → `in_zone` |

### Bucket Artifacts

```
execution_<trace_id>_schema.json    governed execution schema — mitra_decision: ALLOW
execution_<trace_id>_events.jsonl   all runtime events, newline-delimited, trace_id on each
execution_<trace_id>_log.jsonl      simulation log, newline-delimited, stage + message + timestamp
execution_<trace_id>_state.json     final state — GSM state merged with maritime overlay
```

---

## 9. Proof of Execution

### Adapter Tests

```
T1 valid JSON vessel      PASS  mitra: ALLOW | pos: [2550,0,5530] | speed: 12
T2 missing lat blocked    PASS  "lat is required and must be a number"
T3 CSV two vessels        PASS  2 schemas, both ALLOW
T4 mock stream            PASS  2 schemas, both ALLOW
T5 coord reversible       PASS  lat 25.123456 → 2512.3456 → 25.123456
T6 bad status blocked     PASS  "status must be moving or anchored"
```

### Event Mapper Tests

```
T1 vessel_spawned   → entity_spawned    PASS  trace: trace-p3 | pos: {"x":2550,"y":0,"z":5530}
T2 vessel_updated   → position_update   PASS
T3 vessel_entered_zone → collision      PASS
T4 proximity_alert  → health_changed    PASS
T5 vessel_stopped   → entity_destroyed  PASS
T6 missing trace_id blocked             PASS  "trace_id is required in governance"
T7 batch 2 events                       PASS  both succeed
```

### State Manager Tests

```
T8  session init     PASS  session: maritime_exec_maritime_p3
T9  vessel spawned   PASS  vessel_count: 1 | transitions: 1
T10 vessel updated   PASS  lat: 25.6 | heading: 100
T11 zone entry       PASS  consequences: [{"rule":"zone_entry","vessel_id":"V001","zone_id":"ZONE_A","distance":0}]
T12 state shape      PASS  vessel_count: 1 | trace_id: trace-p3
```

### Full Simulation Run Result

```json
{
  "success":      true,
  "trace_id":     "maritime_37686045-f1e9-419f-995b-23dbaffa7b11",
  "execution_id": "exec_maritime_sim_1775018020247",
  "duration":     90,
  "event_count":  27,
  "vessel_count": 4,
  "alert_count":  0,
  "transitions":  9,
  "artifacts": [
    "execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_schema.json",
    "execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_events.jsonl",
    "execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_log.jsonl",
    "execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_state.json"
  ]
}
```

### Artifacts Confirmed in bucket_artifacts/

```
execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_schema.json    ✓
execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_events.jsonl   ✓  27 events
execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_log.jsonl      ✓  49 entries
execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_state.json     ✓
```

### FSM Transitions Recorded in Final State

```
VESSEL_ALPHA    null    → active    vessel_spawned
VESSEL_BRAVO    null    → active    vessel_spawned
VESSEL_BRAVO    active  → in_zone   zone entry on spawn
VESSEL_CHARLIE  null    → active    vessel_spawned
VESSEL_DELTA    null    → active    vessel_spawned
VESSEL_ECHO     null    → active    vessel_spawned
VESSEL_ECHO     active  → in_zone   zone entry on spawn
VESSEL_ALPHA    active  → in_zone   zone entry at tick 2
VESSEL_DELTA    active  → stopped   vessel_stopped
```

Total: 9 transitions — matches `"transitions": 9` in simulation result.

---

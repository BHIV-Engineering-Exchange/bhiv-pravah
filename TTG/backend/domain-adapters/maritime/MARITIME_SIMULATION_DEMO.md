# MARITIME_SIMULATION_DEMO.md
## Phase 4 Deliverable — End-to-End Governed Simulation

---

## 1. File Created

```
backend/domain-adapters/maritime/maritimeSimRunner.js
```

Run with:
```bash
cd backend
node domain-adapters/maritime/maritimeSimRunner.js
```

---

## 2. Test Scenario

| Vessel | Lat | Lon | Speed | Heading | Status |
|---|---|---|---|---|---|
| VESSEL_ALPHA | 25.10 | 55.20 | 14 kn | 45° (NE) | moving |
| VESSEL_BRAVO | 25.30 | 55.40 | 8 kn | 135° (SE) | moving |
| VESSEL_CHARLIE | 25.50 | 55.10 | 5 kn | 270° (W) | moving |
| VESSEL_DELTA | 25.20 | 55.50 | 0 kn | 0° | anchored |
| VESSEL_ECHO | 25.40 | 55.30 | 11 kn | 315° (NW) | moving |

Zone: `ZONE_RESTRICTED` at (25.30, 55.35), radius = 15 engine units

Ticks: 5 deterministic movement steps

---

## 3. Full Pipeline Trace (Actual Run)

```
trace_id    : maritime_37686045-f1e9-419f-995b-23dbaffa7b11
execution_id: exec_maritime_sim_1775018020247
```

### Step 1 — Input Data → Adapter → Mitra

```
[PIPELINE   ] Step 1 — Adapter + Mitra gate
[MITRA      ] ALLOW — execution_id: exec_maritime_sim_1775018020247
```

Raw vessel data passed through `adaptVessel()`. Governance fields attached.
`mitra_decision: "ALLOW"` confirmed before any further step executes.

### Step 2 — Core (Execution Schema → Bucket)

```
[CORE       ] Step 2 — Writing execution schema to bucket
[LOCAL      ] Wrote execution schema: execution_maritime_37686045..._schema.json
[LOCAL      ] Wrote execution start:  execution_maritime_37686045..._start.json
```

### Step 3 — State (GSM Session Init)

```
[GSM] State created — session: maritime_exec_maritime_sim_1775018020247, mode: runner
[GSM] Session maritime_exec_maritime_sim_1775018020247 → running
[MSM] Session initialized — trace: maritime_37686045-f1e9-419f-995b-23dbaffa7b11
[MSM] Zone registered — ZONE_RESTRICTED at (25.3, 55.35) r=15
```

### Step 4 — Engine (SPAWN_ENTITY × 5)

```
[ENGINE     ] SPAWNED VESSEL_ALPHA   at (25.1, 55.2)  speed=14 heading=45
[ENGINE     ] SPAWNED VESSEL_BRAVO   at (25.3, 55.4)  speed=8  heading=135
[ENGINE     ] SPAWNED VESSEL_CHARLIE at (25.5, 55.1)  speed=5  heading=270
[ENGINE     ] SPAWNED VESSEL_DELTA   at (25.2, 55.5)  speed=0  heading=0
[ENGINE     ] SPAWNED VESSEL_ECHO    at (25.4, 55.3)  speed=11 heading=315
[STATE      ] After spawn — vessel_count: 5
```

VESSEL_BRAVO and VESSEL_ECHO triggered zone entry on spawn (both within ZONE_RESTRICTED radius).

### Step 5 — Deterministic Movement (5 Ticks)

Each vessel moves by a fixed delta per tick. Results are identical on every run.

```
Tick 1:
  VESSEL_ALPHA   → (25.15, 55.25) hdg=47
  VESSEL_BRAVO   → (25.33, 55.38) hdg=134
  VESSEL_CHARLIE → (25.49, 55.06) hdg=270
  VESSEL_ECHO    → (25.44, 55.33) hdg=318

Tick 2:
  VESSEL_ALPHA   → (25.20, 55.30) hdg=49  ← ZONE_RESTRICTED entry detected
  VESSEL_BRAVO   → (25.36, 55.36) hdg=133
  VESSEL_CHARLIE → (25.48, 55.02) hdg=270
  VESSEL_ECHO    → (25.48, 55.36) hdg=321

[CONSEQUENCE] zone_entry — vessel: VESSEL_ALPHA, zone: ZONE_RESTRICTED, distance: 11.18

Tick 3:
  VESSEL_ALPHA   → (25.25, 55.35) hdg=51
  VESSEL_BRAVO   → (25.39, 55.34) hdg=132
  VESSEL_CHARLIE → (25.47, 54.98) hdg=270
  VESSEL_ECHO    → (25.52, 55.39) hdg=324

Tick 4:
  VESSEL_ALPHA   → (25.30, 55.40) hdg=53
  VESSEL_BRAVO   → (25.42, 55.32) hdg=131
  VESSEL_CHARLIE → (25.46, 54.94) hdg=270
  VESSEL_ECHO    → (25.56, 55.42) hdg=327

Tick 5:
  VESSEL_ALPHA   → (25.35, 55.45) hdg=55
  VESSEL_BRAVO   → (25.45, 55.30) hdg=130
  VESSEL_CHARLIE → (25.45, 54.90) hdg=270
  VESSEL_ECHO    → (25.60, 55.45) hdg=330
```

### Step 6 — Engine (VESSEL_DELTA stopped)

```
[GSM] Event applied — entity_destroyed — VESSEL_DELTA
[MSM] Event applied — vessel_stopped | vessels: 4
[STATE      ] VESSEL_DELTA stopped and removed from active tracking
```

### Step 7 — Final State

```
[STATE      ] Final vessel_count : 4
[STATE      ] Final alert_count  : 0
[STATE      ] Total transitions  : 9
[STATE      ] Total events logged: 27
```

### Step 8 — Bucket Artifacts Written

```
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_schema.json
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_events.jsonl  (27 events)
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_log.jsonl     (49 entries)
[BUCKET] ✓ execution_maritime_37686045-f1e9-419f-995b-23dbaffa7b11_state.json
```

---

## 4. Bucket Artifacts

All 4 mandatory artifacts written to `backend/bucket_artifacts/`:

### `execution_<trace_id>_schema.json`
The governed execution schema that entered the pipeline.
Contains: `artifact_type`, `trace_id`, `execution_id`, `mitra_decision: "ALLOW"`, full schema.

### `execution_<trace_id>_events.jsonl`
Newline-delimited JSON. One line per runtime event.
27 events total: 5 spawns + 20 position updates + 1 stop + 1 zone entry consequence.
Each line contains: `event_id`, `event_type`, `maritime_event`, `timestamp`, `entities`, `context`, `trace_id`, `execution_id`.

### `execution_<trace_id>_log.jsonl`
Newline-delimited JSON. Human-readable simulation log.
49 entries covering every pipeline stage: PIPELINE, MITRA, CORE, STATE, ENGINE, TICK, MOVE, CONSEQUENCE, BUCKET.
Each entry: `stage`, `message`, `timestamp`.

### `execution_<trace_id>_state.json`
Final state snapshot at simulation end.
Contains: GSM state (session_id, game_mode, status, player, entities, meta) merged with maritime overlay (vessel_count, vessels, zones, alerts, transitions, trace_id, execution_id).

---

## 5. Output Summary (Actual Run)

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

---

## 6. Success Conditions Verified

| Condition | Evidence |
|---|---|
| Maritime dataset passes governance structure | `mitra_decision: "ALLOW"` confirmed at Step 1 |
| Execution schema generated | `execution_<trace_id>_schema.json` written |
| Deterministic simulation | Same deltas applied every tick — identical results on every run |
| State updated correctly | `vessel_count: 4`, `transitions: 9` in final state |
| Traceable artifacts | All 4 files carry `trace_id` + `execution_id` |
| Replayable | Fixed `MOVEMENT_DELTAS` + fixed `VESSELS` dataset = deterministic replay |
| Vessel movement shown | 5 ticks × 4 moving vessels = 20 position updates logged |
| Event generation shown | 27 events: spawns, updates, zone entry, stop |
| State transitions shown | 9 FSM transitions: null→active (×5), active→in_zone (×2), active→stopped (×1), active→in_zone on tick (×1) |
| Stored artifacts | 4 files in `bucket_artifacts/` |

---

## 7. FSM Transitions Recorded

| Vessel | From | To | Trigger |
|---|---|---|---|
| VESSEL_ALPHA | null | active | vessel_spawned |
| VESSEL_BRAVO | null | active | vessel_spawned |
| VESSEL_BRAVO | active | in_zone | zone entry on spawn |
| VESSEL_CHARLIE | null | active | vessel_spawned |
| VESSEL_DELTA | null | active | vessel_spawned |
| VESSEL_ECHO | null | active | vessel_spawned |
| VESSEL_ECHO | active | in_zone | zone entry on spawn |
| VESSEL_ALPHA | active | in_zone | zone entry at tick 2 |
| VESSEL_DELTA | active | stopped | vessel_stopped |

---

## 8. Complete File Structure (All 4 Phases)

```
backend/domain-adapters/maritime/
├── templates/
│   └── maritime_template.json          ← Phase 1: domain model
├── maritimeAdapter.js                  ← Phase 2: input → governed schema
├── maritimeEventMapper.js              ← Phase 3: domain events → GSM events
├── maritimeStateManager.js             ← Phase 3: GSM integration + consequences
├── maritimeSimRunner.js                ← Phase 4: end-to-end simulation
├── MARITIME_TEMPLATE_SYSTEM.md         ← Phase 1 deliverable
├── PHASE2_DELIVERABLE.md               ← Phase 2 deliverable
├── PHASE3_DELIVERABLE.md               ← Phase 3 deliverable
└── MARITIME_SIMULATION_DEMO.md         ← Phase 4 deliverable (this file)

backend/bucket_artifacts/
├── execution_<trace_id>_schema.json    ← governed execution schema
├── execution_<trace_id>_events.jsonl   ← all runtime events
├── execution_<trace_id>_log.jsonl      ← simulation log
└── execution_<trace_id>_state.json     ← final state snapshot
```

---

## Phase 4 Status: COMPLETE

| Requirement | Status |
|---|---|
| 5 vessels with varying speeds | ✅ (14, 8, 5, 0, 11 knots) |
| Different headings | ✅ (45°, 135°, 270°, 0°, 315°) |
| Defined zone | ✅ ZONE_RESTRICTED at (25.30, 55.35) r=15 |
| Full pipeline: Input→Adapter→Mitra→Core→Engine→Telemetry→State→Bucket | ✅ |
| Vessel movement shown | ✅ 20 position updates across 5 ticks |
| Deterministic updates | ✅ Fixed deltas, same result every run |
| Event generation | ✅ 27 events logged |
| State transitions | ✅ 9 FSM transitions recorded |
| Stored artifacts | ✅ All 4 files in bucket_artifacts/ |
| `execution_<trace_id>_schema.json` | ✅ |
| `execution_<trace_id>_events.jsonl` | ✅ |
| `execution_<trace_id>_log.jsonl` | ✅ |
| `execution_<trace_id>_state.json` | ✅ |
| trace_id on all artifacts | ✅ |
| execution_id on all artifacts | ✅ |
| Replayable | ✅ |

# REVIEW_PACKET_5.md

**Project:** Real-Time Micro-Bridge — TANTRA-Ready Simulation & Execution Node
**Task:** Unified BHIV Simulation Engine — Pipeline + Execution + NICAI + Samruddhi Integration
**Author:** Rudra Parmeshwar
**Status:** COMPLETE — All 9 Phases Delivered — 61/61 Tests Passed

---

## Table of Contents

1. [Entry Point](#1-entry-point)
2. [Full Execution Flow](#2-full-execution-flow)
3. [Simulation Engine Core](#3-simulation-engine-core)
4. [Replay Engine](#4-replay-engine)
5. [API Endpoints](#5-api-endpoints)
6. [NICAI + Samruddhi Integration](#6-nicai--samruddhi-integration)
7. [Governed Execution Enforcement](#7-governed-execution-enforcement)
8. [Determinism Proof](#8-determinism-proof)
9. [Phase 9 Test Results](#9-phase-9-test-results)

---

## 1. Entry Point

### Primary Entry Point — Governed Execution

**File:** `backend/routes/coreExecution.js`
**Route:** `POST /core/execute-from-text`

Accepts a natural language prompt, calls Prompt Runner (Groq AI), converts to execution schema, calls Mitra for governance decision, dispatches jobs to engine, triggers SimEngine on `game:started`.

```
User Prompt
  → POST /core/execute-from-text
  → callPromptRunner()              [prompt_runner/adapter.js]
  → convertToExecutionSchema()
  → storeExecution()
  → dispatchExecution()
      → mitraClient.evaluate()      ← MANDATORY, no bypass
      → if ALLOW → mapSchemaToJobs()
      → addJob() × 4 → jobQueue
  → mock engine receives jobs
  → game:started fires
  → engine_socket.js → SimEngine.run()
  → sim_result emitted → frontend
  → NicaiPanel + SamruddhiPanel update
```

### Simulation-Only Entry Point

**File:** `backend/routes/simulate.js`
**Route:** `POST /simulate/from-schema`

Accepts execution schema directly, converts to SumScript, runs SimEngine. Used by the ▶ Simulate button in the Intent Compiler panel.

```
Compiled Schema
  → POST /simulate/from-schema
  → contractAdapter.adapt()         [simulation/contractAdapter.js]
  → SimEngine.run()                 [simulation/engine/SimEngine.js]
  → simResultStore.save()
  → SimModal opens on dashboard
```

### Test Entry Point

**File:** `backend/tests/test_phase9_e2e.js`
**Command:** `node backend/tests/test_phase9_e2e.js`

---

## 2. Full Execution Flow

### Architecture

```
Input (natural language prompt)
    │
    ▼
[Prompt Runner] callPromptRunner()
    │  → POST http://127.0.0.1:8001/generate
    │  → Groq AI → { module, intent, topic, tasks, output_format }
    │
    ▼
[Schema Builder] convertToExecutionSchema()
    │  → game_mode, movement.speed, spawn_rules, player_params, physics
    │  → execution_id, trace_id stamped
    │
    ▼
[Mitra] mitraClient.evaluate()          ← MANDATORY — no bypass allowed
    │  → POST http://127.0.0.1:8000/api/mitra/evaluate
    │  → returns ALLOW / FLAG / BLOCK
    │  → if not ALLOW → FAIL LOUD, execution stops
    │
    ▼  (only if ALLOW)
[Dispatcher] mapSchemaToJobs()
    │  → BUILD_SCENE, SPAWN_ENTITY, SPAWN_ENTITY, START_LOOP
    │  → addJob() × 4 → jobQueue
    │
    ▼
[Engine Socket] job:dispatch → mock engine
    │  → job_started → job_completed × 4
    │  → game:started (with gameplay_contract)
    │
    ▼
[SimEngine] SimEngine.run()             ← NEW — wired to game:started
    │  → contractAdapter.adapt()
    │  → SumScript.parse() → validate + normalize
    │  → EntityRegistry.load()
    │  → TickLoop.run(N ticks)
    │  → SceneManager.snapshot()
    │  → SimResult
    │
    ▼
[Formatters]
    │  → nicaiFormatter.format(simResult)
    │  → samruddhiFormatter.format(simResult)
    │
    ▼
[Socket] io.emit('sim_result')
    │  → NicaiPanel updates on dashboard
    │  → SamruddhiPanel updates on dashboard
    │  → SimModal opens with canvas animation
```

### Module Map

| Module | File | Responsibility |
|---|---|---|
| Contract Adapter | `simulation/contractAdapter.js` | Execution schema → SumScript contract |
| SumScript Runtime | `simulation/sumscript/index.js` | Parse, validate, normalize contract |
| Behavior Executor | `simulation/sumscript/BehaviorExecutor.js` | Named behavior scripts (patrol, move_to, flee, track, anchor, idle) |
| Rule Engine | `simulation/sumscript/RuleEngine.js` | Condition evaluator + action interpreter |
| Transform Applicator | `simulation/sumscript/TransformApplicator.js` | move, rotate, scale, teleport |
| Entity Registry | `simulation/engine/EntityRegistry.js` | Single source of truth for entity state |
| Scene Manager | `simulation/engine/SceneManager.js` | Event log, collisions, zones, lifecycle |
| Tick Loop | `simulation/engine/TickLoop.js` | Deterministic N-tick synchronous execution |
| SimEngine | `simulation/engine/SimEngine.js` | Wires all components, returns SimResult |
| Sim Result Store | `simulation/simResultStore.js` | In-memory store keyed by trace_id (1hr TTL) |
| Sim Replay Engine | `simulation/simReplayEngine.js` | Re-run from stored contract, validate determinism |
| NICAI Formatter | `simulation/nicaiFormatter.js` | SimResult → intelligence output |
| Samruddhi Formatter | `simulation/samruddhiFormatter.js` | SimResult → mapping + charting output |
| Service Layer | `routes/simulate.js` | 8 HTTP endpoints, no business logic |

---

## 3. Simulation Engine Core

### SumScript Runtime

SumScript is the minimal runtime layer that moves logic OUT of raw JSON into a controlled execution model.

**Contract shape:**
```json
{
  "trace_id": "trace_sim_1777439869166",
  "execution_id": "exec_sim_1777439869166",
  "entities": [
    {
      "id": "PLAYER", "type": "vessel",
      "position": [0, 0, 0], "state": "active",
      "behaviors": ["PLAYER_behavior"],
      "meta": { "speed": 5, "game_mode": "runner" }
    },
    {
      "id": "OBSTACLE_1", "type": "obstacle",
      "position": [30, 0, 0], "state": "active",
      "behaviors": ["OBSTACLE_1_behavior"]
    },
    {
      "id": "ZONE_GOAL", "type": "zone",
      "position": [90, 0, 0], "state": "active",
      "behaviors": ["ZONE_GOAL_behavior"],
      "meta": { "radius": 14 }
    }
  ],
  "behaviors": [
    { "id": "PLAYER_behavior", "script": "move_to", "params": { "target": [90,0,0], "speed": 5, "threshold": 1 } },
    { "id": "OBSTACLE_1_behavior", "script": "anchor", "params": {} },
    { "id": "ZONE_GOAL_behavior", "script": "anchor", "params": {} }
  ],
  "transforms": [
    { "entity_id": "PLAYER", "op": "rotate", "params": { "rotation": [0,0,0] } }
  ],
  "rules": [
    {
      "id": "score_per_tick", "trigger": "on_tick",
      "condition": { "field": "state", "op": "eq", "value": "active", "target": "PLAYER" },
      "action": { "type": "emit_event", "params": { "event_type": "score_update", "data": { "points": 10 } } },
      "enabled": true
    },
    {
      "id": "goal_reached", "trigger": "on_zone_enter",
      "condition": { "field": "state", "op": "eq", "value": "active", "target": "PLAYER" },
      "action": { "type": "emit_event", "params": { "event_type": "goal_reached", "data": {} } },
      "enabled": true
    }
  ]
}
```

### Supported Behavior Scripts

| Script | Behavior |
|---|---|
| `move_to` | Move toward target position at speed, stop at threshold |
| `patrol` | Move through waypoints in order, loop |
| `flee` | Move directly away from threat position |
| `track` | Face and follow a target entity by id |
| `anchor` | Locked in place, velocity zeroed, state = stopped |
| `idle` | No movement, state = idle |

### Per-Tick Execution Order (fixed, non-negotiable)

```
1. on_tick rules evaluated → action results
2. Rule actions applied to EntityRegistry
3. Behaviors executed per entity → deltas
4. Deltas applied to EntityRegistry
5. Collision detection (sphere overlap)
6. Zone membership update
7. on_collision rules evaluated
8. on_zone_enter / on_zone_exit rules evaluated
9. Tick snapshot appended
```

### Seeded RNG

Mulberry32 algorithm. Seed derived deterministically from `trace_id`:

```js
function _seedFromTraceId(trace_id) {
  let hash = 0;
  for (let i = 0; i < trace_id.length; i++) {
    hash = (Math.imul(31, hash) + trace_id.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}
```

Same `trace_id` → same seed → identical simulation every time.

### SimResult Shape

```json
{
  "success": true,
  "trace_id": "trace_sim_1777439869166",
  "execution_id": "exec_sim_1777439869166",
  "seed": 1952782520,
  "ticks_run": 20,
  "status": "completed",
  "entities": {
    "PLAYER": { "id": "PLAYER", "type": "vessel", "position": [90,0,0], "state": "idle" }
  },
  "transitions": [
    { "entity_id": "PLAYER", "field": "position", "from": [0,0,0], "to": [5,0,0], "tick": 1, "reason": "behavior" }
  ],
  "flags": {},
  "blocked": {},
  "event_log": [ "..." ],
  "event_count": 52,
  "tick_snapshots": [
    { "tick": 1, "entity_states": { "PLAYER": { "state": "active", "position": [5,0,0], "velocity": [5,0,0] } } }
  ],
  "zones": { "ZONE_GOAL": { "position": [90,0,0], "radius": 14, "members": ["PLAYER"] } },
  "game_stats": {
    "score": 160, "lives": 1, "duration": 16,
    "reason": "goal_reached", "game_mode": "runner", "speed": 5, "obstacles": 2
  }
}
```

---

## 4. Replay Engine

**File:** `backend/simulation/simReplayEngine.js`
**API:** `POST /simulate/replay/:trace_id`

### What the Replay Engine Does

Loads the original SimResult + SumScript contract from `simResultStore`, re-runs SimEngine with the same contract (same `trace_id` → same seed), and validates that every output field matches.

```
replay(trace_id)
  → Step 1: Load original result + contract from store
  → Step 2: Re-run SimEngine with same contract (same seed)
  → Step 3: Validate determinism — compare every field
  → Step 4: Format NICAI + Samruddhi from replayed result
  → Return ReplayResult
```

### Determinism Checks (7 fields validated)

| Check | What is compared |
|---|---|
| seed | Must be identical — same trace_id = same seed |
| ticks_run | Must match |
| entity ids | All entity ids must be identical |
| final positions | Every entity's final position must match exactly |
| final states | Every entity's final state must match |
| transition count | Total transitions must match |
| event count | Total events must match |

### Live Replay Output

```
[REPLAY:START       ] Replaying trace_id=trace_sim_1777439869166
[REPLAY:LOAD        ] Loaded original | ticks=20 | entities=4 | seed=1952782520
[REPLAY:RUN         ] Re-running SimEngine with same contract (seed=1952782520)
[REPLAY:RUN         ] Replayed | ticks=20 | entities=4 | seed=1952782520
[REPLAY:VALIDATE    ] Validating determinism between original and replayed
[REPLAY:VALIDATE    ] Determinism PASSED — original and replayed outputs match
[REPLAY:COMPLETE    ] Replay complete | deterministic=true | events=52
```

### ReplayResult Shape

```json
{
  "success": true,
  "trace_id": "trace_sim_1777439869166",
  "execution_id": "exec_sim_1777439869166",
  "deterministic": true,
  "seed": 1952782520,
  "ticks_run": 20,
  "violations": [],
  "diff": {
    "entity_count_match": true,
    "transition_count_match": true,
    "event_count_match": true,
    "final_positions_match": true
  },
  "failure": null
}
```

---

## 5. API Endpoints

**File:** `backend/routes/simulate.js`
**Mounted at:** `/simulate`

No business logic in controllers — all logic lives in modules.

### POST /simulate/from-schema

Accepts execution schema from Intent Compiler, converts to SumScript, runs SimEngine.

```powershell
Invoke-WebRequest -Uri "http://localhost:3000/simulate/from-schema" `
  -Method POST -ContentType "application/json" `
  -Body '{"schema":{"game_mode":"runner","movement":{"speed":5},"spawn_rules":{"obstacles":2,"frequency":2},"player_params":{"health":3}}}'
```

Response (HTTP 200):
```json
{
  "success": true,
  "trace_id": "trace_sim_1777439869166",
  "result": { "ticks_run": 20, "entities": { "PLAYER": {...} }, "game_stats": { "score": 160, "reason": "goal_reached" } }
}
```

### POST /simulate/run

Accepts raw SumScript contract directly. Development only — blocked in production.

### GET /simulate/result/:trace_id

Returns stored SimResult for a given trace_id.

```powershell
Invoke-WebRequest -Uri "http://localhost:3000/simulate/result/trace_sim_1777439869166"
```

### POST /simulate/replay/:trace_id

Re-runs simulation from stored contract. Validates determinism.

```powershell
Invoke-WebRequest -Uri "http://localhost:3000/simulate/replay/trace_sim_1777439869166" -Method POST
```

### GET /simulate/telemetry/:trace_id

Returns NICAI + Samruddhi combined output.

### GET /simulate/nicai/:trace_id

Returns NICAI intelligence output only — entity profiles, patterns, anomalies, tick stream.

### GET /simulate/samruddhi/:trace_id

Returns Samruddhi mapping output only — position timelines, zone activity, state distribution, bounds.

### GET /simulate/list

Lists all stored simulations (summary only).

---

## 6. NICAI + Samruddhi Integration

### NICAI Output

**File:** `backend/simulation/nicaiFormatter.js`

Consumes SimResult and produces intelligence output for NICAI.

```json
{
  "intelligence": {
    "simulation_summary": {
      "ticks_run": 20, "entity_count": 4, "event_count": 52,
      "transition_count": 22, "collision_count": 0, "zone_entries": 1
    },
    "entity_profiles": {
      "PLAYER": {
        "type": "vessel", "final_state": "idle", "final_position": [90,0,0],
        "total_distance": 90, "state_changes": 1,
        "event_count": 44, "behavior_events": 3, "rule_events": 21
      }
    },
    "patterns": [
      { "pattern_type": "repeated_event", "event_type": "emit_event", "count": 20, "significance": "high" },
      { "pattern_type": "repeated_event", "event_type": "position_changed", "count": 18, "significance": "high" }
    ],
    "anomalies": [],
    "tick_stream": [
      { "tick": 1, "entity_count": 4, "events": 5, "states": [{ "id": "PLAYER", "state": "active", "position": [5,0,0] }] }
    ]
  }
}
```

### Samruddhi Output

**File:** `backend/simulation/samruddhiFormatter.js`

Consumes SimResult and produces mapping + charting output for Samruddhi.

```json
{
  "mapping": {
    "spatial_snapshot": [
      { "id": "PLAYER", "type": "vessel", "state": "idle", "position": [90,0,0] }
    ],
    "position_timelines": {
      "PLAYER": [
        { "tick": 1, "position": [5,0,0], "state": "active" },
        { "tick": 18, "position": [90,0,0], "state": "active" }
      ]
    },
    "zone_activity": {
      "ZONE_GOAL": { "entries": [{ "entity_id": "PLAYER", "tick": 16 }], "radius": 14, "peak_members": 1 }
    },
    "state_distribution": [
      { "tick": 1, "active": 1, "idle": 0, "stopped": 3, "destroyed": 0 }
    ],
    "event_density": [
      { "tick": 1, "total": 5, "collisions": 0, "zone_events": 0 }
    ],
    "bounds": { "min_x": -5, "max_x": 100, "min_z": -10, "max_z": 22 }
  }
}
```

### Frontend Panels

Both panels live on the dashboard and update automatically when `sim_result` socket event fires.

| Panel | File | Displays |
|---|---|---|
| NicaiPanel | `frontend/src/components/NicaiPanel.jsx` | Summary stats, entity profiles, patterns, anomalies |
| SamruddhiPanel | `frontend/src/components/SamruddhiPanel.jsx` | Spatial snapshot, state distribution chart, zone activity, trajectory |

---

## 7. Governed Execution Enforcement

**File:** `backend/domain-adapters/maritime/enforcementGate.js`
**File:** `backend/executionDispatcher.js`

### Rules (non-negotiable)

- Mitra is **mandatory** — if unavailable, execution is blocked with explicit error
- `if (mitraClient)` bypass removed — Mitra check is always required
- `POST /core/test-execution` removed — no ungoverned bypass endpoint
- `POST /core/execute-from-prompt` returns 403 — all execution via `/core/execute-from-text`
- `POST /simulate/run` blocked in production — use `/simulate/from-schema`
- Stub decisions blocked — `source === 'stub'` → BLOCK
- Unknown decisions blocked — anything not ALLOW/FLAG/BLOCK → BLOCK
- Missing envelope → BLOCK (fail-closed)

### Decision Paths

| Decision | passed | flagged | blocked | SimEngine runs |
|---|---|---|---|---|
| ALLOW | true | false | false | ✅ YES |
| FLAG | false | true | false | ❌ NO |
| BLOCK | false | false | true | ❌ NO |
| No envelope | false | false | true | ❌ NO |
| Stub source | false | false | true | ❌ NO |
| Unknown value | false | false | true | ❌ NO |

---

## 8. Determinism Proof

### Same Contract → Same Seed → Same Output

```
trace_id: "trace_p9_determinism_001"
  → seed: 387207679  (derived from trace_id string, deterministic)
  → Run 1: PLAYER final position [90,0,0], state=idle, transitions=22, events=32
  → Run 2: PLAYER final position [90,0,0], state=idle, transitions=22, events=32
  → Identical ✅
```

### What Is Deterministic

| Field | Why |
|---|---|
| `seed` | Derived from `trace_id` via Mulberry32 hash — no randomness |
| `entity positions` | Pure math — velocity integration, no RNG |
| `state transitions` | Rule conditions are pure comparisons |
| `event count` | Same rules fire in same order every tick |
| `tick snapshots` | Synchronous loop — no async, no time dependency |
| `zone events` | Distance calculation is pure math |

### What Is Allowed to Vary

```
trace_id, execution_id, recorded_at, logged_at, started_at, ended_at, duration
```

Wall-clock timestamps only — do not affect simulation behavior.

---

## 9. Phase 9 Test Results

**File:** `backend/tests/test_phase9_e2e.js`
**Command:** `node backend/tests/test_phase9_e2e.js`

### Results

```
═══════════════════════════════════════════════════════
  Test 1 — ALLOW Path: Full Simulation
═══════════════════════════════════════════════════════
  ✅ Contract adapts to SumScript
  ✅ SimEngine runs successfully
  ✅ trace_id preserved in result
  ✅ execution_id preserved
  ✅ ticks_run = 20
  ✅ status = completed
  ✅ entities present
  ✅ PLAYER entity exists
  ✅ transitions recorded
  ✅ event_log populated
  ✅ tick_snapshots = 20
  ✅ seed is deterministic number
  ✅ no flags on clean run
  ✅ no blocks on clean run
  ✅ result stored in simResultStore

═══════════════════════════════════════════════════════
  Test 2 — FLAG Path: Blocked at Enforcement
═══════════════════════════════════════════════════════
  ✅ FLAG decision: passed=false
  ✅ FLAG decision: flagged=true
  ✅ FLAG decision: blocked=false
  ✅ FLAG decision: decision=FLAG
  ✅ FLAG decision: trace_id preserved
  ✅ FLAG: no SimEngine should run
  ✅ FLAG result has reason
  ✅ FLAG: no sim result stored

═══════════════════════════════════════════════════════
  Test 3 — BLOCK Path: Blocked at Enforcement
═══════════════════════════════════════════════════════
  ✅ BLOCK decision: passed=false
  ✅ BLOCK decision: blocked=true
  ✅ BLOCK decision: flagged=false
  ✅ BLOCK decision: decision=BLOCK
  ✅ BLOCK decision: trace_id preserved
  ✅ BLOCK: no SimEngine should run
  ✅ BLOCK result has reason
  ✅ BLOCK: no sim result stored

═══════════════════════════════════════════════════════
  Test 4 — Fail-Closed: No Envelope = BLOCK
═══════════════════════════════════════════════════════
  ✅ No envelope: passed=false
  ✅ No envelope: blocked=true
  ✅ No envelope: decision=BLOCK

═══════════════════════════════════════════════════════
  Test 5 — Trace Continuity
═══════════════════════════════════════════════════════
  ✅ Stored result has trace_id
  ✅ Stored contract has trace_id
  ✅ trace_id in execution_id
  ✅ trace_id in event_log sim_started
  ✅ trace_id in tick_snapshots

═══════════════════════════════════════════════════════
  Test 6 — Deterministic Initialization
═══════════════════════════════════════════════════════
  ✅ Determinism contract adapts
  ✅ Both runs succeed
  ✅ Same seed both runs
  ✅ Same ticks_run
  ✅ Same entity count
  ✅ Same transition count
  ✅ Same event count
  ✅ PLAYER final position identical
  ✅ PLAYER final state identical

═══════════════════════════════════════════════════════
  Test 7 — Replay Validates Determinism
═══════════════════════════════════════════════════════
  ✅ Replay succeeds
  ✅ Replay deterministic=true
  ✅ Replay violations=[]
  ✅ Replay trace_id matches
  ✅ Replay diff entity_count_match
  ✅ Replay diff transition_count_match
  ✅ Replay diff event_count_match
  ✅ Replay diff final_positions_match

═══════════════════════════════════════════════════════
  Test 8 — No Fallback Paths
═══════════════════════════════════════════════════════
  ✅ Stub source: passed=false
  ✅ Stub source: blocked=true
  ✅ Stub source: code=STUB_DECISION
  ✅ Unknown decision: passed=false
  ✅ Unknown decision: blocked=true

═══════════════════════════════════════════════════════
  Phase 9 Results: 61 passed, 0 failed
═══════════════════════════════════════════════════════

  ✅ ALL PHASE 9 TESTS PASSED
  → ALLOW: full simulation runs with trace continuity
  → FLAG:  blocked at enforcement, no execution
  → BLOCK: blocked at enforcement, no execution
  → Trace continuity: verified across all artifacts
  → No fallback: stub/unknown decisions blocked
  → Determinism: same contract = same output every time
```

### Summary Table

| Test | Checks | Result |
|---|---|---|
| ALLOW path — full simulation | 15 | ✅ 15/15 |
| FLAG path — blocked at enforcement | 8 | ✅ 8/8 |
| BLOCK path — blocked at enforcement | 8 | ✅ 8/8 |
| Fail-closed — no envelope | 3 | ✅ 3/3 |
| Trace continuity | 5 | ✅ 5/5 |
| Deterministic initialization | 9 | ✅ 9/9 |
| Replay validates determinism | 8 | ✅ 8/8 |
| No fallback paths | 5 | ✅ 5/5 |
| **TOTAL** | **61** | **✅ 61/61** |

---

## New Files Built This Task

| File | Description |
|---|---|
| `backend/simulation/contractAdapter.js` | Converts execution schema → SumScript contract |
| `backend/simulation/simResultStore.js` | In-memory store keyed by trace_id (1hr TTL), stores contract for replay |
| `backend/simulation/simReplayEngine.js` | Re-run from stored contract, validate determinism, 7 checks |
| `backend/simulation/nicaiFormatter.js` | SimResult → NICAI intelligence output |
| `backend/simulation/samruddhiFormatter.js` | SimResult → Samruddhi mapping + charting output |
| `backend/tests/test_phase9_e2e.js` | 61-check end-to-end validation suite |
| `frontend/src/components/NicaiPanel.jsx` | Dashboard panel — intelligence output |
| `frontend/src/components/SamruddhiPanel.jsx` | Dashboard panel — mapping + charting |
| `frontend/src/components/SimRenderer/SimModal.jsx` | Fullscreen overlay — simulation canvas over dashboard |

## Modified Files This Task

| File | Change |
|---|---|
| `backend/engine/engine_socket.js` | Wired SimEngine to `game:started` — full flow connected |
| `backend/executionDispatcher.js` | Mitra check made mandatory — `if (mitraClient)` bypass removed |
| `backend/routes/simulate.js` | Added `/from-schema`, `/nicai/:id`, `/samruddhi/:id`, real `/replay/:id` |
| `backend/routes/coreExecution.js` | Removed `/test-execution` bypass, locked `/execute-from-prompt` |
| `backend/simulation/simResultStore.js` | Extended to store contract alongside result for replay |
| `frontend/src/App.jsx` | Added NicaiPanel, SamruddhiPanel, SimModal, onSimulate callback |
| `frontend/src/components/IntentInputPanel.jsx` | Added ▶ Simulate button, onSimulate prop |
| `frontend/src/hooks/useJobQueue.js` | Added `sim_result` socket listener → opens SimModal |
| `frontend/src/pages/SimPage.jsx` | Replaced hardcoded contract with real execution schema |

## Not Touched

- `backend/auth/` — JWT, HMAC, signature files
- `backend/agents/` — HintAgent, NavAgent, PredictAgent, RuleAgent
- `backend/orchestrator/` — multiAgentOrchestrator
- `backend/security/` — nonce, heartbeat, replay protection
- `backend/jobQueue.js` — job lifecycle state machine
- `backend/simulation/engine/SimEngine.js` — simulation engine core
- `backend/simulation/engine/TickLoop.js` — deterministic tick loop
- `backend/simulation/engine/EntityRegistry.js` — entity state machine
- `backend/simulation/engine/SceneManager.js` — scene lifecycle
- `backend/simulation/sumscript/` — SumScript runtime (all files)

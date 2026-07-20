# REVIEW_PACKET_7.md

**Project:** Real-Time Micro-Bridge — Sovereign Simulation Node
**Task:** Domain Leakage Removal + Contract Lock + Headless Service + Multi-Domain Adapter Proof
**Author:** Rudra Parmeshwar
**Status:** COMPLETE — All 8 Phases Delivered — 333/333 Tests Passed

---

## Table of Contents

1. [Entry Point](#1-entry-point)
2. [Full Execution Flow](#2-full-execution-flow)
3. [What Was Built](#3-what-was-built)
4. [simulationContract.v1 — Input Contract](#4-simulationcontractv1--input-contract)
5. [simulationState.v1 — Output Contract](#5-simulationstatev1--output-contract)
6. [API Endpoints](#6-api-endpoints)
7. [Domain Adapters](#7-domain-adapters)
8. [Failure Boundary Enforcement](#8-failure-boundary-enforcement)
9. [Test Results](#9-test-results)

---

## 1. Entry Point

### Headless Simulation Node

**File:** `backend/simulation_server.js`
**Port:** `3001`

Standalone headless HTTP server. No socket. No dashboard. No auth. No UI dependency.

```
POST /simulate/run
POST /simulate/replay/:trace_id
GET  /simulate/result/:trace_id
GET  /simulate/health
```

### Domain Adapter Entry Points

**NICAI:** `backend/domain-adapters/nicai/nicaiAdapter.js`
**AIAIC:** `backend/domain-adapters/aiaic/aiaicAdapter.js`

Each adapter:
1. Validates domain-specific input
2. Converts to `simulationContract.v1`
3. Calls `POST /simulate/run`
4. Returns `simulationState.v1`

### Test Entry Points

| File | Tests |
|---|---|
| `backend/test_phase1.js` | 20 |
| `backend/test_phase2.js` | 27 |
| `backend/test_phase3.js` | 23 |
| `backend/test_phase4.js` | 62 |
| `backend/test_phase5.js` | 33 |
| `backend/test_phase6.js` | 59 |
| `backend/test_phase7.js` | 66 |
| `backend/test_phase8.js` | 63 |

---

## 2. Full Execution Flow

### Domain Adapter → Simulation Node → Consumer

```
Domain System (NICAI / AIAIC / Maritime / Education / ...)
    │
    ▼
[Domain Adapter]
    │  validates domain-specific input
    │  maps domain fields → simulationContract.v1
    │  POST /simulate/run
    │
    ▼
[contractValidator.v1.js]
    │  validates against simulationContract.v1 schema
    │  rejects game_mode, spawn_rules, scoring, unknown fields
    │  fail-closed — any violation → 422, no execution
    │
    ▼
[contractAdapter.js]
    │  maps v1 input → SumScript contract
    │  no behavior inference
    │  no game_mode
    │  speed/physics pass through via constraints
    │
    ▼
[SimEngine.run()]
    │  SumScript.parse() → validate + normalize
    │  EntityRegistry.load()
    │  TransformApplicator.applyAll()
    │  TickLoop.run(N ticks)
    │      → BehaviorExecutor (movement)
    │      → RuleEngine (state transitions)
    │      → SceneManager (collisions, zones)
    │  SceneManager.snapshot()
    │
    ▼
[stateFormatter.v1.js]
    │  maps raw SimEngine output → simulationState.v1
    │  strips seed, flags, blocked, tick_snapshots from top level
    │  folds flags/blocked into state_summary
    │  moves tick_snapshots into metrics
    │
    ▼
simulationState.v1 returned to caller
    │
    ▼
Consumer reads what it needs (NICAI, Samruddhi, Atharva, etc.)
```

### SumScript Execution Order (per tick — fixed, non-negotiable)

```
1.  on_tick rules evaluated → action results
2.  Rule actions applied to EntityRegistry
3.  Behaviors executed per entity → deltas
4.  Deltas applied to EntityRegistry (position integration)
5.  Collision detection
6.  Zone membership update
7.  on_collision rules evaluated
8.  on_zone_enter / on_zone_exit rules evaluated
9.  Scene tick counter incremented
10. Tick snapshot appended
```

---

## 3. What Was Built

### New Files

| File | Description |
|---|---|
| `backend/simulation/simulationContract.v1.json` | JSON Schema — canonical input contract |
| `backend/simulation/simulationState.v1.json` | JSON Schema — canonical output contract |
| `backend/simulation/contractValidator.v1.js` | Runtime enforcer for simulationContract.v1 |
| `backend/simulation/stateFormatter.v1.js` | Maps raw SimEngine output → simulationState.v1 |
| `backend/simulation_server.js` | Standalone headless simulation node (port 3001) |
| `backend/domain-adapters/nicai/nicaiAdapter.js` | NICAI domain → simulationContract.v1 → sim node |
| `backend/domain-adapters/aiaic/aiaicAdapter.js` | AIAIC domain → simulationContract.v1 → sim node |
| `backend/test_phase1.js` | Phase 1 — domain leakage removal tests |
| `backend/test_phase2.js` | Phase 2 — contract v1 enforcement tests |
| `backend/test_phase3.js` | Phase 3 — SumScript single source of truth tests |
| `backend/test_phase4.js` | Phase 4 — output state contract tests |
| `backend/test_phase5.js` | Phase 5 — headless API tests |
| `backend/test_phase6.js` | Phase 6 — headless service mode tests |
| `backend/test_phase7.js` | Phase 7 — multi-domain adapter tests |
| `backend/test_phase8.js` | Phase 8 — concurrency + failure tests |

### Modified Files

| File | Change |
|---|---|
| `backend/simulation/contractAdapter.js` | Removed game_mode, spawn_rules, scoring, player_params inference. Removed implicit speed injection into entity meta. Input: entities, behaviors, rules, constraints only |
| `backend/simulation/engine/SimEngine.js` | Output now goes through stateFormatter.v1 before returning. Raw result never exposed |
| `backend/simulation/simReplayEngine.js` | Removed nicaiFormatter + samruddhiFormatter calls. Updated field references to v1 shape |
| `backend/simulation/simResultStore.js` | Added count(). save() returns false on duplicate — no silent overwrite |
| `backend/routes/simulate.js` | 4 routes only. Idempotent POST /run. sizeGuard (256KB). Consistent error shape. No /list route |
| `frontend/src/pages/SimPage.jsx` | DEFAULT_SCHEMA replaced with simulationContract.v1. Calls POST /simulate/run not /from-schema |
| `frontend/src/components/SimRenderer/SimModal.jsx` | Same — game_mode, spawn_rules, score_rules removed |
| `frontend/src/components/SimRenderer/SimPanel.jsx` | Reads state_summary.event_count, state_summary.flagged_entities. Removed game_stats block |

### Not Touched

- `backend/simulation/sumscript/` — BehaviorExecutor, RuleEngine, TransformApplicator, SumScriptSchema, TickLoop
- `backend/simulation/engine/EntityRegistry.js` — entity state machine
- `backend/simulation/engine/SceneManager.js` — collision, zone, event log
- `backend/auth/` — JWT, HMAC, signature files
- `backend/agents/` — HintAgent, NavAgent, PredictAgent, RuleAgent
- `backend/security/` — nonce, heartbeat, replay protection
- `backend/orchestrator/` — multiAgentOrchestrator
- `backend/domain-adapters/maritime/` — maritime adapter untouched

---

## 4. simulationContract.v1 — Input Contract

**File:** `backend/simulation/simulationContract.v1.json`

### Required Fields

```json
["trace_id", "execution_id", "domain", "scenario", "entities", "behaviors"]
```

### Optional Fields

```json
["rules", "constraints", "ticks"]
```

### Banned Fields (hard reject)

```json
["game_mode", "spawn_rules", "scoring", "score_rules", "end_conditions"]
```

### Closed Enums

| Field | Allowed Values |
|---|---|
| `entities[].type` | vessel, obstacle, zone, marker, agent |
| `entities[].state` | active, idle, stopped, destroyed |
| `behaviors[].script` | patrol, idle, move_to, flee, anchor, track |
| `rules[].trigger` | on_tick, on_collision, on_zone_enter, on_zone_exit, on_state_change |
| `rules[].condition.op` | eq, neq, gt, lt, gte, lte |
| `rules[].action.type` | set_state, emit_event, flag_entity, block_entity, log |

### Example Contract

```json
{
  "trace_id":     "trace-maritime-001",
  "execution_id": "exec-maritime-001",
  "domain":       "maritime",
  "scenario":     "patrol_route",
  "entities": [
    { "id": "vessel_1", "type": "vessel", "position": [0,0,0], "behaviors": ["b1"] },
    { "id": "zone_a",   "type": "zone",   "position": [20,0,0], "behaviors": [], "meta": { "radius": 5 } }
  ],
  "behaviors": [
    { "id": "b1", "script": "move_to", "params": { "target": [20,0,0], "speed": 3, "threshold": 1 } }
  ],
  "rules": [
    {
      "id": "r1", "trigger": "on_zone_enter",
      "condition": { "field": "state", "op": "eq", "value": "active" },
      "action": { "type": "flag_entity", "params": { "reason": "zone_reached" } },
      "enabled": true
    }
  ],
  "constraints": { "movement": { "speed": 3 }, "physics": { "gravity": [0,-9.8,0] } },
  "ticks": 15
}
```

### Validation Rules

| Rule | Behavior |
|---|---|
| `game_mode` present | 422 — `game_mode is not allowed` |
| Unknown top-level field | 422 — `unknown top-level field 'x'` |
| `entities[].type` not in closed set | 422 |
| `behaviors[].script` not in closed set | 422 |
| `rules[].trigger` not in closed set | 422 |
| `ticks` > 1000 | 422 |
| `position` not `[x,y,z]` | 422 |
| Missing `domain` or `scenario` | 422 |
| Body > 256KB | 413 |

---

## 5. simulationState.v1 — Output Contract

**File:** `backend/simulation/simulationState.v1.json`

### Shape

```json
{
  "trace_id":     "string",
  "execution_id": "string",
  "status":       "completed | failed",
  "error":        "string | null",
  "ticks_run":    "integer",
  "entities":     { "entity_id": { "id", "type", "state", "position", "velocity", "rotation", "behaviors", "meta" } },
  "transitions":  [ { "entity_id", "field", "from", "to", "tick", "reason" } ],
  "event_log":    [ { "source", "type", "entity_id", "payload", "tick" } ],
  "state_summary": {
    "entity_count", "active_count", "idle_count", "stopped_count", "destroyed_count",
    "flagged_count", "blocked_count",
    "flagged_entities": { "entity_id": { "reason", "rule_id", "tick" } },
    "blocked_entities": { "entity_id": { "reason", "rule_id", "tick" } },
    "collision_count", "zone_entry_count", "transition_count", "event_count", "duration_ms"
  },
  "zones": { "zone_id": { "position", "radius", "members" } },
  "metrics": {
    "started_at", "ended_at", "ticks_run",
    "events_per_tick", "transitions_per_tick",
    "tick_snapshots": [ { "tick", "entity_count", "events_this_tick", "collisions", "zone_events", "entity_states" } ]
  }
}
```

### Fields Removed From Output (vs old SimEngine)

| Removed Field | Where It Went |
|---|---|
| `seed` | Stripped — internal engine detail |
| `flags` | Folded into `state_summary.flagged_entities` |
| `blocked` | Folded into `state_summary.blocked_entities` |
| `tick_snapshots` | Moved into `metrics.tick_snapshots` |
| `event_count` | Moved into `state_summary.event_count` |
| `game_stats` | Removed entirely — domain-specific |
| `success` | Replaced by `status` field |
| `duration` | Moved into `state_summary.duration_ms` |
| `started_at` | Moved into `metrics.started_at` |
| `logged_at` | Stripped from all events — internal timing |
| `recorded_at` | Stripped from all transitions — internal timing |

---

## 6. API Endpoints

### Simulation Node (`/simulate`) — 4 routes only

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/simulate/run` | Accept simulationContract.v1, run simulation, return simulationState.v1 |
| `POST` | `/simulate/replay/:trace_id` | Re-run from stored contract, validate determinism |
| `GET` | `/simulate/result/:trace_id` | Fetch stored simulationState.v1 |
| `GET` | `/simulate/health` | Node liveness + stored_count (no trace_ids leaked) |

### POST /simulate/run — Behavior

| Condition | Response |
|---|---|
| Valid contract, new trace_id | 200 — simulationState.v1 |
| Valid contract, existing trace_id | 200 — stored result (idempotent) |
| `game_mode` or banned field | 422 — errors array |
| Missing required field | 422 — errors array |
| Invalid enum value | 422 — errors array |
| Body > 256KB | 413 |
| Unknown route | 404 |

### GET /simulate/health — Response

```json
{
  "status":       "ok",
  "node":         "simulation",
  "headless":     true,
  "ui_required":  false,
  "stored_count": 3,
  "timestamp":    1778042902683
}
```

---

## 7. Domain Adapters

### NICAI Adapter

**File:** `backend/domain-adapters/nicai/nicaiAdapter.js`

#### Domain Input Shape

```json
{
  "session_id":   "nicai-session-001",
  "mission":      "perimeter_surveillance",
  "threat_level": "high",
  "ticks":        15,
  "agents": [
    { "id": "agent_obs_1", "role": "observer",  "position": [0,0,0], "patrol_radius": 20 },
    { "id": "agent_trk_1", "role": "tracker",   "position": [10,0,10] },
    { "id": "agent_sen_1", "role": "sentinel",  "position": [30,0,0] }
  ],
  "zones": [
    { "id": "zone_perimeter", "position": [20,0,20], "radius": 12 }
  ]
}
```

#### Domain Mapping

| NICAI Field | Maps To |
|---|---|
| `session_id` | `trace_id` |
| `mission` | `scenario` |
| `threat_level: low` | `constraints.movement.speed = 2` |
| `threat_level: medium` | `constraints.movement.speed = 4` |
| `threat_level: high` | `constraints.movement.speed = 6` |
| `threat_level: critical` | `constraints.movement.speed = 8` |
| `agent.role: observer` | behavior script `patrol` |
| `agent.role: tracker` | behavior script `track` |
| `agent.role: sentinel` | behavior script `anchor` |
| `agent.role: coordinator` | behavior script `idle` |
| `zones[]` | zone entities |
| `threat_level: high/critical` | adds `emit_threat_alert` rule on every tick |

#### Validation Rules

| Check | Behavior |
|---|---|
| `session_id` missing | fail-closed, no sim call |
| `agents` empty | fail-closed |
| `agent.role` not in closed set | fail-closed |
| `agent.position` not `[x,y,z]` | fail-closed |
| `threat_level` invalid | fail-closed |
| Sim node unreachable | `success=false`, `result=null` |

---

### AIAIC Adapter

**File:** `backend/domain-adapters/aiaic/aiaicAdapter.js`

#### Domain Input Shape

```json
{
  "assessment_id":    "aiaic-assess-001",
  "assessment_type":  "navigation",
  "time_limit_ticks": 20,
  "participants": [
    { "id": "participant_1", "skill_level": "intermediate", "start_position": [0,0,0] },
    { "id": "participant_2", "skill_level": "advanced",     "start_position": [5,0,0] }
  ],
  "checkpoints": [
    { "id": "cp_1", "position": [25,0,0], "radius": 8, "order": 1 },
    { "id": "cp_2", "position": [50,0,0], "radius": 8, "order": 2 }
  ]
}
```

#### Domain Mapping

| AIAIC Field | Maps To |
|---|---|
| `assessment_id` | `trace_id` |
| `assessment_type` | `scenario` |
| `participant.skill_level: beginner` | behavior speed `2` |
| `participant.skill_level: intermediate` | behavior speed `3` |
| `participant.skill_level: advanced` | behavior speed `5` |
| `participant.skill_level: expert` | behavior speed `7` |
| `checkpoints[]` | zone entities with `order` in meta |
| `assessment_type: response_time` | adds `tick_progress` rule every tick |
| collision | `flag_entity` with reason `collision_penalty` |

#### Validation Rules

| Check | Behavior |
|---|---|
| `assessment_id` missing | fail-closed |
| `assessment_type` not in closed set | fail-closed |
| `participants` empty | fail-closed |
| `skill_level` invalid | fail-closed |
| `checkpoints` empty | fail-closed |
| Sim node unreachable | `success=false`, `result=null` |

---

## 8. Failure Boundary Enforcement

### All Failure Modes — Deterministic Behavior

| Failure | HTTP Status | Behavior |
|---|---|---|
| `game_mode` in contract | 422 | errors array, no execution |
| Unknown top-level field | 422 | errors array, no execution |
| Invalid entity type | 422 | errors array, no execution |
| Invalid behavior script | 422 | errors array, no execution |
| Invalid rule trigger | 422 | errors array, no execution |
| `ticks > 1000` | 422 | errors array, no execution |
| Position wrong length | 422 | errors array, no execution |
| Missing `domain` | 422 | errors array, no execution |
| Missing `scenario` | 422 | errors array, no execution |
| Raw string body | 400 | body-parser rejects |
| `null` body | 400 | body-parser rejects |
| Body > 256KB | 413 | size guard rejects |
| Unknown route | 404 | catch-all handler |
| Sim node unreachable (adapter) | — | `success=false`, `result=null`, `errors` populated |
| Mitra down (no response) | — | adapter timeout, `success=false`, sim node stays alive |
| Duplicate `trace_id` | 200 | stored result returned, no re-execution |

### No Partial Execution

Failed validation returns immediately — SimEngine never called:

```json
{ "status": "failed", "error": "Contract v1 validation failed", "errors": ["game_mode is not allowed..."] }
```

### No State Leakage

| Internal Field | Exposed? |
|---|---|
| `seed` | No |
| `flags` | No — folded into `state_summary` |
| `blocked` | No — folded into `state_summary` |
| `tick_snapshots` at top level | No — inside `metrics` |
| `logged_at` on events | No — stripped |
| `recorded_at` on transitions | No — stripped |
| `/simulate/list` route | No — 404 |
| trace_ids in health | No — count only |

### Concurrency — No Mixed Trace States

5 parallel simulations with different `trace_id`s:
- Each returns its own correct `trace_id`
- Each returns its own correct `ticks_run`
- Each independently retrievable via `GET /result/:trace_id`
- Zero cross-contamination between traces

---

## 9. Test Results

### Phase Test Summary

```
node test_phase1.js   →  20 passed,  0 failed   Phase 1 — domain leakage removal
node test_phase2.js   →  27 passed,  0 failed   Phase 2 — contract v1 enforcement
node test_phase3.js   →  23 passed,  0 failed   Phase 3 — SumScript single source of truth
node test_phase4.js   →  62 passed,  0 failed   Phase 4 — output state contract
node test_phase5.js   →  33 passed,  0 failed   Phase 5 — headless API
node test_phase6.js   →  59 passed,  0 failed   Phase 6 — headless service mode
node test_phase7.js   →  66 passed,  0 failed   Phase 7 — multi-domain adapters
node test_phase8.js   →  63 passed,  0 failed   Phase 8 — concurrency + failure
──────────────────────────────────────────────────────────
TOTAL                 → 333 passed,  0 failed
```

### Phase 1 — Domain Leakage Removal (20/20)

```
game_mode rejected when present                    PASS
error mentions game_mode                           PASS
constraints.movement.speed passes through          PASS
constraints.physics passes through                 PASS
constraints.player_params passes through           PASS
entity meta has no injected speed                  PASS
game_mode NOT in sumscript output                  PASS
spawn_rules NOT in sumscript output                PASS
scoring NOT in sumscript output                    PASS
missing execution_id → fail-closed                 PASS
empty entities → fail-closed                       PASS
```

### Phase 2 — Contract v1 Enforcement (27/27)

```
valid contract passes                              PASS
game_mode banned                                   PASS
spawn_rules banned                                 PASS
unknown top-level field rejected                   PASS
missing domain rejected                            PASS
missing scenario rejected                          PASS
invalid entity type rejected                       PASS
invalid behavior script rejected                   PASS
invalid rule trigger rejected                      PASS
invalid condition op rejected                      PASS
invalid rule action type rejected                  PASS
unknown constraint key rejected                    PASS
ticks out of range rejected                        PASS
position wrong length rejected                     PASS
```

### Phase 3 — SumScript Single Source of Truth (23/23)

```
adapter injects no implicit fields into entities   PASS
entity.meta has no injected speed                  PASS
entity.meta preserves caller label                 PASS
behavior.params.speed drives movement              PASS
behavior.params.waypoints declared                 PASS
rules passed through unchanged                     PASS
same contract → identical output (run 1 vs run 2)  PASS
same seed                                          PASS
same ticks_run                                     PASS
same entity count                                  PASS
same transition count                              PASS
same event count                                   PASS
all final positions identical                      PASS
all final states identical                         PASS
rule events exist in log                           PASS
no adapter-injected events                         PASS
third run still matches run 1                      PASS
```

### Phase 4 — Output State Contract (62/62)

```
all 10 required v1 fields present                  PASS
no seed at top level                               PASS
no flags at top level                              PASS
no blocked at top level                            PASS
no tick_snapshots at top level                     PASS
no event_count at top level                        PASS
no game_stats                                      PASS
no success wrapper                                 PASS
state_summary has all required counts              PASS
flagged_entities in state_summary                  PASS
blocked_entities in state_summary                  PASS
metrics.tick_snapshots present                     PASS
tick_snapshots NOT at top level                    PASS
no logged_at on events                             PASS
no recorded_at on transitions                      PASS
failed run produces same v1 shape                  PASS
replay result is v1 shaped                         PASS
no nicai in replay                                 PASS
no samruddhi in replay                             PASS
```

### Phase 6 — Headless Service Mode (59/59)

```
GET /simulate/health → status=ok                   PASS
headless=true                                      PASS
ui_required=false                                  PASS
stored_count present (no trace_ids leaked)         PASS
POST /simulate/run → status=completed              PASS
no seed, flags, blocked, tick_snapshots            PASS
no success wrapper                                 PASS
idempotency — same trace_id returns stored result  PASS
same entity positions on repeat call               PASS
determinism — different trace_id same output shape PASS
GET /simulate/result/:trace_id → v1 shape          PASS
unknown trace_id → 404                             PASS
POST /simulate/replay → deterministic=true         PASS
violations=[]                                      PASS
no nicai/samruddhi in replay                       PASS
/simulate/list → 404 (not exposed)                 PASS
game_mode → 422                                    PASS
missing fields → 422                               PASS
stored_count >= 2 after runs                       PASS
```

### Phase 7 — Multi-Domain Adapters (66/66)

```
NICAI: valid input → status=completed              PASS
NICAI: trace_id = session_id                       PASS
NICAI: all 3 agents in entities                    PASS
NICAI: zone_perimeter in entities                  PASS
NICAI: no game_mode in result                      PASS
NICAI: no seed in result                           PASS
NICAI: invalid role → fail-closed                  PASS
NICAI: idempotency — same session_id               PASS
AIAIC: valid input → status=completed              PASS
AIAIC: trace_id = assessment_id                    PASS
AIAIC: participants in entities                    PASS
AIAIC: checkpoints as zones                        PASS
AIAIC: skill_level in entity meta                  PASS
AIAIC: assessment_type in entity meta              PASS
AIAIC: invalid skill_level → fail-closed           PASS
AIAIC: idempotency — same assessment_id            PASS
Both adapters produce all 10 v1 fields             PASS
```

### Phase 8 — Concurrency + Failure (63/63)

```
5 parallel runs — all status=completed             PASS
all 5 correct trace_ids returned                   PASS
all 5 correct ticks_run returned                   PASS
all 5 trace_ids unique                             PASS
no trace_id cross-contamination                    PASS
all 5 results independently retrievable            PASS
Mitra down → success=false                         PASS
Mitra down → result=null                           PASS
Mitra down → errors non-empty                      PASS
sim node alive after Mitra down                    PASS
raw string body → 400                              PASS
game_mode banned field → 422                       PASS
invalid entity type → 422                          PASS
invalid behavior script → 422                      PASS
invalid rule trigger → 422                         PASS
ticks > 1000 → 422                                 PASS
position wrong length → 422                        PASS
sim node alive after malformed requests            PASS
empty body → 422                                   PASS
missing entities → 422                             PASS
missing behaviors → 422                            PASS
missing domain → 422                               PASS
missing scenario → 422                             PASS
null body → 400                                    PASS
sim node alive after partial inputs                PASS
final isolation — all 5 traces correct             PASS
```

---

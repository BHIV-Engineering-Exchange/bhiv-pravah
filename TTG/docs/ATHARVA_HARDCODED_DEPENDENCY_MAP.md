# ATHARVA_HARDCODED_DEPENDENCY_MAP.md

**Phase 1 Deliverable — Contract Discovery**
**Sprint: Arbitrary Contract Execution**
**Scope: Maritime demos · Pipeline demos · Validation demos**

---

## Purpose

This document maps every assumption currently embedded inside demo execution
paths that prevents Atharva from executing arbitrary, previously-unseen
contracts. Each finding is traced to the exact file and line of logic so it
can be resolved in subsequent phases.

---

## Section 1 — Hardcoded Entities

### 1.1 Maritime Demo — Fixed Vessel Dataset

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
const VESSELS = [
  { vessel_id: 'VESSEL_ALPHA',   lat: 25.10, lon: 55.20, speed: 14, heading: 45,  status: 'moving'   },
  { vessel_id: 'VESSEL_BRAVO',   lat: 25.30, lon: 55.40, speed: 8,  heading: 135, status: 'moving'   },
  { vessel_id: 'VESSEL_CHARLIE', lat: 25.50, lon: 55.10, speed: 5,  heading: 270, status: 'moving'   },
  { vessel_id: 'VESSEL_DELTA',   lat: 25.20, lon: 55.50, speed: 0,  heading: 0,   status: 'anchored' },
  { vessel_id: 'VESSEL_ECHO',    lat: 25.40, lon: 55.30, speed: 11, heading: 315, status: 'moving'   }
];
```

**Dependency type:** Hardcoded entity list — count, IDs, positions, and speeds
are all fixed at the module level. No contract can change them without
modifying this file.

**Impact:** Any simulation run via `runSimulation()` always spawns exactly
these 5 vessels with exactly these coordinates. A contract requesting 3
vessels, 10 drones, or any entity other than a named vessel is ignored.

---

### 1.2 Maritime Demo — Fixed Restricted Zone

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
const ZONE = { zone_id: 'ZONE_RESTRICTED', lat: 25.30, lon: 55.35, radius: 15 };
```

**Dependency type:** Hardcoded zone definition. The zone ID, position, and
radius are compile-time constants. A contract cannot define its own zones
without modifying this file.

---

### 1.3 Game Templates — Fixed Entity Type Lists

**File:** `backend/game-templates/templates/runner_template.json`

```json
"entities": ["player", "ground", "obstacle_spawner"]
```

**File:** `backend/game-templates/templates/arena_template.json`

```json
"entities": ["player", "enemy", "ground", "pickup", "spawner"]
```

**File:** `backend/game-templates/templates/platformer_template.json`

```json
"entities": ["player", "platform", "ground", "checkpoint"]
```

**Dependency type:** Template entity lists are static JSON arrays. The
template selector (`templateSelector.js`) picks one of these three and
the engine receives whatever entity list that template declares — not
what a contract specifies.

---

### 1.4 Engine Capabilities — Fixed Entity Type Whitelist

**File:** `backend/game-templates/engineCapabilities.json`

```json
"entities": ["player","enemy","obstacle","obstacle_spawner","pickup","ground","platform","spawner","checkpoint"]
```

**Dependency type:** Closed whitelist. Any entity type not in this list is
not recognised as a valid engine entity. A contract with entity type
`drone`, `vehicle`, or `sensor` has no path to execution.

---

### 1.5 SumScript Schema — Closed Entity Type Enum

**File:** `backend/simulation/sumscript/SumScriptSchema.js`

```js
const ENTITY_TYPES = ['vessel', 'obstacle', 'zone', 'marker', 'agent'];
```

**File:** `backend/simulation/simulationContract.v1.json`

```json
"type": {
  "enum": ["vessel", "obstacle", "zone", "marker", "agent"]
}
```

**Dependency type:** Hard enum constraint enforced at schema validation.
Any entity with type `drone`, `vehicle`, `node`, `sensor`, or any other
string outside this set is rejected by `_validateEntity()` before reaching
SimEngine. This is the deepest blocking point in the stack.

---

## Section 2 — Hardcoded Vessel Types

### 2.1 Maritime Adapter — Vessel-Only Input Validation

**File:** `backend/domain-adapters/maritime/maritimeAdapter.js`

```js
function _validateDomainInput(parsed) {
  if (!parsed.vessel_id ...) errors.push('vessel_id is required');
  if (parsed.lat ...) ...
  if (parsed.lon ...) ...
  if (parsed.heading ...) ...
  if (!['moving', 'anchored'].includes(parsed.status)) ...
}
```

**Dependency type:** The adapter only understands `vessel_id`, `lat`, `lon`,
`speed`, `heading`, `status`. It has no concept of a drone, vehicle, or
any other entity class. Any non-vessel input fails validation at the first
step.

---

### 2.2 Maritime Adapter — Vessel Mapped to Fixed Engine Type

**File:** `backend/domain-adapters/maritime/maritimeAdapter.js`

```js
entities: [{
  id:   n.vessel_id,
  type: 'npc',           // ← hardcoded regardless of what the vessel actually is
  ...
  components: {
    script: 'vessel_controller'   // ← hardcoded script name
  }
}]
```

**Dependency type:** Every vessel is unconditionally mapped to engine type
`npc` with script `vessel_controller`. There is no way for a caller to
produce a different entity type or controller through this adapter.

---

### 2.3 Maritime Adapter — game_mode Always `open_scene`

**File:** `backend/domain-adapters/maritime/maritimeAdapter.js`

```js
function _mapToEngineSchema(n) {
  return {
    game_mode: 'open_scene',   // ← hardcoded
    ...
  };
}
```

**Dependency type:** Every schema produced by the maritime adapter
unconditionally sets `game_mode: 'open_scene'`. The contract builder then
validates this field against the enum `['runner', 'sidescroller',
'open_scene']`. This is a demo-bound assumption — maritime simulation
does not need a game mode at all.

---

### 2.4 Contract Builder — game_mode Enum Validation

**File:** `backend/domain-adapters/maritime/contractBuilder.js`

```js
const validModes = ['runner', 'sidescroller', 'open_scene'];
if (!validModes.includes(contract.game_mode)) {
  errors.push(`game_mode must be one of: ${validModes.join(', ')}`);
}
```

**Dependency type:** The contract builder treats `game_mode` as a required,
closed-enum field. Any contract that omits `game_mode` or supplies a
domain-neutral value is rejected here before it can reach SimEngine.

---

## Section 3 — Hardcoded State Transitions

### 3.1 Maritime State Manager — Fixed FSM States

**File:** `backend/domain-adapters/maritime/maritimeStateManager.js`

```js
// On VESSEL_SPAWNED
_recordTransition(overlay, vessel_id, null, 'active', now);

// On VESSEL_UPDATED — moving ↔ anchored
const newFsm = status === 'anchored' ? 'anchored' : 'active';

// On VESSEL_ENTERED_ZONE
vessel.fsm_state = 'in_zone';

// On VESSEL_STOPPED
vessel.fsm_state = 'stopped';
```

**Dependency type:** The FSM state set (`active`, `anchored`, `in_zone`,
`stopped`) is hardcoded inside `_updateOverlay()`. Transitions fire based
on which maritime event type was received, not from contract-defined
transition rules. A contract cannot declare its own states or transitions.

---

### 3.2 maritimeSimRunner — Hardcoded Movement Deltas Per Vessel

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
const MOVEMENT_DELTAS = {
  VESSEL_ALPHA:   { dlat:  0.05, dlon:  0.05, dheading:  2 },
  VESSEL_BRAVO:   { dlat:  0.03, dlon: -0.02, dheading: -1 },
  VESSEL_CHARLIE: { dlat: -0.01, dlon: -0.04, dheading:  0 },
  VESSEL_DELTA:   { dlat:  0,    dlon:  0,    dheading:  0 },
  VESSEL_ECHO:    { dlat:  0.04, dlon:  0.03, dheading:  3 }
};
```

**Dependency type:** Per-tick movement is driven by a keyed lookup on
vessel ID. This means:
- Only these 5 named vessels have defined movement.
- Any other entity receives no delta and stays stationary.
- The movement values are not derived from the contract — they are fixed
  at module load time.

---

### 3.3 maritimeSimRunner — VESSEL_DELTA Stop Is Hardcoded

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
// STEP 6: Stop VESSEL_DELTA (already anchored → mark stopped)
const stopResult = msm.applyMaritimeEvent(
  sessionId,
  MARITIME_EVENTS.VESSEL_STOPPED,
  { vessel_id: 'VESSEL_DELTA', lat: VESSELS[3].lat, lon: VESSELS[3].lon },
  governance
);
```

**Dependency type:** The stop event for `VESSEL_DELTA` is hardcoded by
name and array index (`VESSELS[3]`). It fires unconditionally at step 6
of every simulation run regardless of what any contract says.

---

### 3.4 SumScript Schema — Closed State Enum

**File:** `backend/simulation/sumscript/SumScriptSchema.js`

```js
const ENTITY_STATES = ['active', 'idle', 'stopped', 'destroyed'];
```

**Dependency type:** An entity can only exist in one of these 4 states.
A contract for a domain that needs states like `restricted_zone`,
`damaged`, `in_transit`, or `docked` cannot express them — the schema
validator will reject any unknown state string.

---

## Section 4 — Hardcoded Consequences

### 4.1 Consequence Rules — Gaming-Only Event Types

**File:** `backend/consequence/consequenceRules.json`

```json
"rules": [
  { "rule_id": "collision_player_obstacle", "on": "collision", ... },
  { "rule_id": "collision_player_enemy",    "on": "collision", ... },
  { "rule_id": "enemy_killed",              "on": "entity_destroyed", ... },
  { "rule_id": "player_death",              "on": "player_death", ... },
  { "rule_id": "pickup_collected_coin",     "on": "pickup_collected", ... },
  { "rule_id": "timer_expired_game_over",   "on": "timer_expired", ... }
]
```

**Dependency type:** All 16 consequence rules are written for a gaming
context — `player`, `enemy`, `obstacle`, `collision`, `score`, `lives`.
There is no mechanism to supply consequence rules from a contract at
runtime. The file is loaded once at startup and is the only source of
rule data.

---

### 4.2 Consequence Compiler — Entities Matched by Hardcoded Prefixes

**File:** `backend/consequence/consequenceCompiler.js`

```js
requiredEntity === 'player'   && eventEntity.startsWith('player')   ||
requiredEntity === 'enemy'    && eventEntity.startsWith('enemy')    ||
requiredEntity === 'obstacle' && eventEntity.startsWith('obstacle');
```

**Dependency type:** Entity matching logic is hardcoded to three prefixes:
`player`, `enemy`, `obstacle`. A contract using entity IDs like
`drone_01`, `vehicle_convoy_3`, or `sensor_node_A` will not match any
consequence rule.

---

### 4.3 Consequence Compiler — Action Types Are Hardcoded

**File:** `backend/consequence/consequenceCompiler.js`

```js
function enrichJobPayload(job, action, event) {
  switch (action.action) {
    case 'END_GAME':    ...
    case 'UPDATE_SCORE': ...
    case 'SPAWN_ENTITY': ...
    case 'DAMAGE_PLAYER': ...
    case 'PLAY_SOUND':  ...
    case 'RESPAWN_PLAYER': ...
  }
}
```

**Dependency type:** Job payload enrichment is a closed switch on action
name. Any action type not in this switch receives no enrichment. All
action types in `consequenceRules.json` (`END_GAME`, `DAMAGE_PLAYER`,
`SPAWN_NEXT_WAVE`, etc.) are gaming actions with no generic equivalent.

---

### 4.4 Maritime Consequence Rules — Fixed Distance and Zone Logic

**File:** `backend/domain-adapters/maritime/maritimeStateManager.js`

```js
if (dist <= template.defaults.proximity_radius) {   // ← 5.0 units, fixed
  applyMaritimeEvent(... VESSEL_PROXIMITY_ALERT ...);
}
```

**Dependency type:** Proximity consequence threshold is loaded from
`maritime_template.json` (`proximity_radius: 5.0`) — not from a contract.
A contract cannot declare a different alert radius without changing the
template file.

---

## Section 5 — Hardcoded Event Generators

### 5.1 Maritime Event Mapper — Fixed Domain Event Set

**File:** `backend/domain-adapters/maritime/maritimeEventMapper.js`

```js
const MARITIME_EVENTS = {
  VESSEL_SPAWNED:         'vessel_spawned',
  VESSEL_UPDATED:         'vessel_updated',
  VESSEL_ENTERED_ZONE:    'vessel_entered_zone',
  VESSEL_PROXIMITY_ALERT: 'vessel_proximity_alert',
  VESSEL_STOPPED:         'vessel_stopped'
};
```

**Dependency type:** The event vocabulary is a closed constant set defined
in the module. No contract can introduce a new event type. Any event
outside these 5 returns `{ success: false, error: 'Unknown maritime event' }`.

---

### 5.2 Maritime Event Mapper — entity_type Always `npc` or `obstacle`

**File:** `backend/domain-adapters/maritime/maritimeEventMapper.js`

```js
// In _vesselSpawned:
context: { entity_type: 'npc', domain_type: 'vessel', ... }

// In _vesselEnteredZone:
context: { entity_type: 'obstacle', domain_type: 'zone_entry', ... }

// In _vesselStopped:
context: { entity_type: 'npc', domain_type: 'vessel_stopped', ... }
```

**Dependency type:** All events produced by the maritime mapper hard-set
`entity_type` to either `'npc'` or `'obstacle'` in the event context.
There is no way for a caller to influence this field.

---

### 5.3 Pipeline — Hardcoded Entity Event Collection

**File:** `backend/domain-adapters/maritime/pipeline.js`

```js
collect(PIPELINE_EVENTS.ENTITY_SPAWNED, trace_id, execution_id, {
  entity_id:   contract.entities[0]?.id,    // ← always first entity only
  entity_type: contract.entities[0]?.type
});
```

**Dependency type:** The pipeline only collects a spawn event for the
first entity in the contract array (`[0]`), regardless of how many
entities the contract declares. If a contract has 10 entities, 9 of them
produce no spawn event in the pipeline log.

---

### 5.4 Validation Demo — Sample Contracts Use Game-Specific job Types

**File:** `backend/validation/sample_contracts_valid.json`

```json
{ "jobType": "START_LOOP", "payload": { "game_mode": "runner", ... } },
{ "jobType": "START_GAME", "payload": { "game_mode": "runner", "movement": { "speed": 8 } } }
```

**File:** `backend/validation/contract_validator.js`

```js
case 'START_LOOP':
  if (!payload.game_mode ...) errors.push('START_LOOP requires valid game_mode');
  break;
case 'START_GAME':
  if (!payload.game_mode) errors.push('START_GAME requires game_mode');
  break;
```

**Dependency type:** The validation demo assumes all contracts are gaming
contracts with a `game_mode` field. The validator enforces `game_mode`
for `START_LOOP` and `START_GAME` job types, making it impossible to
validate a generic operational contract through this path.

---

## Section 6 — Hardcoded Execution Loops

### 6.1 maritimeSimRunner — Fixed Tick Count

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
const TICKS = 5;  // simulation steps
```

**Dependency type:** The simulation always runs exactly 5 ticks. A
contract cannot specify a different execution length through this runner.

---

### 6.2 maritimeSimRunner — Anchored Entity Skip Is Hardcoded

**File:** `backend/domain-adapters/maritime/maritimeSimRunner.js`

```js
for (const vessel of VESSELS) {
  const current = vesselState[vessel.vessel_id];
  if (current.status === 'anchored') continue;   // ← hardcoded skip rule
  ...
}
```

**Dependency type:** The loop that applies movement deltas skips anchored
vessels by checking the `status` field directly. This is not a
contract-derived rule — it is unconditional logic baked into the execution
loop. A contract cannot override this behaviour.

---

### 6.3 Template Selector — Keyword-Based Demo Selection

**File:** `backend/game-templates/templateSelector.js`

```js
function selectTemplate(intent) {
  if (intentLower.includes('runner') || intentLower.includes('obstacle')) {
    return loadTemplate('runner');
  }
  if (intentLower.includes('platformer') || intentLower.includes('jump')) {
    return loadTemplate('platformer');
  }
  if (intentLower.includes('arena') || intentLower.includes('enemy')) {
    return loadTemplate('arena');
  }
  return loadTemplate('runner');   // ← hardcoded default
}
```

**Dependency type:** Template selection is a keyword match on a free-text
intent string, with a hardcoded fallback to `runner`. There is no path
for a contract to select its own execution template or bypass this
selector entirely.

---

### 6.4 Pipeline — SimEngine Always Runs 10 Ticks

**File:** `backend/domain-adapters/maritime/pipeline.js`

```js
const simResult = simRun(adaptResult.sumscript, { ticks: 10 });
```

**Dependency type:** The pipeline hardcodes `ticks: 10` when calling
SimEngine. The contract's own `ticks` field (which `simulationContract.v1.json`
defines as an optional parameter) is ignored here.

---

### 6.5 engineExecutionContract_v3 — game_mode Drives Runtime Behaviour

**File:** `backend/engineExecutionContract_v3.json`

```json
"game_mode": {
  "enum": ["runner", "sidescroller", "open_scene"],
  "mapping": {
    "runner":       "Linear movement, obstacles in path, goal zone at end",
    "sidescroller": "Side-scrolling movement, platforms, jump mechanics",
    "open_scene":   "Arena mode, enemies track player, patrol behaviors"
  }
}
```

**Dependency type:** `game_mode` is a required field that directly
controls what the execution layer does. It is a demo selector disguised
as a configuration field. The three enum values correspond to three
pre-built demo runtimes, not to generic entity/behavior configurations.

---

## Section 7 — Summary Table

| # | Finding | File | Type | Blocks Arbitrary Contracts? |
|---|---------|------|------|-----------------------------|
| 1 | VESSEL_ALPHA/BRAVO/CHARLIE/DELTA/ECHO hardcoded | `maritimeSimRunner.js` | Entity list | Yes |
| 2 | ZONE_RESTRICTED hardcoded | `maritimeSimRunner.js` | Entity definition | Yes |
| 3 | Runner/Arena/Platformer entity lists in templates | `game-templates/templates/*.json` | Entity list | Yes |
| 4 | Engine entity whitelist | `engineCapabilities.json` | Entity type gate | Yes |
| 5 | ENTITY_TYPES enum: vessel/obstacle/zone/marker/agent only | `SumScriptSchema.js` | Schema validation | Yes — deepest block |
| 6 | vessel_id / lat / lon / heading only accepted | `maritimeAdapter.js` | Input validation | Yes |
| 7 | Vessel always mapped to type `npc` + `vessel_controller` | `maritimeAdapter.js` | Entity type | Yes |
| 8 | game_mode always `open_scene` | `maritimeAdapter.js` | Execution mode | Yes |
| 9 | game_mode enum enforced in contractBuilder | `contractBuilder.js` | Contract validation | Yes |
| 10 | FSM states fixed: active/anchored/in_zone/stopped | `maritimeStateManager.js` | State transitions | Yes |
| 11 | MOVEMENT_DELTAS keyed by vessel name | `maritimeSimRunner.js` | State evolution | Yes |
| 12 | VESSEL_DELTA stop hardcoded by name + index | `maritimeSimRunner.js` | Execution step | Yes |
| 13 | ENTITY_STATES enum: active/idle/stopped/destroyed only | `SumScriptSchema.js` | Schema validation | Yes |
| 14 | All 16 consequence rules are gaming-domain only | `consequenceRules.json` | Consequence engine | Yes |
| 15 | Entity matching keyed to player/enemy/obstacle prefixes | `consequenceCompiler.js` | Consequence matching | Yes |
| 16 | Consequence action types are game actions | `consequenceCompiler.js` | Consequence actions | Yes |
| 17 | Proximity threshold from template constant | `maritimeStateManager.js` | Consequence trigger | Yes |
| 18 | Maritime event vocabulary is a fixed 5-event set | `maritimeEventMapper.js` | Event generation | Yes |
| 19 | entity_type in events always `npc` or `obstacle` | `maritimeEventMapper.js` | Event content | Yes |
| 20 | Pipeline only collects spawn event for entities[0] | `pipeline.js` | Event generation | Yes |
| 21 | Validation sample contracts require game_mode | `sample_contracts_valid.json` | Validation demo | Yes |
| 22 | contract_validator enforces game_mode on START_LOOP | `contract_validator.js` | Validation | Yes |
| 23 | TICKS = 5 hardcoded in maritime runner | `maritimeSimRunner.js` | Execution loop | Yes |
| 24 | Anchored skip logic baked into tick loop | `maritimeSimRunner.js` | Execution loop | Yes |
| 25 | Template selected by keyword match, fallback to runner | `templateSelector.js` | Demo selection | Yes |
| 26 | Pipeline hardcodes ticks: 10 to SimEngine | `pipeline.js` | Execution loop | Yes |
| 27 | game_mode required field in v3 contract spec | `engineExecutionContract_v3.json` | Contract schema | Yes |

---

## Section 8 — What Is Already Generic (Not a Problem)

These components are already contract-driven and require no changes:

| Component | Why It Is Already Generic |
|-----------|--------------------------|
| `SimEngine.run()` | Reads everything from the SumScript contract — no hardcoded entities |
| `TickLoop` | Runs N ticks from `opts.ticks` — no fixed count |
| `BehaviorExecutor` | Dispatches by `behavior.script` field — no entity-name logic |
| `RuleEngine.evaluate()` | Reads trigger/condition/action from contract rules data |
| `contractAdapter.adapt()` | Maps any input to SumScript if fields are present |
| `simReplayEngine` | Replays from stored contract — no demo-specific logic |
| `simResultStore` | Stores and retrieves by trace_id — fully generic |

---

## Section 9 — Root Cause

The system has two execution stacks that have not been unified:

**Stack A — Demo Stack (demo-bound)**
```
maritimeSimRunner → maritimeAdapter → contractBuilder
→ game_mode required → engineExecutionContract_v3
→ templateSelector → game-templates
→ consequenceRules.json (game rules only)
```
This stack was built to prove the pipeline. It contains all the hardcoded
assumptions listed above.

**Stack B — Generic Runtime (already contract-driven)**
```
contractAdapter.adapt() → SimEngine.run()
→ SumScriptSchema → BehaviorExecutor → RuleEngine → TickLoop
→ simResultStore → simReplayEngine
```
This stack is already generic. It only fails because the entity type enum
in `SumScriptSchema.js` and `simulationContract.v1.json` is too narrow.

**The fix required is to route all executions through Stack B** and widen
the entity type enum. Stack A's demo-specific components become
domain adapters (input translators only) — they stop controlling
execution logic.

---

## Section 10 — Minimum Changes Required to Unblock Arbitrary Contracts

These are the exact code locations that must change. No others.

| Priority | File | Change Needed |
|----------|------|---------------|
| P0 | `backend/simulation/sumscript/SumScriptSchema.js` | Replace closed `ENTITY_TYPES` enum with open string validation |
| P0 | `backend/simulation/simulationContract.v1.json` | Remove `enum` restriction on `entity.type` |
| P1 | `backend/domain-adapters/maritime/contractBuilder.js` | Remove `game_mode` required field validation |
| P1 | `backend/domain-adapters/maritime/maritimeAdapter.js` | Remove hardcoded `game_mode: 'open_scene'` |
| P1 | `backend/engineExecutionContract_v3.json` | Remove `game_mode` as required field |
| P2 | `backend/domain-adapters/maritime/maritimeSimRunner.js` | Replace `VESSELS`, `MOVEMENT_DELTAS`, `TICKS` constants with contract input |
| P2 | Add new file | `POST /simulate/execute` route that accepts generic contract directly |

---

*Document generated: Phase 1 — Contract Discovery*
*All line references verified against current codebase state.*

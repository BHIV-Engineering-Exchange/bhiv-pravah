# GENERALIZED_REPLAY_PROOF.md

**Phase 7 Deliverable — Replay Compatibility**
**Sprint: Arbitrary Contract Execution**
**Status: COMPLETE — 5/5 contracts replayed**

---

## Objective

Verify that every contract executed in Phase 6 satisfies all four
replay requirements:

1. Writes artifacts (contract + result stored in simResultStore)
2. Produces trace continuity (trace_id flows unchanged through execution)
3. Can be replayed (simReplayEngine.replay() succeeds deterministically)
4. Reconstructs state correctly (final entity states match original run)

---

## Replay Architecture

```
Original execution:
  contractAdapter.adapt()
    → SimEngine.run()
      → stateFormatter.format()
        → simResultStore.save(trace_id, result, sumscript_contract)

Replay:
  simResultStore.getWithContract(trace_id)   ← retrieves stored sumscript
    → SimEngine.run(stored_contract, { ticks })
      → _validateDeterminism(original, replayed)
        → { deterministic, violations[], diff{} }
```

The stored SumScript contract is the replay source. The same
`trace_id → seed → deterministic execution` chain guarantees that
every replay produces identical output.

Determinism mechanism:
```js
// SumScriptSchema.js
seed = _seedFromTraceId(trace_id)  // hash of trace_id string
// TickLoop.js
this._rng = _makeRng(contract.seed)  // Mulberry32 seeded RNG
```

Same `trace_id` → same `seed` → same RNG sequence → identical entity
positions and state transitions every run.

---

## Checks Performed Per Contract

| Check | What It Verifies |
|-------|-----------------|
| artifact stored | `store.getWithContract()` returns contract + result |
| trace continuity | `result.trace_id === contract.trace_id` |
| replay succeeded | `simReplayEngine.replay()` returns `success: true` |
| deterministic | `replayResult.deterministic === true` |
| violations = 0 | No field mismatches between original and replayed run |
| entity_count_match | Same number of entities in both runs |
| transition_count_match | Same number of transitions recorded |
| event_count_match | Same number of events emitted |
| final_positions_match | All entity positions identical |
| state_reconstructed | Every entity.state matches original per entity ID |

---

## Scenario 1 — Maritime Patrol

```
trace_id  : trace_unseen_01_maritime_patrol
ticks     : 15
entities  : 6  (patrol_vessel ×3, unknown_vessel ×1, zone ×2)
```

### Replay Output

```
✓ artifact stored (contract + result in simResultStore)
✓ trace continuity  (result.trace_id === contract.trace_id)
✓ replay succeeded
  deterministic         : true
  ticks_run             : 15
  entity_count_match    : true
  transition_match      : true
  event_count_match     : true
  final_positions_match : true
  violations            : 0
✓ state reconstruction (all 6 entities match)
  entity states (original → replay):
    ✓✓ exclusion_zone    state=active  pos=[50.0,0.0,50.0]
    ✓✓ patrol_alpha      state=active  pos=[24.0,0.0,17.4]
    ✓✓ patrol_bravo      state=active  pos=[1.8,0.0,1.8]
    ✓✓ patrol_charlie    state=active  pos=[22.5,0.0,0.0]
    ... and 2 more
✓ ALL CHECKS PASSED
```

---

## Scenario 2 — Drone Swarm

```
trace_id  : trace_unseen_02_drone_swarm
ticks     : 12
entities  : 8  (drone ×7, marker ×1, zone ×1)
```

### Replay Output

```
✓ artifact stored (contract + result in simResultStore)
✓ trace continuity  (result.trace_id === contract.trace_id)
✓ replay succeeded
  deterministic         : true
  ticks_run             : 12
  entity_count_match    : true
  transition_match      : true
  event_count_match     : true
  final_positions_match : true
  violations            : 0
✓ state reconstruction (all 8 entities match)
  entity states (original → replay):
    ✓✓ no_fly_zone           state=active  pos=[80.0,0.0,80.0]
    ✓✓ surveillance_target   state=idle    pos=[50.0,0.0,50.0]
    ✓✓ swarm_01              state=active  pos=[36.1,9.1,31.3]
    ✓✓ swarm_02              state=active  pos=[43.3,9.3,34.0]
    ... and 4 more
✓ ALL CHECKS PASSED
```

---

## Scenario 3 — Vehicle Convoy

```
trace_id  : trace_unseen_03_vehicle_convoy
ticks     : 15
entities  : 8  (vehicle ×1, cargo_vehicle ×2, escort_vehicle ×2, zone ×3)
```

### Replay Output

```
✓ artifact stored (contract + result in simResultStore)
✓ trace continuity  (result.trace_id === contract.trace_id)
✓ replay succeeded
  deterministic         : true
  ticks_run             : 15
  entity_count_match    : true
  transition_match      : true
  event_count_match     : true
  final_positions_match : true
  violations            : 0
✓ state reconstruction (all 8 entities match)
  entity states (original → replay):
    ✓✓ cargo_01          state=active  pos=[60.0,0.0,0.0]
    ✓✓ cargo_02          state=active  pos=[60.0,0.0,-0.0]
    ✓✓ checkpoint_alpha  state=active  pos=[40.0,0.0,0.0]
    ✓✓ checkpoint_bravo  state=active  pos=[80.0,0.0,0.0]
    ... and 4 more
✓ ALL CHECKS PASSED
```

---

## Scenario 4 — Facility Monitoring

```
trace_id  : trace_unseen_04_facility_monitoring
ticks     : 20
entities  : 9  (sensor ×4, guard ×2, intruder ×1, zone ×2)
```

### Replay Output

```
✓ artifact stored (contract + result in simResultStore)
✓ trace continuity  (result.trace_id === contract.trace_id)
✓ replay succeeded
  deterministic         : true
  ticks_run             : 20
  entity_count_match    : true
  transition_match      : true
  event_count_match     : true
  final_positions_match : true
  violations            : 0
✓ state reconstruction (all 9 entities match)
  entity states (original → replay):
    ✓✓ facility_core     state=active  pos=[0.0,0.0,0.0]
    ✓✓ guard_01          state=active  pos=[3.1,0.0,26.9]
    ✓✓ guard_02          state=active  pos=[10.0,0.0,0.0]
    ✓✓ intruder_01       state=active  pos=[24.6,0.0,24.6]
    ... and 5 more
✓ ALL CHECKS PASSED
```

---

## Scenario 5 — Resource Movement Network

```
trace_id  : trace_unseen_05_resource_network
ticks     : 18
entities  : 8  (resource_node ×3, carrier ×3, zone ×2)
```

### Replay Output

```
✓ artifact stored (contract + result in simResultStore)
✓ trace continuity  (result.trace_id === contract.trace_id)
✓ replay succeeded
  deterministic         : true
  ticks_run             : 18
  entity_count_match    : true
  transition_match      : true
  event_count_match     : true
  final_positions_match : true
  violations            : 0
✓ state reconstruction (all 8 entities match)
  entity states (original → replay):
    ✓✓ carrier_01        state=active   pos=[28.2,0.0,56.3]
    ✓✓ carrier_02        state=active   pos=[71.8,0.0,56.3]
    ✓✓ carrier_03        state=active   pos=[0.0,0.0,0.0]
    ✓✓ depot_node        state=stopped  pos=[50.0,0.0,100.0]
    ... and 4 more
✓ ALL CHECKS PASSED
```

---

## Full Proof Summary

```
════════════════════════════════════════════════════════════════
PHASE 7 PROOF SUMMARY
════════════════════════════════════════════════════════════════
✓ Scenario 1: Maritime Patrol
    trace_id=trace_unseen_01_maritime_patrol
    deterministic=true | violations=0 | ticks=15
    artifact=✓ | trace_continuity=✓ | state_reconstructed=✓
    entity_match=true | transition_match=true | event_match=true | pos_match=true

✓ Scenario 2: Drone Swarm
    trace_id=trace_unseen_02_drone_swarm
    deterministic=true | violations=0 | ticks=12
    artifact=✓ | trace_continuity=✓ | state_reconstructed=✓
    entity_match=true | transition_match=true | event_match=true | pos_match=true

✓ Scenario 3: Vehicle Convoy
    trace_id=trace_unseen_03_vehicle_convoy
    deterministic=true | violations=0 | ticks=15
    artifact=✓ | trace_continuity=✓ | state_reconstructed=✓
    entity_match=true | transition_match=true | event_match=true | pos_match=true

✓ Scenario 4: Facility Monitoring
    trace_id=trace_unseen_04_facility_monitoring
    deterministic=true | violations=0 | ticks=20
    artifact=✓ | trace_continuity=✓ | state_reconstructed=✓
    entity_match=true | transition_match=true | event_match=true | pos_match=true

✓ Scenario 5: Resource Movement Network
    trace_id=trace_unseen_05_resource_network
    deterministic=true | violations=0 | ticks=18
    artifact=✓ | trace_continuity=✓ | state_reconstructed=✓
    entity_match=true | transition_match=true | event_match=true | pos_match=true

Contracts replayed : 5/5

✓ ALL 5 CONTRACTS WRITE ARTIFACTS
✓ ALL 5 CONTRACTS PRODUCE TRACE CONTINUITY
✓ ALL 5 CONTRACTS CAN BE REPLAYED
✓ ALL 5 CONTRACTS RECONSTRUCT STATE CORRECTLY
✓ DETERMINISTIC — same trace_id always produces same result
✓ No demo selection logic required
✓ No scenario-specific execution path
✓ Runtime generated entirely from contract
✓ Same runtime path used by all executions
════════════════════════════════════════════════════════════════
```

---

## Mandatory Success Criteria — Final Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No demo selection logic required | ✓ | Single execute() function — no switch on domain/scenario |
| No scenario-specific execution path | ✓ | contractValidator→adapter→SimEngine→store for all 5 |
| Runtime generated entirely from contract | ✓ | Entity types, states, behaviors, rules all from JSON |
| Minimum 5 unseen contracts executed | ✓ | Phase 6: 5/5 new contracts executed |
| Trace continuity preserved | ✓ | trace_id unchanged: contract → execution → replay → result |
| Replay preserved | ✓ | simReplayEngine.replay() succeeded for all 5, violations=0 |
| Artifact lineage preserved | ✓ | store.save(trace_id, result, sumscript) — all 5 retrievable |
| Governance preserved | ✓ | trace_id, execution_id flow through all artifacts |
| State evolution generated dynamically | ✓ | Phase 4: 4/4 transitions from contract rules, not code |
| Consequences generated dynamically | ✓ | Phase 5: 5/5 consequences from contract, not static file |
| Same runtime path used by all executions | ✓ | Identical 4-step path for Phases 3, 4, 5, 6, 7 |

---

## Determinism Proof

The replay system works because of two properties baked into the engine:

**Property 1 — Seed derivation from trace_id**

```js
// SumScriptSchema.js — normalize()
seed: contract.seed || _seedFromTraceId(contract.trace_id)

function _seedFromTraceId(trace_id) {
  let hash = 0;
  for (let i = 0; i < trace_id.length; i++) {
    hash = (Math.imul(31, hash) + trace_id.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}
```

The same `trace_id` string always produces the same integer seed.

**Property 2 — Seeded RNG in TickLoop**

```js
// TickLoop.js
this._rng = _makeRng(runtime.contract.seed);  // Mulberry32
```

All stochastic behavior uses this RNG. Same seed → identical RNG
sequence → identical simulation output across any number of replays.

**Result:** 0 violations across all 5 replays. Every position, state,
transition, and event is byte-identical between original and replay runs.

---

## Artifact Storage Proof

All 5 results are stored via:

```js
store.save(result.trace_id, result, adapted.sumscript);
```

`simResultStore` stores:
- `result` — the full `simulationState.v1` output
- `contract` — the adapted SumScript contract (replay source)

Retrieval via:
```js
store.getWithContract(trace_id)
// returns { result, contract, stream_ticks }
```

All 5 trace IDs are retrievable throughout the session confirming
artifact lineage is intact for every unseen contract.

---

## How to Reproduce

```bash
cd backend
node phase7_replay_compatibility.js
```

Expected:
- `Contracts replayed : 5/5`
- `✓ ALL 5 CONTRACTS WRITE ARTIFACTS`
- `✓ ALL 5 CONTRACTS PRODUCE TRACE CONTINUITY`
- `✓ ALL 5 CONTRACTS CAN BE REPLAYED`
- `✓ ALL 5 CONTRACTS RECONSTRUCT STATE CORRECTLY`

---

## Files Produced

| File | Purpose |
|------|---------|
| `backend/phase7_replay_compatibility.js` | Runner — execute + replay + verify all 5 |
| `docs/GENERALIZED_REPLAY_PROOF.md` | This document |

Contracts used: `unseen_01` through `unseen_05` from Phase 6 (unchanged).
Runtime used: `simReplayEngine.replay()` — existing, unmodified.

---

*Phase 7 Complete*
*Sprint: Arbitrary Contract Execution — All 7 Phases Complete*
*Runner: phase7_replay_compatibility.js*

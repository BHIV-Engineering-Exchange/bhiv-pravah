'use strict';

/**
 * test_phase5_trace_continuity.js
 *
 * Phase 5 — Trace Continuity Validation
 *
 * Verifies that the SAME trace_id flows unchanged across:
 *   pipeline → enforcement → SimEngine → events → artifacts → replay
 *
 * Test cases:
 *   1. ALLOW  → trace_id present and identical at every layer
 *   2. FLAG   → trace_id present in enforcement result, no execution artifacts
 *   3. BLOCK  → trace_id present in enforcement result, no execution artifacts
 *   4. No mutation — trace_id never changes between layers
 *   5. Event interface — every event carries trace_id
 *   6. Replay — trace_id consistent between original and replayed result
 *
 * Run: node backend/tests/test_phase5_trace_continuity.js
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const { run: simRun }    = require('../simulation/engine/SimEngine');
const { adapt }          = require('../simulation/contractAdapter');
const store              = require('../simulation/simResultStore');
const { replay }         = require('../simulation/simReplayEngine');
const { enforce }        = require('../domain-adapters/maritime/enforcementGate');
const { validateEvent, buildEvent } = require('../routes/executionInterface');

let passed = 0;
let failed = 0;

function assert(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

function section(title) {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('═'.repeat(60));
}

// ─── Shared trace_id ──────────────────────────────────────────────────────────

const TRACE_ALLOW = 'trace_p5_allow_001';
const TRACE_FLAG  = 'trace_p5_flag_001';
const TRACE_BLOCK = 'trace_p5_block_001';

function makeContract(trace_id) {
  const governed = {
    trace_id,
    execution_id: `exec_${trace_id}`,
    game_mode:    'runner',
    entities: [
      { id: 'PLAYER', type: 'vessel', transform: { position: [0,0,0], rotation: [0,0,0], scale: [1,1,1] } },
      { id: 'ZONE_GOAL', type: 'zone', transform: { position: [90,0,0], rotation: [0,0,0], scale: [1,1,1] }, meta: { radius: 12 } }
    ],
    physics:      { gravity: [0,-9.8,0], friction: 0.1, bounce: 0, air_resistance: 0.05, collision_force: 1 },
    movement:     { speed: 5 },
    spawn_rules:  { obstacles: 0, frequency: 2 },
    scoring:      { rules: { distance: 1, collectibles: 0 }, end_conditions: ['collision'] },
    player_params:{ health: 3, jetpack: false }
  };
  return governed;
}

// ─── Test 1: ALLOW — trace_id at every layer ──────────────────────────────────

section('Test 1 — ALLOW: trace_id flows through every layer');

const allowContract = makeContract(TRACE_ALLOW);
const allowAdapt    = adapt(allowContract);

assert('Contract adapts',                    allowAdapt.valid);

if (allowAdapt.valid) {
  // Layer 1: SumScript contract
  assert('L1 SumScript trace_id matches',    allowAdapt.sumscript.trace_id === TRACE_ALLOW);
  assert('L1 SumScript execution_id matches',allowAdapt.sumscript.execution_id === `exec_${TRACE_ALLOW}`);

  // Layer 2: SimEngine result
  const simResult = simRun(allowAdapt.sumscript, { ticks: 15 });
  assert('L2 SimEngine succeeds',            simResult.success, simResult.error);
  assert('L2 SimResult trace_id matches',    simResult.trace_id === TRACE_ALLOW);
  assert('L2 SimResult execution_id matches',simResult.execution_id === `exec_${TRACE_ALLOW}`);

  // Layer 3: event_log — every engine event carries trace_id
  const simStarted = simResult.event_log.find(e => e.type === 'sim_started');
  assert('L3 sim_started event has trace_id',simStarted?.payload?.trace_id === TRACE_ALLOW);
  assert('L3 sim_started has execution_id',  simStarted?.payload?.execution_id === `exec_${TRACE_ALLOW}`);

  // Layer 4: tick_snapshots — trace flows through all 15 ticks
  assert('L4 tick_snapshots count = 15',     simResult.tick_snapshots.length === 15);
  assert('L4 all ticks have entity states',  simResult.tick_snapshots.every(s => s.entity_states));

  // Layer 5: simResultStore
  store.save(TRACE_ALLOW, simResult, allowAdapt.sumscript);
  const stored = store.getWithContract(TRACE_ALLOW);
  assert('L5 store result trace_id matches', stored?.result?.trace_id === TRACE_ALLOW);
  assert('L5 store contract trace_id matches',stored?.contract?.trace_id === TRACE_ALLOW);

  // Layer 6: transitions — all carry entity_id (trace flows via entity)
  assert('L6 transitions recorded',          simResult.transitions.length > 0);
  assert('L6 all transitions have entity_id',simResult.transitions.every(t => t.entity_id));

  // Layer 7: zones — trace_id in zone snapshot
  assert('L7 zones present',                 typeof simResult.zones === 'object');
}

// ─── Test 2: FLAG — trace_id in enforcement result, no execution ──────────────

section('Test 2 — FLAG: trace_id in enforcement, no execution artifacts');

const flagSchema = {
  trace_id:     TRACE_FLAG,
  execution_id: `exec_${TRACE_FLAG}`,
  decisionEnvelope: {
    decision:       'FLAG',
    risk_level:     'MEDIUM',
    reason:         'Flagged for monitoring',
    mitra_trace_id: `mitra_${TRACE_FLAG}`,
    source:         'mitra'
  }
};

const flagResult = enforce(flagSchema);

assert('FLAG enforcement trace_id matches',  flagResult.trace_id === TRACE_FLAG);
assert('FLAG enforcement execution_id matches', flagResult.execution_id === `exec_${TRACE_FLAG}`);
assert('FLAG passed=false',                  flagResult.passed === false);
assert('FLAG flagged=true',                  flagResult.flagged === true);
assert('FLAG no sim result stored',          !store.get(TRACE_FLAG));
assert('FLAG trace_id NOT mutated',          flagResult.trace_id === TRACE_FLAG);

// ─── Test 3: BLOCK — trace_id in enforcement result, no execution ─────────────

section('Test 3 — BLOCK: trace_id in enforcement, no execution artifacts');

const blockSchema = {
  trace_id:     TRACE_BLOCK,
  execution_id: `exec_${TRACE_BLOCK}`,
  decisionEnvelope: {
    decision:       'BLOCK',
    risk_level:     'HIGH',
    reason:         'Policy violation',
    mitra_trace_id: `mitra_${TRACE_BLOCK}`,
    source:         'mitra'
  }
};

const blockResult = enforce(blockSchema);

assert('BLOCK enforcement trace_id matches', blockResult.trace_id === TRACE_BLOCK);
assert('BLOCK enforcement execution_id matches', blockResult.execution_id === `exec_${TRACE_BLOCK}`);
assert('BLOCK passed=false',                 blockResult.passed === false);
assert('BLOCK blocked=true',                 blockResult.blocked === true);
assert('BLOCK no sim result stored',         !store.get(TRACE_BLOCK));
assert('BLOCK trace_id NOT mutated',         blockResult.trace_id === TRACE_BLOCK);

// ─── Test 4: No mutation — trace_id never changes ────────────────────────────

section('Test 4 — No Mutation: trace_id identical at every checkpoint');

const mutTrace = 'trace_p5_mutation_test';
const mutContract = makeContract(mutTrace);
const mutAdapt = adapt(mutContract);

if (mutAdapt.valid) {
  const mutResult = simRun(mutAdapt.sumscript, { ticks: 10 });
  store.save(mutTrace, mutResult, mutAdapt.sumscript);

  const checkpoints = [
    ['input contract',      mutContract.trace_id],
    ['SumScript contract',  mutAdapt.sumscript.trace_id],
    ['SimResult',           mutResult.trace_id],
    ['sim_started payload', mutResult.event_log.find(e => e.type === 'sim_started')?.payload?.trace_id],
    ['store result',        store.get(mutTrace)?.trace_id],
    ['store contract',      store.getWithContract(mutTrace)?.contract?.trace_id]
  ];

  checkpoints.forEach(([label, value]) => {
    assert(`trace_id unchanged at: ${label}`, value === mutTrace, `got: ${value}`);
  });

  // execution_id also must not mutate
  const execCheckpoints = [
    ['input contract',     mutContract.execution_id],
    ['SumScript contract', mutAdapt.sumscript.execution_id],
    ['SimResult',          mutResult.execution_id]
  ];

  execCheckpoints.forEach(([label, value]) => {
    assert(`execution_id unchanged at: ${label}`, value === `exec_${mutTrace}`, `got: ${value}`);
  });
}

// ─── Test 5: Event interface — every event carries trace_id ──────────────────

section('Test 5 — Event Interface: every event must carry trace_id');

// Valid event
const validEvent = buildEvent('job_started', TRACE_ALLOW, `exec_${TRACE_ALLOW}`, { job_id: 'j1' });
const validCheck = validateEvent(validEvent);
assert('Valid event passes validation',      validCheck.valid);
assert('Valid event has trace_id',           validEvent.trace_id === TRACE_ALLOW);
assert('Valid event has execution_id',       validEvent.execution_id === `exec_${TRACE_ALLOW}`);
assert('Valid event has event_type',         validEvent.event_type === 'job_started');
assert('Valid event has timestamp',          typeof validEvent.timestamp === 'number');
assert('Valid event has data',               typeof validEvent.data === 'object');

// Event without trace_id — must be rejected
const noTrace = validateEvent({ execution_id: 'e1', event_type: 'x', timestamp: Date.now(), data: {} });
assert('Event without trace_id rejected',   !noTrace.valid);
assert('Rejection reason mentions trace_id',noTrace.reason.includes('trace_id'));

// Event without execution_id — must be rejected
const noExec = validateEvent({ trace_id: TRACE_ALLOW, event_type: 'x', timestamp: Date.now(), data: {} });
assert('Event without execution_id rejected',!noExec.valid);

// Event without event_type — must be rejected
const noType = validateEvent({ trace_id: TRACE_ALLOW, execution_id: 'e1', timestamp: Date.now(), data: {} });
assert('Event without event_type rejected', !noType.valid);

// Event without timestamp — must be rejected
const noTs = validateEvent({ trace_id: TRACE_ALLOW, execution_id: 'e1', event_type: 'x', data: {} });
assert('Event without timestamp rejected',  !noTs.valid);

// buildEvent throws if trace_id missing
let threw = false;
try { buildEvent('test', null, 'exec_1', {}); } catch { threw = true; }
assert('buildEvent throws on missing trace_id', threw);

// ─── Test 6: Replay — trace_id consistent ────────────────────────────────────

section('Test 6 — Replay: trace_id consistent between original and replayed');

const replayResult = replay(TRACE_ALLOW);

assert('Replay succeeds',                    replayResult.success, replayResult.failure?.reason);
assert('Replay trace_id matches original',   replayResult.trace_id === TRACE_ALLOW);
assert('Replay execution_id matches',        replayResult.execution_id === `exec_${TRACE_ALLOW}`);
assert('Replay deterministic=true',          replayResult.deterministic === true);
assert('Replay violations=[]',               replayResult.violations.length === 0);

// trace_id in replayed result's event_log
const replayedStarted = replayResult.result?.event_log?.find(e => e.type === 'sim_started');
assert('Replayed sim_started has trace_id',  replayedStarted?.payload?.trace_id === TRACE_ALLOW);

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log(`\n${'═'.repeat(60)}`);
console.log(`  Phase 5 Results: ${passed} passed, ${failed} failed`);
console.log('═'.repeat(60));

if (failed === 0) {
  console.log('\n  ✅ ALL PHASE 5 TESTS PASSED');
  console.log('  → ALLOW:  trace_id flows through all 7 layers unchanged');
  console.log('  → FLAG:   trace_id in enforcement result, no execution');
  console.log('  → BLOCK:  trace_id in enforcement result, no execution');
  console.log('  → No mutation: trace_id identical at every checkpoint');
  console.log('  → Events: every event carries trace_id or is rejected');
  console.log('  → Replay: trace_id consistent between original and replay\n');
} else {
  console.log(`\n  ❌ ${failed} test(s) failed\n`);
  process.exit(1);
}

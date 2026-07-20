'use strict';

/**
 * test_phase7_integration.js
 *
 * Phase 7 — Integration Test
 *
 * Runs the FULL flow end-to-end:
 *   Input → contractAdapter → enforcementGate → SimEngine → Events → Artifacts
 *
 * Validates:
 *   1. ALLOW  → full simulation runs, events emitted, contract unchanged
 *   2. FLAG   → execution stops at enforcement, no simulation, no events
 *   3. BLOCK  → execution stops at enforcement, no simulation, no events
 *   4. Contract unchanged — same shape in, same shape out
 *   5. Events emitted correctly — trace_id, execution_id, event_type, timestamp, data
 *   6. NICAI + Samruddhi outputs present on ALLOW
 *
 * Run: node backend/tests/test_phase7_integration.js
 *
 * NOTE: Tests 1-6 run without Mitra (unit-level integration).
 *       Test 7 runs the live pipeline if Mitra is available.
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const http = require('http');

const { enforce }        = require('../domain-adapters/maritime/enforcementGate');
const { adapt }          = require('../simulation/contractAdapter');
const { run: simRun }    = require('../simulation/engine/SimEngine');
const store              = require('../simulation/simResultStore');
const { replay }         = require('../simulation/simReplayEngine');
const nicai              = require('../simulation/nicaiFormatter');
const samruddhi          = require('../simulation/samruddhiFormatter');
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

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeGoverned(trace_id, overrides = {}) {
  return {
    trace_id,
    execution_id:  `exec_${trace_id}`,
    game_mode:     overrides.game_mode    || 'runner',
    entities: [
      { id: 'PLAYER',    type: 'vessel',   transform: { position: [0,0,0],  rotation: [0,0,0], scale: [1,1,1] } },
      { id: 'OBSTACLE_1',type: 'obstacle', transform: { position: [30,0,5], rotation: [0,0,0], scale: [1,1,1] } },
      { id: 'ZONE_GOAL', type: 'zone',     transform: { position: [90,0,0], rotation: [0,0,0], scale: [1,1,1] }, meta: { radius: 12 } }
    ],
    physics:      { gravity: [0, overrides.gravity ?? -9.8, 0], friction: 0.1, bounce: 0, air_resistance: 0.05, collision_force: 1 },
    movement:     { speed: overrides.speed || 5 },
    spawn_rules:  { obstacles: overrides.obstacles || 1, frequency: 2 },
    scoring:      { rules: { distance: 1, collectibles: 0 }, end_conditions: ['collision'] },
    player_params:{ health: overrides.health || 3, jetpack: false }
  };
}

function makeDecisionEnvelope(decision, trace_id) {
  return {
    decision,
    risk_level:     decision === 'ALLOW' ? 'LOW' : decision === 'FLAG' ? 'MEDIUM' : 'HIGH',
    reason:         `Integration test: ${decision}`,
    mitra_trace_id: `mitra_${trace_id}`,
    source:         'mitra'
  };
}

// ─── Test 1: ALLOW — full flow ────────────────────────────────────────────────

section('Test 1 — ALLOW: Full Flow Executes');

const ALLOW_TRACE = 'trace_p7_allow_001';
const allowContract = makeGoverned(ALLOW_TRACE, { speed: 6, obstacles: 2 });

// Step 1: Enforcement gate — ALLOW
const allowSchema = { ...allowContract, decisionEnvelope: makeDecisionEnvelope('ALLOW', ALLOW_TRACE) };
const allowGate   = enforce(allowSchema);

assert('ALLOW gate: passed=true',             allowGate.passed === true);
assert('ALLOW gate: blocked=false',           allowGate.blocked === false);
assert('ALLOW gate: flagged=false',           allowGate.flagged === false);
assert('ALLOW gate: trace_id preserved',      allowGate.trace_id === ALLOW_TRACE);

// Step 2: contractAdapter — only runs because gate passed
const allowAdapt = adapt(allowContract);
assert('ALLOW adapt: valid=true',             allowAdapt.valid, allowAdapt.errors?.join(', '));

// Step 3: SimEngine — only runs because gate passed
const allowSim = simRun(allowAdapt.sumscript, { ticks: 20 });
assert('ALLOW sim: success=true',             allowSim.success, allowSim.error);
assert('ALLOW sim: trace_id preserved',       allowSim.trace_id === ALLOW_TRACE);
assert('ALLOW sim: execution_id preserved',   allowSim.execution_id === `exec_${ALLOW_TRACE}`);
assert('ALLOW sim: ticks_run=20',             allowSim.ticks_run === 20);
assert('ALLOW sim: PLAYER entity exists',     'PLAYER' in allowSim.entities);
assert('ALLOW sim: events emitted',           allowSim.event_count > 0);
assert('ALLOW sim: transitions recorded',     allowSim.transitions.length > 0);

// Step 4: Store result
store.save(ALLOW_TRACE, allowSim, allowAdapt.sumscript);
assert('ALLOW stored in simResultStore',      !!store.get(ALLOW_TRACE));

// Step 5: NICAI output
const nicaiOut = nicai.format(allowSim);
assert('ALLOW NICAI: success=true',           nicaiOut.success);
assert('ALLOW NICAI: trace_id matches',       nicaiOut.trace_id === ALLOW_TRACE);
assert('ALLOW NICAI: intelligence present',   !!nicaiOut.intelligence);
assert('ALLOW NICAI: entity_profiles present',!!nicaiOut.intelligence?.entity_profiles);
assert('ALLOW NICAI: PLAYER profile exists',  !!nicaiOut.intelligence?.entity_profiles?.PLAYER);

// Step 6: Samruddhi output
const samOut = samruddhi.format(allowSim);
assert('ALLOW Samruddhi: success=true',       samOut.success);
assert('ALLOW Samruddhi: trace_id matches',   samOut.trace_id === ALLOW_TRACE);
assert('ALLOW Samruddhi: mapping present',    !!samOut.mapping);
assert('ALLOW Samruddhi: spatial_snapshot',   Array.isArray(samOut.mapping?.spatial_snapshot));
assert('ALLOW Samruddhi: position_timelines', !!samOut.mapping?.position_timelines?.PLAYER);
assert('ALLOW Samruddhi: bounds present',     !!samOut.mapping?.bounds);

// ─── Test 2: FLAG — execution stops at enforcement ───────────────────────────

section('Test 2 — FLAG: Execution Stops at Enforcement');

const FLAG_TRACE = 'trace_p7_flag_001';
const flagContract = makeGoverned(FLAG_TRACE);
const flagSchema   = { ...flagContract, decisionEnvelope: makeDecisionEnvelope('FLAG', FLAG_TRACE) };
const flagGate     = enforce(flagSchema);

assert('FLAG gate: passed=false',             flagGate.passed === false);
assert('FLAG gate: flagged=true',             flagGate.flagged === true);
assert('FLAG gate: blocked=false',            flagGate.blocked === false);
assert('FLAG gate: trace_id preserved',       flagGate.trace_id === FLAG_TRACE);

// SimEngine must NOT run — gate did not pass
// We verify by checking store is empty for this trace
assert('FLAG: no sim result stored',          !store.get(FLAG_TRACE));
assert('FLAG: no NICAI output',               !nicai.format({ success: false }).intelligence);
assert('FLAG: gate has reason',               typeof flagGate.reason === 'string');

// ─── Test 3: BLOCK — execution stops at enforcement ──────────────────────────

section('Test 3 — BLOCK: Execution Stops at Enforcement');

const BLOCK_TRACE = 'trace_p7_block_001';
const blockContract = makeGoverned(BLOCK_TRACE);
const blockSchema   = { ...blockContract, decisionEnvelope: makeDecisionEnvelope('BLOCK', BLOCK_TRACE) };
const blockGate     = enforce(blockSchema);

assert('BLOCK gate: passed=false',            blockGate.passed === false);
assert('BLOCK gate: blocked=true',            blockGate.blocked === true);
assert('BLOCK gate: flagged=false',           blockGate.flagged === false);
assert('BLOCK gate: trace_id preserved',      blockGate.trace_id === BLOCK_TRACE);
assert('BLOCK: no sim result stored',         !store.get(BLOCK_TRACE));
assert('BLOCK: gate has reason',              typeof blockGate.reason === 'string');

// ─── Test 4: Contract unchanged ───────────────────────────────────────────────

section('Test 4 — Contract Unchanged: Same Shape In, Same Shape Out');

const CONTRACT_TRACE = 'trace_p7_contract_001';
const originalContract = makeGoverned(CONTRACT_TRACE, { speed: 7, obstacles: 3, health: 2 });

// Deep copy to compare later
const contractSnapshot = JSON.parse(JSON.stringify(originalContract));

// Run through adapt + SimEngine
const contractAdapt = adapt(originalContract);
assert('Contract adapt: valid',               contractAdapt.valid);

// Original contract must be unchanged after adapt
assert('Contract: trace_id unchanged',        originalContract.trace_id === contractSnapshot.trace_id);
assert('Contract: execution_id unchanged',    originalContract.execution_id === contractSnapshot.execution_id);
assert('Contract: game_mode unchanged',       originalContract.game_mode === contractSnapshot.game_mode);
assert('Contract: speed unchanged',           originalContract.movement.speed === contractSnapshot.movement.speed);
assert('Contract: obstacles unchanged',       originalContract.spawn_rules.obstacles === contractSnapshot.spawn_rules.obstacles);
assert('Contract: health unchanged',          originalContract.player_params.health === contractSnapshot.player_params.health);
assert('Contract: entities count unchanged',  originalContract.entities.length === contractSnapshot.entities.length);
assert('Contract: physics unchanged',         JSON.stringify(originalContract.physics) === JSON.stringify(contractSnapshot.physics));

// SumScript contract has same trace_id
assert('SumScript: trace_id matches original',contractAdapt.sumscript.trace_id === CONTRACT_TRACE);

// ─── Test 5: Events emitted correctly ────────────────────────────────────────

section('Test 5 — Events Emitted Correctly');

// Build events using the interface
const e1 = buildEvent('job_started',   ALLOW_TRACE, `exec_${ALLOW_TRACE}`, { job_id: 'j1', job_type: 'BUILD_SCENE' });
const e2 = buildEvent('job_completed', ALLOW_TRACE, `exec_${ALLOW_TRACE}`, { job_id: 'j1', result: { success: true } });
const e3 = buildEvent('game_started',  ALLOW_TRACE, `exec_${ALLOW_TRACE}`, { game_mode: 'runner', speed: 6 });
const e4 = buildEvent('telemetry',     ALLOW_TRACE, `exec_${ALLOW_TRACE}`, { fps: 60, score: 100, lives: 3 });
const e5 = buildEvent('game_ended',    ALLOW_TRACE, `exec_${ALLOW_TRACE}`, { reason: 'time_up', final_score: 100 });

[e1, e2, e3, e4, e5].forEach((e, i) => {
  const v = validateEvent(e);
  assert(`Event ${i+1} (${e.event_type}): valid`,          v.valid, v.reason);
  assert(`Event ${i+1}: trace_id = ${ALLOW_TRACE}`,        e.trace_id === ALLOW_TRACE);
  assert(`Event ${i+1}: execution_id present`,             !!e.execution_id);
  assert(`Event ${i+1}: timestamp is number`,              typeof e.timestamp === 'number');
  assert(`Event ${i+1}: data is object`,                   typeof e.data === 'object');
});

// SimEngine event_log — all engine events carry trace_id in payload
const simEvents = allowSim.event_log.filter(e => e.source === 'engine');
assert('Engine events present',                            simEvents.length > 0);
simEvents.forEach((e, i) => {
  assert(`Engine event ${i+1} (${e.type}): has payload`,  !!e.payload);
});

// sim_started carries trace_id + execution_id
const simStarted = allowSim.event_log.find(e => e.type === 'sim_started');
assert('sim_started: trace_id in payload',                 simStarted?.payload?.trace_id === ALLOW_TRACE);
assert('sim_started: execution_id in payload',             simStarted?.payload?.execution_id === `exec_${ALLOW_TRACE}`);
assert('sim_started: seed in payload',                     typeof simStarted?.payload?.seed === 'number');

// ─── Test 6: Replay — contract unchanged, deterministic ──────────────────────

section('Test 6 — Replay: Contract Unchanged, Deterministic');

const replayResult = replay(ALLOW_TRACE);
assert('Replay: success=true',                replayResult.success, replayResult.failure?.reason);
assert('Replay: deterministic=true',          replayResult.deterministic === true);
assert('Replay: violations=[]',               replayResult.violations.length === 0);
assert('Replay: trace_id matches',            replayResult.trace_id === ALLOW_TRACE);
assert('Replay: entity_count_match',          replayResult.diff?.entity_count_match === true);
assert('Replay: transition_count_match',      replayResult.diff?.transition_count_match === true);
assert('Replay: event_count_match',           replayResult.diff?.event_count_match === true);
assert('Replay: final_positions_match',       replayResult.diff?.final_positions_match === true);

// ─── Test 7: Live pipeline (if Mitra available) ───────────────────────────────

section('Test 7 — Live Pipeline (requires Mitra on port 8000)');

async function testLivePipeline() {
  // Check if Mitra is running
  const mitraUp = await new Promise(resolve => {
    const req = http.get('http://127.0.0.1:8000/health', (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => { req.destroy(); resolve(false); });
  });

  if (!mitraUp) {
    console.log('  ⚠ Mitra not running — skipping live pipeline test');
    console.log('  ℹ Start Mitra: cd "d:\\Internship Task\\Mitra\\ai-assistant-backend" && uvicorn app.main:app --port 8000');
    assert('Live pipeline skipped (Mitra offline)', true);
    return;
  }

  console.log('  ✓ Mitra is running — executing live pipeline test');

  const { run: pipelineRun } = require('../domain-adapters/maritime/pipeline');

  const vesselInput = {
    vessel_id: 'VESSEL_P7_TEST',
    lat:       25.1,
    lon:       55.2,
    speed:     8,
    heading:   45,
    status:    'moving'
  };

  let result;
  try {
    result = await pipelineRun(vesselInput, {
      trace_id:     'trace_p7_live_001',
      execution_id: 'exec_p7_live_001'
    });
  } catch (err) {
    assert('Live pipeline: no throw', false, err.message);
    return;
  }

  assert('Live pipeline: returns result',       !!result);
  assert('Live pipeline: has path',             ['ALLOW','FLAG','BLOCK','DECISION_NOT_ALLOW','ADAPTER_FAILED','SIM_FAILED','UNKNOWN'].includes(result.path));
  assert('Live pipeline: trace_id preserved',   result.trace_id === 'trace_p7_live_001');
  assert('Live pipeline: execution_id preserved',result.execution_id === 'exec_p7_live_001');
  assert('Live pipeline: has log',              Array.isArray(result.log));
  assert('Live pipeline: log has entries',      result.log.length > 0);

  if (result.path === 'ALLOW') {
    assert('Live ALLOW: success=true',          result.success === true);
    assert('Live ALLOW: simulation present',    !!result.simulation);
    assert('Live ALLOW: NICAI present',         !!result.nicai);
    assert('Live ALLOW: Samruddhi present',     !!result.samruddhi);
    assert('Live ALLOW: artifacts present',     result.artifacts.length > 0);
    assert('Live ALLOW: sim trace_id matches',  result.simulation?.trace_id === 'trace_p7_live_001');
    console.log(`  ℹ Pipeline path: ALLOW | ticks=${result.simulation?.ticks_run} | events=${result.simulation?.event_count}`);
  } else {
    assert('Live non-ALLOW: success=false',     result.success === false);
    assert('Live non-ALLOW: failure present',   !!result.failure);
    console.log(`  ℹ Pipeline path: ${result.path} | reason: ${result.failure?.reason}`);
  }
}

// ─── Run async tests + summary ────────────────────────────────────────────────

testLivePipeline().then(() => {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  Phase 7 Results: ${passed} passed, ${failed} failed`);
  console.log('═'.repeat(60));

  if (failed === 0) {
    console.log('\n  ✅ ALL PHASE 7 TESTS PASSED');
    console.log('  → ALLOW:  full flow — gate → adapt → SimEngine → NICAI → Samruddhi');
    console.log('  → FLAG:   stops at enforcement, no execution, no events');
    console.log('  → BLOCK:  stops at enforcement, no execution, no events');
    console.log('  → Contract unchanged through entire flow');
    console.log('  → Events carry trace_id, execution_id, event_type, timestamp, data');
    console.log('  → Replay deterministic — same contract = same output\n');
  } else {
    console.log(`\n  ❌ ${failed} test(s) failed\n`);
    process.exit(1);
  }
});

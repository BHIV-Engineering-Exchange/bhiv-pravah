'use strict';

const { adapt }  = require('./simulation/contractAdapter');
const { run }    = require('./simulation/engine/SimEngine');
const store      = require('./simulation/simResultStore');
const { replay } = require('./simulation/simReplayEngine');

let pass = 0, fail = 0;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

const CONTRACT = {
  trace_id: 'trace-p4-001', execution_id: 'exec-p4-001',
  domain: 'maritime', scenario: 'patrol',
  entities: [
    { id: 'vessel_1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] },
    { id: 'zone_a',   type: 'zone',   position: [15,0,0], behaviors: [], meta: { radius: 5 } }
  ],
  behaviors: [{ id: 'b1', script: 'move_to', params: { target: [30,0,0], speed: 3, threshold: 1 } }],
  rules: [
    { id: 'r1', trigger: 'on_zone_enter', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'flag_entity', params: { reason: 'zone_entered' } }, enabled: true }
  ],
  constraints: { movement: { speed: 3 } },
  ticks: 15
};

console.log('\n=== Phase 4 — simulationState.v1 output contract ===\n');

const adapted = adapt(CONTRACT);
const result  = run(adapted.sumscript, { ticks: CONTRACT.ticks });

// ── Test 1: required top-level fields ─────────────────────────────────────────
console.log('Test 1: all required v1 fields present');
check('trace_id',     typeof result.trace_id     === 'string');
check('execution_id', typeof result.execution_id === 'string');
check('status',       result.status === 'completed');
check('ticks_run',    typeof result.ticks_run    === 'number');
check('entities',     typeof result.entities     === 'object');
check('transitions',  Array.isArray(result.transitions));
check('event_log',    Array.isArray(result.event_log));
check('state_summary',typeof result.state_summary === 'object');
check('zones',        typeof result.zones         === 'object');
check('metrics',      typeof result.metrics       === 'object');

// ── Test 2: NO internal/domain fields at top level ────────────────────────────
console.log('\nTest 2: no internal or domain fields in output');
check('no seed',          !('seed'          in result));
check('no flags',         !('flags'         in result));
check('no blocked',       !('blocked'       in result));
check('no tick_snapshots',!('tick_snapshots' in result));
check('no event_count',   !('event_count'   in result));
check('no game_stats',    !('game_stats'    in result));
check('no game_mode',     !('game_mode'     in result));
check('no duration',      !('duration'      in result));
check('no started_at',    !('started_at'    in result));

// ── Test 3: state_summary shape ───────────────────────────────────────────────
console.log('\nTest 3: state_summary has correct shape');
const ss = result.state_summary;
check('entity_count is number',     typeof ss.entity_count     === 'number');
check('active_count is number',     typeof ss.active_count     === 'number');
check('flagged_count is number',    typeof ss.flagged_count    === 'number');
check('blocked_count is number',    typeof ss.blocked_count    === 'number');
check('collision_count is number',  typeof ss.collision_count  === 'number');
check('zone_entry_count is number', typeof ss.zone_entry_count === 'number');
check('transition_count is number', typeof ss.transition_count === 'number');
check('event_count is number',      typeof ss.event_count      === 'number');
check('flagged_entities is object', typeof ss.flagged_entities === 'object');
check('blocked_entities is object', typeof ss.blocked_entities === 'object');
check('no raw flags at top level',  !('flags' in result));
check('no raw blocked at top level',!('blocked' in result));

// ── Test 4: metrics shape ─────────────────────────────────────────────────────
console.log('\nTest 4: metrics has correct shape');
const m = result.metrics;
check('ticks_run in metrics',           typeof m.ticks_run            === 'number');
check('events_per_tick in metrics',     typeof m.events_per_tick      === 'number');
check('transitions_per_tick in metrics',typeof m.transitions_per_tick === 'number');
check('tick_snapshots in metrics',      Array.isArray(m.tick_snapshots));
check('tick_snapshots NOT at top level',!('tick_snapshots' in result));

// ── Test 5: entity shape ──────────────────────────────────────────────────────
console.log('\nTest 5: entity output shape');
const entity = result.entities['vessel_1'];
check('entity.id',       typeof entity.id       === 'string');
check('entity.type',     typeof entity.type     === 'string');
check('entity.state',    typeof entity.state    === 'string');
check('entity.position', Array.isArray(entity.position) && entity.position.length === 3);
check('entity.velocity', Array.isArray(entity.velocity) && entity.velocity.length === 3);

// ── Test 6: transition shape ──────────────────────────────────────────────────
console.log('\nTest 6: transition shape');
if (result.transitions.length > 0) {
  const t = result.transitions[0];
  check('transition.entity_id', typeof t.entity_id === 'string');
  check('transition.field',     typeof t.field     === 'string');
  check('transition.tick',      typeof t.tick      === 'number');
  check('transition.reason',    typeof t.reason    === 'string');
  check('no recorded_at',       !('recorded_at' in t));
} else {
  console.log('  SKIP  no transitions (entity may not have moved enough)');
}

// ── Test 7: event_log shape ───────────────────────────────────────────────────
console.log('\nTest 7: event_log shape');
if (result.event_log.length > 0) {
  const e = result.event_log[0];
  check('event.source', typeof e.source === 'string');
  check('event.type',   typeof e.type   === 'string');
  check('event.tick',   typeof e.tick   === 'number');
  check('no logged_at', !('logged_at' in e));
} else {
  console.log('  SKIP  no events');
}

// ── Test 8: failed run produces v1 shape ──────────────────────────────────────
console.log('\nTest 8: failed run still produces v1 shape');
const badResult = run({ trace_id: null, execution_id: null }, { ticks: 5 });
check('status=failed',       badResult.status === 'failed');
check('error is string',     typeof badResult.error === 'string');
check('entities is object',  typeof badResult.entities === 'object');
check('transitions is array',Array.isArray(badResult.transitions));
check('state_summary exists',typeof badResult.state_summary === 'object');
check('metrics exists',      typeof badResult.metrics === 'object');

// ── Test 9: replay uses v1 shape ──────────────────────────────────────────────
console.log('\nTest 9: replay result uses v1 shape');
store.save(result.trace_id, result, adapted.sumscript);
const replayResult = replay(result.trace_id);
check('replay success',                replayResult.success);
check('replay.result is v1',           replayResult.result?.status === 'completed');
check('no nicai in replay',            !('nicai'     in replayResult));
check('no samruddhi in replay',        !('samruddhi' in replayResult));
check('replay diff present',           typeof replayResult.diff === 'object');
check('event_count_match',             replayResult.diff?.event_count_match === true);

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);

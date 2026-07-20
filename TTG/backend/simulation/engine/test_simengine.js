'use strict';

/**
 * test_simengine.js
 *
 * End-to-end test for the Phase 3 Simulation Engine.
 * Run: node backend/simulation/engine/test_simengine.js
 */

const { run } = require('./SimEngine');

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

// ─── Contract ─────────────────────────────────────────────────────────────────

const CONTRACT = {
  trace_id:     'trace_engine_test_001',
  execution_id: 'exec_engine_test_001',

  entities: [
    {
      id: 'VESSEL_ALPHA', type: 'vessel',
      position: [0, 0, 0], state: 'active',
      behaviors: ['move_forward'],
      meta: {}
    },
    {
      id: 'VESSEL_BRAVO', type: 'vessel',
      position: [50, 0, 0], state: 'active',
      behaviors: ['anchor_b'],
      meta: {}
    },
    {
      id: 'ZONE_A', type: 'zone',
      position: [20, 0, 0], state: 'active',
      behaviors: [],
      meta: { radius: 5 }
    }
  ],

  transforms: [
    { entity_id: 'VESSEL_ALPHA', op: 'move', params: { delta: [1, 0, 0] } }
  ],

  rules: [
    {
      id: 'flag_fast', trigger: 'on_tick',
      condition: { field: 'meta.speed', op: 'gt', value: 100 },
      action: { type: 'flag_entity', params: { reason: 'overspeed' } }
    },
    {
      id: 'stop_bravo', trigger: 'on_tick',
      condition: { field: 'state', op: 'eq', value: 'stopped', target: 'VESSEL_BRAVO' },
      action: { type: 'emit_event', params: { event_type: 'bravo_anchored', data: {} } }
    }
  ],

  behaviors: [
    {
      id: 'move_forward', script: 'move_to',
      params: { target: [30, 0, 0], speed: 2, threshold: 0.5 }
    },
    {
      id: 'anchor_b', script: 'anchor',
      params: {}
    }
  ]
};

// ─── Tests ────────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════════');
console.log('  SimEngine — Phase 3 Test Suite');
console.log('══════════════════════════════════════════\n');

// 1. Basic run
console.log('1. Basic Run');
const result = run(CONTRACT, { ticks: 10 });
assert('run succeeds',           result.success, result.error);
assert('status = completed',     result.status === 'completed');
assert('ticks_run = 10',         result.ticks_run === 10);
assert('trace_id preserved',     result.trace_id === 'trace_engine_test_001');
assert('execution_id preserved', result.execution_id === 'exec_engine_test_001');
assert('seed is a number',       typeof result.seed === 'number');

// 2. Entity state
console.log('\n2. Entity State After 10 Ticks');
assert('entities returned',      Object.keys(result.entities).length === 3);
assert('VESSEL_ALPHA exists',    'VESSEL_ALPHA' in result.entities);
assert('VESSEL_BRAVO exists',    'VESSEL_BRAVO' in result.entities);

const alpha = result.entities['VESSEL_ALPHA'];
const bravo = result.entities['VESSEL_BRAVO'];

assert('ALPHA moved from origin',  alpha.position[0] > 1);
assert('BRAVO state = stopped',    bravo.state === 'stopped');
assert('BRAVO velocity zeroed',    bravo.velocity.every(v => v === 0));

// 3. Transitions
console.log('\n3. State Transitions');
assert('transitions recorded',     result.transitions.length > 0);
const stateTransitions = result.transitions.filter(t => t.field === 'state');
assert('state transitions exist',  stateTransitions.length > 0);
assert('BRAVO stopped transition', stateTransitions.some(t => t.entity_id === 'VESSEL_BRAVO' && t.to === 'stopped'));

// 4. Event log
console.log('\n4. Event Log');
assert('events recorded',          result.event_count > 0);
assert('event_log is array',       Array.isArray(result.event_log));
assert('sim_started event exists', result.event_log.some(e => e.type === 'sim_started'));
assert('sim_completed event exists',result.event_log.some(e => e.type === 'sim_completed'));

// 5. Tick snapshots
console.log('\n5. Tick Snapshots');
assert('10 tick snapshots',        result.tick_snapshots.length === 10);
assert('snapshot has tick number', result.tick_snapshots[0].tick === 1);
assert('snapshot has entity_states', typeof result.tick_snapshots[0].entity_states === 'object');
assert('snapshot has event count', typeof result.tick_snapshots[0].events_this_tick === 'number');

// 6. Zone events
console.log('\n6. Zone Events');
const zoneEnterEvents = result.event_log.filter(e => e.type === 'zone_enter');
assert('zone_enter fired when ALPHA enters ZONE_A', zoneEnterEvents.length > 0);

// 7. Rule actions
console.log('\n7. Rule Actions');
const ruleEvents = result.event_log.filter(e => e.source === 'rule');
assert('rule events logged',       ruleEvents.length > 0);
assert('stop_bravo rule fired',    ruleEvents.some(e => e.rule_id === 'stop_bravo'));

// 8. Determinism
console.log('\n8. Determinism');
const run1 = run(CONTRACT, { ticks: 10 });
const run2 = run(CONTRACT, { ticks: 10 });
assert('same seed both runs',      run1.seed === run2.seed);
assert('same final positions',
  JSON.stringify(run1.entities['VESSEL_ALPHA'].position) ===
  JSON.stringify(run2.entities['VESSEL_ALPHA'].position)
);
assert('same transition count',    run1.transitions.length === run2.transitions.length);
assert('same event count',         run1.event_count === run2.event_count);

// 9. Invalid contract
console.log('\n9. Invalid Contract Handling');
const bad = run({ trace_id: 'x' }, { ticks: 5 });
assert('invalid contract returns failure', !bad.success);
assert('error message present',            typeof bad.error === 'string');
assert('no entities on failure',           Object.keys(bad.entities).length === 0);

// 10. Timing
console.log('\n10. Timing');
assert('started_at is set',  result.started_at !== null);
assert('ended_at is set',    result.ended_at !== null);
assert('duration > 0',       result.duration >= 0);

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════════');
console.log(`  Results: ${passed} passed, ${failed} failed`);
console.log('══════════════════════════════════════════\n');

if (failed > 0) process.exit(1);

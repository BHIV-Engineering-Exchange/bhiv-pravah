'use strict';

/**
 * test_sumscript.js
 *
 * Validates the SumScript runtime layer end-to-end.
 * Run: node backend/simulation/sumscript/test_sumscript.js
 */

const SumScript = require('./index');

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

// ─── Sample contract ──────────────────────────────────────────────────────────

const SAMPLE_CONTRACT = {
  trace_id:     'trace_sumscript_test_001',
  execution_id: 'exec_sumscript_test_001',

  entities: [
    {
      id:       'VESSEL_ALPHA',
      type:     'vessel',
      position: [25.1, 0, 55.2],
      rotation: [0, 45, 0],
      velocity: [0, 0, 0],
      state:    'active',
      behaviors: ['patrol_alpha'],
      meta:     { patrol_index: 0 }
    },
    {
      id:       'VESSEL_BRAVO',
      type:     'vessel',
      position: [25.3, 0, 55.4],
      state:    'active',
      behaviors: ['anchor_bravo']
    },
    {
      id:       'ZONE_RESTRICTED',
      type:     'zone',
      position: [25.3, 0, 55.35],
      state:    'active',
      behaviors: []
    }
  ],

  transforms: [
    {
      entity_id: 'VESSEL_ALPHA',
      op:        'move',
      params:    { delta: [0.05, 0, 0.05] }
    },
    {
      entity_id: 'VESSEL_BRAVO',
      op:        'rotate',
      params:    { rotation: [0, 135, 0] }
    }
  ],

  rules: [
    {
      id:      'rule_high_speed',
      trigger: 'on_tick',
      condition: {
        field: 'meta.speed',
        op:    'gt',
        value: 10
      },
      action: {
        type:   'flag_entity',
        params: { reason: 'speed exceeds threshold' }
      }
    },
    {
      id:      'rule_stopped_state',
      trigger: 'on_state_change',
      condition: {
        field:  'state',
        op:     'eq',
        value:  'stopped',
        target: 'VESSEL_BRAVO'
      },
      action: {
        type:   'emit_event',
        params: { event_type: 'vessel_anchored', data: { vessel_id: 'VESSEL_BRAVO' } }
      }
    }
  ],

  behaviors: [
    {
      id:     'patrol_alpha',
      script: 'patrol',
      params: {
        waypoints: [
          [25.1, 0, 55.2],
          [25.3, 0, 55.4],
          [25.5, 0, 55.1]
        ],
        speed:     0.05,
        threshold: 0.1
      }
    },
    {
      id:     'anchor_bravo',
      script: 'anchor',
      params: {}
    }
  ]
};

// ─── Tests ────────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════════');
console.log('  SumScript Runtime — Test Suite');
console.log('══════════════════════════════════════════\n');

// 1. Validation
console.log('1. Schema Validation');
const valid_result = SumScript.validate(SAMPLE_CONTRACT);
assert('valid contract passes validation', valid_result.valid, valid_result.errors.join(', '));

const invalid_result = SumScript.validate({ trace_id: 'x', entities: [] });
assert('missing execution_id fails', !invalid_result.valid);
assert('empty entities fails', invalid_result.errors.some(e => e.includes('entities')));

// 2. Parse + normalize
console.log('\n2. Parse & Normalize');
const parsed = SumScript.parse(SAMPLE_CONTRACT);
assert('parse succeeds', parsed.valid, parsed.errors.join(', '));
assert('runtime object returned', parsed.runtime !== null);
assert('seed derived from trace_id', typeof parsed.runtime.contract.seed === 'number');
assert('same trace_id → same seed', (() => {
  const a = SumScript.parse(SAMPLE_CONTRACT);
  const b = SumScript.parse(SAMPLE_CONTRACT);
  return a.runtime.contract.seed === b.runtime.contract.seed;
})());

const { runtime } = parsed;

// 3. Entities map
console.log('\n3. Entity Registry');
const entities_map = runtime.buildEntitiesMap();
assert('entities map built', Object.keys(entities_map).length === 3);
assert('VESSEL_ALPHA in map', 'VESSEL_ALPHA' in entities_map);
assert('VESSEL_BRAVO in map', 'VESSEL_BRAVO' in entities_map);
assert('ZONE_RESTRICTED in map', 'ZONE_RESTRICTED' in entities_map);
assert('entity has normalized defaults', entities_map['VESSEL_BRAVO'].rotation !== undefined);

// 4. Transforms
console.log('\n4. Transforms');
const { entities_map: after_transforms, events: t_events } = runtime.applyTransforms(entities_map);
assert('transforms applied', t_events.length === 2);
assert('VESSEL_ALPHA moved', after_transforms['VESSEL_ALPHA'].position[0] !== entities_map['VESSEL_ALPHA'].position[0]);
assert('VESSEL_BRAVO rotated', after_transforms['VESSEL_BRAVO'].rotation[1] === 135);
assert('transform events emitted', t_events.some(e => e.type === 'transform_move'));
assert('transform events emitted', t_events.some(e => e.type === 'transform_rotate'));

// 5. Behaviors
console.log('\n5. Behaviors');
const context = {
  tick:         1,
  dt:           1,
  entities_map: after_transforms,
  rng:          null
};

const alpha_delta = runtime.executeBehaviors(after_transforms['VESSEL_ALPHA'], context);
assert('patrol behavior returns delta', alpha_delta !== null);
assert('patrol sets velocity', alpha_delta.velocity !== null);

const bravo_delta = runtime.executeBehaviors(after_transforms['VESSEL_BRAVO'], context);
assert('anchor behavior returns delta', bravo_delta !== null);
assert('anchor sets state to stopped', bravo_delta.state === 'stopped');
assert('anchor zeroes velocity', bravo_delta.velocity && bravo_delta.velocity.every(v => v === 0));

// 6. Rules
console.log('\n6. Rules');
// Inject a high-speed entity to trigger rule_high_speed
const high_speed_map = {
  ...after_transforms,
  VESSEL_FAST: {
    id: 'VESSEL_FAST', type: 'vessel',
    position: [0, 0, 0], rotation: [0, 0, 0], velocity: [0, 0, 0],
    state: 'active', behaviors: [], meta: { speed: 15 }
  }
};

const simState = { entities_map: high_speed_map, tick: 1, events: [] };
const rule_results = runtime.evaluateRules('on_tick', simState);
assert('high speed rule fires', rule_results.some(r => r.type === 'flag_entity'));
assert('flag_entity has reason', rule_results.find(r => r.type === 'flag_entity')?.payload?.reason !== undefined);

// on_state_change rule — VESSEL_BRAVO is stopped
const stopped_map = {
  ...after_transforms,
  VESSEL_BRAVO: { ...after_transforms['VESSEL_BRAVO'], state: 'stopped' }
};
const state_change_results = runtime.evaluateRules('on_state_change', {
  entities_map: stopped_map, tick: 2, events: []
});
assert('state_change rule fires for VESSEL_BRAVO', state_change_results.some(r => r.type === 'emit_event'));

// 7. Determinism check
console.log('\n7. Determinism');
const run1 = SumScript.parse(SAMPLE_CONTRACT);
const run2 = SumScript.parse(SAMPLE_CONTRACT);
const map1 = run1.runtime.buildEntitiesMap();
const map2 = run2.runtime.buildEntitiesMap();
const { entities_map: em1 } = run1.runtime.applyTransforms(map1);
const { entities_map: em2 } = run2.runtime.applyTransforms(map2);
assert('same contract → same entity positions', JSON.stringify(em1) === JSON.stringify(em2));
assert('same contract → same seed', run1.runtime.contract.seed === run2.runtime.contract.seed);

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════════');
console.log(`  Results: ${passed} passed, ${failed} failed`);
console.log('══════════════════════════════════════════\n');

if (failed > 0) process.exit(1);

'use strict';

const { adapt }  = require('./simulation/contractAdapter');
const { run }    = require('./simulation/engine/SimEngine');

let pass = 0, fail = 0;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

// ── Canonical test contract ───────────────────────────────────────────────────
// All movement, rules, state transitions declared explicitly in SumScript.
// No domain inference anywhere.
const CONTRACT = {
  trace_id:     'trace-p3-determinism',
  execution_id: 'exec-p3-001',
  domain:       'education',
  scenario:     'patrol_test',
  entities: [
    {
      id: 'agent_1', type: 'vessel', position: [0, 0, 0],
      behaviors: ['b_patrol'],
      meta: { label: 'patroller' }
    },
    {
      id: 'zone_a', type: 'zone', position: [20, 0, 0],
      behaviors: [],
      meta: { radius: 5 }
    }
  ],
  behaviors: [
    {
      id: 'b_patrol', script: 'patrol',
      params: {
        waypoints: [[20,0,0],[20,0,20],[0,0,20],[0,0,0]],
        speed: 3,
        threshold: 1
      }
    }
  ],
  rules: [
    {
      id: 'flag_on_zone', trigger: 'on_zone_enter',
      condition: { field: 'state', op: 'eq', value: 'active' },
      action: { type: 'flag_entity', params: { reason: 'entered_zone_a' } },
      enabled: true
    }
  ],
  constraints: { movement: { speed: 3 } },
  ticks: 20
};

console.log('\n=== Phase 3 — SumScript as Single Source of Truth ===\n');

// ── Test 1: adapter produces no implicit fields ───────────────────────────────
console.log('Test 1: adapter injects no implicit fields into entities');
const adapted = adapt(CONTRACT);
check('adapt succeeds', adapted.valid, adapted.errors);

const entity = adapted.sumscript.entities.find(e => e.id === 'agent_1');
check('entity.meta has no injected speed', !('speed' in entity.meta));
check('entity.meta preserves caller label', entity.meta.label === 'patroller');
check('entity.behaviors = [b_patrol] as declared', JSON.stringify(entity.behaviors) === JSON.stringify(['b_patrol']));

// ── Test 2: behavior params are the source of speed, not meta ─────────────────
console.log('\nTest 2: movement driven by behavior.params.speed, not entity.meta');
const behavior = adapted.sumscript.behaviors.find(b => b.id === 'b_patrol');
check('behavior.params.speed = 3', behavior.params.speed === 3);
check('behavior.params.waypoints declared', Array.isArray(behavior.params.waypoints) && behavior.params.waypoints.length === 4);

// ── Test 3: rules are passed through unchanged ────────────────────────────────
console.log('\nTest 3: rules passed through from contract unchanged');
const rule = adapted.sumscript.rules.find(r => r.id === 'flag_on_zone');
check('rule trigger = on_zone_enter', rule.trigger === 'on_zone_enter');
check('rule action = flag_entity',    rule.action.type === 'flag_entity');
check('rule enabled = true',          rule.enabled === true);

// ── Test 4: same contract → same output (determinism run 1 vs run 2) ──────────
console.log('\nTest 4: same contract → identical output (determinism)');
const r1 = run(adapted.sumscript, { ticks: CONTRACT.ticks });
const r2 = run(adapted.sumscript, { ticks: CONTRACT.ticks });

check('both runs succeed',            r1.success && r2.success);
check('same seed',                    r1.seed === r2.seed);
check('same ticks_run',               r1.ticks_run === r2.ticks_run);
check('same entity count',            Object.keys(r1.entities).length === Object.keys(r2.entities).length);
check('same transition count',        r1.transitions.length === r2.transitions.length);
check('same event count',             r1.event_count === r2.event_count);

// Compare final positions of every entity
let positionsMatch = true;
for (const id of Object.keys(r1.entities)) {
  const p1 = r1.entities[id].position;
  const p2 = r2.entities[id].position;
  if (p1[0] !== p2[0] || p1[1] !== p2[1] || p1[2] !== p2[2]) {
    positionsMatch = false;
    console.log(`    position mismatch for ${id}: run1=${JSON.stringify(p1)} run2=${JSON.stringify(p2)}`);
  }
}
check('all final positions identical', positionsMatch);

// Compare final states of every entity
let statesMatch = true;
for (const id of Object.keys(r1.entities)) {
  if (r1.entities[id].state !== r2.entities[id].state) {
    statesMatch = false;
  }
}
check('all final states identical', statesMatch);

// ── Test 5: state transitions driven by rules, not adapter ────────────────────
console.log('\nTest 5: state transitions driven by SumScript rules only');
// flag_on_zone rule should fire when agent_1 enters zone_a
const flagEvents = r1.event_log.filter(e => e.type === 'flag_entity');
const ruleEvents = r1.event_log.filter(e => e.source === 'rule');
check('rule events exist in log',     ruleEvents.length > 0);
check('no adapter-injected events',   !r1.event_log.some(e => e.source === 'adapter'));

// ── Test 6: third run still matches run 1 ────────────────────────────────────
console.log('\nTest 6: third run still matches (determinism is not fluke)');
const r3 = run(adapted.sumscript, { ticks: CONTRACT.ticks });
check('run3 seed = run1 seed',        r3.seed === r1.seed);
check('run3 event_count = run1',      r3.event_count === r1.event_count);
check('run3 transition count = run1', r3.transitions.length === r1.transitions.length);

let r3PosMatch = true;
for (const id of Object.keys(r1.entities)) {
  const p1 = r1.entities[id].position;
  const p3 = r3.entities[id].position;
  if (p1[0] !== p3[0] || p1[1] !== p3[1] || p1[2] !== p3[2]) r3PosMatch = false;
}
check('run3 final positions = run1',  r3PosMatch);

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);

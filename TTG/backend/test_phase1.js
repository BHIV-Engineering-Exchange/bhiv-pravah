'use strict';

const { adapt } = require('./simulation/contractAdapter');

let pass = 0, fail = 0;

function check(label, condition, detail = '') {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail); fail++; }
}

console.log('\n=== Phase 1 — contractAdapter tests ===\n');

// ── Test 1: game_mode is rejected ─────────────────────────────────────────────
console.log('Test 1: game_mode rejected');
const t1 = adapt({
  trace_id: 'trace-001', execution_id: 'exec-001',
  game_mode: 'runner',
  entities:  [{ id: 'e1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] }],
  behaviors: [{ id: 'b1', script: 'move_to', params: { target: [10,0,0], speed: 2, threshold: 1 } }]
});
check('valid=false when game_mode present', !t1.valid);
check('error mentions game_mode', t1.errors.some(e => e.includes('game_mode')), t1.errors);

// ── Test 2: speed passes through via constraints ──────────────────────────────
console.log('\nTest 2: speed passes through constraints');
const t2 = adapt({
  trace_id: 'trace-002', execution_id: 'exec-002',
  entities:  [{ id: 'e1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] }],
  behaviors: [{ id: 'b1', script: 'move_to', params: { target: [10,0,0], speed: 5, threshold: 1 } }],
  constraints: { movement: { speed: 5 }, physics: { gravity: [0,-9.8,0] }, player_params: { health: 3 } }
});
check('valid=true', t2.valid, t2.errors);
check('constraints.movement.speed = 5', t2.sumscript?.constraints?.movement?.speed === 5);
check('constraints.physics present',    typeof t2.sumscript?.constraints?.physics === 'object');
check('constraints.player_params present', typeof t2.sumscript?.constraints?.player_params === 'object');
check('entity meta.speed = 5', t2.sumscript?.entities[0]?.meta?.speed === 5);
check('game_mode NOT in sumscript', !('game_mode' in t2.sumscript));

// ── Test 3: valid contract — no constraints ───────────────────────────────────
console.log('\nTest 3: valid contract without constraints');
const t3 = adapt({
  trace_id: 'trace-003', execution_id: 'exec-003',
  domain: 'education', scenario: 'classroom',
  entities: [
    { id: 'student_1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] },
    { id: 'zone_exit', type: 'zone',   position: [50,0,0], behaviors: [] }
  ],
  behaviors: [{ id: 'b1', script: 'move_to', params: { target: [50,0,0], speed: 2, threshold: 1 } }],
  rules: [{ id: 'r1', trigger: 'on_zone_enter', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: { message: 'reached exit' } }, enabled: true }]
});
check('valid=true', t3.valid, t3.errors);
check('sumscript has entities',   Array.isArray(t3.sumscript?.entities));
check('sumscript has behaviors',  Array.isArray(t3.sumscript?.behaviors));
check('sumscript has rules',      Array.isArray(t3.sumscript?.rules));
check('sumscript has transforms', Array.isArray(t3.sumscript?.transforms));
check('game_mode NOT in sumscript', !('game_mode' in t3.sumscript));
check('spawn_rules NOT in sumscript', !('spawn_rules' in t3.sumscript));
check('scoring NOT in sumscript', !('scoring' in t3.sumscript));

// ── Test 4: missing required fields ──────────────────────────────────────────
console.log('\nTest 4: missing required fields');
const t4 = adapt({ trace_id: 'trace-004' });
check('valid=false', !t4.valid);
check('error mentions execution_id', t4.errors.some(e => e.includes('execution_id')), t4.errors);

// ── Test 5: empty entities → rejected ────────────────────────────────────────
console.log('\nTest 5: empty entities rejected');
const t5 = adapt({ trace_id: 'trace-005', execution_id: 'exec-005', entities: [], behaviors: [] });
check('valid=false', !t5.valid);
check('error mentions entities', t5.errors.some(e => e.includes('entities')), t5.errors);

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);

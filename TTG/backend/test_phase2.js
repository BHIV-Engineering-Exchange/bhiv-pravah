'use strict';

const { validate } = require('./simulation/contractValidator.v1');

let pass = 0, fail = 0;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

// ── Minimal valid contract ────────────────────────────────────────────────────
const VALID = {
  trace_id:     'trace-p2-001',
  execution_id: 'exec-p2-001',
  domain:       'education',
  scenario:     'classroom',
  entities: [
    { id: 'student_1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] },
    { id: 'zone_exit', type: 'zone',   position: [50,0,0], behaviors: [] }
  ],
  behaviors: [
    { id: 'b1', script: 'move_to', params: { target: [50,0,0], speed: 2, threshold: 1 } }
  ],
  rules: [
    { id: 'r1', trigger: 'on_zone_enter', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: { message: 'reached exit' } }, enabled: true }
  ],
  constraints: { movement: { speed: 2 }, physics: { gravity: [0,-9.8,0] }, player_params: { health: 3 } },
  ticks: 15
};

console.log('\n=== Phase 2 — simulationContract.v1 enforcement ===\n');

// ── Test 1: valid contract passes ─────────────────────────────────────────────
console.log('Test 1: valid contract passes');
const t1 = validate(VALID);
check('valid=true', t1.valid, t1.errors);

// ── Test 2: game_mode banned ──────────────────────────────────────────────────
console.log('\nTest 2: game_mode is banned');
const t2 = validate({ ...VALID, game_mode: 'runner' });
check('valid=false', !t2.valid);
check('error mentions game_mode', t2.errors.some(e => e.includes('game_mode')), t2.errors);

// ── Test 3: spawn_rules banned ────────────────────────────────────────────────
console.log('\nTest 3: spawn_rules is banned');
const t3 = validate({ ...VALID, spawn_rules: { obstacles: 3 } });
check('valid=false', !t3.valid);
check('error mentions spawn_rules', t3.errors.some(e => e.includes('spawn_rules')), t3.errors);

// ── Test 4: unknown top-level field rejected ──────────────────────────────────
console.log('\nTest 4: unknown top-level field rejected');
const t4 = validate({ ...VALID, mystery_field: 'hello' });
check('valid=false', !t4.valid);
check('error mentions mystery_field', t4.errors.some(e => e.includes('mystery_field')), t4.errors);

// ── Test 5: missing domain → rejected ────────────────────────────────────────
console.log('\nTest 5: missing domain rejected');
const { domain, ...noDomain } = VALID;
const t5 = validate(noDomain);
check('valid=false', !t5.valid);
check('error mentions domain', t5.errors.some(e => e.includes('domain')), t5.errors);

// ── Test 6: missing scenario → rejected ──────────────────────────────────────
console.log('\nTest 6: missing scenario rejected');
const { scenario, ...noScenario } = VALID;
const t6 = validate(noScenario);
check('valid=false', !t6.valid);
check('error mentions scenario', t6.errors.some(e => e.includes('scenario')), t6.errors);

// ── Test 7: invalid entity type → rejected ────────────────────────────────────
console.log('\nTest 7: invalid entity type rejected');
const t7 = validate({ ...VALID, entities: [{ id: 'e1', type: 'player', position: [0,0,0], behaviors: [] }] });
check('valid=false', !t7.valid);
check('error mentions type', t7.errors.some(e => e.includes('type')), t7.errors);

// ── Test 8: invalid behavior script → rejected ────────────────────────────────
console.log('\nTest 8: invalid behavior script rejected');
const t8 = validate({ ...VALID, behaviors: [{ id: 'b1', script: 'jump', params: {} }] });
check('valid=false', !t8.valid);
check('error mentions script', t8.errors.some(e => e.includes('script')), t8.errors);

// ── Test 9: invalid rule trigger → rejected ───────────────────────────────────
console.log('\nTest 9: invalid rule trigger rejected');
const t9 = validate({ ...VALID, rules: [{ id: 'r1', trigger: 'on_jump', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: {} } }] });
check('valid=false', !t9.valid);
check('error mentions trigger', t9.errors.some(e => e.includes('trigger')), t9.errors);

// ── Test 10: invalid condition op → rejected ──────────────────────────────────
console.log('\nTest 10: invalid condition op rejected');
const t10 = validate({ ...VALID, rules: [{ id: 'r1', trigger: 'on_tick', condition: { field: 'state', op: 'like', value: 'active' }, action: { type: 'log', params: {} } }] });
check('valid=false', !t10.valid);
check('error mentions op', t10.errors.some(e => e.includes('op')), t10.errors);

// ── Test 11: invalid rule action type → rejected ──────────────────────────────
console.log('\nTest 11: invalid rule action type rejected');
const t11 = validate({ ...VALID, rules: [{ id: 'r1', trigger: 'on_tick', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'kill_player', params: {} } }] });
check('valid=false', !t11.valid);
check('error mentions action.type', t11.errors.some(e => e.includes('action.type')), t11.errors);

// ── Test 12: unknown constraint key → rejected ────────────────────────────────
console.log('\nTest 12: unknown constraint key rejected');
const t12 = validate({ ...VALID, constraints: { movement: { speed: 2 }, arena_size: 100 } });
check('valid=false', !t12.valid);
check('error mentions arena_size', t12.errors.some(e => e.includes('arena_size')), t12.errors);

// ── Test 13: ticks out of range → rejected ────────────────────────────────────
console.log('\nTest 13: ticks out of range rejected');
const t13 = validate({ ...VALID, ticks: 9999 });
check('valid=false', !t13.valid);
check('error mentions ticks', t13.errors.some(e => e.includes('ticks')), t13.errors);

// ── Test 14: position wrong length → rejected ─────────────────────────────────
console.log('\nTest 14: position wrong length rejected');
const t14 = validate({ ...VALID, entities: [{ id: 'e1', type: 'vessel', position: [0,0], behaviors: [] }] });
check('valid=false', !t14.valid);
check('error mentions position', t14.errors.some(e => e.includes('position')), t14.errors);

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);

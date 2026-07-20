// test_state_integrity_guard.js - Phase 9: State Integrity Protection
// Run: node tests/test_state_integrity_guard.js

const { v4: uuidv4 } = require('uuid');
const gsm = require('../state/gameStateManager');
const {
  validateState,
  validateTransition,
  validateEvent,
  guardedApply
} = require('../state/stateIntegrityGuard');

let passed = 0;
let failed = 0;

function expect(label, condition) {
  if (condition) { console.log(`  ✅ ${label}`); passed++; }
  else           { console.log(`  ❌ ${label}`); failed++; }
}

function makeEvent(type, overrides = {}) {
  return {
    event_type:      type,
    event_id:        uuidv4(),
    timestamp:       Date.now(),
    game_session_id: 'test',
    entities:        [],
    context:         {},
    metadata:        {},
    ...overrides
  };
}

// ─── Test 1: validateState — valid state ──────────────────────────────────────
console.log('\n=== Test 1: validateState — valid state ===');
{
  const sid = `ig_t1_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const state = gsm.getCurrentState(sid);
  const r = validateState(state);
  expect('valid runner state passes', r.valid);
  expect('no violations', r.violations.length === 0);
}

// ─── Test 2: validateState — corrupted fields ─────────────────────────────────
console.log('\n=== Test 2: validateState — corrupted fields ===');
{
  const bad = {
    session_id: '',
    game_mode:  'unknown_mode',
    status:     'flying',
    player:     { health: -5, score: -1, lives: -1, position: [0, 0], is_alive: true },
    entities:   { enemy_count: -1, obstacle_count: 0, collectible_count: 0, active_entities: {} },
    world:      { level: 0, time_elapsed: -1 },
    meta:       { event_count: -1, snapshot_version: 0, created_at: 1000, last_updated_at: 500 }
  };
  const r = validateState(bad);
  expect('corrupted state fails', !r.valid);
  expect('detects bad session_id',  r.violations.some(v => v.includes('session_id')));
  expect('detects bad game_mode',   r.violations.some(v => v.includes('game_mode')));
  expect('detects bad status',      r.violations.some(v => v.includes('status')));
  expect('detects negative health', r.violations.some(v => v.includes('player.health')));
  expect('detects negative score',  r.violations.some(v => v.includes('player.score')));
  expect('detects level < 1',       r.violations.some(v => v.includes('world.level')));
  expect('detects clock corruption',r.violations.some(v => v.includes('last_updated_at is before')));
}

// ─── Test 3: validateState — health > max_health ──────────────────────────────
console.log('\n=== Test 3: validateState — health exceeds max_health ===');
{
  const sid = `ig_t3_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).player.health = 999; // corrupt it
  const state = gsm.getCurrentState(sid);
  const r = validateState(state);
  expect('health > max_health detected', r.violations.some(v => v.includes('exceeds max_health')));
}

// ─── Test 4: validateState — health=0 but is_alive=true ──────────────────────
console.log('\n=== Test 4: validateState — health=0 but is_alive=true ===');
{
  const sid = `ig_t4_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  const s = _sessions.get(sid);
  s.player.health   = 0;
  s.player.is_alive = true; // inconsistent
  const r = validateState(gsm.getCurrentState(sid));
  expect('health=0 + is_alive=true detected', r.violations.some(v => v.includes('is_alive is true')));
}

// ─── Test 5: validateTransition — valid transition ────────────────────────────
console.log('\n=== Test 5: validateTransition — valid transition ===');
{
  const sid = `ig_t5_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'running';
  const before = gsm.getCurrentState(sid);
  const event  = makeEvent('score_update', { context: { score_delta: 10 } });
  gsm.applyEventToState(sid, event);
  const after  = gsm.getCurrentState(sid);
  const r = validateTransition(before, event, after);
  expect('valid score_update transition passes', r.valid);
  expect('no violations', r.violations.length === 0);
}

// ─── Test 6: validateTransition — illegal status jump ────────────────────────
console.log('\n=== Test 6: validateTransition — illegal status jump ===');
{
  const sid = `ig_t6_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'running';
  const before = gsm.getCurrentState(sid);
  // Manually corrupt after-state to simulate illegal jump
  const fakeAfter = JSON.parse(JSON.stringify(before));
  fakeAfter.status = 'initializing'; // running → initializing is illegal
  fakeAfter.meta.event_count++;
  fakeAfter.meta.last_updated_at = Date.now();
  const r = validateTransition(before, makeEvent('game_start'), fakeAfter);
  expect('illegal status transition detected', r.violations.some(v => v.includes('Invalid status transition')));
}

// ─── Test 7: validateTransition — score decrease ─────────────────────────────
console.log('\n=== Test 7: validateTransition — score decrease ===');
{
  const sid = `ig_t7_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  const s = _sessions.get(sid);
  s.status = 'running'; s.player.score = 100;
  const before = gsm.getCurrentState(sid);
  const fakeAfter = JSON.parse(JSON.stringify(before));
  fakeAfter.player.score = 50; // score went down
  fakeAfter.meta.event_count++;
  fakeAfter.meta.last_updated_at = Date.now();
  const r = validateTransition(before, makeEvent('score_update'), fakeAfter);
  expect('score decrease detected', r.violations.some(v => v.includes('score decreased')));
}

// ─── Test 8: validateEvent — event on terminal session ───────────────────────
console.log('\n=== Test 8: validateEvent — event on terminal session ===');
{
  const sid = `ig_t8_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'game_over';
  const state = gsm.getCurrentState(sid);
  const r = validateEvent(makeEvent('score_update'), state);
  expect('event on game_over session rejected', !r.valid);
  expect('terminal violation message present', r.violations.some(v => v.includes('terminal')));
}

// ─── Test 9: validateEvent — event on dead player ────────────────────────────
console.log('\n=== Test 9: validateEvent — event requires alive player ===');
{
  const sid = `ig_t9_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  const s = _sessions.get(sid);
  s.status = 'running'; s.player.is_alive = false;
  const state = gsm.getCurrentState(sid);
  const r = validateEvent(makeEvent('health_changed', { context: { delta: -1 } }), state);
  expect('health_changed on dead player rejected', !r.valid);
  expect('not alive violation present', r.violations.some(v => v.includes('not alive')));
}

// ─── Test 10: validateEvent — entity_destroyed for unknown entity ─────────────
console.log('\n=== Test 10: validateEvent — entity_destroyed unknown entity ===');
{
  const sid = `ig_t10_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'arena_v1', defaults: { player_health: 100 } }, {});
  const { _sessions } = gsm.__internals();
  const s = _sessions.get(sid);
  s.status = 'running';
  s.entities.active_entities['enemy_001'] = 'enemy'; // only this one exists
  const state = gsm.getCurrentState(sid);
  const r = validateEvent(
    makeEvent('entity_destroyed', { entities: ['enemy_999'] }), // unknown ID
    state
  );
  expect('unknown entity_destroyed rejected', !r.valid);
  expect('unknown entity violation present', r.violations.some(v => v.includes('unknown entity')));
}

// ─── Test 11: validateEvent — negative score_delta ───────────────────────────
console.log('\n=== Test 11: validateEvent — negative score_delta ===');
{
  const sid = `ig_t11_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'running';
  const state = gsm.getCurrentState(sid);
  const r = validateEvent(
    makeEvent('score_update', { context: { score_delta: -50 } }),
    state
  );
  expect('negative score_delta rejected', !r.valid);
  expect('score_delta violation present', r.violations.some(v => v.includes('score_delta')));
}

// ─── Test 12: guardedApply — valid event passes through ──────────────────────
console.log('\n=== Test 12: guardedApply — valid event passes through ===');
{
  const sid = `ig_t12_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'running';
  const state = gsm.getCurrentState(sid);
  const event = makeEvent('score_update', { context: { score_delta: 100 } });
  const r = guardedApply(state, event, () => gsm.applyEventToState(sid, event));
  expect('guardedApply succeeds', r.success);
  expect('no violations', r.violations.length === 0);
  expect('score updated', gsm.getCurrentState(sid).player.score === 100);
}

// ─── Test 13: guardedApply — invalid event is blocked ────────────────────────
console.log('\n=== Test 13: guardedApply — invalid event is blocked ===');
{
  const sid = `ig_t13_${Date.now()}`;
  gsm.createGameState(sid, { template_id: 'runner_v1', defaults: { player_health: 3 } }, {});
  const { _sessions } = gsm.__internals();
  _sessions.get(sid).status = 'game_over';
  const state = gsm.getCurrentState(sid);
  const event = makeEvent('score_update', { context: { score_delta: 100 } });
  const r = guardedApply(state, event, () => gsm.applyEventToState(sid, event));
  expect('guardedApply blocks invalid event', !r.success);
  expect('blocked flag set', r.blocked === true);
  expect('score unchanged', gsm.getCurrentState(sid).player.score === 0);
}

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(50)}`);
console.log(`Results: ${passed}/${passed + failed} tests passed`);
if (failed === 0) {
  console.log('✅ Phase 9 complete — all integrity checks verified');
} else {
  console.log('❌ Some tests failed');
  process.exit(1);
}

'use strict';

/**
 * test_phase4_trace_continuity.js
 *
 * Phase 4 — Trace Continuity Lock
 *
 * Verifies trace_id is:
 *   - present on every stream:tick
 *   - present on every replay stream:tick
 *   - present on stream:done (live)
 *   - present on stream:done (replay)
 *   - present on stream:error payloads
 *   - never regenerated (same value end-to-end)
 *   - originates from the caller (upstream authority)
 *
 * Run:
 *   cd backend
 *   node test_phase4_trace_continuity.js
 */

const { io } = require('socket.io-client');

const SERVER_URL = 'http://localhost:3000';
const NAMESPACE  = '/simulate/stream';
const TRACE_ID   = 'p4-trace-continuity-' + Date.now();
const TICKS      = 5;

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

function makeContract(trace_id) {
  return {
    trace_id,
    execution_id: 'exec-p4-' + Date.now(),
    domain:       'maritime',
    scenario:     'patrol_route',
    ticks:        TICKS,
    entities: [
      { id: 'ship_1', type: 'vessel', position: [0,0,0], behaviors: ['pb'], state: 'active' }
    ],
    behaviors: [
      { id: 'pb', script: 'patrol', params: { waypoints: [[0,0,0],[5,0,0]], speed: 1.0 } }
    ]
  };
}

async function main() {
  console.log('\n[PHASE 4 TRACE CONTINUITY TEST]');
  console.log(`trace_id (upstream): ${TRACE_ID}\n`);

  const socket = io(`${SERVER_URL}${NAMESPACE}`, {
    transports: ['websocket'],
    reconnection: false
  });

  await new Promise((resolve, reject) => {
    socket.on('connect', resolve);
    socket.on('connect_error', (err) => {
      console.error(`[FATAL] Cannot connect: ${err.message}`);
      process.exit(1);
    });
  });

  info(`Connected — socket.id=${socket.id}\n`);

  // ── A: Live stream — trace_id on every tick and done ─────────────────────
  console.log('── A: Live stream trace continuity ──────────────────');

  const { live_ticks, live_done } = await new Promise((resolve, reject) => {
    const ticks = [];
    socket.emit('stream:start', { contract: makeContract(TRACE_ID) });
    socket.on('stream:tick',  (d) => ticks.push(d));
    socket.on('stream:done',  (s) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      resolve({ live_ticks: ticks, live_done: s });
    });
    socket.on('stream:error', (e) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      reject(new Error(`stream:error — ${e.code}: ${e.reason}`));
    });
  });

  // Every tick must carry the exact trace_id
  const live_tick_trace_ok = live_ticks.every(t => t.trace_id === TRACE_ID);
  if (live_tick_trace_ok) pass(`all ${live_ticks.length} live ticks carry trace_id="${TRACE_ID}"`);
  else {
    const bad = live_ticks.filter(t => t.trace_id !== TRACE_ID);
    fail(`${bad.length} live ticks have wrong trace_id`);
  }

  // stream:done must carry trace_id
  if (live_done.trace_id === TRACE_ID) pass(`stream:done (live) carries trace_id`);
  else                                   fail(`stream:done (live) trace_id="${live_done.trace_id}" expected "${TRACE_ID}"`);

  // trace_id must not be null or empty on any tick
  const no_nulls = live_ticks.every(t => t.trace_id && typeof t.trace_id === 'string');
  if (no_nulls) pass(`no null/empty trace_id on any live tick`);
  else          fail(`some live ticks have null/empty trace_id`);

  // ── B: Replay stream — same trace_id throughout ───────────────────────────
  console.log('\n── B: Replay stream trace continuity ────────────────');

  const { replay_ticks, replay_done } = await new Promise((resolve, reject) => {
    const ticks = [];
    socket.emit('replay:start', { trace_id: TRACE_ID });
    socket.on('stream:tick',  (d) => ticks.push(d));
    socket.on('stream:done',  (s) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      resolve({ replay_ticks: ticks, replay_done: s });
    });
    socket.on('stream:error', (e) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      reject(new Error(`replay stream:error — ${e.code}: ${e.reason}`));
    });
  });

  const replay_tick_trace_ok = replay_ticks.every(t => t.trace_id === TRACE_ID);
  if (replay_tick_trace_ok) pass(`all ${replay_ticks.length} replay ticks carry trace_id="${TRACE_ID}"`);
  else {
    const bad = replay_ticks.filter(t => t.trace_id !== TRACE_ID);
    fail(`${bad.length} replay ticks have wrong trace_id`);
  }

  if (replay_done.trace_id === TRACE_ID) pass(`stream:done (replay) carries trace_id`);
  else                                    fail(`stream:done (replay) trace_id="${replay_done.trace_id}" expected "${TRACE_ID}"`);

  // ── C: stream:error carries trace_id ─────────────────────────────────────
  console.log('\n── C: stream:error trace continuity ─────────────────');

  await new Promise((resolve) => {
    // Trigger MISSING_TRACE_ID error by sending replay:start with no trace_id
    socket.emit('replay:start', {});
    socket.once('stream:error', (err) => {
      // trace_id may be null here (no trace known) — that's acceptable for MISSING_TRACE_ID
      // What matters: the field EXISTS in the payload
      if ('trace_id' in err) pass(`stream:error payload contains trace_id field (value="${err.trace_id}")`);
      else                    fail(`stream:error payload missing trace_id field entirely`);

      if (err.code === 'MISSING_TRACE_ID') pass(`stream:error code=MISSING_TRACE_ID as expected`);
      else                                  fail(`unexpected error code: ${err.code}`);
      resolve();
    });
  });

  // Trigger INVALID_CONTRACT error — trace_id should be null (no contract provided)
  await new Promise((resolve) => {
    socket.emit('stream:start', { contract: { trace_id: 'bad', execution_id: 'x' } });
    socket.once('stream:error', (err) => {
      if ('trace_id' in err) pass(`stream:error (INVALID_CONTRACT) contains trace_id field`);
      else                    fail(`stream:error (INVALID_CONTRACT) missing trace_id field`);
      resolve();
    });
  });

  // ── D: trace_id never regenerated — live vs replay match exactly ──────────
  console.log('\n── D: trace_id never regenerated ────────────────────');

  const live_ids    = live_ticks.map(t => t.trace_id);
  const replay_ids  = replay_ticks.map(t => t.trace_id);
  const all_same    = [...live_ids, ...replay_ids].every(id => id === TRACE_ID);

  if (all_same) pass(`trace_id="${TRACE_ID}" unchanged across all ${live_ids.length + replay_ids.length} payloads (live + replay)`);
  else          fail(`trace_id was mutated somewhere`);

  _finish(socket);
}

function _finish(socket) {
  console.log('\n' + '─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 4 trace continuity test PASSED\n');
  } else {
    console.log('✗ Phase 4 trace continuity test FAILED\n');
  }
  socket.disconnect();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

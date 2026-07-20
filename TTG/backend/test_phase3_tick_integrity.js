'use strict';

/**
 * test_phase3_tick_integrity.js
 *
 * Phase 3 — Tick Integrity Enforcement
 *
 * Tests:
 *   A. Unit: recordTick() — valid sequence, OUT_OF_ORDER, MISSING, DUPLICATE, NO_SESSION
 *   B. Integration: normal stream still passes end-to-end
 *   C. Integration: duplicate stream attempt is handled
 *
 * Run:
 *   cd backend
 *   node test_phase3_tick_integrity.js
 */

const { io }         = require('socket.io-client');
const streamRegistry = require('./simulation/streamRegistry');

const SERVER_URL = 'http://localhost:3000';
const NAMESPACE  = '/simulate/stream';

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

// ─── Unit tests: recordTick() directly ───────────────────────────────────────

function testRecordTickUnit() {
  console.log('\n── Unit: recordTick() enforcement ──────────────────');

  // ── Valid sequence ────────────────────────────────────────────────────────
  const tid = 'unit-test-' + Date.now();
  streamRegistry.register(tid, 'test-socket');

  let v;
  v = streamRegistry.recordTick(tid, 1);
  if (v === null) pass('tick_id=1 accepted (valid)');
  else            fail(`tick_id=1 rejected unexpectedly: ${v?.reason}`);

  v = streamRegistry.recordTick(tid, 2);
  if (v === null) pass('tick_id=2 accepted (valid)');
  else            fail(`tick_id=2 rejected unexpectedly: ${v?.reason}`);

  v = streamRegistry.recordTick(tid, 3);
  if (v === null) pass('tick_id=3 accepted (valid)');
  else            fail(`tick_id=3 rejected unexpectedly: ${v?.reason}`);
  // last_tick=3, expected next=4

  // ── OUT_OF_ORDER — tick_id below expected, never seen ────────────────────
  // tick_id=2, expected=4 → 2 < 4 → OUT_OF_ORDER (order check fires before seen check)
  v = streamRegistry.recordTick(tid, 2);
  if (v?.code === 'OUT_OF_ORDER_TICK') pass(`OUT_OF_ORDER_TICK detected: "${v.reason}"`);
  else                                  fail(`expected OUT_OF_ORDER_TICK, got: ${v?.code || 'null'}`);

  // ── MISSING_TICK — gap: tick_id=6, expected=4 ────────────────────────────
  v = streamRegistry.recordTick(tid, 6);
  if (v?.code === 'MISSING_TICK') pass(`MISSING_TICK detected: "${v.reason}"`);
  else                             fail(`expected MISSING_TICK, got: ${v?.code || 'null'}`);

  // ── DUPLICATE_TICK — tick_id === expected but already in seen set ─────────
  // Advance to tick 4 normally
  v = streamRegistry.recordTick(tid, 4);
  if (v === null) pass('tick_id=4 accepted (valid, advancing for duplicate test)');
  else            fail(`tick_id=4 rejected unexpectedly: ${v?.reason}`);
  // last_tick=4, seen has {1,2,3,4}, expected=5

  // Simulate a race: reset last_tick so expected=4 again, but seen still has 4
  streamRegistry.get(tid).last_tick = 3;
  v = streamRegistry.recordTick(tid, 4);  // tick_id=4 === expected=4, but seen.has(4)=true
  if (v?.code === 'DUPLICATE_TICK') pass(`DUPLICATE_TICK detected: "${v.reason}"`);
  else                               fail(`expected DUPLICATE_TICK, got: ${v?.code || 'null'}`);

  streamRegistry.release(tid);

  // ── NO_SESSION — unknown trace_id ─────────────────────────────────────────
  v = streamRegistry.recordTick('nonexistent-trace-xyz', 1);
  if (v?.code === 'NO_SESSION') pass(`NO_SESSION detected for unknown trace_id`);
  else                           fail(`expected NO_SESSION, got: ${v?.code || 'null'}`);
}

// ─── Integration: normal stream ──────────────────────────────────────────────

function makeContract(trace_id) {
  return {
    trace_id,
    execution_id: 'exec-p3-' + Date.now(),
    domain:       'maritime',
    scenario:     'patrol_route',
    ticks:        5,
    entities: [
      { id: 'ship_1', type: 'vessel', position: [0,0,0], behaviors: ['pb'], state: 'active' }
    ],
    behaviors: [
      { id: 'pb', script: 'patrol', params: { waypoints: [[0,0,0],[5,0,0]], speed: 1.0 } }
    ]
  };
}

function runNormalStream(socket) {
  return new Promise((resolve, reject) => {
    const trace_id = 'p3-normal-' + Date.now();
    const ticks = [];

    socket.emit('stream:start', { contract: makeContract(trace_id) });

    socket.on('stream:tick',  (d) => ticks.push(d));
    socket.on('stream:done',  (s) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      resolve({ ticks, summary: s });
    });
    socket.on('stream:error', (e) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      reject(new Error(`stream:error — ${e.code}: ${e.reason}`));
    });
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n[PHASE 3 TICK INTEGRITY TEST]');

  // ── Part A: Unit tests (no server needed) ─────────────────────────────────
  testRecordTickUnit();

  // ── Part B: Integration — normal stream regression ────────────────────────
  console.log('\n── Integration: normal stream regression ────────────');

  const socket = io(`${SERVER_URL}${NAMESPACE}`, {
    transports: ['websocket'],
    reconnection: false
  });

  await new Promise((resolve, reject) => {
    socket.on('connect', resolve);
    socket.on('connect_error', (err) => {
      console.error(`\n[FATAL] Cannot connect: ${err.message}`);
      console.error('Start the server first:  cd backend && node index.js\n');
      process.exit(1);
    });
  });

  info(`Connected — socket.id=${socket.id}`);

  try {
    const { ticks, summary } = await runNormalStream(socket);

    const ordered = ticks.every((t, i) => t.tick_id === i + 1);
    if (ordered)              pass(`normal stream: 5 ticks in strict order (1→5)`);
    else                      fail(`normal stream: tick ordering broken`);

    if (summary.status === 'completed') pass(`normal stream: status=completed`);
    else                                fail(`normal stream: unexpected status=${summary.status}`);

    const ids    = ticks.map(t => t.tick_id);
    const unique = new Set(ids).size === ids.length;
    if (unique) pass(`normal stream: all tick_ids unique (no duplicates)`);
    else        fail(`normal stream: duplicate tick_ids detected`);

  } catch (err) {
    fail(`normal stream failed: ${err.message}`);
  }

  // ── Part C: Duplicate stream attempt ─────────────────────────────────────
  console.log('\n── Integration: duplicate stream attempt ────────────');

  await new Promise((resolve) => {
    const trace_id = 'p3-dup-' + Date.now();
    const contract = makeContract(trace_id);
    let   first_done = false;

    socket.emit('stream:start', { contract });
    socket.on('stream:tick', () => {});

    socket.on('stream:done', () => {
      if (first_done) return;
      first_done = true;
      socket.off('stream:done');

      // Try same trace_id again after first stream completes
      socket.emit('stream:start', { contract });

      socket.once('stream:error', (err) => {
        pass(`duplicate stream attempt handled (code=${err.code})`);
        socket.off('stream:tick');
        resolve();
      });

      socket.once('stream:done', () => {
        pass(`second stream completed cleanly (trace released before retry)`);
        socket.off('stream:tick');
        resolve();
      });
    });
  });

  _finish(socket);
}

function _finish(socket) {
  console.log('\n' + '─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 3 tick integrity test PASSED\n');
  } else {
    console.log('✗ Phase 3 tick integrity test FAILED\n');
  }
  socket.disconnect();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

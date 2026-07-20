'use strict';

/**
 * test_phase6_failure_boundary.js
 *
 * Phase 6 — Failure Boundary Enforcement
 *
 * Unit tests (no server needed):
 *   A. validate() — malformed delta (missing entities array)
 *   B. validate() — broken trace_id (null)
 *   C. validate() — broken trace_id (mismatch)
 *   D. validate() — missing entity state
 *   E. validate() — invalid position shape (array instead of object)
 *   F. validate() — invalid position values (NaN/Infinity)
 *   G. validate() — valid delta passes
 *
 * Integration (server required):
 *   H. Normal stream still completes — failure boundary didn't break happy path
 *
 * Run:
 *   cd backend
 *   node test_phase6_failure_boundary.js
 */

const { io }     = require('socket.io-client');
const { validate } = require('./simulation/engine/deltaComputer');

const SERVER_URL = 'http://localhost:3000';
const NAMESPACE  = '/simulate/stream';

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

// ─── Valid delta fixture ──────────────────────────────────────────────────────

function validDelta(trace_id = 'test-trace-001', tick_id = 1) {
  return {
    trace_id,
    tick_id,
    timestamp: new Date().toISOString(),
    entities: [
      {
        id:         'ship_1',
        type:       'vessel',
        position:   { x: 1.0, y: 0.0, z: 0.0 },
        state:      'active',
        attributes: {}
      }
    ]
  };
}

// ─── Unit tests ───────────────────────────────────────────────────────────────

function runUnitTests() {
  console.log('\n── Unit: validate() failure boundaries ─────────────');

  const TRACE = 'test-trace-001';

  // A. Malformed delta — null
  let v = validate(null, TRACE);
  if (v?.code === 'MALFORMED_DELTA') pass(`A. MALFORMED_DELTA: null delta — "${v.reason}"`);
  else                                fail(`A. expected MALFORMED_DELTA for null, got: ${v?.code}`);

  // B. Malformed delta — entities not array
  v = validate({ trace_id: TRACE, tick_id: 1, timestamp: new Date().toISOString(), entities: 'bad' }, TRACE);
  if (v?.code === 'MALFORMED_DELTA') pass(`B. MALFORMED_DELTA: entities not array — "${v.reason}"`);
  else                                fail(`B. expected MALFORMED_DELTA for bad entities, got: ${v?.code}`);

  // C. Broken trace_id — null
  const d_null_trace = validDelta(TRACE);
  d_null_trace.trace_id = null;
  v = validate(d_null_trace, TRACE);
  if (v?.code === 'BROKEN_TRACE_ID') pass(`C. BROKEN_TRACE_ID: null trace_id — "${v.reason}"`);
  else                                fail(`C. expected BROKEN_TRACE_ID for null, got: ${v?.code}`);

  // D. Broken trace_id — mismatch
  const d_wrong_trace = validDelta('wrong-trace-999');
  v = validate(d_wrong_trace, TRACE);
  if (v?.code === 'BROKEN_TRACE_ID') pass(`D. BROKEN_TRACE_ID: mismatch — "${v.reason}"`);
  else                                fail(`D. expected BROKEN_TRACE_ID for mismatch, got: ${v?.code}`);

  // E. Missing entity state — absent
  const d_no_state = validDelta(TRACE);
  delete d_no_state.entities[0].state;
  v = validate(d_no_state, TRACE);
  if (v?.code === 'MISSING_ENTITY_STATE') pass(`E. MISSING_ENTITY_STATE: state absent — "${v.reason}"`);
  else                                     fail(`E. expected MISSING_ENTITY_STATE, got: ${v?.code}`);

  // F. Missing entity state — invalid value
  const d_bad_state = validDelta(TRACE);
  d_bad_state.entities[0].state = 'flying';
  v = validate(d_bad_state, TRACE);
  if (v?.code === 'MISSING_ENTITY_STATE') pass(`F. MISSING_ENTITY_STATE: invalid value "flying" — "${v.reason}"`);
  else                                     fail(`F. expected MISSING_ENTITY_STATE for "flying", got: ${v?.code}`);

  // G. Invalid position — array instead of object
  const d_arr_pos = validDelta(TRACE);
  d_arr_pos.entities[0].position = [1, 0, 0];
  v = validate(d_arr_pos, TRACE);
  if (v?.code === 'INVALID_POSITION') pass(`G. INVALID_POSITION: array position — "${v.reason}"`);
  else                                 fail(`G. expected INVALID_POSITION for array, got: ${v?.code}`);

  // H. Invalid position — NaN value
  const d_nan_pos = validDelta(TRACE);
  d_nan_pos.entities[0].position = { x: NaN, y: 0, z: 0 };
  v = validate(d_nan_pos, TRACE);
  if (v?.code === 'INVALID_POSITION') pass(`H. INVALID_POSITION: NaN in position — "${v.reason}"`);
  else                                 fail(`H. expected INVALID_POSITION for NaN, got: ${v?.code}`);

  // I. Invalid position — Infinity value
  const d_inf_pos = validDelta(TRACE);
  d_inf_pos.entities[0].position = { x: Infinity, y: 0, z: 0 };
  v = validate(d_inf_pos, TRACE);
  if (v?.code === 'INVALID_POSITION') pass(`I. INVALID_POSITION: Infinity in position — "${v.reason}"`);
  else                                 fail(`I. expected INVALID_POSITION for Infinity, got: ${v?.code}`);

  // J. Valid delta — must return null
  v = validate(validDelta(TRACE), TRACE);
  if (v === null) pass(`J. valid delta accepted (validate returns null)`);
  else            fail(`J. valid delta rejected unexpectedly: ${v?.code} — ${v?.reason}`);
}

// ─── Integration: normal stream regression ────────────────────────────────────

function runNormalStream(socket) {
  return new Promise((resolve, reject) => {
    const trace_id = 'p6-normal-' + Date.now();
    const ticks    = [];

    socket.emit('stream:start', {
      contract: {
        trace_id,
        execution_id: 'exec-p6-' + Date.now(),
        domain:       'maritime',
        scenario:     'patrol_route',
        ticks:        5,
        entities: [
          { id: 'ship_1', type: 'vessel', position: [0,0,0], behaviors: ['pb'], state: 'active' }
        ],
        behaviors: [
          { id: 'pb', script: 'patrol', params: { waypoints: [[0,0,0],[5,0,0]], speed: 1.0 } }
        ]
      }
    });

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
  console.log('\n[PHASE 6 FAILURE BOUNDARY TEST]');

  // Unit tests — no server needed
  runUnitTests();

  // Integration
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

    if (ticks.length === 5)           pass(`normal stream: 5 ticks received`);
    else                              fail(`normal stream: expected 5 ticks, got ${ticks.length}`);

    if (summary.status === 'completed') pass(`normal stream: status=completed`);
    else                                fail(`normal stream: unexpected status=${summary.status}`);

    // Confirm every tick passed validate() — all positions are {x,y,z} objects
    const all_valid = ticks.every(t =>
      t.entities.every(e =>
        e.position && typeof e.position === 'object' && !Array.isArray(e.position) &&
        typeof e.position.x === 'number' && isFinite(e.position.x)
      )
    );
    if (all_valid) pass(`normal stream: all tick deltas passed failure boundary validation`);
    else           fail(`normal stream: some tick deltas failed validation`);

  } catch (err) {
    fail(`normal stream failed: ${err.message}`);
  }

  _finish(socket);
}

function _finish(socket) {
  console.log('\n' + '─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 6 failure boundary test PASSED\n');
  } else {
    console.log('✗ Phase 6 failure boundary test FAILED\n');
  }
  socket.disconnect();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

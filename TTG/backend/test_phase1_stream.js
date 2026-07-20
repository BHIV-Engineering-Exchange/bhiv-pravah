'use strict';

/**
 * test_phase1_stream.js
 *
 * Tests the Phase 1 delta stream endpoint.
 *
 * What it checks:
 *   1. Connection to /simulate/stream namespace succeeds
 *   2. stream:tick payloads arrive in strict tick_id order (1, 2, 3 ...)
 *   3. Every tick payload has: trace_id, tick_id, timestamp, entities[]
 *   4. trace_id on every tick matches the one sent in the contract
 *   5. position shape is { x, y, z } — not an array
 *   6. stream:done arrives after all ticks
 *   7. stream:error is NOT received
 *
 * Run:
 *   cd backend
 *   node test_phase1_stream.js
 *
 * Server must be running on port 3000 first:
 *   node index.js
 */

const { io } = require('socket.io-client');

const SERVER_URL = 'http://localhost:3000';
const NAMESPACE  = '/simulate/stream';
const TRACE_ID   = 'phase1-test-' + Date.now();
const TICKS      = 5;

// ── Valid simulationContract.v1 payload ───────────────────────────────────────
const CONTRACT = {
  trace_id:     TRACE_ID,
  execution_id: 'exec-phase1-test-001',
  domain:       'maritime',
  scenario:     'patrol_route',
  ticks:        TICKS,
  entities: [
    {
      id:        'ship_1',
      type:      'vessel',
      position:  [0, 0, 0],
      behaviors: ['patrol_behavior'],
      state:     'active'
    },
    {
      id:        'ship_2',
      type:      'vessel',
      position:  [10, 0, 0],
      behaviors: ['patrol_behavior'],
      state:     'active'
    }
  ],
  behaviors: [
    {
      id:     'patrol_behavior',
      script: 'patrol',
      params: {
        waypoints: [[0,0,0], [5,0,0], [10,0,0]],
        speed:     1.0
      }
    }
  ]
};

// ── Test state ────────────────────────────────────────────────────────────────
const received_ticks = [];
let   errors_received = 0;
let   passed = 0;
let   failed = 0;

function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

// ── Connect ───────────────────────────────────────────────────────────────────
console.log(`\n[PHASE 1 STREAM TEST]`);
console.log(`Server : ${SERVER_URL}${NAMESPACE}`);
console.log(`trace_id: ${TRACE_ID}`);
console.log(`ticks   : ${TICKS}\n`);

const socket = io(`${SERVER_URL}${NAMESPACE}`, {
  transports: ['websocket'],
  reconnection: false
});

socket.on('connect', () => {
  info(`Connected — socket.id=${socket.id}`);
  info(`Sending stream:start ...\n`);
  socket.emit('stream:start', { contract: CONTRACT });
});

socket.on('connect_error', (err) => {
  console.error(`\n[FATAL] Cannot connect to server: ${err.message}`);
  console.error('Make sure the backend is running:  cd backend && node index.js\n');
  process.exit(1);
});

// ── stream:tick ───────────────────────────────────────────────────────────────
socket.on('stream:tick', (payload) => {
  const tick_num = received_ticks.length + 1;
  received_ticks.push(payload);

  console.log(`[tick ${payload.tick_id}] received`);

  // 1. tick_id must be a number
  if (typeof payload.tick_id !== 'number') {
    fail(`tick_id is not a number — got: ${typeof payload.tick_id}`);
  }

  // 2. strict order — tick_id must equal position in sequence
  if (payload.tick_id !== tick_num) {
    fail(`out-of-order tick — expected tick_id=${tick_num} got tick_id=${payload.tick_id}`);
  }

  // 3. trace_id must match what we sent
  if (payload.trace_id !== TRACE_ID) {
    fail(`trace_id mismatch — expected ${TRACE_ID} got ${payload.trace_id}`);
  }

  // 4. timestamp must be ISO-8601 string
  if (typeof payload.timestamp !== 'string' || isNaN(Date.parse(payload.timestamp))) {
    fail(`timestamp is not a valid ISO-8601 string — got: ${payload.timestamp}`);
  }

  // 5. entities must be an array
  if (!Array.isArray(payload.entities)) {
    fail(`entities is not an array`);
  }

  // 6. each entity must have { x, y, z } position — not array
  for (const e of payload.entities) {
    if (typeof e.position !== 'object' || Array.isArray(e.position)) {
      fail(`entity ${e.id} position is not {x,y,z} object — got: ${JSON.stringify(e.position)}`);
    } else if (typeof e.position.x !== 'number' || typeof e.position.y !== 'number' || typeof e.position.z !== 'number') {
      fail(`entity ${e.id} position missing x/y/z numbers`);
    }
    if (!e.id)    fail(`entity missing id`);
    if (!e.type)  fail(`entity missing type`);
    if (!e.state) fail(`entity missing state`);
  }

  // Print the payload
  console.log(JSON.stringify(payload, null, 2));
  console.log('');
});

// ── stream:done ───────────────────────────────────────────────────────────────
socket.on('stream:done', (summary) => {
  console.log(`\n[stream:done]`);
  console.log(JSON.stringify(summary, null, 2));
  console.log('');

  // Validate tick count
  if (received_ticks.length === TICKS) {
    pass(`received exactly ${TICKS} ticks`);
  } else {
    fail(`expected ${TICKS} ticks, got ${received_ticks.length}`);
  }

  // Validate all tick_ids were in order
  const out_of_order = received_ticks.filter((t, i) => t.tick_id !== i + 1);
  if (out_of_order.length === 0) {
    pass(`all tick_ids in strict order (1 → ${TICKS})`);
  } else {
    fail(`${out_of_order.length} out-of-order ticks detected`);
  }

  // Validate all trace_ids match
  const wrong_trace = received_ticks.filter(t => t.trace_id !== TRACE_ID);
  if (wrong_trace.length === 0) {
    pass(`trace_id consistent across all ${TICKS} ticks`);
  } else {
    fail(`${wrong_trace.length} ticks had wrong trace_id`);
  }

  // Validate no errors received
  if (errors_received === 0) {
    pass(`no stream:error events received`);
  } else {
    fail(`received ${errors_received} stream:error events`);
  }

  // Validate summary fields
  if (summary.trace_id === TRACE_ID) {
    pass(`stream:done trace_id matches`);
  } else {
    fail(`stream:done trace_id mismatch`);
  }

  if (summary.ticks_run === TICKS) {
    pass(`stream:done ticks_run=${TICKS} correct`);
  } else {
    fail(`stream:done ticks_run expected ${TICKS} got ${summary.ticks_run}`);
  }

  if (summary.status === 'completed') {
    pass(`stream:done status=completed`);
  } else {
    fail(`stream:done status expected 'completed' got '${summary.status}'`);
  }

  _printResult();
  socket.disconnect();
});

// ── stream:error ──────────────────────────────────────────────────────────────
socket.on('stream:error', (err) => {
  errors_received++;
  console.error(`\n[stream:error] code=${err.code} reason=${err.reason}`);
  console.error(JSON.stringify(err, null, 2));

  // If error before any ticks — fatal
  if (received_ticks.length === 0) {
    fail(`stream:error received before any ticks — ${err.code}: ${err.reason}`);
    _printResult();
    socket.disconnect();
  }
});

// ── Timeout guard ─────────────────────────────────────────────────────────────
setTimeout(() => {
  if (received_ticks.length < TICKS) {
    fail(`timeout — only received ${received_ticks.length}/${TICKS} ticks`);
    _printResult();
    socket.disconnect();
    process.exit(1);
  }
}, 10000);

// ── Result summary ────────────────────────────────────────────────────────────
function _printResult() {
  console.log('─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 1 stream test PASSED\n');
  } else {
    console.log('✗ Phase 1 stream test FAILED\n');
    process.exit(1);
  }
}

'use strict';

/**
 * test_phase7_concurrency.js
 *
 * Phase 7 — Stream Performance Validation
 *
 * Tests:
 *   A. 5 simultaneous live streams — all complete, correct tick counts
 *   B. Zero cross-trace contamination — no tick from trace X in trace Y's stream
 *   C. Stable ordering — every stream has tick_ids 1→N with no gaps
 *   D. Concurrent replay under live load — replay runs while 3 live streams active
 *   E. Replay consistency — replay ticks match live ticks under concurrent load
 *
 * Run:
 *   cd backend
 *   node test_phase7_concurrency.js
 */

const { io } = require('socket.io-client');

const SERVER_URL    = 'http://localhost:3000';
const NAMESPACE     = '/simulate/stream';
const TICKS         = 8;
const STREAM_COUNT  = 5;

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeContract(trace_id, index) {
  return {
    trace_id,
    execution_id: `exec-p7-${index}-${Date.now()}`,
    domain:       'maritime',
    scenario:     'patrol_route',
    ticks:        TICKS,
    entities: [
      {
        id:        `vessel_${index}_a`,
        type:      'vessel',
        position:  [index * 5, 0, 0],
        behaviors: ['pb'],
        state:     'active'
      },
      {
        id:        `vessel_${index}_b`,
        type:      'vessel',
        position:  [index * 5 + 10, 0, 0],
        behaviors: ['pb'],
        state:     'active'
      }
    ],
    behaviors: [
      {
        id:     'pb',
        script: 'patrol',
        params: { waypoints: [[0,0,0],[5,0,0],[10,0,0]], speed: 1.0 }
      }
    ]
  };
}

// Open a fresh socket connection
function openSocket() {
  return new Promise((resolve, reject) => {
    const socket = io(`${SERVER_URL}${NAMESPACE}`, {
      transports: ['websocket'],
      reconnection: false
    });
    socket.on('connect', () => resolve(socket));
    socket.on('connect_error', reject);
  });
}

// Run one live stream, collect all ticks
function runLiveStream(socket, contract) {
  return new Promise((resolve, reject) => {
    const ticks = [];
    socket.emit('stream:start', { contract });
    socket.on('stream:tick',  (d) => ticks.push(d));
    socket.on('stream:done',  (s) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      resolve({ ticks, summary: s, trace_id: contract.trace_id });
    });
    socket.on('stream:error', (e) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      reject(new Error(`[${contract.trace_id}] stream:error ${e.code}: ${e.reason}`));
    });
  });
}

// Run one replay stream, collect all ticks
function runReplayStream(socket, trace_id) {
  return new Promise((resolve, reject) => {
    const ticks = [];
    socket.emit('replay:start', { trace_id });
    socket.on('stream:tick',  (d) => ticks.push(d));
    socket.on('stream:done',  (s) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      resolve({ ticks, summary: s, trace_id });
    });
    socket.on('stream:error', (e) => {
      socket.off('stream:tick'); socket.off('stream:done'); socket.off('stream:error');
      reject(new Error(`[replay:${trace_id}] stream:error ${e.code}: ${e.reason}`));
    });
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n[PHASE 7 CONCURRENCY TEST]');
  console.log(`Streams : ${STREAM_COUNT} simultaneous live + 1 concurrent replay`);
  console.log(`Ticks   : ${TICKS} per stream\n`);

  // ── Open 5 sockets simultaneously ────────────────────────────────────────
  info('Opening 5 socket connections...');
  const sockets = await Promise.all(
    Array.from({ length: STREAM_COUNT }, () => openSocket())
  );
  info(`All ${STREAM_COUNT} sockets connected\n`);

  // ── Build 5 unique trace_ids and contracts ────────────────────────────────
  const ts = Date.now();
  const trace_ids = Array.from({ length: STREAM_COUNT }, (_, i) => `p7-trace-${i}-${ts}`);
  const contracts = trace_ids.map((tid, i) => makeContract(tid, i));

  // ── A + B + C: Launch all 5 streams simultaneously ────────────────────────
  console.log('── A/B/C: 5 simultaneous live streams ───────────────');
  const start_ms = Date.now();

  const stream_results = await Promise.all(
    sockets.map((socket, i) => runLiveStream(socket, contracts[i]))
  );

  const elapsed = Date.now() - start_ms;
  info(`All 5 streams completed in ${elapsed}ms\n`);

  // A: All streams completed with correct tick count
  const all_completed = stream_results.every(r => r.summary.status === 'completed');
  if (all_completed) pass(`A. all ${STREAM_COUNT} streams completed successfully`);
  else               fail(`A. some streams did not complete`);

  const all_tick_counts = stream_results.every(r => r.ticks.length === TICKS);
  if (all_tick_counts) pass(`A. all streams received exactly ${TICKS} ticks`);
  else {
    stream_results.forEach(r => {
      if (r.ticks.length !== TICKS)
        fail(`A. trace ${r.trace_id} got ${r.ticks.length} ticks, expected ${TICKS}`);
    });
  }

  // B: Zero cross-trace contamination
  // Every tick in stream[i] must have trace_id === trace_ids[i]
  let contamination_found = false;
  for (let i = 0; i < STREAM_COUNT; i++) {
    const { ticks, trace_id } = stream_results[i];
    for (const tick of ticks) {
      if (tick.trace_id !== trace_id) {
        fail(`B. CONTAMINATION: stream[${i}] (${trace_id}) received tick with trace_id="${tick.trace_id}"`);
        contamination_found = true;
      }
    }
  }
  if (!contamination_found) pass(`B. zero cross-trace contamination across all ${STREAM_COUNT} streams`);

  // C: Stable ordering — tick_ids must be 1→TICKS in every stream
  let ordering_broken = false;
  for (let i = 0; i < STREAM_COUNT; i++) {
    const { ticks, trace_id } = stream_results[i];
    const ordered = ticks.every((t, idx) => t.tick_id === idx + 1);
    if (!ordered) {
      fail(`C. stream[${i}] (${trace_id}) has out-of-order tick_ids`);
      ordering_broken = true;
    }
  }
  if (!ordering_broken) pass(`C. stable ordering confirmed in all ${STREAM_COUNT} streams (tick_ids 1→${TICKS})`);

  // ── D + E: Concurrent replay under live load ──────────────────────────────
  console.log('\n── D/E: Concurrent replay under live load ───────────');

  // Pick trace[0] for replay — it was already stored during live run
  const replay_trace_id = trace_ids[0];
  const live_ticks_0    = stream_results[0].ticks;

  // Open 3 more sockets for concurrent live streams during replay
  info('Opening 3 more sockets for concurrent live load...');
  const load_sockets = await Promise.all([openSocket(), openSocket(), openSocket()]);
  const replay_socket = await openSocket();

  // Build 3 new contracts for concurrent live load
  const load_ts       = Date.now();
  const load_contracts = [0, 1, 2].map(i =>
    makeContract(`p7-load-${i}-${load_ts}`, i + 10)
  );

  // Launch 3 live streams + 1 replay simultaneously
  info(`Launching 3 live streams + replay of ${replay_trace_id} simultaneously...`);
  const concurrent_start = Date.now();

  const [replay_result, ...load_results] = await Promise.all([
    runReplayStream(replay_socket, replay_trace_id),
    ...load_sockets.map((s, i) => runLiveStream(s, load_contracts[i]))
  ]);

  const concurrent_elapsed = Date.now() - concurrent_start;
  info(`Concurrent phase completed in ${concurrent_elapsed}ms\n`);

  // D: Replay completed under concurrent load
  if (replay_result.summary.status === 'completed') {
    pass(`D. replay completed under concurrent live load (${concurrent_elapsed}ms)`);
  } else {
    fail(`D. replay failed under load: ${replay_result.summary.status}`);
  }

  if (replay_result.ticks.length === TICKS) {
    pass(`D. replay received all ${TICKS} ticks under load`);
  } else {
    fail(`D. replay got ${replay_result.ticks.length} ticks, expected ${TICKS}`);
  }

  // Concurrent live streams also completed
  const load_ok = load_results.every(r => r.summary.status === 'completed');
  if (load_ok) pass(`D. all 3 concurrent live streams completed alongside replay`);
  else         fail(`D. some concurrent live streams failed`);

  // E: Replay consistency — replay ticks match original live ticks
  let replay_consistent = true;
  for (let i = 0; i < live_ticks_0.length; i++) {
    const live    = live_ticks_0[i];
    const replayed = replay_result.ticks[i];

    if (!replayed) {
      fail(`E. replay missing tick at index ${i}`);
      replay_consistent = false;
      break;
    }

    if (live.tick_id !== replayed.tick_id) {
      fail(`E. tick[${i}] tick_id mismatch: live=${live.tick_id} replay=${replayed.tick_id}`);
      replay_consistent = false;
    }

    if (live.trace_id !== replayed.trace_id) {
      fail(`E. tick[${i}] trace_id mismatch under load`);
      replay_consistent = false;
    }

    // Compare entity positions
    const live_sorted    = [...live.entities].sort((a, b) => a.id < b.id ? -1 : 1);
    const replay_sorted  = [...replayed.entities].sort((a, b) => a.id < b.id ? -1 : 1);

    for (let j = 0; j < live_sorted.length; j++) {
      const le = live_sorted[j];
      const re = replay_sorted[j];
      if (!re || le.id !== re.id ||
          le.position.x !== re.position.x ||
          le.position.y !== re.position.y ||
          le.position.z !== re.position.z) {
        fail(`E. tick[${i}] entity position mismatch under concurrent load`);
        replay_consistent = false;
      }
    }
  }
  if (replay_consistent) pass(`E. replay consistent with live under concurrent load — all ${TICKS} ticks match`);

  // Replay has no contamination from concurrent live streams
  const replay_contaminated = replay_result.ticks.some(t => t.trace_id !== replay_trace_id);
  if (!replay_contaminated) pass(`E. replay stream has zero contamination from concurrent live streams`);
  else                       fail(`E. replay stream contaminated by concurrent live streams`);

  // ── Cleanup ───────────────────────────────────────────────────────────────
  [...sockets, ...load_sockets, replay_socket].forEach(s => s.disconnect());

  _finish();
}

function _finish() {
  console.log('\n' + '─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 7 concurrency test PASSED\n');
  } else {
    console.log('✗ Phase 7 concurrency test FAILED\n');
  }
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

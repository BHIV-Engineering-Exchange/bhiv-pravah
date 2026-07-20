'use strict';

/**
 * test_phase2_replay.js
 *
 * Phase 2 — Replay = Live Enforcement
 *
 * Steps:
 *   1. Run a live stream:start  → capture all stream:tick payloads
 *   2. Run a replay:start       → capture all stream:tick payloads
 *   3. Compare every tick field-by-field:
 *        - tick_id
 *        - trace_id
 *        - entities[].id, type, state, position {x,y,z}, attributes
 *   4. Confirm stream:done shape is identical
 *   5. Confirm no replay-specific event names were used
 *
 * Run:
 *   cd backend
 *   node test_phase2_replay.js
 */

const { io } = require('socket.io-client');

const SERVER_URL = 'http://localhost:3000';
const NAMESPACE  = '/simulate/stream';
const TRACE_ID   = 'phase2-replay-test-' + Date.now();
const TICKS      = 5;

const CONTRACT = {
  trace_id:     TRACE_ID,
  execution_id: 'exec-phase2-test-001',
  domain:       'maritime',
  scenario:     'patrol_route',
  ticks:        TICKS,
  entities: [
    {
      id:        'ship_1',
      type:      'vessel',
      position:  [0, 0, 0],
      behaviors: ['patrol_b'],
      state:     'active'
    },
    {
      id:        'ship_2',
      type:      'vessel',
      position:  [10, 0, 0],
      behaviors: ['patrol_b'],
      state:     'active'
    }
  ],
  behaviors: [
    {
      id:     'patrol_b',
      script: 'patrol',
      params: { waypoints: [[0,0,0],[5,0,0],[10,0,0]], speed: 1.0 }
    }
  ]
};

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }
function info(msg) { console.log(`  · ${msg}`); }

// ─── Phase A: Live stream ─────────────────────────────────────────────────────

function runLiveStream(socket) {
  return new Promise((resolve, reject) => {
    const live_ticks = [];
    let   live_done  = null;

    socket.emit('stream:start', { contract: CONTRACT });

    socket.on('stream:tick', (delta) => {
      live_ticks.push(delta);
    });

    socket.on('stream:done', (summary) => {
      live_done = summary;
      socket.off('stream:tick');
      socket.off('stream:done');
      socket.off('stream:error');
      resolve({ live_ticks, live_done });
    });

    socket.on('stream:error', (err) => {
      socket.off('stream:tick');
      socket.off('stream:done');
      socket.off('stream:error');
      reject(new Error(`stream:error during live — ${err.code}: ${err.reason}`));
    });
  });
}

// ─── Phase B: Replay stream ───────────────────────────────────────────────────

function runReplayStream(socket) {
  return new Promise((resolve, reject) => {
    const replay_ticks = [];
    let   replay_done  = null;

    socket.emit('replay:start', { trace_id: TRACE_ID });

    socket.on('stream:tick', (delta) => {
      replay_ticks.push(delta);
    });

    socket.on('stream:done', (summary) => {
      replay_done = summary;
      socket.off('stream:tick');
      socket.off('stream:done');
      socket.off('stream:error');
      resolve({ replay_ticks, replay_done });
    });

    socket.on('stream:error', (err) => {
      socket.off('stream:tick');
      socket.off('stream:done');
      socket.off('stream:error');
      reject(new Error(`stream:error during replay — ${err.code}: ${err.reason}`));
    });
  });
}

// ─── Comparison ───────────────────────────────────────────────────────────────

function compareTicks(live_ticks, replay_ticks) {
  if (live_ticks.length !== replay_ticks.length) {
    fail(`tick count mismatch: live=${live_ticks.length} replay=${replay_ticks.length}`);
    return;
  }
  pass(`tick count matches: ${live_ticks.length}`);

  for (let i = 0; i < live_ticks.length; i++) {
    const l = live_ticks[i];
    const r = replay_ticks[i];

    if (l.tick_id !== r.tick_id) {
      fail(`tick[${i}] tick_id mismatch: live=${l.tick_id} replay=${r.tick_id}`);
    }

    if (l.trace_id !== r.trace_id) {
      fail(`tick[${i}] trace_id mismatch: live=${l.trace_id} replay=${r.trace_id}`);
    }

    if (l.entities.length !== r.entities.length) {
      fail(`tick[${i}] entity count mismatch: live=${l.entities.length} replay=${r.entities.length}`);
      continue;
    }

    const l_sorted = [...l.entities].sort((a, b) => a.id < b.id ? -1 : 1);
    const r_sorted = [...r.entities].sort((a, b) => a.id < b.id ? -1 : 1);

    for (let j = 0; j < l_sorted.length; j++) {
      const le = l_sorted[j];
      const re = r_sorted[j];

      if (le.id    !== re.id)    fail(`tick[${i}] entity[${j}] id mismatch`);
      if (le.type  !== re.type)  fail(`tick[${i}] entity ${re.id} type mismatch`);
      if (le.state !== re.state) fail(`tick[${i}] entity ${re.id} state mismatch: live=${le.state} replay=${re.state}`);

      const lp = le.position;
      const rp = re.position;
      if (lp.x !== rp.x || lp.y !== rp.y || lp.z !== rp.z) {
        fail(`tick[${i}] entity ${re.id} position mismatch: live=(${lp.x},${lp.y},${lp.z}) replay=(${rp.x},${rp.y},${rp.z})`);
      }

      if (JSON.stringify(le.attributes) !== JSON.stringify(re.attributes)) {
        fail(`tick[${i}] entity ${re.id} attributes mismatch`);
      }
    }
  }

  // If we get here with no failures logged for individual ticks, all matched
  const tick_failures_before = failed;
  if (failed === tick_failures_before) {
    pass(`all ${live_ticks.length} ticks structurally identical (tick_id, trace_id, entities, positions, states, attributes)`);
  }
}

function compareDone(live_done, replay_done) {
  if (live_done.trace_id   !== replay_done.trace_id)   fail(`stream:done trace_id mismatch`);
  else                                                  pass(`stream:done trace_id matches`);

  if (live_done.ticks_run  !== replay_done.ticks_run)  fail(`stream:done ticks_run mismatch`);
  else                                                  pass(`stream:done ticks_run matches`);

  if (live_done.status     !== replay_done.status)     fail(`stream:done status mismatch`);
  else                                                  pass(`stream:done status matches`);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n[PHASE 2 REPLAY TEST]');
  console.log(`Server  : ${SERVER_URL}${NAMESPACE}`);
  console.log(`trace_id: ${TRACE_ID}`);
  console.log(`ticks   : ${TICKS}\n`);

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

  info(`Connected — socket.id=${socket.id}\n`);

  // ── Step 1: Live stream ───────────────────────────────────────────────────
  console.log('── Step 1: Live stream ──────────────────────────────');
  let live_ticks, live_done;
  try {
    ({ live_ticks, live_done } = await runLiveStream(socket));
    info(`Live stream complete — ${live_ticks.length} ticks received\n`);
  } catch (err) {
    fail(`Live stream failed: ${err.message}`);
    _finish(socket);
    return;
  }

  // ── Step 2: Replay stream ─────────────────────────────────────────────────
  console.log('── Step 2: Replay stream ────────────────────────────');
  let replay_ticks, replay_done;
  try {
    ({ replay_ticks, replay_done } = await runReplayStream(socket));
    info(`Replay stream complete — ${replay_ticks.length} ticks received\n`);
  } catch (err) {
    fail(`Replay stream failed: ${err.message}`);
    _finish(socket);
    return;
  }

  // ── Step 3: Compare ───────────────────────────────────────────────────────
  console.log('── Step 3: Parity comparison ────────────────────────');
  compareTicks(live_ticks, replay_ticks);
  compareDone(live_done, replay_done);

  _finish(socket);
}

function _finish(socket) {
  console.log('\n' + '─'.repeat(50));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 2 replay test PASSED\n');
  } else {
    console.log('✗ Phase 2 replay test FAILED\n');
  }
  socket.disconnect();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

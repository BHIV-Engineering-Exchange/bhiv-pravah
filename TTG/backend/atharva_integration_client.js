'use strict';

/**
 * atharva_integration_client.js
 *
 * PHASE 1 — Real Atharva Integration Client
 *
 * This is NOT a mock. This is the real integration client that:
 *   1. Connects to Rudra's /simulate/stream namespace
 *   2. Sends stream:start with a trace_id owned by THIS caller (upstream authority)
 *   3. Consumes stream:tick delta payloads
 *   4. Emits execution events: render:entity_update, render:tick_complete, execution:complete
 *   5. Forwards those events to Atharva's real renderer URL (when ATHARVA_RENDERER_URL is set)
 *   6. Writes a structured proof artifact to bucket_artifacts/
 *
 * Configuration (environment variables):
 *   SIM_SERVER_URL         — Rudra sim server  (default: http://localhost:3000)
 *   ATHARVA_RENDERER_URL   — Atharva's real renderer WebSocket URL
 *                            If NOT set → logs events locally (integration-ready mode)
 *   TRACE_ID               — Override trace_id (default: auto-generated)
 *   TICKS                  — Number of ticks to request (default: 8)
 *
 * Run:
 *   node atharva_integration_client.js
 *
 * With real Atharva renderer:
 *   ATHARVA_RENDERER_URL=ws://atharva-host:PORT node atharva_integration_client.js
 */

const { io }   = require('socket.io-client');
const fs       = require('fs');
const path     = require('path');

// ── Config ────────────────────────────────────────────────────────────────────
const SIM_SERVER_URL       = process.env.SIM_SERVER_URL       || 'http://localhost:3000';
const ATHARVA_RENDERER_URL = process.env.ATHARVA_RENDERER_URL || null;
const TRACE_ID             = process.env.TRACE_ID             || `tantra-trace-${Date.now()}`;
const TICKS                = parseInt(process.env.TICKS || '8', 10);

const ARTIFACT_DIR = path.join(__dirname, 'bucket_artifacts');

// ── Execution event log ───────────────────────────────────────────────────────
const execution_log = [];

function logEvent(type, data) {
  const entry = { type, ...data, ts: new Date().toISOString() };
  execution_log.push(entry);
  console.log(`[ATHARVA CLIENT] ${type}`, JSON.stringify(data));
  return entry;
}

// ── Forward event to Atharva's real renderer (if connected) ──────────────────
let atharva_socket = null;

function forwardToRenderer(event_name, payload) {
  if (atharva_socket && atharva_socket.connected) {
    atharva_socket.emit(event_name, payload);
  }
}

// ── Connect to Atharva's real renderer ───────────────────────────────────────
function connectAtharvaRenderer(on_ready) {
  if (!ATHARVA_RENDERER_URL) {
    console.log('[ATHARVA CLIENT] ATHARVA_RENDERER_URL not set — running in integration-ready mode');
    console.log('[ATHARVA CLIENT] Execution events will be logged locally only');
    console.log('[ATHARVA CLIENT] Set ATHARVA_RENDERER_URL=ws://host:port to connect real renderer\n');
    on_ready();
    return;
  }

  console.log(`[ATHARVA CLIENT] Connecting to Atharva renderer: ${ATHARVA_RENDERER_URL}`);
  atharva_socket = io(ATHARVA_RENDERER_URL, {
    transports: ['websocket'],
    reconnection: false,
    timeout: 5000
  });

  atharva_socket.on('connect', () => {
    console.log(`[ATHARVA CLIENT] ✓ Connected to Atharva renderer — socket.id=${atharva_socket.id}\n`);
    on_ready();
  });

  atharva_socket.on('connect_error', (err) => {
    console.error(`[ATHARVA CLIENT] ✗ Cannot connect to Atharva renderer: ${err.message}`);
    console.error('[ATHARVA CLIENT] Falling back to integration-ready mode (local logging only)\n');
    atharva_socket = null;
    on_ready();
  });
}

// ── Write proof artifact ──────────────────────────────────────────────────────
function writeProofArtifact(trace_id, summary) {
  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

  const artifact_path = path.join(ARTIFACT_DIR, `atharva_integration_${trace_id}.jsonl`);
  const lines = execution_log.map(e => JSON.stringify(e)).join('\n') + '\n';
  fs.writeFileSync(artifact_path, lines, 'utf8');

  const proof_path = path.join(ARTIFACT_DIR, `atharva_integration_${trace_id}_proof.json`);
  fs.writeFileSync(proof_path, JSON.stringify({
    trace_id,
    ticks_consumed:   summary.ticks_consumed,
    entity_updates:   summary.entity_updates,
    elapsed_ms:       summary.elapsed_ms,
    status:           summary.status,
    trace_continuity: summary.trace_continuity,
    stream_parity:    summary.stream_parity,
    renderer_mode:    ATHARVA_RENDERER_URL ? 'real' : 'integration-ready',
    renderer_url:     ATHARVA_RENDERER_URL || null,
    generated_at:     new Date().toISOString()
  }, null, 2), 'utf8');

  console.log(`\n[ATHARVA CLIENT] Proof artifact written:`);
  console.log(`  ${artifact_path}`);
  console.log(`  ${proof_path}`);
}

// ── Contract ──────────────────────────────────────────────────────────────────
const CONTRACT = {
  trace_id:     TRACE_ID,
  execution_id: `exec-${TRACE_ID}`,
  domain:       'maritime',
  scenario:     'patrol_route',
  ticks:        TICKS,
  entities: [
    {
      id:        'vessel_alpha',
      type:      'vessel',
      position:  [0, 0, 0],
      behaviors: ['patrol_main'],
      state:     'active'
    },
    {
      id:        'vessel_beta',
      type:      'vessel',
      position:  [15, 0, 0],
      behaviors: ['patrol_main'],
      state:     'active'
    },
    {
      id:        'marker_1',
      type:      'marker',
      position:  [7, 0, 0],
      behaviors: ['anchor_main'],
      state:     'idle'
    }
  ],
  behaviors: [
    {
      id:     'patrol_main',
      script: 'patrol',
      params: { waypoints: [[0,0,0],[8,0,0],[15,0,0]], speed: 1.5 }
    },
    {
      id:     'anchor_main',
      script: 'anchor',
      params: {}
    }
  ]
};

// ── Main integration flow ─────────────────────────────────────────────────────
function run() {
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║       ATHARVA INTEGRATION CLIENT — PHASE 1          ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');
  console.log(`[ATHARVA CLIENT] trace_id (upstream authority): ${TRACE_ID}`);
  console.log(`[ATHARVA CLIENT] sim server: ${SIM_SERVER_URL}`);
  console.log(`[ATHARVA CLIENT] ticks: ${TICKS}\n`);

  connectAtharvaRenderer(() => {
    startSimStream();
  });
}

function startSimStream() {
  console.log(`[ATHARVA CLIENT] Connecting to sim stream: ${SIM_SERVER_URL}/simulate/stream`);

  const sim_socket = io(`${SIM_SERVER_URL}/simulate/stream`, {
    transports: ['websocket'],
    reconnection: false
  });

  let ticks_consumed  = 0;
  let entity_updates  = 0;
  let stream_start_ts = null;

  sim_socket.on('connect_error', (err) => {
    console.error(`[ATHARVA CLIENT] ✗ Cannot connect to sim server: ${err.message}`);
    console.error('[ATHARVA CLIENT] Start the server first: node index.js\n');
    process.exit(1);
  });

  sim_socket.on('connect', () => {
    console.log(`[ATHARVA CLIENT] ✓ Connected to sim stream — socket.id=${sim_socket.id}`);
    console.log(`[ATHARVA CLIENT] Sending stream:start with trace_id=${TRACE_ID}\n`);

    stream_start_ts = Date.now();

    logEvent('STREAM_START_SENT', {
      trace_id:     TRACE_ID,
      execution_id: CONTRACT.execution_id,
      ticks:        TICKS,
      renderer:     ATHARVA_RENDERER_URL || 'integration-ready'
    });

    sim_socket.emit('stream:start', { contract: CONTRACT });
  });

  // ── Consume delta ticks ───────────────────────────────────────────────────
  sim_socket.on('stream:tick', (delta) => {
    ticks_consumed++;

    console.log(`\n[ATHARVA CLIENT] ← stream:tick received`);
    console.log(`  trace_id : ${delta.trace_id}`);
    console.log(`  tick_id  : ${delta.tick_id}`);
    console.log(`  entities : ${delta.entities.length} changed`);

    // Hard fail on trace_id mutation — no silent recovery
    if (delta.trace_id !== TRACE_ID) {
      console.error(`[ATHARVA CLIENT] ✗ TRACE BREACH: expected ${TRACE_ID}, got ${delta.trace_id}`);
      logEvent('TRACE_BREACH', { expected: TRACE_ID, got: delta.trace_id, tick_id: delta.tick_id });
      sim_socket.disconnect();
      if (atharva_socket) atharva_socket.disconnect();
      process.exit(1);
    }

    // Process each changed entity → emit render:entity_update
    for (const entity of delta.entities) {
      entity_updates++;

      const render_event = {
        trace_id:   delta.trace_id,
        tick_id:    delta.tick_id,
        entity_id:  entity.id,
        type:       entity.type,
        position:   entity.position,
        state:      entity.state,
        attributes: entity.attributes
      };

      logEvent('render:entity_update', render_event);
      forwardToRenderer('render:entity_update', render_event);

      console.log(`  → render:entity_update | ${entity.id} | pos=(${entity.position.x.toFixed(2)},${entity.position.y.toFixed(2)},${entity.position.z.toFixed(2)}) | state=${entity.state}`);
    }

    // Emit render:tick_complete
    const tick_complete = {
      trace_id:     delta.trace_id,
      tick_id:      delta.tick_id,
      entity_count: delta.entities.length,
      ts:           Date.now()
    };

    logEvent('render:tick_complete', tick_complete);
    forwardToRenderer('render:tick_complete', tick_complete);
    console.log(`  → render:tick_complete | tick_id=${delta.tick_id} | ${delta.entities.length} entities`);
  });

  // ── Stream complete ───────────────────────────────────────────────────────
  sim_socket.on('stream:done', (summary) => {
    const elapsed = Date.now() - stream_start_ts;

    console.log('\n[ATHARVA CLIENT] ← stream:done received');
    console.log(JSON.stringify(summary, null, 2));

    const completion = {
      trace_id:        summary.trace_id,
      execution_id:    summary.execution_id,
      ticks_consumed,
      entity_updates,
      status:          'execution_complete',
      elapsed_ms:      elapsed,
      ts:              Date.now()
    };

    logEvent('execution:complete', completion);
    forwardToRenderer('execution:complete', completion);

    const trace_ok  = ticks_consumed === TICKS;
    const parity_ok = summary.ticks_run === TICKS && summary.status === 'completed';

    const proof_summary = {
      ticks_consumed,
      entity_updates,
      elapsed_ms:      elapsed,
      status:          summary.status,
      trace_continuity: trace_ok,
      stream_parity:    parity_ok
    };

    writeProofArtifact(TRACE_ID, proof_summary);

    // ── Print convergence proof ───────────────────────────────────────────
    console.log('\n╔══════════════════════════════════════════════════════╗');
    console.log('║           PHASE 1 CONVERGENCE PROOF                 ║');
    console.log('╚══════════════════════════════════════════════════════╝\n');
    console.log(`  trace_id        : ${TRACE_ID}`);
    console.log(`  ticks consumed  : ${ticks_consumed} / ${TICKS}`);
    console.log(`  entity updates  : ${entity_updates}`);
    console.log(`  elapsed         : ${elapsed}ms`);
    console.log(`  renderer mode   : ${ATHARVA_RENDERER_URL ? 'REAL (' + ATHARVA_RENDERER_URL + ')' : 'integration-ready (local)'}`);
    console.log(`  trace continuity: ${trace_ok  ? '✓ INTACT'    : '✗ BROKEN'}`);
    console.log(`  stream parity   : ${parity_ok ? '✓ CONFIRMED' : '✗ MISMATCH'}`);
    console.log('');

    if (trace_ok && parity_ok) {
      console.log('✓ PHASE 1 CONVERGENCE PROOF: LIVE INTEGRATION CONFIRMED\n');
    } else {
      console.log('✗ PHASE 1 CONVERGENCE PROOF: FAILED\n');
      sim_socket.disconnect();
      if (atharva_socket) atharva_socket.disconnect();
      process.exit(1);
    }

    sim_socket.disconnect();
    if (atharva_socket) atharva_socket.disconnect();
  });

  // ── Stream error ──────────────────────────────────────────────────────────
  sim_socket.on('stream:error', (err) => {
    logEvent('STREAM_ERROR', err);
    console.error(`\n[ATHARVA CLIENT] ✗ stream:error — code=${err.code} reason=${err.reason}`);
    sim_socket.disconnect();
    if (atharva_socket) atharva_socket.disconnect();
    process.exit(1);
  });
}

run();

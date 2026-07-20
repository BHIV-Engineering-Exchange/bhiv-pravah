'use strict';

/**
 * test_phase1_atharva_real.js
 *
 * Phase 1 — Real Atharva Live Convergence Proof
 *
 * Connects to Atharva's REAL TTG server (Python FastAPI, port 8080).
 * Protocol: HTTP POST /execute + WebSocket /ws
 *
 * Flow:
 *   1. POST contract to http://localhost:8080/execute
 *   2. Connect WebSocket ws://localhost:8080/ws
 *   3. Receive telemetry events (contract_accepted, game_start, game_over, game_exit)
 *   4. Validate trace_id preserved in every event
 *   5. Write proof artifact to bucket_artifacts/
 *
 * Run:
 *   node test_phase1_atharva_real.js
 *
 * Atharva's server must be running:
 *   cd "d:\Internship Task\ttg (1)\ttg"
 *   uvicorn server:app --host 0.0.0.0 --port 8080
 */

const http      = require('http');
const WebSocket = require('ws');
const fs        = require('fs');
const path      = require('path');

const ATHARVA_HOST    = process.env.ATHARVA_HOST || 'localhost';
const ATHARVA_PORT    = parseInt(process.env.ATHARVA_PORT || '8080', 10);
const TRACE_ID        = process.env.TRACE_ID || `tantra-p1-${Date.now()}`;
const EXECUTION_ID    = `exec-${TRACE_ID}`;
const TIMEOUT_MS      = parseInt(process.env.TIMEOUT_MS || '8000', 10);
const ARTIFACT_DIR    = path.join(__dirname, 'bucket_artifacts');

// ── Proof log ─────────────────────────────────────────────────────────────────
const proof_log = [];

function log(type, data) {
  const entry = { type, trace_id: TRACE_ID, ...data, ts: new Date().toISOString() };
  proof_log.push(entry);
  console.log(`[PHASE1] ${type}`, JSON.stringify(data));
  return entry;
}

// ── Write proof artifact ──────────────────────────────────────────────────────
function writeProof(result) {
  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

  const ts = Date.now();
  const log_path   = path.join(ARTIFACT_DIR, `phase1_atharva_${TRACE_ID}_log.jsonl`);
  const proof_path = path.join(ARTIFACT_DIR, `phase1_atharva_${TRACE_ID}_proof.json`);

  fs.writeFileSync(log_path, proof_log.map(e => JSON.stringify(e)).join('\n') + '\n', 'utf8');
  fs.writeFileSync(proof_path, JSON.stringify({
    phase:            1,
    trace_id:         TRACE_ID,
    execution_id:     EXECUTION_ID,
    atharva_host:     `${ATHARVA_HOST}:${ATHARVA_PORT}`,
    events_received:  result.events_received,
    trace_intact:     result.trace_intact,
    contract_accepted:result.contract_accepted,
    game_started:     result.game_started,
    status:           result.status,
    elapsed_ms:       result.elapsed_ms,
    generated_at:     new Date().toISOString()
  }, null, 2), 'utf8');

  console.log(`\n[PHASE1] Proof written:`);
  console.log(`  ${log_path}`);
  console.log(`  ${proof_path}`);
}

// ── HTTP POST contract ────────────────────────────────────────────────────────
function postContract() {
  return new Promise((resolve, reject) => {
    const contract = {
      trace_id:       TRACE_ID,
      execution_id:   EXECUTION_ID,
      mitra_decision: 'ALLOW',
      game_mode:      'runner',
      parameters:     {},
      jobs:           []
    };

    const body = JSON.stringify(contract);
    const options = {
      hostname: ATHARVA_HOST,
      port:     ATHARVA_PORT,
      path:     '/execute',
      method:   'POST',
      headers:  {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    };

    log('CONTRACT_POST_SENT', { url: `http://${ATHARVA_HOST}:${ATHARVA_PORT}/execute`, contract });

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          log('CONTRACT_POST_RESPONSE', { status: res.statusCode, body: parsed });
          if (res.statusCode === 200) {
            resolve(parsed);
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        } catch (e) {
          reject(new Error(`Parse error: ${e.message} — body: ${data}`));
        }
      });
    });

    req.on('error', (err) => {
      reject(new Error(`Cannot reach Atharva server at ${ATHARVA_HOST}:${ATHARVA_PORT} — ${err.message}`));
    });

    req.write(body);
    req.end();
  });
}

// ── WebSocket listener ────────────────────────────────────────────────────────
function listenForTelemetry(resolve_proof) {
  const ws_url = `ws://${ATHARVA_HOST}:${ATHARVA_PORT}/ws`;
  console.log(`\n[PHASE1] Connecting WebSocket: ${ws_url}`);

  const ws = new WebSocket(ws_url);

  let events_received   = 0;
  let trace_intact      = true;
  let contract_accepted = false;
  let game_started      = false;
  const start_ts        = Date.now();

  // Auto-close after timeout
  const timer = setTimeout(() => {
    log('TIMEOUT', { elapsed_ms: Date.now() - start_ts, events_received });
    ws.close();
  }, TIMEOUT_MS);

  ws.on('open', () => {
    log('WS_CONNECTED', { url: ws_url });
    console.log(`[PHASE1] ✓ WebSocket connected to Atharva renderer`);
  });

  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw.toString()); } catch { return; }

    events_received++;

    // Validate trace_id on every event that carries one
    if (msg.trace_id) {
      if (msg.trace_id !== TRACE_ID) {
        trace_intact = false;
        log('TRACE_BREACH', { expected: TRACE_ID, got: msg.trace_id, event_type: msg.event_type });
        console.error(`[PHASE1] ✗ TRACE BREACH: expected ${TRACE_ID}, got ${msg.trace_id}`);
      } else {
        log('TRACE_VALIDATED', { event_type: msg.event_type, tick: events_received });
      }
    }

    // Track key lifecycle events
    if (msg.event_type === 'contract_accepted') {
      contract_accepted = true;
      log('CONTRACT_ACCEPTED', { trace_id: msg.trace_id, execution_id: msg.execution_id, game_mode: msg.data?.game_mode });
      console.log(`[PHASE1] ✓ contract_accepted — trace_id=${msg.trace_id}`);
    }

    if (msg.event_type === 'game_start') {
      game_started = true;
      log('GAME_STARTED', { trace_id: msg.trace_id, game_mode: msg.data?.game_mode });
      console.log(`[PHASE1] ✓ game_start — game_mode=${msg.data?.game_mode}`);
      // game_start is the completion signal — close cleanly
      clearTimeout(timer);
      setTimeout(() => ws.close(), 200);
    }

    if (msg.event_type === 'game_over' || msg.event_type === 'game_exit') {
      log('GAME_ENDED', { trace_id: msg.trace_id, event_type: msg.event_type, data: msg.data });
      console.log(`[PHASE1] ✓ ${msg.event_type} — closing`);
      clearTimeout(timer);
      ws.close();
    }

    // Also log job messages (scene updates)
    if (msg.jobType) {
      log('JOB_RECEIVED', { jobType: msg.jobType, payload_keys: Object.keys(msg.payload || {}) });
    }
  });

  ws.on('close', () => {
    clearTimeout(timer);
    const elapsed = Date.now() - start_ts;
    log('WS_CLOSED', { elapsed_ms: elapsed, events_received });

    resolve_proof({
      events_received,
      trace_intact,
      contract_accepted,
      game_started,
      elapsed_ms: elapsed,
      status: (contract_accepted && trace_intact) ? 'PROOF_CONFIRMED' : 'PROOF_FAILED'
    });
  });

  ws.on('error', (err) => {
    clearTimeout(timer);
    log('WS_ERROR', { message: err.message });
    console.error(`[PHASE1] ✗ WebSocket error: ${err.message}`);
    resolve_proof({
      events_received,
      trace_intact: false,
      contract_accepted,
      game_started,
      elapsed_ms: Date.now() - start_ts,
      status: 'WS_ERROR'
    });
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function run() {
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║     PHASE 1 — ATHARVA LIVE CONVERGENCE PROOF        ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');
  console.log(`[PHASE1] trace_id    : ${TRACE_ID}`);
  console.log(`[PHASE1] execution_id: ${EXECUTION_ID}`);
  console.log(`[PHASE1] target      : ${ATHARVA_HOST}:${ATHARVA_PORT}`);
  console.log(`[PHASE1] timeout     : ${TIMEOUT_MS}ms\n`);

  // Step 1: Connect WebSocket first (so we don't miss early events)
  const proof_result = await new Promise((resolve) => {
    listenForTelemetry(resolve);

    // Step 2: POST contract after a short delay (let WS connect first)
    setTimeout(async () => {
      try {
        const response = await postContract();
        console.log(`\n[PHASE1] Contract accepted by Atharva: status=${response.status} trace_id=${response.trace_id}`);
      } catch (err) {
        console.error(`\n[PHASE1] ✗ Contract POST failed: ${err.message}`);
        console.error('[PHASE1] Is Atharva server running? uvicorn server:app --port 8080');
        log('CONTRACT_POST_FAILED', { error: err.message });
      }
    }, 500);
  });

  // Step 3: Write proof
  writeProof(proof_result);

  // Step 4: Print result
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║              PHASE 1 PROOF RESULT                   ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');
  console.log(`  trace_id         : ${TRACE_ID}`);
  console.log(`  events received  : ${proof_result.events_received}`);
  console.log(`  contract accepted: ${proof_result.contract_accepted ? '✓ YES' : '✗ NO'}`);
  console.log(`  game started     : ${proof_result.game_started ? '✓ YES' : '✗ NO'}`);
  console.log(`  trace intact     : ${proof_result.trace_intact ? '✓ YES' : '✗ BROKEN'}`);
  console.log(`  elapsed          : ${proof_result.elapsed_ms}ms`);
  console.log(`  status           : ${proof_result.status}`);
  console.log('');

  if (proof_result.status === 'PROOF_CONFIRMED') {
    console.log('✓ PHASE 1 LIVE CONVERGENCE PROOF: CONFIRMED\n');
    process.exit(0);
  } else {
    console.log('✗ PHASE 1 LIVE CONVERGENCE PROOF: FAILED\n');
    process.exit(1);
  }
}

run().catch(err => {
  console.error('[PHASE1] Fatal:', err.message);
  process.exit(1);
});

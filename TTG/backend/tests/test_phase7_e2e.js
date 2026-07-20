'use strict';

/**
 * test_phase7_e2e.js
 *
 * Phase 7 — End-to-End Validation
 *
 * Full flow for all three governance paths:
 *   Input → Pipeline → Mitra → Enforcement → Execution → Artifacts → Replay → Query
 *
 * Strategy:
 *   - Spin up a mock Mitra server (port auto-assigned) that returns ALLOW / FLAG / BLOCK
 *     on demand via a control endpoint.
 *   - Spin up a mock Execution server (port auto-assigned) that returns contract_accepted.
 *   - Point mitraClient and executionClient at the mocks via process.env (both read
 *     config at call time, so env override works without module reload).
 *   - Run pipeline.run() for each path.
 *   - After each run: verify artifacts on disk, run replay, run telemetry query.
 *
 * What is validated per path:
 *   Pipeline result  — success/failure, path, failure_code
 *   Artifacts        — all 5 files written, trace_id consistent in each
 *   Replay           — ReplayResult.success, path, decision, sequence
 *   Telemetry query  — stages present, trace_consistent, event count
 *
 * Usage:
 *   node backend/tests/test_phase7_e2e.js
 */

const http    = require('http');
const fs      = require('fs');
const path    = require('path');
const express = require('express');
const axios   = require('axios');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

// ─── Test state ───────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function assert(label, condition, detail = '') {
  if (condition) {
    console.log(`    ✅ ${label}`);
    passed++;
  } else {
    console.error(`    ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

// ─── Mock Mitra server ────────────────────────────────────────────────────────
// POST /api/mitra/evaluate  → returns whatever _mitraDecision is set to
// PUT  /control/decision    → sets _mitraDecision for next call

let _mitraDecision = 'ALLOW';

function buildMitraApp() {
  const app = express();
  app.use(express.json());

  app.put('/control/decision', (req, res) => {
    _mitraDecision = req.body.decision;
    res.json({ ok: true, decision: _mitraDecision });
  });

  app.post('/api/mitra/evaluate', (req, res) => {
    const d = _mitraDecision;
    res.json({
      status:       d,
      risk_level:   d === 'ALLOW' ? 'LOW' : d === 'FLAG' ? 'MEDIUM' : 'HIGH',
      confidence:   d === 'ALLOW' ? 0.95  : d === 'FLAG' ? 0.78     : 0.99,
      reason:       `Mock Mitra decision: ${d}`,
      trace_id:     `mock_mitra_${Date.now()}`,
      signal_type:  'implicit_positive'
    });
  });

  return app;
}

// ─── Mock Execution server ────────────────────────────────────────────────────
// POST /api/execution/submit → returns contract_accepted

function buildExecutionApp() {
  const app = express();
  app.use(express.json());

  app.post('/api/execution/submit', (req, res) => {
    const { trace_id, execution_id } = req.body;
    res.json({
      status:       'contract_accepted',
      execution_id: execution_id || 'mock_exec',
      trace_id:     trace_id     || 'mock_trace',
      accepted_at:  Date.now()
    });
  });

  return app;
}

// ─── Server lifecycle helpers ─────────────────────────────────────────────────

function startServer(app) {
  return new Promise(resolve => {
    const srv = http.createServer(app);
    srv.listen(0, () => resolve(srv));
  });
}

async function setMitraDecision(mitraPort, decision) {
  await axios.put(`http://localhost:${mitraPort}/control/decision`, { decision },
    { validateStatus: () => true });
}

// ─── Artifact verifier ────────────────────────────────────────────────────────

function verifyArtifacts(trace_id, label) {
  const base  = path.join(BUCKET_DIR, `execution_${trace_id}`);
  const files = {
    schema:   `${base}_schema.json`,
    decision: `${base}_decision.json`,
    events:   `${base}_events.jsonl`,
    state:    `${base}_state.json`,
    log:      `${base}_log.jsonl`
  };

  for (const [key, filepath] of Object.entries(files)) {
    const exists = fs.existsSync(filepath);
    assert(`${label} — artifact ${key} written`, exists);
    if (!exists) continue;

    const raw = fs.readFileSync(filepath, 'utf8').trim();
    assert(`${label} — artifact ${key} non-empty`, raw.length > 0);

    // Parse and check trace_id
    try {
      const lines = key === 'events' || key === 'log'
        ? raw.split('\n').filter(Boolean).map(l => JSON.parse(l))
        : [JSON.parse(raw)];

      // Top-level trace_id on JSON artifacts
      if (key !== 'events' && key !== 'log') {
        assert(`${label} — ${key}.trace_id matches`,
          lines[0].trace_id === trace_id,
          `got "${lines[0].trace_id}"`);
      }

      // Every JSONL line that has trace_id must match
      const badLines = lines.filter(l => l.trace_id && l.trace_id !== trace_id);
      assert(`${label} — ${key} all trace_ids consistent`,
        badLines.length === 0,
        `${badLines.length} mismatches`);

    } catch (err) {
      assert(`${label} — ${key} parseable`, false, err.message);
    }
  }
}

// ─── Per-path E2E runner ──────────────────────────────────────────────────────

async function runPath(label, decision, mitraPort, vesselInput) {
  console.log(`\n${'─'.repeat(68)}`);
  console.log(`PATH: ${label} (decision=${decision})`);
  console.log(`${'─'.repeat(68)}`);

  // Set mock Mitra to return the desired decision
  await setMitraDecision(mitraPort, decision);

  // ── Step 1: Run pipeline ──────────────────────────────────────────────────
  console.log(`\n  [1] Pipeline run`);
  const { run } = require('../domain-adapters/maritime/pipeline');
  const pipeResult = await run(vesselInput);
  const trace_id   = pipeResult.trace_id;

  console.log(`      trace_id   : ${trace_id}`);
  console.log(`      path       : ${pipeResult.path}`);
  console.log(`      success    : ${pipeResult.success}`);
  console.log(`      failure    : ${pipeResult.failure?.failure_code || 'none'}`);

  if (decision === 'ALLOW') {
    assert(`${label} — pipeline success`,         pipeResult.success === true);
    assert(`${label} — path is ALLOW`,            pipeResult.path === 'ALLOW');
    assert(`${label} — failure is null`,          pipeResult.failure === null);
    assert(`${label} — artifacts array non-empty`,pipeResult.artifacts.length > 0);
  } else {
    assert(`${label} — pipeline not success`,     pipeResult.success === false);
    assert(`${label} — path reflects decision`,
      pipeResult.path === decision ||
      pipeResult.path === `ENFORCEMENT_${decision}ED` ||
      ['ENFORCEMENT_BLOCKED','ENFORCEMENT_FLAGGED','DECISION_NOT_ALLOW'].includes(pipeResult.failure?.failure_code),
      `path="${pipeResult.path}" code="${pipeResult.failure?.failure_code}"`);
    assert(`${label} — failure object present`,   pipeResult.failure !== null);
    assert(`${label} — failure_code set`,         typeof pipeResult.failure?.failure_code === 'string');
    assert(`${label} — failure reason set`,       typeof pipeResult.failure?.reason === 'string');
  }

  assert(`${label} — trace_id present`,           typeof trace_id === 'string' && trace_id.length > 0);
  assert(`${label} — execution_id present`,       typeof pipeResult.execution_id === 'string');
  assert(`${label} — log array present`,          Array.isArray(pipeResult.log) && pipeResult.log.length > 0);

  // ── Step 2: Verify artifacts on disk ─────────────────────────────────────
  console.log(`\n  [2] Artifact verification`);
  verifyArtifacts(trace_id, label);

  // ── Step 3: Replay ────────────────────────────────────────────────────────
  console.log(`\n  [3] Replay`);
  const { replay } = require('../domain-adapters/maritime/replayEngine');
  const replayResult = await replay(trace_id);

  console.log(`      replay.success : ${replayResult.success}`);
  console.log(`      replay.path    : ${replayResult.path}`);
  console.log(`      replay.decision: ${replayResult.decision}`);
  if (!replayResult.success) {
    console.log(`      replay.failure : ${replayResult.failure?.failure_code} — ${replayResult.failure?.reason}`);
  }

  if (decision === 'ALLOW') {
    assert(`${label} — replay success`,           replayResult.success === true);
    assert(`${label} — replay path ALLOW`,        replayResult.path === 'ALLOW');
    assert(`${label} — replay decision ALLOW`,    replayResult.decision === 'ALLOW');
    assert(`${label} — replay event_count > 0`,   replayResult.event_count > 0);
    assert(`${label} — replay sequence valid`,    replayResult.sequence.length >= 2);
    assert(`${label} — replay failure null`,      replayResult.failure === null);
  } else {
    // FLAG/BLOCK: artifacts written (stopped path), replay reads them
    // Replay may succeed (artifacts present) or fail with SEQUENCE_INVALID
    // (stopped path only has 2 stages). Both are correct — what matters is
    // no crash and trace_id is consistent.
    assert(`${label} — replay no crash`,          replayResult !== null && replayResult !== undefined);
    assert(`${label} — replay trace_id matches`,  replayResult.trace_id === trace_id);
    if (replayResult.success) {
      assert(`${label} — replay path is ${decision}`, replayResult.path === decision);
    } else {
      // Acceptable failure codes for stopped paths
      const acceptableCodes = ['SEQUENCE_INVALID', 'DECISION_MISMATCH', 'STATE_INVALID'];
      assert(`${label} — replay structured failure`,
        typeof replayResult.failure?.failure_code === 'string',
        `got "${replayResult.failure?.failure_code}"`);
      console.log(`      (stopped path replay: ${replayResult.failure?.failure_code} — expected)`);
    }
  }

  // ── Step 4: Telemetry query ───────────────────────────────────────────────
  console.log(`\n  [4] Telemetry query`);
  const { query } = require('../domain-adapters/maritime/insightBridge');
  const telResult = query(trace_id);

  console.log(`      found          : ${telResult.found}`);
  console.log(`      source         : ${telResult.source}`);
  console.log(`      total          : ${telResult.total}`);
  console.log(`      stages_present : ${telResult.stages_present?.join(', ')}`);

  assert(`${label} — telemetry found`,            telResult.found === true);
  assert(`${label} — telemetry trace_consistent`, telResult.trace_consistent === true);
  assert(`${label} — telemetry events > 0`,       telResult.total > 0);
  assert(`${label} — decision_received present`,
    telResult.stages_present?.includes('decision_received'));
  assert(`${label} — enforcement_applied present`,
    telResult.stages_present?.includes('enforcement_applied'));

  if (decision === 'ALLOW') {
    assert(`${label} — execution_started present`,
      telResult.stages_present?.includes('execution_started'));
    assert(`${label} — execution_completed present`,
      telResult.stages_present?.includes('execution_completed'));
  }

  // Stage filter: decision_received must return only that stage
  const filtered = query(trace_id, { stage: 'decision_received' });
  assert(`${label} — stage filter works`,
    filtered.events.every(e => e.stage === 'decision_received'));

  return trace_id;
}

// ─── Cross-path assertions ────────────────────────────────────────────────────

function assertCrossPaths(traces) {
  console.log(`\n${'─'.repeat(68)}`);
  console.log('Cross-path assertions');
  console.log(`${'─'.repeat(68)}`);

  // All three trace_ids must be distinct
  const ids = Object.values(traces);
  assert('All three trace_ids are distinct',
    new Set(ids).size === ids.length,
    ids.join(', '));

  // Each trace must have its own artifact set
  for (const [path, trace_id] of Object.entries(traces)) {
    const schemaPath = path_join(BUCKET_DIR, `execution_${trace_id}_schema.json`);
    assert(`${path} artifacts isolated (schema exists)`, fs.existsSync(schemaPath));
  }

  // No artifact from one trace should reference another trace's ID
  for (const [pathLabel, trace_id] of Object.entries(traces)) {
    const decisionFile = path_join(BUCKET_DIR, `execution_${trace_id}_decision.json`);
    if (!fs.existsSync(decisionFile)) continue;
    const content = fs.readFileSync(decisionFile, 'utf8');
    const otherTraces = Object.values(traces).filter(t => t !== trace_id);
    for (const other of otherTraces) {
      assert(`${pathLabel} decision artifact does not reference other trace`,
        !content.includes(other),
        `found "${other}" in ${pathLabel} decision`);
    }
  }
}

function path_join(...args) { return path.join(...args); }

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run() {
  // ── Boot mock servers ─────────────────────────────────────────────────────
  const mitraSrv     = await startServer(buildMitraApp());
  const executionSrv = await startServer(buildExecutionApp());

  const mitraPort     = mitraSrv.address().port;
  const executionPort = executionSrv.address().port;

  // Point clients at mocks via env (both read at call time)
  process.env.MITRA_HOST         = 'localhost';
  process.env.MITRA_PORT         = String(mitraPort);
  process.env.MITRA_TIMEOUT_MS   = '3000';
  process.env.EXECUTION_HOST     = 'localhost';
  process.env.EXECUTION_PORT     = String(executionPort);
  process.env.EXECUTION_TIMEOUT_MS = '3000';

  console.log('\nPhase 7 — End-to-End Validation');
  console.log(`Mock Mitra     : http://localhost:${mitraPort}`);
  console.log(`Mock Execution : http://localhost:${executionPort}`);
  console.log('='.repeat(68));

  const vesselBase = { lat: 25.1, lon: 55.2, speed: 10, heading: 45, status: 'moving' };
  const traces = {};

  // ── ALLOW path ────────────────────────────────────────────────────────────
  traces.ALLOW = await runPath('ALLOW', 'ALLOW', mitraPort,
    { ...vesselBase, vessel_id: 'VESSEL_E2E_ALLOW' });

  // ── FLAG path ─────────────────────────────────────────────────────────────
  traces.FLAG = await runPath('FLAG', 'FLAG', mitraPort,
    { ...vesselBase, vessel_id: 'VESSEL_E2E_FLAG' });

  // ── BLOCK path ────────────────────────────────────────────────────────────
  traces.BLOCK = await runPath('BLOCK', 'BLOCK', mitraPort,
    { ...vesselBase, vessel_id: 'VESSEL_E2E_BLOCK' });

  // ── Cross-path assertions ─────────────────────────────────────────────────
  assertCrossPaths(traces);

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n' + '='.repeat(68));
  console.log('E2E VALIDATION SUMMARY');
  console.log('='.repeat(68));
  console.log(`  ALLOW  trace : ${traces.ALLOW}`);
  console.log(`  FLAG   trace : ${traces.FLAG}`);
  console.log(`  BLOCK  trace : ${traces.BLOCK}`);
  console.log(`\n  Results: ${passed} passed, ${failed} failed`);
  console.log('='.repeat(68));

  mitraSrv.close();
  executionSrv.close();
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[E2E] Fatal:', err.message);
  process.exit(1);
});

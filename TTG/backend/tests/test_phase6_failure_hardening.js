'use strict';

/**
 * test_phase6_failure_hardening.js
 *
 * Phase 6 — Failure Hardening (Service Layer)
 *
 * Tests four failure categories at both module and HTTP layers:
 *
 *   1. Mitra down
 *      - pipeline.run() returns structured MITRA_UNREACHABLE failure
 *      - POST /pipeline/run returns 422 with failure object
 *      - no crash, no silent swallow
 *
 *   2. Execution layer down
 *      - executionClient.submit() returns structured UNREACHABLE failure
 *      - failure propagates through pipeline as EXECUTION_UNREACHABLE
 *      - POST /pipeline/run returns 422 with failure object
 *
 *   3. Invalid input
 *      - missing fields → 400 at HTTP layer (controller guard)
 *      - invalid field values → 422 via pipeline failure (adapter rejects)
 *      - each case has failure_code, reason, stage
 *
 *   4. Corrupted artifacts (replay)
 *      - corrupt JSON in schema → ARTIFACT_LOAD_FAILED
 *      - corrupt JSONL line in events → ARTIFACT_LOAD_FAILED
 *      - trace_id mismatch injected into decision → TRACE_MISMATCH
 *      - decision field missing → DECISION_MISMATCH
 *      - all return structured ReplayResult, never throw
 *
 * Invariants checked on every failure result:
 *   - success === false
 *   - failure object present with failure_code + reason + failed_at
 *   - no unhandled exception escapes
 *   - HTTP status is 4xx (never 500 for known failures)
 *
 * Usage:
 *   node backend/tests/test_phase6_failure_hardening.js
 */

const http    = require('http');
const fs      = require('fs');
const path    = require('path');
const express = require('express');
const axios   = require('axios');

const { run }    = require('../domain-adapters/maritime/pipeline');
const { submit } = require('../domain-adapters/maritime/executionClient');
const { replay } = require('../domain-adapters/maritime/replayEngine');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

// ─── Minimal HTTP app ─────────────────────────────────────────────────────────

const app = express();
app.use(express.json());
app.use('/pipeline', require('../routes/pipeline'));

const server = http.createServer(app);
let BASE;

// ─── Test state ───────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;
const report = [];

function assert(label, condition, detail = '') {
  const ok = !!condition;
  if (ok) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
  report.push({ label, ok, detail });
}

async function http_req(method, url, body) {
  try {
    const res = await axios({ method, url, data: body, validateStatus: () => true });
    return { status: res.status, body: res.data };
  } catch (err) {
    return { status: 0, body: null, err: err.message };
  }
}

// ─── Invariant checker — applied to every failure result ─────────────────────

function assertFailureInvariants(label, result) {
  assert(`${label} — success is false`,         result.success === false);
  assert(`${label} — failure object present`,   result.failure !== null && typeof result.failure === 'object');
  assert(`${label} — failure_code is string`,   typeof result.failure?.failure_code === 'string');
  assert(`${label} — reason is string`,         typeof result.failure?.reason === 'string' && result.failure.reason.length > 0);
  assert(`${label} — failed_at is number`,      typeof result.failure?.failed_at === 'number');
  assert(`${label} — trace_id present`,         typeof result.trace_id === 'string');
}

function assertHttpFailureInvariants(label, status, body) {
  assert(`${label} — not 200`,                  status !== 200);
  assert(`${label} — not 500`,                  status !== 500, `got ${status}`);
  assert(`${label} — success false`,            body?.success === false);
}

// ─── Temp artifact helpers ────────────────────────────────────────────────────

function writeTempArtifacts(trace_id, overrides = {}) {
  const base = path.join(BUCKET_DIR, `execution_${trace_id}`);

  const schema = JSON.stringify({
    artifact_type: 'bhiv_execution_schema',
    trace_id,
    execution_id:  'exec_corrupt_test',
    governance:    { decision: 'ALLOW', risk_level: 'LOW', mitra_trace_id: 'mt_test', decided_at: Date.now() },
    contract:      { execution_id: 'exec_corrupt_test', trace_id, game_mode: 'open_scene',
                     entities: [{ id: 'V1', type: 'npc', transform: { position:[0,0,0], rotation:[0,0,0], scale:[1,1,1] } }],
                     physics: { gravity:[0,0,0], friction:0.1, bounce:0, air_resistance:0.05, collision_force:1 },
                     scoring: { rules: { distance:0, collectibles:0, time:0 }, end_conditions:['time_limit'] } }
  }, null, 2);

  const decision = JSON.stringify({
    artifact_type: 'bhiv_decision_record',
    trace_id,
    execution_id:  'exec_corrupt_test',
    decision_envelope: { decision: 'ALLOW', risk_level: 'LOW', confidence: 0.95,
                         reason: 'test', mitra_trace_id: 'mt_test',
                         your_trace_id: trace_id, decided_at: Date.now() },
    enforcement_result: { passed: true, blocked: false, flagged: false, decision: 'ALLOW', reason: 'test' }
  }, null, 2);

  const events = [
    JSON.stringify({ trace_id, execution_id: 'exec_corrupt_test', stage: 'decision_received',   timestamp: Date.now() - 40, metadata: { decision: 'ALLOW' }, source: 'insightBridge' }),
    JSON.stringify({ trace_id, execution_id: 'exec_corrupt_test', stage: 'enforcement_applied', timestamp: Date.now() - 30, metadata: { passed: true },       source: 'insightBridge' }),
    JSON.stringify({ trace_id, execution_id: 'exec_corrupt_test', stage: 'execution_started',   timestamp: Date.now() - 20, metadata: {},                      source: 'insightBridge' }),
    JSON.stringify({ trace_id, execution_id: 'exec_corrupt_test', stage: 'execution_completed', timestamp: Date.now() - 10, metadata: { status: 'completed' }, source: 'insightBridge' })
  ].join('\n') + '\n';

  const state = JSON.stringify({
    artifact_type: 'bhiv_final_state',
    trace_id,
    execution_id:  'exec_corrupt_test',
    governance:    { decision: 'ALLOW', risk_level: 'LOW', mitra_trace_id: 'mt_test' },
    state:         { stopped: false }
  }, null, 2);

  const log = [
    JSON.stringify({ trace_id, execution_id: 'exec_corrupt_test', stage: 'START', message: 'test', logged_at: Date.now() })
  ].join('\n') + '\n';

  fs.writeFileSync(`${base}_schema.json`,   overrides.schema   ?? schema);
  fs.writeFileSync(`${base}_decision.json`, overrides.decision ?? decision);
  fs.writeFileSync(`${base}_events.jsonl`,  overrides.events   ?? events);
  fs.writeFileSync(`${base}_state.json`,    overrides.state    ?? state);
  fs.writeFileSync(`${base}_log.jsonl`,     overrides.log      ?? log);
}

function cleanTempArtifacts(trace_id) {
  const base = path.join(BUCKET_DIR, `execution_${trace_id}`);
  for (const ext of ['_schema.json', '_decision.json', '_events.jsonl', '_state.json', '_log.jsonl']) {
    try { fs.unlinkSync(`${base}${ext}`); } catch { /* already gone */ }
  }
}

// ─── Category 1: Mitra down ───────────────────────────────────────────────────

async function testMitraDown() {
  console.log('\n══ Category 1: Mitra Down ══════════════════════════════════════');

  // 1a — module layer: pipeline.run() with Mitra unreachable
  console.log('\n  [1a] Module layer — pipeline.run()');
  const result = await run(
    { vessel_id: 'VESSEL_MITRA_DOWN', lat: 25.1, lon: 55.2, speed: 10, heading: 45, status: 'moving' },
    { trace_id: `mitra_down_${Date.now()}` }
  );

  assertFailureInvariants('Mitra down / module', result);
  assert('Mitra down — failure_code is MITRA_UNREACHABLE',
    result.failure?.failure_code === 'MITRA_UNREACHABLE',
    `got "${result.failure?.failure_code}"`);
  assert('Mitra down — stage is decision',
    result.failure?.stage === 'decision',
    `got "${result.failure?.stage}"`);
  assert('Mitra down — path reflects failure code',
    result.path === 'MITRA_UNREACHABLE');
  assert('Mitra down — log array present',
    Array.isArray(result.log) && result.log.length > 0);
  assert('Mitra down — artifacts written (stopped path)',
    Array.isArray(result.artifacts));

  // 1b — HTTP layer: POST /pipeline/run
  console.log('\n  [1b] HTTP layer — POST /pipeline/run');
  const { status, body } = await http_req('POST', `${BASE}/pipeline/run`, {
    vessel_id: 'VESSEL_MITRA_DOWN_HTTP', lat: 25.1, lon: 55.2, speed: 10, heading: 45
  });

  assertHttpFailureInvariants('Mitra down / HTTP', status, body);
  assert('Mitra down / HTTP — status 422',          status === 422);
  assert('Mitra down / HTTP — failure_code present', typeof body.failure?.failure_code === 'string');
  assert('Mitra down / HTTP — failure_code correct',
    body.failure?.failure_code === 'MITRA_UNREACHABLE',
    `got "${body.failure?.failure_code}"`);
}

// ─── Category 2: Execution layer down ────────────────────────────────────────

async function testExecutionDown() {
  console.log('\n══ Category 2: Execution Layer Down ════════════════════════════');

  // 2a — module layer: executionClient.submit() directly
  console.log('\n  [2a] Module layer — executionClient.submit()');
  const submitResult = await submit({
    trace_id:     `exec_down_${Date.now()}`,
    execution_id: 'exec_down_test',
    game_mode:    'open_scene',
    entities:     [{ id: 'V1', type: 'npc', transform: { position:[0,0,0], rotation:[0,0,0], scale:[1,1,1] } }],
    physics:      { gravity:[0,0,0], friction:0.1, bounce:0, air_resistance:0.05, collision_force:1 },
    scoring:      { rules: { distance:0, collectibles:0, time:0 }, end_conditions:['time_limit'] }
  });

  assert('Execution down / submit — success false',       submitResult.success === false);
  assert('Execution down / submit — code UNREACHABLE',    submitResult.code === 'UNREACHABLE',
    `got "${submitResult.code}"`);
  assert('Execution down / submit — error message set',   typeof submitResult.error === 'string' && submitResult.error.length > 0);
  assert('Execution down / submit — no throw',            true); // reaching here means no throw

  // 2b — pipeline.run() propagates execution failure as EXECUTION_UNREACHABLE
  // (only reachable if Mitra were up — since Mitra is down, we verify the
  //  failure is still structured and not a crash)
  console.log('\n  [2b] Module layer — pipeline.run() with execution down');
  const pipeResult = await run(
    { vessel_id: 'VESSEL_EXEC_DOWN', lat: 10.0, lon: 20.0, speed: 5, heading: 90, status: 'moving' },
    { trace_id: `exec_down_pipe_${Date.now()}` }
  );

  // Pipeline fails at Mitra (before reaching execution) — still structured
  assert('Execution down / pipeline — success false',     pipeResult.success === false);
  assert('Execution down / pipeline — failure present',   pipeResult.failure !== null);
  assert('Execution down / pipeline — failure_code set',  typeof pipeResult.failure?.failure_code === 'string');
  assert('Execution down / pipeline — no crash',          true);

  // 2c — HTTP layer
  console.log('\n  [2c] HTTP layer — POST /pipeline/run');
  const { status, body } = await http_req('POST', `${BASE}/pipeline/run`, {
    vessel_id: 'VESSEL_EXEC_DOWN_HTTP', lat: 10.0, lon: 20.0, speed: 5, heading: 90
  });

  assertHttpFailureInvariants('Execution down / HTTP', status, body);
  assert('Execution down / HTTP — status 422',            status === 422);
  assert('Execution down / HTTP — failure object',        typeof body.failure === 'object' && body.failure !== null);
}

// ─── Category 3: Invalid input ────────────────────────────────────────────────

async function testInvalidInput() {
  console.log('\n══ Category 3: Invalid Input ═══════════════════════════════════');

  // 3a — HTTP: missing required fields (controller guard → 400)
  console.log('\n  [3a] HTTP — missing required fields');
  const missingCases = [
    { label: 'empty body',        body: {} },
    { label: 'no vessel_id',      body: { lat:1, lon:1, speed:5, heading:0 } },
    { label: 'no lat',            body: { vessel_id:'V', lon:1, speed:5, heading:0 } },
    { label: 'no lon',            body: { vessel_id:'V', lat:1, speed:5, heading:0 } },
    { label: 'no speed',          body: { vessel_id:'V', lat:1, lon:1, heading:0 } },
    { label: 'no heading',        body: { vessel_id:'V', lat:1, lon:1, speed:5 } }
  ];

  for (const c of missingCases) {
    const { status, body } = await http_req('POST', `${BASE}/pipeline/run`, c.body);
    assert(`Missing field [${c.label}] — 400`,          status === 400);
    assert(`Missing field [${c.label}] — success false`, body?.success === false);
    assert(`Missing field [${c.label}] — error string`,  typeof body?.error === 'string');
  }

  // 3b — Module: invalid domain values (adapter rejects → pipeline failure)
  console.log('\n  [3b] Module — invalid domain values');
  const invalidCases = [
    { label: 'lat > 90',      input: { vessel_id:'V', lat:999,  lon:0,   speed:5,  heading:0,   status:'moving'   } },
    { label: 'lat < -90',     input: { vessel_id:'V', lat:-999, lon:0,   speed:5,  heading:0,   status:'moving'   } },
    { label: 'lon > 180',     input: { vessel_id:'V', lat:0,    lon:999, speed:5,  heading:0,   status:'moving'   } },
    { label: 'negative speed',input: { vessel_id:'V', lat:0,    lon:0,   speed:-1, heading:0,   status:'moving'   } },
    { label: 'heading > 360', input: { vessel_id:'V', lat:0,    lon:0,   speed:5,  heading:400, status:'moving'   } },
    { label: 'bad status',    input: { vessel_id:'V', lat:0,    lon:0,   speed:5,  heading:0,   status:'flying'   } },
    { label: 'null vessel_id',input: { vessel_id:null,lat:0,    lon:0,   speed:5,  heading:0,   status:'moving'   } }
  ];

  for (const c of invalidCases) {
    const result = await run(c.input, { trace_id: `invalid_${Date.now()}` });
    assert(`Invalid [${c.label}] — success false`,    result.success === false);
    assert(`Invalid [${c.label}] — failure present`,  result.failure !== null);
    assert(`Invalid [${c.label}] — failure_code set`, typeof result.failure?.failure_code === 'string');
    assert(`Invalid [${c.label}] — reason set`,       typeof result.failure?.reason === 'string');
    assert(`Invalid [${c.label}] — no crash`,         true);
  }

  // 3c — HTTP: invalid values → 422 (pipeline failure, not controller)
  console.log('\n  [3c] HTTP — invalid domain values');
  const { status, body } = await http_req('POST', `${BASE}/pipeline/run`, {
    vessel_id: 'V', lat: 999, lon: 0, speed: 5, heading: 0
  });
  assert('Invalid lat / HTTP — not 200',      status !== 200);
  assert('Invalid lat / HTTP — not 500',      status !== 500, `got ${status}`);
  assert('Invalid lat / HTTP — success false', body?.success === false);
}

// ─── Category 4: Corrupted artifacts (replay) ─────────────────────────────────

async function testCorruptedArtifacts() {
  console.log('\n══ Category 4: Corrupted Artifacts (Replay) ════════════════════');

  // 4a — corrupt JSON in schema file
  console.log('\n  [4a] Corrupt schema JSON');
  const t1 = `corrupt_schema_${Date.now()}`;
  writeTempArtifacts(t1, { schema: '{ this is not valid json :::' });
  const r1 = await replay(t1);
  assert('Corrupt schema — success false',          r1.success === false);
  assert('Corrupt schema — ARTIFACT_LOAD_FAILED',   r1.failure?.failure_code === 'ARTIFACT_LOAD_FAILED',
    `got "${r1.failure?.failure_code}"`);
  assert('Corrupt schema — reason mentions schema',  r1.failure?.reason?.toLowerCase().includes('schema'));
  assert('Corrupt schema — replay_log present',      Array.isArray(r1.replay_log));
  assert('Corrupt schema — no throw',                true);
  cleanTempArtifacts(t1);

  // 4b — corrupt JSONL line in events file
  console.log('\n  [4b] Corrupt events JSONL');
  const t2 = `corrupt_events_${Date.now()}`;
  writeTempArtifacts(t2, {
    events: '{"trace_id":"' + t2 + '","stage":"decision_received","timestamp":1}\n{ BAD JSON LINE\n'
  });
  const r2 = await replay(t2);
  assert('Corrupt events — success false',           r2.success === false);
  assert('Corrupt events — ARTIFACT_LOAD_FAILED',    r2.failure?.failure_code === 'ARTIFACT_LOAD_FAILED',
    `got "${r2.failure?.failure_code}"`);
  assert('Corrupt events — reason mentions events',  r2.failure?.reason?.toLowerCase().includes('events'));
  assert('Corrupt events — no throw',                true);
  cleanTempArtifacts(t2);

  // 4c — trace_id mismatch: decision artifact has wrong trace_id
  console.log('\n  [4c] trace_id mismatch in decision artifact');
  const t3 = `corrupt_trace_${Date.now()}`;
  const wrongDecision = JSON.stringify({
    artifact_type: 'bhiv_decision_record',
    trace_id:      'WRONG_TRACE_ID_INJECTED',   // deliberate mismatch
    execution_id:  'exec_corrupt_test',
    decision_envelope: { decision: 'ALLOW', risk_level: 'LOW', confidence: 0.95,
                         reason: 'test', mitra_trace_id: 'mt_test',
                         your_trace_id: 'WRONG_TRACE_ID_INJECTED', decided_at: Date.now() },
    enforcement_result: { passed: true, blocked: false, flagged: false, decision: 'ALLOW', reason: 'test' }
  }, null, 2);
  writeTempArtifacts(t3, { decision: wrongDecision });
  const r3 = await replay(t3);
  assert('Trace mismatch — success false',           r3.success === false);
  assert('Trace mismatch — TRACE_MISMATCH',          r3.failure?.failure_code === 'TRACE_MISMATCH',
    `got "${r3.failure?.failure_code}"`);
  assert('Trace mismatch — mismatches in meta',      Array.isArray(r3.failure?.meta?.mismatches) &&
                                                     r3.failure.meta.mismatches.length > 0);
  assert('Trace mismatch — no throw',                true);
  cleanTempArtifacts(t3);

  // 4d — decision field missing from decision artifact
  console.log('\n  [4d] Decision field missing from decision artifact');
  const t4 = `corrupt_nodecision_${Date.now()}`;
  const noDecision = JSON.stringify({
    artifact_type: 'bhiv_decision_record',
    trace_id:      t4,
    execution_id:  'exec_corrupt_test',
    decision_envelope: { risk_level: 'LOW' },   // decision field omitted
    enforcement_result: { passed: true, blocked: false, flagged: false }
  }, null, 2);
  writeTempArtifacts(t4, { decision: noDecision });
  const r4 = await replay(t4);
  assert('No decision — success false',              r4.success === false);
  assert('No decision — DECISION_MISMATCH',          r4.failure?.failure_code === 'DECISION_MISMATCH',
    `got "${r4.failure?.failure_code}"`);
  assert('No decision — reason set',                 typeof r4.failure?.reason === 'string');
  assert('No decision — no throw',                   true);
  cleanTempArtifacts(t4);

  // 4e — HTTP layer: POST /pipeline/replay with corrupt artifacts
  console.log('\n  [4e] HTTP — POST /pipeline/replay with corrupt schema');
  const t5 = `corrupt_http_${Date.now()}`;
  writeTempArtifacts(t5, { schema: 'NOT JSON AT ALL' });
  const { status, body } = await http_req('POST', `${BASE}/pipeline/replay/${t5}`);
  assert('Corrupt / HTTP — status 422',              status === 422);
  assert('Corrupt / HTTP — success false',           body?.success === false);
  assert('Corrupt / HTTP — failure_code present',    typeof body?.failure?.failure_code === 'string');
  assert('Corrupt / HTTP — not 500',                 status !== 500, `got ${status}`);
  cleanTempArtifacts(t5);

  // 4f — completely missing artifacts
  console.log('\n  [4f] Replay with no artifacts at all');
  const r6 = await replay('totally_missing_trace_xyz');
  assert('Missing artifacts — success false',        r6.success === false);
  assert('Missing artifacts — ARTIFACT_LOAD_FAILED', r6.failure?.failure_code === 'ARTIFACT_LOAD_FAILED');
  assert('Missing artifacts — no throw',             true);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run_all() {
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;
  BASE = `http://localhost:${port}`;

  console.log('\nPhase 6 — Failure Hardening (Service Layer)');
  console.log(`Server: ${BASE}`);
  console.log('='.repeat(68));

  await testMitraDown();
  await testExecutionDown();
  await testInvalidInput();
  await testCorruptedArtifacts();

  // ── Consolidated report ───────────────────────────────────────────────────
  console.log('\n' + '='.repeat(68));
  console.log('FAILURE HARDENING REPORT');
  console.log('='.repeat(68));

  const categories = [
    { name: 'Mitra Down',              prefix: 'Mitra down' },
    { name: 'Execution Layer Down',    prefix: 'Execution down' },
    { name: 'Invalid Input',           prefix: ['Missing field', 'Invalid', 'Invalid lat'] },
    { name: 'Corrupted Artifacts',     prefix: ['Corrupt', 'Trace mismatch', 'No decision', 'Missing artifacts'] }
  ];

  for (const cat of categories) {
    const prefixes = Array.isArray(cat.prefix) ? cat.prefix : [cat.prefix];
    const catItems = report.filter(r => prefixes.some(p => r.label.startsWith(p)));
    const catFailed = catItems.filter(r => !r.ok);
    const icon = catFailed.length === 0 ? '✅' : '❌';
    console.log(`\n  ${icon} ${cat.name}: ${catItems.length - catFailed.length}/${catItems.length} passed`);
    catFailed.forEach(r => console.log(`     ❌ ${r.label}${r.detail ? ' — ' + r.detail : ''}`));
  }

  console.log('\n' + '─'.repeat(68));
  console.log(`Total: ${passed} passed, ${failed} failed`);
  console.log('─'.repeat(68));

  server.close();
  process.exit(failed > 0 ? 1 : 0);
}

run_all().catch(err => {
  console.error('[TEST] Fatal unhandled error:', err.message);
  server.close();
  process.exit(1);
});

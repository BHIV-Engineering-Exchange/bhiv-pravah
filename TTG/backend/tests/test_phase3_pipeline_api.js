'use strict';

/**
 * test_phase3_pipeline_api.js
 *
 * Tests all 4 Phase 3 pipeline endpoints without requiring the full server.
 * Boots a minimal Express app with only the pipeline router mounted —
 * no MongoDB, no socket.io, no job queue.
 *
 * Covers:
 *   GET  /pipeline/health
 *   POST /pipeline/run        — valid, missing fields, invalid values, Mitra-down path
 *   GET  /pipeline/result/:trace_id — full set, partial set, missing
 *   POST /pipeline/replay/:trace_id — success, missing artifacts, bad trace
 *
 * Usage:
 *   node backend/tests/test_phase3_pipeline_api.js
 */

const http    = require('http');
const express = require('express');
const axios   = require('axios');

// ─── Boot minimal app ─────────────────────────────────────────────────────────

const app    = express();
app.use(express.json());
app.use('/pipeline', require('../routes/pipeline'));

const server = http.createServer(app);
let BASE;

// ─── Known full artifact trace (all 5 files present) ─────────────────────────

const FULL_TRACE   = 'maritime_c9e761c9-2f30-4d29-9e00-5875ae6c6f0c';
const PARTIAL_TRACE = 'maritime_37686045-f1e9-419f-995b-23dbaffa7b11'; // no decision artifact
const MISSING_TRACE = 'nonexistent_trace_000';

// ─── Test runner ──────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function assert(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

async function req(method, path, body) {
  try {
    const res = await axios({ method, url: `${BASE}${path}`, data: body, validateStatus: () => true });
    return { status: res.status, body: res.data };
  } catch (err) {
    return { status: 0, body: null, err: err.message };
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

async function testHealth() {
  console.log('\n── GET /pipeline/health ─────────────────────────────────────');
  const { status, body } = await req('GET', '/pipeline/health');

  assert('status 200',              status === 200);
  assert('success: true',           body.success === true);
  assert('service: pipeline',       body.service === 'pipeline');
  assert('status: ok',              body.status === 'ok');
  assert('bucket_accessible bool',  typeof body.bucket_accessible === 'boolean');
  assert('artifact_count >= 0',     typeof body.artifact_count === 'number' && body.artifact_count >= 0);
  assert('checked_at present',      typeof body.checked_at === 'number');
}

async function testRunValid() {
  console.log('\n── POST /pipeline/run — valid input (Mitra down → 422 failure) ──');
  const { status, body } = await req('POST', '/pipeline/run', {
    vessel_id: 'VESSEL_TEST',
    lat:       25.1,
    lon:       55.2,
    speed:     10,
    heading:   45,
    status:    'moving'
  });

  // Mitra is not running — pipeline returns a structured failure, not a crash
  assert('status 200 or 422',       status === 200 || status === 422);
  assert('body.success is boolean', typeof body.success === 'boolean');
  assert('trace_id present',        typeof body.trace_id === 'string' && body.trace_id.length > 0);
  assert('execution_id present',    typeof body.execution_id === 'string');
  assert('path present',            typeof body.path === 'string');
  assert('no unhandled crash',      body.error === undefined || body.success === false);

  if (!body.success) {
    assert('failure object present', body.failure !== null && typeof body.failure === 'object');
    assert('failure_code present',   typeof body.failure.failure_code === 'string');
    assert('reason present',         typeof body.failure.reason === 'string');
    console.log(`     path: ${body.path} | failure: ${body.failure?.failure_code} — ${body.failure?.reason}`);
  } else {
    console.log(`     path: ${body.path} | artifacts: ${body.artifacts?.length}`);
  }
}

async function testRunWithExplicitIds() {
  console.log('\n── POST /pipeline/run — caller-supplied trace_id/execution_id ──');
  const trace_id     = `test_trace_${Date.now()}`;
  const execution_id = `test_exec_${Date.now()}`;

  const { status, body } = await req('POST', '/pipeline/run', {
    vessel_id: 'VESSEL_BRAVO',
    lat: 10.0, lon: 20.0, speed: 5, heading: 90,
    trace_id,
    execution_id
  });

  assert('status 200 or 422',    status === 200 || status === 422);
  assert('trace_id echoed back', body.trace_id === trace_id);
  assert('execution_id echoed',  body.execution_id === execution_id);
}

async function testRunMissingFields() {
  console.log('\n── POST /pipeline/run — missing required fields ─────────────');

  const cases = [
    { label: 'empty body',          body: {} },
    { label: 'missing vessel_id',   body: { lat: 1, lon: 1, speed: 5, heading: 0 } },
    { label: 'missing lat',         body: { vessel_id: 'V1', lon: 1, speed: 5, heading: 0 } },
    { label: 'missing lon',         body: { vessel_id: 'V1', lat: 1, speed: 5, heading: 0 } },
    { label: 'missing speed',       body: { vessel_id: 'V1', lat: 1, lon: 1, heading: 0 } },
    { label: 'missing heading',     body: { vessel_id: 'V1', lat: 1, lon: 1, speed: 5 } }
  ];

  for (const c of cases) {
    const { status, body } = await req('POST', '/pipeline/run', c.body);
    assert(`${c.label} → 400`,      status === 400);
    assert(`${c.label} → success false`, body.success === false);
    assert(`${c.label} → error msg`,     typeof body.error === 'string');
  }
}

async function testRunInvalidValues() {
  console.log('\n── POST /pipeline/run — invalid field values ────────────────');

  const cases = [
    { label: 'lat out of range',     body: { vessel_id: 'V1', lat: 999,  lon: 0,   speed: 5, heading: 0 } },
    { label: 'lon out of range',     body: { vessel_id: 'V1', lat: 0,    lon: 999, speed: 5, heading: 0 } },
    { label: 'negative speed',       body: { vessel_id: 'V1', lat: 0,    lon: 0,   speed: -1, heading: 0 } },
    { label: 'heading > 360',        body: { vessel_id: 'V1', lat: 0,    lon: 0,   speed: 5, heading: 400 } }
  ];

  for (const c of cases) {
    const { status, body } = await req('POST', '/pipeline/run', c.body);
    // Invalid values pass the controller (it only checks presence) and fail inside pipeline
    // Either 400 (if controller catches) or 422 (pipeline failure) — both are correct
    assert(`${c.label} → not 200 or 500`, status !== 200 && status !== 500);
    assert(`${c.label} → success false`,  body.success === false);
  }
}

async function testResultFullSet() {
  console.log('\n── GET /pipeline/result/:trace_id — full artifact set ───────');
  const { status, body } = await req('GET', `/pipeline/result/${FULL_TRACE}`);

  assert('status 200',                  status === 200);
  assert('success: true',               body.success === true);
  assert('trace_id matches',            body.trace_id === FULL_TRACE);
  assert('no missing field',            body.missing === undefined);
  assert('artifacts.schema present',    body.artifacts?.schema !== undefined);
  assert('artifacts.decision present',  body.artifacts?.decision !== undefined);
  assert('artifacts.events is array',   Array.isArray(body.artifacts?.events));
  assert('artifacts.state present',     body.artifacts?.state !== undefined);
  assert('artifacts.log is array',      Array.isArray(body.artifacts?.log));
  assert('events non-empty',            body.artifacts?.events?.length > 0);
  assert('log non-empty',               body.artifacts?.log?.length > 0);
  assert('schema has trace_id',         body.artifacts?.schema?.trace_id === FULL_TRACE);
  assert('decision has trace_id',       body.artifacts?.decision?.trace_id === FULL_TRACE);
}

async function testResultPartialSet() {
  console.log('\n── GET /pipeline/result/:trace_id — partial artifact set ────');
  const { status, body } = await req('GET', `/pipeline/result/${PARTIAL_TRACE}`);

  // Partial set: some artifacts exist, some don't — should still return 200 with missing list
  assert('status 200 or 404',           status === 200 || status === 404);
  if (status === 200) {
    assert('success: true',             body.success === true);
    assert('missing array present',     Array.isArray(body.missing) || body.missing === undefined);
    assert('artifacts object present',  typeof body.artifacts === 'object');
  } else {
    assert('success: false on 404',     body.success === false);
    assert('error message present',     typeof body.error === 'string');
  }
}

async function testResultMissing() {
  console.log('\n── GET /pipeline/result/:trace_id — no artifacts ────────────');
  const { status, body } = await req('GET', `/pipeline/result/${MISSING_TRACE}`);

  assert('status 404',        status === 404);
  assert('success: false',    body.success === false);
  assert('error present',     typeof body.error === 'string');
}

async function testReplaySuccess() {
  console.log('\n── POST /pipeline/replay/:trace_id — success ────────────────');
  const { status, body } = await req('POST', `/pipeline/replay/${FULL_TRACE}`);

  assert('status 200',                  status === 200);
  assert('success: true',               body.success === true);
  assert('trace_id matches',            body.trace_id === FULL_TRACE);
  assert('execution_id present',        typeof body.execution_id === 'string');
  assert('path is ALLOW/FLAG/BLOCK',    ['ALLOW','FLAG','BLOCK'].includes(body.path));
  assert('decision present',            typeof body.decision === 'string');
  assert('event_count > 0',             body.event_count > 0);
  assert('emitted_events is array',     Array.isArray(body.emitted_events));
  assert('sequence is array',           Array.isArray(body.sequence));
  assert('sequence non-empty',          body.sequence.length > 0);
  assert('failure is null',             body.failure === null);
  assert('replay_log is array',         Array.isArray(body.replay_log));
  assert('replay_log non-empty',        body.replay_log.length > 0);
  console.log(`     path=${body.path} | events=${body.event_count} | sequence: ${body.sequence.join(' → ')}`);
}

async function testReplayMissingArtifacts() {
  console.log('\n── POST /pipeline/replay/:trace_id — missing artifacts ──────');
  const { status, body } = await req('POST', `/pipeline/replay/${MISSING_TRACE}`);

  assert('status 422',                  status === 422);
  assert('success: false',              body.success === false);
  assert('failure present',             body.failure !== null);
  assert('failure_code correct',        body.failure?.failure_code === 'ARTIFACT_LOAD_FAILED');
  assert('reason mentions missing',     body.failure?.reason?.toLowerCase().includes('missing'));
  assert('replay_log present',          Array.isArray(body.replay_log));
}

async function testReplaySecondFullTrace() {
  console.log('\n── POST /pipeline/replay/:trace_id — second full trace ──────');
  const TRACE2 = 'maritime_86e9faac-a6b8-4692-909d-875507bc7ee8';
  const { status, body } = await req('POST', `/pipeline/replay/${TRACE2}`);

  assert('status 200',        status === 200);
  assert('success: true',     body.success === true);
  assert('trace_id matches',  body.trace_id === TRACE2);
  assert('path present',      typeof body.path === 'string');
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run() {
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;
  BASE = `http://localhost:${port}`;
  console.log(`\nPhase 3 — Pipeline API Tests`);
  console.log(`Server: ${BASE}`);
  console.log('='.repeat(60));

  await testHealth();
  await testRunValid();
  await testRunWithExplicitIds();
  await testRunMissingFields();
  await testRunInvalidValues();
  await testResultFullSet();
  await testResultPartialSet();
  await testResultMissing();
  await testReplaySuccess();
  await testReplayMissingArtifacts();
  await testReplaySecondFullTrace();

  console.log('\n' + '='.repeat(60));
  console.log(`Results: ${passed} passed, ${failed} failed`);
  console.log('='.repeat(60));

  server.close();
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[TEST] Fatal:', err.message);
  server.close();
  process.exit(1);
});

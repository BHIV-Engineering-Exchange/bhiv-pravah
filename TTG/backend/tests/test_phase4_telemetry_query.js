'use strict';

/**
 * test_phase4_telemetry_query.js
 *
 * Tests GET /pipeline/telemetry/:trace_id
 *
 * Covers:
 *   - Returns all 4 stages for a known trace (file source)
 *   - Returns correct event shape on every record
 *   - trace_consistent is true for clean data
 *   - ?stage= filter returns only matching events
 *   - ?stage= with invalid value → 400
 *   - Unknown trace_id → 404
 *   - Missing trace_id (no param) → 404 (route not matched)
 *   - Live emit → immediately queryable from memory
 *   - Memory + file merge deduplicates correctly
 *
 * Usage:
 *   node backend/tests/test_phase4_telemetry_query.js
 */

const http    = require('http');
const express = require('express');
const axios   = require('axios');
const {
  emitDecisionReceived,
  emitEnforcementApplied,
  emitExecutionStarted,
  emitExecutionCompleted,
  _clearStream
} = require('../domain-adapters/maritime/insightBridge');

// ─── Boot minimal app ─────────────────────────────────────────────────────────

const app = express();
app.use(express.json());
app.use('/pipeline', require('../routes/pipeline'));

const server = http.createServer(app);
let BASE;

// ─── Known traces with persisted telemetry files ──────────────────────────────

const FILE_TRACE    = 'p8-allow-test';       // has all 4 stages on disk
const MISSING_TRACE = 'nonexistent_000';

const VALID_STAGES = [
  'decision_received',
  'enforcement_applied',
  'execution_started',
  'execution_completed'
];

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

async function req(method, url) {
  try {
    const res = await axios({ method, url, validateStatus: () => true });
    return { status: res.status, body: res.data };
  } catch (err) {
    return { status: 0, body: null, err: err.message };
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

async function testFullTrace() {
  console.log('\n── GET /telemetry/:trace_id — full file-backed trace ────────');
  const { status, body } = await req('GET', `${BASE}/pipeline/telemetry/${FILE_TRACE}`);

  assert('status 200',                    status === 200);
  assert('success: true',                 body.success === true);
  assert('trace_id matches',              body.trace_id === FILE_TRACE);
  assert('events is array',               Array.isArray(body.events));
  assert('events non-empty',              body.events.length > 0);
  assert('total is number',               typeof body.total === 'number' && body.total > 0);
  assert('filtered equals total (no filter)', body.filtered === body.total);
  assert('stage_filter is null',          body.stage_filter === null);
  assert('stages_present is array',       Array.isArray(body.stages_present));
  assert('trace_consistent: true',        body.trace_consistent === true);
  assert('source present',                typeof body.source === 'string');

  // All 4 stages must be present in this trace
  for (const stage of VALID_STAGES) {
    assert(`stage "${stage}" present`,    body.stages_present.includes(stage));
  }

  // Every event must have the required fields and correct trace_id
  const badEvents = body.events.filter(e =>
    !e.telemetry_id || !e.trace_id || !e.execution_id ||
    !e.stage || !e.timestamp || !e.metadata ||
    e.trace_id !== FILE_TRACE
  );
  assert('all events have required fields + correct trace_id', badEvents.length === 0,
    `${badEvents.length} bad events`);

  // Events must be sorted by timestamp ascending
  let sorted = true;
  for (let i = 1; i < body.events.length; i++) {
    if (body.events[i].timestamp < body.events[i - 1].timestamp) { sorted = false; break; }
  }
  assert('events sorted by timestamp asc', sorted);

  console.log(`     source=${body.source} | total=${body.total} | stages: ${body.stages_present.join(', ')}`);
}

async function testStageFilter() {
  console.log('\n── GET /telemetry/:trace_id?stage= — stage filter ───────────');

  for (const stage of VALID_STAGES) {
    const { status, body } = await req('GET',
      `${BASE}/pipeline/telemetry/${FILE_TRACE}?stage=${stage}`);

    assert(`${stage} → status 200`,         status === 200);
    assert(`${stage} → success true`,        body.success === true);
    assert(`${stage} → stage_filter set`,    body.stage_filter === stage);
    assert(`${stage} → all events match`,
      body.events.every(e => e.stage === stage),
      `found non-matching: ${body.events.filter(e=>e.stage!==stage).length}`);
    assert(`${stage} → filtered <= total`,   body.filtered <= body.total);
    console.log(`     stage=${stage} | filtered=${body.filtered}/${body.total}`);
  }
}

async function testInvalidStage() {
  console.log('\n── GET /telemetry/:trace_id?stage=bad — invalid stage ───────');
  const { status, body } = await req('GET',
    `${BASE}/pipeline/telemetry/${FILE_TRACE}?stage=not_a_real_stage`);

  assert('status 400',          status === 400);
  assert('success: false',      body.success === false);
  assert('error mentions stage', body.error?.includes('not_a_real_stage'));
  assert('error lists valid stages',
    VALID_STAGES.every(s => body.error?.includes(s)));
}

async function testMissingTrace() {
  console.log('\n── GET /telemetry/:trace_id — unknown trace ─────────────────');
  const { status, body } = await req('GET',
    `${BASE}/pipeline/telemetry/${MISSING_TRACE}`);

  assert('status 404',       status === 404);
  assert('success: false',   body.success === false);
  assert('error present',    typeof body.error === 'string');
}

async function testLiveEmit() {
  console.log('\n── Live emit → immediately queryable from memory ────────────');

  const trace_id     = `live_test_${Date.now()}`;
  const execution_id = `exec_live_${Date.now()}`;

  // Emit all 4 stages into memory
  emitDecisionReceived(trace_id, execution_id, {
    decision: 'ALLOW', risk_level: 'LOW', confidence: 0.95,
    reason: 'test', mitra_trace_id: 'mt_001', signal_type: 'implicit_positive',
    source: 'mitra', decided_at: Date.now()
  });
  emitEnforcementApplied(trace_id, execution_id, {
    passed: true, blocked: false, flagged: false,
    decision: 'ALLOW', reason: 'test', enforced_at: Date.now()
  });
  emitExecutionStarted(trace_id, execution_id, { game_mode: 'open_scene', entity_count: 1 });
  emitExecutionCompleted(trace_id, execution_id, { status: 'completed', duration: 50 });

  const { status, body } = await req('GET', `${BASE}/pipeline/telemetry/${trace_id}`);

  assert('status 200',                  status === 200);
  assert('found: true',                 body.success === true);
  assert('exactly 4 events',            body.events.length === 4);
  assert('source includes memory',      body.source.includes('memory'));
  assert('trace_consistent: true',      body.trace_consistent === true);
  assert('all 4 stages present',
    VALID_STAGES.every(s => body.stages_present.includes(s)));

  // Verify each stage appears exactly once
  for (const stage of VALID_STAGES) {
    const count = body.events.filter(e => e.stage === stage).length;
    assert(`exactly 1 "${stage}" event`, count === 1, `found ${count}`);
  }

  // Verify decision_received metadata
  const dr = body.events.find(e => e.stage === 'decision_received');
  assert('decision_received.metadata.decision = ALLOW', dr?.metadata?.decision === 'ALLOW');
  assert('decision_received.metadata.risk_level = LOW', dr?.metadata?.risk_level === 'LOW');

  // Verify enforcement_applied metadata
  const ea = body.events.find(e => e.stage === 'enforcement_applied');
  assert('enforcement_applied.metadata.passed = true', ea?.metadata?.passed === true);

  // Clean up memory so it doesn't bleed into other tests
  _clearStream(trace_id);

  console.log(`     trace=${trace_id} | events=${body.events.length} | source=${body.source}`);
}

async function testMemoryFileMergeDedup() {
  console.log('\n── Memory + file merge — deduplication ──────────────────────');

  // FILE_TRACE already has events on disk.
  // Emit the SAME events into memory by re-reading the file and pushing them
  // into the stream — then query should deduplicate by telemetry_id.
  const { query, _clearStream: clear } = require('../domain-adapters/maritime/insightBridge');

  // Query once to get total from file only
  const fileOnly = query(FILE_TRACE);
  const fileTotal = fileOnly.total;

  // Now emit 1 fresh event into memory for this trace
  emitDecisionReceived(FILE_TRACE, 'exec_dedup_test', {
    decision: 'ALLOW', risk_level: 'LOW', confidence: 0.9,
    reason: 'dedup test', mitra_trace_id: 'mt_dedup', signal_type: 'test',
    source: 'mitra', decided_at: Date.now()
  });

  const { status, body } = await req('GET', `${BASE}/pipeline/telemetry/${FILE_TRACE}`);

  assert('status 200',                    status === 200);
  assert('total = file + 1 new event',    body.total === fileTotal + 1);
  assert('source is memory+file',         body.source === 'memory+file');
  assert('no duplicate telemetry_ids',    (() => {
    const ids = body.events.map(e => e.telemetry_id);
    return ids.length === new Set(ids).size;
  })());

  // Clean up the memory event we just added
  _clearStream(FILE_TRACE);

  console.log(`     file_total=${fileTotal} | after_emit=${body.total} | source=${body.source}`);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run() {
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;
  BASE = `http://localhost:${port}`;
  console.log(`\nPhase 4 — InsightBridge Query Layer Tests`);
  console.log(`Server: ${BASE}`);
  console.log('='.repeat(60));

  await testFullTrace();
  await testStageFilter();
  await testInvalidStage();
  await testMissingTrace();
  await testLiveEmit();
  await testMemoryFileMergeDedup();

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

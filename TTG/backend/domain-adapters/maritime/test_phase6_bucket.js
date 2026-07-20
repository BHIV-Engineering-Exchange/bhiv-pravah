'use strict';

/**
 * test_phase6_bucket.js
 *
 * Phase 6 — Bucket Artifacts Verification
 *
 * Tests:
 *   1.  No files exist before flush() — buffer-only until completion
 *   2.  flush() produces all 5 artifacts
 *   3.  schema.json — valid JSON, correct artifact_type, trace_id, contract present
 *   4.  decision.json — valid JSON, decision_envelope + enforcement_result present
 *   5.  events.jsonl — valid JSONL, every line has trace_id + execution_id
 *   6.  state.json — valid JSON, state present, governance present
 *   7.  log.jsonl — valid JSONL, every line has stage + message + trace_id
 *   8.  All 5 artifacts share the same trace_id
 *   9.  flush() with missing buffer → throws, no partial files written
 *  10.  Double flush() → throws
 *  11.  appendEvents() stamps trace_id on every event
 *  12.  status() reflects buffer state before and after flush
 *
 * Run: node backend/domain-adapters/maritime/test_phase6_bucket.js
 */

const fs   = require('fs');
const path = require('path');
const { create } = require('./pipelineBucketWriter');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

let passed = 0;
let failed = 0;

function check(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function artifactPath(trace_id, suffix) {
  return path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`);
}

function readJson(trace_id, suffix) {
  const p = artifactPath(trace_id, suffix);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function readJsonl(trace_id, suffix) {
  const p = artifactPath(trace_id, suffix);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));
}

function cleanArtifacts(trace_id) {
  ['schema.json', 'decision.json', 'events.jsonl', 'state.json', 'log.jsonl'].forEach(s => {
    const p = artifactPath(trace_id, s);
    if (fs.existsSync(p)) fs.unlinkSync(p);
  });
}

// ── Shared test data ──────────────────────────────────────────────────────────

const TRACE = 'trace-p6-test';
const EXEC  = 'exec_p6_001';

const MOCK_CONTRACT = {
  execution_id: EXEC,
  trace_id:     TRACE,
  game_mode:    'open_scene',
  entities:     [{ id: 'VESSEL_ALPHA', type: 'npc', transform: { position: [2510, 0, 5520], rotation: [0, 45, 0], scale: [1, 1, 1] } }],
  physics:      { gravity: [0, 0, 0], friction: 0.1, bounce: 0, air_resistance: 0.05, collision_force: 1 },
  scoring:      { rules: { distance: 0, collectibles: 0, time: 0 }, end_conditions: ['time_limit'] }
};

const MOCK_ENVELOPE = {
  decision: 'ALLOW', risk_level: 'LOW', confidence: 0.95,
  reason: 'passed', signal_type: 'implicit_positive', source: 'mitra',
  mitra_trace_id: 'mitra-p6-001', your_trace_id: TRACE, decided_at: Date.now()
};

const MOCK_GATE = {
  passed: true, blocked: false, flagged: false,
  decision: 'ALLOW', reason: 'gate passed', source: 'mitra', enforced_at: Date.now()
};

const MOCK_STATE = {
  vessel_count: 3, alert_count: 1,
  vessels: { VESSEL_ALPHA: { lat: 25.1, lon: 55.2, status: 'moving' } }
};

async function run() {

  // ── Case 1: No files before flush ─────────────────────────────────────────
  console.log('\n── Case 1: No files exist before flush() ──────────────────────');
  cleanArtifacts(TRACE);
  {
    const writer = create(TRACE, EXEC);
    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    writer.setDecision(MOCK_ENVELOPE, MOCK_GATE);
    writer.appendEvent('contract_accepted', { accepted_at: Date.now() });
    writer.setState(MOCK_STATE, MOCK_ENVELOPE);
    writer.log('PIPELINE', 'test log entry');

    // Before flush — no files
    check('schema.json not written yet',   !fs.existsSync(artifactPath(TRACE, 'schema.json')));
    check('decision.json not written yet', !fs.existsSync(artifactPath(TRACE, 'decision.json')));
    check('events.jsonl not written yet',  !fs.existsSync(artifactPath(TRACE, 'events.jsonl')));
    check('state.json not written yet',    !fs.existsSync(artifactPath(TRACE, 'state.json')));
    check('log.jsonl not written yet',     !fs.existsSync(artifactPath(TRACE, 'log.jsonl')));
  }

  // ── Case 2: flush() produces all 5 artifacts ──────────────────────────────
  console.log('\n── Case 2: flush() produces all 5 artifacts ───────────────────');
  {
    cleanArtifacts(TRACE);
    const writer = create(TRACE, EXEC);
    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    writer.setDecision(MOCK_ENVELOPE, MOCK_GATE);
    writer.appendEvent('contract_accepted',   { accepted_at: Date.now() });
    writer.appendEvent('execution_started',   { started_at: Date.now() });
    writer.appendEvent('entity_spawned',      { entity_id: 'VESSEL_ALPHA' });
    writer.appendEvent('execution_completed', { status: 'completed', duration: 500 });
    writer.setState(MOCK_STATE, MOCK_ENVELOPE);
    writer.log('PIPELINE', 'adapter ready');
    writer.log('MITRA',    'decision received: ALLOW');
    writer.log('GATE',     'enforcement passed');
    writer.log('EXEC',     'execution completed');

    const result = await writer.flush();

    check('flush returns 5 artifacts',     result.artifacts.length === 5);
    check('schema.json exists',            fs.existsSync(artifactPath(TRACE, 'schema.json')));
    check('decision.json exists',          fs.existsSync(artifactPath(TRACE, 'decision.json')));
    check('events.jsonl exists',           fs.existsSync(artifactPath(TRACE, 'events.jsonl')));
    check('state.json exists',             fs.existsSync(artifactPath(TRACE, 'state.json')));
    check('log.jsonl exists',              fs.existsSync(artifactPath(TRACE, 'log.jsonl')));
    check('flushed_at present',            typeof result.flushed_at === 'number');
    check('event_count=4',                 result.counts.events === 4);
    check('log_count=4',                   result.counts.log    === 4);
  }

  // ── Case 3: schema.json content ───────────────────────────────────────────
  console.log('\n── Case 3: schema.json — content validation ───────────────────');
  {
    const s = readJson(TRACE, 'schema.json');
    check('artifact_type correct',         s.artifact_type === 'bhiv_execution_schema');
    check('trace_id correct',              s.trace_id      === TRACE);
    check('execution_id correct',          s.execution_id  === EXEC);
    check('governance.decision present',   s.governance.decision === 'ALLOW');
    check('governance.mitra_trace_id',     typeof s.governance.mitra_trace_id === 'string');
    check('contract present',              !!s.contract);
    check('contract.game_mode present',    s.contract.game_mode === 'open_scene');
    check('flushed_at present',            typeof s.flushed_at === 'number');
  }

  // ── Case 4: decision.json content ─────────────────────────────────────────
  console.log('\n── Case 4: decision.json — content validation ─────────────────');
  {
    const d = readJson(TRACE, 'decision.json');
    check('artifact_type correct',              d.artifact_type === 'bhiv_decision_record');
    check('trace_id correct',                   d.trace_id      === TRACE);
    check('decision_envelope.decision=ALLOW',   d.decision_envelope.decision    === 'ALLOW');
    check('decision_envelope.source=mitra',     d.decision_envelope.source      === 'mitra');
    check('decision_envelope.confidence',       typeof d.decision_envelope.confidence === 'number');
    check('enforcement_result.passed=true',     d.enforcement_result.passed     === true);
    check('enforcement_result.blocked=false',   d.enforcement_result.blocked    === false);
    check('enforcement_result.decision=ALLOW',  d.enforcement_result.decision   === 'ALLOW');
  }

  // ── Case 5: events.jsonl content ──────────────────────────────────────────
  console.log('\n── Case 5: events.jsonl — JSONL validity + trace continuity ───');
  {
    const lines = readJsonl(TRACE, 'events.jsonl');
    check('events.jsonl has 4 lines',           lines.length === 4);
    check('all lines parse as JSON',            lines.every(l => typeof l === 'object'));
    check('all lines have trace_id',            lines.every(l => l.trace_id === TRACE));
    check('all lines have execution_id',        lines.every(l => l.execution_id === EXEC));
    check('all lines have event_type',          lines.every(l => typeof l.event_type === 'string'));
    check('all lines have buffered_at',         lines.every(l => typeof l.buffered_at === 'number'));
    check('event order preserved',             lines.map(l => l.event_type).join(',') ===
      'contract_accepted,execution_started,entity_spawned,execution_completed');
  }

  // ── Case 6: state.json content ────────────────────────────────────────────
  console.log('\n── Case 6: state.json — content validation ────────────────────');
  {
    const s = readJson(TRACE, 'state.json');
    check('artifact_type correct',              s.artifact_type === 'bhiv_final_state');
    check('trace_id correct',                   s.trace_id      === TRACE);
    check('governance.decision present',        s.governance.decision === 'ALLOW');
    check('state.vessel_count present',         s.state.vessel_count === 3);
    check('state.alert_count present',          s.state.alert_count  === 1);
    check('flushed_at present',                 typeof s.flushed_at === 'number');
  }

  // ── Case 7: log.jsonl content ─────────────────────────────────────────────
  console.log('\n── Case 7: log.jsonl — JSONL validity ─────────────────────────');
  {
    const lines = readJsonl(TRACE, 'log.jsonl');
    check('log.jsonl has 4 lines',              lines.length === 4);
    check('all lines have trace_id',            lines.every(l => l.trace_id === TRACE));
    check('all lines have execution_id',        lines.every(l => l.execution_id === EXEC));
    check('all lines have stage',               lines.every(l => typeof l.stage === 'string'));
    check('all lines have message',             lines.every(l => typeof l.message === 'string'));
    check('all lines have logged_at',           lines.every(l => typeof l.logged_at === 'number'));
  }

  // ── Case 8: All 5 artifacts share same trace_id ───────────────────────────
  console.log('\n── Case 8: All 5 artifacts share same trace_id ────────────────');
  {
    const schema   = readJson(TRACE, 'schema.json');
    const decision = readJson(TRACE, 'decision.json');
    const state    = readJson(TRACE, 'state.json');
    const events   = readJsonl(TRACE, 'events.jsonl');
    const log      = readJsonl(TRACE, 'log.jsonl');

    check('schema trace_id',   schema.trace_id   === TRACE);
    check('decision trace_id', decision.trace_id === TRACE);
    check('state trace_id',    state.trace_id    === TRACE);
    check('events trace_ids',  events.every(e => e.trace_id === TRACE));
    check('log trace_ids',     log.every(l => l.trace_id    === TRACE));
  }

  // ── Case 9: flush() with missing buffer → throws, no partial files ────────
  console.log('\n── Case 9: flush() with missing buffers → throws ───────────────');
  {
    const T2 = 'trace-p6-incomplete';
    cleanArtifacts(T2);
    const writer = create(T2, 'exec_p6_incomplete');
    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    // deliberately skip setDecision, appendEvent, setState, log

    let threw = false;
    try {
      await writer.flush();
    } catch (err) {
      threw = true;
      check('error mentions missing buffers', err.message.includes('missing buffers'));
    }
    check('flush threw',                    threw);
    check('no schema.json written',         !fs.existsSync(artifactPath(T2, 'schema.json')));
    check('no decision.json written',       !fs.existsSync(artifactPath(T2, 'decision.json')));
  }

  // ── Case 10: Double flush → throws ────────────────────────────────────────
  console.log('\n── Case 10: Double flush() → throws ───────────────────────────');
  {
    const T3 = 'trace-p6-double';
    cleanArtifacts(T3);
    const writer = create(T3, 'exec_p6_double');
    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    writer.setDecision(MOCK_ENVELOPE, MOCK_GATE);
    writer.appendEvent('contract_accepted', {});
    writer.setState(MOCK_STATE, MOCK_ENVELOPE);
    writer.log('TEST', 'double flush test');

    await writer.flush();

    let threw = false;
    try { await writer.flush(); } catch { threw = true; }
    check('second flush throws', threw);
    cleanArtifacts(T3);
  }

  // ── Case 11: appendEvents() stamps trace_id ───────────────────────────────
  console.log('\n── Case 11: appendEvents() stamps trace_id on every event ──────');
  {
    const T4 = 'trace-p6-stamp';
    cleanArtifacts(T4);
    const writer = create(T4, 'exec_p6_stamp');
    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    writer.setDecision(MOCK_ENVELOPE, MOCK_GATE);

    // Simulate events from eventCollector that might have a different trace
    writer.appendEvents([
      { event_type: 'contract_accepted',   trace_id: 'WRONG', execution_id: 'WRONG', payload: {} },
      { event_type: 'execution_completed', trace_id: 'WRONG', execution_id: 'WRONG', payload: {} }
    ]);

    writer.setState(MOCK_STATE, MOCK_ENVELOPE);
    writer.log('TEST', 'stamp test');

    await writer.flush();

    const lines = readJsonl(T4, 'events.jsonl');
    check('trace_id overridden to correct value', lines.every(l => l.trace_id === T4));
    check('execution_id overridden',              lines.every(l => l.execution_id === 'exec_p6_stamp'));
    cleanArtifacts(T4);
  }

  // ── Case 12: status() reflects buffer state ───────────────────────────────
  console.log('\n── Case 12: status() reflects buffer state ─────────────────────');
  {
    const writer = create('trace-p6-status', 'exec_p6_status');
    const s1 = writer.status();
    check('initially nothing set',   !s1.schema_set && !s1.decision_set && s1.event_count === 0);
    check('flushed=false initially', s1.flushed === false);

    writer.setSchema(MOCK_CONTRACT, MOCK_ENVELOPE);
    writer.appendEvent('contract_accepted', {});
    const s2 = writer.status();
    check('schema_set=true after setSchema', s2.schema_set === true);
    check('event_count=1 after appendEvent', s2.event_count === 1);
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n══════════════════════════════════════════════════════');
  console.log(`Phase 6 Bucket Artifacts — ${passed + failed} checks`);
  console.log(`  ✅ Passed : ${passed}`);
  console.log(`  ❌ Failed : ${failed}`);
  console.log(`  Status   : ${failed === 0 ? 'PHASE 6 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
  console.log('══════════════════════════════════════════════════════\n');
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[TEST] Fatal:', err.message);
  process.exit(1);
});

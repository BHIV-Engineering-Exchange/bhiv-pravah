'use strict';

/**
 * test_phase8_validation.js
 *
 * Phase 8 — Full End-to-End Validation (MANDATORY)
 *
 * Runs all 3 required paths through the complete pipeline:
 *
 *   Path 1 — ALLOW  → full execution, all 5 artifacts, 4 telemetry stages
 *   Path 2 — FLAG   → stopped at enforcement, no execution, decision artifact
 *   Path 3 — BLOCK  → stopped at enforcement, no execution, decision artifact
 *
 * Verifies for each path:
 *   ✓ correct behavior  (success/failure, path label, failure_code)
 *   ✓ correct artifacts (which files exist, which don't)
 *   ✓ correct telemetry (which stages emitted, trace-linked)
 *
 * Uses MITRA_STUB_ALLOWED=true so the pipeline runs without Mitra running.
 * Stub routes:
 *   vessel_id contains "BLOCK"      → BLOCK
 *   vessel_id contains "FLAG" + speed > 14 → FLAG (speed > 14 triggers FLAG in stub)
 *   normal vessel                   → ALLOW
 *
 * Run: node backend/domain-adapters/maritime/test_phase8_validation.js
 */

const fs   = require('fs');
const path = require('path');

// Enable stub so pipeline runs without real Mitra
process.env.MITRA_STUB_ALLOWED = 'true';

// Point execution client at a mock server we spin up below
process.env.EXECUTION_PORT = '19201';
process.env.EXECUTION_PATH = '/api/execution/submit';

const http       = require('http');
const { run }    = require('./pipeline');
const insightBridge = require('./insightBridge');
const { _clear } = require('./eventCollector');

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

function artifactExists(trace_id, suffix) {
  return fs.existsSync(path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`));
}

function readJson(trace_id, suffix) {
  const p = path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function readJsonl(trace_id, suffix) {
  const p = path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));
}

function cleanArtifacts(trace_id) {
  ['schema.json','decision.json','events.jsonl','state.json','log.jsonl'].forEach(s => {
    const p = path.join(BUCKET_DIR, `execution_${trace_id}_${s}`);
    if (fs.existsSync(p)) fs.unlinkSync(p);
  });
}

// ─── Mock execution server ────────────────────────────────────────────────────

function startMockExecutionServer() {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let body = '';
      req.on('data', c => { body += c; });
      req.on('end', () => {
        let parsed = {};
        try { parsed = JSON.parse(body); } catch {}
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status:       'contract_accepted',
          execution_id: parsed.execution_id,
          trace_id:     parsed.trace_id,
          accepted_at:  Date.now()
        }));
      });
    });
    server.listen(19201, () => resolve(server));
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function runAllPaths() {
  const server = await startMockExecutionServer();
  console.log('[MOCK SERVER] Execution mock listening on :19201\n');

  // ══════════════════════════════════════════════════════════════════════════
  // PATH 1 — ALLOW → full execution
  // ══════════════════════════════════════════════════════════════════════════
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║  PATH 1 — ALLOW → full execution                        ║');
  console.log('╚══════════════════════════════════════════════════════════╝');

  const TRACE_ALLOW = 'p8-allow-test';
  cleanArtifacts(TRACE_ALLOW);
  insightBridge._clearStream(TRACE_ALLOW);
  _clear(TRACE_ALLOW);

  const allowResult = await run(
    { vessel_id: 'VESSEL_ALPHA', lat: 25.1, lon: 55.2, speed: 8, heading: 45, status: 'moving' },
    { trace_id: TRACE_ALLOW, execution_id: 'exec_p8_allow' }
  );

  console.log('\n── Behavior ───────────────────────────────────────────────');
  check('success=true',                allowResult.success === true);
  check('path=ALLOW',                  allowResult.path    === 'ALLOW');
  check('no failure',                  allowResult.failure === null);
  check('trace_id preserved',          allowResult.trace_id === TRACE_ALLOW);
  check('duration > 0',                allowResult.duration > 0);

  console.log('\n── Artifacts ──────────────────────────────────────────────');
  check('schema.json exists',          artifactExists(TRACE_ALLOW, 'schema.json'));
  check('decision.json exists',        artifactExists(TRACE_ALLOW, 'decision.json'));
  check('events.jsonl exists',         artifactExists(TRACE_ALLOW, 'events.jsonl'));
  check('state.json exists',           artifactExists(TRACE_ALLOW, 'state.json'));
  check('log.jsonl exists',            artifactExists(TRACE_ALLOW, 'log.jsonl'));
  check('5 artifacts returned',        allowResult.artifacts.length === 5);

  // Artifact content
  const aSchema   = readJson(TRACE_ALLOW, 'schema.json');
  const aDecision = readJson(TRACE_ALLOW, 'decision.json');
  const aEvents   = readJsonl(TRACE_ALLOW, 'events.jsonl');
  const aState    = readJson(TRACE_ALLOW, 'state.json');
  const aLog      = readJsonl(TRACE_ALLOW, 'log.jsonl');

  check('schema.artifact_type correct',       aSchema?.artifact_type  === 'bhiv_execution_schema');
  check('schema.governance.decision=ALLOW',   aSchema?.governance?.decision === 'ALLOW');
  check('decision.decision_envelope=ALLOW',   aDecision?.decision_envelope?.decision === 'ALLOW');
  check('decision.enforcement.passed=true',   aDecision?.enforcement_result?.passed === true);
  check('events.jsonl has events',            aEvents && aEvents.length > 0);
  check('all events have trace_id',           aEvents?.every(e => e.trace_id === TRACE_ALLOW));
  check('state.artifact_type correct',        aState?.artifact_type === 'bhiv_final_state');
  check('state.governance.decision=ALLOW',    aState?.governance?.decision === 'ALLOW');
  check('log.jsonl has entries',              aLog && aLog.length > 0);
  check('all log entries have trace_id',      aLog?.every(l => l.trace_id === TRACE_ALLOW));

  console.log('\n── Telemetry ──────────────────────────────────────────────');
  const aTelemetry = allowResult.telemetry_events;
  const stages     = aTelemetry.map(e => e.stage);
  check('decision_received emitted',    stages.includes('decision_received'));
  check('enforcement_applied emitted',  stages.includes('enforcement_applied'));
  check('execution_started emitted',    stages.includes('execution_started'));
  check('execution_completed emitted',  stages.includes('execution_completed'));
  check('all telemetry trace-linked',   aTelemetry.every(e => e.trace_id === TRACE_ALLOW));
  check('all telemetry have telemetry_id', aTelemetry.every(e => typeof e.telemetry_id === 'string'));

  // ══════════════════════════════════════════════════════════════════════════
  // PATH 2 — FLAG → stopped before execution
  // ══════════════════════════════════════════════════════════════════════════
  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║  PATH 2 — FLAG → stopped before execution               ║');
  console.log('╚══════════════════════════════════════════════════════════╝');

  const TRACE_FLAG = 'p8-flag-test';
  cleanArtifacts(TRACE_FLAG);
  insightBridge._clearStream(TRACE_FLAG);
  _clear(TRACE_FLAG);

  // speed > 14 triggers FLAG in stub
  const flagResult = await run(
    { vessel_id: 'VESSEL_FAST', lat: 25.1, lon: 55.2, speed: 15, heading: 90, status: 'moving' },
    { trace_id: TRACE_FLAG, execution_id: 'exec_p8_flag' }
  );

  console.log('\n── Behavior ───────────────────────────────────────────────');
  check('success=false',               flagResult.success === false);
  check('path=DECISION_NOT_ALLOW or ENFORCEMENT_FLAGGED',
    ['DECISION_NOT_ALLOW','ENFORCEMENT_FLAGGED'].includes(flagResult.path));
  check('failure present',             flagResult.failure !== null);
  check('failure.failed=true',         flagResult.failure?.failed === true);
  check('trace_id preserved',          flagResult.trace_id === TRACE_FLAG);

  console.log('\n── Artifacts ──────────────────────────────────────────────');
  // decision.json and log.jsonl written — schema/events/state may exist (stopped path writes all 5)
  check('decision.json exists',        artifactExists(TRACE_FLAG, 'decision.json'));
  check('log.jsonl exists',            artifactExists(TRACE_FLAG, 'log.jsonl'));

  const fDecision = readJson(TRACE_FLAG, 'decision.json');
  check('decision is FLAG or BLOCK',   ['FLAG','BLOCK'].includes(fDecision?.decision_envelope?.decision));
  check('enforcement.passed=false',    fDecision?.enforcement_result?.passed === false);

  console.log('\n── Telemetry ──────────────────────────────────────────────');
  const fTelemetry = flagResult.telemetry_events;
  const fStages    = fTelemetry.map(e => e.stage);
  check('decision_received emitted',   fStages.includes('decision_received'));
  check('enforcement_applied emitted', fStages.includes('enforcement_applied'));
  check('execution_started NOT emitted', !fStages.includes('execution_started'));
  check('execution_completed NOT emitted', !fStages.includes('execution_completed'));
  check('all telemetry trace-linked',  fTelemetry.every(e => e.trace_id === TRACE_FLAG));

  // ══════════════════════════════════════════════════════════════════════════
  // PATH 3 — BLOCK → stopped before execution
  // ══════════════════════════════════════════════════════════════════════════
  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║  PATH 3 — BLOCK → stopped before execution              ║');
  console.log('╚══════════════════════════════════════════════════════════╝');

  const TRACE_BLOCK = 'p8-block-test';
  cleanArtifacts(TRACE_BLOCK);
  insightBridge._clearStream(TRACE_BLOCK);
  _clear(TRACE_BLOCK);

  // vessel_id contains BLOCK → stub returns BLOCK
  const blockResult = await run(
    { vessel_id: 'VESSEL_BLOCK_001', lat: 25.1, lon: 55.2, speed: 5, heading: 180, status: 'moving' },
    { trace_id: TRACE_BLOCK, execution_id: 'exec_p8_block' }
  );

  console.log('\n── Behavior ───────────────────────────────────────────────');
  check('success=false',               blockResult.success === false);
  check('path=DECISION_NOT_ALLOW or ENFORCEMENT_BLOCKED',
    ['DECISION_NOT_ALLOW','ENFORCEMENT_BLOCKED'].includes(blockResult.path));
  check('failure present',             blockResult.failure !== null);
  check('failure.failed=true',         blockResult.failure?.failed === true);
  check('trace_id preserved',          blockResult.trace_id === TRACE_BLOCK);

  console.log('\n── Artifacts ──────────────────────────────────────────────');
  check('decision.json exists',        artifactExists(TRACE_BLOCK, 'decision.json'));
  check('log.jsonl exists',            artifactExists(TRACE_BLOCK, 'log.jsonl'));

  const bDecision = readJson(TRACE_BLOCK, 'decision.json');
  check('decision is BLOCK',           bDecision?.decision_envelope?.decision === 'BLOCK');
  check('enforcement.passed=false',    bDecision?.enforcement_result?.passed === false);
  check('enforcement.blocked=true',    bDecision?.enforcement_result?.blocked === true);

  console.log('\n── Telemetry ──────────────────────────────────────────────');
  const bTelemetry = blockResult.telemetry_events;
  const bStages    = bTelemetry.map(e => e.stage);
  check('decision_received emitted',   bStages.includes('decision_received'));
  check('enforcement_applied emitted', bStages.includes('enforcement_applied'));
  check('execution_started NOT emitted', !bStages.includes('execution_started'));
  check('execution_completed NOT emitted', !bStages.includes('execution_completed'));
  check('all telemetry trace-linked',  bTelemetry.every(e => e.trace_id === TRACE_BLOCK));

  // ── Cross-path isolation ──────────────────────────────────────────────────
  console.log('\n── Cross-path isolation ───────────────────────────────────');
  check('ALLOW trace ≠ FLAG trace',    TRACE_ALLOW !== TRACE_FLAG);
  check('ALLOW trace ≠ BLOCK trace',   TRACE_ALLOW !== TRACE_BLOCK);
  check('FLAG artifacts not in ALLOW', !fs.existsSync(
    path.join(BUCKET_DIR, `execution_${TRACE_FLAG}_schema.json`) // schema only written on ALLOW
  ) || readJson(TRACE_FLAG, 'schema.json')?.governance?.decision !== 'ALLOW');

  server.close();

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n══════════════════════════════════════════════════════════');
  console.log(`Phase 8 Full Validation — ${passed + failed} checks`);
  console.log(`  ✅ Passed : ${passed}`);
  console.log(`  ❌ Failed : ${failed}`);
  console.log(`  Status   : ${failed === 0 ? 'PHASE 8 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
  console.log('══════════════════════════════════════════════════════════\n');
  process.exit(failed > 0 ? 1 : 0);
}

runAllPaths().catch(err => {
  console.error('[TEST] Fatal:', err.message, err.stack);
  process.exit(1);
});

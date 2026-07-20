'use strict';

/**
 * test_phase6_e2e_governed_flow.js
 *
 * Phase 6 — End-to-End Governed Flow
 *
 * Proves the full BHIV pipeline works for all 3 decision paths:
 *
 *   Input Data
 *     → Adapter    (no decision)
 *     → Mitra      (decision)
 *     → Enforcement Gate
 *     → Execution Schema
 *     → Engine
 *     → Telemetry
 *     → State
 *     → Bucket
 *     → InsightBridge
 *
 * Test cases:
 *   CASE 1 — ALLOW  : normal vessel, speed 10  → full pipeline runs, 5 artifacts written
 *   CASE 2 — FLAG   : speed > 14               → halted at gate, no execution, logged
 *   CASE 3 — BLOCK  : RESTRICTED vessel        → terminated at gate, no execution
 */

const { v4: uuidv4 }       = require('uuid');
const fs                   = require('fs').promises;
const path                 = require('path');
const { adaptVessel }      = require('../domain-adapters/maritime/maritimeAdapter');
const mitraClient          = require('../domain-adapters/maritime/mitraClient');
const enforcementGate      = require('../domain-adapters/maritime/enforcementGate');
const insightBridge        = require('../domain-adapters/maritime/insightBridge');
const msm                  = require('../domain-adapters/maritime/maritimeStateManager');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

let passed = 0;
let failed = 0;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function assert(condition, label) {
  if (condition) {
    console.log(`    ✅ ${label}`);
    passed++;
  } else {
    console.log(`    ❌ ${label}`);
    failed++;
  }
}

function section(title) {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('═'.repeat(60));
}

function step(label) {
  console.log(`\n  ──▶ ${label}`);
}

async function artifactExists(trace_id, suffix) {
  try {
    await fs.access(path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`));
    return true;
  } catch {
    return false;
  }
}

async function readArtifact(trace_id, suffix) {
  const file = path.join(BUCKET_DIR, `execution_${trace_id}_${suffix}`);
  const raw  = await fs.readFile(file, 'utf8');
  return suffix.endsWith('.jsonl')
    ? raw.trim().split('\n').filter(Boolean).map(l => JSON.parse(l))
    : JSON.parse(raw);
}

// ─── Core pipeline (used by all 3 cases) ─────────────────────────────────────
// Accepts a stub_decision override so we can force FLAG and BLOCK paths
// without needing Mitra to return those values.

async function runPipeline(vessel, stub_decision = null) {
  const trace_id     = `maritime_${uuidv4()}`;
  const execution_id = `exec_p6_${Date.now()}`;
  const governance   = { trace_id, execution_id };
  const simLog       = [];
  const eventLog     = [];

  const _log = (stage, msg) => {
    simLog.push({ stage, message: msg, timestamp: Date.now() });
    console.log(`    [${stage.padEnd(12)}] ${msg}`);
  };

  // ── Step 1: Adapter ────────────────────────────────────────────────────────
  step('Step 1 — Adapter (no decision)');
  const adapterResult = adaptVessel(vessel, governance);
  if (!adapterResult.success) {
    return { success: false, halted_at: 'adapter', errors: adapterResult.errors };
  }
  const schema = adapterResult.schema;
  _log('ADAPTER', `schema ready | trace=${trace_id}`);

  // ── Step 2: Mitra ──────────────────────────────────────────────────────────
  step('Step 2 — Mitra (external decision)');
  const mitraResult = await mitraClient.evaluate(schema);
  if (!mitraResult.success) {
    return { success: false, halted_at: 'mitra', error: mitraResult.error };
  }

  // Allow test to force a specific decision via stub_decision override
  if (stub_decision) {
    const overrides = {
      ALLOW: { decision: 'ALLOW', risk_level: 'LOW',    confidence: 0.95, reason: 'Test override: ALLOW' },
      FLAG:  { decision: 'FLAG',  risk_level: 'MEDIUM', confidence: 0.78, reason: 'Test override: FLAG — speed threshold exceeded' },
      BLOCK: { decision: 'BLOCK', risk_level: 'HIGH',   confidence: 0.99, reason: 'Test override: BLOCK — restricted vessel pattern' }
    };
    mitraResult.envelope = { ...mitraResult.envelope, ...overrides[stub_decision] };
    console.log(`    [MITRA_OVERRIDE] decision forced to ${stub_decision} for test`);
  }

  schema.decisionEnvelope = mitraResult.envelope;
  _log('MITRA', `decision=${mitraResult.envelope.decision} risk=${mitraResult.envelope.risk_level}`);

  // Phase 4 — emit: decision_received
  insightBridge.emitDecisionReceived(trace_id, execution_id, mitraResult.envelope);

  // ── Step 3: Enforcement Gate ───────────────────────────────────────────────
  step('Step 3 — Enforcement Gate');
  const gateResult = enforcementGate.enforce(schema);
  _log('ENFORCEMENT', `decision=${gateResult.decision} passed=${gateResult.passed} blocked=${gateResult.blocked} flagged=${gateResult.flagged}`);

  // Phase 4 — emit: enforcement_applied
  insightBridge.emitEnforcementApplied(trace_id, execution_id, gateResult);

  if (!gateResult.passed) {
    const label = gateResult.blocked ? 'BLOCKED' : 'FLAGGED';
    _log(label, `Execution halted — ${gateResult.reason}`);

    // Write partial artifacts even on halt — decision record must exist
    await fs.mkdir(BUCKET_DIR, { recursive: true });
    const decisionFile = path.join(BUCKET_DIR, `execution_${trace_id}_decision.json`);
    await fs.writeFile(decisionFile, JSON.stringify({
      artifact_type:  'bhiv_decision_record',
      trace_id, execution_id,
      written_at:     Date.now(),
      decision_envelope:  mitraResult.envelope,
      enforcement_result: gateResult
    }, null, 2));

    const eventsFile = path.join(BUCKET_DIR, `execution_${trace_id}_events.jsonl`);
    const ibEvents   = insightBridge.getStream(trace_id);
    await fs.writeFile(eventsFile, ibEvents.map(e => JSON.stringify({ ...e, source: 'insightBridge' })).join('\n') + '\n');

    const logFile = path.join(BUCKET_DIR, `execution_${trace_id}_log.jsonl`);
    await fs.writeFile(logFile, simLog.map(e => JSON.stringify(e)).join('\n') + '\n');

    return {
      success:    false,
      halted_at:  'enforcement',
      decision:   gateResult.decision,
      blocked:    gateResult.blocked,
      flagged:    gateResult.flagged,
      reason:     gateResult.reason,
      trace_id,
      execution_id,
      artifacts:  [decisionFile, eventsFile, logFile]
    };
  }

  // ── Step 4: Execution ──────────────────────────────────────────────────────
  step('Step 4 — Execution (Engine + State)');
  insightBridge.emitExecutionStarted(trace_id, execution_id, {
    vessel_id: vessel.vessel_id, speed: vessel.speed, status: vessel.status
  });

  const sessionInit = msm.initSession(schema);
  if (!sessionInit.success) {
    return { success: false, halted_at: 'state', error: sessionInit.error };
  }
  const sessionId = sessionInit.sessionId;
  _log('STATE', `session created: ${sessionId}`);

  const spawnResult = msm.applyMaritimeEvent(
    sessionId, 'vessel_spawned', vessel, governance
  );
  if (spawnResult.success) {
    eventLog.push({
      event_type: spawnResult.event.event_type,
      trace_id, execution_id,
      timestamp:  spawnResult.event.timestamp
    });
    _log('ENGINE', `vessel spawned: ${vessel.vessel_id}`);
  }

  // ── Step 5: Telemetry ──────────────────────────────────────────────────────
  step('Step 5 — Telemetry + State');
  const finalState = msm.getMaritimeState(sessionId);
  _log('TELEMETRY', `vessel_count=${finalState.maritime.vessel_count} transitions=${finalState.maritime.transitions.length}`);

  insightBridge.emitExecutionCompleted(trace_id, execution_id, {
    status:      'completed',
    vessel_id:   vessel.vessel_id,
    event_count: eventLog.length
  });

  // ── Step 6: Bucket — all 5 artifacts ──────────────────────────────────────
  step('Step 6 — Bucket (5 artifacts)');
  await fs.mkdir(BUCKET_DIR, { recursive: true });
  const written_at = Date.now();
  const envelope   = schema.decisionEnvelope;
  const artifacts  = [];

  const schemaFile = path.join(BUCKET_DIR, `execution_${trace_id}_schema.json`);
  await fs.writeFile(schemaFile, JSON.stringify({
    artifact_type: 'bhiv_execution_schema', trace_id, execution_id, written_at,
    governance: { decision: envelope.decision, risk_level: envelope.risk_level, mitra_trace_id: envelope.mitra_trace_id },
    schema
  }, null, 2));
  artifacts.push(schemaFile);

  const decisionFile = path.join(BUCKET_DIR, `execution_${trace_id}_decision.json`);
  await fs.writeFile(decisionFile, JSON.stringify({
    artifact_type: 'bhiv_decision_record', trace_id, execution_id, written_at,
    decision_envelope:  envelope,
    enforcement_result: gateResult
  }, null, 2));
  artifacts.push(decisionFile);

  const ibEvents   = insightBridge.getStream(trace_id);
  const allEvents  = [...eventLog, ...ibEvents.map(e => ({ ...e, source: 'insightBridge' }))];
  const eventsFile = path.join(BUCKET_DIR, `execution_${trace_id}_events.jsonl`);
  await fs.writeFile(eventsFile, allEvents.map(e => JSON.stringify(e)).join('\n') + '\n');
  artifacts.push(eventsFile);

  const stateFile = path.join(BUCKET_DIR, `execution_${trace_id}_state.json`);
  await fs.writeFile(stateFile, JSON.stringify({
    artifact_type: 'bhiv_final_state', trace_id, execution_id, written_at,
    governance: { decision: envelope.decision, risk_level: envelope.risk_level },
    state: finalState
  }, null, 2));
  artifacts.push(stateFile);

  const logFile = path.join(BUCKET_DIR, `execution_${trace_id}_log.jsonl`);
  await fs.writeFile(logFile, simLog.map(e => JSON.stringify(e)).join('\n') + '\n');
  artifacts.push(logFile);

  artifacts.forEach(a => _log('BUCKET', `✓ ${path.basename(a)}`));

  return {
    success: true, trace_id, execution_id, sessionId,
    decision: gateResult.decision,
    event_count: eventLog.length,
    final_state: finalState,
    artifacts
  };
}

// ─── CASE 1 — ALLOW ───────────────────────────────────────────────────────────

async function case1_allow() {
  section('CASE 1 — ALLOW PATH');
  console.log('  Vessel: VESSEL_NORMAL | speed: 10 | status: moving');
  console.log('  Expected: full pipeline runs, 5 artifacts written\n');

  const vessel = { vessel_id: 'VESSEL_NORMAL', lat: 25.1, lon: 55.2, speed: 10, heading: 90, status: 'moving' };
  const result = await runPipeline(vessel, 'ALLOW');

  assert(result.success === true,                    'pipeline completed successfully');
  assert(result.decision === 'ALLOW',                'decision is ALLOW');
  assert(result.halted_at === undefined,             'not halted at any stage');
  assert(result.event_count > 0,                     'events were produced');
  assert(result.artifacts.length === 5,              '5 artifacts written');

  // Verify all 5 artifacts exist on disk
  assert(await artifactExists(result.trace_id, 'schema.json'),   '_schema.json exists');
  assert(await artifactExists(result.trace_id, 'decision.json'), '_decision.json exists');
  assert(await artifactExists(result.trace_id, 'events.jsonl'),  '_events.jsonl exists');
  assert(await artifactExists(result.trace_id, 'state.json'),    '_state.json exists');
  assert(await artifactExists(result.trace_id, 'log.jsonl'),     '_log.jsonl exists');

  // Verify decision artifact has correct content
  const decision = await readArtifact(result.trace_id, 'decision.json');
  assert(decision.decision_envelope.decision === 'ALLOW',        'decision.json has ALLOW');
  assert(decision.enforcement_result.passed  === true,           'enforcement_result.passed is true');
  assert(decision.enforcement_result.blocked === false,          'enforcement_result.blocked is false');

  // Verify InsightBridge events in events.jsonl
  const events = await readArtifact(result.trace_id, 'events.jsonl');
  const stages = events.filter(e => e.source === 'insightBridge').map(e => e.stage);
  assert(stages.includes('decision_received'),   'InsightBridge: decision_received emitted');
  assert(stages.includes('enforcement_applied'), 'InsightBridge: enforcement_applied emitted');
  assert(stages.includes('execution_started'),   'InsightBridge: execution_started emitted');
  assert(stages.includes('execution_completed'), 'InsightBridge: execution_completed emitted');

  // Verify trace propagation — every event has trace_id
  const missing = events.filter(e => !e.trace_id);
  assert(missing.length === 0, 'no missing trace_id in any event');

  console.log(`\n  trace_id     : ${result.trace_id}`);
  console.log(`  execution_id : ${result.execution_id}`);
}

// ─── CASE 2 — FLAG ────────────────────────────────────────────────────────────

async function case2_flag() {
  section('CASE 2 — FLAG PATH');
  console.log('  Vessel: VESSEL_FAST | speed: 15 | status: moving');
  console.log('  Expected: halted at enforcement gate, decision.json + events.jsonl + log.jsonl written\n');

  const vessel = { vessel_id: 'VESSEL_FAST', lat: 25.3, lon: 55.4, speed: 15, heading: 45, status: 'moving' };
  const result = await runPipeline(vessel, 'FLAG');

  assert(result.success  === false,          'pipeline did NOT complete (correct)');
  assert(result.flagged  === true,           'flagged is true');
  assert(result.blocked  === false,          'blocked is false');
  assert(result.decision === 'FLAG',         'decision is FLAG');
  assert(result.halted_at === 'enforcement', 'halted at enforcement gate');
  assert(typeof result.reason === 'string',  'reason is present');

  // Verify decision artifact written even on FLAG
  assert(await artifactExists(result.trace_id, 'decision.json'), '_decision.json written on FLAG');
  assert(await artifactExists(result.trace_id, 'events.jsonl'),  '_events.jsonl written on FLAG');
  assert(await artifactExists(result.trace_id, 'log.jsonl'),     '_log.jsonl written on FLAG');

  // Verify no schema or state artifact (execution never started)
  assert(!(await artifactExists(result.trace_id, 'schema.json')), '_schema.json NOT written (no execution)');
  assert(!(await artifactExists(result.trace_id, 'state.json')),  '_state.json NOT written (no execution)');

  // Verify decision artifact content
  const decision = await readArtifact(result.trace_id, 'decision.json');
  assert(decision.decision_envelope.decision   === 'FLAG',  'decision.json has FLAG');
  assert(decision.enforcement_result.flagged   === true,    'enforcement_result.flagged is true');
  assert(decision.enforcement_result.passed    === false,   'enforcement_result.passed is false');

  // Verify InsightBridge emitted decision_received and enforcement_applied but NOT execution_started
  const events = await readArtifact(result.trace_id, 'events.jsonl');
  const stages = events.filter(e => e.source === 'insightBridge').map(e => e.stage);
  assert(stages.includes('decision_received'),    'InsightBridge: decision_received emitted');
  assert(stages.includes('enforcement_applied'),  'InsightBridge: enforcement_applied emitted');
  assert(!stages.includes('execution_started'),   'InsightBridge: execution_started NOT emitted (correct)');
  assert(!stages.includes('execution_completed'), 'InsightBridge: execution_completed NOT emitted (correct)');

  console.log(`\n  trace_id     : ${result.trace_id}`);
  console.log(`  reason       : ${result.reason}`);
}

// ─── CASE 3 — BLOCK ───────────────────────────────────────────────────────────

async function case3_block() {
  section('CASE 3 — BLOCK PATH');
  console.log('  Vessel: VESSEL_RESTRICTED_001 | speed: 5 | status: moving');
  console.log('  Expected: terminated at enforcement gate, decision.json written, no execution\n');

  const vessel = { vessel_id: 'VESSEL_RESTRICTED_001', lat: 25.2, lon: 55.5, speed: 5, heading: 180, status: 'moving' };
  const result = await runPipeline(vessel, 'BLOCK');

  assert(result.success  === false,          'pipeline did NOT complete (correct)');
  assert(result.blocked  === true,           'blocked is true');
  assert(result.flagged  === false,          'flagged is false');
  assert(result.decision === 'BLOCK',        'decision is BLOCK');
  assert(result.halted_at === 'enforcement', 'halted at enforcement gate');
  assert(typeof result.reason === 'string',  'reason is present');

  // Verify decision artifact written even on BLOCK
  assert(await artifactExists(result.trace_id, 'decision.json'), '_decision.json written on BLOCK');
  assert(await artifactExists(result.trace_id, 'events.jsonl'),  '_events.jsonl written on BLOCK');
  assert(await artifactExists(result.trace_id, 'log.jsonl'),     '_log.jsonl written on BLOCK');

  // Verify no schema or state artifact (execution never started)
  assert(!(await artifactExists(result.trace_id, 'schema.json')), '_schema.json NOT written (no execution)');
  assert(!(await artifactExists(result.trace_id, 'state.json')),  '_state.json NOT written (no execution)');

  // Verify decision artifact content
  const decision = await readArtifact(result.trace_id, 'decision.json');
  assert(decision.decision_envelope.decision   === 'BLOCK', 'decision.json has BLOCK');
  assert(decision.enforcement_result.blocked   === true,    'enforcement_result.blocked is true');
  assert(decision.enforcement_result.passed    === false,   'enforcement_result.passed is false');

  // Verify InsightBridge emitted decision_received and enforcement_applied but NOT execution_started
  const events = await readArtifact(result.trace_id, 'events.jsonl');
  const stages = events.filter(e => e.source === 'insightBridge').map(e => e.stage);
  assert(stages.includes('decision_received'),    'InsightBridge: decision_received emitted');
  assert(stages.includes('enforcement_applied'),  'InsightBridge: enforcement_applied emitted');
  assert(!stages.includes('execution_started'),   'InsightBridge: execution_started NOT emitted (correct)');

  console.log(`\n  trace_id     : ${result.trace_id}`);
  console.log(`  reason       : ${result.reason}`);
}

// ─── Runner ───────────────────────────────────────────────────────────────────

async function runAll() {
  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║   PHASE 6 — END-TO-END GOVERNED FLOW                    ║');
  console.log('║   Input → Adapter → Mitra → Gate → Engine → Bucket      ║');
  console.log('╚══════════════════════════════════════════════════════════╝');

  await case1_allow();
  await case2_flag();
  await case3_block();

  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log(`║  RESULTS: ${passed} passed, ${failed} failed`.padEnd(59) + '║');
  console.log('╚══════════════════════════════════════════════════════════╝\n');

  process.exit(failed > 0 ? 1 : 0);
}

runAll().catch(err => {
  console.error('[TEST RUNNER] Fatal:', err.message);
  process.exit(1);
});

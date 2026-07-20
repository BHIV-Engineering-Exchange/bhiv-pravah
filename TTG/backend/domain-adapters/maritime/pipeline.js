'use strict';

/**
 * pipeline.js
 *
 * Phase 8 — Full Pipeline Orchestrator
 *
 * Wires every phase into one callable function:
 *
 *   Input
 *   → Phase 1: contractBuilder    (schema lock)
 *   → Phase 2: mitraClient        (decision)
 *   → Phase 2: enforcementGate    (enforcement)
 *   → Phase 3: executionClient    (execution trigger)
 *   → Phase 4: eventCollector     (event stream)
 *   → Phase 5: insightBridge      (telemetry emission)
 *   → Phase 6: pipelineBucketWriter (buffer → flush artifacts)
 *   → Phase 7: failureGuard       (explicit failure at every step)
 *
 * Returns a PipelineResult — same shape for all 3 paths:
 *   { success, path, trace_id, execution_id, failure?, artifacts?, telemetry_events, log }
 *
 * Paths:
 *   ALLOW  → full execution, 5 artifacts flushed
 *   FLAG   → stopped at enforcement, decision artifact only
 *   BLOCK  → stopped at enforcement, decision artifact only
 */

const { v4: uuidv4 }          = require('uuid');
const { adaptVessel }          = require('./maritimeAdapter');
const { build }                = require('./contractBuilder');
const mitraClient              = require('./mitraClient');
const { enforce }              = require('./enforcementGate');
const { collect, getStream,
        isComplete, PIPELINE_EVENTS } = require('./eventCollector');
const insightBridge            = require('./insightBridge');
const { create: createBucket } = require('./pipelineBucketWriter');
const {
  assertTraceId,
  checkMitraResult,
  checkGateResult,
  checkContractBuild,
  fromError
} = require('./failureGuard');
const { run: simRun }          = require('../../simulation/engine/SimEngine');
const { adapt: adaptToSumScript } = require('../../simulation/contractAdapter');
const simResultStore           = require('../../simulation/simResultStore');
const nicaiFormatter           = require('../../simulation/nicaiFormatter');
const samruddhiFormatter       = require('../../simulation/samruddhiFormatter');

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Run the full pipeline for one vessel input.
 *
 * @param {Object} vesselInput  - Raw vessel data { vessel_id, lat, lon, speed, heading, status }
 * @param {Object} [opts]       - { trace_id, execution_id } — generated if omitted
 * @returns {Promise<PipelineResult>}
 */
async function run(vesselInput, opts = {}) {
  const trace_id     = opts.trace_id     || `maritime_${uuidv4()}`;
  const execution_id = opts.execution_id || `exec_${Date.now()}`;
  const startedAt    = Date.now();
  const pipelineLog  = [];

  function _log(stage, message, meta = {}) {
    const entry = { stage, message, meta, trace_id, execution_id, logged_at: Date.now() };
    pipelineLog.push(entry);
    console.log(`[PIPELINE:${stage.padEnd(12)}] ${message}`);
  }

  _log('START', `Pipeline started | trace=${trace_id} | vessel=${vesselInput?.vessel_id}`);

  // ── Guard: trace_id ────────────────────────────────────────────────────────
  const traceFailure = assertTraceId(trace_id, execution_id);
  if (traceFailure) return _result(false, 'UNKNOWN', trace_id, execution_id, startedAt, traceFailure, null, [], pipelineLog);

  // ── Phase 1: Adapt + Contract Lock ────────────────────────────────────────
  _log('ADAPTER', 'Building execution schema');
  const adapted = adaptVessel(vesselInput, { trace_id, execution_id });
  if (!adapted.success) {
    const f = fromError(`Adapter failed: ${adapted.errors.join(', ')}`, 'contract', trace_id, execution_id);
    return _result(false, 'UNKNOWN', trace_id, execution_id, startedAt, f, null, [], pipelineLog);
  }

  const built = build(adapted.schema);
  const contractFailure = checkContractBuild(built, trace_id, execution_id);
  if (contractFailure) return _result(false, 'UNKNOWN', trace_id, execution_id, startedAt, contractFailure, null, [], pipelineLog);

  const contract = built.contract;
  _log('ADAPTER', `Contract locked | execution_id=${execution_id}`);

  // ── Phase 2a: Mitra Decision ──────────────────────────────────────────────
  _log('MITRA', 'Requesting governance decision');
  insightBridge._clearStream(trace_id);

  const mitraResult = await mitraClient.evaluate(adapted.schema);

  const envelope = mitraResult.success && mitraResult.envelope ? mitraResult.envelope : null;

  const mitraFailure = checkMitraResult(
    envelope ? { ...mitraResult, envelope } : mitraResult,
    trace_id, execution_id
  );

  // Always emit decision_received telemetry (even for FLAG/BLOCK)
  if (envelope) {
    insightBridge.emitDecisionReceived(trace_id, execution_id, envelope);
    _log('MITRA', `Decision: ${envelope.decision} | risk=${envelope.risk_level} | source=${envelope.source}`);
  }

  if (mitraFailure) {
    _log('MITRA', `Decision failed: ${mitraFailure.reason}`);
    // Emit enforcement_applied with the synthetic stopped gate result
    const syntheticGate = {
      passed:      false,
      blocked:     envelope?.decision === 'BLOCK',
      flagged:     envelope?.decision === 'FLAG',
      decision:    envelope?.decision || 'UNKNOWN',
      reason:      mitraFailure.reason,
      enforced_at: Date.now()
    };
    insightBridge.emitEnforcementApplied(trace_id, execution_id, syntheticGate);
    const artifacts = await _writeStoppedArtifacts(
      trace_id, execution_id, contract, envelope || {}, syntheticGate, pipelineLog
    );
    return _result(false, mitraFailure.failure_code, trace_id, execution_id, startedAt, mitraFailure, artifacts, insightBridge.getStream(trace_id), pipelineLog);
  }

  // ── Phase 2b: Enforcement Gate ────────────────────────────────────────────
  _log('ENFORCEMENT', 'Applying governance decision');
  adapted.schema.decisionEnvelope = envelope;
  const gateResult   = enforce(adapted.schema);
  const gateFailure  = checkGateResult(gateResult, trace_id, execution_id);

  insightBridge.emitEnforcementApplied(trace_id, execution_id, gateResult);
  _log('ENFORCEMENT', `Gate result: passed=${gateResult.passed} | decision=${gateResult.decision}`);

  // ── FLAG / BLOCK path — stop here, write decision artifact only ───────────
  if (gateFailure) {
    _log('ENFORCEMENT', `Execution STOPPED — ${gateFailure.failure_code}: ${gateFailure.reason}`);

    // Write partial artifacts (decision + log only — no schema/events/state)
    const artifacts = await _writeStoppedArtifacts(
      trace_id, execution_id, contract, envelope, gateResult, pipelineLog
    );

    return _result(false, gateFailure.failure_code, trace_id, execution_id, startedAt, gateFailure, artifacts, insightBridge.getStream(trace_id), pipelineLog);
  }

  // ── Phase 3: Execution — run SimEngine directly ─────────────────────────
  _log('EXECUTION', 'Adapting contract to SumScript and running SimEngine');
  insightBridge.emitExecutionStarted(trace_id, execution_id, {
    game_mode:    contract.game_mode,
    entity_count: contract.entities.length
  });

  // Convert governed contract → SumScript contract
  const adaptResult = adaptToSumScript(contract);
  if (!adaptResult.valid) {
    const f = fromError(`SumScript adapter failed: ${adaptResult.errors.join(', ')}`, 'execution', trace_id, execution_id);
    _log('EXECUTION', `Adapter failed: ${f.reason}`);
    insightBridge.emitExecutionCompleted(trace_id, execution_id, { status: 'rejected', reason: f.reason });
    const artifacts = await _writeStoppedArtifacts(trace_id, execution_id, contract, envelope, gateResult, pipelineLog);
    return _result(false, 'ADAPTER_FAILED', trace_id, execution_id, startedAt, f, artifacts, insightBridge.getStream(trace_id), pipelineLog);
  }

  // Run the simulation
  const simResult = simRun(adaptResult.sumscript, { ticks: 10 });

  if (!simResult.success) {
    const f = fromError(`SimEngine failed: ${simResult.error}`, 'execution', trace_id, execution_id);
    _log('EXECUTION', `SimEngine failed: ${simResult.error}`);
    insightBridge.emitExecutionCompleted(trace_id, execution_id, { status: 'failed', reason: simResult.error });
    const artifacts = await _writeStoppedArtifacts(trace_id, execution_id, contract, envelope, gateResult, pipelineLog);
    return _result(false, 'SIM_FAILED', trace_id, execution_id, startedAt, f, artifacts, insightBridge.getStream(trace_id), pipelineLog);
  }

  // Store result for GET /simulate/result/:trace_id
  simResultStore.save(trace_id, simResult);

  // Format outputs for NICAI + Samruddhi
  const nicaiOutput     = nicaiFormatter.format(simResult);
  const samruddhiOutput = samruddhiFormatter.format(simResult);

  _log('EXECUTION', `SimEngine completed | ticks=${simResult.ticks_run} | events=${simResult.event_count} | entities=${Object.keys(simResult.entities).length}`);

  // ── Phase 4: Event Stream ─────────────────────────────────────────────────
  _log('EVENTS', 'Collecting runtime events');

  collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED,   trace_id, execution_id, { accepted_at: Date.now() });
  collect(PIPELINE_EVENTS.EXECUTION_STARTED,   trace_id, execution_id, { started_at: Date.now() });
  collect(PIPELINE_EVENTS.ENTITY_SPAWNED,      trace_id, execution_id, { entity_id: contract.entities[0]?.id, entity_type: contract.entities[0]?.type });
  collect(PIPELINE_EVENTS.EXECUTION_COMPLETED, trace_id, execution_id, { status: 'completed', duration: Date.now() - startedAt });

  const collectedEvents = getStream(trace_id).events;
  _log('EVENTS', `Stream complete | ${collectedEvents.length} events collected`);

  // ── Phase 5: Telemetry ────────────────────────────────────────────────────
  insightBridge.emitExecutionCompleted(trace_id, execution_id, {
    status:      'completed',
    duration:    Date.now() - startedAt,
    event_count: simResult.event_count
  });
  _log('TELEMETRY', `Emitted 4 telemetry stages`);

  // ── Phase 6: Flush all 5 artifacts ───────────────────────────────────────
  _log('BUCKET', 'Flushing artifacts');
  const bucket = createBucket(trace_id, execution_id);

  bucket.setSchema(contract, envelope);
  bucket.setDecision(envelope, gateResult);
  bucket.appendEvents(collectedEvents);
  bucket.appendEvents(insightBridge.getStream(trace_id).map(e => ({ ...e, event_type: e.stage })));
  bucket.setState(
    { vessel_id: vesselInput.vessel_id, lat: vesselInput.lat, lon: vesselInput.lon,
      speed: vesselInput.speed, status: vesselInput.status, completed_at: Date.now() },
    envelope
  );
  pipelineLog.forEach(e => bucket.log(e.stage, e.message, e.meta));

  const flushResult = await bucket.flush();
  _log('BUCKET', `Flushed ${flushResult.artifacts.length} artifacts`);

  const duration = Date.now() - startedAt;
  _log('COMPLETE', `Pipeline complete | duration=${duration}ms`);

  return _result(true, 'ALLOW', trace_id, execution_id, startedAt, null, flushResult.artifacts, insightBridge.getStream(trace_id), pipelineLog, simResult, nicaiOutput, samruddhiOutput);
}

// ─── Stopped-path artifact writer (FLAG / BLOCK / rejected) ──────────────────
// Writes only decision.json + log.jsonl — no schema/events/state

async function _writeStoppedArtifacts(trace_id, execution_id, contract, envelope, gateResult, pipelineLog) {
  const bucket = createBucket(trace_id, execution_id);
  bucket.setSchema(contract, envelope);
  bucket.setDecision(envelope, gateResult);
  bucket.appendEvent('pipeline_stopped', { decision: gateResult.decision, reason: gateResult.reason });
  bucket.setState({ stopped: true, decision: gateResult.decision }, envelope);
  pipelineLog.forEach(e => bucket.log(e.stage, e.message, e.meta));
  const result = await bucket.flush();
  return result.artifacts;
}

// ─── Result builder ───────────────────────────────────────────────────────────

function _result(success, path, trace_id, execution_id, startedAt, failure, artifacts, telemetry_events, log, simResult, nicaiOutput, samruddhiOutput) {
  return {
    success,
    path,
    trace_id,
    execution_id,
    duration:         Date.now() - startedAt,
    failure:          failure        || null,
    artifacts:        artifacts      || [],
    telemetry_events: telemetry_events || [],
    log,
    // Simulation outputs — only present on ALLOW path
    simulation:  simResult      || null,
    nicai:       nicaiOutput    || null,
    samruddhi:   samruddhiOutput || null
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { run };

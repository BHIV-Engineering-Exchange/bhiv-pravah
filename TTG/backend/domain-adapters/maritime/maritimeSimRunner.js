'use strict';

/**
 * maritimeSimRunner.js
 *
 * Phase 4 — End-to-End Governed Simulation
 *
 * Full pipeline:
 *   Input Data → Adapter → Mitra (ALLOW) → Core → Engine → Telemetry → State → Bucket
 *
 * Produces 4 mandatory artifacts in bucket_artifacts/:
 *   execution_<trace_id>_schema.json
 *   execution_<trace_id>_events.jsonl
 *   execution_<trace_id>_log.jsonl
 *   execution_<trace_id>_state.json
 */

const { v4: uuidv4 }                    = require('uuid');
const fs                                = require('fs').promises;
const path                              = require('path');
const { adaptVessel }                   = require('./maritimeAdapter');
const mitraClient                       = require('./mitraClient');
const enforcementGate                   = require('./enforcementGate');
const insightBridge                     = require('./insightBridge');
const { MARITIME_EVENTS, mapEvent }     = require('./maritimeEventMapper');
const msm                               = require('./maritimeStateManager');
const bucketWriter                      = require('../../bucketWriter');
const { recordExecutionTelemetry,
        recordJobStarted,
        recordJobCompleted,
        recordExecutionDuration }        = require('../../telemetry/behaviourRecorder');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

// ─── Simulation dataset ───────────────────────────────────────────────────────
// 5 vessels, varying speeds, different headings, one defined zone

const VESSELS = [
  { vessel_id: 'VESSEL_ALPHA',   lat: 25.10, lon: 55.20, speed: 14, heading: 45,  status: 'moving'   },
  { vessel_id: 'VESSEL_BRAVO',   lat: 25.30, lon: 55.40, speed: 8,  heading: 135, status: 'moving'   },
  { vessel_id: 'VESSEL_CHARLIE', lat: 25.50, lon: 55.10, speed: 5,  heading: 270, status: 'moving'   },
  { vessel_id: 'VESSEL_DELTA',   lat: 25.20, lon: 55.50, speed: 0,  heading: 0,   status: 'anchored' },
  { vessel_id: 'VESSEL_ECHO',    lat: 25.40, lon: 55.30, speed: 11, heading: 315, status: 'moving'   }
];

const ZONE = { zone_id: 'ZONE_RESTRICTED', lat: 25.30, lon: 55.35, radius: 15 };

// Movement deltas per tick — each vessel moves deterministically
const MOVEMENT_DELTAS = {
  VESSEL_ALPHA:   { dlat:  0.05, dlon:  0.05, dheading:  2 },
  VESSEL_BRAVO:   { dlat:  0.03, dlon: -0.02, dheading: -1 },
  VESSEL_CHARLIE: { dlat: -0.01, dlon: -0.04, dheading:  0 },
  VESSEL_DELTA:   { dlat:  0,    dlon:  0,    dheading:  0 },  // anchored
  VESSEL_ECHO:    { dlat:  0.04, dlon:  0.03, dheading:  3 }
};

const TICKS = 5;  // simulation steps

// ─── Main runner ──────────────────────────────────────────────────────────────

async function runSimulation() {
  const trace_id     = `maritime_${uuidv4()}`;
  const execution_id = `exec_maritime_sim_${Date.now()}`;
  const governance   = { trace_id, execution_id };
  const startTime    = Date.now();

  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║     MARITIME GOVERNED SIMULATION — PHASE 4               ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`trace_id    : ${trace_id}`);
  console.log(`execution_id: ${execution_id}`);
  console.log(`vessels     : ${VESSELS.length}`);
  console.log(`ticks       : ${TICKS}`);
  console.log(`zone        : ${ZONE.zone_id} at (${ZONE.lat}, ${ZONE.lon}) r=${ZONE.radius}\n`);

  // In-memory event log and telemetry for artifact writing
  const eventLog  = [];   // all runtime events produced
  const simLog    = [];   // human-readable simulation log entries

  // ── STEP 1: Adapt first vessel → schema (no decision yet) ──────────────────
  _log(simLog, 'PIPELINE', 'Step 1 — Adapter: building execution schema');

  const primarySchema = adaptVessel(VESSELS[0], governance);
  if (!primarySchema.success) {
    throw new Error(`Adapter failed: ${primarySchema.errors.join(', ')}`);
  }
  _log(simLog, 'ADAPTER', `Schema ready — execution_id: ${execution_id}, trace_id: ${trace_id}`);

  // ── STEP 2+3: Phase 3 Authority Lock ────────────────────────────────────
  // maritimeSimRunner MUST NOT call Mitra or enforcementGate directly.
  // All governance decisions belong to pipeline.js ONLY.
  // Redirect: use require('./pipeline').run(vesselInput) instead.
  throw new Error(
    '[PHASE 3 VIOLATION] maritimeSimRunner called Mitra directly. ' +
    'Mitra call and enforcement are ONLY allowed in pipeline.js. ' +
    'Use: const { run } = require("./pipeline"); await run(vesselInput);'
  );

  // ── STEP 4: Core — write execution schema to bucket ──────────────────────
  _log(simLog, 'CORE', 'Step 2 — Writing execution schema to bucket');
  await bucketWriter.writeExecutionSchema(
    trace_id,
    trace_id,
    primarySchema.schema,
    startTime
  );
  await bucketWriter.writeExecutionStart(trace_id, trace_id, startTime);
  _log(simLog, 'CORE', `execution_${trace_id}_schema.json written`);

  // ── STEP 3: State — initialize maritime session ───────────────────────────
  _log(simLog, 'STATE', 'Step 3 — Initializing maritime session in GSM');
  const sessionInit = msm.initSession(primarySchema.schema);
  if (!sessionInit.success) {
    throw new Error(`Session init failed: ${sessionInit.error}`);
  }
  const sessionId = sessionInit.sessionId;
  _log(simLog, 'STATE', `Session created: ${sessionId}`);

  // Register the restricted zone
  msm.registerZone(sessionId, ZONE.zone_id, ZONE.lat, ZONE.lon, ZONE.radius);
  _log(simLog, 'STATE', `Zone registered: ${ZONE.zone_id}`);

  // ── STEP 4: Engine — spawn all vessels ───────────────────────────────────
  _log(simLog, 'ENGINE', 'Step 4 — Spawning all vessels (SPAWN_ENTITY jobs)');

  const vesselState = {};
  VESSELS.forEach(v => { vesselState[v.vessel_id] = { ...v }; });

  for (const vessel of VESSELS) {
    recordJobStarted(execution_id, trace_id, `spawn_${vessel.vessel_id}`, 'SPAWN_ENTITY');

    const result = msm.applyMaritimeEvent(
      sessionId,
      MARITIME_EVENTS.VESSEL_SPAWNED,
      vessel,
      governance
    );

    if (!result.success) {
      _log(simLog, 'ERROR', `Failed to spawn ${vessel.vessel_id}: ${result.error}`);
      continue;
    }

    eventLog.push(_eventEntry(result.event, trace_id, execution_id, 'vessel_spawned'));
    recordJobCompleted(execution_id, trace_id, `spawn_${vessel.vessel_id}`, 'SPAWN_ENTITY', 0);
    recordExecutionTelemetry(execution_id, 'vessel_spawned', { vessel_id: vessel.vessel_id, lat: vessel.lat, lon: vessel.lon });

    _log(simLog, 'ENGINE', `SPAWNED ${vessel.vessel_id} at (${vessel.lat}, ${vessel.lon}) speed=${vessel.speed} heading=${vessel.heading}`);
  }

  const afterSpawn = msm.getMaritimeState(sessionId);
  _log(simLog, 'STATE', `After spawn — vessel_count: ${afterSpawn.maritime.vessel_count}`);

  // ── STEP 5: Simulation ticks — deterministic movement ────────────────────
  _log(simLog, 'ENGINE', `Step 5 — Running ${TICKS} simulation ticks`);

  for (let tick = 1; tick <= TICKS; tick++) {
    _log(simLog, 'TICK', `─── Tick ${tick}/${TICKS} ───────────────────────────────`);

    for (const vessel of VESSELS) {
      const current = vesselState[vessel.vessel_id];
      if (current.status === 'anchored') continue;

      const delta = MOVEMENT_DELTAS[vessel.vessel_id];

      // Deterministic position update
      current.lat     = parseFloat((current.lat     + delta.dlat).toFixed(6));
      current.lon     = parseFloat((current.lon     + delta.dlon).toFixed(6));
      current.heading = parseFloat(((current.heading + delta.dheading + 360) % 360).toFixed(2));

      recordJobStarted(execution_id, trace_id, `update_${vessel.vessel_id}_t${tick}`, 'UPDATE_ENTITY');

      const result = msm.applyMaritimeEvent(
        sessionId,
        MARITIME_EVENTS.VESSEL_UPDATED,
        { ...current, timestamp: Date.now() },
        governance
      );

      if (result.success) {
        eventLog.push(_eventEntry(result.event, trace_id, execution_id, 'vessel_updated'));
        recordJobCompleted(execution_id, trace_id, `update_${vessel.vessel_id}_t${tick}`, 'UPDATE_ENTITY', 0);
        recordExecutionTelemetry(execution_id, 'vessel_updated', {
          vessel_id: current.vessel_id, tick,
          lat: current.lat, lon: current.lon, heading: current.heading
        });

        _log(simLog, 'MOVE', `${vessel.vessel_id} → (${current.lat}, ${current.lon}) hdg=${current.heading}`);

        // Log any consequences triggered (zone entry, proximity)
        if (result.consequences && result.consequences.length > 0) {
          result.consequences.forEach(c => {
            _log(simLog, 'CONSEQUENCE', `${c.rule} — ${JSON.stringify(c)}`);
            eventLog.push({ consequence: c, trace_id, execution_id, timestamp: Date.now() });
            recordExecutionTelemetry(execution_id, c.rule, c);
          });
        }
      }
    }

    // Telemetry snapshot per tick
    const tickState = msm.getMaritimeState(sessionId);
    recordExecutionTelemetry(execution_id, `tick_${tick}_state`, {
      vessel_count: tickState.maritime.vessel_count,
      alert_count:  tickState.maritime.alert_count,
      transitions:  tickState.maritime.transitions.length
    });
  }

  // ── STEP 6: Stop VESSEL_DELTA (already anchored → mark stopped) ──────────
  _log(simLog, 'ENGINE', 'Step 6 — Stopping VESSEL_DELTA (anchored → stopped)');
  const stopResult = msm.applyMaritimeEvent(
    sessionId,
    MARITIME_EVENTS.VESSEL_STOPPED,
    { vessel_id: 'VESSEL_DELTA', lat: VESSELS[3].lat, lon: VESSELS[3].lon },
    governance
  );
  if (stopResult.success) {
    eventLog.push(_eventEntry(stopResult.event, trace_id, execution_id, 'vessel_stopped'));
    _log(simLog, 'STATE', 'VESSEL_DELTA stopped and removed from active tracking');
  }

  // ── STEP 7: Final state snapshot ─────────────────────────────────────────
  _log(simLog, 'STATE', 'Step 7 — Capturing final state');
  const finalState = msm.getMaritimeState(sessionId);

  _log(simLog, 'STATE', `Final vessel_count : ${finalState.maritime.vessel_count}`);
  _log(simLog, 'STATE', `Final alert_count  : ${finalState.maritime.alert_count}`);
  _log(simLog, 'STATE', `Total transitions  : ${finalState.maritime.transitions.length}`);
  _log(simLog, 'STATE', `Total events logged: ${eventLog.length}`);

  // ── STEP 8: Write all 4 bucket artifacts ─────────────────────────────────
  _log(simLog, 'BUCKET', 'Step 8 — Writing bucket artifacts');

  const duration = Date.now() - startTime;
  await bucketWriter.writeExecutionCompletion(trace_id, trace_id, Date.now(), 'completed', duration);
  recordExecutionDuration(execution_id, trace_id, duration, 'completed');

  // Phase 4 — emit: execution_completed
  insightBridge.emitExecutionCompleted(trace_id, execution_id, {
    status:       'completed',
    duration,
    event_count:  eventLog.length,
    vessel_count: finalState.maritime.vessel_count,
    alert_count:  finalState.maritime.alert_count,
    transitions:  finalState.maritime.transitions.length
  });

  const artifacts = await _writeAllArtifacts(trace_id, execution_id, {
    schema:    primarySchema.schema,
    events:    eventLog,
    simLog,
    finalState,
    gateResult
  });

  // ── STEP 9: Print summary ─────────────────────────────────────────────────
  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║     SIMULATION COMPLETE                                  ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`Duration     : ${duration}ms`);
  console.log(`Events logged: ${eventLog.length}`);
  console.log(`Vessels final: ${finalState.maritime.vessel_count}`);
  console.log(`Alerts fired : ${finalState.maritime.alert_count}`);
  console.log(`Transitions  : ${finalState.maritime.transitions.length}`);
  console.log('\nArtifacts written:');
  artifacts.forEach(a => console.log(`  ✓ ${path.basename(a)}`));

  return {
    success:      true,
    trace_id,
    execution_id,
    sessionId,
    duration,
    event_count:  eventLog.length,
    final_state:  finalState,
    artifacts
  };
}

// ─── Artifact writers — BHIV 5-artifact contract ─────────────────────────────

async function _writeAllArtifacts(trace_id, execution_id, data) {
  await fs.mkdir(BUCKET_DIR, { recursive: true });
  const written    = [];
  const written_at = Date.now();
  const envelope   = data.schema.decisionEnvelope || {};
  const gate       = data.gateResult             || {};

  // ── 1. execution_<trace_id>_schema.json ──────────────────────────────────
  // Engine execution contract — includes decision metadata for replay
  const schemaFile = path.join(BUCKET_DIR, `execution_${trace_id}_schema.json`);
  await fs.writeFile(schemaFile, JSON.stringify({
    artifact_type:  'bhiv_execution_schema',
    trace_id,
    execution_id,
    written_at,
    // decision metadata included for replay compatibility
    governance: {
      decision:       envelope.decision,
      risk_level:     envelope.risk_level,
      mitra_trace_id: envelope.mitra_trace_id,
      decided_at:     envelope.decided_at
    },
    schema: data.schema
  }, null, 2));
  written.push(schemaFile);
  console.log(`[BUCKET] ✓ execution_${trace_id}_schema.json`);

  // ── 2. execution_<trace_id>_decision.json ────────────────────────────────
  // Full decision + enforcement record — NEW artifact required by BHIV contract
  const decisionFile = path.join(BUCKET_DIR, `execution_${trace_id}_decision.json`);
  await fs.writeFile(decisionFile, JSON.stringify({
    artifact_type:  'bhiv_decision_record',
    trace_id,
    execution_id,
    written_at,
    decision_envelope: {
      decision:       envelope.decision,
      risk_level:     envelope.risk_level,
      confidence:     envelope.confidence,
      reason:         envelope.reason,
      signal_type:    envelope.signal_type,
      mitra_trace_id: envelope.mitra_trace_id,
      your_trace_id:  envelope.your_trace_id,
      decided_at:     envelope.decided_at
    },
    enforcement_result: {
      passed:   gate.passed,
      blocked:  gate.blocked,
      flagged:  gate.flagged,
      decision: gate.decision,
      reason:   gate.reason,
      code:     gate.code || null
    }
  }, null, 2));
  written.push(decisionFile);
  console.log(`[BUCKET] ✓ execution_${trace_id}_decision.json`);

  // ── 3. execution_<trace_id>_events.jsonl ─────────────────────────────────
  // Runtime events + InsightBridge telemetry stream — newline-delimited
  const eventsFile  = path.join(BUCKET_DIR, `execution_${trace_id}_events.jsonl`);
  const ibEvents    = insightBridge.getStream(trace_id);
  const allEvents   = [
    ...data.events,
    ...ibEvents.map(e => ({ ...e, source: 'insightBridge' }))
  ];
  await fs.writeFile(eventsFile, allEvents.map(e => JSON.stringify(e)).join('\n') + '\n');
  written.push(eventsFile);
  console.log(`[BUCKET] ✓ execution_${trace_id}_events.jsonl (${allEvents.length} events — ${data.events.length} runtime + ${ibEvents.length} telemetry)`);

  // ── 4. execution_<trace_id>_state.json ───────────────────────────────────
  // Final state snapshot — includes decision metadata for replay
  const stateFile = path.join(BUCKET_DIR, `execution_${trace_id}_state.json`);
  await fs.writeFile(stateFile, JSON.stringify({
    artifact_type: 'bhiv_final_state',
    trace_id,
    execution_id,
    written_at,
    governance: {
      decision:       envelope.decision,
      risk_level:     envelope.risk_level,
      mitra_trace_id: envelope.mitra_trace_id
    },
    state: data.finalState
  }, null, 2));
  written.push(stateFile);
  console.log(`[BUCKET] ✓ execution_${trace_id}_state.json`);

  // ── 5. execution_<trace_id>_log.jsonl ────────────────────────────────────
  // Simulation log — newline-delimited, replay compatible
  const logFile = path.join(BUCKET_DIR, `execution_${trace_id}_log.jsonl`);
  await fs.writeFile(logFile, data.simLog.map(e => JSON.stringify(e)).join('\n') + '\n');
  written.push(logFile);
  console.log(`[BUCKET] ✓ execution_${trace_id}_log.jsonl (${data.simLog.length} entries)`);

  return written;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _eventEntry(runtimeEvent, trace_id, execution_id, maritime_event) {
  return {
    event_id:       runtimeEvent.event_id,
    event_type:     runtimeEvent.event_type,
    maritime_event,
    timestamp:      runtimeEvent.timestamp,
    entities:       runtimeEvent.entities,
    context:        runtimeEvent.context,
    trace_id,
    execution_id
  };
}

function _log(simLog, stage, message) {
  const entry = { stage, message, timestamp: Date.now() };
  simLog.push(entry);
  console.log(`[${stage.padEnd(11)}] ${message}`);
}

// ─── Entry point ──────────────────────────────────────────────────────────────

if (require.main === module) {
  runSimulation()
    .then(result => {
      console.log('\n[RUNNER] Simulation result:', JSON.stringify({
        success:      result.success,
        trace_id:     result.trace_id,
        execution_id: result.execution_id,
        duration:     result.duration,
        event_count:  result.event_count,
        vessel_count: result.final_state.maritime.vessel_count,
        alert_count:  result.final_state.maritime.alert_count,
        transitions:  result.final_state.maritime.transitions.length,
        artifacts:    result.artifacts.map(a => path.basename(a))
      }, null, 2));
      process.exit(0);
    })
    .catch(err => {
      console.error('[RUNNER] Fatal error:', err.message);
      process.exit(1);
    });
}

module.exports = { runSimulation };

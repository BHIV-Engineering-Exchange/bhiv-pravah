'use strict';

/**
 * replayEngine.js
 *
 * Pure artifact-driven replay engine.
 *
 * Reads 5 artifacts from bucket_artifacts/:
 *   execution_<trace_id>_schema.json
 *   execution_<trace_id>_decision.json
 *   execution_<trace_id>_events.jsonl
 *   execution_<trace_id>_state.json
 *   execution_<trace_id>_log.jsonl
 *
 * Validates:
 *   - All artifacts present and parseable
 *   - trace_id consistent across every artifact and every line
 *   - Event sequence: decision_received → enforcement_applied → execution_started → execution_completed
 *   - Decision correctness: schema governance matches decision artifact
 *   - State trace_id matches
 *
 * Returns ReplayResult — never throws.
 */

const fs   = require('fs').promises;
const path = require('path');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

// Required pipeline event stages in order (from insightBridge telemetry in events.jsonl)
const REQUIRED_STAGE_SEQUENCE = [
  'decision_received',
  'enforcement_applied',
  'execution_started',
  'execution_completed'
];

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Replay a pipeline execution from its bucket artifacts.
 *
 * @param {string} trace_id
 * @returns {Promise<ReplayResult>}
 */
async function replay(trace_id) {
  if (!trace_id) {
    return _fail('MISSING_TRACE_ID', 'trace_id is required', [], trace_id);
  }

  const replayLog = [];
  const _log = (stage, message, meta = {}) => {
    replayLog.push({ stage, message, meta, replayed_at: Date.now() });
    console.log(`[REPLAY:${stage.padEnd(14)}] ${message}`);
  };

  _log('START', `Replaying trace_id=${trace_id}`);

  // ── Step 1: Load all 5 artifacts ─────────────────────────────────────────
  _log('LOAD', 'Loading artifacts from bucket');
  let artifacts;
  try {
    artifacts = await _loadArtifacts(trace_id);
  } catch (err) {
    return _fail('ARTIFACT_LOAD_FAILED', err.message, replayLog, trace_id);
  }
  _log('LOAD', `All 5 artifacts loaded`);

  const { schema, decision, events, state, log } = artifacts;

  // ── Step 2: Validate trace_id consistency ─────────────────────────────────
  _log('VALIDATE', 'Checking trace_id consistency across all artifacts');
  const traceErrors = _validateTraceConsistency(trace_id, schema, decision, events, state, log);
  if (traceErrors.length > 0) {
    _log('VALIDATE', `trace_id mismatches: ${traceErrors.length}`);
    return _fail('TRACE_MISMATCH', traceErrors.join('; '), replayLog, trace_id, {
      mismatches: traceErrors
    });
  }
  _log('VALIDATE', 'trace_id consistent across all artifacts');

  // ── Step 3: Reconstruct execution path ───────────────────────────────────
  _log('PATH', 'Reconstructing execution path from decision artifact');
  const pathResult = _reconstructPath(decision);
  _log('PATH', `Execution path: ${pathResult.path} | decision=${pathResult.decision} | passed=${pathResult.passed}`);

  // ── Step 4: Re-emit events in order ──────────────────────────────────────
  _log('EVENTS', `Re-emitting ${events.length} events in timestamp order`);
  const sortedEvents = _sortEvents(events);
  const emitted = [];
  for (const evt of sortedEvents) {
    emitted.push(_emitEvent(evt));
  }
  _log('EVENTS', `Re-emitted ${emitted.length} events`);

  // ── Step 5: Validate event sequence ──────────────────────────────────────
  _log('SEQUENCE', 'Validating pipeline stage sequence');
  const sequenceResult = _validateSequence(sortedEvents, pathResult.path);
  if (!sequenceResult.valid) {
    _log('SEQUENCE', `Sequence invalid: ${sequenceResult.reason}`);
    return _fail('SEQUENCE_INVALID', sequenceResult.reason, replayLog, trace_id, {
      expected: sequenceResult.expected,
      found:    sequenceResult.found,
      missing:  sequenceResult.missing
    });
  }
  _log('SEQUENCE', `Sequence valid — stages: ${sequenceResult.found.join(' → ')}`);

  // ── Step 6: Validate decision correctness ────────────────────────────────
  _log('DECISION', 'Validating decision correctness against schema');
  const decisionResult = _validateDecision(schema, decision);
  if (!decisionResult.valid) {
    _log('DECISION', `Decision mismatch: ${decisionResult.reason}`);
    return _fail('DECISION_MISMATCH', decisionResult.reason, replayLog, trace_id, {
      schema_decision:   decisionResult.schema_decision,
      artifact_decision: decisionResult.artifact_decision
    });
  }
  _log('DECISION', `Decision correct: ${decisionResult.decision} | risk=${decisionResult.risk_level}`);

  // ── Step 7: Validate state trace ─────────────────────────────────────────
  _log('STATE', 'Validating final state');
  const stateResult = _validateState(trace_id, state, pathResult.path);
  if (!stateResult.valid) {
    _log('STATE', `State invalid: ${stateResult.reason}`);
    return _fail('STATE_INVALID', stateResult.reason, replayLog, trace_id);
  }
  _log('STATE', `State valid | execution_id=${stateResult.execution_id}`);

  // ── Complete ──────────────────────────────────────────────────────────────
  _log('COMPLETE', `Replay complete | path=${pathResult.path} | events=${emitted.length}`);

  return {
    success:      true,
    trace_id,
    execution_id: schema.execution_id,
    path:         pathResult.path,
    decision:     decisionResult.decision,
    risk_level:   decisionResult.risk_level,
    event_count:  emitted.length,
    emitted_events: emitted,
    sequence:     sequenceResult.found,
    state_summary: stateResult.summary,
    failure:      null,
    replay_log:   replayLog
  };
}

// ─── Artifact loader ──────────────────────────────────────────────────────────

async function _loadArtifacts(trace_id) {
  const base = path.join(BUCKET_DIR, `execution_${trace_id}`);

  const files = {
    schema:   `${base}_schema.json`,
    decision: `${base}_decision.json`,
    events:   `${base}_events.jsonl`,
    state:    `${base}_state.json`,
    log:      `${base}_log.jsonl`
  };

  // Check all files exist before reading
  const missing = [];
  for (const [key, filepath] of Object.entries(files)) {
    try {
      await fs.access(filepath);
    } catch {
      missing.push(`${key} (${path.basename(filepath)})`);
    }
  }
  if (missing.length > 0) {
    throw new Error(`Missing artifacts: ${missing.join(', ')}`);
  }

  const [schemaRaw, decisionRaw, eventsRaw, stateRaw, logRaw] = await Promise.all([
    fs.readFile(files.schema,   'utf8'),
    fs.readFile(files.decision, 'utf8'),
    fs.readFile(files.events,   'utf8'),
    fs.readFile(files.state,    'utf8'),
    fs.readFile(files.log,      'utf8')
  ]);

  const schema   = _parseJson(schemaRaw,   'schema');
  const decision = _parseJson(decisionRaw, 'decision');
  const state    = _parseJson(stateRaw,    'state');
  const events   = _parseJsonl(eventsRaw,  'events');
  const log      = _parseJsonl(logRaw,     'log');

  // Normalise schema: handle both artifact_type formats
  // bhiv_execution_schema  → uses `contract` key
  // maritime_execution_schema → uses `schema` key
  const schemaBody = schema.contract || schema.schema || null;
  if (!schemaBody) {
    throw new Error('schema artifact has neither `contract` nor `schema` key');
  }

  return {
    schema:   { ...schema, _body: schemaBody },
    decision,
    events,
    state,
    log
  };
}

function _parseJson(raw, label) {
  try {
    return JSON.parse(raw);
  } catch (err) {
    throw new Error(`${label} artifact is not valid JSON: ${err.message}`);
  }
}

function _parseJsonl(raw, label) {
  const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
  const parsed = [];
  for (let i = 0; i < lines.length; i++) {
    try {
      parsed.push(JSON.parse(lines[i]));
    } catch (err) {
      throw new Error(`${label} artifact line ${i + 1} is not valid JSON: ${err.message}`);
    }
  }
  return parsed;
}

// ─── Trace consistency ────────────────────────────────────────────────────────

function _validateTraceConsistency(trace_id, schema, decision, events, state, log) {
  const errors = [];

  // Top-level artifact fields
  if (schema.trace_id   !== trace_id) errors.push(`schema.trace_id="${schema.trace_id}"`);
  if (decision.trace_id !== trace_id) errors.push(`decision.trace_id="${decision.trace_id}"`);
  if (state.trace_id    !== trace_id) errors.push(`state.trace_id="${state.trace_id}"`);

  // decision_envelope.your_trace_id (present in bhiv format)
  const de = decision.decision_envelope;
  if (de && de.your_trace_id && de.your_trace_id !== trace_id) {
    errors.push(`decision_envelope.your_trace_id="${de.your_trace_id}"`);
  }

  // Every event line
  events.forEach((evt, i) => {
    if (evt.trace_id && evt.trace_id !== trace_id) {
      errors.push(`events[${i}].trace_id="${evt.trace_id}"`);
    }
  });

  // Every log line
  log.forEach((entry, i) => {
    if (entry.trace_id && entry.trace_id !== trace_id) {
      errors.push(`log[${i}].trace_id="${entry.trace_id}"`);
    }
  });

  return errors;
}

// ─── Execution path reconstruction ───────────────────────────────────────────

function _reconstructPath(decision) {
  const de = decision.decision_envelope || {};
  const er = decision.enforcement_result || {};

  const rawDecision = de.decision || decision.mitra_decision || 'UNKNOWN';

  if (er.passed === true || rawDecision === 'ALLOW') {
    return { path: 'ALLOW', decision: 'ALLOW', passed: true };
  }
  if (er.flagged === true || rawDecision === 'FLAG') {
    return { path: 'FLAG',  decision: 'FLAG',  passed: false };
  }
  return { path: 'BLOCK', decision: rawDecision, passed: false };
}

// ─── Event ordering and emission ─────────────────────────────────────────────

function _sortEvents(events) {
  return [...events].sort((a, b) => {
    const ta = a.timestamp || a.collected_at || a.buffered_at || 0;
    const tb = b.timestamp || b.collected_at || b.buffered_at || 0;
    return ta - tb;
  });
}

function _emitEvent(evt) {
  // Normalise: insightBridge events use `stage`, eventCollector events use `event_type`
  const type      = evt.stage || evt.event_type || 'unknown';
  const timestamp = evt.timestamp || evt.collected_at || evt.buffered_at || null;
  return { type, timestamp, trace_id: evt.trace_id, payload: evt.metadata || evt.payload || evt.context || {} };
}

// ─── Sequence validation ──────────────────────────────────────────────────────

function _validateSequence(sortedEvents, path) {
  // Extract stage names from insightBridge telemetry lines (have `stage` field + `source: insightBridge`)
  const stageEvents = sortedEvents
    .filter(e => e.source === 'insightBridge' || REQUIRED_STAGE_SEQUENCE.includes(e.stage))
    .map(e => e.stage)
    .filter(Boolean);

  // For ALLOW path all 4 stages required; FLAG/BLOCK stop after enforcement_applied
  const required = path === 'ALLOW'
    ? REQUIRED_STAGE_SEQUENCE
    : ['decision_received', 'enforcement_applied'];

  const missing = required.filter(s => !stageEvents.includes(s));

  if (missing.length > 0) {
    return {
      valid:    false,
      reason:   `Missing required pipeline stages: ${missing.join(', ')}`,
      expected: required,
      found:    stageEvents,
      missing
    };
  }

  // Verify order: each required stage must appear before the next
  for (let i = 0; i < required.length - 1; i++) {
    const idxA = stageEvents.indexOf(required[i]);
    const idxB = stageEvents.indexOf(required[i + 1]);
    if (idxA > idxB) {
      return {
        valid:    false,
        reason:   `Stage order violation: "${required[i]}" appears after "${required[i + 1]}"`,
        expected: required,
        found:    stageEvents,
        missing:  []
      };
    }
  }

  return { valid: true, expected: required, found: stageEvents, missing: [] };
}

// ─── Decision correctness ─────────────────────────────────────────────────────

function _validateDecision(schema, decision) {
  // Extract decision from schema artifact (two formats)
  const schemaDecision =
    schema.governance?.decision ||          // bhiv_execution_schema
    schema.mitra_decision       ||          // maritime_execution_schema
    schema._body?.decisionEnvelope?.decision || // embedded in schema body
    null;

  const artifactDecision =
    decision.decision_envelope?.decision ||
    decision.mitra_decision              ||
    null;

  if (!artifactDecision) {
    return { valid: false, reason: 'decision artifact has no decision field' };
  }

  if (schemaDecision && schemaDecision !== artifactDecision) {
    return {
      valid:             false,
      reason:            `Decision mismatch: schema says "${schemaDecision}", decision artifact says "${artifactDecision}"`,
      schema_decision:   schemaDecision,
      artifact_decision: artifactDecision
    };
  }

  if (!['ALLOW', 'FLAG', 'BLOCK'].includes(artifactDecision)) {
    return { valid: false, reason: `Unknown decision value: "${artifactDecision}"` };
  }

  return {
    valid:      true,
    decision:   artifactDecision,
    risk_level: decision.decision_envelope?.risk_level || null
  };
}

// ─── State validation ─────────────────────────────────────────────────────────

function _validateState(trace_id, state, path) {
  if (state.trace_id !== trace_id) {
    return { valid: false, reason: `state.trace_id="${state.trace_id}" does not match trace_id="${trace_id}"` };
  }

  const stateBody = state.state || {};
  const summary = {
    execution_id: state.execution_id,
    stopped:      stateBody.stopped || false,
    decision:     state.governance?.decision || null
  };

  // ALLOW path: state must not be stopped
  if (path === 'ALLOW' && stateBody.stopped === true) {
    return { valid: false, reason: 'ALLOW path but state.stopped=true — state inconsistent with path' };
  }

  // FLAG/BLOCK path: state must be stopped
  if (path !== 'ALLOW' && stateBody.stopped === false) {
    // Not a hard failure — some older artifacts don't set stopped
    // but we note it in summary
    summary.warning = `${path} path but state.stopped is not true`;
  }

  return { valid: true, execution_id: state.execution_id, summary };
}

// ─── Result builder ───────────────────────────────────────────────────────────

function _fail(failure_code, reason, replayLog, trace_id, meta = {}) {
  console.error(`[REPLAY] ❌ ${failure_code} | trace=${trace_id} | reason=${reason}`);
  return {
    success:        false,
    trace_id:       trace_id || null,
    execution_id:   null,
    path:           null,
    decision:       null,
    risk_level:     null,
    event_count:    0,
    emitted_events: [],
    sequence:       [],
    state_summary:  null,
    failure: {
      failure_code,
      reason,
      meta,
      failed_at: Date.now()
    },
    replay_log: replayLog
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { replay };

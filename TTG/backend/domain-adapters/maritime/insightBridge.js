'use strict';

/**
 * insightBridge.js
 *
 * Phase 5 — Telemetry Emission (Externalized)
 *
 * Emits structured telemetry at every BHIV pipeline stage.
 * Every event is trace-linked: trace_id + execution_id on every record.
 *
 * Stages:
 *   decision_received    — Mitra returned a decisionEnvelope
 *   enforcement_applied  — enforcementGate processed the decision
 *   execution_started    — contract accepted, execution running
 *   execution_completed  — execution finished (success or failure)
 *
 * Transports (all non-blocking, failures logged but never crash the pipeline):
 *   1. In-memory stream  — keyed by trace_id, replayable
 *   2. File transport    — appends each event to telemetry_<trace_id>.jsonl
 *   3. HTTP transport    — POSTs each event to TELEMETRY_HTTP_ENDPOINT (if set)
 *
 * Rules:
 *   - trace_id missing  → event NOT emitted, error logged
 *   - execution_id missing → event NOT emitted, error logged
 *   - File/HTTP failures → logged, pipeline continues (non-fatal)
 *   - Every event has: telemetry_id, trace_id, execution_id, stage, timestamp, metadata
 */

const fs   = require('fs');
const path = require('path');
const http = require('http');
const { v4: uuidv4 } = require('uuid');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

// ─── In-memory stream ─────────────────────────────────────────────────────────
const _stream = new Map(); // trace_id → Array of events

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Emit: decision_received
 * @param {string} trace_id
 * @param {string} execution_id
 * @param {Object} decisionEnvelope
 */
function emitDecisionReceived(trace_id, execution_id, decisionEnvelope) {
  return _emit(trace_id, execution_id, 'decision_received', {
    decision:       decisionEnvelope.decision,
    risk_level:     decisionEnvelope.risk_level,
    confidence:     decisionEnvelope.confidence,
    reason:         decisionEnvelope.reason,
    mitra_trace_id: decisionEnvelope.mitra_trace_id,
    signal_type:    decisionEnvelope.signal_type,
    source:         decisionEnvelope.source,
    decided_at:     decisionEnvelope.decided_at
  });
}

/**
 * Emit: enforcement_applied
 * @param {string} trace_id
 * @param {string} execution_id
 * @param {Object} gateResult  - Output of enforcementGate.enforce()
 */
function emitEnforcementApplied(trace_id, execution_id, gateResult) {
  return _emit(trace_id, execution_id, 'enforcement_applied', {
    passed:      gateResult.passed,
    blocked:     gateResult.blocked,
    flagged:     gateResult.flagged,
    decision:    gateResult.decision,
    reason:      gateResult.reason,
    source:      gateResult.source   || null,
    enforced_at: gateResult.enforced_at || null,
    code:        gateResult.code     || null
  });
}

/**
 * Emit: execution_started
 * @param {string} trace_id
 * @param {string} execution_id
 * @param {Object} metadata
 */
function emitExecutionStarted(trace_id, execution_id, metadata = {}) {
  return _emit(trace_id, execution_id, 'execution_started', metadata);
}

/**
 * Emit: execution_completed
 * @param {string} trace_id
 * @param {string} execution_id
 * @param {Object} metadata
 */
function emitExecutionCompleted(trace_id, execution_id, metadata = {}) {
  return _emit(trace_id, execution_id, 'execution_completed', metadata);
}

const VALID_STAGES = new Set([
  'decision_received',
  'enforcement_applied',
  'execution_started',
  'execution_completed'
]);

/**
 * Get all events for a trace_id (snapshot — immutable).
 * @param {string} trace_id
 * @returns {Array}
 */
function getStream(trace_id) {
  return _stream.has(trace_id) ? [..._stream.get(trace_id)] : [];
}

/**
 * Get all events across all traces.
 * @returns {Array}
 */
function getAllEvents() {
  const all = [];
  for (const events of _stream.values()) all.push(...events);
  return all;
}

/**
 * Query telemetry for a trace_id.
 * Merges in-memory stream with persisted file, deduplicates by telemetry_id,
 * sorts by timestamp ascending.
 *
 * @param {string} trace_id
 * @param {Object} [opts]
 * @param {string} [opts.stage]  — filter to a single stage
 * @returns {{ found, trace_id, events, stages_present, trace_consistent, source }}
 */
function query(trace_id, opts = {}) {
  if (!trace_id) {
    return { found: false, trace_id: null, events: [], stages_present: [],
             trace_consistent: true, source: 'none',
             error: 'trace_id is required' };
  }

  // ── Collect from in-memory ────────────────────────────────────────────────
  const memEvents = _stream.has(trace_id) ? [..._stream.get(trace_id)] : [];

  // ── Collect from file ─────────────────────────────────────────────────────
  const fileEvents = _readFromFile(trace_id);

  // ── Merge + deduplicate by telemetry_id ───────────────────────────────────
  const seen = new Set();
  const merged = [];
  for (const evt of [...fileEvents, ...memEvents]) {
    if (!seen.has(evt.telemetry_id)) {
      seen.add(evt.telemetry_id);
      merged.push(evt);
    }
  }

  if (merged.length === 0) {
    return { found: false, trace_id, events: [], stages_present: [],
             trace_consistent: true, source: 'none' };
  }

  // ── Sort by timestamp ascending ───────────────────────────────────────────
  merged.sort((a, b) => a.timestamp - b.timestamp);

  // ── Trace consistency check ───────────────────────────────────────────────
  const mismatches = merged.filter(e => e.trace_id !== trace_id);
  const trace_consistent = mismatches.length === 0;

  // ── Stage filter ─────────────────────────────────────────────────────────
  const { stage } = opts;
  if (stage !== undefined) {
    if (!VALID_STAGES.has(stage)) {
      return { found: false, trace_id, events: [], stages_present: [],
               trace_consistent, source: 'none',
               error: `Unknown stage: "${stage}". Valid: ${[...VALID_STAGES].join(', ')}` };
    }
  }
  const events = stage ? merged.filter(e => e.stage === stage) : merged;

  // ── Stages present in full (unfiltered) set ───────────────────────────────
  const stages_present = [...new Set(merged.map(e => e.stage))];

  // ── Source label ─────────────────────────────────────────────────────────
  const source = memEvents.length > 0 && fileEvents.length > 0 ? 'memory+file'
               : memEvents.length > 0 ? 'memory'
               : 'file';

  return { found: true, trace_id, events, stages_present, trace_consistent, source,
           total: merged.length, filtered: events.length };
}

/**
 * Read persisted telemetry from file for a trace_id.
 * Returns [] if file does not exist — never throws.
 * @param {string} trace_id
 * @returns {Array}
 */
function _readFromFile(trace_id) {
  const filePath = path.join(BUCKET_DIR, `telemetry_${trace_id}.jsonl`);
  try {
    const raw   = fs.readFileSync(filePath, 'utf8');
    const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
    const events = [];
    for (const line of lines) {
      try { events.push(JSON.parse(line)); } catch { /* skip corrupt line */ }
    }
    return events;
  } catch (err) {
    if (err.code !== 'ENOENT') {
      console.error(`[INSIGHTBRIDGE] ⚠ Could not read telemetry file for trace=${trace_id}: ${err.message}`);
    }
    return [];
  }
}

/**
 * Clear stream — testing only.
 * @param {string} [trace_id]
 */
function _clearStream(trace_id) {
  if (trace_id) _stream.delete(trace_id);
  else          _stream.clear();
}

// ─── Core emit ────────────────────────────────────────────────────────────────

function _emit(trace_id, execution_id, stage, metadata) {
  // ── Guards ────────────────────────────────────────────────────────────────
  if (!trace_id) {
    console.error(`[INSIGHTBRIDGE] ❌ trace_id missing on stage: ${stage} — event NOT emitted`);
    return null;
  }
  if (!execution_id) {
    console.error(`[INSIGHTBRIDGE] ❌ execution_id missing on stage: ${stage} — event NOT emitted`);
    return null;
  }

  // ── Build event ───────────────────────────────────────────────────────────
  const event = {
    telemetry_id: uuidv4(),
    trace_id,
    execution_id,
    stage,
    timestamp:    Date.now(),
    metadata:     metadata || {}
  };

  // ── Transport 1: in-memory ────────────────────────────────────────────────
  if (!_stream.has(trace_id)) _stream.set(trace_id, []);
  _stream.get(trace_id).push(event);

  console.log(`[INSIGHTBRIDGE] stage=${stage} | trace=${trace_id} | execution=${execution_id} | id=${event.telemetry_id}`);

  // ── Transport 2: file (non-blocking) ─────────────────────────────────────
  _writeToFile(trace_id, event);

  // ── Transport 3: HTTP (non-blocking, only if endpoint configured) ─────────
  _postToEndpoint(event);

  return event;
}

// ─── Transport 2: File ────────────────────────────────────────────────────────

function _writeToFile(trace_id, event) {
  try {
    if (!fs.existsSync(BUCKET_DIR)) fs.mkdirSync(BUCKET_DIR, { recursive: true });
    const filePath = path.join(BUCKET_DIR, `telemetry_${trace_id}.jsonl`);
    fs.appendFileSync(filePath, JSON.stringify(event) + '\n');
  } catch (err) {
    // Non-fatal — log and continue
    console.error(`[INSIGHTBRIDGE] ⚠ File transport failed for trace=${trace_id}: ${err.message}`);
  }
}

// ─── Transport 3: HTTP ────────────────────────────────────────────────────────

function _postToEndpoint(event) {
  const endpoint = process.env.TELEMETRY_HTTP_ENDPOINT;
  if (!endpoint) return; // not configured — skip silently

  let url;
  try {
    url = new URL(endpoint);
  } catch {
    console.error(`[INSIGHTBRIDGE] ⚠ Invalid TELEMETRY_HTTP_ENDPOINT: ${endpoint}`);
    return;
  }

  const payload = JSON.stringify(event);

  const options = {
    hostname: url.hostname,
    port:     url.port || 80,
    path:     url.pathname,
    method:   'POST',
    headers: {
      'Content-Type':   'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'X-Trace-Id':     event.trace_id,
      'X-Execution-Id': event.execution_id,
      'X-Stage':        event.stage
    }
  };

  const req = http.request(options, (res) => {
    if (res.statusCode !== 200 && res.statusCode !== 204) {
      console.error(`[INSIGHTBRIDGE] ⚠ HTTP transport returned ${res.statusCode} for stage=${event.stage}`);
    }
    // drain response body
    res.resume();
  });

  req.setTimeout(3000, () => {
    req.destroy();
    console.error(`[INSIGHTBRIDGE] ⚠ HTTP transport timed out for stage=${event.stage}`);
  });

  req.on('error', (err) => {
    // Non-fatal — pipeline continues
    console.error(`[INSIGHTBRIDGE] ⚠ HTTP transport error for stage=${event.stage}: ${err.message}`);
  });

  req.write(payload);
  req.end();
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  emitDecisionReceived,
  emitEnforcementApplied,
  emitExecutionStarted,
  emitExecutionCompleted,
  getStream,
  getAllEvents,
  query,
  VALID_STAGES,
  _clearStream
};

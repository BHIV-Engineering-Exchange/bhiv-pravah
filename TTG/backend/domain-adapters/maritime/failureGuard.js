'use strict';

/**
 * failureGuard.js
 *
 * Phase 7 — Failure Hardening
 *
 * Single authoritative failure handler for the entire pipeline.
 * Every failure case is:
 *   - Explicitly named (failure_code)
 *   - Classified by stage (where in the pipeline it occurred)
 *   - Trace-linked (trace_id always present)
 *   - Structured (FailureResult — same shape every time)
 *   - Logged immediately (no silent behavior)
 *
 * Failure codes:
 *   MISSING_TRACE_ID        — trace_id absent anywhere in pipeline
 *   DECISION_NOT_ALLOW      — Mitra returned FLAG or BLOCK → no execution
 *   MITRA_UNREACHABLE       — Mitra endpoint down, stub disabled
 *   MITRA_INVALID_RESPONSE  — Mitra returned malformed/unknown response
 *   ENFORCEMENT_BLOCKED     — enforcementGate blocked execution
 *   ENFORCEMENT_FLAGGED     — enforcementGate flagged execution
 *   STUB_DECISION           — stub decision reached gate (never allowed)
 *   CONTRACT_BUILD_FAILED   — contractBuilder rejected the schema
 *   EXECUTION_REJECTED      — execution layer returned contract_rejected
 *   EXECUTION_UNREACHABLE   — execution layer endpoint down
 *   EVENT_STREAM_BROKEN     — eventCollector received invalid/missing event
 *   EVENT_STREAM_INCOMPLETE — execution_completed never arrived
 *   UNKNOWN                 — unclassified error (always explicit, never silent)
 */

// ─── Failure codes ────────────────────────────────────────────────────────────

const FAILURE_CODES = {
  MISSING_TRACE_ID:        'MISSING_TRACE_ID',
  DECISION_NOT_ALLOW:      'DECISION_NOT_ALLOW',
  MITRA_UNREACHABLE:       'MITRA_UNREACHABLE',
  MITRA_INVALID_RESPONSE:  'MITRA_INVALID_RESPONSE',
  ENFORCEMENT_BLOCKED:     'ENFORCEMENT_BLOCKED',
  ENFORCEMENT_FLAGGED:     'ENFORCEMENT_FLAGGED',
  STUB_DECISION:           'STUB_DECISION',
  CONTRACT_BUILD_FAILED:   'CONTRACT_BUILD_FAILED',
  EXECUTION_REJECTED:      'EXECUTION_REJECTED',
  EXECUTION_UNREACHABLE:   'EXECUTION_UNREACHABLE',
  EVENT_STREAM_BROKEN:     'EVENT_STREAM_BROKEN',
  EVENT_STREAM_INCOMPLETE: 'EVENT_STREAM_INCOMPLETE',
  UNKNOWN:                 'UNKNOWN'
};

// Stage each code belongs to
const CODE_STAGE = {
  MISSING_TRACE_ID:        'input',
  DECISION_NOT_ALLOW:      'decision',
  MITRA_UNREACHABLE:       'decision',
  MITRA_INVALID_RESPONSE:  'decision',
  ENFORCEMENT_BLOCKED:     'enforcement',
  ENFORCEMENT_FLAGGED:     'enforcement',
  STUB_DECISION:           'enforcement',
  CONTRACT_BUILD_FAILED:   'contract',
  EXECUTION_REJECTED:      'execution',
  EXECUTION_UNREACHABLE:   'execution',
  EVENT_STREAM_BROKEN:     'event_stream',
  EVENT_STREAM_INCOMPLETE: 'event_stream',
  UNKNOWN:                 'unknown'
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Assert trace_id is present. Call at the very start of every pipeline entry point.
 * @param {string} trace_id
 * @param {string} [execution_id]
 * @returns {FailureResult|null}  null = OK, FailureResult = stop immediately
 */
function assertTraceId(trace_id, execution_id) {
  if (!trace_id) {
    return _fail(FAILURE_CODES.MISSING_TRACE_ID, 'input',
      'trace_id is missing — pipeline cannot proceed without it',
      null, execution_id || null);
  }
  return null;
}

/**
 * Evaluate the result of mitraClient.evaluate().
 * Returns a FailureResult if the decision is not ALLOW or if Mitra failed.
 *
 * @param {Object} mitraResult  - { success, envelope, error }
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult|null}
 */
function checkMitraResult(mitraResult, trace_id, execution_id) {
  if (!mitraResult.success) {
    const code = (mitraResult.error || '').includes('unreachable')
      ? FAILURE_CODES.MITRA_UNREACHABLE
      : FAILURE_CODES.MITRA_INVALID_RESPONSE;
    return _fail(code, 'decision',
      mitraResult.error || 'Mitra evaluation failed',
      trace_id, execution_id);
  }

  const decision = mitraResult.envelope?.decision;
  if (decision !== 'ALLOW') {
    const code = decision === 'FLAG'
      ? FAILURE_CODES.DECISION_NOT_ALLOW
      : FAILURE_CODES.DECISION_NOT_ALLOW;
    return _fail(code, 'decision',
      `Decision is ${decision} — execution will not proceed. Reason: ${mitraResult.envelope?.reason}`,
      trace_id, execution_id,
      { decision, risk_level: mitraResult.envelope?.risk_level, reason: mitraResult.envelope?.reason });
  }

  return null; // ALLOW — proceed
}

/**
 * Evaluate the result of enforcementGate.enforce().
 * Returns a FailureResult if gate did not pass.
 *
 * @param {Object} gateResult  - Output of enforcementGate.enforce()
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult|null}
 */
function checkGateResult(gateResult, trace_id, execution_id) {
  if (gateResult.passed) return null; // gate passed — proceed

  if (gateResult.code === 'STUB_DECISION') {
    return _fail(FAILURE_CODES.STUB_DECISION, 'enforcement',
      gateResult.reason, trace_id, execution_id,
      { gate_code: gateResult.code });
  }

  if (gateResult.flagged) {
    return _fail(FAILURE_CODES.ENFORCEMENT_FLAGGED, 'enforcement',
      gateResult.reason, trace_id, execution_id,
      { gate_code: gateResult.code || null, decision: gateResult.decision });
  }

  return _fail(FAILURE_CODES.ENFORCEMENT_BLOCKED, 'enforcement',
    gateResult.reason, trace_id, execution_id,
    { gate_code: gateResult.code || null, decision: gateResult.decision });
}

/**
 * Evaluate the result of contractBuilder.build().
 * Returns a FailureResult if contract could not be built.
 *
 * @param {Object} buildResult  - { success, contract, errors }
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult|null}
 */
function checkContractBuild(buildResult, trace_id, execution_id) {
  if (buildResult.success) return null;
  return _fail(FAILURE_CODES.CONTRACT_BUILD_FAILED, 'contract',
    `Contract build failed: ${buildResult.errors.join(', ')}`,
    trace_id, execution_id,
    { errors: buildResult.errors });
}

/**
 * Evaluate the result of executionClient.submit().
 * Returns a FailureResult if execution was rejected or unreachable.
 *
 * @param {Object} submitResult  - { success, status, reason?, error?, code? }
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult|null}
 */
function checkExecutionResult(submitResult, trace_id, execution_id) {
  if (submitResult.success) return null;

  const code = submitResult.code === 'UNREACHABLE'
    ? FAILURE_CODES.EXECUTION_UNREACHABLE
    : FAILURE_CODES.EXECUTION_REJECTED;

  return _fail(code, 'execution',
    submitResult.reason || submitResult.error || 'Execution layer rejected the contract',
    trace_id, execution_id,
    { submit_code: submitResult.code || null, status: submitResult.status });
}

/**
 * Validate an incoming event from the event stream.
 * Returns a FailureResult if the event is broken (missing required fields).
 *
 * @param {Object} event        - Raw event from Atharva's execution layer
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult|null}
 */
function checkIncomingEvent(event, trace_id, execution_id) {
  if (!event || typeof event !== 'object') {
    return _fail(FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream',
      'Received null or non-object event from execution layer',
      trace_id, execution_id);
  }

  const missing = [];
  if (!event.event_type)  missing.push('event_type');
  if (!event.trace_id)    missing.push('trace_id');

  if (missing.length > 0) {
    return _fail(FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream',
      `Event missing required fields: ${missing.join(', ')}`,
      trace_id, execution_id,
      { received: event });
  }

  // trace_id mismatch — event from wrong execution
  if (event.trace_id !== trace_id) {
    return _fail(FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream',
      `Event trace_id mismatch: expected ${trace_id}, got ${event.trace_id}`,
      trace_id, execution_id,
      { expected_trace: trace_id, received_trace: event.trace_id });
  }

  return null; // event is valid
}

/**
 * Assert the event stream completed (execution_completed was received).
 * Returns a FailureResult if the stream never completed.
 *
 * @param {boolean} isComplete
 * @param {string}  trace_id
 * @param {string}  execution_id
 * @returns {FailureResult|null}
 */
function checkStreamComplete(isComplete, trace_id, execution_id) {
  if (isComplete) return null;
  return _fail(FAILURE_CODES.EVENT_STREAM_INCOMPLETE, 'event_stream',
    'execution_completed event never received — stream is incomplete',
    trace_id, execution_id);
}

/**
 * Wrap an unexpected/unclassified error into a FailureResult.
 * Ensures nothing is ever silent.
 *
 * @param {Error|string} err
 * @param {string} stage
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {FailureResult}
 */
function fromError(err, stage, trace_id, execution_id) {
  const message = err instanceof Error ? err.message : String(err);
  return _fail(FAILURE_CODES.UNKNOWN, stage || 'unknown',
    `Unclassified error: ${message}`, trace_id, execution_id);
}

// ─── Internal ─────────────────────────────────────────────────────────────────

/**
 * Build a FailureResult and log it immediately.
 * @returns {FailureResult}
 */
function _fail(failure_code, stage, reason, trace_id, execution_id, meta = {}) {
  const now = Date.now();
  const result = {
    failed:       true,
    failure_code,
    stage:        stage || CODE_STAGE[failure_code] || 'unknown',
    reason,
    trace_id:     trace_id     || null,
    execution_id: execution_id || null,
    stopped_at:   now,
    failed_at:    now,
    meta
  };

  console.error(
    `[FAILURE_GUARD] ❌ ${failure_code} | stage=${result.stage} | trace=${result.trace_id} | reason=${reason}`
  );

  return result;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  FAILURE_CODES,
  assertTraceId,
  checkMitraResult,
  checkGateResult,
  checkContractBuild,
  checkExecutionResult,
  checkIncomingEvent,
  checkStreamComplete,
  fromError
};

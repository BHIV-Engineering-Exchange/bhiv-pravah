'use strict';

/**
 * enforcementGate.js
 *
 * Phase 2 — Enforcement Gate
 *
 * Separates decision from execution.
 * Reads the decisionEnvelope produced by mitraClient.
 * Makes NO decisions — only enforces what Mitra decided.
 *
 * Rules (Phase 2 — non-negotiable):
 *   ALLOW  → passed=true, execution may proceed
 *   FLAG   → passed=false, execution STOPS, logged
 *   BLOCK  → passed=false, execution STOPS, terminated
 *
 * Fail-closed (any ambiguity → BLOCK):
 *   Missing decisionEnvelope → BLOCK
 *   Missing decision field   → BLOCK
 *   Unknown decision value   → BLOCK
 *   source === 'stub'        → BLOCK (stub decisions never reach execution)
 */

const _flagLog = [];

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Enforce the governance decision on the schema.
 * This is the ONLY entry point — nothing bypasses this.
 *
 * @param {Object} schema  - Schema with decisionEnvelope attached
 * @returns {{ passed, blocked, flagged, decision, reason, source, enforced_at, code?, trace_id, execution_id }}
 */
function enforce(schema) {
  const trace_id     = schema.trace_id     || 'unknown';
  const execution_id = schema.execution_id || 'unknown';

  // ── Fail-closed: no envelope → BLOCK ─────────────────────────────────────
  if (!schema.decisionEnvelope) {
    return _block(trace_id, execution_id, 'NO_ENVELOPE',
      'decisionEnvelope is missing — no governance decision was attached');
  }

  const { decision, risk_level, reason, mitra_trace_id, source } = schema.decisionEnvelope;

  // ── Fail-closed: stub decision never reaches execution ────────────────────
  if (source === 'stub') {
    return _block(trace_id, execution_id, 'STUB_DECISION',
      'Decision source is stub — real Mitra decision required for execution');
  }

  // ── Fail-closed: missing decision → BLOCK ────────────────────────────────
  if (!decision) {
    return _block(trace_id, execution_id, 'NO_DECISION',
      'decision field is missing from decisionEnvelope');
  }

  // ── Fail-closed: unknown decision value → BLOCK ───────────────────────────
  if (!['ALLOW', 'FLAG', 'BLOCK'].includes(decision)) {
    return _block(trace_id, execution_id, 'UNKNOWN_DECISION',
      `Unknown decision value: "${decision}" — failing closed`);
  }

  // ── ALLOW ─────────────────────────────────────────────────────────────────
  if (decision === 'ALLOW') {
    console.log(`[ENFORCEMENT] ✅ ALLOW | trace=${trace_id} | risk=${risk_level} | source=${source} | mitra_trace=${mitra_trace_id}`);
    return {
      passed:      true,
      blocked:     false,
      flagged:     false,
      decision:    'ALLOW',
      reason:      reason || 'Governance decision: ALLOW',
      source,
      enforced_at: Date.now(),
      trace_id,
      execution_id
    };
  }

  // ── FLAG — execution STOPS ────────────────────────────────────────────────
  if (decision === 'FLAG') {
    const entry = {
      trace_id,
      execution_id,
      mitra_trace_id,
      risk_level,
      source,
      reason:     reason || 'Flagged for monitoring',
      flagged_at: Date.now()
    };
    _flagLog.push(entry);

    console.warn(`[ENFORCEMENT] ⚠ FLAG | trace=${trace_id} | risk=${risk_level} | source=${source} | reason=${entry.reason}`);
    console.warn(`[ENFORCEMENT] Execution STOPPED — FLAG does not proceed (${_flagLog.length} total flags)`);

    return {
      passed:      false,
      blocked:     false,
      flagged:     true,
      decision:    'FLAG',
      reason:      entry.reason,
      source,
      enforced_at: Date.now(),
      trace_id,
      execution_id
    };
  }

  // ── BLOCK ─────────────────────────────────────────────────────────────────
  return _block(trace_id, execution_id, 'POLICY_VIOLATION',
    reason || 'Governance decision: BLOCK — execution terminated');
}

/**
 * Return all flagged entries (for telemetry + bucket artifacts).
 * @returns {Array}
 */
function getFlagLog() {
  return [..._flagLog];
}

/**
 * Clear flag log — testing only.
 */
function _clearFlagLog() {
  _flagLog.length = 0;
}

// ─── Internal ─────────────────────────────────────────────────────────────────

function _block(trace_id, execution_id, code, reason) {
  console.error(`[ENFORCEMENT] 🚫 BLOCK | trace=${trace_id} | code=${code} | reason=${reason}`);
  return {
    passed:      false,
    blocked:     true,
    flagged:     false,
    decision:    'BLOCK',
    code,
    reason,
    enforced_at: Date.now(),
    trace_id,
    execution_id
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { enforce, getFlagLog, _clearFlagLog };

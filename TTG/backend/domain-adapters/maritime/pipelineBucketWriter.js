'use strict';

/**
 * pipelineBucketWriter.js
 *
 * Phase 6 — Bucket Artifacts (Replay Ready)
 *
 * Produces all 5 BHIV-compliant artifacts for a single pipeline execution.
 * Buffer-then-flush: NOTHING is written to disk until flush() is called.
 *
 * Artifacts produced on flush():
 *   execution_<trace_id>_schema.json    — contract-locked execution schema
 *   execution_<trace_id>_decision.json  — Mitra decision + enforcement result
 *   execution_<trace_id>_events.jsonl   — runtime events + telemetry stream
 *   execution_<trace_id>_state.json     — final state snapshot
 *   execution_<trace_id>_log.jsonl      — pipeline log entries
 *
 * Rules:
 *   - NO file I/O before flush() — all data lives in memory buffers
 *   - flush() is called ONCE on pipeline completion
 *   - flush() is atomic — all 5 files written in one pass
 *   - trace_id missing → every operation throws immediately
 *   - Each writer instance is isolated to one trace_id
 */

const fs   = require('fs').promises;
const path = require('path');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

// ─── Factory ──────────────────────────────────────────────────────────────────

/**
 * Create a new buffer for one pipeline execution.
 *
 * @param {string} trace_id
 * @param {string} execution_id
 * @returns {PipelineBucketWriter}
 */
function create(trace_id, execution_id) {
  if (!trace_id)     throw new Error('[BUCKET_WRITER] trace_id is required');
  if (!execution_id) throw new Error('[BUCKET_WRITER] execution_id is required');

  return new PipelineBucketWriter(trace_id, execution_id);
}

// ─── PipelineBucketWriter ─────────────────────────────────────────────────────

class PipelineBucketWriter {
  constructor(trace_id, execution_id) {
    this.trace_id     = trace_id;
    this.execution_id = execution_id;
    this._flushed     = false;

    // In-memory buffers — nothing written to disk until flush()
    this._schema   = null;   // object  → schema.json
    this._decision = null;   // object  → decision.json
    this._events   = [];     // array   → events.jsonl  (append)
    this._state    = null;   // object  → state.json
    this._log      = [];     // array   → log.jsonl     (append)
  }

  // ── Buffer: schema ──────────────────────────────────────────────────────────

  /**
   * Set the execution schema (contract-locked output of contractBuilder).
   * @param {Object} contract  - Output of contractBuilder.build().contract
   * @param {Object} governance - { decision, risk_level, mitra_trace_id, decided_at }
   */
  setSchema(contract, governance = {}) {
    this._assertNotFlushed('setSchema');
    this._schema = {
      artifact_type: 'bhiv_execution_schema',
      trace_id:      this.trace_id,
      execution_id:  this.execution_id,
      buffered_at:   Date.now(),
      governance: {
        decision:       governance.decision       || null,
        risk_level:     governance.risk_level     || null,
        mitra_trace_id: governance.mitra_trace_id || null,
        decided_at:     governance.decided_at     || null
      },
      contract
    };
  }

  // ── Buffer: decision ────────────────────────────────────────────────────────

  /**
   * Set the decision + enforcement record.
   * @param {Object} decisionEnvelope  - Output of mitraClient.evaluate().envelope
   * @param {Object} gateResult        - Output of enforcementGate.enforce()
   */
  setDecision(decisionEnvelope, gateResult) {
    this._assertNotFlushed('setDecision');
    this._decision = {
      artifact_type: 'bhiv_decision_record',
      trace_id:      this.trace_id,
      execution_id:  this.execution_id,
      buffered_at:   Date.now(),
      decision_envelope: {
        decision:       decisionEnvelope.decision,
        risk_level:     decisionEnvelope.risk_level,
        confidence:     decisionEnvelope.confidence,
        reason:         decisionEnvelope.reason,
        signal_type:    decisionEnvelope.signal_type,
        source:         decisionEnvelope.source,
        mitra_trace_id: decisionEnvelope.mitra_trace_id,
        your_trace_id:  decisionEnvelope.your_trace_id,
        decided_at:     decisionEnvelope.decided_at
      },
      enforcement_result: {
        passed:      gateResult.passed,
        blocked:     gateResult.blocked,
        flagged:     gateResult.flagged,
        decision:    gateResult.decision,
        reason:      gateResult.reason,
        source:      gateResult.source      || null,
        enforced_at: gateResult.enforced_at || null,
        code:        gateResult.code        || null
      }
    };
  }

  // ── Buffer: events ──────────────────────────────────────────────────────────

  /**
   * Append one runtime event to the events buffer.
   * trace_id is stamped automatically — caller cannot omit it.
   * @param {string} event_type
   * @param {Object} payload
   */
  appendEvent(event_type, payload = {}) {
    this._assertNotFlushed('appendEvent');
    this._events.push({
      trace_id:     this.trace_id,
      execution_id: this.execution_id,
      event_type,
      payload,
      buffered_at:  Date.now()
    });
  }

  /**
   * Append multiple events at once (e.g. from eventCollector.getStream()).
   * @param {Array} events
   */
  appendEvents(events) {
    this._assertNotFlushed('appendEvents');
    if (!Array.isArray(events)) throw new Error('[BUCKET_WRITER] appendEvents requires an array');
    events.forEach(e => {
      this._events.push({
        ...e,
        trace_id:     this.trace_id,   // enforce trace continuity
        execution_id: this.execution_id
      });
    });
  }

  // ── Buffer: state ───────────────────────────────────────────────────────────

  /**
   * Set the final state snapshot.
   * @param {Object} state       - Final runtime/domain state
   * @param {Object} governance  - { decision, risk_level, mitra_trace_id }
   */
  setState(state, governance = {}) {
    this._assertNotFlushed('setState');
    this._state = {
      artifact_type: 'bhiv_final_state',
      trace_id:      this.trace_id,
      execution_id:  this.execution_id,
      buffered_at:   Date.now(),
      governance: {
        decision:       governance.decision       || null,
        risk_level:     governance.risk_level     || null,
        mitra_trace_id: governance.mitra_trace_id || null
      },
      state
    };
  }

  // ── Buffer: log ─────────────────────────────────────────────────────────────

  /**
   * Append one log entry.
   * @param {string} stage
   * @param {string} message
   * @param {Object} [meta]
   */
  log(stage, message, meta = {}) {
    this._assertNotFlushed('log');
    this._log.push({
      trace_id:     this.trace_id,
      execution_id: this.execution_id,
      stage,
      message,
      meta,
      logged_at:    Date.now()
    });
  }

  // ── Flush — write all 5 artifacts atomically ────────────────────────────────

  /**
   * Write all 5 artifacts to disk.
   * Called ONCE on pipeline completion.
   * Throws if any required buffer is missing.
   *
   * @returns {Promise<{ artifacts: string[], trace_id, execution_id, flushed_at }>}
   */
  async flush() {
    this._assertNotFlushed('flush');

    // ── Validate all buffers are populated ───────────────────────────────────
    const missing = [];
    if (!this._schema)              missing.push('schema (call setSchema first)');
    if (!this._decision)            missing.push('decision (call setDecision first)');
    if (this._events.length === 0)  missing.push('events (call appendEvent first)');
    if (!this._state)               missing.push('state (call setState first)');
    if (this._log.length === 0)     missing.push('log (call log() first)');

    if (missing.length > 0) {
      throw new Error(`[BUCKET_WRITER] Cannot flush — missing buffers: ${missing.join(', ')}`);
    }

    await fs.mkdir(BUCKET_DIR, { recursive: true });

    const flushed_at = Date.now();
    const written    = [];

    // ── 1. execution_<trace_id>_schema.json ──────────────────────────────────
    const schemaPath = path.join(BUCKET_DIR, `execution_${this.trace_id}_schema.json`);
    await fs.writeFile(schemaPath, JSON.stringify({ ...this._schema, flushed_at }, null, 2));
    written.push(schemaPath);
    console.log(`[BUCKET_WRITER] ✓ execution_${this.trace_id}_schema.json`);

    // ── 2. execution_<trace_id>_decision.json ────────────────────────────────
    const decisionPath = path.join(BUCKET_DIR, `execution_${this.trace_id}_decision.json`);
    await fs.writeFile(decisionPath, JSON.stringify({ ...this._decision, flushed_at }, null, 2));
    written.push(decisionPath);
    console.log(`[BUCKET_WRITER] ✓ execution_${this.trace_id}_decision.json`);

    // ── 3. execution_<trace_id>_events.jsonl ─────────────────────────────────
    const eventsPath = path.join(BUCKET_DIR, `execution_${this.trace_id}_events.jsonl`);
    await fs.writeFile(eventsPath, this._events.map(e => JSON.stringify(e)).join('\n') + '\n');
    written.push(eventsPath);
    console.log(`[BUCKET_WRITER] ✓ execution_${this.trace_id}_events.jsonl (${this._events.length} events)`);

    // ── 4. execution_<trace_id>_state.json ───────────────────────────────────
    const statePath = path.join(BUCKET_DIR, `execution_${this.trace_id}_state.json`);
    await fs.writeFile(statePath, JSON.stringify({ ...this._state, flushed_at }, null, 2));
    written.push(statePath);
    console.log(`[BUCKET_WRITER] ✓ execution_${this.trace_id}_state.json`);

    // ── 5. execution_<trace_id>_log.jsonl ────────────────────────────────────
    const logPath = path.join(BUCKET_DIR, `execution_${this.trace_id}_log.jsonl`);
    await fs.writeFile(logPath, this._log.map(e => JSON.stringify(e)).join('\n') + '\n');
    written.push(logPath);
    console.log(`[BUCKET_WRITER] ✓ execution_${this.trace_id}_log.jsonl (${this._log.length} entries)`);

    this._flushed = true;

    return {
      artifacts:    written,
      trace_id:     this.trace_id,
      execution_id: this.execution_id,
      flushed_at,
      counts: {
        events: this._events.length,
        log:    this._log.length
      }
    };
  }

  // ── Inspection helpers ──────────────────────────────────────────────────────

  /** Returns current buffer sizes — useful for debugging before flush */
  status() {
    return {
      trace_id:      this.trace_id,
      execution_id:  this.execution_id,
      flushed:       this._flushed,
      schema_set:    this._schema   !== null,
      decision_set:  this._decision !== null,
      state_set:     this._state    !== null,
      event_count:   this._events.length,
      log_count:     this._log.length
    };
  }

  // ── Internal ────────────────────────────────────────────────────────────────

  _assertNotFlushed(op) {
    if (this._flushed) {
      throw new Error(`[BUCKET_WRITER] Cannot call ${op}() — writer already flushed for trace=${this.trace_id}`);
    }
  }
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { create };

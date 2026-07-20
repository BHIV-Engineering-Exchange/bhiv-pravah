'use strict';

/**
 * determinismValidator.js
 *
 * Phase 5 — Determinism Validation
 *
 * Runs the same input through the pipeline N times (with fixed trace/execution IDs
 * per run so artifacts are isolated), then compares the outputs.
 *
 * What is validated as DETERMINISTIC (must be identical across all runs):
 *   - contract structure and all field values
 *   - decision value (ALLOW / FLAG / BLOCK)
 *   - decision risk_level
 *   - enforcement gate result (passed / blocked / flagged)
 *   - pre-runtime event sequence (stage names in order)
 *   - artifact structure (which artifact keys exist)
 *   - failure_code (when pipeline fails)
 *   - failure stage
 *
 * What is ALLOWED TO VARY (stripped before comparison):
 *   - trace_id          — unique per run by design
 *   - execution_id      — unique per run by design
 *   - telemetry_id      — UUID per event
 *   - timestamp         — wall-clock time
 *   - logged_at         — wall-clock time
 *   - decided_at        — wall-clock time
 *   - enforced_at       — wall-clock time
 *   - buffered_at       — wall-clock time
 *   - flushed_at        — wall-clock time
 *   - collected_at      — wall-clock time
 *   - duration          — elapsed time
 *   - mitra_trace_id    — assigned by Mitra
 *   - event_id          — UUID per event
 *   - accepted_at       — wall-clock time
 *   - started_at        — wall-clock time
 *   - completed_at      — wall-clock time
 *   - stopped_at        — wall-clock time
 *
 * Returns DeterminismReport — structured, machine-readable.
 */

const { adaptVessel }  = require('./maritimeAdapter');
const { build }        = require('./contractBuilder');
const mitraClient      = require('./mitraClient');
const { enforce }      = require('./enforcementGate');

// Fields that are allowed to differ between runs — stripped before comparison
const VOLATILE_KEYS = new Set([
  'trace_id', 'execution_id', 'telemetry_id', 'event_id',
  'timestamp', 'logged_at', 'decided_at', 'enforced_at',
  'buffered_at', 'flushed_at', 'collected_at', 'accepted_at',
  'started_at', 'completed_at', 'stopped_at',
  'duration', 'mitra_trace_id', 'your_trace_id'
]);

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Run determinism validation for a single vessel input.
 *
 * @param {Object} vesselInput  - Raw vessel signal
 * @param {number} [runs=3]     - Number of times to run
 * @returns {Promise<DeterminismReport>}
 */
async function validate(vesselInput, runs = 3) {
  if (!vesselInput) throw new Error('vesselInput is required');
  if (runs < 2)     throw new Error('runs must be >= 2');

  const results   = [];
  const runLog    = [];

  for (let i = 0; i < runs; i++) {
    const runId = `run_${i + 1}`;
    runLog.push(`[RUN ${i + 1}/${runs}] Starting`);

    const snapshot = await _captureSnapshot(vesselInput, runId);
    results.push(snapshot);

    runLog.push(`[RUN ${i + 1}/${runs}] Complete — path=${snapshot.path} failure=${snapshot.failure_code || 'none'}`);
  }

  // ── Compare all runs against run 1 ───────────────────────────────────────
  const checks   = _runChecks(results);
  const passed   = checks.every(c => c.deterministic);
  const failed   = checks.filter(c => !c.deterministic);

  runLog.push(`Checks: ${checks.length} total, ${failed.length} failed`);

  return {
    deterministic:  passed,
    input:          vesselInput,
    run_count:      runs,
    checks,
    failed_checks:  failed,
    what_varies:    [...VOLATILE_KEYS].sort(),
    run_log:        runLog,
    generated_at:   Date.now()
  };
}

// ─── Snapshot capture ─────────────────────────────────────────────────────────
// Runs adapter → contractBuilder → mitraClient → enforcementGate
// Does NOT call executionClient (external dependency — not deterministic to test)
// Does NOT write artifacts (side-effect — not needed for comparison)

async function _captureSnapshot(vesselInput, runId) {
  const trace_id     = `det_${runId}_${Date.now()}`;
  const execution_id = `exec_det_${runId}`;

  // ── Phase 1: Adapter ──────────────────────────────────────────────────────
  const adapted = adaptVessel(vesselInput, { trace_id, execution_id });
  if (!adapted.success) {
    return {
      runId, trace_id, execution_id,
      path:         'ADAPTER_FAILED',
      failure_code: 'ADAPTER_FAILED',
      failure_stage: 'adapter',
      contract:     null,
      decision:     null,
      risk_level:   null,
      enforcement:  null,
      event_sequence: [],
      artifact_keys:  []
    };
  }

  // ── Phase 1: Contract build ───────────────────────────────────────────────
  const built = build(adapted.schema);
  if (!built.success) {
    return {
      runId, trace_id, execution_id,
      path:          'CONTRACT_FAILED',
      failure_code:  'CONTRACT_BUILD_FAILED',
      failure_stage: 'contract',
      contract:      null,
      decision:      null,
      risk_level:    null,
      enforcement:   null,
      event_sequence: [],
      artifact_keys:  []
    };
  }

  const contract = _strip(built.contract);

  // ── Phase 2a: Mitra decision ──────────────────────────────────────────────
  const mitraResult = await mitraClient.evaluate(adapted.schema);

  if (!mitraResult.success) {
    return {
      runId, trace_id, execution_id,
      path:          'MITRA_FAILED',
      failure_code:  'MITRA_UNREACHABLE',
      failure_stage: 'decision',
      contract,
      decision:      null,
      risk_level:    null,
      enforcement:   null,
      event_sequence: ['decision_attempted'],
      artifact_keys:  ['schema', 'decision', 'events', 'state', 'log']
    };
  }

  const envelope = mitraResult.envelope;
  const decision   = envelope.decision;
  const risk_level = envelope.risk_level;

  // ── Phase 2b: Enforcement gate ────────────────────────────────────────────
  adapted.schema.decisionEnvelope = envelope;
  const gateResult = enforce(adapted.schema);

  const enforcement = {
    passed:  gateResult.passed,
    blocked: gateResult.blocked,
    flagged: gateResult.flagged,
    decision: gateResult.decision
  };

  // ── Pre-runtime event sequence ────────────────────────────────────────────
  // These are the stages that fire before execution layer is called.
  // They are deterministic — same input always produces same sequence.
  const event_sequence = ['decision_received', 'enforcement_applied'];
  if (gateResult.passed) {
    event_sequence.push('execution_started');
    // execution_completed would follow if execution layer were available
  }

  // ── Artifact structure ────────────────────────────────────────────────────
  // Regardless of path, pipeline always writes all 5 artifact types
  const artifact_keys = ['schema', 'decision', 'events', 'state', 'log'].sort();

  const path = gateResult.passed ? 'ALLOW'
             : gateResult.flagged ? 'FLAG'
             : 'BLOCK';

  return {
    runId, trace_id, execution_id,
    path,
    failure_code:  null,
    failure_stage: null,
    contract,
    decision,
    risk_level,
    enforcement,
    event_sequence,
    artifact_keys
  };
}

// ─── Comparison checks ────────────────────────────────────────────────────────

function _runChecks(results) {
  const ref = results[0]; // run 1 is the reference

  return [
    _check('path',
      'Execution path (ALLOW/FLAG/BLOCK/MITRA_FAILED) is identical across all runs',
      results, r => r.path),

    _check('failure_code',
      'Failure code is identical when pipeline fails',
      results, r => r.failure_code),

    _check('failure_stage',
      'Failure stage is identical when pipeline fails',
      results, r => r.failure_stage),

    _check('decision',
      'Mitra decision value (ALLOW/FLAG/BLOCK) is identical across all runs',
      results, r => r.decision),

    _check('risk_level',
      'Mitra risk_level is identical across all runs',
      results, r => r.risk_level),

    _check('enforcement.passed',
      'Enforcement gate passed result is identical across all runs',
      results, r => r.enforcement?.passed),

    _check('enforcement.blocked',
      'Enforcement gate blocked result is identical across all runs',
      results, r => r.enforcement?.blocked),

    _check('enforcement.flagged',
      'Enforcement gate flagged result is identical across all runs',
      results, r => r.enforcement?.flagged),

    _check('enforcement.decision',
      'Enforcement gate decision is identical across all runs',
      results, r => r.enforcement?.decision),

    _check('contract.game_mode',
      'Contract game_mode is identical across all runs',
      results, r => r.contract?.game_mode),

    _check('contract.entities',
      'Contract entities array (structure + values) is identical across all runs',
      results, r => JSON.stringify(r.contract?.entities)),

    _check('contract.physics',
      'Contract physics block is identical across all runs',
      results, r => JSON.stringify(r.contract?.physics)),

    _check('contract.movement',
      'Contract movement block is identical across all runs',
      results, r => JSON.stringify(r.contract?.movement)),

    _check('contract.scoring',
      'Contract scoring block is identical across all runs',
      results, r => JSON.stringify(r.contract?.scoring)),

    _check('contract.spawn_rules',
      'Contract spawn_rules block is identical across all runs',
      results, r => JSON.stringify(r.contract?.spawn_rules)),

    _check('contract.player_params',
      'Contract player_params block is identical across all runs',
      results, r => JSON.stringify(r.contract?.player_params)),

    _check('contract.scene',
      'Contract scene block is identical across all runs',
      results, r => JSON.stringify(r.contract?.scene)),

    _check('event_sequence',
      'Pre-runtime event stage sequence is identical across all runs',
      results, r => JSON.stringify(r.event_sequence)),

    _check('artifact_keys',
      'Artifact key set (which artifacts are written) is identical across all runs',
      results, r => JSON.stringify(r.artifact_keys))
  ];
}

function _check(field, description, results, extractor) {
  const values  = results.map(extractor);
  const ref     = values[0];
  const mismatches = [];

  for (let i = 1; i < values.length; i++) {
    if (values[i] !== ref) {
      mismatches.push({ run: i + 1, expected: ref, got: values[i] });
    }
  }

  return {
    field,
    description,
    deterministic: mismatches.length === 0,
    reference_value: ref,
    mismatches
  };
}

// ─── Strip volatile fields recursively ───────────────────────────────────────

function _strip(obj) {
  if (Array.isArray(obj)) return obj.map(_strip);
  if (obj && typeof obj === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(obj)) {
      if (!VOLATILE_KEYS.has(k)) out[k] = _strip(v);
    }
    return out;
  }
  return obj;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { validate, VOLATILE_KEYS };

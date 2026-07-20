'use strict';

/**
 * simReplayEngine.js
 *
 * Two replay modes:
 *
 * 1. replay(trace_id)
 *    Original HTTP replay — re-runs SimEngine, validates determinism.
 *    Returns a comparison object. Used by POST /simulate/replay/:trace_id.
 *
 * 2. replayStream(trace_id, { onTick, onComplete, onError })
 *    Phase 2 stream replay — re-runs SimEngineStream, validates each tick
 *    is structurally identical to the stored live tick, then emits it.
 *    Emits the EXACT same stream:tick / stream:done / stream:error shape
 *    as the live stream. No replay-specific shape allowed.
 *
 * Parity rule:
 *   replayed_tick[i] must equal live_tick[i] on:
 *     - tick_id
 *     - entities[].id, type, state, position {x,y,z}, attributes
 *   trace_id is always the original — never regenerated.
 */

const { run }       = require('./engine/SimEngine');
const { runStream } = require('./engine/SimEngineStream');
const store         = require('./simResultStore');

// ─── replayStream ─────────────────────────────────────────────────────────────

/**
 * Replay a simulation as a delta stream.
 * Emits the same events as the live stream — structurally identical.
 *
 * @param {string}   trace_id
 * @param {Object}   opts
 * @param {Function} opts.onTick      - Called with each validated delta payload
 * @param {Function} opts.onComplete  - Called with summary on success
 * @param {Function} opts.onError     - Called with { code, reason, trace_id } on failure
 */
function replayStream(trace_id, { onTick, onComplete, onError }) {
  if (!trace_id) {
    return onError({ code: 'MISSING_TRACE_ID', reason: 'trace_id is required', trace_id: null });
  }

  // ── Step 1: Load stored contract + live ticks ─────────────────────────────
  const stored = store.getWithContract(trace_id);
  if (!stored) {
    return onError({ code: 'NOT_FOUND', reason: `No simulation found for trace_id: ${trace_id}`, trace_id });
  }

  const { contract, stream_ticks: live_ticks } = stored;

  if (!contract) {
    return onError({ code: 'NO_CONTRACT', reason: 'No contract stored — cannot replay', trace_id });
  }

  if (!live_ticks || live_ticks.length === 0) {
    return onError({ code: 'NO_STREAM_TICKS', reason: 'No live stream ticks stored — run via stream:start first', trace_id });
  }

  const expected_ticks = live_ticks.length;
  let   replay_index   = 0;

  // ── Step 2: Re-run via SimEngineStream ────────────────────────────────────
  // onTick receives each replayed delta — validate parity then emit
  runStream(contract, {
    ticks: expected_ticks,
    _isReplay: true,  // Phase 2: prevent bucket writes during replay

    onTick(replayed_delta) {
      const live_delta = live_ticks[replay_index];
      replay_index++;

      // ── Parity check ──────────────────────────────────────────────────
      const violation = _checkParity(live_delta, replayed_delta, trace_id);
      if (violation) {
        // Hard fail — stop stream, emit error with trace_id
        onError({
          code:     'PARITY_VIOLATION',
          reason:   violation,
          trace_id,
          tick_id:  replayed_delta.tick_id
        });
        // Throw to abort the runStream loop
        throw new Error(`PARITY_VIOLATION: ${violation}`);
      }

      // Parity confirmed — emit the replayed delta (same shape as live)
      onTick(replayed_delta);
    },

    onComplete(summary) {
      // Validate total tick count matches
      if (replay_index !== expected_ticks) {
        return onError({
          code:     'TICK_COUNT_MISMATCH',
          reason:   `Expected ${expected_ticks} ticks, replayed ${replay_index}`,
          trace_id
        });
      }
      onComplete(summary);
    },

    onError(err) {
      // Only forward if not already a parity violation (already emitted above)
      if (err.code !== 'TICK_ERROR' || !err.reason?.startsWith('PARITY_VIOLATION')) {
        onError(err);
      }
    }
  });
}

// ─── Parity checker ───────────────────────────────────────────────────────────

/**
 * Compare a replayed delta tick against the stored live tick.
 * Returns a violation string if they differ, null if identical.
 *
 * Checks:
 *   - tick_id matches
 *   - trace_id matches
 *   - entity count matches
 *   - per-entity: id, type, state, position {x,y,z}, attributes
 */
function _checkParity(live, replayed, trace_id) {
  if (!live) return `no live tick at index for tick_id=${replayed.tick_id}`;

  if (live.tick_id !== replayed.tick_id) {
    return `tick_id mismatch: live=${live.tick_id} replayed=${replayed.tick_id}`;
  }

  if (replayed.trace_id !== trace_id) {
    return `trace_id mismatch on tick ${replayed.tick_id}: got ${replayed.trace_id}`;
  }

  if (live.entities.length !== replayed.entities.length) {
    return `tick ${replayed.tick_id} entity count mismatch: live=${live.entities.length} replayed=${replayed.entities.length}`;
  }

  // Sort both by id for stable comparison
  const live_sorted     = [...live.entities].sort((a, b) => a.id < b.id ? -1 : 1);
  const replayed_sorted = [...replayed.entities].sort((a, b) => a.id < b.id ? -1 : 1);

  for (let i = 0; i < live_sorted.length; i++) {
    const l = live_sorted[i];
    const r = replayed_sorted[i];

    if (l.id    !== r.id)    return `tick ${replayed.tick_id} entity[${i}] id mismatch: ${l.id} vs ${r.id}`;
    if (l.type  !== r.type)  return `tick ${replayed.tick_id} entity ${r.id} type mismatch`;
    if (l.state !== r.state) return `tick ${replayed.tick_id} entity ${r.id} state mismatch: ${l.state} vs ${r.state}`;

    const lp = l.position;
    const rp = r.position;
    if (lp.x !== rp.x || lp.y !== rp.y || lp.z !== rp.z) {
      return `tick ${replayed.tick_id} entity ${r.id} position mismatch: live=(${lp.x},${lp.y},${lp.z}) replayed=(${rp.x},${rp.y},${rp.z})`;
    }

    if (JSON.stringify(l.attributes) !== JSON.stringify(r.attributes)) {
      return `tick ${replayed.tick_id} entity ${r.id} attributes mismatch`;
    }
  }

  return null;  // parity confirmed
}

// ─── Original HTTP replay (unchanged) ────────────────────────────────────────

function replay(trace_id) {
  if (!trace_id) return _fail('MISSING_TRACE_ID', 'trace_id is required', null);

  const log  = [];
  const _log = (stage, msg) => { log.push({ stage, msg, ts: Date.now() }); };

  _log('START', `Replaying trace_id=${trace_id}`);

  const stored = store.getWithContract(trace_id);
  if (!stored) return _fail('NOT_FOUND', `No simulation found for trace_id: ${trace_id}`, trace_id);

  const { result: original, contract } = stored;
  if (!contract) return _fail('NO_CONTRACT', 'Original SumScript contract not stored — cannot replay', trace_id);

  _log('LOAD', `ticks=${original.ticks_run} entities=${Object.keys(original.entities || {}).length}`);

  let replayed;
  try {
    replayed = run(contract, { ticks: original.ticks_run });
  } catch (err) {
    return _fail('RUN_ERROR', `SimEngine threw during replay: ${err.message}`, trace_id);
  }

  if (replayed.status === 'failed') {
    return _fail('RUN_FAILED', `SimEngine failed during replay: ${replayed.error}`, trace_id);
  }

  _log('RUN', `ticks=${replayed.ticks_run} entities=${Object.keys(replayed.entities).length}`);

  const violations = _validateDeterminism(original, replayed);

  if (violations.length > 0) {
    _log('VALIDATE', `FAILED — ${violations.length} violations`);
    return _fail('DETERMINISM_FAILED', `Replay produced different output: ${violations.join('; ')}`, trace_id, { violations });
  }

  _log('COMPLETE', `deterministic=true events=${replayed.state_summary.event_count}`);

  return {
    success:       true,
    trace_id,
    execution_id:  replayed.execution_id,
    deterministic: true,
    ticks_run:     replayed.ticks_run,
    violations:    [],
    result:        replayed,
    diff: {
      entity_count_match:     Object.keys(original.entities).length === Object.keys(replayed.entities).length,
      transition_count_match: original.transitions.length === replayed.transitions.length,
      event_count_match:      original.state_summary.event_count === replayed.state_summary.event_count,
      final_positions_match:  _comparePositions(original.entities, replayed.entities)
    },
    replay_log: log,
    failure:    null
  };
}

function _validateDeterminism(original, replayed) {
  const violations = [];
  if (!original || !original.entities) return ['original result missing'];

  if (original.ticks_run !== replayed.ticks_run) {
    violations.push(`ticks_run mismatch: ${original.ticks_run} vs ${replayed.ticks_run}`);
  }

  const origIds     = Object.keys(original.entities).sort();
  const replayedIds = Object.keys(replayed.entities).sort();
  if (JSON.stringify(origIds) !== JSON.stringify(replayedIds)) {
    violations.push('entity ids mismatch');
  }

  for (const id of origIds) {
    const o = original.entities[id];
    const r = replayed.entities[id];
    if (!r) continue;
    if (!_posEqual(o.position, r.position)) violations.push(`entity ${id} position mismatch`);
    if (o.state !== r.state)                violations.push(`entity ${id} state mismatch`);
  }

  if (original.transitions.length !== replayed.transitions.length) {
    violations.push(`transition count mismatch: ${original.transitions.length} vs ${replayed.transitions.length}`);
  }

  if (original.state_summary.event_count !== replayed.state_summary.event_count) {
    violations.push(`event count mismatch: ${original.state_summary.event_count} vs ${replayed.state_summary.event_count}`);
  }

  if (original.metrics.tick_snapshots.length !== replayed.metrics.tick_snapshots.length) {
    violations.push('tick_snapshots count mismatch');
  }

  return violations;
}

function _posEqual(a, b) {
  if (!a || !b) return false;
  return a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
}

function _comparePositions(origEntities, replayedEntities) {
  for (const [id, e] of Object.entries(origEntities)) {
    const r = replayedEntities[id];
    if (!r || !_posEqual(e.position, r.position)) return false;
  }
  return true;
}

function _fail(code, reason, trace_id, meta = {}) {
  return {
    success: false, trace_id: trace_id || null, execution_id: null,
    deterministic: false, ticks_run: 0, violations: [],
    result: null, diff: null, replay_log: [],
    failure: { code, reason, meta, failed_at: Date.now() }
  };
}

module.exports = { replay, replayStream };

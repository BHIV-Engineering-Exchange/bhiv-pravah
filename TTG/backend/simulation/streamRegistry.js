'use strict';

/**
 * streamRegistry.js
 *
 * Tracks active delta stream sessions.
 * Enforces tick integrity — one stream per trace_id, strict tick ordering.
 *
 * Tick integrity rules (Phase 3):
 *   - tick_id must equal last_tick + 1 exactly
 *   - tick_id === last_tick     → DUPLICATE
 *   - tick_id <  last_tick + 1  → OUT_OF_ORDER
 *   - tick_id >  last_tick + 1  → MISSING_TICK (gap detected)
 *
 * On any violation: recordTick() returns a violation descriptor.
 * Caller (SimEngineStream) must hard-fail immediately — no recovery.
 */

const _active = new Map(); // trace_id → { socket_id, started_at, last_tick, seen: Set }

function register(trace_id, socket_id) {
  if (_active.has(trace_id)) return false;
  _active.set(trace_id, {
    socket_id,
    started_at: Date.now(),
    last_tick:  0,
    seen:       new Set()   // tracks every tick_id emitted — for duplicate detection
  });
  return true;
}

function release(trace_id) {
  _active.delete(trace_id);
}

function get(trace_id) {
  return _active.get(trace_id) || null;
}

function isActive(trace_id) {
  return _active.has(trace_id);
}

function count() {
  return _active.size;
}

/**
 * Record a tick emission and enforce integrity.
 *
 * @param {string} trace_id
 * @param {number} tick_id
 * @returns {Object|null}  null = ok, { code, reason } = violation → caller must hard-fail
 */
function recordTick(trace_id, tick_id) {
  const session = _active.get(trace_id);
  if (!session) {
    return { code: 'NO_SESSION', reason: `No active stream session for trace_id: ${trace_id}` };
  }

  const expected = session.last_tick + 1;

  // ── Out-of-order or missing — check BEFORE duplicate ─────────────────────
  // A tick_id below expected is out-of-order regardless of whether it was seen.
  // Check this first so out-of-order takes priority over duplicate.
  if (tick_id !== expected) {
    const code = tick_id < expected ? 'OUT_OF_ORDER_TICK' : 'MISSING_TICK';
    return {
      code,
      reason:   `${code}: expected tick_id=${expected}, got tick_id=${tick_id} for trace_id=${trace_id}`,
      tick_id,
      expected
    };
  }

  // ── Duplicate — same tick_id as expected (already emitted) ───────────────
  if (session.seen.has(tick_id)) {
    return {
      code:     'DUPLICATE_TICK',
      reason:   `Duplicate tick_id=${tick_id} for trace_id=${trace_id} (already emitted)`,
      tick_id,
      expected
    };
  }

  // ── Valid — record and advance ────────────────────────────────────────────
  session.seen.add(tick_id);
  session.last_tick = tick_id;
  return null;
}

module.exports = { register, release, get, isActive, count, recordTick };

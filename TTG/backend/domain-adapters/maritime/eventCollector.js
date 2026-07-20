'use strict';

/**
 * eventCollector.js
 *
 * Phase 4 — Event Stream Capture
 *
 * Collects runtime events emitted by Atharva's execution layer.
 * Every event is stamped with trace_id and execution_id for full continuity.
 *
 * Required events (in order):
 *   contract_accepted   — execution layer accepted the contract
 *   execution_started   — runtime has begun processing
 *   entity_spawned      — one or more entities spawned (may fire multiple times)
 *   execution_completed — runtime finished (success or failure)
 *
 * Rules:
 *   - trace_id MUST be present on every collect() call — fail loud if missing
 *   - execution_id MUST be present — fail loud if missing
 *   - Stream is append-only — no mutation after write
 *   - Unknown event types are rejected — not silently dropped
 *   - Each trace has its own isolated stream
 *   - getStream(trace_id) returns a snapshot — caller cannot mutate internal state
 */

const { v4: uuidv4 } = require('uuid');

// ─── Allowed event types ──────────────────────────────────────────────────────

const PIPELINE_EVENTS = {
  CONTRACT_ACCEPTED:   'contract_accepted',
  EXECUTION_STARTED:   'execution_started',
  ENTITY_SPAWNED:      'entity_spawned',
  EXECUTION_COMPLETED: 'execution_completed'
};

const ALLOWED_TYPES = new Set(Object.values(PIPELINE_EVENTS));

// ─── Internal store ───────────────────────────────────────────────────────────
// Map: trace_id → { execution_id, events: [], started_at, completed: bool }

const _store = new Map();

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Collect a runtime event into the stream for its trace_id.
 *
 * @param {string} event_type  - One of PIPELINE_EVENTS values
 * @param {string} trace_id    - Must match the trace from contractBuilder
 * @param {string} execution_id
 * @param {Object} [payload]   - Event-specific data from Atharva's layer
 * @returns {{ success, event, error }}
 */
function collect(event_type, trace_id, execution_id, payload = {}) {
  // ── Guard: trace_id required ──────────────────────────────────────────────
  if (!trace_id) {
    const msg = `trace_id is required — event "${event_type}" NOT collected`;
    console.error(`[EVENT_COLLECTOR] ❌ ${msg}`);
    return { success: false, event: null, error: msg };
  }

  // ── Guard: execution_id required ─────────────────────────────────────────
  if (!execution_id) {
    const msg = `execution_id is required — event "${event_type}" NOT collected`;
    console.error(`[EVENT_COLLECTOR] ❌ ${msg}`);
    return { success: false, event: null, error: msg };
  }

  // ── Guard: unknown event type rejected ───────────────────────────────────
  if (!ALLOWED_TYPES.has(event_type)) {
    const msg = `Unknown event type: "${event_type}" — allowed: ${[...ALLOWED_TYPES].join(', ')}`;
    console.error(`[EVENT_COLLECTOR] ❌ ${msg}`);
    return { success: false, event: null, error: msg };
  }

  // ── Guard: stream already completed — no more events ─────────────────────
  const existing = _store.get(trace_id);
  if (existing && existing.completed && event_type !== PIPELINE_EVENTS.EXECUTION_COMPLETED) {
    const msg = `Stream for trace=${trace_id} is already completed — event "${event_type}" rejected`;
    console.error(`[EVENT_COLLECTOR] ❌ ${msg}`);
    return { success: false, event: null, error: msg };
  }

  // ── Initialise stream for this trace if first event ──────────────────────
  if (!_store.has(trace_id)) {
    _store.set(trace_id, {
      trace_id,
      execution_id,
      events:     [],
      started_at: Date.now(),
      completed:  false
    });
  }

  const stream = _store.get(trace_id);

  // ── Build event record ────────────────────────────────────────────────────
  const event = {
    event_id:     uuidv4(),
    event_type,
    trace_id,
    execution_id,
    collected_at: Date.now(),
    payload:      payload || {}
  };

  stream.events.push(event);

  // Mark stream complete when execution_completed arrives
  if (event_type === PIPELINE_EVENTS.EXECUTION_COMPLETED) {
    stream.completed    = true;
    stream.completed_at = Date.now();
  }

  console.log(`[EVENT_COLLECTOR] ✅ ${event_type} | trace=${trace_id} | execution=${execution_id} | total=${stream.events.length}`);

  return { success: true, event, error: null };
}

/**
 * Get all collected events for a trace_id.
 * Returns a snapshot — mutations do not affect internal state.
 *
 * @param {string} trace_id
 * @returns {{ found, trace_id, execution_id, events, started_at, completed, completed_at? }}
 */
function getStream(trace_id) {
  const stream = _store.get(trace_id);
  if (!stream) {
    return { found: false, trace_id, events: [] };
  }
  return {
    found:        true,
    trace_id:     stream.trace_id,
    execution_id: stream.execution_id,
    events:       [...stream.events],   // snapshot — immutable copy
    started_at:   stream.started_at,
    completed:    stream.completed,
    completed_at: stream.completed_at || null
  };
}

/**
 * Get events of a specific type for a trace_id.
 *
 * @param {string} trace_id
 * @param {string} event_type
 * @returns {Array}
 */
function getEventsByType(trace_id, event_type) {
  const stream = _store.get(trace_id);
  if (!stream) return [];
  return stream.events.filter(e => e.event_type === event_type);
}

/**
 * Check whether a specific event type has been collected for a trace.
 *
 * @param {string} trace_id
 * @param {string} event_type
 * @returns {boolean}
 */
function hasEvent(trace_id, event_type) {
  return getEventsByType(trace_id, event_type).length > 0;
}

/**
 * Check whether the stream for a trace is complete
 * (execution_completed has been collected).
 *
 * @param {string} trace_id
 * @returns {boolean}
 */
function isComplete(trace_id) {
  const stream = _store.get(trace_id);
  return stream ? stream.completed : false;
}

/**
 * Get all streams (for bucket artifact writing in Phase 6).
 * @returns {Array}
 */
function getAllStreams() {
  return [..._store.values()].map(s => ({
    trace_id:     s.trace_id,
    execution_id: s.execution_id,
    events:       [...s.events],
    started_at:   s.started_at,
    completed:    s.completed,
    completed_at: s.completed_at || null
  }));
}

/**
 * Clear a stream — testing only.
 * @param {string} [trace_id]  - If omitted, clears all streams
 */
function _clear(trace_id) {
  if (trace_id) {
    _store.delete(trace_id);
  } else {
    _store.clear();
  }
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  collect,
  getStream,
  getEventsByType,
  hasEvent,
  isComplete,
  getAllStreams,
  PIPELINE_EVENTS,
  _clear
};

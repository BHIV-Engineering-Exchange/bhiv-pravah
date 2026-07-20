'use strict';

/**
 * stateFormatter.v1.js
 *
 * Maps raw SimEngine output → simulationState.v1 contract shape.
 *
 * Rules:
 *   - This is the ONLY place that touches output formatting
 *   - No domain-specific fields in output
 *   - No consumer-specific logic (no NICAI, no Samruddhi, no Atharva)
 *   - flags{} and blocked{} fold into state_summary — not top-level
 *   - tick_snapshots move into metrics — they are execution data, not state
 *   - seed is internal — not exposed in output contract
 *
 * Any consumer (NICAI, AIAIC, Samruddhi, etc.) reads from this
 * standard shape via their own domain adapter.
 */

/**
 * Format raw SimEngine result into simulationState.v1
 *
 * @param {Object} raw  - Direct output of SimEngine.run()
 * @returns {Object}    - simulationState.v1 shaped object
 */
function format(raw) {
  if (!raw || !raw.success) {
    return {
      trace_id:      raw?.trace_id      || null,
      execution_id:  raw?.execution_id  || null,
      status:        'failed',
      error:         raw?.error         || 'Simulation failed',
      ticks_run:     0,
      entities:      {},
      transitions:   [],
      event_log:     [],
      state_summary: _emptySummary(),
      zones:         {},
      metrics:       _emptyMetrics()
    };
  }

  const ticks = raw.ticks_run || 0;

  return {
    trace_id:     raw.trace_id,
    execution_id: raw.execution_id,
    status:       'completed',
    error:        null,
    ticks_run:    ticks,

    // Final entity state — strip internal fields (seed, game_mode, etc.)
    entities:     _formatEntities(raw.entities),

    // Full transition log — unchanged, already domain-agnostic
    transitions:  _formatTransitions(raw.transitions),

    // Full event log — strip logged_at (internal timing detail)
    event_log:    _formatEventLog(raw.event_log),

    // Aggregate summary — flags/blocked folded in here
    state_summary: _buildStateSummary(raw),

    // Zone final state
    zones:        raw.zones || {},

    // Execution metrics — tick_snapshots live here
    metrics:      _buildMetrics(raw)
  };
}

// ─── Entity formatter ─────────────────────────────────────────────────────────

function _formatEntities(entities) {
  if (!entities) return {};
  const out = {};
  for (const [id, e] of Object.entries(entities)) {
    out[id] = {
      id:        e.id,
      type:      e.type,
      state:     e.state,
      position:  e.position,
      rotation:  e.rotation  || [0, 0, 0],
      velocity:  e.velocity  || [0, 0, 0],
      behaviors: e.behaviors || [],
      meta:      e.meta      || {}
    };
  }
  return out;
}

// ─── Transition formatter ─────────────────────────────────────────────────────

function _formatTransitions(transitions) {
  if (!Array.isArray(transitions)) return [];
  return transitions.map(t => ({
    entity_id: t.entity_id,
    field:     t.field,
    from:      t.from,
    to:        t.to,
    tick:      t.tick,
    reason:    t.reason
    // recorded_at stripped — internal timing detail
  }));
}

// ─── Event log formatter ──────────────────────────────────────────────────────

function _formatEventLog(event_log) {
  if (!Array.isArray(event_log)) return [];
  return event_log.map(e => {
    const out = {
      source:    e.source,
      type:      e.type,
      entity_id: e.entity_id || null,
      payload:   e.payload   || {},
      tick:      e.tick
    };
    if (e.rule_id) out.rule_id = e.rule_id;
    return out;
    // logged_at stripped — internal timing detail
  });
}

// ─── State summary ────────────────────────────────────────────────────────────

function _buildStateSummary(raw) {
  const entities = raw.entities || {};
  const flags    = raw.flags    || {};
  const blocked  = raw.blocked  || {};
  const log      = raw.event_log || [];

  const stateCount = { active: 0, idle: 0, stopped: 0, destroyed: 0 };
  for (const e of Object.values(entities)) {
    if (stateCount[e.state] !== undefined) stateCount[e.state]++;
  }

  return {
    entity_count:     Object.keys(entities).length,
    active_count:     stateCount.active,
    idle_count:       stateCount.idle,
    stopped_count:    stateCount.stopped,
    destroyed_count:  stateCount.destroyed,
    flagged_count:    Object.keys(flags).length,
    blocked_count:    Object.keys(blocked).length,
    // flags/blocked folded in — not separate top-level fields
    flagged_entities: _formatFlags(flags),
    blocked_entities: _formatBlocked(blocked),
    collision_count:  log.filter(e => e.type === 'collision_detected').length,
    zone_entry_count: log.filter(e => e.type === 'zone_enter').length,
    transition_count: (raw.transitions || []).length,
    event_count:      raw.event_count || log.length,
    duration_ms:      raw.duration    || null
  };
}

function _formatFlags(flags) {
  const out = {};
  for (const [id, f] of Object.entries(flags)) {
    out[id] = { reason: f.reason, rule_id: f.rule_id, tick: f.flagged_at };
  }
  return out;
}

function _formatBlocked(blocked) {
  const out = {};
  for (const [id, b] of Object.entries(blocked)) {
    out[id] = { reason: b.reason, rule_id: b.rule_id, tick: b.blocked_at };
  }
  return out;
}

// ─── Metrics ──────────────────────────────────────────────────────────────────

function _buildMetrics(raw) {
  const ticks = raw.ticks_run || 0;
  const events = raw.event_count || 0;
  const transitions = (raw.transitions || []).length;

  return {
    started_at:           raw.started_at || null,
    ended_at:             raw.ended_at   || null,
    ticks_run:            ticks,
    events_per_tick:      ticks > 0 ? parseFloat((events / ticks).toFixed(3)) : 0,
    transitions_per_tick: ticks > 0 ? parseFloat((transitions / ticks).toFixed(3)) : 0,
    tick_snapshots:       raw.tick_snapshots || []
  };
}

// ─── Empty shapes (for failed runs) ──────────────────────────────────────────

function _emptySummary() {
  return {
    entity_count: 0, active_count: 0, idle_count: 0,
    stopped_count: 0, destroyed_count: 0,
    flagged_count: 0, blocked_count: 0,
    flagged_entities: {}, blocked_entities: {},
    collision_count: 0, zone_entry_count: 0,
    transition_count: 0, event_count: 0, duration_ms: null
  };
}

function _emptyMetrics() {
  return {
    started_at: null, ended_at: null, ticks_run: 0,
    events_per_tick: 0, transitions_per_tick: 0, tick_snapshots: []
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { format };

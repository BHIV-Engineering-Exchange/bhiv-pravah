'use strict';

/**
 * nicaiFormatter.js
 *
 * Formats SimEngine output (SimResult) into NICAI-consumable intelligence output.
 *
 * NICAI consumes:
 *   - Entity behavior summaries (what each entity did across ticks)
 *   - State transition analysis (how many times each entity changed state)
 *   - Event pattern detection (repeated event types = patterns)
 *   - Anomaly flags (flagged/blocked entities)
 *   - Tick-level intelligence stream (per-tick summaries)
 */

/**
 * Format a SimResult for NICAI consumption.
 *
 * @param {Object} simResult  - Output of SimEngine.run()
 * @returns {Object} nicaiOutput
 */
function format(simResult) {
  if (!simResult || !simResult.success) {
    return {
      success:      false,
      trace_id:     simResult?.trace_id || null,
      error:        simResult?.error    || 'Simulation failed',
      intelligence: null
    };
  }

  return {
    success:      true,
    trace_id:     simResult.trace_id,
    execution_id: simResult.execution_id,
    generated_at: Date.now(),

    intelligence: {
      // Summary of what happened
      simulation_summary: _buildSummary(simResult),

      // Per-entity behavior analysis
      entity_profiles: _buildEntityProfiles(simResult),

      // Detected patterns from event log
      patterns: _detectPatterns(simResult),

      // Anomalies: flagged + blocked entities
      anomalies: _buildAnomalies(simResult),

      // Per-tick intelligence stream (for NICAI to replay/analyze)
      tick_stream: _buildTickStream(simResult)
    }
  };
}

// ─── Builders ─────────────────────────────────────────────────────────────────

function _buildSummary(r) {
  const entityCount   = Object.keys(r.entities).length;
  const flaggedCount  = Object.keys(r.flags).length;
  const blockedCount  = Object.keys(r.blocked).length;
  const activeCount   = Object.values(r.entities).filter(e => e.state === 'active').length;
  const stoppedCount  = Object.values(r.entities).filter(e => e.state === 'stopped').length;

  return {
    ticks_run:       r.ticks_run,
    duration_ms:     r.duration,
    entity_count:    entityCount,
    event_count:     r.event_count,
    transition_count: r.transitions.length,
    flagged_count:   flaggedCount,
    blocked_count:   blockedCount,
    active_count:    activeCount,
    stopped_count:   stoppedCount,
    collision_count: r.event_log.filter(e => e.type === 'collision_detected').length,
    zone_entries:    r.event_log.filter(e => e.type === 'zone_enter').length,
    status:          r.status
  };
}

function _buildEntityProfiles(r) {
  const profiles = {};

  for (const [id, entity] of Object.entries(r.entities)) {
    const entityTransitions = r.transitions.filter(t => t.entity_id === id);
    const entityEvents      = r.event_log.filter(e => e.entity_id === id);

    // Calculate total distance traveled from transitions
    const posTransitions = entityTransitions.filter(t => t.field === 'position');
    let totalDistance = 0;
    for (const t of posTransitions) {
      if (Array.isArray(t.from) && Array.isArray(t.to)) {
        const dx = t.to[0] - t.from[0];
        const dz = t.to[2] - t.from[2];
        totalDistance += Math.sqrt(dx * dx + dz * dz);
      }
    }

    profiles[id] = {
      type:             entity.type,
      final_state:      entity.state,
      final_position:   entity.position,
      is_flagged:       !!r.flags[id],
      is_blocked:       !!r.blocked[id],
      flag_reason:      r.flags[id]?.reason   || null,
      block_reason:     r.blocked[id]?.reason || null,
      state_changes:    entityTransitions.filter(t => t.field === 'state').length,
      total_distance:   parseFloat(totalDistance.toFixed(3)),
      event_count:      entityEvents.length,
      behavior_events:  entityEvents.filter(e => e.source === 'behavior').length,
      rule_events:      entityEvents.filter(e => e.source === 'rule').length
    };
  }

  return profiles;
}

function _detectPatterns(r) {
  const patterns = [];

  // Pattern: repeated event types
  const eventTypeCounts = {};
  for (const evt of r.event_log) {
    eventTypeCounts[evt.type] = (eventTypeCounts[evt.type] || 0) + 1;
  }

  for (const [type, count] of Object.entries(eventTypeCounts)) {
    if (count >= 3) {
      patterns.push({
        pattern_type: 'repeated_event',
        event_type:   type,
        count,
        significance: count >= 10 ? 'high' : count >= 5 ? 'medium' : 'low'
      });
    }
  }

  // Pattern: multiple entities flagged
  const flagCount = Object.keys(r.flags).length;
  if (flagCount > 0) {
    patterns.push({
      pattern_type: 'mass_flag',
      count:        flagCount,
      entities:     Object.keys(r.flags),
      significance: flagCount >= 3 ? 'high' : 'medium'
    });
  }

  // Pattern: high collision rate
  const collisions = r.event_log.filter(e => e.type === 'collision_detected').length;
  if (collisions > 0) {
    patterns.push({
      pattern_type: 'collision_activity',
      count:        collisions,
      per_tick:     parseFloat((collisions / r.ticks_run).toFixed(3)),
      significance: collisions >= 5 ? 'high' : 'low'
    });
  }

  return patterns;
}

function _buildAnomalies(r) {
  const anomalies = [];

  for (const [id, flag] of Object.entries(r.flags)) {
    anomalies.push({
      type:      'flagged',
      entity_id: id,
      reason:    flag.reason,
      rule_id:   flag.rule_id,
      tick:      flag.flagged_at
    });
  }

  for (const [id, block] of Object.entries(r.blocked)) {
    anomalies.push({
      type:      'blocked',
      entity_id: id,
      reason:    block.reason,
      rule_id:   block.rule_id,
      tick:      block.blocked_at
    });
  }

  return anomalies;
}

function _buildTickStream(r) {
  return r.tick_snapshots.map(snap => ({
    tick:          snap.tick,
    entity_count:  snap.entity_count,
    events:        snap.events_this_tick,
    collisions:    snap.collisions,
    zone_events:   snap.zone_events,
    flags:         snap.flags,
    blocked:       snap.blocked,
    // Compact entity state for NICAI
    states: Object.entries(snap.entity_states || {}).map(([id, s]) => ({
      id,
      state:    s.state,
      position: s.position
    }))
  }));
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { format };

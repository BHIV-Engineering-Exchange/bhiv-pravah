'use strict';

/**
 * samruddhiFormatter.js
 *
 * Formats SimEngine output (SimResult) into Samruddhi-consumable
 * market mapping + visualization output.
 *
 * Samruddhi consumes:
 *   - Entity position timelines (for path charting)
 *   - Zone membership over time (for heatmaps)
 *   - State distribution per tick (for bar/line charts)
 *   - Event density timeline (for activity charts)
 *   - Final spatial snapshot (for map rendering)
 */

/**
 * Format a SimResult for Samruddhi consumption.
 *
 * @param {Object} simResult  - Output of SimEngine.run()
 * @returns {Object} samruddhiOutput
 */
function format(simResult) {
  if (!simResult || !simResult.success) {
    return {
      success:      false,
      trace_id:     simResult?.trace_id || null,
      error:        simResult?.error    || 'Simulation failed',
      mapping:      null
    };
  }

  return {
    success:      true,
    trace_id:     simResult.trace_id,
    execution_id: simResult.execution_id,
    generated_at: Date.now(),

    mapping: {
      // Spatial snapshot — final positions of all entities (for map rendering)
      spatial_snapshot: _buildSpatialSnapshot(simResult),

      // Position timelines per entity (for path/trajectory charts)
      position_timelines: _buildPositionTimelines(simResult),

      // Zone activity over time (for heatmaps)
      zone_activity: _buildZoneActivity(simResult),

      // State distribution per tick (for stacked bar charts)
      state_distribution: _buildStateDistribution(simResult),

      // Event density per tick (for activity timeline charts)
      event_density: _buildEventDensity(simResult),

      // Bounding box of the simulation space (for map scaling)
      bounds: _computeBounds(simResult)
    }
  };
}

// ─── Builders ─────────────────────────────────────────────────────────────────

function _buildSpatialSnapshot(r) {
  return Object.entries(r.entities).map(([id, e]) => ({
    id,
    type:      e.type,
    state:     e.state,
    position:  e.position,
    velocity:  e.velocity,
    flagged:   !!r.flags[id],
    blocked:   !!r.blocked[id]
  }));
}

function _buildPositionTimelines(r) {
  // Build per-entity position history from tick_snapshots
  const timelines = {};

  for (const snap of r.tick_snapshots) {
    for (const [id, s] of Object.entries(snap.entity_states || {})) {
      if (!timelines[id]) timelines[id] = [];
      timelines[id].push({
        tick:     snap.tick,
        position: s.position,
        state:    s.state
      });
    }
  }

  return timelines;
}

function _buildZoneActivity(r) {
  // Extract zone_enter / zone_exit events grouped by zone_id
  const activity = {};

  for (const evt of r.event_log) {
    if (evt.type !== 'zone_enter' && evt.type !== 'zone_exit') continue;
    const zone_id = evt.payload?.zone_id;
    if (!zone_id) continue;

    if (!activity[zone_id]) {
      activity[zone_id] = { entries: [], exits: [], peak_members: 0 };
    }

    if (evt.type === 'zone_enter') {
      activity[zone_id].entries.push({ entity_id: evt.entity_id, tick: evt.tick });
    } else {
      activity[zone_id].exits.push({ entity_id: evt.entity_id, tick: evt.tick });
    }
  }

  // Add zone geometry from result
  for (const [zone_id, zone] of Object.entries(r.zones || {})) {
    if (!activity[zone_id]) {
      activity[zone_id] = { entries: [], exits: [], peak_members: 0 };
    }
    activity[zone_id].position = zone.position;
    activity[zone_id].radius   = zone.radius;
    activity[zone_id].peak_members = zone.members?.length || 0;
  }

  return activity;
}

function _buildStateDistribution(r) {
  // Per-tick count of entities in each state
  return r.tick_snapshots.map(snap => {
    const dist = { active: 0, idle: 0, stopped: 0, destroyed: 0 };
    for (const s of Object.values(snap.entity_states || {})) {
      if (dist[s.state] !== undefined) dist[s.state]++;
    }
    return { tick: snap.tick, ...dist };
  });
}

function _buildEventDensity(r) {
  // Per-tick event count broken down by source
  return r.tick_snapshots.map(snap => ({
    tick:       snap.tick,
    total:      snap.events_this_tick,
    collisions: snap.collisions,
    zone_events: snap.zone_events
  }));
}

function _computeBounds(r) {
  // Compute world-space bounding box from all entity positions across all ticks
  let minX = Infinity, maxX = -Infinity;
  let minZ = Infinity, maxZ = -Infinity;

  for (const snap of r.tick_snapshots) {
    for (const s of Object.values(snap.entity_states || {})) {
      const [x, , z] = s.position;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }
  }

  // Fallback if no snapshots
  if (!isFinite(minX)) {
    for (const e of Object.values(r.entities)) {
      const [x, , z] = e.position;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }
  }

  const pad = 10;
  return {
    min_x: isFinite(minX) ? minX - pad : -100,
    max_x: isFinite(maxX) ? maxX + pad :  100,
    min_z: isFinite(minZ) ? minZ - pad : -100,
    max_z: isFinite(maxZ) ? maxZ + pad :  100
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { format };

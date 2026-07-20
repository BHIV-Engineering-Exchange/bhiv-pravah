'use strict';

/**
 * maritimeStateManager.js
 *
 * Maritime-specific integration layer over the existing Game State Manager (GSM).
 *
 * Responsibilities:
 *   - Initialize a maritime session in GSM using the governed execution schema
 *   - Process maritime events through the State Event Processor (SEP)
 *   - Maintain a maritime overlay: vessel positions, counts, alerts, transitions
 *   - Evaluate consequence rules: proximity alert + zone entry detection
 *   - Propagate trace_id + execution_id on every operation
 *
 * What this does NOT do:
 *   - Does NOT modify GSM
 *   - Does NOT modify SEP
 *   - Does NOT modify consequenceCompiler
 *   - Reads GSM state, writes maritime overlay on top
 */

const gsm              = require('../../state/gameStateManager');
const sep              = require('../../state/stateEventProcessor');
const stateBucketWriter= require('../../state/stateBucketWriter');
const { mapEvent, MARITIME_EVENTS } = require('./maritimeEventMapper');
const template         = require('./templates/maritime_template.json');

// ─── In-memory maritime overlay ───────────────────────────────────────────────
// sessionId → maritime state overlay
const _maritimeSessions = new Map();

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Initialize a maritime simulation session.
 * Creates a GSM session using the governed execution schema from the adapter.
 *
 * @param {Object} governedSchema  - Output of maritimeAdapter.adaptVessel()
 * @returns {{ success, sessionId, state }}
 */
function initSession(governedSchema) {
  const { execution_id, trace_id } = governedSchema;

  if (!execution_id) return _fail('execution_id is required');
  if (!trace_id)     return _fail('trace_id is required');

  const sessionId = `maritime_${execution_id}`;

  if (gsm.hasSession(sessionId)) {
    console.warn(`[MSM] Session ${sessionId} already exists — returning existing`);
    return { success: true, sessionId, state: _getFullState(sessionId) };
  }

  // Build a GSM-compatible template from the maritime template
  const gsmTemplate = {
    template_id: 'maritime_v1',
    entities:    ['vessel', 'zone', 'port'],
    defaults: {
      player_health:    1,
      enemy_count:      0,
      obstacle_count:   0,
      collectible_count:0,
      gravity:          0,
      friction:         0.1,
      collision_force:  1.0
    }
  };

  // Create GSM session
  gsm.createGameState(sessionId, gsmTemplate, { execution_id, trace_id });
  gsm.setRunning(sessionId);

  // Initialize maritime overlay
  _maritimeSessions.set(sessionId, {
    execution_id,
    trace_id,
    vessels:     {},   // vessel_id → { lat, lon, x, z, speed, heading, status, last_updated }
    zones:       {},   // zone_id   → { lat, lon, radius }
    alerts:      [],   // active proximity alerts
    transitions: [],   // FSM transitions: vessel_id, from, to, timestamp
    vessel_count:  0,
    alert_count:   0,
    created_at:    Date.now(),
    last_updated:  Date.now()
  });

  console.log(`[MSM] Session initialized — ${sessionId}, trace: ${trace_id}`);
  return { success: true, sessionId, state: _getFullState(sessionId) };
}

/**
 * Register a zone in the session (used for zone entry detection).
 *
 * @param {string} sessionId
 * @param {string} zone_id
 * @param {number} lat
 * @param {number} lon
 * @param {number} radius  - in engine units (same scale as coordinate mapping)
 */
function registerZone(sessionId, zone_id, lat, lon, radius) {
  const overlay = _maritimeSessions.get(sessionId);
  if (!overlay) return _fail(`Session ${sessionId} not found`);

  overlay.zones[zone_id] = { lat, lon, radius: radius || template.defaults.proximity_radius };
  console.log(`[MSM] Zone registered — ${zone_id} at (${lat}, ${lon}) r=${radius}`);
  return { success: true };
}

/**
 * Apply a maritime event to the session.
 * Routes through SEP → GSM, then updates the maritime overlay.
 *
 * @param {string} sessionId
 * @param {string} maritimeEventType  - One of MARITIME_EVENTS
 * @param {Object} payload
 * @param {Object} governance         - { trace_id, execution_id }
 * @returns {{ success, state, changes, alerts }}
 */
function applyMaritimeEvent(sessionId, maritimeEventType, payload, governance) {
  if (!gsm.hasSession(sessionId)) {
    return _fail(`Session ${sessionId} not found in GSM`);
  }

  // 1. Map maritime event → GSM runtime event
  const mapped = mapEvent(maritimeEventType, payload, governance);
  if (!mapped.success) return _fail(mapped.error);

  const runtimeEvent = mapped.event;

  // 2. Process through SEP → GSM
  const sepResult = sep.processEvent(sessionId, runtimeEvent);
  if (!sepResult.success) {
    // SEP failure is non-fatal for maritime — log and continue
    console.warn(`[MSM] SEP non-fatal: ${sepResult.error}`);
  }

  // 3. Update maritime overlay
  const overlay = _maritimeSessions.get(sessionId);
  if (overlay) {
    _updateOverlay(overlay, maritimeEventType, payload, runtimeEvent);
  }

  // 4. Run consequence checks
  const consequences = _evaluateConsequences(sessionId, payload, governance);

  const fullState = _getFullState(sessionId);

  console.log(`[MSM] Event applied — ${maritimeEventType} | session: ${sessionId} | vessels: ${fullState.maritime?.vessel_count}`);

  return {
    success:      true,
    state:        fullState,
    changes:      sepResult.changes || {},
    consequences,
    event:        runtimeEvent
  };
}

/**
 * Get the current full state for a maritime session.
 * Returns GSM state merged with maritime overlay.
 *
 * @param {string} sessionId
 * @returns {Object|null}
 */
function getMaritimeState(sessionId) {
  if (!gsm.hasSession(sessionId)) return null;
  return _getFullState(sessionId);
}

/**
 * Write a state snapshot to the bucket for this session.
 * @param {string} sessionId
 */
async function snapshotSession(sessionId) {
  return stateBucketWriter.writeStateSnapshot(sessionId);
}

/**
 * Destroy a maritime session from both GSM and the overlay.
 * @param {string} sessionId
 */
function destroySession(sessionId) {
  gsm.destroySession(sessionId);
  _maritimeSessions.delete(sessionId);
  console.log(`[MSM] Session destroyed — ${sessionId}`);
}

/**
 * List all active maritime session IDs.
 * @returns {string[]}
 */
function getActiveSessions() {
  return Array.from(_maritimeSessions.keys());
}

// ─── Overlay update ───────────────────────────────────────────────────────────

function _updateOverlay(overlay, eventType, payload, runtimeEvent) {
  const now = Date.now();
  overlay.last_updated = now;

  switch (eventType) {

    case MARITIME_EVENTS.VESSEL_SPAWNED: {
      const { vessel_id, lat, lon, speed, heading, status } = payload;
      overlay.vessels[vessel_id] = {
        lat, lon,
        x:            runtimeEvent.context.position.x,
        z:            runtimeEvent.context.position.z,
        speed, heading, status,
        last_updated: now,
        fsm_state:    'active'
      };
      overlay.vessel_count = Object.keys(overlay.vessels).length;
      _recordTransition(overlay, vessel_id, null, 'active', now);
      break;
    }

    case MARITIME_EVENTS.VESSEL_UPDATED: {
      const { vessel_id, lat, lon, speed, heading, status } = payload;
      const existing = overlay.vessels[vessel_id];
      if (existing) {
        const prevStatus = existing.status;
        existing.lat          = lat;
        existing.lon          = lon;
        existing.x            = runtimeEvent.context.position[0];
        existing.z            = runtimeEvent.context.position[2];
        existing.speed        = speed;
        existing.heading      = heading;
        existing.status       = status;
        existing.last_updated = now;
        // FSM transition: moving ↔ anchored
        if (prevStatus !== status) {
          const newFsm = status === 'anchored' ? 'anchored' : 'active';
          existing.fsm_state = newFsm;
          _recordTransition(overlay, vessel_id, prevStatus, newFsm, now);
        }
      }
      break;
    }

    case MARITIME_EVENTS.VESSEL_ENTERED_ZONE: {
      const { vessel_id, zone_id } = payload;
      const vessel = overlay.vessels[vessel_id];
      if (vessel) {
        vessel.in_zone    = zone_id || 'zone_boundary';
        vessel.fsm_state  = 'in_zone';
        vessel.last_updated = now;
        _recordTransition(overlay, vessel_id, vessel.status, 'in_zone', now);
      }
      break;
    }

    case MARITIME_EVENTS.VESSEL_PROXIMITY_ALERT: {
      const { vessel_id, other_vessel_id, distance } = payload;
      // Add alert if not already active for this pair
      const alertKey = [vessel_id, other_vessel_id].sort().join('::');
      const existing = overlay.alerts.find(a => a.key === alertKey);
      if (!existing) {
        overlay.alerts.push({
          key:             alertKey,
          vessel_id,
          other_vessel_id,
          distance,
          triggered_at:   now,
          trace_id:        runtimeEvent.metadata.trace_id,
          execution_id:    runtimeEvent.metadata.execution_id
        });
        overlay.alert_count = overlay.alerts.length;
      }
      break;
    }

    case MARITIME_EVENTS.VESSEL_STOPPED: {
      const { vessel_id } = payload;
      const vessel = overlay.vessels[vessel_id];
      if (vessel) {
        const prev = vessel.fsm_state;
        vessel.fsm_state    = 'stopped';
        vessel.last_updated = now;
        _recordTransition(overlay, vessel_id, prev, 'stopped', now);
      }
      // Remove from active vessel tracking
      delete overlay.vessels[vessel_id];
      overlay.vessel_count = Object.keys(overlay.vessels).length;
      break;
    }
  }
}

function _recordTransition(overlay, vessel_id, from, to, timestamp) {
  overlay.transitions.push({ vessel_id, from, to, timestamp });
  // Keep last 100 transitions only
  if (overlay.transitions.length > 100) overlay.transitions.shift();
}

// ─── Consequence rules ────────────────────────────────────────────────────────

/**
 * Evaluate maritime consequence rules after each event.
 * Rules:
 *   1. Proximity alert — if two vessels are within proximity_radius, emit alert event
 *   2. Zone entry detection — if vessel position is inside a registered zone, emit zone event
 *
 * These are checked here rather than in the consequence compiler because they
 * require maritime domain knowledge (lat/lon distance, zone radius).
 */
function _evaluateConsequences(sessionId, payload, governance) {
  const overlay = _maritimeSessions.get(sessionId);
  if (!overlay) return [];

  const triggered = [];

  // ── Rule 1: Proximity alert ───────────────────────────────────────────────
  const vesselIds = Object.keys(overlay.vessels);
  for (let i = 0; i < vesselIds.length; i++) {
    for (let j = i + 1; j < vesselIds.length; j++) {
      const a = overlay.vessels[vesselIds[i]];
      const b = overlay.vessels[vesselIds[j]];
      const dist = _euclideanDistance(a.x, a.z, b.x, b.z);

      if (dist <= template.defaults.proximity_radius) {
        const alertKey = [vesselIds[i], vesselIds[j]].sort().join('::');
        const alreadyActive = overlay.alerts.some(al => al.key === alertKey);

        if (!alreadyActive) {
          // Emit proximity alert event back into the session
          applyMaritimeEvent(sessionId, MARITIME_EVENTS.VESSEL_PROXIMITY_ALERT, {
            vessel_id:       vesselIds[i],
            other_vessel_id: vesselIds[j],
            distance:        dist,
            lat:             a.lat,
            lon:             a.lon
          }, governance);

          triggered.push({
            rule:            'proximity_alert',
            vessel_id:       vesselIds[i],
            other_vessel_id: vesselIds[j],
            distance:        dist
          });
        }
      }
    }
  }

  // ── Rule 2: Zone entry detection ──────────────────────────────────────────
  const updatedVesselId = payload.vessel_id;
  const vessel = overlay.vessels[updatedVesselId];

  if (vessel && vessel.fsm_state !== 'in_zone') {
    Object.entries(overlay.zones).forEach(([zone_id, zone]) => {
      const { x: zx, z: zz } = _latLonToXZ(zone.lat, zone.lon);
      const dist = _euclideanDistance(vessel.x, vessel.z, zx, zz);

      if (dist <= zone.radius) {
        applyMaritimeEvent(sessionId, MARITIME_EVENTS.VESSEL_ENTERED_ZONE, {
          vessel_id: updatedVesselId,
          zone_id,
          lat:       vessel.lat,
          lon:       vessel.lon,
          speed:     vessel.speed
        }, governance);

        triggered.push({ rule: 'zone_entry', vessel_id: updatedVesselId, zone_id, distance: dist });
      }
    });
  }

  return triggered;
}

// ─── State assembly ───────────────────────────────────────────────────────────

function _getFullState(sessionId) {
  const gsmState = gsm.getCurrentState(sessionId);
  const overlay  = _maritimeSessions.get(sessionId);

  if (!overlay) return gsmState;

  return {
    ...gsmState,
    maritime: {
      vessel_count:  overlay.vessel_count,
      vessels:       { ...overlay.vessels },
      zones:         { ...overlay.zones },
      alerts:        [...overlay.alerts],
      alert_count:   overlay.alert_count,
      transitions:   [...overlay.transitions],
      execution_id:  overlay.execution_id,
      trace_id:      overlay.trace_id,
      last_updated:  overlay.last_updated
    }
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _euclideanDistance(x1, z1, x2, z2) {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(z2 - z1, 2));
}

function _latLonToXZ(lat, lon) {
  const { latToX, lonToZ } = require('./maritimeAdapter');
  return { x: latToX(lat), z: lonToZ(lon) };
}

function _fail(error) {
  console.error(`[MSM] Error: ${error}`);
  return { success: false, error };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  initSession,
  registerZone,
  applyMaritimeEvent,
  getMaritimeState,
  snapshotSession,
  destroySession,
  getActiveSessions
};

'use strict';

/**
 * maritimeEventMapper.js
 *
 * Maps maritime domain events → GSM-compatible runtime events.
 *
 * Maritime event          GSM event_type       Why
 * ─────────────────────   ──────────────────   ──────────────────────────────
 * vessel_spawned        → entity_spawned       vessel is a tracked entity
 * vessel_updated        → position_update      lat/lon change = position change
 * vessel_entered_zone   → collision            zone boundary = collision trigger
 * vessel_proximity_alert→ health_changed       alert = state flag via health field
 * vessel_stopped        → entity_destroyed     stopped vessel exits active tracking
 *
 * RULE: Every event produced by this module carries trace_id + execution_id.
 * No event exits without both fields present.
 */

const { v4: uuidv4 }          = require('uuid');
const { EVENT_TYPES }         = require('../../events/runtimeEvents');
const { latToX, lonToZ }      = require('./maritimeAdapter');

// ─── Maritime event type constants ───────────────────────────────────────────

const MARITIME_EVENTS = {
  VESSEL_SPAWNED:         'vessel_spawned',
  VESSEL_UPDATED:         'vessel_updated',
  VESSEL_ENTERED_ZONE:    'vessel_entered_zone',
  VESSEL_PROXIMITY_ALERT: 'vessel_proximity_alert',
  VESSEL_STOPPED:         'vessel_stopped'
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Map a maritime domain event → GSM runtime event.
 *
 * @param {string} maritimeEventType  - One of MARITIME_EVENTS values
 * @param {Object} payload            - Domain-specific data for this event
 * @param {Object} governance         - { trace_id, execution_id } — REQUIRED
 * @returns {{ success, event, error }}
 */
function mapEvent(maritimeEventType, payload, governance) {
  const traceCheck = _requireGovernance(governance);
  if (!traceCheck.valid) {
    return { success: false, event: null, error: traceCheck.error };
  }

  const { trace_id, execution_id } = governance;

  switch (maritimeEventType) {

    case MARITIME_EVENTS.VESSEL_SPAWNED:
      return { success: true, event: _vesselSpawned(payload, trace_id, execution_id) };

    case MARITIME_EVENTS.VESSEL_UPDATED:
      return { success: true, event: _vesselUpdated(payload, trace_id, execution_id) };

    case MARITIME_EVENTS.VESSEL_ENTERED_ZONE:
      return { success: true, event: _vesselEnteredZone(payload, trace_id, execution_id) };

    case MARITIME_EVENTS.VESSEL_PROXIMITY_ALERT:
      return { success: true, event: _vesselProximityAlert(payload, trace_id, execution_id) };

    case MARITIME_EVENTS.VESSEL_STOPPED:
      return { success: true, event: _vesselStopped(payload, trace_id, execution_id) };

    default:
      return { success: false, event: null, error: `Unknown maritime event: ${maritimeEventType}` };
  }
}

/**
 * Map an array of maritime events in sequence.
 * Stops on first governance failure; continues on mapping errors (logs them).
 *
 * @param {Array<{ type, payload }>} events
 * @param {Object} governance  - { trace_id, execution_id }
 * @returns {{ success, events: Array, errors: Array }}
 */
function mapEventBatch(events, governance) {
  const traceCheck = _requireGovernance(governance);
  if (!traceCheck.valid) {
    return { success: false, events: [], errors: [traceCheck.error] };
  }

  const out = { success: true, events: [], errors: [] };

  events.forEach((item, i) => {
    const result = mapEvent(item.type, item.payload, governance);
    if (result.success) {
      out.events.push(result.event);
    } else {
      out.success = false;
      out.errors.push({ index: i, type: item.type, error: result.error });
    }
  });

  return out;
}

// ─── Event builders ───────────────────────────────────────────────────────────

/**
 * vessel_spawned → entity_spawned
 * Vessel appears in the simulation for the first time.
 */
function _vesselSpawned(payload, trace_id, execution_id) {
  const { vessel_id, lat, lon, speed, heading, status } = payload;
  const x = latToX(lat);
  const z = lonToZ(lon);

  return _build(EVENT_TYPES.ENTITY_SPAWNED, {
    entities:     [vessel_id],
    game_session_id: execution_id,
    context: {
      entity_type: 'npc',
      domain_type: 'vessel',
      position:    { x, y: 0, z },
      speed,
      heading,
      status,
      lat,
      lon
    },
    metadata: { trace_id, execution_id, maritime_event: MARITIME_EVENTS.VESSEL_SPAWNED }
  });
}

/**
 * vessel_updated → position_update
 * Vessel moved — new lat/lon/heading/speed received.
 */
function _vesselUpdated(payload, trace_id, execution_id) {
  const { vessel_id, lat, lon, speed, heading, status, timestamp } = payload;
  const x = latToX(lat);
  const z = lonToZ(lon);

  return _build(EVENT_TYPES.POSITION_UPDATE, {
    entities:        [vessel_id],
    game_session_id: execution_id,
    timestamp:       timestamp || Date.now(),
    context: {
      position:    [x, 0, z],
      speed,
      heading,
      status,
      lat,
      lon
    },
    metadata: { trace_id, execution_id, maritime_event: MARITIME_EVENTS.VESSEL_UPDATED }
  });
}

/**
 * vessel_entered_zone → collision
 * Vessel crossed a zone boundary — treated as a collision trigger.
 * entities[0] = vessel, entities[1] = zone
 */
function _vesselEnteredZone(payload, trace_id, execution_id) {
  const { vessel_id, zone_id, lat, lon, speed } = payload;
  const x = latToX(lat);
  const z = lonToZ(lon);

  return _build(EVENT_TYPES.COLLISION, {
    entities:        [vessel_id, zone_id || 'zone_boundary'],
    game_session_id: execution_id,
    context: {
      entity_type:     'obstacle',       // zone boundary = obstacle in engine terms
      domain_type:     'zone_entry',
      position:        { x, y: 0, z },
      velocity:        speed || 0,
      collision_force: 0,                // no physical impact — informational
      damage:          0,
      lat,
      lon,
      zone_id:         zone_id || 'zone_boundary'
    },
    metadata: { trace_id, execution_id, maritime_event: MARITIME_EVENTS.VESSEL_ENTERED_ZONE }
  });
}

/**
 * vessel_proximity_alert → health_changed
 * Two vessels are within proximity_radius of each other.
 * Uses health_changed as the state flag: delta = -1 signals an active alert.
 * The GSM health field on the vessel entity reflects alert state (1=clear, 0=alert).
 */
function _vesselProximityAlert(payload, trace_id, execution_id) {
  const { vessel_id, other_vessel_id, distance, lat, lon } = payload;
  const x = latToX(lat);
  const z = lonToZ(lon);

  return _build(EVENT_TYPES.HEALTH_CHANGED, {
    entities:        [vessel_id, other_vessel_id || 'unknown_vessel'],
    game_session_id: execution_id,
    context: {
      delta:       -1,                   // alert active = health drops to 0
      health:      0,
      domain_type: 'proximity_alert',
      distance,
      position:    { x, y: 0, z },
      lat,
      lon,
      other_vessel_id: other_vessel_id || null
    },
    metadata: { trace_id, execution_id, maritime_event: MARITIME_EVENTS.VESSEL_PROXIMITY_ALERT }
  });
}

/**
 * vessel_stopped → entity_destroyed
 * Vessel has stopped (speed = 0, status = anchored) and exits active tracking.
 */
function _vesselStopped(payload, trace_id, execution_id) {
  const { vessel_id, lat, lon } = payload;
  const x = latToX(lat);
  const z = lonToZ(lon);

  return _build(EVENT_TYPES.ENTITY_DESTROYED, {
    entities:        [vessel_id],
    game_session_id: execution_id,
    context: {
      entity_type: 'npc',
      domain_type: 'vessel_stopped',
      position:    { x, y: 0, z },
      lat,
      lon
    },
    metadata: { trace_id, execution_id, maritime_event: MARITIME_EVENTS.VESSEL_STOPPED }
  });
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

/**
 * Build a fully-formed runtime event.
 * Guarantees event_id, timestamp, and trace propagation on every event.
 */
function _build(eventType, opts = {}) {
  return {
    event_type:      eventType,
    event_id:        uuidv4(),
    timestamp:       opts.timestamp || Date.now(),
    game_session_id: opts.game_session_id || null,
    entities:        opts.entities  || [],
    context:         opts.context   || {},
    metadata:        opts.metadata  || {}
  };
}

/**
 * Enforce governance fields before any event is produced.
 * trace_id and execution_id are MANDATORY on every event.
 */
function _requireGovernance(governance) {
  if (!governance)                  return { valid: false, error: 'governance object is required' };
  if (!governance.trace_id)         return { valid: false, error: 'trace_id is required in governance' };
  if (!governance.execution_id)     return { valid: false, error: 'execution_id is required in governance' };
  return { valid: true };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  MARITIME_EVENTS,
  mapEvent,
  mapEventBatch
};

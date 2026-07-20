'use strict';

/**
 * BehaviorExecutor.js
 *
 * Interprets SumScript behavior scripts against entity state.
 *
 * Rules:
 *   - NO eval(), no Function(), no dynamic code execution
 *   - Each behavior script is a named handler in a closed dispatch table
 *   - Behaviors produce a delta (position/velocity/state change) — they do NOT
 *     mutate entity state directly. The SimEngine applies the delta.
 *   - All math is deterministic given the same inputs
 *
 * Supported scripts (must match SumScriptSchema.BEHAVIOR_SCRIPTS):
 *   patrol    — move along a waypoint list, loop
 *   idle      — no movement, stay in place
 *   move_to   — move toward a target position at given speed
 *   flee      — move away from a threat position at given speed
 *   anchor    — locked in place, state = stopped
 *   track     — face and follow a target entity
 */

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Execute a single behavior against an entity's current state.
 *
 * @param {Object} behavior  - Normalized behavior { id, script, params }
 * @param {Object} entity    - Current entity state { id, position, rotation, velocity, state, meta }
 * @param {Object} context   - Execution context { tick, dt, entities_map, rng }
 * @returns {Object} delta   - { position?, rotation?, velocity?, state?, meta?, events[] }
 */
function execute(behavior, entity, context) {
  const handler = BEHAVIOR_HANDLERS[behavior.script];
  if (!handler) {
    return _delta({ events: [_event('behavior_unknown', entity.id, { script: behavior.script })] });
  }

  try {
    return handler(behavior.params, entity, context);
  } catch (err) {
    return _delta({ events: [_event('behavior_error', entity.id, { script: behavior.script, error: err.message })] });
  }
}

/**
 * Execute all behaviors assigned to an entity in order.
 * Later behaviors override earlier ones for the same delta field.
 *
 * @param {Object}   entity      - Current entity state
 * @param {Object[]} behaviors   - Array of normalized behavior objects
 * @param {Object}   context     - Execution context
 * @returns {Object} merged delta
 */
function executeAll(entity, behaviors, context) {
  const merged = _delta({});

  for (const behavior of behaviors) {
    const delta = execute(behavior, entity, context);
    _mergeDelta(merged, delta);
  }

  return merged;
}

// ─── Behavior handlers ────────────────────────────────────────────────────────
// Each handler receives (params, entity, context) and returns a delta.
// Handlers are pure functions — no side effects, no external calls.

const BEHAVIOR_HANDLERS = {

  // ── idle ──────────────────────────────────────────────────────────────────
  // Entity stays in place. Velocity zeroed.
  idle(_params, entity, _ctx) {
    return _delta({
      velocity: [0, 0, 0],
      state:    entity.state === 'active' ? 'idle' : entity.state
    });
  },

  // ── anchor ────────────────────────────────────────────────────────────────
  // Entity is locked. Position unchanged, velocity zeroed, state = stopped.
  anchor(_params, entity, _ctx) {
    return _delta({
      position: [...entity.position],
      velocity: [0, 0, 0],
      state:    'stopped'
    });
  },

  // ── move_to ───────────────────────────────────────────────────────────────
  // Move toward params.target [x, y, z] at params.speed units/tick.
  // Stops when within params.threshold (default 0.5).
  move_to(params, entity, _ctx) {
    const target    = _vec3(params.target, entity.position);
    const speed     = _num(params.speed, 1);
    const threshold = _num(params.threshold, 0.5);

    const dir  = _subtract(target, entity.position);
    const dist = _magnitude(dir);

    if (dist <= threshold) {
      return _delta({
        velocity: [0, 0, 0],
        state:    'idle',
        events:   [_event('reached_target', entity.id, { target })]
      });
    }

    const norm = _normalize(dir);
    const step = Math.min(speed, dist);
    const velocity = _scale(norm, step);

    return _delta({ velocity, state: 'active' });
  },

  // ── flee ──────────────────────────────────────────────────────────────────
  // Move directly away from params.threat [x, y, z] at params.speed.
  flee(params, entity, _ctx) {
    const threat = _vec3(params.threat, entity.position);
    const speed  = _num(params.speed, 1);

    const dir  = _subtract(entity.position, threat);  // away from threat
    const dist = _magnitude(dir);

    if (dist < 0.001) {
      // Exactly on top of threat — move in +x as fallback
      return _delta({ velocity: [speed, 0, 0], state: 'active' });
    }

    const norm     = _normalize(dir);
    const velocity = _scale(norm, speed);

    return _delta({ velocity, state: 'active' });
  },

  // ── patrol ────────────────────────────────────────────────────────────────
  // Move through params.waypoints[] in order, looping.
  // Waypoint index is tracked in entity.meta.patrol_index.
  patrol(params, entity, _ctx) {
    const waypoints = Array.isArray(params.waypoints) ? params.waypoints : [];
    const speed     = _num(params.speed, 1);
    const threshold = _num(params.threshold, 0.5);

    if (waypoints.length === 0) {
      return _delta({ velocity: [0, 0, 0] });
    }

    const idx    = _num(entity.meta.patrol_index, 0) % waypoints.length;
    const target = _vec3(waypoints[idx], entity.position);
    const dir    = _subtract(target, entity.position);
    const dist   = _magnitude(dir);

    if (dist <= threshold) {
      // Reached this waypoint — advance index
      const next_index = (idx + 1) % waypoints.length;
      return _delta({
        velocity: [0, 0, 0],
        meta:     { patrol_index: next_index },
        events:   [_event('waypoint_reached', entity.id, { waypoint_index: idx, next_index })]
      });
    }

    const norm     = _normalize(dir);
    const step     = Math.min(speed, dist);
    const velocity = _scale(norm, step);

    return _delta({ velocity, state: 'active', meta: { patrol_index: idx } });
  },

  // ── track ─────────────────────────────────────────────────────────────────
  // Face and follow a target entity by id (params.target_id).
  // Requires context.entities_map to resolve the target.
  track(params, entity, context) {
    const target_id = params.target_id;
    const speed     = _num(params.speed, 1);

    if (!target_id) {
      return _delta({ events: [_event('track_no_target', entity.id, {})] });
    }

    const target_entity = context.entities_map[target_id];
    if (!target_entity) {
      return _delta({ events: [_event('track_target_missing', entity.id, { target_id })] });
    }

    const dir  = _subtract(target_entity.position, entity.position);
    const dist = _magnitude(dir);

    if (dist < 0.001) {
      return _delta({ velocity: [0, 0, 0] });
    }

    const norm     = _normalize(dir);
    const step     = Math.min(speed, dist);
    const velocity = _scale(norm, step);

    // Rotation: face the target (y-axis rotation in degrees)
    const angle_y = Math.atan2(dir[0], dir[2]) * (180 / Math.PI);

    return _delta({
      velocity,
      rotation: [0, angle_y, 0],
      state:    'active'
    });
  }
};

// ─── Delta helpers ────────────────────────────────────────────────────────────

function _delta(fields) {
  return {
    position: fields.position || null,
    rotation: fields.rotation || null,
    velocity: fields.velocity || null,
    state:    fields.state    || null,
    meta:     fields.meta     || null,
    events:   fields.events   || []
  };
}

function _mergeDelta(base, incoming) {
  if (incoming.position !== null) base.position = incoming.position;
  if (incoming.rotation !== null) base.rotation = incoming.rotation;
  if (incoming.velocity !== null) base.velocity = incoming.velocity;
  if (incoming.state    !== null) base.state    = incoming.state;
  if (incoming.meta     !== null) base.meta     = { ...(base.meta || {}), ...incoming.meta };
  base.events.push(...incoming.events);
}

function _event(type, entity_id, payload) {
  return { type, entity_id, payload, emitted_at: null }; // emitted_at set by SimEngine
}

// ─── Vector math (pure, no external deps) ────────────────────────────────────

function _vec3(val, fallback) {
  if (Array.isArray(val) && val.length === 3) return val.map(Number);
  return [...fallback];
}

function _num(val, fallback) {
  const n = parseFloat(val);
  return isNaN(n) ? fallback : n;
}

function _subtract(a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function _magnitude(v) {
  return Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
}

function _normalize(v) {
  const mag = _magnitude(v);
  if (mag < 0.0001) return [0, 0, 0];
  return [v[0] / mag, v[1] / mag, v[2] / mag];
}

function _scale(v, s) {
  return [v[0] * s, v[1] * s, v[2] * s];
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { execute, executeAll };

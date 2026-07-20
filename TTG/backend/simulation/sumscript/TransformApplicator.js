'use strict';

/**
 * TransformApplicator.js
 *
 * Applies SumScript transform operations to entity state.
 *
 * Transforms are declarative operations defined in the contract.
 * They are applied once at simulation initialization (before tick loop starts),
 * or can be queued mid-simulation by rule actions.
 *
 * Operations:
 *   move      — offset position by [dx, dy, dz]
 *   rotate    — set rotation to [rx, ry, rz] (degrees)
 *   scale     — set scale to [sx, sy, sz] (stored in meta.scale)
 *   teleport  — set position to exact [x, y, z]
 *
 * All operations are pure — they return a new entity state, never mutate.
 */

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Apply a single transform to an entity.
 *
 * @param {Object} transform  - Normalized transform { entity_id, op, params }
 * @param {Object} entity     - Current entity state
 * @returns {{ entity: Object, event: Object }}
 *   entity — new entity state with transform applied
 *   event  — structured event describing what changed
 */
function apply(transform, entity) {
  const handler = TRANSFORM_HANDLERS[transform.op];

  if (!handler) {
    return {
      entity,
      event: _event('transform_unknown', entity.id, { op: transform.op })
    };
  }

  return handler(transform.params, entity);
}

/**
 * Apply a list of transforms to an entities map.
 * Transforms targeting unknown entity_ids are skipped (logged as events).
 *
 * @param {Object[]} transforms  - Array of normalized transforms
 * @param {Object}   entities_map - { [entity_id]: entity }
 * @returns {{ entities_map: Object, events: Object[] }}
 */
function applyAll(transforms, entities_map) {
  const updated = { ...entities_map };
  const events  = [];

  for (const transform of transforms) {
    const entity = updated[transform.entity_id];

    if (!entity) {
      events.push(_event('transform_target_missing', null, { entity_id: transform.entity_id, op: transform.op }));
      continue;
    }

    const result = apply(transform, entity);
    updated[transform.entity_id] = result.entity;
    events.push(result.event);
  }

  return { entities_map: updated, events };
}

// ─── Transform handlers ───────────────────────────────────────────────────────

const TRANSFORM_HANDLERS = {

  // move: offset position by delta
  move(params, entity) {
    const delta = _vec3(params.delta, [0, 0, 0]);
    const prev  = [...entity.position];
    const next  = [
      entity.position[0] + delta[0],
      entity.position[1] + delta[1],
      entity.position[2] + delta[2]
    ];

    return {
      entity: { ...entity, position: next },
      event:  _event('transform_move', entity.id, { from: prev, to: next, delta })
    };
  },

  // rotate: set rotation to absolute [rx, ry, rz]
  rotate(params, entity) {
    const rotation = _vec3(params.rotation, entity.rotation || [0, 0, 0]);
    // Normalize angles to [0, 360)
    const normalized = rotation.map(a => ((a % 360) + 360) % 360);

    return {
      entity: { ...entity, rotation: normalized },
      event:  _event('transform_rotate', entity.id, { rotation: normalized })
    };
  },

  // scale: store in meta.scale (simulation doesn't use scale for physics)
  scale(params, entity) {
    const scale = _vec3(params.scale, [1, 1, 1]);
    const meta  = { ...(entity.meta || {}), scale };

    return {
      entity: { ...entity, meta },
      event:  _event('transform_scale', entity.id, { scale })
    };
  },

  // teleport: set position to exact coordinates
  teleport(params, entity) {
    const target = _vec3(params.position, entity.position);
    const prev   = [...entity.position];

    return {
      entity: { ...entity, position: target, velocity: [0, 0, 0] },
      event:  _event('transform_teleport', entity.id, { from: prev, to: target })
    };
  }
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _vec3(val, fallback) {
  if (Array.isArray(val) && val.length === 3) return val.map(Number);
  return [...fallback];
}

function _event(type, entity_id, payload) {
  return { type, entity_id, payload };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { apply, applyAll };

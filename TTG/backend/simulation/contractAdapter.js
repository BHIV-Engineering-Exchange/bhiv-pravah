'use strict';

/**
 * contractAdapter.js
 *
 * Converts a simulation input contract into a valid SumScript contract
 * that SimEngine.run() can consume.
 *
 * Input  : {
 *   trace_id, execution_id, domain, scenario,
 *   entities[],
 *   behaviors[],
 *   rules[],
 *   constraints: { movement, physics, player_params }
 * }
 * Output : { valid, sumscript, errors[] }
 *
 * Rules:
 *   - game_mode is NOT accepted — removed entirely
 *   - Caller declares behaviors explicitly — no script inference
 *   - speed, physics, player_params pass through via constraints
 *   - Fail-closed: missing required field → reject
 */

const REQUIRED_FIELDS = ['trace_id', 'execution_id', 'entities', 'behaviors'];

/**
 * @param {Object} input
 * @returns {{ valid: boolean, sumscript: Object|null, errors: string[] }}
 */
function adapt(input) {
  const errors = _validateInput(input);
  if (errors.length > 0) {
    return { valid: false, sumscript: null, errors };
  }

  const constraints = input.constraints || {};

  const sumscript = {
    trace_id:     input.trace_id,
    execution_id: input.execution_id,
    entities:     _mapEntities(input.entities),
    behaviors:    input.behaviors,
    rules:        Array.isArray(input.rules) ? input.rules : [],
    transforms:   _extractTransforms(input.entities),
    // constraints passed through for SimEngine context (speed, physics, etc.)
    constraints: {
      movement:     constraints.movement     || {},
      physics:      constraints.physics      || {},
      player_params: constraints.player_params || {}
    }
  };

  return { valid: true, sumscript, errors: [] };
}

// ─── Validation ───────────────────────────────────────────────────────────────

function _validateInput(input) {
  const errors = [];

  if (!input || typeof input !== 'object') {
    return ['input must be an object'];
  }

  // Reject game_mode — it is not part of the generic contract
  if ('game_mode' in input) {
    errors.push('game_mode is not allowed — use domain + scenario instead');
  }

  for (const field of REQUIRED_FIELDS) {
    if (!input[field]) errors.push(`${field} is required`);
  }

  if (errors.length > 0) return errors;

  if (!Array.isArray(input.entities) || input.entities.length === 0) {
    errors.push('entities must be a non-empty array');
  }

  if (!Array.isArray(input.behaviors) || input.behaviors.length === 0) {
    errors.push('behaviors must be a non-empty array');
  }

  if (errors.length > 0) return errors;

  input.entities.forEach((e, i) => {
    if (!e.id)       errors.push(`entities[${i}].id is required`);
    if (!e.type)     errors.push(`entities[${i}].type is required`);
    if (!e.position) errors.push(`entities[${i}].position is required`);
  });

  input.behaviors.forEach((b, i) => {
    if (!b.id)     errors.push(`behaviors[${i}].id is required`);
    if (!b.script) errors.push(`behaviors[${i}].script is required`);
  });

  return errors;
}

// ─── Mappers ──────────────────────────────────────────────────────────────────

// Entities are mapped as declared — no field injection.
// speed lives in behavior.params, not in entity.meta.
// SumScript is the single source of truth for movement.
function _mapEntities(entities) {
  return entities.map(e => ({
    id:        e.id,
    type:      e.type,
    position:  e.position,
    rotation:  e.rotation  || [0, 0, 0],
    velocity:  e.velocity  || [0, 0, 0],
    state:     e.state     || 'active',
    behaviors: e.behaviors || [],
    meta:      e.meta      || {}
  }));
}

function _extractTransforms(entities) {
  return entities
    .filter(e => Array.isArray(e.rotation) && e.rotation.some(v => v !== 0))
    .map(e => ({
      entity_id: e.id,
      op:        'rotate',
      params:    { rotation: e.rotation }
    }));
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { adapt };

'use strict';

/**
 * SumScriptSchema.js
 *
 * Defines the canonical SumScript contract shape and validates it.
 *
 * A SumScript contract has exactly 4 top-level sections:
 *
 *   entities   — what exists in the simulation
 *   transforms — positional/rotational operations applied to entities
 *   rules      — trigger → condition → action declarations (data only, no logic)
 *   behaviors  — named behavior scripts assigned to entities
 *
 * This module ONLY defines and validates the shape.
 * Execution lives in BehaviorExecutor.js.
 * Interpretation lives in the SimEngine.
 */

// ─── Allowed values (closed sets) ────────────────────────────────────────────

// Open string — any domain type accepted (vessel, drone, vehicle, sensor, node, etc.)
// Removed closed enum: runtime does not restrict entity types.
// Open string — any state accepted from contract.
// Removed closed enum: runtime does not restrict entity states.
const ENTITY_STATES    = ['active', 'idle', 'stopped', 'destroyed']; // kept for normalizer default only
const TRANSFORM_OPS    = ['move', 'rotate', 'scale', 'teleport'];
const RULE_TRIGGERS    = ['on_tick', 'on_collision', 'on_zone_enter', 'on_zone_exit', 'on_state_change'];
const RULE_ACTIONS     = ['set_state', 'emit_event', 'flag_entity', 'block_entity', 'log'];
const BEHAVIOR_SCRIPTS = ['patrol', 'idle', 'move_to', 'flee', 'anchor', 'track'];

// ─── Default values ───────────────────────────────────────────────────────────

const ENTITY_DEFAULTS = {
  state:     'active',
  velocity:  [0, 0, 0],
  behaviors: []
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Validate a raw SumScript contract object.
 * Returns { valid, errors[] } — never throws.
 *
 * @param {*} contract
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validate(contract) {
  const errors = [];

  if (!contract || typeof contract !== 'object') {
    return { valid: false, errors: ['contract must be an object'] };
  }

  // ── Required top-level fields ─────────────────────────────────────────────
  if (!contract.trace_id || typeof contract.trace_id !== 'string') {
    errors.push('trace_id is required (string)');
  }
  if (!contract.execution_id || typeof contract.execution_id !== 'string') {
    errors.push('execution_id is required (string)');
  }

  // ── entities ──────────────────────────────────────────────────────────────
  if (!Array.isArray(contract.entities) || contract.entities.length === 0) {
    errors.push('entities must be a non-empty array');
  } else {
    contract.entities.forEach((e, i) => _validateEntity(e, i, errors));
  }

  // ── transforms ────────────────────────────────────────────────────────────
  if (contract.transforms !== undefined) {
    if (!Array.isArray(contract.transforms)) {
      errors.push('transforms must be an array');
    } else {
      contract.transforms.forEach((t, i) => _validateTransform(t, i, errors));
    }
  }

  // ── rules ─────────────────────────────────────────────────────────────────
  if (contract.rules !== undefined) {
    if (!Array.isArray(contract.rules)) {
      errors.push('rules must be an array');
    } else {
      contract.rules.forEach((r, i) => _validateRule(r, i, errors));
    }
  }

  // ── behaviors ─────────────────────────────────────────────────────────────
  if (contract.behaviors !== undefined) {
    if (!Array.isArray(contract.behaviors)) {
      errors.push('behaviors must be an array');
    } else {
      contract.behaviors.forEach((b, i) => _validateBehavior(b, i, errors));
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Normalize a validated SumScript contract:
 * - fills in defaults for optional fields
 * - coerces numeric types
 * - strips unknown fields
 *
 * Call validate() first. normalize() assumes the contract is valid.
 *
 * @param {Object} contract
 * @returns {Object} normalized contract
 */
function normalize(contract) {
  return {
    trace_id:     contract.trace_id,
    execution_id: contract.execution_id,
    seed:         contract.seed || _seedFromTraceId(contract.trace_id),

    entities: contract.entities.map(_normalizeEntity),

    transforms: Array.isArray(contract.transforms)
      ? contract.transforms.map(_normalizeTransform)
      : [],

    rules: Array.isArray(contract.rules)
      ? contract.rules.map(_normalizeRule)
      : [],

    behaviors: Array.isArray(contract.behaviors)
      ? contract.behaviors.map(_normalizeBehavior)
      : []
  };
}

// ─── Entity validators / normalizers ─────────────────────────────────────────

function _validateEntity(e, i, errors) {
  const p = `entities[${i}]`;

  if (!e.id || typeof e.id !== 'string') {
    errors.push(`${p}.id is required (string)`);
  }
  if (!e.type || typeof e.type !== 'string' || e.type.trim() === '') {
    errors.push(`${p}.type is required (non-empty string)`);
  }
  if (!e.position || !Array.isArray(e.position) || e.position.length !== 3) {
    errors.push(`${p}.position must be [x, y, z]`);
  }
  if (e.state !== undefined && (typeof e.state !== 'string' || e.state.trim() === '')) {
    errors.push(`${p}.state must be a non-empty string`);
  }
  if (e.behaviors !== undefined) {
    if (!Array.isArray(e.behaviors)) {
      errors.push(`${p}.behaviors must be an array of behavior ids`);
    } else {
      e.behaviors.forEach((b, j) => {
        if (typeof b !== 'string') errors.push(`${p}.behaviors[${j}] must be a string (behavior id)`);
      });
    }
  }
}

function _normalizeEntity(e) {
  return {
    id:        e.id,
    type:      e.type,
    position:  e.position.map(Number),
    rotation:  Array.isArray(e.rotation) && e.rotation.length === 3
      ? e.rotation.map(Number)
      : [0, 0, 0],
    velocity:  Array.isArray(e.velocity) && e.velocity.length === 3
      ? e.velocity.map(Number)
      : [...ENTITY_DEFAULTS.velocity],
    state:     (e.state && typeof e.state === 'string') ? e.state : ENTITY_DEFAULTS.state,
    behaviors: Array.isArray(e.behaviors) ? [...e.behaviors] : [],
    meta:      e.meta && typeof e.meta === 'object' ? { ...e.meta } : {}
  };
}

// ─── Transform validators / normalizers ──────────────────────────────────────

function _validateTransform(t, i, errors) {
  const p = `transforms[${i}]`;

  if (!t.entity_id || typeof t.entity_id !== 'string') {
    errors.push(`${p}.entity_id is required (string)`);
  }
  if (!TRANSFORM_OPS.includes(t.op)) {
    errors.push(`${p}.op must be one of: ${TRANSFORM_OPS.join(', ')} — got: ${t.op}`);
  }
  if (!t.params || typeof t.params !== 'object') {
    errors.push(`${p}.params is required (object)`);
  }
}

function _normalizeTransform(t) {
  return {
    entity_id: t.entity_id,
    op:        t.op,
    params:    { ...t.params }
  };
}

// ─── Rule validators / normalizers ───────────────────────────────────────────

function _validateRule(r, i, errors) {
  const p = `rules[${i}]`;

  if (!r.id || typeof r.id !== 'string') {
    errors.push(`${p}.id is required (string)`);
  }
  if (!RULE_TRIGGERS.includes(r.trigger)) {
    errors.push(`${p}.trigger must be one of: ${RULE_TRIGGERS.join(', ')} — got: ${r.trigger}`);
  }
  if (!r.condition || typeof r.condition !== 'object') {
    errors.push(`${p}.condition is required (object)`);
  } else {
    if (!r.condition.field || typeof r.condition.field !== 'string') {
      errors.push(`${p}.condition.field is required (string)`);
    }
    if (!r.condition.op || typeof r.condition.op !== 'string') {
      errors.push(`${p}.condition.op is required — e.g. "gt", "lt", "eq", "gte", "lte"`);
    }
    if (r.condition.value === undefined) {
      errors.push(`${p}.condition.value is required`);
    }
  }
  if (!r.action || typeof r.action !== 'object') {
    errors.push(`${p}.action is required (object)`);
  } else {
    if (!RULE_ACTIONS.includes(r.action.type)) {
      errors.push(`${p}.action.type must be one of: ${RULE_ACTIONS.join(', ')} — got: ${r.action.type}`);
    }
  }
}

function _normalizeRule(r) {
  return {
    id:        r.id,
    trigger:   r.trigger,
    condition: {
      field:  r.condition.field,
      op:     r.condition.op,
      value:  r.condition.value,
      target: r.condition.target || null   // optional: entity_id to scope condition to
    },
    action: {
      type:   r.action.type,
      params: r.action.params && typeof r.action.params === 'object'
        ? { ...r.action.params }
        : {}
    },
    enabled: r.enabled !== false   // default true
  };
}

// ─── Behavior validators / normalizers ───────────────────────────────────────

function _validateBehavior(b, i, errors) {
  const p = `behaviors[${i}]`;

  if (!b.id || typeof b.id !== 'string') {
    errors.push(`${p}.id is required (string)`);
  }
  if (!BEHAVIOR_SCRIPTS.includes(b.script)) {
    errors.push(`${p}.script must be one of: ${BEHAVIOR_SCRIPTS.join(', ')} — got: ${b.script}`);
  }
}

function _normalizeBehavior(b) {
  return {
    id:     b.id,
    script: b.script,
    params: b.params && typeof b.params === 'object' ? { ...b.params } : {}
  };
}

// ─── Seed derivation ─────────────────────────────────────────────────────────
// Deterministic integer seed from trace_id string.
// Same trace_id always produces the same seed — required for replay.

function _seedFromTraceId(trace_id) {
  let hash = 0;
  for (let i = 0; i < trace_id.length; i++) {
    hash = (Math.imul(31, hash) + trace_id.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  validate,
  normalize,
  ENTITY_STATES,
  TRANSFORM_OPS,
  RULE_TRIGGERS,
  RULE_ACTIONS,
  BEHAVIOR_SCRIPTS
};

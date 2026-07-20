'use strict';

/**
 * contractValidator.v1.js
 *
 * Runtime enforcer for simulationContract.v1.json
 *
 * Validates every incoming simulation request against the canonical schema.
 * Fail-closed — any violation returns errors, execution is blocked.
 *
 * Does NOT use AJV (no extra dependency).
 * Mirrors the schema rules directly in code so the schema file
 * and this validator are always in sync.
 */

// Open string — any domain type accepted. No enum restriction.
const ENTITY_TYPES_REMOVED = null; // was: ['vessel', 'obstacle', 'zone', 'marker', 'agent']
const ENTITY_STATES    = ['active', 'idle', 'stopped', 'destroyed'];
const BEHAVIOR_SCRIPTS = ['patrol', 'idle', 'move_to', 'flee', 'anchor', 'track'];
const RULE_TRIGGERS    = ['on_tick', 'on_collision', 'on_zone_enter', 'on_zone_exit', 'on_state_change'];
const RULE_ACTIONS     = ['set_state', 'emit_event', 'flag_entity', 'block_entity', 'log'];
const CONDITION_OPS    = ['eq', 'neq', 'gt', 'lt', 'gte', 'lte'];

// Fields that are NOT part of the v1 contract — reject on sight
const BANNED_FIELDS = ['game_mode', 'spawn_rules', 'scoring', 'score_rules', 'end_conditions'];

/**
 * Validate an incoming request body against simulationContract.v1
 *
 * @param {*} body
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validate(body) {
  const errors = [];

  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return { valid: false, errors: ['request body must be a JSON object'] };
  }

  // ── Banned fields — hard reject ───────────────────────────────────────────
  for (const field of BANNED_FIELDS) {
    if (field in body) {
      errors.push(`'${field}' is not allowed in simulationContract.v1 — remove it`);
    }
  }

  // ── Required top-level fields ─────────────────────────────────────────────
  if (!body.trace_id     || typeof body.trace_id     !== 'string') errors.push('trace_id is required (string)');
  if (!body.execution_id || typeof body.execution_id !== 'string') errors.push('execution_id is required (string)');
  if (!body.domain       || typeof body.domain       !== 'string') errors.push('domain is required (string)');
  if (!body.scenario     || typeof body.scenario     !== 'string') errors.push('scenario is required (string)');

  // ── ticks (optional) ─────────────────────────────────────────────────────
  if (body.ticks !== undefined) {
    if (!Number.isInteger(body.ticks) || body.ticks < 1 || body.ticks > 1000) {
      errors.push('ticks must be an integer between 1 and 1000');
    }
  }

  // ── entities ──────────────────────────────────────────────────────────────
  if (!Array.isArray(body.entities) || body.entities.length === 0) {
    errors.push('entities must be a non-empty array');
  } else {
    body.entities.forEach((e, i) => _validateEntity(e, i, errors));
  }

  // ── behaviors ─────────────────────────────────────────────────────────────
  if (!Array.isArray(body.behaviors) || body.behaviors.length === 0) {
    errors.push('behaviors must be a non-empty array');
  } else {
    body.behaviors.forEach((b, i) => _validateBehavior(b, i, errors));
  }

  // ── rules (optional) ─────────────────────────────────────────────────────
  if (body.rules !== undefined) {
    if (!Array.isArray(body.rules)) {
      errors.push('rules must be an array');
    } else {
      body.rules.forEach((r, i) => _validateRule(r, i, errors));
    }
  }

  // ── constraints (optional) ────────────────────────────────────────────────
  if (body.constraints !== undefined) {
    _validateConstraints(body.constraints, errors);
  }

  // ── No extra top-level fields ─────────────────────────────────────────────
  const ALLOWED_TOP = new Set(['trace_id', 'execution_id', 'domain', 'scenario', 'ticks', 'entities', 'behaviors', 'rules', 'constraints']);
  for (const key of Object.keys(body)) {
    if (!ALLOWED_TOP.has(key)) {
      errors.push(`unknown top-level field '${key}' — not part of simulationContract.v1`);
    }
  }

  return { valid: errors.length === 0, errors };
}

// ─── Entity ───────────────────────────────────────────────────────────────────

function _validateEntity(e, i, errors) {
  const p = `entities[${i}]`;
  if (!e.id       || typeof e.id !== 'string')          errors.push(`${p}.id is required (string)`);
  if (!e.type     || typeof e.type !== 'string' || e.type.trim() === '') errors.push(`${p}.type is required (non-empty string)`);
  if (!_isVec3(e.position))                             errors.push(`${p}.position must be [x, y, z]`);
  if (!Array.isArray(e.behaviors))                      errors.push(`${p}.behaviors must be an array`);
  if (e.rotation !== undefined && !_isVec3(e.rotation)) errors.push(`${p}.rotation must be [rx, ry, rz]`);
  if (e.velocity !== undefined && !_isVec3(e.velocity)) errors.push(`${p}.velocity must be [vx, vy, vz]`);
  if (e.state !== undefined && (typeof e.state !== 'string' || e.state.trim() === '')) {
    errors.push(`${p}.state must be a non-empty string`);
  }
}

// ─── Behavior ─────────────────────────────────────────────────────────────────

function _validateBehavior(b, i, errors) {
  const p = `behaviors[${i}]`;
  if (!b.id     || typeof b.id !== 'string')        errors.push(`${p}.id is required (string)`);
  if (!BEHAVIOR_SCRIPTS.includes(b.script))         errors.push(`${p}.script must be one of: ${BEHAVIOR_SCRIPTS.join(', ')} — got: ${b.script}`);
  if (b.params !== undefined && typeof b.params !== 'object') errors.push(`${p}.params must be an object`);
}

// ─── Rule ─────────────────────────────────────────────────────────────────────

function _validateRule(r, i, errors) {
  const p = `rules[${i}]`;
  if (!r.id      || typeof r.id !== 'string')    errors.push(`${p}.id is required (string)`);
  if (!RULE_TRIGGERS.includes(r.trigger))        errors.push(`${p}.trigger must be one of: ${RULE_TRIGGERS.join(', ')} — got: ${r.trigger}`);

  if (!r.condition || typeof r.condition !== 'object') {
    errors.push(`${p}.condition is required (object)`);
  } else {
    if (!r.condition.field || typeof r.condition.field !== 'string') errors.push(`${p}.condition.field is required (string)`);
    if (!CONDITION_OPS.includes(r.condition.op))  errors.push(`${p}.condition.op must be one of: ${CONDITION_OPS.join(', ')} — got: ${r.condition.op}`);
    if (r.condition.value === undefined)           errors.push(`${p}.condition.value is required`);
  }

  if (!r.action || typeof r.action !== 'object') {
    errors.push(`${p}.action is required (object)`);
  } else {
    if (!RULE_ACTIONS.includes(r.action.type))   errors.push(`${p}.action.type must be one of: ${RULE_ACTIONS.join(', ')} — got: ${r.action.type}`);
  }
}

// ─── Constraints ──────────────────────────────────────────────────────────────

function _validateConstraints(c, errors) {
  if (typeof c !== 'object' || Array.isArray(c)) {
    errors.push('constraints must be an object'); return;
  }

  const ALLOWED_CONSTRAINT_KEYS = new Set(['movement', 'physics', 'player_params']);
  for (const key of Object.keys(c)) {
    if (!ALLOWED_CONSTRAINT_KEYS.has(key)) {
      errors.push(`constraints.${key} is not allowed — only movement, physics, player_params`);
    }
  }

  if (c.movement !== undefined) {
    if (c.movement.speed !== undefined && typeof c.movement.speed !== 'number') {
      errors.push('constraints.movement.speed must be a number');
    }
  }

  if (c.physics !== undefined) {
    if (c.physics.gravity !== undefined && !_isVec3(c.physics.gravity)) {
      errors.push('constraints.physics.gravity must be [x, y, z]');
    }
  }

  if (c.player_params !== undefined) {
    if (c.player_params.health !== undefined && typeof c.player_params.health !== 'number') {
      errors.push('constraints.player_params.health must be a number');
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _isVec3(v) {
  return Array.isArray(v) && v.length === 3 && v.every(n => typeof n === 'number');
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { validate };

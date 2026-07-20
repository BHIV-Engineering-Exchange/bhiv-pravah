'use strict';

/**
 * RuleEngine.js
 *
 * Evaluates SumScript rules against simulation state.
 *
 * Rules are DATA — they declare what should happen, not how.
 * This module is the interpreter that reads those declarations.
 *
 * Design:
 *   - Rules are evaluated in order, all matching rules fire
 *   - Conditions are evaluated against entity fields or global state
 *   - Actions produce structured output — they do NOT mutate state directly
 *   - The SimEngine applies action outputs
 *
 * Condition operators: gt, lt, eq, gte, lte, neq, in, not_in
 * Action types: set_state, emit_event, flag_entity, block_entity, log
 */

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Evaluate all rules for a given trigger against current simulation state.
 *
 * @param {string}   trigger    - One of RULE_TRIGGERS
 * @param {Object[]} rules      - Normalized rules from SumScript contract
 * @param {Object}   simState   - { entities_map, tick, events[] }
 * @returns {Object[]} fired    - Array of { rule_id, entity_id, action, matched_at }
 */
function evaluate(trigger, rules, simState) {
  const fired = [];

  for (const rule of rules) {
    if (!rule.enabled)          continue;
    if (rule.trigger !== trigger) continue;

    // Scope: if condition.target is set, only evaluate for that entity
    const targets = rule.condition.target
      ? [simState.entities_map[rule.condition.target]].filter(Boolean)
      : Object.values(simState.entities_map);

    for (const entity of targets) {
      if (_evaluateCondition(rule.condition, entity, simState)) {
        fired.push({
          rule_id:    rule.id,
          entity_id:  entity.id,
          action:     rule.action,
          matched_at: simState.tick
        });
      }
    }
  }

  return fired;
}

/**
 * Apply a list of fired rule actions and return structured outputs.
 * Does NOT mutate anything — returns a list of action results.
 *
 * @param {Object[]} fired     - Output of evaluate()
 * @param {Object}   simState  - Current simulation state
 * @returns {Object[]} results - Array of action results
 */
function applyActions(fired, simState) {
  return fired.map(f => ACTION_HANDLERS[f.action.type]
    ? ACTION_HANDLERS[f.action.type](f, simState)
    : _unknownAction(f)
  );
}

// ─── Condition evaluator ──────────────────────────────────────────────────────

function _evaluateCondition(condition, entity, simState) {
  const value = _resolveField(condition.field, entity, simState);
  if (value === undefined) return false;

  return CONDITION_OPS[condition.op]
    ? CONDITION_OPS[condition.op](value, condition.value)
    : false;
}

// Resolve a dot-notation field path against entity or simState
// e.g. "velocity.0", "state", "meta.patrol_index", "tick"
function _resolveField(field, entity, simState) {
  if (field === 'tick') return simState.tick;

  const parts = field.split('.');
  let   obj   = entity;

  for (const part of parts) {
    if (obj === null || obj === undefined) return undefined;
    obj = obj[part];
  }

  return obj;
}

// ─── Condition operators ──────────────────────────────────────────────────────

const CONDITION_OPS = {
  gt:     (a, b) => Number(a) >  Number(b),
  lt:     (a, b) => Number(a) <  Number(b),
  gte:    (a, b) => Number(a) >= Number(b),
  lte:    (a, b) => Number(a) <= Number(b),
  eq:     (a, b) => String(a) === String(b),
  neq:    (a, b) => String(a) !== String(b),
  in:     (a, b) => Array.isArray(b) && b.map(String).includes(String(a)),
  not_in: (a, b) => Array.isArray(b) && !b.map(String).includes(String(a))
};

// ─── Action handlers ──────────────────────────────────────────────────────────
// Each handler returns a structured result — no mutation.

const ACTION_HANDLERS = {

  set_state(fired, _simState) {
    const new_state = fired.action.params.state;
    return {
      type:      'set_state',
      rule_id:   fired.rule_id,
      entity_id: fired.entity_id,
      payload:   { state: new_state },
      applied_at: fired.matched_at
    };
  },

  emit_event(fired, _simState) {
    return {
      type:      'emit_event',
      rule_id:   fired.rule_id,
      entity_id: fired.entity_id,
      payload:   {
        event_type: fired.action.params.event_type || 'rule_event',
        data:       fired.action.params.data       || {}
      },
      applied_at: fired.matched_at
    };
  },

  flag_entity(fired, _simState) {
    return {
      type:      'flag_entity',
      rule_id:   fired.rule_id,
      entity_id: fired.entity_id,
      payload:   {
        reason: fired.action.params.reason || `flagged by rule ${fired.rule_id}`
      },
      applied_at: fired.matched_at
    };
  },

  block_entity(fired, _simState) {
    return {
      type:      'block_entity',
      rule_id:   fired.rule_id,
      entity_id: fired.entity_id,
      payload:   {
        reason: fired.action.params.reason || `blocked by rule ${fired.rule_id}`
      },
      applied_at: fired.matched_at
    };
  },

  log(fired, _simState) {
    return {
      type:      'log',
      rule_id:   fired.rule_id,
      entity_id: fired.entity_id,
      payload:   {
        message: fired.action.params.message || `rule ${fired.rule_id} fired`
      },
      applied_at: fired.matched_at
    };
  }
};

function _unknownAction(fired) {
  return {
    type:      'unknown_action',
    rule_id:   fired.rule_id,
    entity_id: fired.entity_id,
    payload:   { action_type: fired.action.type },
    applied_at: fired.matched_at
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { evaluate, applyActions };

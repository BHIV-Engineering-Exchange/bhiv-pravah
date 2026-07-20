'use strict';

/**
 * contractConsequenceEngine.js
 *
 * Generic consequence engine — evaluates consequences[] declared
 * inside a contract. No static rules file. No hardcoded logic.
 *
 * Phase 5 requirement:
 *   Consequences come from contract configuration, not from code.
 *
 * Input:
 *   consequences[] — from contract
 *   event          — { event_type, entities[], context{} }
 *   state          — optional sim state for state_checks
 *
 * Output:
 *   { matched: rule_id[], actions: [{ rule_id, action, priority, payload }] }
 */

// ─── Public API ───────────────────────────────────────────────────────────────

function evaluate(consequences, event, state = null) {
  if (!Array.isArray(consequences) || consequences.length === 0) {
    return { matched: [], actions: [] };
  }

  const matched = [];
  const actions = [];

  for (const rule of consequences) {
    if (rule.on !== event.event_type) continue;
    if (!_checkCondition(rule.if || {}, event, state)) continue;

    matched.push(rule.rule_id);

    for (const a of (rule.then || [])) {
      actions.push({
        rule_id:     rule.rule_id,
        action:      a.action,
        priority:    a.priority || 'medium',
        payload:     a.payload  || {},
        description: rule.description || ''
      });
    }
  }

  // Sort critical first
  actions.sort((a, b) => _priorityValue(a.priority) - _priorityValue(b.priority));

  return { matched, actions };
}

// ─── Condition evaluator ──────────────────────────────────────────────────────

function _checkCondition(condition, event, state) {
  // entities check
  if (condition.entities && condition.entities.length > 0) {
    const eventEntities = event.entities || [];
    const allPresent = condition.entities.every(required =>
      eventEntities.some(id => id === required || id.startsWith(required))
    );
    if (!allPresent) return false;
  }

  // context_checks
  if (condition.context_checks) {
    for (const [key, expected] of Object.entries(condition.context_checks)) {
      const actual = event.context?.[key];
      if (typeof expected === 'object' && expected.operator) {
        if (!_op(actual, expected.operator, expected.value)) return false;
      } else {
        if (actual !== expected) return false;
      }
    }
  }

  // state_checks
  if (condition.state_checks && state) {
    for (const [path, expected] of Object.entries(condition.state_checks)) {
      const actual = path.split('.').reduce((o, k) => o?.[k], state);
      if (typeof expected === 'object' && expected.operator) {
        if (!_op(actual, expected.operator, expected.value)) return false;
      } else {
        if (actual !== expected) return false;
      }
    }
  }

  return true;
}

function _op(actual, operator, expected) {
  switch (operator) {
    case '>=': case 'gte': return Number(actual) >= Number(expected);
    case '<=': case 'lte': return Number(actual) <= Number(expected);
    case '>':  case 'gt':  return Number(actual) >  Number(expected);
    case '<':  case 'lt':  return Number(actual) <  Number(expected);
    case '==': case 'eq':  return String(actual) === String(expected);
    case '!=': case 'neq': return String(actual) !== String(expected);
    default:               return false;
  }
}

function _priorityValue(p) {
  return { critical: 1, high: 2, medium: 3, low: 4 }[p] ?? 3;
}

module.exports = { evaluate };

'use strict';

/**
 * index.js — SumScript Runtime Entry Point
 *
 * Public API for the SumScript runtime layer.
 *
 * Usage:
 *   const SumScript = require('./simulation/sumscript');
 *
 *   const result = SumScript.parse(rawContract);
 *   if (!result.valid) { ... handle errors ... }
 *
 *   // result.runtime is ready to pass to SimEngine
 *   simEngine.load(result.runtime);
 *
 * The runtime object exposes:
 *   contract   — normalized, validated SumScript contract
 *   execute    — run behaviors for one entity
 *   evaluate   — evaluate rules for a trigger
 *   applyAll   — apply all transforms to an entities map
 */

const schema              = require('./SumScriptSchema');
const { executeAll }      = require('./BehaviorExecutor');
const { evaluate,
        applyActions }    = require('./RuleEngine');
const { applyAll }        = require('./TransformApplicator');

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Parse and validate a raw SumScript contract.
 * Returns a runtime-ready object on success.
 *
 * @param {*} raw  - Raw input (from HTTP body, file, or adapter output)
 * @returns {{ valid, errors, runtime|null }}
 */
function parse(raw) {
  // 1. Validate shape
  const validation = schema.validate(raw);
  if (!validation.valid) {
    return { valid: false, errors: validation.errors, runtime: null };
  }

  // 2. Normalize (fill defaults, coerce types, strip unknowns)
  const contract = schema.normalize(raw);

  // 3. Build behavior lookup map: behavior_id → behavior object
  const behaviors_map = {};
  for (const b of contract.behaviors) {
    behaviors_map[b.id] = b;
  }

  // 4. Build runtime object
  const runtime = {
    contract,
    behaviors_map,

    /**
     * Run all behaviors for a single entity.
     * Returns a delta — does not mutate entity.
     *
     * @param {Object} entity   - Current entity state
     * @param {Object} context  - { tick, dt, entities_map, rng }
     * @returns {Object} delta
     */
    executeBehaviors(entity, context) {
      const entityBehaviors = entity.behaviors
        .map(id => behaviors_map[id])
        .filter(Boolean);

      return executeAll(entity, entityBehaviors, context);
    },

    /**
     * Evaluate rules for a given trigger.
     * Returns fired rule actions — does not mutate state.
     *
     * @param {string} trigger   - e.g. 'on_tick', 'on_collision'
     * @param {Object} simState  - { entities_map, tick, events }
     * @returns {Object[]} action results
     */
    evaluateRules(trigger, simState) {
      const fired = evaluate(trigger, contract.rules, simState);
      return applyActions(fired, simState);
    },

    /**
     * Apply all contract-level transforms to an entities map.
     * Called once at simulation init.
     *
     * @param {Object} entities_map  - { [entity_id]: entity }
     * @returns {{ entities_map, events }}
     */
    applyTransforms(entities_map) {
      return applyAll(contract.transforms, entities_map);
    },

    /**
     * Build the initial entities map from the contract.
     * Keyed by entity.id for O(1) lookup.
     *
     * @returns {Object} entities_map
     */
    buildEntitiesMap() {
      const map = {};
      for (const e of contract.entities) {
        map[e.id] = { ...e };
      }
      return map;
    }
  };

  return { valid: true, errors: [], runtime };
}

/**
 * Quick validation only — no normalization, no runtime object.
 * Use when you only need to check if a contract is valid.
 *
 * @param {*} raw
 * @returns {{ valid, errors }}
 */
function validate(raw) {
  return schema.validate(raw);
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  parse,
  validate,
  // Re-export constants for consumers
  ENTITY_TYPES:     schema.ENTITY_TYPES,
  ENTITY_STATES:    schema.ENTITY_STATES,
  TRANSFORM_OPS:    schema.TRANSFORM_OPS,
  RULE_TRIGGERS:    schema.RULE_TRIGGERS,
  RULE_ACTIONS:     schema.RULE_ACTIONS,
  BEHAVIOR_SCRIPTS: schema.BEHAVIOR_SCRIPTS
};

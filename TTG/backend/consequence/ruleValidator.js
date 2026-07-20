/**
 * Consequence Rule Validator
 * Validates consequence rules against schema and business logic
 */

const fs = require('fs');
const path = require('path');

/**
 * Load consequence rules from JSON file
 * @returns {Object} Consequence rules object
 */
function loadConsequenceRules() {
  const rulesPath = path.join(__dirname, 'consequenceRules.json');
  const rulesData = fs.readFileSync(rulesPath, 'utf8');
  return JSON.parse(rulesData);
}

/**
 * Validate a single consequence rule
 * @param {Object} rule - Rule to validate
 * @returns {Object} { valid: boolean, errors: string[] }
 */
function validateRule(rule) {
  const errors = [];

  // Required fields
  if (!rule.rule_id) {
    errors.push('Missing required field: rule_id');
  }

  if (!rule.on) {
    errors.push('Missing required field: on (event type)');
  }

  if (!rule.if) {
    errors.push('Missing required field: if (condition)');
  } else {
    if (!rule.if.condition) {
      errors.push('Missing required field: if.condition');
    }
  }

  if (!rule.then || !Array.isArray(rule.then)) {
    errors.push('Missing or invalid field: then (must be array)');
  } else {
    // Validate each action
    rule.then.forEach((action, index) => {
      if (!action.action) {
        errors.push(`Action ${index}: missing action name`);
      }
      if (!action.priority) {
        errors.push(`Action ${index}: missing priority`);
      } else if (!['critical', 'high', 'medium', 'low'].includes(action.priority)) {
        errors.push(`Action ${index}: invalid priority '${action.priority}'`);
      }
      if (action.payload === undefined) {
        errors.push(`Action ${index}: missing payload`);
      }
    });
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate all consequence rules
 * @param {Object} rulesData - Rules data object
 * @returns {Object} { valid: boolean, errors: Object }
 */
function validateAllRules(rulesData) {
  const errors = {};
  let allValid = true;

  if (!rulesData.rules || !Array.isArray(rulesData.rules)) {
    return {
      valid: false,
      errors: { global: ['Rules data must contain a rules array'] }
    };
  }

  rulesData.rules.forEach((rule) => {
    const validation = validateRule(rule);
    if (!validation.valid) {
      errors[rule.rule_id || 'unknown'] = validation.errors;
      allValid = false;
    }
  });

  return {
    valid: allValid,
    errors
  };
}

/**
 * Check for duplicate rule IDs
 * @param {Object} rulesData - Rules data object
 * @returns {Object} { valid: boolean, duplicates: string[] }
 */
function checkDuplicateRuleIds(rulesData) {
  const ruleIds = new Set();
  const duplicates = [];

  rulesData.rules.forEach((rule) => {
    if (ruleIds.has(rule.rule_id)) {
      duplicates.push(rule.rule_id);
    } else {
      ruleIds.add(rule.rule_id);
    }
  });

  return {
    valid: duplicates.length === 0,
    duplicates
  };
}

/**
 * Get rules for a specific event type
 * @param {Object} rulesData - Rules data object
 * @param {string} eventType - Event type to filter by
 * @returns {Array} Array of matching rules
 */
function getRulesForEvent(rulesData, eventType) {
  return rulesData.rules.filter(rule => rule.on === eventType);
}

/**
 * Get rule by ID
 * @param {Object} rulesData - Rules data object
 * @param {string} ruleId - Rule ID to find
 * @returns {Object|null} Rule object or null if not found
 */
function getRuleById(rulesData, ruleId) {
  return rulesData.rules.find(rule => rule.rule_id === ruleId) || null;
}

/**
 * Get all action definitions
 * @param {Object} rulesData - Rules data object
 * @returns {Object} Action definitions
 */
function getActionDefinitions(rulesData) {
  return rulesData.action_definitions || {};
}

/**
 * Validate action against definition
 * @param {Object} action - Action to validate
 * @param {Object} actionDef - Action definition
 * @returns {Object} { valid: boolean, errors: string[] }
 */
function validateActionPayload(action, actionDef) {
  const errors = [];

  if (!actionDef) {
    errors.push(`Unknown action: ${action.action}`);
    return { valid: false, errors };
  }

  // Check required payload fields
  if (actionDef.required_payload) {
    actionDef.required_payload.forEach((field) => {
      if (!(field in action.payload)) {
        errors.push(`Missing required payload field: ${field}`);
      }
    });
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Get priority value for sorting
 * @param {string} priority - Priority level
 * @returns {number} Priority value (lower = higher priority)
 */
function getPriorityValue(priority) {
  const priorities = {
    critical: 1,
    high: 2,
    medium: 3,
    low: 4
  };
  return priorities[priority] || 999;
}

/**
 * Sort actions by priority
 * @param {Array} actions - Array of actions
 * @returns {Array} Sorted actions (highest priority first)
 */
function sortActionsByPriority(actions) {
  return [...actions].sort((a, b) => {
    return getPriorityValue(a.priority) - getPriorityValue(b.priority);
  });
}

/**
 * Get statistics about rules
 * @param {Object} rulesData - Rules data object
 * @returns {Object} Statistics
 */
function getRuleStatistics(rulesData) {
  const stats = {
    total_rules: rulesData.rules.length,
    rules_by_event: {},
    rules_by_priority: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    },
    total_actions: 0,
    unique_actions: new Set()
  };

  rulesData.rules.forEach((rule) => {
    // Count by event type
    if (!stats.rules_by_event[rule.on]) {
      stats.rules_by_event[rule.on] = 0;
    }
    stats.rules_by_event[rule.on]++;

    // Count actions
    rule.then.forEach((action) => {
      stats.total_actions++;
      stats.unique_actions.add(action.action);
      
      // Count by priority
      if (stats.rules_by_priority[action.priority] !== undefined) {
        stats.rules_by_priority[action.priority]++;
      }
    });
  });

  stats.unique_actions = Array.from(stats.unique_actions);

  return stats;
}

module.exports = {
  loadConsequenceRules,
  validateRule,
  validateAllRules,
  checkDuplicateRuleIds,
  getRulesForEvent,
  getRuleById,
  getActionDefinitions,
  validateActionPayload,
  getPriorityValue,
  sortActionsByPriority,
  getRuleStatistics
};

/**
 * Gameplay Rules Loader
 * Utility to load and apply game-mode-specific consequence rules
 */

const fs = require('fs');
const path = require('path');

/**
 * Load gameplay rules from JSON file
 * @returns {Object} Gameplay rules object
 */
function loadGameplayRules() {
  const rulesPath = path.join(__dirname, 'gameplayRules.json');
  const rulesData = fs.readFileSync(rulesPath, 'utf8');
  return JSON.parse(rulesData);
}

/**
 * Get rules for a specific game mode
 * @param {string} gameMode - Game mode (runner, arena, platformer, etc.)
 * @returns {Array} Array of rules for the game mode
 */
function getRulesForGameMode(gameMode) {
  const gameplayRules = loadGameplayRules();
  
  const mode = gameplayRules.game_modes[gameMode];
  if (!mode) {
    console.warn(`[GAMEPLAY RULES] Unknown game mode: ${gameMode}`);
    return [];
  }

  return mode.rules || [];
}

/**
 * Get all available game modes
 * @returns {Array} Array of game mode names
 */
function getAvailableGameModes() {
  const gameplayRules = loadGameplayRules();
  return Object.keys(gameplayRules.game_modes);
}

/**
 * Get game mode information
 * @param {string} gameMode - Game mode name
 * @returns {Object} Game mode info
 */
function getGameModeInfo(gameMode) {
  const gameplayRules = loadGameplayRules();
  const mode = gameplayRules.game_modes[gameMode];
  
  if (!mode) {
    return null;
  }

  return {
    name: mode.name,
    description: mode.description,
    rule_count: mode.rules.length
  };
}

/**
 * Merge game mode rules with base consequence rules
 * @param {string} gameMode - Game mode
 * @param {Object} baseRules - Base consequence rules
 * @returns {Object} Merged rules
 */
function mergeGameModeRules(gameMode, baseRules) {
  const gameModeRules = getRulesForGameMode(gameMode);
  const gameplayRules = loadGameplayRules();
  const commonRules = gameplayRules.common_rules?.rules || [];

  // Combine all rules
  const allRules = [
    ...baseRules.rules,
    ...gameModeRules,
    ...commonRules
  ];

  // Remove duplicates by rule_id
  const uniqueRules = [];
  const seenIds = new Set();

  allRules.forEach(rule => {
    if (!seenIds.has(rule.rule_id)) {
      seenIds.add(rule.rule_id);
      uniqueRules.push(rule);
    }
  });

  return {
    ...baseRules,
    rules: uniqueRules
  };
}

/**
 * Get rules by event type for a specific game mode
 * @param {string} gameMode - Game mode
 * @param {string} eventType - Event type
 * @returns {Array} Matching rules
 */
function getRulesByEventType(gameMode, eventType) {
  const rules = getRulesForGameMode(gameMode);
  return rules.filter(rule => rule.on === eventType);
}

/**
 * Get statistics about gameplay rules
 * @returns {Object} Statistics
 */
function getGameplayRulesStatistics() {
  const gameplayRules = loadGameplayRules();
  
  const stats = {
    total_game_modes: Object.keys(gameplayRules.game_modes).length,
    total_rules: 0,
    rules_by_mode: {},
    common_rules: gameplayRules.common_rules?.rules.length || 0
  };

  Object.entries(gameplayRules.game_modes).forEach(([mode, data]) => {
    const ruleCount = data.rules.length;
    stats.rules_by_mode[mode] = ruleCount;
    stats.total_rules += ruleCount;
  });

  stats.total_rules += stats.common_rules;

  return stats;
}

/**
 * Validate game mode rules
 * @param {string} gameMode - Game mode to validate
 * @returns {Object} Validation result
 */
function validateGameModeRules(gameMode) {
  const rules = getRulesForGameMode(gameMode);
  const errors = [];

  rules.forEach((rule, index) => {
    if (!rule.rule_id) {
      errors.push(`Rule ${index}: Missing rule_id`);
    }
    if (!rule.on) {
      errors.push(`Rule ${index}: Missing event type (on)`);
    }
    if (!rule.if) {
      errors.push(`Rule ${index}: Missing condition (if)`);
    }
    if (!rule.then || !Array.isArray(rule.then)) {
      errors.push(`Rule ${index}: Missing or invalid actions (then)`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
    rule_count: rules.length
  };
}

/**
 * Get example rules for demonstration
 * @param {string} gameMode - Game mode
 * @param {number} count - Number of examples to return
 * @returns {Array} Example rules
 */
function getExampleRules(gameMode, count = 3) {
  const rules = getRulesForGameMode(gameMode);
  return rules.slice(0, count);
}

module.exports = {
  loadGameplayRules,
  getRulesForGameMode,
  getAvailableGameModes,
  getGameModeInfo,
  mergeGameModeRules,
  getRulesByEventType,
  getGameplayRulesStatistics,
  validateGameModeRules,
  getExampleRules
};

/**
 * Game Mode Mapper - Text to Game Mode Converter
 * Deterministic mapper: User text → { game_mode, params }
 * No LLM creativity - only classification and parameter fill
 */

const {
  analyzeTheme,
  detectSpeed,
  detectDifficulty,
  detectObstacles,
  generateWorldName
} = require('./text_to_json');

/**
 * Map theme to game mode
 * Deterministic classification
 */
function mapThemeToGameMode(theme) {
  const gameModeMap = {
    'runner': 'runner',
    'endless': 'runner',
    'chase': 'runner',
    'side_scroller': 'side_scroller',
    'platform': 'side_scroller',
    'platformer': 'side_scroller',
    'mario': 'side_scroller',
    // Default mappings
    'alien': 'runner',
    'horror': 'side_scroller',
    'medieval': 'side_scroller',
    'fantasy': 'side_scroller'
  };

  return gameModeMap[theme] || 'runner'; // default to runner
}

/**
 * Extract spawn rules from text
 */
function extractSpawnRules(promptLower, difficulty) {
  const baseInterval = 2.0;
  const baseDistance = 10.0;

  // Adjust based on difficulty
  const difficultyMultipliers = {
    'easy': { interval: 1.5, distance: 1.2 },
    'medium': { interval: 1.0, distance: 1.0 },
    'hard': { interval: 0.7, distance: 0.8 }
  };

  const multiplier = difficultyMultipliers[difficulty] || difficultyMultipliers['medium'];

  return {
    interval: baseInterval * multiplier.interval,
    distance: baseDistance * multiplier.distance
  };
}

/**
 * Extract scoring rules from text
 */
function extractScoring(promptLower, difficulty) {
  const basePoints = 10;
  const baseBonus = 50;

  // Adjust based on difficulty
  const difficultyMultipliers = {
    'easy': { points: 0.8, bonus: 0.8 },
    'medium': { points: 1.0, bonus: 1.0 },
    'hard': { points: 1.5, bonus: 2.0 }
  };

  const multiplier = difficultyMultipliers[difficulty] || difficultyMultipliers['medium'];

  return {
    points_per_second: Math.round(basePoints * multiplier.points),
    obstacle_bonus: Math.round(baseBonus * multiplier.bonus)
  };
}

/**
 * Extract end condition from text
 */
function extractEndCondition(promptLower, difficulty) {
  // Check for explicit conditions
  if (promptLower.includes('distance') || promptLower.includes('reach')) {
    return { type: 'distance', value: 1000 };
  }
  if (promptLower.includes('time') || promptLower.includes('survive')) {
    return { type: 'time', value: 60 };
  }
  if (promptLower.includes('score') || promptLower.includes('points')) {
    return { type: 'score', value: 5000 };
  }

  // Default: lives based on difficulty
  const lives = {
    'easy': 5,
    'medium': 3,
    'hard': 1
  };

  return {
    type: 'lives',
    value: lives[difficulty] || 3
  };
}

/**
 * Main mapper function: Text → Game Mode Schema
 * Deterministic, no LLM required
 */
function mapTextToGameMode(userText) {
  const promptLower = userText.toLowerCase();
  const words = promptLower.split(/\s+/);

  // Step 1: Analyze theme
  const themeAnalysis = analyzeTheme(promptLower, words);
  
  // Step 2: Map to game mode
  const gameMode = mapThemeToGameMode(themeAnalysis.type);
  
  // Step 3: Extract parameters
  const movementSpeed = detectSpeed(promptLower);
  const difficulty = detectDifficulty(promptLower);
  const obstacles = detectObstacles(promptLower, themeAnalysis.type);
  
  // Step 4: Build complete game mode object
  const gameModeData = {
    game_mode: gameMode,
    params: {
      movement_speed: movementSpeed,
      gravity: [0, -9.8, 0], // Standard gravity
      difficulty: difficulty,
      obstacles: obstacles,
      spawn_rules: extractSpawnRules(promptLower, difficulty),
      scoring: extractScoring(promptLower, difficulty),
      end_condition: extractEndCondition(promptLower, difficulty)
    }
  };

  console.log(`✅ Mapped text to game mode: ${gameMode} (${difficulty})`);
  return gameModeData;
}

/**
 * Validate game mode data against schema
 */
function validateGameMode(gameModeData) {
  const errors = [];

  // Required fields
  if (!gameModeData.game_mode) {
    errors.push('Missing required field: game_mode');
  }
  if (!gameModeData.params) {
    errors.push('Missing required field: params');
  }

  // Game mode validation
  if (!['runner', 'side_scroller'].includes(gameModeData.game_mode)) {
    errors.push(`Invalid game_mode: ${gameModeData.game_mode}. Must be 'runner' or 'side_scroller'`);
  }

  // Parameter validation
  if (gameModeData.params) {
    const { movement_speed, gravity, difficulty } = gameModeData.params;

    if (typeof movement_speed !== 'number' || movement_speed < 1.0 || movement_speed > 15.0) {
      errors.push('movement_speed must be a number between 1.0 and 15.0');
    }

    if (!Array.isArray(gravity) || gravity.length !== 3) {
      errors.push('gravity must be an array of 3 numbers');
    }

    if (!['easy', 'medium', 'hard'].includes(difficulty)) {
      errors.push(`Invalid difficulty: ${difficulty}. Must be 'easy', 'medium', or 'hard'`);
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors
  };
}

module.exports = {
  mapTextToGameMode,
  mapThemeToGameMode,
  extractSpawnRules,
  extractScoring,
  extractEndCondition,
  validateGameMode
};

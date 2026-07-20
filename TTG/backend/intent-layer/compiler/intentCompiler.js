const fs = require('fs');
const path = require('path');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'compiler.config.json'), 'utf8'));

const match = (text, keywords) => keywords.some(kw => text.includes(kw));

const findFirst = (text, keywordMap) => {
  for (const [key, keywords] of Object.entries(keywordMap)) {
    if (match(text, keywords)) return key;
  }
  return null;
};

function compile(userInput) {
  if (!userInput || typeof userInput !== 'string' || !userInput.trim()) {
    throw new Error('Invalid input: empty or non-string');
  }

  const text = userInput.toLowerCase().trim();

  if (text.length < config.validation.min_input_length) {
    throw new Error(`Input too short: minimum ${config.validation.min_input_length} characters`);
  }

  if (config.validation.unsupported_genres.some(g => text.includes(g))) {
    throw new Error('Unsupported game genre detected');
  }

  if (config.validation.unsupported_features.some(f => text.includes(f))) {
    throw new Error('Unsupported game features detected');
  }

  const gameMode = findFirst(text, config.keywords.game_modes) || config.defaults.game_mode;
  const difficulty = findFirst(text, config.keywords.difficulty) || 'medium';
  const speedType = findFirst(text, config.keywords.speed);
  const speed = speedType ? config.mappings.speed_values[speedType] : config.defaults.speed;

  const abilities = Object.keys(config.keywords.abilities).filter(a => match(text, config.keywords.abilities[a]));
  const hasJump = abilities.includes('jump');
  const hasJetpack = abilities.includes('jetpack');

  const movement = { speed };
  if (hasJump) movement.jump_height = config.defaults.jump_height;

  const camera = {
    type: config.mappings.camera[gameMode],
    distance: config.defaults.camera_distance
  };

  const hasObstacles = match(text, config.keywords.obstacles);
  const spawnRules = {
    obstacles: hasObstacles ? 2 : config.defaults.obstacles,
    frequency: config.mappings.difficulty_spawn_rate[difficulty]
  };

  const hasCollectibles = match(text, config.keywords.scoring.collectibles);
  const hasScore = match(text, config.keywords.scoring.score);
  const scoreRules = {
    distance: (hasCollectibles && !hasScore) ? 0 : config.mappings.scoring_values.distance,
    collectibles: hasCollectibles ? config.mappings.scoring_values.collectibles : 0
  };

  const endConditions = ['collision'];
  if (match(text, config.keywords.end_conditions.time_limit)) endConditions.push('time_limit');
  if (match(text, config.keywords.end_conditions.distance_goal)) endConditions.push('distance_goal');

  const playerParams = {
    jetpack: hasJetpack,
    health: config.mappings.difficulty_health[difficulty]
  };

  const worldParams = { theme: config.defaults.theme };

  const physics = {
    gravity: findFirst(text, config.keywords.physics) === 'low_gravity' ? config.mappings.physics_values.low_gravity :
             findFirst(text, config.keywords.physics) === 'high_gravity' ? config.mappings.physics_values.high_gravity :
             config.defaults.gravity,
    friction: findFirst(text, config.keywords.physics) === 'slippery' ? config.mappings.physics_values.slippery :
              findFirst(text, config.keywords.physics) === 'sticky' ? config.mappings.physics_values.sticky :
              config.defaults.friction,
    bounce: findFirst(text, config.keywords.physics) === 'bouncy' ? config.mappings.physics_values.bouncy :
            findFirst(text, config.keywords.physics) === 'solid' ? config.mappings.physics_values.solid :
            config.defaults.bounce,
    air_resistance: config.defaults.air_resistance,
    collision_force: config.defaults.collision_force
  };

  return { game_mode: gameMode, movement, camera, spawn_rules: spawnRules, score_rules: scoreRules, end_conditions: endConditions, player_params: playerParams, world_params: worldParams, physics };
}

module.exports = { compile };

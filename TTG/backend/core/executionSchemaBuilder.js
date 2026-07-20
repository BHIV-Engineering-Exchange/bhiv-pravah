const { selectTemplate } = require('../game-templates/templateSelector');
const { injectParameters, extractParameters } = require('../game-templates/parameterInjector');

function buildExecutionSchema(intent) {
  // Step 1: Select template based on intent
  const template = selectTemplate(intent);
  
  // Step 2: Extract parameters from intent
  const intentParams = extractParameters(intent);
  
  // Step 3: Inject parameters into template
  const config = injectParameters(template, intentParams);
  
  // Step 4: Transform to execution schema format
  const executionSchema = transformToSchema(config, template.template_id);
  
  return {
    template,
    config,
    executionSchema
  };
}

function transformToSchema(config, templateId) {
  const params = config.parameters;
  const gameMode = templateId.split('_')[0]; // runner_v1 -> runner
  
  const schema = {
    game_mode: mapGameMode(gameMode),
    movement: {
      speed: params.movement_speed || 5,
      jump_height: params.jump_height || 5
    },
    camera: {
      type: getCameraType(gameMode),
      distance: 10
    },
    spawn_rules: {
      obstacles: params.obstacle_count || params.enemy_count || 2,
      frequency: params.spawn_frequency || 2
    },
    score_rules: {
      distance: 1,
      collectibles: 10
    },
    end_conditions: getEndConditions(gameMode),
    player_params: {
      health: params.player_health || 3
    },
    world_params: {
      theme: "default"
    },
    physics: {
      gravity: params.gravity || -9.8,
      friction: 0.5,
      bounce: 0.3,
      air_resistance: 0.1,
      collision_force: 1.0
    }
  };
  
  return schema;
}

function mapGameMode(templateMode) {
  const modeMap = {
    runner: 'runner',
    platformer: 'sidescroller',
    arena: 'open_scene'
  };
  return modeMap[templateMode] || 'runner';
}

function getCameraType(gameMode) {
  const cameraMap = {
    runner: 'third_person',
    platformer: 'side_view',
    arena: 'top_down'
  };
  return cameraMap[gameMode] || 'third_person';
}

function getEndConditions(gameMode) {
  const conditionsMap = {
    runner: ['collision', 'distance_goal'],
    platformer: ['collision', 'distance_goal'],
    arena: ['time_limit', 'score_goal']
  };
  return conditionsMap[gameMode] || ['collision'];
}

module.exports = { buildExecutionSchema };

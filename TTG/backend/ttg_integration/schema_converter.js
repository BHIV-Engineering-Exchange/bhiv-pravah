/**
 * Schema Converter - Game Mode to Engine Schema
 * Converts game mode data to Engine Schema v1.0 format
 */

/**
 * Convert game mode data to Engine Schema v1.0
 */
function convertToEngineSchema(gameModeData) {
  const worldId = `world_${Date.now()}`;
  const sceneId = `scene_${gameModeData.game_mode}`;

  return {
    schema_version: "1.0",
    
    world: {
      id: worldId,
      name: gameModeData.game_mode === 'runner' ? 'Endless Runner' : 'Platform Adventure',
      gravity: gameModeData.params.gravity
    },

    scene: {
      id: sceneId,
      ambientLight: [0.6, 0.6, 0.6],
      skybox: "default_sky"
    },

    entities: generateEntities(gameModeData),
    
    quests: [],
    
    jobs: []
  };
}

/**
 * Generate entities based on game mode
 */
function generateEntities(gameModeData) {
  const entities = [];

  // Add player entity
  entities.push(createPlayerEntity(gameModeData));

  // Add obstacles based on game mode
  const obstacleCount = gameModeData.params.difficulty === 'hard' ? 5 : 3;
  for (let i = 0; i < obstacleCount; i++) {
    entities.push(createObstacleEntity(gameModeData, i));
  }

  return entities;
}

/**
 * Create player entity
 */
function createPlayerEntity(gameModeData) {
  return {
    id: "player_1",
    type: "player",
    
    transform: {
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      scale: [1, 1, 1]
    },

    material: {
      shader: "standard",
      texture: "player_skin",
      color: [1, 1, 1]
    },

    components: {
      mesh: "player",
      collider: "box",
      script: gameModeData.game_mode === 'runner' ? "runner_controller" : "platformer_controller"
    }
  };
}

/**
 * Create obstacle entity
 */
function createObstacleEntity(gameModeData, index) {
  const obstacleType = gameModeData.params.obstacles[index % gameModeData.params.obstacles.length] || 'rock';
  const distance = gameModeData.params.spawn_rules?.distance || 10.0;

  return {
    id: `obstacle_${index + 1}`,
    type: "object",
    
    transform: {
      position: [(index + 1) * distance, 0, 0],
      rotation: [0, 0, 0],
      scale: [1, 2, 1]
    },

    material: {
      shader: "standard",
      texture: obstacleType,
      color: [0.5, 0.5, 0.5]
    },

    components: {
      mesh: "cube",
      collider: "box",
      script: ""
    }
  };
}

module.exports = {
  convertToEngineSchema,
  generateEntities,
  createPlayerEntity,
  createObstacleEntity
};

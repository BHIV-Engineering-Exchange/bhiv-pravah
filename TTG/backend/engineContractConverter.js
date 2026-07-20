// engineContractConverter.js - Convert execution schema to engine contract
function convertToEngineContract(executionSchema, execution_id, trace_id) {
  return {
    execution_id,
    trace_id,
    game_mode: executionSchema.game_mode,
    
    scene: {
      scene_id: `scene_${executionSchema.game_mode}`,
      ambient_light: [0.6, 0.6, 0.6],
      skybox: 'default_sky'
    },
    
    entities: [
      {
        id: 'player_1',
        type: 'player',
        transform: {
          position: [0, 0, 0],
          rotation: [0, 0, 0],
          scale: [1, 1, 1]
        },
        material: {
          shader: 'standard',
          texture: 'player_skin',
          color: [1, 1, 1]
        },
        components: {
          mesh: 'player',
          collider: 'box',
          script: 'runner_controller'
        }
      }
    ],
    
    physics: {
      gravity: [0, executionSchema.physics?.gravity || -9.8, 0],
      friction: executionSchema.physics?.friction || 0.5,
      bounce: executionSchema.physics?.bounce || 0.3,
      air_resistance: executionSchema.physics?.air_resistance || 0.1,
      collision_force: executionSchema.physics?.collision_force || 1.0
    },
    
    movement: {
      speed: executionSchema.movement?.speed || 5,
      jump_height: executionSchema.movement?.jump_height || 5
    },
    
    camera: {
      type: executionSchema.camera?.type || 'third_person',
      distance: executionSchema.camera?.distance || 10
    },
    
    spawn_rules: {
      obstacles: executionSchema.spawn_rules?.obstacles || 2,
      frequency: executionSchema.spawn_rules?.frequency || 2,
      distance: 10
    },
    
    scoring: {
      rules: {
        distance: executionSchema.score_rules?.distance || 1,
        collectibles: executionSchema.score_rules?.collectibles || 0,
        time: 0
      },
      end_conditions: executionSchema.end_conditions || ['collision']
    },
    
    player_params: {
      health: executionSchema.player_params?.health || 3,
      jetpack: executionSchema.player_params?.jetpack || false
    }
  };
}

module.exports = { convertToEngineContract };

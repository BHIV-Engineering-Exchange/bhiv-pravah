function injectParameters(template, intentParams) {
  const config = {
    template_id: template.template_id,
    entities: template.entities,
    components: template.components,
    jobs: template.jobs,
    parameters: { ...template.defaults }
  };

  // Override defaults with intent parameters
  if (intentParams) {
    Object.keys(intentParams).forEach(key => {
      if (intentParams[key] !== undefined && intentParams[key] !== null) {
        config.parameters[key] = intentParams[key];
      }
    });
  }

  return config;
}

function extractParameters(intent) {
  const params = {};
  const intentLower = intent.toLowerCase();

  // Speed modifiers
  if (intentLower.includes('fast') || intentLower.includes('quick')) {
    params.movement_speed = 8;
  } else if (intentLower.includes('slow')) {
    params.movement_speed = 3;
  }

  // Difficulty modifiers
  if (intentLower.includes('easy')) {
    params.spawn_frequency = 5;
    params.jump_height = 6;
    params.enemy_count = 3;
  } else if (intentLower.includes('hard') || intentLower.includes('difficult')) {
    params.spawn_frequency = 1.5;
    params.jump_height = 4;
    params.enemy_count = 10;
  }

  // Size modifiers
  if (intentLower.includes('large') || intentLower.includes('big')) {
    params.arena_size = 30;
    params.platform_count = 15;
  } else if (intentLower.includes('small')) {
    params.arena_size = 10;
    params.platform_count = 5;
  }

  return params;
}

module.exports = { injectParameters, extractParameters };

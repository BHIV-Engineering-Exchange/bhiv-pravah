function validate(schema) {
  const errors = [];
  const warnings = [];

  // -------------------------
  // Required fields
  // -------------------------
  if (!schema.meta?.game_title) errors.push('Missing meta.game_title');
  if (!schema.meta?.version) errors.push('Missing meta.version');

  if (!schema.gameplay?.game_mode) errors.push('Missing gameplay.game_mode');
  if (!schema.gameplay?.movement_axis) errors.push('Missing gameplay.movement_axis');
  if (schema.gameplay?.global_speed === undefined)
    errors.push('Missing gameplay.global_speed');

  if (!schema.camera?.mode) errors.push('Missing camera.mode');
  if (!schema.camera?.offset) errors.push('Missing camera.offset');
  if (!schema.camera?.look_at) errors.push('Missing camera.look_at');

  if (!schema.player?.start_pos) errors.push('Missing player.start_pos');
  if (!schema.player?.abilities) errors.push('Missing player.abilities');

  if (!Array.isArray(schema.entities))
    errors.push('Missing entities array');

  // -------------------------
  // Array structure validation
  // -------------------------
  if (!Array.isArray(schema.camera?.offset) || schema.camera.offset.length !== 3) {
    errors.push('camera.offset must be an array of 3 numbers');
  }

  if (!Array.isArray(schema.camera?.look_at) || schema.camera.look_at.length !== 3) {
    errors.push('camera.look_at must be an array of 3 numbers');
  }

  if (!Array.isArray(schema.player?.start_pos) || schema.player.start_pos.length !== 3) {
    errors.push('player.start_pos must be an array of 3 values');
  }

  // -------------------------
  // Number type validation
  // -------------------------
  if (typeof schema.gameplay?.global_speed !== 'number') {
    errors.push('gameplay.global_speed must be a number');
  }

  if (schema.gameplay?.gravity !== undefined &&
      typeof schema.gameplay.gravity !== 'number') {
    errors.push('gameplay.gravity must be a number');
  }

  // -------------------------
  // Enum validation
  // -------------------------
  const validGameModes = ['infinite_runner', 'side_scroller', 'arena_loop'];
  if (schema.gameplay?.game_mode &&
      !validGameModes.includes(schema.gameplay.game_mode)) {
    errors.push(`Invalid game_mode: ${schema.gameplay.game_mode}`);
  }

  const validAxes = ['x', 'z', 'free'];
  if (schema.gameplay?.movement_axis &&
      !validAxes.includes(schema.gameplay.movement_axis)) {
    errors.push(`Invalid movement_axis: ${schema.gameplay.movement_axis}`);
  }

  const validScoreMetrics = ['distance', 'time', 'collection'];
  if (schema.gameplay?.score_metric &&
      !validScoreMetrics.includes(schema.gameplay.score_metric)) {
    errors.push(`Invalid score_metric: ${schema.gameplay.score_metric}`);
  }

  const validCameraModes = ['follow_third_person', 'fixed_ortho', 'top_down'];
  if (schema.camera?.mode &&
      !validCameraModes.includes(schema.camera.mode)) {
    errors.push(`Invalid camera.mode: ${schema.camera.mode}`);
  }

  // -------------------------
  // Entity validation
  // -------------------------
  const validEntityTypes = ['obstacle', 'pickup', 'decoration'];
  const validCollisionEffects = ['game_over', 'score_add', 'none'];
  const validLaneDistributions = ['random', 'all', 'center'];

  schema.entities?.forEach((entity, idx) => {
    if (!entity.id) errors.push(`Entity ${idx}: missing id`);
    if (!entity.type) errors.push(`Entity ${idx}: missing type`);

    if (entity.type && !validEntityTypes.includes(entity.type)) {
      errors.push(`Entity ${idx}: invalid type ${entity.type}`);
    }

    if (!entity.spawn_rule) {
      errors.push(`Entity ${idx}: missing spawn_rule`);
    } else {
      if (typeof entity.spawn_rule.spawn_rate !== 'number') {
        errors.push(`Entity ${idx}: spawn_rate must be a number`);
      }

      if (entity.spawn_rule.y_offset !== undefined &&
          typeof entity.spawn_rule.y_offset !== 'number') {
        errors.push(`Entity ${idx}: y_offset must be a number`);
      }

      if (entity.spawn_rule.lane_distribution &&
          !validLaneDistributions.includes(entity.spawn_rule.lane_distribution)) {
        errors.push(
          `Entity ${idx}: invalid lane_distribution ${entity.spawn_rule.lane_distribution}`
        );
      }
    }

    if (entity.collision_effect &&
        !validCollisionEffects.includes(entity.collision_effect)) {
      errors.push(
        `Entity ${idx}: invalid collision_effect ${entity.collision_effect}`
      );
    }
  });

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Explain validation errors to user
 */
function explainErrors(validationResult, intent) {
  if (validationResult.valid) {
    return '✅ Schema is valid';
  }

  let explanation = '❌ Cannot compile your request:\n';
  validationResult.errors.forEach(err => {
    explanation += `  - ${err}\n`;
  });

  if (intent?.genre &&
      !['runner', 'platformer', 'arena'].includes(intent.genre)) {
    explanation += '\n💡 Supported genres: runner, platformer, arena';
  }

  return explanation;
}

module.exports = { validate, explainErrors };

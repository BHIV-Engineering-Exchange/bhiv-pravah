const fs = require('fs');
const path = require('path');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, '../compiler/compiler.config.json'), 'utf8'));

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function guard(schema) {
  const safe = JSON.parse(JSON.stringify(schema));
  const limits = config.limits;

  if (safe.movement) {
    if (safe.movement.speed !== undefined) {
      safe.movement.speed = clamp(safe.movement.speed, limits.speed.min, limits.speed.max);
    }
    if (safe.movement.jump_height !== undefined) {
      safe.movement.jump_height = clamp(safe.movement.jump_height, limits.jump_height.min, limits.jump_height.max);
    }
  }

  if (safe.spawn_rules) {
    if (safe.spawn_rules.obstacles !== undefined) {
      safe.spawn_rules.obstacles = clamp(safe.spawn_rules.obstacles, limits.obstacles.min, limits.obstacles.max);
    }
    if (safe.spawn_rules.frequency !== undefined) {
      safe.spawn_rules.frequency = clamp(safe.spawn_rules.frequency, limits.frequency.min, limits.frequency.max);
    }
  }

  if (safe.player_params) {
    if (safe.player_params.health !== undefined) {
      safe.player_params.health = clamp(safe.player_params.health, limits.health.min, limits.health.max);
    }
  }

  if (safe.physics) {
    if (safe.physics.gravity !== undefined) {
      safe.physics.gravity = clamp(safe.physics.gravity, limits.gravity.min, limits.gravity.max);
    }
    if (safe.physics.friction !== undefined) {
      safe.physics.friction = clamp(safe.physics.friction, limits.friction.min, limits.friction.max);
    }
    if (safe.physics.bounce !== undefined) {
      safe.physics.bounce = clamp(safe.physics.bounce, limits.bounce.min, limits.bounce.max);
    }
    if (safe.physics.air_resistance !== undefined) {
      safe.physics.air_resistance = clamp(safe.physics.air_resistance, limits.air_resistance.min, limits.air_resistance.max);
    }
    if (safe.physics.collision_force !== undefined) {
      safe.physics.collision_force = clamp(safe.physics.collision_force, limits.collision_force.min, limits.collision_force.max);
    }
  }

  return safe;
}

module.exports = { guard, LIMITS: config.limits };

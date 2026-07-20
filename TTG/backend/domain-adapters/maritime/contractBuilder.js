'use strict';

/**
 * contractBuilder.js
 *
 * Phase 1 — Contract Lock
 *
 * Takes the raw output of maritimeAdapter.adaptVessel() and produces
 * a contract-locked payload that matches engineExecutionContract.json v2.0
 * field-for-field — no drift, no extra fields, no missing required fields.
 *
 * Required fields (from engineExecutionContract.json):
 *   execution_id, trace_id, game_mode, entities[], physics, scoring
 *
 * Rules:
 *   - Missing required field  → throw immediately (fail loud)
 *   - Missing trace_id        → throw immediately
 *   - domain passthrough      → stripped from contract output (kept separately)
 *   - decisionEnvelope        → stripped from contract output (governance only)
 *   - Unknown fields          → stripped silently
 */

const REQUIRED_FIELDS = ['execution_id', 'trace_id', 'game_mode', 'entities', 'physics', 'scoring'];

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Build a strict, contract-locked execution payload from adapter output.
 *
 * @param {Object} adapterSchema  - Output of maritimeAdapter.adaptVessel().schema
 * @returns {{ success, contract, domain, errors }}
 *
 * On success: contract is ready to send to Atharva's execution layer.
 * On failure: contract is null, errors lists every missing/invalid field.
 */
function build(adapterSchema) {
  if (!adapterSchema || typeof adapterSchema !== 'object') {
    return { success: false, contract: null, domain: null, errors: ['adapterSchema must be an object'] };
  }

  // ── 1. trace_id guard — fail immediately, no contract without it ──────────
  if (!adapterSchema.trace_id || typeof adapterSchema.trace_id !== 'string') {
    return { success: false, contract: null, domain: null, errors: ['trace_id is missing — cannot build contract'] };
  }

  // ── 2. Validate all required fields are present ───────────────────────────
  const errors = _validateRequired(adapterSchema);
  if (errors.length > 0) {
    return { success: false, contract: null, domain: adapterSchema.domain || null, errors };
  }

  // ── 3. Build strict contract — only fields defined in v2.0 schema ─────────
  const contract = {
    execution_id: adapterSchema.execution_id,
    trace_id:     adapterSchema.trace_id,
    game_mode:    adapterSchema.game_mode,

    scene: _buildScene(adapterSchema.scene),

    entities: _buildEntities(adapterSchema.entities),

    physics: _buildPhysics(adapterSchema.physics),

    movement: _buildMovement(adapterSchema.movement),

    camera: _buildCamera(adapterSchema.camera),

    spawn_rules: _buildSpawnRules(adapterSchema.spawn_rules),

    scoring: _buildScoring(adapterSchema.scoring),

    player_params: _buildPlayerParams(adapterSchema.player_params)
  };

  // ── 4. Validate the built contract ────────────────────────────────────────
  const contractErrors = _validateContract(contract);
  if (contractErrors.length > 0) {
    return { success: false, contract: null, domain: adapterSchema.domain || null, errors: contractErrors };
  }

  // ── 5. Return contract + domain separately (domain is NOT sent to engine) ─
  return {
    success:  true,
    contract,
    domain:   adapterSchema.domain || null,  // kept for telemetry/artifacts only
    errors:   []
  };
}

// ─── Field builders — each maps adapter fields → contract fields exactly ─────

function _buildScene(scene) {
  if (!scene) {
    return { scene_id: 'scene_maritime', ambient_light: [0.5, 0.7, 0.9], skybox: 'ocean_sky' };
  }
  return {
    scene_id:      scene.scene_id     || 'scene_maritime',
    ambient_light: scene.ambient_light || [0.5, 0.7, 0.9],
    skybox:        scene.skybox        || 'ocean_sky'
  };
}

function _buildEntities(entities) {
  if (!Array.isArray(entities) || entities.length === 0) {
    throw new Error('entities must be a non-empty array');
  }
  return entities.map((e, i) => {
    if (!e.id)        throw new Error(`entities[${i}].id is required`);
    if (!e.type)      throw new Error(`entities[${i}].type is required`);
    if (!e.transform) throw new Error(`entities[${i}].transform is required`);

    const built = {
      id:        e.id,
      type:      e.type,
      transform: {
        position: _vec3(e.transform.position, [0, 0, 0]),
        rotation: _vec3(e.transform.rotation, [0, 0, 0]),
        scale:    _vec3(e.transform.scale,    [1, 1, 1])
      }
    };
    if (e.material)   built.material   = e.material;
    if (e.components) built.components = e.components;
    return built;
  });
}

function _buildPhysics(physics) {
  if (!physics) throw new Error('physics is required');
  return {
    gravity:         _vec3(physics.gravity, [0, 0, 0]),
    friction:        _clamp(physics.friction,        0, 1,   0.1),
    bounce:          _clamp(physics.bounce,          0, 1,   0.0),
    air_resistance:  _clamp(physics.air_resistance,  0, 1,   0.05),
    collision_force: _clamp(physics.collision_force, 0.1, 2, 1.0)
  };
}

function _buildMovement(movement) {
  if (!movement) return { speed: 1, jump_height: 0 };
  return {
    speed:       _clamp(movement.speed,       1, 15, 1),
    jump_height: _clamp(movement.jump_height, 0, 10, 0)
  };
}

function _buildCamera(camera) {
  if (!camera) return { type: 'top_down', distance: 20 };
  return {
    type:     camera.type     || 'top_down',
    distance: _clamp(camera.distance, 5, 20, 20)
  };
}

function _buildSpawnRules(spawn_rules) {
  if (!spawn_rules) return { obstacles: 0, frequency: 1, distance: 10 };
  return {
    obstacles: _clamp(spawn_rules.obstacles, 0, 10, 0),
    frequency: _clamp(spawn_rules.frequency, 0.5, 10, 1),
    distance:  _clamp(spawn_rules.distance,  5, 50, 10)
  };
}

function _buildScoring(scoring) {
  // scoring is required — adapter must have been fixed to produce scoring.rules
  if (!scoring || !scoring.rules) {
    throw new Error('scoring.rules is required — check maritimeAdapter output');
  }
  return {
    rules: {
      distance:     scoring.rules.distance     ?? 0,
      collectibles: scoring.rules.collectibles ?? 0,
      time:         scoring.rules.time         ?? 0
    },
    end_conditions: Array.isArray(scoring.end_conditions) ? scoring.end_conditions : ['time_limit']
  };
}

function _buildPlayerParams(player_params) {
  if (!player_params) return { health: 1, jetpack: false };
  return {
    health:  player_params.health  ?? 1,
    jetpack: player_params.jetpack ?? false
  };
}

// ─── Validation ───────────────────────────────────────────────────────────────

function _validateRequired(schema) {
  return REQUIRED_FIELDS
    .filter(f => schema[f] === undefined || schema[f] === null)
    .map(f => `Required field missing: ${f}`);
}

function _validateContract(contract) {
  const errors = [];

  if (!contract.execution_id) errors.push('execution_id is empty');
  if (!contract.trace_id)     errors.push('trace_id is empty');

  const validModes = ['runner', 'sidescroller', 'open_scene'];
  if (!validModes.includes(contract.game_mode)) {
    errors.push(`game_mode must be one of: ${validModes.join(', ')} — got: ${contract.game_mode}`);
  }

  if (!Array.isArray(contract.entities) || contract.entities.length === 0) {
    errors.push('entities must be a non-empty array');
  }

  if (!Array.isArray(contract.physics.gravity) || contract.physics.gravity.length !== 3) {
    errors.push('physics.gravity must be [x, y, z]');
  }

  if (!contract.scoring || !contract.scoring.rules) {
    errors.push('scoring.rules is required');
  }

  return errors;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _vec3(val, fallback) {
  if (Array.isArray(val) && val.length === 3 && val.every(v => typeof v === 'number' && isFinite(v))) {
    return val;
  }
  return fallback;
}

function _clamp(val, min, max, fallback) {
  const n = parseFloat(val);
  if (isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { build, REQUIRED_FIELDS };

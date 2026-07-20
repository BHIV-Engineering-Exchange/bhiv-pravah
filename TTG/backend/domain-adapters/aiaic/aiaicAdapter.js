'use strict';

/**
 * aiaicAdapter.js
 *
 * Domain adapter: AIAIC → Simulation Node
 *
 * AIAIC domain input describes an assessment scenario:
 *   participants with skill levels, assessment zones,
 *   evaluation rules, time constraints.
 *
 * This adapter:
 *   1. Validates AIAIC domain input
 *   2. Converts it to simulationContract.v1
 *   3. Calls POST /simulate/run on the simulation node
 *   4. Returns simulationState.v1 result
 *
 * NO engine modification. NO game fields. NO domain logic inside engine.
 */

const http = require('http');

// ── Simulation node config ────────────────────────────────────────────────────
const SIM_HOST = process.env.SIM_HOST || 'localhost';
const SIM_PORT = process.env.SIM_PORT || 3001;

// ── AIAIC domain constants ────────────────────────────────────────────────────
const VALID_SKILL_LEVELS  = ['beginner', 'intermediate', 'advanced', 'expert'];
const VALID_ASSESSMENT_TYPES = ['navigation', 'coordination', 'response_time', 'accuracy'];

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Run an AIAIC assessment scenario through the simulation node.
 *
 * @param {Object} aiaicInput - AIAIC domain input
 * @returns {Promise<{ success, result, errors }>}
 */
async function run(aiaicInput) {
  // Step 1: validate domain input
  const validation = _validate(aiaicInput);
  if (!validation.valid) {
    return { success: false, result: null, errors: validation.errors };
  }

  // Step 2: convert to simulationContract.v1
  const contract = _toContract(aiaicInput);

  // Step 3: call simulation node
  let simResult;
  try {
    simResult = await _callSimNode(contract);
  } catch (err) {
    return { success: false, result: null, errors: [`Simulation node unreachable: ${err.message}`] };
  }

  // Step 4: return simulationState.v1 result
  if (simResult.status === 'failed') {
    return { success: false, result: simResult, errors: [simResult.error || 'Simulation failed'] };
  }

  return { success: true, result: simResult, errors: [] };
}

// ─── Step 1: Domain validation ────────────────────────────────────────────────

function _validate(input) {
  const errors = [];

  if (!input || typeof input !== 'object') return { valid: false, errors: ['input must be an object'] };

  if (!input.assessment_id || typeof input.assessment_id !== 'string') errors.push('assessment_id is required (string)');
  if (!input.assessment_type || !VALID_ASSESSMENT_TYPES.includes(input.assessment_type)) {
    errors.push(`assessment_type must be one of: ${VALID_ASSESSMENT_TYPES.join(', ')}`);
  }

  if (!Array.isArray(input.participants) || input.participants.length === 0) {
    errors.push('participants must be a non-empty array');
  } else {
    input.participants.forEach((p, i) => {
      if (!p.id)                                          errors.push(`participants[${i}].id is required`);
      if (!VALID_SKILL_LEVELS.includes(p.skill_level))   errors.push(`participants[${i}].skill_level must be one of: ${VALID_SKILL_LEVELS.join(', ')}`);
      if (!Array.isArray(p.start_position) || p.start_position.length !== 3) errors.push(`participants[${i}].start_position must be [x,y,z]`);
    });
  }

  if (!Array.isArray(input.checkpoints) || input.checkpoints.length === 0) {
    errors.push('checkpoints must be a non-empty array');
  } else {
    input.checkpoints.forEach((c, i) => {
      if (!c.id)                                              errors.push(`checkpoints[${i}].id is required`);
      if (!Array.isArray(c.position) || c.position.length !== 3) errors.push(`checkpoints[${i}].position must be [x,y,z]`);
    });
  }

  return { valid: errors.length === 0, errors };
}

// ─── Step 2: Convert AIAIC domain → simulationContract.v1 ────────────────────

function _toContract(input) {
  const ticks = input.time_limit_ticks || 30;

  const entities  = [];
  const behaviors = [];

  // Map each participant → vessel entity + move_to behavior toward first checkpoint
  const firstCheckpoint = input.checkpoints[0];

  input.participants.forEach(p => {
    const behaviorId = `bhv_${p.id}`;
    const speed      = _skillToSpeed(p.skill_level);

    entities.push({
      id:        p.id,
      type:      'vessel',
      position:  p.start_position,
      rotation:  [0, 0, 0],
      behaviors: [behaviorId],
      state:     'active',
      meta:      { skill_level: p.skill_level, assessment_type: input.assessment_type }
    });

    behaviors.push({
      id:     behaviorId,
      script: 'move_to',
      params: {
        target:    firstCheckpoint.position,
        speed,
        threshold: 2
      }
    });
  });

  // Map each checkpoint → zone entity
  input.checkpoints.forEach(c => {
    entities.push({
      id:        c.id,
      type:      'zone',
      position:  c.position,
      behaviors: [],
      meta:      { radius: c.radius || 8, label: c.label || c.id, order: c.order || 0 }
    });
  });

  // Assessment rules
  const rules = _buildRules(input);

  return {
    trace_id:     input.assessment_id,
    execution_id: `aiaic_exec_${Date.now()}`,
    domain:       'aiaic',
    scenario:     input.assessment_type,
    entities,
    behaviors,
    rules,
    constraints: {
      movement:     { speed: _skillToSpeed(input.participants[0]?.skill_level || 'beginner') },
      physics:      { gravity: [0, -9.8, 0] },
      player_params: { health: input.participants.length }
    },
    ticks
  };
}

// ─── Domain mapping helpers ───────────────────────────────────────────────────

// skill level → movement speed
function _skillToSpeed(skill) {
  return { beginner: 2, intermediate: 3, advanced: 5, expert: 7 }[skill] || 2;
}

function _buildRules(input) {
  const rules = [];

  // Flag participant when they reach a checkpoint zone
  rules.push({
    id:        'checkpoint_reached',
    trigger:   'on_zone_enter',
    condition: { field: 'state', op: 'eq', value: 'active' },
    action:    { type: 'emit_event', params: { event_type: 'checkpoint_reached', data: { assessment_type: input.assessment_type } } },
    enabled:   true
  });

  // Log collisions — penalise in assessment scoring
  rules.push({
    id:        'collision_penalty',
    trigger:   'on_collision',
    condition: { field: 'state', op: 'neq', value: 'stopped' },
    action:    { type: 'flag_entity', params: { reason: 'collision_penalty' } },
    enabled:   true
  });

  // Emit progress event every tick for response_time assessment
  if (input.assessment_type === 'response_time') {
    rules.push({
      id:        'tick_progress',
      trigger:   'on_tick',
      condition: { field: 'state', op: 'eq', value: 'active' },
      action:    { type: 'emit_event', params: { event_type: 'tick_progress', data: {} } },
      enabled:   true
    });
  }

  return rules;
}

// ─── Step 3: Call simulation node ─────────────────────────────────────────────

function _callSimNode(contract) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(contract);
    const req  = http.request({
      hostname: SIM_HOST,
      port:     SIM_PORT,
      path:     '/simulate/run',
      method:   'POST',
      headers:  { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve(JSON.parse(raw)); }
        catch (e) { reject(new Error(`Invalid JSON from sim node: ${raw.slice(0, 100)}`)); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { run };

'use strict';

/**
 * nicaiAdapter.js
 *
 * Domain adapter: NICAI → Simulation Node
 *
 * NICAI domain input describes an intelligence session:
 *   agents with roles, observation zones, patrol/track behaviors,
 *   anomaly detection rules.
 *
 * This adapter:
 *   1. Validates NICAI domain input
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

// ── NICAI domain constants ────────────────────────────────────────────────────
const VALID_AGENT_ROLES  = ['observer', 'tracker', 'sentinel', 'coordinator'];
const VALID_THREAT_LEVELS = ['low', 'medium', 'high', 'critical'];

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Run a NICAI intelligence session through the simulation node.
 *
 * @param {Object} nicaiInput - NICAI domain input
 * @returns {Promise<{ success, result, errors }>}
 */
async function run(nicaiInput) {
  // Step 1: validate domain input
  const validation = _validate(nicaiInput);
  if (!validation.valid) {
    return { success: false, result: null, errors: validation.errors };
  }

  // Step 2: convert to simulationContract.v1
  const contract = _toContract(nicaiInput);

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

  if (!input.session_id || typeof input.session_id !== 'string') errors.push('session_id is required (string)');
  if (!input.mission    || typeof input.mission    !== 'string') errors.push('mission is required (string)');

  if (!Array.isArray(input.agents) || input.agents.length === 0) {
    errors.push('agents must be a non-empty array');
  } else {
    input.agents.forEach((a, i) => {
      if (!a.id)                                    errors.push(`agents[${i}].id is required`);
      if (!VALID_AGENT_ROLES.includes(a.role))      errors.push(`agents[${i}].role must be one of: ${VALID_AGENT_ROLES.join(', ')}`);
      if (!Array.isArray(a.position) || a.position.length !== 3) errors.push(`agents[${i}].position must be [x,y,z]`);
    });
  }

  if (input.threat_level && !VALID_THREAT_LEVELS.includes(input.threat_level)) {
    errors.push(`threat_level must be one of: ${VALID_THREAT_LEVELS.join(', ')}`);
  }

  return { valid: errors.length === 0, errors };
}

// ─── Step 2: Convert NICAI domain → simulationContract.v1 ────────────────────

function _toContract(input) {
  const threat  = input.threat_level || 'low';
  const speed   = _threatToSpeed(threat);
  const ticks   = input.ticks || 20;

  // Map each NICAI agent → simulation entity + behavior
  const entities   = [];
  const behaviors  = [];

  input.agents.forEach(agent => {
    const behaviorId = `bhv_${agent.id}`;
    const script     = _roleToScript(agent.role);
    const params     = _buildBehaviorParams(agent, script, speed, input.agents);

    entities.push({
      id:        agent.id,
      type:      'agent',
      position:  agent.position,
      rotation:  agent.rotation  || [0, 0, 0],
      behaviors: [behaviorId],
      state:     'active',
      meta:      { role: agent.role, mission: input.mission }
    });

    behaviors.push({ id: behaviorId, script, params });
  });

  // Observation zones → zone entities (no behavior)
  if (Array.isArray(input.zones)) {
    input.zones.forEach(z => {
      entities.push({
        id:        z.id,
        type:      'zone',
        position:  z.position,
        behaviors: [],
        meta:      { radius: z.radius || 10, label: z.label || z.id }
      });
    });
  }

  // Anomaly detection rules → simulation rules
  const rules = _buildRules(input, threat);

  return {
    trace_id:     input.session_id,
    execution_id: `nicai_exec_${Date.now()}`,
    domain:       'nicai',
    scenario:     input.mission,
    entities,
    behaviors,
    rules,
    constraints: {
      movement:     { speed },
      physics:      { gravity: [0, 0, 0] },  // NICAI operates in flat space
      player_params: { health: input.agents.length }
    },
    ticks
  };
}

// ─── Domain mapping helpers ───────────────────────────────────────────────────

// threat level → movement speed
function _threatToSpeed(threat) {
  return { low: 2, medium: 4, high: 6, critical: 8 }[threat] || 2;
}

// NICAI agent role → SumScript behavior script
function _roleToScript(role) {
  return {
    observer:    'patrol',
    tracker:     'track',
    sentinel:    'anchor',
    coordinator: 'idle'
  }[role] || 'idle';
}

function _buildBehaviorParams(agent, script, speed, allAgents) {
  switch (script) {
    case 'patrol': {
      // Observer patrols a square around its starting position
      const [x, y, z] = agent.position;
      const r = agent.patrol_radius || 15;
      return {
        waypoints: [[x+r,y,z],[x+r,y,z+r],[x,y,z+r],[x,y,z]],
        speed,
        threshold: 2
      };
    }
    case 'track': {
      // Tracker follows the first non-tracker agent
      const target = allAgents.find(a => a.id !== agent.id && a.role !== 'tracker');
      return { target_id: target?.id || agent.id, speed };
    }
    case 'anchor':
      return {};
    case 'idle':
    default:
      return {};
  }
}

function _buildRules(input, threat) {
  const rules = [];

  // Flag any agent that enters an observation zone
  rules.push({
    id:        'flag_zone_entry',
    trigger:   'on_zone_enter',
    condition: { field: 'state', op: 'eq', value: 'active' },
    action:    { type: 'flag_entity', params: { reason: `zone_entry_${threat}_threat` } },
    enabled:   true
  });

  // Log collisions between agents
  rules.push({
    id:        'log_agent_collision',
    trigger:   'on_collision',
    condition: { field: 'state', op: 'neq', value: 'stopped' },
    action:    { type: 'log', params: { message: 'agent_collision_detected' } },
    enabled:   true
  });

  // On high/critical threat — emit alert event on tick
  if (threat === 'high' || threat === 'critical') {
    rules.push({
      id:        'emit_threat_alert',
      trigger:   'on_tick',
      condition: { field: 'state', op: 'eq', value: 'active' },
      action:    { type: 'emit_event', params: { event_type: 'threat_alert', data: { level: threat } } },
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

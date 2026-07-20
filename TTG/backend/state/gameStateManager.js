'use strict';

/**
 * Game State Manager
 * 
 * Single source of truth for all active gameplay sessions.
 * 
 * Rules:
 *  - State is NEVER mutated directly from outside — only via applyEventToState()
 *  - getCurrentState() returns a deep-frozen snapshot (read-only)
 *  - All mutations are logged with the event that caused them
 */

const { v4: uuidv4 } = require('uuid');
const { EVENT_TYPES } = require('../events/runtimeEvents');

// In-memory store: sessionId → state object
const _sessions = new Map();

// ─── Template defaults per game mode ────────────────────────────────────────

const MODE_DEFAULTS = {
  runner: {
    player:   { health: 3,   max_health: 3,   lives: 3 },
    entities: { enemy_count: 0, obstacle_count: 3, collectible_count: 5 },
    physics:  { gravity: -9.8, friction: 0.5, collision_force: 1.0 }
  },
  arena: {
    player:   { health: 100, max_health: 100, lives: 1 },
    entities: { enemy_count: 5, obstacle_count: 0, collectible_count: 3 },
    physics:  { gravity: -9.8, friction: 0.5, collision_force: 1.0 }
  },
  platformer: {
    player:   { health: 3,   max_health: 3,   lives: 3 },
    entities: { enemy_count: 0, obstacle_count: 0, collectible_count: 0 },
    physics:  { gravity: -9.8, friction: 0.5, collision_force: 1.0 }
  }
};

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Create a new gameplay state for a session.
 * 
 * @param {string} sessionId   - Unique session ID (from execution schema)
 * @param {Object} template    - Game template object (from templateSelector / stateInitializer)
 * @param {Object} [overrides] - Optional field overrides (e.g. from execution schema params)
 * @returns {Object} The created state (read-only snapshot)
 */
function createGameState(sessionId, template, overrides = {}) {
  if (!sessionId) throw new Error('[GSM] sessionId is required');
  if (_sessions.has(sessionId)) {
    console.warn(`[GSM] Session ${sessionId} already exists — returning existing state`);
    return getCurrentState(sessionId);
  }

  const gameMode = _resolveGameMode(template);
  const defaults = MODE_DEFAULTS[gameMode] || MODE_DEFAULTS.runner;
  const params   = template.defaults || template.parameters || {};

  const now = Date.now();

  const state = {
    session_id: sessionId,
    game_mode:  gameMode,
    status:     'initializing',

    player: {
      health:          params.player_health  ?? defaults.player.health,
      max_health:      params.player_health  ?? defaults.player.max_health,
      score:           0,
      lives:           params.lives          ?? defaults.player.lives,
      position:        [0, 0, 0],
      is_alive:        true,
      active_powerups: []
    },

    entities: {
      enemy_count:      params.enemy_count      ?? defaults.entities.enemy_count,
      obstacle_count:   params.obstacle_count   ?? defaults.entities.obstacle_count,
      collectible_count:params.collectible_count ?? defaults.entities.collectible_count,
      active_entities:  {}
    },

    world: {
      level:        1,
      time_elapsed: 0,
      difficulty:   1,
      theme:        params.theme || overrides.theme || 'default',
      physics: {
        gravity:         params.gravity         ?? defaults.physics.gravity,
        friction:        params.friction        ?? defaults.physics.friction,
        collision_force: params.collision_force ?? defaults.physics.collision_force
      }
    },

    meta: {
      created_at:       now,
      last_updated_at:  now,
      event_count:      0,
      snapshot_version: 0,
      execution_id:     overrides.execution_id || null,
      trace_id:         overrides.trace_id     || null
    }
  };

  _sessions.set(sessionId, state);
  console.log(`[GSM] State created — session: ${sessionId}, mode: ${gameMode}`);
  return getCurrentState(sessionId);
}

/**
 * Apply a validated runtime event to the session state.
 * This is the ONLY way state is mutated.
 * 
 * @param {string} sessionId - Target session
 * @param {Object} event     - Validated runtime event (from runtimeEvents.js)
 * @returns {Object} { success, state, changes } — state is a read-only snapshot
 */
function applyEventToState(sessionId, event) {
  const state = _sessions.get(sessionId);
  if (!state) {
    return { success: false, error: `Session ${sessionId} not found` };
  }
  if (state.status === 'game_over' || state.status === 'completed') {
    return { success: false, error: `Session ${sessionId} is ${state.status} — no further updates` };
  }

  const changes = _applyMutation(state, event);

  state.meta.event_count++;
  state.meta.last_updated_at = Date.now();

  console.log(`[GSM] Event applied — session: ${sessionId}, event: ${event.event_type}, changes: ${JSON.stringify(changes)}`);

  return {
    success: true,
    state:   getCurrentState(sessionId),
    changes
  };
}

/**
 * Return a deep-frozen read-only snapshot of the current state.
 * 
 * @param {string} sessionId
 * @returns {Object|null} Frozen state snapshot, or null if session not found
 */
function getCurrentState(sessionId) {
  const state = _sessions.get(sessionId);
  if (!state) return null;
  return _deepFreeze(JSON.parse(JSON.stringify(state)));
}

/**
 * Mark session as running (called after engine confirms game started).
 * @param {string} sessionId
 */
function setRunning(sessionId) {
  const state = _sessions.get(sessionId);
  if (state && state.status === 'initializing') {
    state.status = 'running';
    state.meta.last_updated_at = Date.now();
    console.log(`[GSM] Session ${sessionId} → running`);
  }
}

/**
 * Check if a session exists.
 * @param {string} sessionId
 * @returns {boolean}
 */
function hasSession(sessionId) {
  return _sessions.has(sessionId);
}

/**
 * Remove a session from memory (call after bucket snapshot is written).
 * @param {string} sessionId
 */
function destroySession(sessionId) {
  _sessions.delete(sessionId);
  console.log(`[GSM] Session ${sessionId} destroyed`);
}

/**
 * Return all active session IDs (for monitoring).
 * @returns {string[]}
 */
function getActiveSessions() {
  return Array.from(_sessions.keys());
}

// ─── Event → State Mutation ──────────────────────────────────────────────────

/**
 * Route an event to the correct mutation handler.
 * Returns a plain object describing what changed.
 */
function _applyMutation(state, event) {
  switch (event.event_type) {

    case EVENT_TYPES.HEALTH_CHANGED: {
      const delta = event.context?.delta ?? 0;
      const prev  = state.player.health;
      state.player.health = Math.max(0, Math.min(state.player.max_health, prev + delta));
      if (state.player.health === 0) state.player.is_alive = false;
      return { field: 'player.health', from: prev, to: state.player.health };
    }

    case EVENT_TYPES.SCORE_UPDATE: {
      const delta = event.context?.score_delta ?? event.context?.score ?? 0;
      const prev  = state.player.score;
      state.player.score = Math.max(0, prev + delta);
      return { field: 'player.score', from: prev, to: state.player.score };
    }

    case EVENT_TYPES.POSITION_UPDATE: {
      const pos  = event.context?.position;
      const prev = [...state.player.position];
      if (Array.isArray(pos) && pos.length === 3) {
        state.player.position = pos;
      } else if (pos && typeof pos === 'object') {
        state.player.position = [pos.x ?? 0, pos.y ?? 0, pos.z ?? 0];
      }
      return { field: 'player.position', from: prev, to: state.player.position };
    }

    case EVENT_TYPES.PLAYER_DEATH: {
      const prevLives = state.player.lives;
      state.player.is_alive = false;
      state.player.lives    = Math.max(0, prevLives - 1);
      if (state.player.lives === 0) state.status = 'game_over';
      return { field: 'player.lives', from: prevLives, to: state.player.lives, status: state.status };
    }

    case EVENT_TYPES.ENTITY_SPAWNED: {
      const entityId   = event.entities?.[0];
      const entityType = event.context?.entity_type;
      if (entityId && entityType) {
        state.entities.active_entities[entityId] = entityType;
        if (entityType === 'enemy')      state.entities.enemy_count++;
        if (entityType === 'obstacle')   state.entities.obstacle_count++;
        if (entityType === 'collectible')state.entities.collectible_count++;
      }
      return { field: `entities.${entityType}_count`, entityId, entityType };
    }

    case EVENT_TYPES.ENTITY_DESTROYED: {
      const entityId   = event.entities?.[0];
      const entityType = event.context?.entity_type
                      || state.entities.active_entities[entityId];
      if (entityId) delete state.entities.active_entities[entityId];
      if (entityType === 'enemy')       state.entities.enemy_count      = Math.max(0, state.entities.enemy_count - 1);
      if (entityType === 'obstacle')    state.entities.obstacle_count   = Math.max(0, state.entities.obstacle_count - 1);
      if (entityType === 'collectible') state.entities.collectible_count= Math.max(0, state.entities.collectible_count - 1);
      return { field: `entities.${entityType}_count`, entityId, entityType };
    }

    case EVENT_TYPES.PICKUP_COLLECTED: {
      const pickupId = event.entities?.[1];
      if (pickupId) delete state.entities.active_entities[pickupId];
      const prev = state.entities.collectible_count;
      state.entities.collectible_count = Math.max(0, prev - 1);
      return { field: 'entities.collectible_count', from: prev, to: state.entities.collectible_count };
    }

    case EVENT_TYPES.LEVEL_COMPLETE: {
      const prevLevel = state.world.level;
      state.world.level++;
      state.world.difficulty = Math.min(10, state.world.difficulty + 1);
      return { field: 'world.level', from: prevLevel, to: state.world.level };
    }

    case EVENT_TYPES.GAME_START: {
      state.status = 'running';
      return { field: 'status', to: 'running' };
    }

    case EVENT_TYPES.GAME_END: {
      state.status = 'completed';
      return { field: 'status', to: 'completed' };
    }

    case EVENT_TYPES.TIMER_EXPIRED: {
      state.world.time_elapsed = event.context?.timer_value ?? state.world.time_elapsed;
      return { field: 'world.time_elapsed', to: state.world.time_elapsed };
    }

    case EVENT_TYPES.COLLISION: {
      // Collision itself doesn't mutate state — health_changed event handles damage.
      // Record position if provided.
      const pos = event.context?.position;
      if (pos) {
        state.player.position = Array.isArray(pos)
          ? pos
          : [pos.x ?? 0, pos.y ?? 0, pos.z ?? 0];
      }
      return { field: 'player.position', note: 'collision position recorded' };
    }

    default:
      return { note: `no mutation defined for ${event.event_type}` };
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function _resolveGameMode(template) {
  const id = (template.template_id || '').toLowerCase();
  if (id.includes('arena'))     return 'arena';
  if (id.includes('platformer'))return 'platformer';
  if (id.includes('runner'))    return 'runner';
  // fallback: check entities list
  if (template.entities?.includes('enemy')) return 'arena';
  if (template.entities?.includes('platform')) return 'platformer';
  return 'runner';
}

function _deepFreeze(obj) {
  Object.getOwnPropertyNames(obj).forEach(name => {
    const val = obj[name];
    if (val && typeof val === 'object') _deepFreeze(val);
  });
  return Object.freeze(obj);
}

// ─── Exports ─────────────────────────────────────────────────────────────────

/**
 * Internal accessor for stateSnapshot.js restore/bump operations.
 * Not for general use — snapshot module only.
 */
function __internals() {
  return { _sessions };
}

module.exports = {
  createGameState,
  applyEventToState,
  getCurrentState,
  setRunning,
  hasSession,
  destroySession,
  getActiveSessions,
  __internals
};

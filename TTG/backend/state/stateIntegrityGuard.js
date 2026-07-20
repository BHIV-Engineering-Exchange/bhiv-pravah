'use strict';

/**
 * State Integrity Guard
 *
 * Three protection layers:
 *   1. validateState(state)          — structural integrity of a state object
 *   2. validateTransition(before, event, after) — event/state mismatch detection
 *   3. validateEvent(event, state)   — event legality against current state
 *
 * Used as a gate before applyEventToState() and after restore().
 * All checks are pure functions — no side effects, no I/O.
 */

const { EVENT_TYPES } = require('../events/runtimeEvents');

// Valid status values from gameStateSchema.json
const VALID_STATUSES   = ['initializing', 'running', 'paused', 'game_over', 'completed'];
const VALID_GAME_MODES = ['runner', 'arena', 'platformer'];

// Status transitions that are allowed: from → [allowed next statuses]
const ALLOWED_TRANSITIONS = {
  initializing: ['running', 'game_over'],
  running:      ['paused', 'game_over', 'completed'],
  paused:       ['running', 'game_over'],
  game_over:    [],          // terminal — no further transitions
  completed:    []           // terminal — no further transitions
};

// Events that must NOT be applied to a terminal session
const BLOCKED_IN_TERMINAL = new Set(Object.values(EVENT_TYPES));

// Events that require player.is_alive === true
const REQUIRES_ALIVE = new Set([
  EVENT_TYPES.COLLISION,
  EVENT_TYPES.HEALTH_CHANGED,
  EVENT_TYPES.SCORE_UPDATE,
  EVENT_TYPES.PICKUP_COLLECTED,
  EVENT_TYPES.POSITION_UPDATE
]);

// ─── 1. State Structure Validation ───────────────────────────────────────────

/**
 * Validate the structural integrity of a state object.
 * Checks required fields, types, and value bounds.
 *
 * @param {Object} state
 * @returns {{ valid: boolean, violations: string[] }}
 */
function validateState(state) {
  const v = [];

  if (!state || typeof state !== 'object') {
    return { valid: false, violations: ['state must be a non-null object'] };
  }

  // Top-level required fields
  if (!state.session_id || typeof state.session_id !== 'string')
    v.push('session_id must be a non-empty string');

  if (!VALID_GAME_MODES.includes(state.game_mode))
    v.push(`game_mode must be one of ${VALID_GAME_MODES.join(', ')} — got: ${state.game_mode}`);

  if (!VALID_STATUSES.includes(state.status))
    v.push(`status must be one of ${VALID_STATUSES.join(', ')} — got: ${state.status}`);

  // player
  const p = state.player;
  if (!p || typeof p !== 'object') {
    v.push('player must be an object');
  } else {
    if (typeof p.health !== 'number' || p.health < 0)
      v.push(`player.health must be >= 0 — got: ${p.health}`);
    if (typeof p.max_health === 'number' && p.health > p.max_health)
      v.push(`player.health (${p.health}) exceeds max_health (${p.max_health})`);
    if (typeof p.score !== 'number' || p.score < 0)
      v.push(`player.score must be >= 0 — got: ${p.score}`);
    if (typeof p.lives !== 'number' || p.lives < 0)
      v.push(`player.lives must be >= 0 — got: ${p.lives}`);
    if (!Array.isArray(p.position) || p.position.length !== 3)
      v.push('player.position must be [x, y, z] array of length 3');
    if (typeof p.is_alive !== 'boolean')
      v.push('player.is_alive must be boolean');
    // Consistency: health=0 must mean is_alive=false
    if (p.health === 0 && p.is_alive === true)
      v.push('player.health is 0 but is_alive is true — inconsistent state');
    // Consistency: lives=0 and status not game_over is suspicious (warn only)
    if (p.lives === 0 && state.status === 'running')
      v.push('player.lives is 0 but status is running — expected game_over');
  }

  // entities
  const e = state.entities;
  if (!e || typeof e !== 'object') {
    v.push('entities must be an object');
  } else {
    if (typeof e.enemy_count !== 'number' || e.enemy_count < 0)
      v.push(`entities.enemy_count must be >= 0 — got: ${e.enemy_count}`);
    if (typeof e.obstacle_count !== 'number' || e.obstacle_count < 0)
      v.push(`entities.obstacle_count must be >= 0 — got: ${e.obstacle_count}`);
    if (typeof e.collectible_count !== 'number' || e.collectible_count < 0)
      v.push(`entities.collectible_count must be >= 0 — got: ${e.collectible_count}`);
    if (typeof e.active_entities !== 'object' || Array.isArray(e.active_entities))
      v.push('entities.active_entities must be a plain object');
  }

  // world
  const w = state.world;
  if (!w || typeof w !== 'object') {
    v.push('world must be an object');
  } else {
    if (typeof w.level !== 'number' || w.level < 1)
      v.push(`world.level must be >= 1 — got: ${w.level}`);
    if (typeof w.time_elapsed !== 'number' || w.time_elapsed < 0)
      v.push(`world.time_elapsed must be >= 0 — got: ${w.time_elapsed}`);
    if (w.difficulty !== undefined && (typeof w.difficulty !== 'number' || w.difficulty < 1))
      v.push(`world.difficulty must be >= 1 — got: ${w.difficulty}`);
  }

  // meta
  const m = state.meta;
  if (!m || typeof m !== 'object') {
    v.push('meta must be an object');
  } else {
    if (typeof m.event_count !== 'number' || m.event_count < 0)
      v.push(`meta.event_count must be >= 0 — got: ${m.event_count}`);
    if (typeof m.snapshot_version !== 'number' || m.snapshot_version < 0)
      v.push(`meta.snapshot_version must be >= 0 — got: ${m.snapshot_version}`);
    if (typeof m.created_at !== 'number')
      v.push('meta.created_at must be a number');
    if (typeof m.last_updated_at !== 'number')
      v.push('meta.last_updated_at must be a number');
    if (m.last_updated_at < m.created_at)
      v.push('meta.last_updated_at is before created_at — clock corruption');
  }

  return { valid: v.length === 0, violations: v };
}

// ─── 2. Transition Validation ─────────────────────────────────────────────────

/**
 * Validate that a state transition caused by an event is legal.
 * Compares stateBefore → stateAfter and checks:
 *   - status transition is allowed
 *   - numeric fields only moved in expected directions
 *   - no field was corrupted (NaN, undefined, negative where forbidden)
 *
 * @param {Object} stateBefore  — frozen snapshot before event
 * @param {Object} event        — the event that caused the transition
 * @param {Object} stateAfter   — frozen snapshot after event
 * @returns {{ valid: boolean, violations: string[] }}
 */
function validateTransition(stateBefore, event, stateAfter) {
  const v = [];

  // Status transition must be allowed
  const fromStatus = stateBefore.status;
  const toStatus   = stateAfter.status;
  if (fromStatus !== toStatus) {
    const allowed = ALLOWED_TRANSITIONS[fromStatus] || [];
    if (!allowed.includes(toStatus)) {
      v.push(`Invalid status transition: ${fromStatus} → ${toStatus} (event: ${event.event_type})`);
    }
  }

  // Score must never decrease (except explicit reset — not in current event set)
  if (stateAfter.player.score < stateBefore.player.score) {
    v.push(`player.score decreased: ${stateBefore.player.score} → ${stateAfter.player.score} (event: ${event.event_type})`);
  }

  // Health must not exceed max_health
  if (stateAfter.player.health > stateAfter.player.max_health) {
    v.push(`player.health (${stateAfter.player.health}) exceeds max_health (${stateAfter.player.max_health}) after ${event.event_type}`);
  }

  // Lives must not increase (no life-gain mechanic in current system)
  if (stateAfter.player.lives > stateBefore.player.lives) {
    v.push(`player.lives increased: ${stateBefore.player.lives} → ${stateAfter.player.lives} — no life-gain mechanic exists`);
  }

  // Level must not decrease
  if (stateAfter.world.level < stateBefore.world.level) {
    v.push(`world.level decreased: ${stateBefore.world.level} → ${stateAfter.world.level} (event: ${event.event_type})`);
  }

  // event_count must increment by exactly 1
  const expectedCount = stateBefore.meta.event_count + 1;
  if (stateAfter.meta.event_count !== expectedCount) {
    v.push(`meta.event_count jumped from ${stateBefore.meta.event_count} to ${stateAfter.meta.event_count} — expected ${expectedCount}`);
  }

  // last_updated_at must not go backwards
  if (stateAfter.meta.last_updated_at < stateBefore.meta.last_updated_at) {
    v.push('meta.last_updated_at went backwards — clock skew or corruption');
  }

  // Structural check on the resulting state
  const structCheck = validateState(stateAfter);
  if (!structCheck.valid) {
    structCheck.violations.forEach(msg => v.push(`post-transition: ${msg}`));
  }

  return { valid: v.length === 0, violations: v };
}

// ─── 3. Event Legality Validation ─────────────────────────────────────────────

/**
 * Validate that an event is legal to apply given the current state.
 * Catches event/state mismatches before mutation happens.
 *
 * @param {Object} event  — runtime event
 * @param {Object} state  — current frozen state snapshot
 * @returns {{ valid: boolean, violations: string[] }}
 */
function validateEvent(event, state) {
  const v = [];

  if (!event || !event.event_type)
    return { valid: false, violations: ['event must have event_type'] };

  if (!state)
    return { valid: false, violations: ['state is required for event validation'] };

  // Block all events on terminal sessions
  const terminal = state.status === 'game_over' || state.status === 'completed';
  if (terminal && BLOCKED_IN_TERMINAL.has(event.event_type)) {
    v.push(`Event ${event.event_type} rejected — session is ${state.status} (terminal)`);
  }

  // Block events that require a live player when player is dead
  if (REQUIRES_ALIVE.has(event.event_type) && state.player.is_alive === false) {
    v.push(`Event ${event.event_type} rejected — player is not alive`);
  }

  // entity_destroyed: entity must exist in active_entities
  if (event.event_type === EVENT_TYPES.ENTITY_DESTROYED) {
    const entityId = event.entities?.[0];
    if (entityId && Object.keys(state.entities.active_entities).length > 0) {
      if (!state.entities.active_entities[entityId]) {
        v.push(`entity_destroyed for unknown entity: ${entityId} — not in active_entities`);
      }
    }
  }

  // player_death: player must currently be alive to die
  if (event.event_type === EVENT_TYPES.PLAYER_DEATH && state.player.is_alive === false) {
    v.push('player_death event rejected — player is already dead');
  }

  // game_start: only valid from initializing
  if (event.event_type === EVENT_TYPES.GAME_START && state.status !== 'initializing') {
    v.push(`game_start rejected — session is already ${state.status}`);
  }

  // health_changed: delta must be a number
  if (event.event_type === EVENT_TYPES.HEALTH_CHANGED) {
    const delta = event.context?.delta;
    if (delta !== undefined && typeof delta !== 'number') {
      v.push(`health_changed.context.delta must be a number — got: ${typeof delta}`);
    }
  }

  // score_update: delta must not be negative (use health_changed for damage)
  if (event.event_type === EVENT_TYPES.SCORE_UPDATE) {
    const delta = event.context?.score_delta ?? event.context?.score;
    if (typeof delta === 'number' && delta < 0) {
      v.push(`score_update.context.score_delta must be >= 0 — got: ${delta}`);
    }
  }

  return { valid: v.length === 0, violations: v };
}

// ─── Guard wrapper ────────────────────────────────────────────────────────────

/**
 * Full guard: validate event legality + post-transition integrity.
 * Call this as a wrapper around gsm.applyEventToState().
 *
 * @param {Object}   state       — current state snapshot (before mutation)
 * @param {Object}   event       — event about to be applied
 * @param {Function} applyFn     — () => gsm.applyEventToState(sessionId, event)
 * @returns {{ success, state, changes, violations }}
 */
function guardedApply(state, event, applyFn) {
  // Pre-check: event legality
  const preCheck = validateEvent(event, state);
  if (!preCheck.valid) {
    console.warn(`[INTEGRITY] Pre-check failed for ${event.event_type}:`, preCheck.violations);
    return { success: false, violations: preCheck.violations, blocked: true };
  }

  // Apply mutation
  const result = applyFn();
  if (!result.success) return result;

  // Post-check: transition integrity
  const postCheck = validateTransition(state, event, result.state);
  if (!postCheck.valid) {
    console.error(`[INTEGRITY] Post-transition violation for ${event.event_type}:`, postCheck.violations);
    return { ...result, violations: postCheck.violations, integrity_warning: true };
  }

  return { ...result, violations: [] };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  validateState,
  validateTransition,
  validateEvent,
  guardedApply
};

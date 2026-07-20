'use strict';

/**
 * State Event Processor
 *
 * Sits between the engine runtime and the Game State Manager.
 *
 * Responsibility:
 *   1. Receive a raw runtime event (from engine socket / dispatcher pipeline)
 *   2. Normalise it into a state-mutation-ready form
 *   3. Derive the correct delta values (health delta, score delta, etc.)
 *   4. Call gameStateManager.applyEventToState()
 *   5. Return { success, state, changes } to the caller
 *      so the Consequence Compiler can read updated state immediately
 *
 * This module does NOT dispatch jobs — that is the Consequence Compiler's job.
 * It only updates state.
 */

const { EVENT_TYPES, validateRuntimeEvent } = require('../events/runtimeEvents');
const gsm = require('./gameStateManager');

// ─── Score deltas per event (matches consequenceRules.json score_delta values) ─

const SCORE_DELTAS = {
  enemy_killed:      100,   // entity_destroyed where entity_type === 'enemy'
  pickup_collected:   10,   // pickup_collected (coin)
  powerup_collected:  50,   // pickup_collected (powerup)
  level_complete:    500    // level_complete bonus
};

// ─── Health deltas per collision entity type ──────────────────────────────────

const COLLISION_DAMAGE = {
  obstacle: -1,   // runner: one hit = instant death (health 3 → 2 → 1 → 0)
  enemy:    -1,   // arena: one enemy hit = -1 health
  default:  -1
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Process a raw runtime event and apply it to the session's game state.
 *
 * @param {string} sessionId  - Target session
 * @param {Object} rawEvent   - Raw event from engine (may be non-standard format)
 * @returns {Object} { success, state, changes, error? }
 */
function processEvent(sessionId, rawEvent) {
  if (!sessionId) return _fail('sessionId is required');
  if (!gsm.hasSession(sessionId)) return _fail(`No active session: ${sessionId}`);

  // Step 1 — normalise
  const event = _normalise(rawEvent, sessionId);

  // Step 2 — validate
  const validation = validateRuntimeEvent(event);
  if (!validation.valid) {
    return _fail(`Invalid event: ${validation.errors.join(', ')}`);
  }

  // Step 3 — enrich with derived deltas before handing to GSM
  const enriched = _enrich(event, sessionId);

  // Step 4 — apply to state
  const result = gsm.applyEventToState(sessionId, enriched);

  if (!result.success) return _fail(result.error);

  console.log(`[SEP] ${event.event_type} → session ${sessionId} | changes: ${JSON.stringify(result.changes)}`);

  return {
    success: true,
    state:   result.state,
    changes: result.changes,
    event:   enriched
  };
}

/**
 * Convenience: process multiple events in sequence for the same session.
 * Stops on first failure.
 *
 * @param {string}   sessionId
 * @param {Object[]} events
 * @returns {Object[]} Array of per-event results
 */
function processEventBatch(sessionId, events) {
  const results = [];
  for (const event of events) {
    const result = processEvent(sessionId, event);
    results.push(result);
    if (!result.success) break;
  }
  return results;
}

// ─── Normalisation ────────────────────────────────────────────────────────────

/**
 * Accept both standard and legacy engine event shapes.
 * Always returns a fully-formed runtime event object.
 */
function _normalise(raw, sessionId) {
  return {
    event_type:      raw.event_type || raw.type || 'unknown',
    event_id:        raw.event_id   || raw.id   || `evt_${Date.now()}`,
    timestamp:       raw.timestamp  || raw.ts   || Date.now(),
    game_session_id: raw.game_session_id || raw.sessionId || sessionId,
    entities:        raw.entities   || [],
    context:         raw.context    || raw.data || {},
    metadata:        raw.metadata   || {}
  };
}

// ─── Enrichment ───────────────────────────────────────────────────────────────

/**
 * Add derived fields to the event context so GSM mutations are unambiguous.
 *
 * Examples:
 *   collision(player, obstacle) → context.delta = -1
 *   entity_destroyed(enemy)     → context.score_delta = 100
 *   pickup_collected            → context.score_delta = 10
 */
function _enrich(event, sessionId) {
  const enriched = JSON.parse(JSON.stringify(event)); // shallow clone
  const ctx      = enriched.context;
  const state    = gsm.getCurrentState(sessionId);

  switch (event.event_type) {

    // ── collision ─────────────────────────────────────────────────────────────
    case EVENT_TYPES.COLLISION: {
      const entityType = _resolveCollisionTarget(enriched.entities, state);
      ctx.entity_type  = ctx.entity_type || entityType;

      // Derive a health_changed sub-event delta so GSM can apply damage
      // The GSM collision handler records position only; damage comes via
      // a synthetic health_changed event we attach as context for Phase 7.
      const damage = COLLISION_DAMAGE[entityType] ?? COLLISION_DAMAGE.default;
      ctx._derived_health_delta = damage;
      ctx._derived_entity_type  = entityType;
      break;
    }

    // ── entity_destroyed (enemy killed) ───────────────────────────────────────
    case EVENT_TYPES.ENTITY_DESTROYED: {
      const entityType = ctx.entity_type
        || _lookupEntityType(enriched.entities[0], state);
      ctx.entity_type = entityType;

      if (entityType === 'enemy') {
        ctx.score_delta = ctx.score_delta ?? SCORE_DELTAS.enemy_killed;
      }
      break;
    }

    // ── pickup_collected ──────────────────────────────────────────────────────
    case EVENT_TYPES.PICKUP_COLLECTED: {
      const isPowerup = ctx.pickup_type === 'powerup' || ctx.is_powerup === true;
      ctx.score_delta = ctx.score_delta
        ?? (isPowerup ? SCORE_DELTAS.powerup_collected : SCORE_DELTAS.pickup_collected);
      break;
    }

    // ── score_update (direct score event from engine) ─────────────────────────
    case EVENT_TYPES.SCORE_UPDATE: {
      // Engine may send absolute score or a delta — normalise to delta
      if (ctx.score !== undefined && ctx.score_delta === undefined) {
        const currentScore = state?.player?.score ?? 0;
        ctx.score_delta = ctx.score - currentScore;
      }
      break;
    }

    // ── health_changed ────────────────────────────────────────────────────────
    case EVENT_TYPES.HEALTH_CHANGED: {
      // Ensure delta field exists — engine may send absolute health value
      if (ctx.health !== undefined && ctx.delta === undefined) {
        const currentHealth = state?.player?.health ?? 0;
        ctx.delta = ctx.health - currentHealth;
      }
      break;
    }

    // ── level_complete ────────────────────────────────────────────────────────
    case EVENT_TYPES.LEVEL_COMPLETE: {
      ctx.score_delta = ctx.score_delta ?? SCORE_DELTAS.level_complete;
      break;
    }

    // All other events pass through unchanged
    default:
      break;
  }

  return enriched;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Determine what the player collided with from the entities array.
 * entities[0] is always the player, entities[1] is the target.
 */
function _resolveCollisionTarget(entities, state) {
  const targetId = entities?.[1];
  if (!targetId) return 'unknown';

  // Check active_entities map first
  const fromMap = state?.entities?.active_entities?.[targetId];
  if (fromMap) return fromMap;

  // Fall back to name-based inference
  if (targetId.startsWith('enemy'))    return 'enemy';
  if (targetId.startsWith('obstacle')) return 'obstacle';
  if (targetId.startsWith('wall'))     return 'obstacle';
  if (targetId.startsWith('platform')) return 'platform';
  return 'unknown';
}

/**
 * Look up entity type from the active_entities map by ID.
 */
function _lookupEntityType(entityId, state) {
  if (!entityId || !state) return 'unknown';
  return state.entities?.active_entities?.[entityId] || 'unknown';
}

function _fail(error) {
  console.error(`[SEP] Error: ${error}`);
  return { success: false, error };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  processEvent,
  processEventBatch,
  SCORE_DELTAS,
  COLLISION_DAMAGE
};

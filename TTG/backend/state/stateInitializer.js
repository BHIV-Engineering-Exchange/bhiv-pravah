'use strict';

/**
 * State Initializer
 *
 * Integration point between Prompt Runner and the Game State Engine.
 *
 * Flow:
 *   Prompt Runner output
 *     → convertToExecutionSchema()       [prompt_runner/adapter.js]
 *     → initializeFromExecutionSchema()  [this file]
 *         → resolve game mode
 *         → load matching template
 *         → extract state params from schema
 *         → gsm.createGameState()
 *         → stateBucketWriter.writeExecutionSchema()
 *     → returns { sessionId, state }
 *
 * Also supports direct initialization from a raw intent string
 * via initializeFromIntent() for testing and internal use.
 */

const { v4: uuidv4 }          = require('uuid');
const { selectTemplate }      = require('../game-templates/templateSelector');
const { injectParameters }    = require('../game-templates/parameterInjector');
const gsm                     = require('./gameStateManager');
const stateBucketWriter       = require('./stateBucketWriter');

// ─── Game mode normalisation ──────────────────────────────────────────────────
// prompt_runner/adapter.js uses 'open_scene' and 'sidescroller'
// GSM uses 'arena' and 'platformer' — map them here

const GAME_MODE_MAP = {
  runner:       'runner',
  sidescroller: 'platformer',
  open_scene:   'arena',
  platformer:   'platformer',
  arena:        'arena'
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Primary entry point.
 * Takes the full execution data object produced by prompt_runner/adapter.js
 * convertToExecutionSchema() and initializes a game state session from it.
 *
 * @param {Object} executionData  — { execution_id, trace_id, user_id, executionSchema }
 * @param {string} [sessionId]   — optional override; auto-generated if omitted
 * @returns {Promise<Object>} { success, sessionId, state, template } | { success: false, error }
 */
async function initializeFromExecutionSchema(executionData, sessionId = null) {
  const { execution_id, trace_id, executionSchema } = executionData;

  if (!executionSchema) return _fail('executionData.executionSchema is required');
  if (!execution_id)    return _fail('executionData.execution_id is required');

  // Step 1 — resolve GSM-compatible game mode
  const rawMode  = executionSchema.game_mode || 'runner';
  const gameMode = GAME_MODE_MAP[rawMode] || 'runner';

  // Step 2 — load the matching template
  const template = _loadTemplate(gameMode, executionSchema);

  // Step 3 — extract state-relevant params from the execution schema
  const stateParams = _extractStateParams(executionSchema, gameMode);

  // Merge schema params into template defaults so GSM picks them up
  template.defaults = { ...template.defaults, ...stateParams };

  // Step 4 — generate session ID
  const sid = sessionId || `session_${execution_id}`;

  // Step 5 — create game state
  const state = gsm.createGameState(sid, template, {
    execution_id,
    trace_id: trace_id || null
  });

  if (!state) return _fail(`GSM failed to create state for session: ${sid}`);

  // Step 6 — persist execution schema to bucket (non-fatal if it fails)
  await stateBucketWriter.writeExecutionSchema(sid, execution_id, trace_id, executionSchema)
    .catch(err => console.warn(`[STATE_INIT] Bucket schema write failed (non-fatal): ${err.message}`));

  console.log(`[STATE_INIT] Initialized — session: ${sid}, mode: ${gameMode}, health: ${state.player.health}, enemies: ${state.entities.enemy_count}`);

  return { success: true, sessionId: sid, state, template };
}

/**
 * Convenience: initialize directly from a natural language intent string.
 * Uses executionSchemaBuilder to produce the schema, then calls
 * initializeFromExecutionSchema().
 *
 * Useful for testing and internal pipeline use without a live Prompt Runner.
 *
 * @param {string} intent     — e.g. "create a hard arena game with many enemies"
 * @param {string} [userId]
 * @returns {Promise<Object>} same shape as initializeFromExecutionSchema()
 */
async function initializeFromIntent(intent, userId = 'system') {
  if (!intent) return _fail('intent string is required');

  const { buildExecutionSchema } = require('../core/executionSchemaBuilder');
  const { execution_id, trace_id, executionSchema } = _wrapSchema(
    buildExecutionSchema(intent),
    userId
  );

  return initializeFromExecutionSchema({ execution_id, trace_id, executionSchema });
}

// ─── Parameter extraction ─────────────────────────────────────────────────────

/**
 * Pull state-relevant fields out of the execution schema.
 * These override the template defaults inside GSM.
 *
 * Maps execution schema fields → GSM template.defaults keys.
 */
function _extractStateParams(schema, gameMode) {
  const params = {};

  // Player health — from player_params.health (set by prompt_runner/adapter.js)
  if (schema.player_params?.health !== undefined) {
    params.player_health = schema.player_params.health;
  }

  // Obstacle / enemy counts — from spawn_rules.obstacles
  if (schema.spawn_rules?.obstacles !== undefined) {
    if (gameMode === 'arena') {
      params.enemy_count    = schema.spawn_rules.obstacles;
    } else {
      params.obstacle_count = schema.spawn_rules.obstacles;
    }
  }

  // Physics — pass through directly
  if (schema.physics) {
    if (schema.physics.gravity         !== undefined) params.gravity         = schema.physics.gravity;
    if (schema.physics.friction        !== undefined) params.friction        = schema.physics.friction;
    if (schema.physics.collision_force !== undefined) params.collision_force = schema.physics.collision_force;
  }

  // World theme
  if (schema.world_params?.theme) {
    params.theme = schema.world_params.theme;
  }

  return params;
}

// ─── Template loader ──────────────────────────────────────────────────────────

/**
 * Load the template for the resolved game mode.
 * Falls back to runner if template loading fails.
 */
function _loadTemplate(gameMode, schema) {
  // Build an intent string templateSelector can parse
  const intentHint = gameMode === 'arena'
    ? 'arena combat enemy'
    : gameMode === 'platformer'
      ? 'platformer jump platform'
      : 'runner obstacle';

  try {
    return selectTemplate(intentHint);
  } catch (err) {
    console.warn(`[STATE_INIT] Template load failed for mode "${gameMode}", falling back to runner: ${err.message}`);
    return selectTemplate('runner');
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Wrap a buildExecutionSchema() result into the executionData shape
 * that initializeFromExecutionSchema() expects.
 */
function _wrapSchema(built, userId) {
  const now = Date.now();
  return {
    execution_id:    `exec_${now}_${uuidv4().slice(0, 8)}`,
    trace_id:        `trace_${now}`,
    user_id:         userId,
    executionSchema: built.executionSchema
  };
}

function _fail(error) {
  console.error(`[STATE_INIT] ${error}`);
  return { success: false, error };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  initializeFromExecutionSchema,
  initializeFromIntent
};

/**
 * TTG Integration Routes
 * Text-to-Game conversion endpoints using intent-layer
 */

const express = require('express');
const router = express.Router();
const { textToSchema, getSupportedFeatures } = require('../intent-layer');
const { contractValidator } = require('../intent-layer/validators/contractValidator');
const { guard } = require('../intent-layer/validators/safetyGuard');
const { buildEngineJobs } = require('../engine/engine_job_queue');
const { validateTTGInput } = require('../ttg_integration/validator');
const { logIntentReceived, logSchemaGenerated, logJobDispatched, logError } = require('../intent-layer/intentLogger');

/**
 * POST /api/ttg/compile
 * Compile user text to gameplay contract
 */
router.post('/compile', (req, res) => {
  try {
    const { text, userId } = req.body;

    // Log: Intent received
    logIntentReceived(text, userId || 'anonymous');

    // Comprehensive validation
    const inputValidation = validateTTGInput(text);
    if (!inputValidation.valid) {
      logError('validation', new Error(inputValidation.error), userId);
      return res.status(400).json({
        success: false,
        error: inputValidation.error
      });
    }

    console.log(`📝 Compile request: "${inputValidation.sanitized}"`);

    // Use intent-compiler
    const result = textToSchema(inputValidation.sanitized);

    if (!result.success) {
      logError('compilation', new Error(result.explanation), userId);
      return res.status(400).json({
        success: false,
        error: 'Compilation failed',
        explanation: result.explanation,
        validation: result.validation
      });
    }

    // Validate contract before returning
    const contractValidation = contractValidator(result.schema);
    if (!contractValidation.valid) {
      console.error('❌ Contract validation failed:', contractValidation.errors);
      logError('contract_validation', new Error(contractValidation.errors.join(', ')), userId);
      return res.status(400).json({
        success: false,
        error: 'Contract validation failed',
        errors: contractValidation.errors,
        violations: contractValidation.violations
      });
    }

    // Apply safety guard
    const safeSchema = guard(contractValidation.sanitized);

    // Log: Schema generated
    logSchemaGenerated(safeSchema.game_mode, result.intent, userId || 'anonymous');

    res.json({
      success: true,
      intent: result.intent,
      schema: safeSchema,
      validation: result.validation,
      message: `Compiled ${safeSchema.game_mode} game`
    });

  } catch (error) {
    console.error('❌ Compile error:', error);
    logError('compile_exception', error, req.body.userId);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/ttg/start-game
 * REMOVED - Day 9: All execution must go through /core/execute
 * This route bypassed security enforcement layer
 */

/**
 * GET /api/intent/features
 * Get supported features
 */
router.get('/features', (req, res) => {
  res.json({
    success: true,
    features: getSupportedFeatures()
  });
});

/**
 * GET /api/intent/engine-capabilities
 * Returns supported entities, components, and job types the engine can handle.
 * Use this to know what gameplay assets are available before dispatching a job.
 */
router.get('/engine-capabilities', (req, res) => {
  const { getEngineCapabilities } = require('../game-templates/templateValidator');
  res.json(getEngineCapabilities());
});

/**
 * GET /api/intent/gameplay-assets
 * Returns all game templates with their entities, components, jobs, and default parameters.
 */
router.get('/gameplay-assets', (req, res) => {
  const fs = require('fs');
  const path = require('path');
  const TEMPLATES_DIR = path.join(__dirname, '../game-templates/templates');
  const TEMPLATE_KEYS = ['runner', 'platformer', 'arena'];
  const TEMPLATE_FILES = {
    runner: 'runner_template.json',
    platformer: 'platformer_template.json',
    arena: 'arena_template.json',
  };

  const assets = {};
  for (const key of TEMPLATE_KEYS) {
    try {
      assets[key] = JSON.parse(fs.readFileSync(path.join(TEMPLATES_DIR, TEMPLATE_FILES[key]), 'utf8'));
    } catch (e) {
      assets[key] = null;
    }
  }

  res.json({ success: true, gameplay_assets: assets });
});

/**
 * GET /api/intent/runtime-consumption
 * Returns estimated runtime resource consumption per game mode.
 */
router.get('/runtime-consumption', (req, res) => {
  const CONSUMPTION_MAP = {
    runner: {
      game_mode: 'runner',
      jobs_dispatched: ['BUILD_SCENE', 'SPAWN_PLAYER', 'SPAWN_OBSTACLE_SYSTEM', 'START_LOOP'],
      job_count: 4,
      entities_spawned: ['player', 'ground', 'obstacle_spawner'],
      estimated_tick_cost_ms: 12,
      memory_estimate_mb: 32,
      notes: 'Lightweight — single lane, no AI agents',
    },
    platformer: {
      game_mode: 'platformer',
      jobs_dispatched: ['BUILD_SCENE', 'SPAWN_PLAYER', 'SPAWN_PLATFORMS', 'SPAWN_PICKUPS', 'START_LOOP'],
      job_count: 5,
      entities_spawned: ['player', 'platform', 'pickup', 'checkpoint'],
      estimated_tick_cost_ms: 18,
      memory_estimate_mb: 48,
      notes: 'Medium — platform physics + pickup triggers',
    },
    arena: {
      game_mode: 'arena',
      jobs_dispatched: ['BUILD_SCENE', 'SPAWN_PLAYER', 'SPAWN_ENEMIES', 'SPAWN_PICKUPS', 'START_LOOP'],
      job_count: 5,
      entities_spawned: ['player', 'enemy', 'pickup', 'spawner'],
      estimated_tick_cost_ms: 35,
      memory_estimate_mb: 96,
      notes: 'Heavy — AI controllers + collision-heavy combat loop',
    },
  };

  const { game_mode } = req.query;
  if (game_mode) {
    if (!CONSUMPTION_MAP[game_mode]) {
      return res.status(400).json({ success: false, error: `Unknown game_mode: ${game_mode}. Valid: runner, platformer, arena` });
    }
    return res.json({ success: true, consumption: CONSUMPTION_MAP[game_mode] });
  }

  res.json({ success: true, consumption: CONSUMPTION_MAP });
});

module.exports = router;

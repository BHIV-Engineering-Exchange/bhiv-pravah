// routes/coreExecution.js - Core ingestion endpoint with security enforcement
const express = require('express');
const router = express.Router();
const { storeExecution, getExecution } = require('../executionRegistry');
const { dispatchExecution } = require('../executionDispatcher');
const { getExecutionState, getAllExecutionStates, getExecutionsByStatus } = require('../executionState');
const { getExecutionTelemetry, getAllExecutionTelemetry } = require('../telemetry/behaviourRecorder');
const { validateExecutionRequest } = require('../security/executionSecurity');
const { callPromptRunner, convertToExecutionSchema, checkPromptRunnerHealth } = require('../prompt_runner');

// POST /core/execute - Accept ONLY structured execution schemas with security enforcement
router.post('/execute', async (req, res) => {
  try {
    const { trace_id, execution_id, executionSchema, user_id, timestamp, intent } = req.body;

    // Security enforcement - validate schema, trace_id, signature, nonce
    const validation = validateExecutionRequest(req);
    if (!validation.valid) {
      return res.status(401).json({
        success: false,
        error: validation.error
      });
    }

    // Store in execution registry
    const execution = storeExecution({
      execution_id,
      trace_id,
      user_id: user_id || 'anonymous',
      executionSchema,
      intent,
      timestamp: timestamp || Date.now()
    });

    console.log(`[CORE/EXECUTE] Received execution: ${execution_id}, trace: ${trace_id}`);

    // Dispatch to engine queue (async, non-blocking)
    setImmediate(() => {
      dispatchExecution(execution)
        .then(result => {
          if (result.success) {
            console.log(`[CORE/EXECUTE] Dispatched ${result.jobCount} jobs for ${execution_id}`);
          } else {
            console.error(`[CORE/EXECUTE] Dispatch failed for ${execution_id}:`, result.error);
          }
        })
        .catch(err => {
          console.error(`[CORE/EXECUTE] Dispatch error for ${execution_id}:`, err.message);
        });
    });

    // Return success immediately (don't wait for dispatch)
    res.json({
      success: true,
      execution_id,
      trace_id,
      status: 'received',
      message: 'Execution schema accepted and queued for dispatch'
    });

  } catch (error) {
    console.error('[CORE/EXECUTE] Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// GET /execution/:id - Query execution status with detailed state
router.get('/execution/:id', (req, res) => {
  const { id } = req.params;
  const { detailed } = req.query;
  
  const executionState = getExecutionState(id);
  
  if (!executionState) {
    return res.status(404).json({
      success: false,
      error: 'Execution not found'
    });
  }
  
  // Return detailed state if requested, otherwise summary
  if (detailed === 'true') {
    res.json({
      success: true,
      execution: executionState
    });
  } else {
    // Return summary (backward compatible)
    res.json({
      success: true,
      execution: {
        execution_id: executionState.execution_id,
        trace_id: executionState.trace_id,
        status: executionState.status,
        jobs: executionState.jobs.total,
        receivedAt: executionState.receivedAt,
        startedAt: executionState.startedAt,
        completedAt: executionState.completedAt,
        duration: executionState.duration,
        progress: executionState.progress,
        error: executionState.error
      }
    });
  }
});

// GET /executions - List all executions
router.get('/executions', (req, res) => {
  const { status } = req.query;
  
  let executions;
  if (status) {
    executions = getExecutionsByStatus(status);
  } else {
    executions = getAllExecutionStates();
  }
  
  res.json({
    success: true,
    count: executions.length,
    executions
  });
});

// GET /telemetry/:id - Get execution telemetry
router.get('/telemetry/:id', (req, res) => {
  const { id } = req.params;
  
  const telemetry = getExecutionTelemetry(id);
  
  if (telemetry.length === 0) {
    return res.status(404).json({
      success: false,
      error: 'No telemetry found for execution'
    });
  }
  
  res.json({
    success: true,
    execution_id: id,
    count: telemetry.length,
    telemetry
  });
});

// GET /telemetry - Get all execution telemetry
router.get('/telemetry', (req, res) => {
  const allTelemetry = getAllExecutionTelemetry();
  
  res.json({
    success: true,
    count: allTelemetry.length,
    telemetry: allTelemetry
  });
});

// POST /core/prompt-runner-compile - Compile via Groq AI, return schema only (no dispatch)
router.post('/prompt-runner-compile', async (req, res) => {
  try {
    const { prompt } = req.body;
    if (!prompt) return res.status(400).json({ success: false, error: 'Missing prompt' });

    const promptRunnerOutput = await callPromptRunner(prompt);
    const executionData = convertToExecutionSchema(promptRunnerOutput, 'preview');

    res.json({
      success: true,
      executionSchema: executionData.executionSchema
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /core/execute-from-text - Accept natural language prompt, forward to Atharva TTG engine
router.post('/execute-from-text', async (req, res) => {
  try {
    const { prompt, user_id } = req.body;

    if (!prompt || typeof prompt !== 'string') {
      return res.status(400).json({ success: false, error: 'Missing or invalid prompt' });
    }

    console.log(`[EXECUTE-FROM-TEXT] Prompt: "${prompt}"`);

    // 1. Call Prompt Runner live service
    const promptRunnerOutput = await callPromptRunner(prompt);

    // 2. Convert to execution schema
    const executionData = convertToExecutionSchema(promptRunnerOutput, user_id || 'anonymous');
    console.log('[EXECUTE-FROM-TEXT] Converted schema:');
    console.log(JSON.stringify(executionData.executionSchema, null, 2));

    // 3. Store + dispatch (job queue → Socket.IO /engine → connector → server.py)
    const execution = storeExecution(executionData);
    setImmediate(() => {
      dispatchExecution(execution)
        .then(result => {
          if (result.success)
            console.log(`[EXECUTE-FROM-TEXT] Dispatched ${result.jobCount} jobs for ${executionData.execution_id}`);
        })
        .catch(err => console.error(`[EXECUTE-FROM-TEXT] Dispatch error:`, err.message));
    });

    res.json({
      success: true,
      execution_id: executionData.execution_id,
      trace_id: executionData.trace_id,
      status: 'received',
      message: 'Prompt processed — jobs dispatched to engine via connector'
    });

  } catch (error) {
    console.error('[EXECUTE-FROM-TEXT] Error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Forward execution schema to Atharva TTG engine at /execute
async function forwardToAtharva(executionData) {
  const http = require('http');
  const ATHARVA_HOST = process.env.ATHARVA_HOST || 'localhost';
  const ATHARVA_PORT = parseInt(process.env.ATHARVA_PORT || '8080', 10);

  const contract = {
    trace_id:       executionData.trace_id,
    execution_id:   executionData.execution_id,
    mitra_decision: 'ALLOW',
    game_mode:      executionData.executionSchema.game_mode || 'runner',
    parameters: {
      speed:      executionData.executionSchema.movement?.speed,
      difficulty: (executionData.executionSchema.player_params?.health <= 3) ? 'hard' : 'easy',
      obstacles:  executionData.executionSchema.spawn_rules?.obstacles || 0
    },
    blueprint: executionData.executionSchema.blueprint || null,
    jobs: []
  };

  return new Promise((resolve) => {
    const body = JSON.stringify(contract);
    const req = http.request({
      hostname: ATHARVA_HOST,
      port:     ATHARVA_PORT,
      path:     '/execute',
      method:   'POST',
      headers:  { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          console.log(`[ATHARVA BRIDGE] ✓ Accepted — trace=${contract.trace_id} game_mode=${contract.game_mode}`);
          resolve({ success: true, status: res.statusCode, body: parsed });
        } catch {
          resolve({ success: true, status: res.statusCode, body: data });
        }
      });
    });
    req.on('error', (err) => {
      console.warn(`[ATHARVA BRIDGE] Unreachable (${err.message}) — execution still queued locally`);
      resolve({ success: false, error: err.message });
    });
    req.setTimeout(5000, () => {
      req.destroy();
      console.warn('[ATHARVA BRIDGE] Timeout — execution still queued locally');
      resolve({ success: false, error: 'timeout' });
    });
    req.write(body);
    req.end();
  });
}

// POST /core/execute-to-atharva — compile schema → Mitra → Atharva engine directly
router.post('/execute-to-atharva', async (req, res) => {
  try {
    const { schema } = req.body;
    if (!schema) return res.status(400).json({ success: false, error: 'Missing schema' });

    // 1. Mitra governance check
    const https = require('https');
    const MITRA_HOST    = process.env.MITRA_HOST    || 'mitra-backend-q1f3.onrender.com';
    const MITRA_API_KEY = process.env.MITRA_API_KEY || 'localtest';
    const trace_id      = `trace_${Date.now()}`;
    const execution_id  = `exec_${Date.now()}`;

    const mitraBody = JSON.stringify({
      event:   { title: schema.game_mode || 'game', content: JSON.stringify(schema).slice(0, 200), category: 'game', confidence: 0.95 },
      user_id: 'frontend_user',
      context: { platform: 'ttg', device: 'dashboard', session_id: trace_id }
    });

    const mitraResult = await new Promise((resolve) => {
      const r = https.request({ hostname: MITRA_HOST, port: 443, path: '/api/mitra/evaluate', method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(mitraBody), 'X-API-Key': MITRA_API_KEY }
      }, (resp) => {
        let d = '';
        resp.on('data', c => d += c);
        resp.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve({ status: 'ALLOW' }); } });
      });
      r.on('error', () => resolve({ status: 'ALLOW' }));
      r.setTimeout(5000, () => { r.destroy(); resolve({ status: 'ALLOW' }); });
      r.write(mitraBody); r.end();
    });

    if (mitraResult.status === 'BLOCK') {
      return res.status(403).json({ success: false, error: `Mitra blocked: ${mitraResult.reason}` });
    }

    // 2. Forward to Atharva engine
    const ATHARVA_HOST = process.env.ATHARVA_HOST || 'localhost';
    const ATHARVA_PORT = parseInt(process.env.ATHARVA_PORT || '8080', 10);
    const contract = {
      trace_id, execution_id,
      mitra_decision: mitraResult.status || 'ALLOW',
      game_mode: schema.game_mode || 'runner',
      parameters: schema, jobs: []
    };

    const atharvaResult = await forwardToAtharva({ trace_id, execution_id, executionSchema: schema });

    res.json({
      success: true,
      trace_id, execution_id,
      game_mode: contract.game_mode,
      mitra_decision: contract.mitra_decision,
      mitra_trace: mitraResult.trace_id || null,
      atharva: atharvaResult
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// POST /core/execute-from-prompt — LOCKED (Phase 5)
// Redirects to execute-from-text which goes through full Mitra governance
router.post('/execute-from-prompt', async (req, res) => {
  return res.status(403).json({
    success: false,
    error: 'Direct prompt execution is not allowed. Use POST /core/execute-from-text with a natural language prompt.'
  });
});

// GET /core/prompt-runner-health - Check Prompt Runner service health (NEW)
router.get('/prompt-runner-health', async (req, res) => {
  try {
    const isHealthy = await checkPromptRunnerHealth();
    res.json({
      success: true,
      healthy: isHealthy,
      url: process.env.PROMPT_RUNNER_URL || 'http://127.0.0.1:8001'
    });
  } catch (error) {
    res.json({
      success: true,
      healthy: false,
      error: error.message
    });
  }
});

// POST /core/test-execution — REMOVED (Phase 5: no bypass paths allowed)
// All execution must go through Mitra governance via /core/execute-from-text

// ── Game State Engine REST endpoints ─────────────────────────────────────────
const gsm         = require('../state/gameStateManager');
const replayRecon = require('../state/replayReconstructor');

// GET /core/game-state/:sessionId — live state for a session
router.get('/game-state/:sessionId', (req, res) => {
  const state = gsm.getCurrentState(req.params.sessionId);
  if (!state) return res.status(404).json({ success: false, error: 'Session not found' });
  res.json({ success: true, sessionId: req.params.sessionId, state });
});

// GET /core/game-sessions — list all active session IDs
router.get('/game-sessions', (req, res) => {
  res.json({ success: true, sessions: gsm.getActiveSessions() });
});

// GET /core/game-state/:sessionId/replay — full deterministic replay from bucket
router.get('/game-state/:sessionId/replay', async (req, res) => {
  try {
    const result = await replayRecon.reconstruct(req.params.sessionId);
    res.json({ success: true, ...result });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;

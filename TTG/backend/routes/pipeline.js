'use strict';

/**
 * routes/pipeline.js
 *
 * Service exposure for the maritime governance pipeline.
 * Pure orchestration — no business logic lives here.
 *
 * POST /pipeline/run
 *   → input : raw vessel signal
 *   → output: PipelineResult
 *
 * GET  /pipeline/result/:trace_id
 *   → returns all 5 artifacts for a completed execution
 *
 * POST /pipeline/replay/:trace_id
 *   → runs replayEngine.replay() and returns ReplayResult
 *
 * GET  /pipeline/health
 *   → service status
 */

const express      = require('express');
const fs           = require('fs').promises;
const path         = require('path');
const router       = express.Router();
const { run }      = require('../domain-adapters/maritime/pipeline');
const { replay }   = require('../domain-adapters/maritime/replayEngine');
const { query, VALID_STAGES } = require('../domain-adapters/maritime/insightBridge');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

// ─── POST /pipeline/run ───────────────────────────────────────────────────────

router.post('/run', async (req, res) => {
  const { vessel_id, lat, lon, speed, heading, status, trace_id, execution_id } = req.body;

  if (!vessel_id || lat === undefined || lon === undefined ||
      speed === undefined || heading === undefined) {
    return res.status(400).json({
      success: false,
      error:   'Missing required fields: vessel_id, lat, lon, speed, heading'
    });
  }

  const vesselInput = { vessel_id, lat, lon, speed, heading, status: status || 'moving' };
  const opts        = {};
  if (trace_id)     opts.trace_id     = trace_id;
  if (execution_id) opts.execution_id = execution_id;

  let result;
  try {
    result = await run(vesselInput, opts);
  } catch (err) {
    console.error('[PIPELINE/RUN] ❌ Unhandled pipeline crash:', err.message);
    return res.status(500).json({ success: false, error: `Pipeline crashed: ${err.message}` });
  }

  const status_code = result.success ? 200 : 422;
  return res.status(status_code).json(result);
});

// ─── GET /pipeline/result/:trace_id ──────────────────────────────────────────

router.get('/result/:trace_id', async (req, res) => {
  const { trace_id } = req.params;

  const ARTIFACT_KEYS = ['schema', 'decision', 'events', 'state', 'log'];
  const EXT           = { schema: '.json', decision: '.json', events: '.jsonl', state: '.json', log: '.jsonl' };

  const artifacts = {};
  const missing   = [];

  try {
    await Promise.all(
      ARTIFACT_KEYS.map(async (key) => {
        const filepath = path.join(BUCKET_DIR, `execution_${trace_id}_${key}${EXT[key]}`);
        try {
          const raw = await fs.readFile(filepath, 'utf8');
          artifacts[key] = EXT[key] === '.jsonl'
            ? raw.split('\n').filter(Boolean).map(l => JSON.parse(l))
            : JSON.parse(raw);
        } catch (err) {
          if (err.code === 'ENOENT') {
            missing.push(key);
          } else {
            throw new Error(`Artifact "${key}" exists but could not be read: ${err.message}`);
          }
        }
      })
    );
  } catch (err) {
    console.error(`[PIPELINE/RESULT] ❌ ${err.message}`);
    return res.status(500).json({ success: false, error: err.message });
  }

  if (missing.length === ARTIFACT_KEYS.length) {
    return res.status(404).json({
      success: false,
      error:   `No artifacts found for trace_id: ${trace_id}`
    });
  }

  return res.status(200).json({
    success:  true,
    trace_id,
    missing:  missing.length > 0 ? missing : undefined,
    artifacts
  });
});

// ─── POST /pipeline/replay/:trace_id ─────────────────────────────────────────

router.post('/replay/:trace_id', async (req, res) => {
  const { trace_id } = req.params;

  const result      = await replay(trace_id);
  const status_code = result.success ? 200 : 422;

  return res.status(status_code).json(result);
});

// ─── GET /pipeline/health ─────────────────────────────────────────────────────

router.get('/health', async (req, res) => {
  let bucket_accessible = false;
  let artifact_count    = 0;

  try {
    const files       = await fs.readdir(BUCKET_DIR);
    bucket_accessible = true;
    artifact_count    = files.filter(f => f.startsWith('execution_')).length;
  } catch {
    // bucket dir missing — not fatal, report it
  }

  return res.status(200).json({
    success:           true,
    service:           'pipeline',
    status:            'ok',
    bucket_accessible,
    artifact_count,
    checked_at:        Date.now()
  });
});

// ─── GET /pipeline/telemetry/:trace_id ──────────────────────────────────────

router.get('/telemetry/:trace_id', (req, res) => {
  const { trace_id } = req.params;
  const { stage }    = req.query;   // optional: ?stage=decision_received

  // Validate stage param before hitting the module
  if (stage !== undefined && !VALID_STAGES.has(stage)) {
    return res.status(400).json({
      success: false,
      error:   `Unknown stage: "${stage}". Valid stages: ${[...VALID_STAGES].join(', ')}`
    });
  }

  const result = query(trace_id, stage ? { stage } : {});

  if (result.error && !result.found) {
    return res.status(400).json({ success: false, error: result.error });
  }

  if (!result.found) {
    return res.status(404).json({
      success: false,
      error:   `No telemetry found for trace_id: ${trace_id}`
    });
  }

  if (!result.trace_consistent) {
    return res.status(500).json({
      success: false,
      error:   `Trace consistency violation detected for trace_id: ${trace_id}`
    });
  }

  return res.status(200).json({
    success:          true,
    trace_id,
    source:           result.source,
    total:            result.total,
    filtered:         result.filtered,
    stage_filter:     stage || null,
    stages_present:   result.stages_present,
    trace_consistent: result.trace_consistent,
    events:           result.events
  });
});

module.exports = router;

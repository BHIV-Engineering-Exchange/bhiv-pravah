'use strict';

const express = require('express');
const router  = express.Router();
const http    = require('http');
const WebSocket = require('ws');

const ATHARVA_HOST = process.env.ATHARVA_HOST || 'localhost';
const ATHARVA_PORT = parseInt(process.env.ATHARVA_PORT || '8080', 10);
const MITRA_HOST   = process.env.MITRA_HOST   || 'localhost';
const MITRA_PORT   = parseInt(process.env.MITRA_PORT   || '8000', 10);
const MITRA_KEY    = process.env.MITRA_API_KEY || 'mitra-local-dev-key-2024';

function mapGameMode(game_mode) {
  const map = {
    runner: 'runner', sidescroller: 'sidescroller',
    platformer: 'sidescroller', arena: 'arena',
    open_scene: 'arena', default: 'runner'
  };
  return map[game_mode] || 'runner';
}

// Send Q key press over WS to exit current game, then wait for menu
function stopCurrentGame() {
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://${ATHARVA_HOST}:${ATHARVA_PORT}/ws`);
    const cleanup = (delay = 0) => setTimeout(() => { try { ws.close(); } catch {} resolve(); }, delay);

    ws.on('error', () => resolve()); // not connected — nothing to stop

    ws.on('open', () => {
      // Send Q press to exit current game
      ws.send(JSON.stringify({ event_type: 'input', data: { key: 'q', action: 'press' } }));
      console.log('[ATHARVA BRIDGE] Sent Q key — stopping current game');
      cleanup(1200); // wait 1.2s for game to exit and menu to reset
    });

    setTimeout(() => { try { ws.close(); } catch {} resolve(); }, 3000); // hard timeout
  });
}

function httpPost(host, port, path, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({
      hostname: host, port, path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', err => reject(new Error(`${host}:${port} unreachable — ${err.message}`)));
    req.setTimeout(5000, () => { req.destroy(); reject(new Error(`${host}:${port} timeout`)); });
    req.write(data);
    req.end();
  });
}

function httpGet(host, port, path) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: host, port, path, method: 'GET' }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', err => reject(new Error(err.message)));
    req.setTimeout(3000, () => { req.destroy(); reject(new Error('timeout')); });
    req.end();
  });
}

// POST /core/execute-to-atharva
router.post('/execute-to-atharva', async (req, res) => {
  try {
    const { schema, trace_id, execution_id } = req.body;
    if (!schema) return res.status(400).json({ success: false, error: 'Missing schema' });

    const tid = trace_id || `tantra-${Date.now()}`;
    const eid = execution_id || `exec-${tid}`;
    const game_mode = mapGameMode(schema.game_mode);

    // ── Step 1: Mitra check ───────────────────────────────────────────────
    let mitra_decision = 'ALLOW';
    let mitra_trace    = null;
    try {
      const mitra_res = await httpPost(
        MITRA_HOST, MITRA_PORT, '/api/mitra/evaluate',
        {
          event:   { title: `Game: ${game_mode}`, content: `prompt schema for ${game_mode} game`, category: 'game' },
          user_id: 'rudra_node',
          context: { platform: 'tantra', device: 'api' }
        },
        { 'X-API-Key': MITRA_KEY }
      );

      if (mitra_res.status === 200) {
        mitra_decision = mitra_res.body.status;   // ALLOW | FLAG | BLOCK
        mitra_trace    = mitra_res.body.trace_id;
        console.log(`[ATHARVA BRIDGE] Mitra decision: ${mitra_decision} | mitra_trace=${mitra_trace}`);
      } else {
        console.warn(`[ATHARVA BRIDGE] Mitra returned ${mitra_res.status} — defaulting to ALLOW`);
      }
    } catch (mitraErr) {
      console.warn(`[ATHARVA BRIDGE] Mitra unreachable (${mitraErr.message}) — defaulting to ALLOW`);
    }

    if (mitra_decision === 'BLOCK') {
      return res.status(403).json({
        success: false,
        mitra_decision,
        mitra_trace,
        error: 'Mitra blocked this execution'
      });
    }

    // ── Step 2: Stop current game if running, then forward to Atharva ───────────────────────────────────────
    // Check if a game is currently running
    let atharva_status;
    try {
      atharva_status = (await httpGet(ATHARVA_HOST, ATHARVA_PORT, '/health')).body;
    } catch { atharva_status = null; }

    if (atharva_status?.game) {
      console.log(`[ATHARVA BRIDGE] Game "${atharva_status.game}" running — sending Q to stop it`);
      await stopCurrentGame();
    }
    const atharva_contract = {
      trace_id:       tid,
      execution_id:   eid,
      mitra_decision: 'ALLOW',
      game_mode,
      parameters: {
        speed:      schema.movement?.speed,
        difficulty: schema.player_params?.health <= 3 ? 'hard' : 'easy',
        obstacles:  schema.spawn_rules?.obstacles || 0
      },
      jobs: []
    };

    console.log(`[ATHARVA BRIDGE] Forwarding — trace=${tid} game_mode=${game_mode} mitra=${mitra_decision}`);

    const result = await httpPost(ATHARVA_HOST, ATHARVA_PORT, '/execute', atharva_contract);

    if (result.status === 200) {
      console.log(`[ATHARVA BRIDGE] ✓ Atharva accepted — trace=${tid}`);
      return res.json({
        success: true,
        trace_id: tid,
        execution_id: eid,
        game_mode,
        mitra_decision,
        mitra_trace,
        atharva: result.body,
        message: `Game launched — mode: ${game_mode} | mitra: ${mitra_decision}`
      });
    } else {
      return res.status(502).json({
        success: false,
        error: `Atharva rejected: ${JSON.stringify(result.body)}`
      });
    }

  } catch (err) {
    console.error('[ATHARVA BRIDGE]', err.message);
    return res.status(503).json({ success: false, error: err.message });
  }
});

// GET /core/atharva-health
router.get('/atharva-health', async (req, res) => {
  const results = { atharva: null, mitra: null, prompt_runner: null };

  try { results.atharva = (await httpGet(ATHARVA_HOST, ATHARVA_PORT, '/health')).body; }
  catch (e) { results.atharva = { reachable: false, error: e.message }; }

  try { results.mitra = (await httpGet(MITRA_HOST, MITRA_PORT, '/health')).body; }
  catch (e) { results.mitra = { reachable: false, error: e.message }; }

  try { results.prompt_runner = (await httpGet('localhost', 8001, '/health')).body; }
  catch (e) { results.prompt_runner = { reachable: false, error: e.message }; }

  res.json(results);
});

module.exports = router;

// Map your schema's game_mode to Atharva's valid game_modes
function mapGameMode(game_mode) {
  const map = {
    runner:       'runner',
    sidescroller: 'sidescroller',
    platformer:   'sidescroller',
    arena:        'arena',
    open_scene:   'arena',
    default:      'runner'
  };
  return map[game_mode] || 'runner';
}

// POST contract to Atharva's server
function postToAtharva(contract) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(contract);
    const options = {
      hostname: ATHARVA_HOST,
      port:     ATHARVA_PORT,
      path:     '/execute',
      method:   'POST',
      headers:  {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', (err) => {
      reject(new Error(`Cannot reach Atharva server at ${ATHARVA_HOST}:${ATHARVA_PORT} — ${err.message}. Is it running?`));
    });

    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Atharva server timeout after 5s'));
    });

    req.write(body);
    req.end();
  });
}

// POST /core/execute-to-atharva
router.post('/execute-to-atharva', async (req, res) => {
  try {
    const { schema, trace_id, execution_id } = req.body;

    if (!schema) {
      return res.status(400).json({ success: false, error: 'Missing schema in request body' });
    }

    const tid = trace_id || `tantra-${Date.now()}`;
    const eid = execution_id || `exec-${tid}`;

    // Build Atharva's contract from your schema
    const atharva_contract = {
      trace_id:       tid,
      execution_id:   eid,
      mitra_decision: 'ALLOW',
      game_mode:      mapGameMode(schema.game_mode),
      parameters:     {
        speed:      schema.movement?.speed,
        difficulty: schema.player_params?.health <= 3 ? 'hard' : 'easy',
        obstacles:  schema.spawn_rules?.obstacles || 0
      },
      jobs: []
    };

    console.log(`[ATHARVA BRIDGE] Forwarding to Atharva — trace=${tid} game_mode=${atharva_contract.game_mode}`);

    const result = await postToAtharva(atharva_contract);

    if (result.status === 200) {
      console.log(`[ATHARVA BRIDGE] ✓ Accepted by Atharva — trace=${tid}`);
      return res.json({
        success:      true,
        trace_id:     tid,
        execution_id: eid,
        game_mode:    atharva_contract.game_mode,
        atharva:      result.body,
        message:      `Game launched on Atharva renderer — game_mode: ${atharva_contract.game_mode}`
      });
    } else {
      console.error(`[ATHARVA BRIDGE] ✗ Rejected by Atharva — ${result.status}:`, result.body);
      return res.status(502).json({
        success: false,
        error:   `Atharva rejected contract: ${JSON.stringify(result.body)}`
      });
    }

  } catch (err) {
    console.error('[ATHARVA BRIDGE] Error:', err.message);
    return res.status(503).json({
      success: false,
      error:   err.message
    });
  }
});

// GET /core/atharva-health — check if Atharva's server is reachable
router.get('/atharva-health', (req, res) => {
  const options = {
    hostname: ATHARVA_HOST,
    port:     ATHARVA_PORT,
    path:     '/health',
    method:   'GET'
  };

  const req2 = http.request(options, (r) => {
    let data = '';
    r.on('data', chunk => data += chunk);
    r.on('end', () => {
      try {
        res.json({ reachable: true, status: r.statusCode, atharva: JSON.parse(data) });
      } catch {
        res.json({ reachable: true, status: r.statusCode });
      }
    });
  });

  req2.on('error', () => {
    res.json({ reachable: false, error: `Atharva not running at ${ATHARVA_HOST}:${ATHARVA_PORT}` });
  });

  req2.setTimeout(3000, () => { req2.destroy(); res.json({ reachable: false, error: 'timeout' }); });
  req2.end();
});

module.exports = router;

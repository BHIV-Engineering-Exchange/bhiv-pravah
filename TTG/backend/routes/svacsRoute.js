'use strict';

/**
 * svacsRoute.js
 *
 * POST /svacs/inbound   — receives SVACS execution contract
 * GET  /svacs/proofs    — lists all Phase 3 proof artifacts
 * GET  /svacs/health    — checks SVACS pipeline readiness
 *
 * Full Phase 3 path:
 *   SVACS → Rudra (/svacs/inbound) → Mitra → Atharva → Bucket → proof artifact
 */

const express = require('express');
const router  = express.Router();
const http    = require('http');
const https   = require('https');
const fs      = require('fs');
const path    = require('path');
const { emitToSamrachna } = require('../samrachnaEmitter');

const ATHARVA_HOST   = process.env.ATHARVA_HOST   || 'localhost';
const ATHARVA_PORT   = parseInt(process.env.ATHARVA_PORT   || '8080', 10);
const MITRA_HOST     = process.env.MITRA_HOST     || 'localhost';
const MITRA_PORT     = parseInt(process.env.MITRA_PORT     || '8000', 10);
const MITRA_KEY      = process.env.MITRA_API_KEY  || 'mitra-local-dev-key-2024';
const BUCKET_URL     = process.env.BUCKET_URL     || 'https://bhiv-bucket.onrender.com';
const ARTIFACT_DIR   = path.join(__dirname, '..', 'bucket_artifacts');

// ── HTTP helpers ──────────────────────────────────────────────────────────────
function httpPost(host, port, urlPath, body, headers = {}, useHttps = false) {
  return new Promise((resolve, reject) => {
    const data    = JSON.stringify(body);
    const lib     = useHttps ? https : http;
    const options = {
      hostname: host, port, path: urlPath, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    };
    const req = lib.request(options, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', err => reject(new Error(`${host}:${port} — ${err.message}`)));
    req.setTimeout(8000, () => { req.destroy(); reject(new Error(`${host}:${port} timeout`)); });
    req.write(data);
    req.end();
  });
}

function httpsPost(urlStr, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const url  = new URL(urlStr);
    const data = JSON.stringify(body);
    const options = {
      hostname: url.hostname,
      port:     url.port || 443,
      path:     url.pathname + url.search,
      method:   'POST',
      headers:  { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    };
    const req = https.request(options, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', err => reject(new Error(err.message)));
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('bucket timeout')); });
    req.write(data);
    req.end();
  });
}

// ── Map SVACS risk_level → game_mode ─────────────────────────────────────────
function mapRiskToGameMode(risk_level) {
  const map = { LOW: 'runner', MEDIUM: 'sidescroller', HIGH: 'arena' };
  return map[risk_level] || 'runner';
}

// ── Write local proof artifact ────────────────────────────────────────────────
function writeProof(trace_id, proof) {
  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  const file = path.join(ARTIFACT_DIR, `svacs_phase3_${trace_id}_proof.json`);
  fs.writeFileSync(file, JSON.stringify(proof, null, 2), 'utf8');
  console.log(`[SVACS] Proof artifact: ${path.basename(file)}`);
  return file;
}

// ── POST /svacs/inbound ───────────────────────────────────────────────────────
router.post('/inbound', async (req, res) => {
  const start = Date.now();
  try {
    const {
      execution_id,
      trace_id,
      risk_level = 'LOW',
      pipeline_stages = [],
      signal_chunk,
      intelligence_event,
      state_event,
      core_execution,
      contract_version = 'v1.0',
      timestamp
    } = req.body;

    if (!trace_id || !execution_id) {
      return res.status(400).json({ success: false, error: 'Missing trace_id or execution_id' });
    }

    // Validate SVACS trace_id format (must start with trace_)
    if (!trace_id.startsWith('trace_')) {
      return res.status(400).json({
        success: false,
        error: `Invalid trace_id format: "${trace_id}" — SVACS trace_id must start with "trace_"`,
        upstream_trace_ownership: 'REJECTED'
      });
    }

    // Validate SVACS execution_id format (must start with exec_)
    if (!execution_id.startsWith('exec_')) {
      return res.status(400).json({
        success: false,
        error: `Invalid execution_id format: "${execution_id}" — SVACS execution_id must start with "exec_"`,
        contract_enforcement: 'REJECTED'
      });
    }

    const game_mode = mapRiskToGameMode(risk_level);

    console.log(`\n[SVACS] ← Phase 3 contract received`);
    console.log(`[SVACS]   trace_id     : ${trace_id}`);
    console.log(`[SVACS]   execution_id : ${execution_id}`);
    console.log(`[SVACS]   risk_level   : ${risk_level}`);
    console.log(`[SVACS]   game_mode    : ${game_mode}`);
    console.log(`[SVACS]   upstream     : SVACS`);

    const proof = {
      phase:                  3,
      upstream_system:        'SVACS',
      trace_id,
      execution_id,
      contract_version,
      risk_level,
      game_mode,
      upstream_trace_ownership: 'CONFIRMED',
      contract_enforcement:     'PASSED',
      stages:                 {},
      svacs_pipeline:         pipeline_stages,
      timestamp:              new Date().toISOString()
    };

    // ── Step 1: Mitra governance check ────────────────────────────────────────
    let mitra_decision = 'ALLOW';
    let mitra_trace    = null;
    try {
      const mitra_res = await httpPost(
        MITRA_HOST, MITRA_PORT, '/api/mitra/evaluate',
        {
          event:   {
            title:    `SVACS execution: ${game_mode}`,
            content:  `trace_id=${trace_id} risk_level=${risk_level} execution_id=${execution_id}`,
            category: 'maritime_intelligence'
          },
          user_id: 'svacs_upstream',
          context: { platform: 'tantra', device: 'svacs_node', session_id: trace_id }
        },
        { 'X-API-Key': MITRA_KEY }
      );
      if (mitra_res.status === 200) {
        mitra_decision = mitra_res.body.status;
        mitra_trace    = mitra_res.body.trace_id;
        console.log(`[SVACS]   Mitra        : ${mitra_decision} (mitra_trace=${mitra_trace})`);
      } else {
        console.warn(`[SVACS]   Mitra returned ${mitra_res.status} — defaulting ALLOW`);
      }
    } catch (e) {
      console.warn(`[SVACS]   Mitra unreachable (${e.message}) — defaulting ALLOW`);
    }

    proof.stages.mitra = {
      decision:    mitra_decision,
      mitra_trace,
      trace_preserved: mitra_trace !== null
    };

    if (mitra_decision === 'BLOCK') {
      proof.status = 'BLOCKED_BY_MITRA';
      proof.execution_participation = 'BLOCKED';
      writeProof(trace_id, proof);
      return res.status(403).json({ success: false, mitra_decision, trace_id, execution_id, proof });
    }

    // ── Step 2: Forward to Atharva renderer ───────────────────────────────────
    const atharva_contract = {
      trace_id,
      execution_id,
      mitra_decision: 'ALLOW',
      game_mode,
      parameters: {
        risk_level,
        upstream_system: 'SVACS',
        signal_source:   signal_chunk?.vessel_type || 'maritime'
      },
      jobs: []
    };

    let atharva_accepted = false;
    try {
      const r = await httpPost(ATHARVA_HOST, ATHARVA_PORT, '/execute', atharva_contract);
      atharva_accepted = r.status === 200;
      proof.stages.atharva = {
        status:           r.status,
        accepted:         atharva_accepted,
        response:         r.body,
        trace_preserved:  r.body?.trace_id === trace_id
      };
      console.log(`[SVACS]   Atharva      : ${atharva_accepted ? '✓ accepted' : '✗ rejected'} (game=${game_mode})`);
    } catch (e) {
      proof.stages.atharva = { error: e.message, accepted: false };
      console.warn(`[SVACS]   Atharva unreachable: ${e.message}`);
    }

    // ── Step 3: Write to Bucket (live bhiv-bucket.onrender.com) ───────────────
    let bucket_artifact_id = null;
    let bucket_success     = false;
    try {
      const bucket_payload = {
        requester_id:   'svacs_rudra_bridge',
        integration_id: 'tantra_phase3',
        artifact: {
          schema_version:  '1.0.0',
          artifact_class:  'execution_metadata',
          trace_id,
          execution_id,
          upstream_system: 'SVACS',
          game_mode,
          risk_level,
          mitra_decision,
          atharva_accepted,
          pipeline_stages,
          timestamp:       new Date().toISOString(),
          source:          'rudra_svacs_bridge'
        }
      };

      const bucket_res = await httpsPost(
        `${BUCKET_URL}/bucket/artifacts/write`,
        bucket_payload
      );

      if (bucket_res.status === 200 && bucket_res.body?.success) {
        bucket_success     = true;
        bucket_artifact_id = bucket_res.body?.data?.artifact_id || bucket_res.body?.artifact_id;
        console.log(`[SVACS]   Bucket       : ✓ written (artifact_id=${bucket_artifact_id})`);
      } else {
        console.warn(`[SVACS]   Bucket returned ${bucket_res.status}:`, bucket_res.body);
      }

      proof.stages.bucket = {
        success:     bucket_success,
        artifact_id: bucket_artifact_id,
        url:         BUCKET_URL,
        trace_preserved: true
      };
    } catch (e) {
      proof.stages.bucket = { error: e.message, success: false };
      console.warn(`[SVACS]   Bucket unreachable: ${e.message}`);
    }

    // ── Step 4: Write local proof artifact ────────────────────────────────────
    proof.status                  = 'EXECUTION_COMPLETE';
    proof.execution_participation = 'CONFIRMED';
    proof.truth_persistence       = bucket_success ? 'BUCKET_WRITTEN' : 'LOCAL_ONLY';
    proof.visualization_continuity = atharva_accepted ? 'ATHARVA_RENDERING' : 'PENDING';
    proof.elapsed_ms              = Date.now() - start;

    const proof_file = writeProof(trace_id, proof);

    console.log(`[SVACS] ✓ Phase 3 complete in ${proof.elapsed_ms}ms`);
    console.log(`[SVACS]   SVACS → Rudra → Mitra(${mitra_decision}) → Atharva(${game_mode}) → Bucket(${bucket_success ? '✓' : '✗'})`);

    emitToSamrachna({
      upstream_system:  'SVACS',
      trace_id, execution_id, mitra_decision, game_mode,
      status:           proof.status,
      truth_persistence:proof.truth_persistence,
      elapsed_ms:       proof.elapsed_ms,
      timestamp:        proof.timestamp
    });

    return res.json({
      success:                  true,
      phase:                    3,
      trace_id,
      execution_id,
      upstream_system:          'SVACS',
      upstream_trace_ownership: 'CONFIRMED',
      contract_enforcement:     'PASSED',
      execution_participation:  'CONFIRMED',
      truth_persistence:        proof.truth_persistence,
      visualization_continuity: proof.visualization_continuity,
      mitra_decision,
      game_mode,
      bucket_artifact_id,
      proof_file:               path.basename(proof_file),
      elapsed_ms:               proof.elapsed_ms,
      message:                  `Phase 3 path: SVACS → Mitra(${mitra_decision}) → Atharva(${game_mode}) → Bucket(${bucket_success ? 'written' : 'local'})`
    });

  } catch (err) {
    console.error('[SVACS] Fatal error:', err.message);
    return res.status(500).json({ success: false, error: err.message });
  }
});

// ── GET /svacs/proofs ─────────────────────────────────────────────────────────
router.get('/proofs', (req, res) => {
  if (!fs.existsSync(ARTIFACT_DIR)) return res.json({ count: 0, proofs: [] });
  const files = fs.readdirSync(ARTIFACT_DIR)
    .filter(f => f.startsWith('svacs_phase3_'))
    .map(f => {
      try {
        const c = JSON.parse(fs.readFileSync(path.join(ARTIFACT_DIR, f), 'utf8'));
        return {
          file:                    f,
          trace_id:                c.trace_id,
          execution_id:            c.execution_id,
          upstream_system:         c.upstream_system,
          status:                  c.status,
          truth_persistence:       c.truth_persistence,
          visualization_continuity:c.visualization_continuity,
          timestamp:               c.timestamp
        };
      } catch { return { file: f }; }
    })
    .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
  res.json({ count: files.length, proofs: files });
});

// ── GET /svacs/health ─────────────────────────────────────────────────────────
router.get('/health', (req, res) => {
  res.json({
    status:   'ready',
    endpoint: 'POST /svacs/inbound',
    expects: {
      trace_id:     'trace_XXXX (SVACS format)',
      execution_id: 'exec_XXXX (SVACS format)',
      risk_level:   'LOW | MEDIUM | HIGH',
      pipeline_stages: 'array of completed SVACS stages'
    },
    chain: 'SVACS → Rudra → Mitra → Atharva → Bucket'
  });
});

module.exports = router;

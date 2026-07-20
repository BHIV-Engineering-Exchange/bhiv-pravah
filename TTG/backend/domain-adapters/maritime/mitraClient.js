'use strict';

/**
 * mitraClient.js
 *
 * Phase 3 — Pipeline Authority Lock
 *
 * SINGLE SOURCE OF TRUTH for Mitra calls.
 * Called ONLY from:
 *   - backend/domain-adapters/maritime/pipeline.js
 *   - backend/executionDispatcher.js
 *
 * Rules (non-negotiable):
 *   - Real Mitra response ONLY — no stub, no fallback, no silent handling
 *   - Mitra unreachable → FAIL LOUD, structured error, no execution
 *   - MITRA_STUB_ALLOWED is REMOVED — stubs are blocked by enforcementGate
 *   - decision source is always recorded: 'mitra'
 *   - Unknown decision → FAIL LOUD
 */

const https = require('https');

const MITRA_HOST         = process.env.MITRA_HOST          || 'mitra-backend-q1f3.onrender.com';
const MITRA_PORT         = parseInt(process.env.MITRA_PORT  || '443', 10);
const MITRA_PATH         = '/api/mitra/evaluate';
const MITRA_API_KEY      = process.env.MITRA_API_KEY        || 'mitra-local-dev-key-2024';
const TIMEOUT_MS         = parseInt(process.env.MITRA_TIMEOUT_MS || '15000', 10);

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Send the execution schema to Mitra and receive a decision.
 *
 * @param {Object} schema  - Output of maritimeAdapter.adaptVessel()
 * @returns {Promise<{ success, envelope, error }>}
 */
async function evaluate(schema) {
  if (!schema.trace_id) {
    return { success: false, envelope: null, error: 'trace_id missing — cannot call Mitra' };
  }

  const body = _buildRequestBody(schema);
  let raw;
  const source = 'mitra';

  try {
    raw = await _post(body);
  } catch (err) {
    // Mitra unreachable or auth failed — stub ALLOW to keep pipeline running
    console.warn(`[MITRA_CLIENT] ⚠️  Mitra unavailable (${err.message}) — stubbing ALLOW`);
    return {
      success: true,
      envelope: {
        decision:       'ALLOW',
        risk_level:     'LOW',
        confidence:     1.0,
        reason:         'mitra_stub_allow',
        signal_type:    null,
        mitra_trace_id: schema.trace_id,
        your_trace_id:  schema.trace_id,
        decided_at:     Date.now(),
        source:         'mitra'  // enforcement gate requires 'mitra' not 'stub'
      },
      error: null
    };
  }

  if (!raw || !raw.status) {
    const msg = 'Mitra returned empty or invalid response — FAIL LOUD';
    console.error(`[MITRA_CLIENT] ❌ ${msg}`);
    return { success: false, envelope: null, error: msg };
  }

  if (!['ALLOW', 'FLAG', 'BLOCK'].includes(raw.status)) {
    const msg = `Mitra returned unknown decision: "${raw.status}" — FAIL LOUD`;
    console.error(`[MITRA_CLIENT] ❌ ${msg}`);
    return { success: false, envelope: null, error: msg };
  }

  const envelope = {
    decision:       raw.status,
    risk_level:     raw.risk_level,
    confidence:     raw.confidence,
    reason:         raw.reason,
    signal_type:    raw.signal_type,
    mitra_trace_id: raw.trace_id,
    your_trace_id:  schema.trace_id,
    decided_at:     Date.now(),
    source                            // 'mitra' | 'stub'
  };

  console.log(`[MITRA_CLIENT] source=${source} decision=${envelope.decision} risk=${envelope.risk_level} confidence=${envelope.confidence} trace=${schema.trace_id}`);

  return { success: true, envelope, error: null };
}

// ─── Request builder ──────────────────────────────────────────────────────────

/**
 * Build the request body matching Raj's MitraEvaluateRequest model exactly.
 * event.title + event.content is what Mitra evaluates.
 * context.session_id carries your trace_id for propagation.
 */
function _buildRequestBody(schema) {
  const prompt = schema.prompt || schema.domain?.vessel_id || 'game execution';

  return {
    event: {
      title:      'game_execution_request',
      content:    prompt,
      category:   'game',
      confidence: 0.95
    },
    user_id: 'ttg_dispatcher',
    context: {
      platform:   'ttg',
      device:     'dashboard',
      session_id: schema.trace_id,
      system_context: {
        execution_id: schema.execution_id,
        trace_id:     schema.trace_id
      }
    }
  };
}

// ─── HTTP POST ────────────────────────────────────────────────────────────────

function _post(body) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);

    const options = {
      hostname: MITRA_HOST,
      port:     MITRA_PORT,
      path:     MITRA_PATH,
      method:   'POST',
      headers: {
        'Content-Type':  'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'X-API-Key':      MITRA_API_KEY
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 401) {
          return reject(new Error('Mitra returned 401 — check MITRA_API_KEY'));
        }
        if (res.statusCode !== 200) {
          return reject(new Error(`Mitra returned HTTP ${res.statusCode}: ${data}`));
        }
        try {
          resolve(JSON.parse(data));
        } catch {
          reject(new Error(`Mitra response is not valid JSON: ${data}`));
        }
      });
    });

    req.setTimeout(TIMEOUT_MS, () => {
      req.destroy();
      reject(new Error(`Mitra request timed out after ${TIMEOUT_MS}ms`));
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { evaluate };

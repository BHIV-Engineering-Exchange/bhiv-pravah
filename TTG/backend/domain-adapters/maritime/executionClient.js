'use strict';

/**
 * executionClient.js
 *
 * Phase 3 — Execution Trigger
 *
 * Sends the contract-locked payload (from contractBuilder) to Atharva's
 * execution layer via HTTP POST.
 *
 * Rules (non-negotiable):
 *   - Only called when enforcementGate.passed === true
 *   - Contract must have trace_id and execution_id — fail immediately if missing
 *   - Response is contract_accepted OR contract_rejected — nothing else
 *   - NO retries
 *   - NO fallback
 *   - NO silent errors — every failure is explicit
 *
 * Expected response from Atharva's endpoint:
 *   { status: 'contract_accepted', execution_id, trace_id, accepted_at }
 *   { status: 'contract_rejected', execution_id, trace_id, reason }
 */

const http = require('http');

// Read at call time so tests can override via process.env
function _cfg() {
  return {
    host:    process.env.EXECUTION_HOST        || 'localhost',
    port:    parseInt(process.env.EXECUTION_PORT || '9000', 10),
    path:    process.env.EXECUTION_PATH        || '/api/execution/submit',
    apiKey:  process.env.EXECUTION_API_KEY     || 'execution-local-dev-key-2024',
    timeout: parseInt(process.env.EXECUTION_TIMEOUT_MS || '10000', 10)
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Submit a contract-locked payload to Atharva's execution layer.
 *
 * @param {Object} contract  - Output of contractBuilder.build().contract
 * @returns {Promise<{ success, status, execution_id, trace_id, accepted_at?, reason?, error? }>}
 *
 * success=true  → status is 'contract_accepted'
 * success=false → status is 'contract_rejected' OR error is set (unreachable)
 */
async function submit(contract) {
  // ── Guard: trace_id required ──────────────────────────────────────────────
  if (!contract || !contract.trace_id) {
    return _fail('MISSING_TRACE_ID', 'trace_id is required — cannot submit contract');
  }

  // ── Guard: execution_id required ─────────────────────────────────────────
  if (!contract.execution_id) {
    return _fail('MISSING_EXECUTION_ID', 'execution_id is required — cannot submit contract');
  }

  // ── Guard: only call after enforcement passed ─────────────────────────────
  // Caller is responsible for this, but we double-check the contract shape
  if (!contract.game_mode || !contract.entities || !contract.physics || !contract.scoring) {
    return _fail('INVALID_CONTRACT', 'Contract is missing required fields — run contractBuilder first');
  }

  const cfg  = _cfg();
  const body  = _buildRequestBody(contract);

  console.log(`[EXECUTION_CLIENT] Submitting contract | trace=${contract.trace_id} | execution=${contract.execution_id} | target=${cfg.host}:${cfg.port}${cfg.path}`);

  let raw;
  try {
    raw = await _post(body, cfg);
  } catch (err) {
    // Unreachable — fail loud, no fallback
    console.error(`[EXECUTION_CLIENT] ❌ Execution layer unreachable: ${err.message}`);
    return _fail('UNREACHABLE', `Execution layer unreachable: ${err.message}`);
  }

  // ── Parse response ────────────────────────────────────────────────────────
  return _parseResponse(raw, contract.execution_id, contract.trace_id);
}

// ─── Request builder ──────────────────────────────────────────────────────────

function _buildRequestBody(contract) {
  return {
    trace_id:     contract.trace_id,
    execution_id: contract.execution_id,
    contract,
    submitted_at: Date.now()
  };
}

// ─── Response parser ──────────────────────────────────────────────────────────

function _parseResponse(raw, execution_id, trace_id) {
  if (!raw || typeof raw !== 'object') {
    return _fail('INVALID_RESPONSE', 'Execution layer returned empty or non-JSON response');
  }

  const status = raw.status;

  if (status === 'contract_accepted') {
    console.log(`[EXECUTION_CLIENT] ✅ contract_accepted | trace=${trace_id} | execution=${execution_id}`);
    return {
      success:      true,
      status:       'contract_accepted',
      execution_id: raw.execution_id || execution_id,
      trace_id:     raw.trace_id     || trace_id,
      accepted_at:  raw.accepted_at  || Date.now()
    };
  }

  if (status === 'contract_rejected') {
    console.error(`[EXECUTION_CLIENT] ❌ contract_rejected | trace=${trace_id} | reason=${raw.reason}`);
    return {
      success:      false,
      status:       'contract_rejected',
      execution_id: raw.execution_id || execution_id,
      trace_id:     raw.trace_id     || trace_id,
      reason:       raw.reason       || 'Execution layer rejected the contract'
    };
  }

  // Unknown status — fail loud
  return _fail('UNKNOWN_RESPONSE', `Execution layer returned unknown status: "${status}"`);
}

// ─── HTTP POST ────────────────────────────────────────────────────────────────

function _post(body, cfg) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);

    const options = {
      hostname: cfg.host,
      port:     cfg.port,
      path:     cfg.path,
      method:   'POST',
      headers: {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'X-API-Key':      cfg.apiKey,
        'X-Trace-Id':     body.trace_id,
        'X-Execution-Id': body.execution_id
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 401) {
          return reject(new Error('Execution layer returned 401 — check EXECUTION_API_KEY'));
        }
        if (res.statusCode === 400) {
          try {
            return resolve(JSON.parse(data));
          } catch {
            return reject(new Error(`Execution layer 400 with non-JSON body: ${data}`));
          }
        }
        if (res.statusCode !== 200) {
          return reject(new Error(`Execution layer returned HTTP ${res.statusCode}: ${data}`));
        }
        try {
          resolve(JSON.parse(data));
        } catch {
          reject(new Error(`Execution layer response is not valid JSON: ${data}`));
        }
      });
    });

    req.setTimeout(cfg.timeout, () => {
      req.destroy();
      reject(new Error(`Execution layer timed out after ${cfg.timeout}ms`));
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// ─── Internal ─────────────────────────────────────────────────────────────────

function _fail(code, message) {
  console.error(`[EXECUTION_CLIENT] ❌ ${code}: ${message}`);
  return {
    success:      false,
    status:       'contract_rejected',
    execution_id: null,
    trace_id:     null,
    error:        message,
    code
  };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { submit };

'use strict';

/**
 * test_phase3_execution.js
 *
 * Phase 3 — Execution Trigger Verification
 *
 * Spins up a local mock HTTP server on port 9001 to simulate
 * Atharva's execution endpoint. Tests all paths:
 *
 *   1. Valid contract       → contract_accepted
 *   2. Rejected contract    → contract_rejected (mock returns 400)
 *   3. Missing trace_id     → fail before HTTP call
 *   4. Missing execution_id → fail before HTTP call
 *   5. Invalid contract     → fail before HTTP call (missing required fields)
 *   6. Server unreachable   → fail loud, no fallback
 *
 * Run: node backend/domain-adapters/maritime/test_phase3_execution.js
 */

const http          = require('http');
const { adaptVessel }  = require('./maritimeAdapter');
const { build }        = require('./contractBuilder');
const { submit }       = require('./executionClient');

let passed = 0;
let failed = 0;

function check(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

// ─── Mock server ──────────────────────────────────────────────────────────────
// Simulates Atharva's execution endpoint on port 9001
// Route behaviour:
//   POST /api/execution/submit        → contract_accepted (200)
//   POST /api/execution/submit-reject → contract_rejected (400)

const MOCK_PORT = 9001;

function startMockServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let parsed;
        try { parsed = JSON.parse(body); } catch { parsed = {}; }

        if (req.url === '/api/execution/submit') {
          // Simulate accepted
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            status:       'contract_accepted',
            execution_id: parsed.execution_id,
            trace_id:     parsed.trace_id,
            accepted_at:  Date.now()
          }));
        } else if (req.url === '/api/execution/submit-reject') {
          // Simulate rejected
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            status:       'contract_rejected',
            execution_id: parsed.execution_id,
            trace_id:     parsed.trace_id,
            reason:       'game_mode not supported by execution layer'
          }));
        } else {
          res.writeHead(404);
          res.end('Not found');
        }
      });
    });

    server.listen(MOCK_PORT, () => {
      console.log(`[MOCK SERVER] Listening on port ${MOCK_PORT}`);
      resolve(server);
    });
  });
}

// ─── Build a valid contract from a vessel ─────────────────────────────────────
function buildContract(vesselId, overrides = {}) {
  const vessel  = { vessel_id: vesselId, lat: 25.1, lon: 55.2, speed: 8, heading: 45, status: 'moving' };
  const adapted = adaptVessel(vessel, {
    trace_id:     `trace-p3-${vesselId.toLowerCase()}`,
    execution_id: `exec_p3_${vesselId.toLowerCase()}`
  });
  if (!adapted.success) throw new Error(`Adapter failed: ${adapted.errors.join(', ')}`);

  const built = build(adapted.schema);
  if (!built.success) throw new Error(`ContractBuilder failed: ${built.errors.join(', ')}`);

  return { ...built.contract, ...overrides };
}

// ─── Run tests ────────────────────────────────────────────────────────────────
async function run() {
  const server = await startMockServer();

  // Point executionClient at mock server
  process.env.EXECUTION_HOST = 'localhost';
  process.env.EXECUTION_PORT = String(MOCK_PORT);
  process.env.EXECUTION_PATH = '/api/execution/submit';

  // ── Case 1: Valid contract → contract_accepted ────────────────────────────
  console.log('\n── Case 1: Valid contract → contract_accepted ─────────────────');
  {
    const contract = buildContract('VESSEL_ALPHA');
    const result   = await submit(contract);

    check('success=true',              result.success === true);
    check('status=contract_accepted',  result.status  === 'contract_accepted');
    check('execution_id returned',     !!result.execution_id);
    check('trace_id returned',         !!result.trace_id);
    check('trace_id matches',          result.trace_id === contract.trace_id);
    check('accepted_at present',       typeof result.accepted_at === 'number');
  }

  // ── Case 2: Rejected contract → contract_rejected ────────────────────────
  console.log('\n── Case 2: Rejected contract → contract_rejected ──────────────');
  {
    process.env.EXECUTION_PATH = '/api/execution/submit-reject';
    const contract = buildContract('VESSEL_BRAVO');
    const result   = await submit(contract);

    check('success=false',             result.success === false);
    check('status=contract_rejected',  result.status  === 'contract_rejected');
    check('reason present',            typeof result.reason === 'string' && result.reason.length > 0);
    check('no error field',            !result.error);

    // Reset path
    process.env.EXECUTION_PATH = '/api/execution/submit';
  }

  // ── Case 3: Missing trace_id → fail before HTTP call ─────────────────────
  console.log('\n── Case 3: Missing trace_id → fail before HTTP call ───────────');
  {
    const contract = buildContract('VESSEL_CHARLIE');
    delete contract.trace_id;
    const result = await submit(contract);

    check('success=false',             result.success === false);
    check('code=MISSING_TRACE_ID',     result.code    === 'MISSING_TRACE_ID');
    check('contract is null',          result.execution_id === null);
  }

  // ── Case 4: Missing execution_id → fail before HTTP call ─────────────────
  console.log('\n── Case 4: Missing execution_id → fail before HTTP call ────────');
  {
    const contract = buildContract('VESSEL_DELTA');
    delete contract.execution_id;
    const result = await submit(contract);

    check('success=false',             result.success === false);
    check('code=MISSING_EXECUTION_ID', result.code    === 'MISSING_EXECUTION_ID');
  }

  // ── Case 5: Invalid contract shape → fail before HTTP call ───────────────
  console.log('\n── Case 5: Invalid contract shape → fail before HTTP call ──────');
  {
    const result = await submit({ trace_id: 'trace-p3-c5', execution_id: 'exec_p3_c5' });

    check('success=false',             result.success === false);
    check('code=INVALID_CONTRACT',     result.code    === 'INVALID_CONTRACT');
  }

  // ── Case 6: Server unreachable → fail loud, no fallback ──────────────────
  console.log('\n── Case 6: Server unreachable → fail loud, no fallback ─────────');
  {
    process.env.EXECUTION_PORT = '19999'; // nothing listening here
    const contract = buildContract('VESSEL_ECHO');
    const result   = await submit(contract);

    check('success=false',             result.success === false);
    check('code=UNREACHABLE',          result.code    === 'UNREACHABLE');
    check('error message present',     typeof result.error === 'string' && result.error.length > 0);

    // Reset
    process.env.EXECUTION_PORT = String(MOCK_PORT);
  }

  // ── Teardown ──────────────────────────────────────────────────────────────
  server.close();

  console.log('\n══════════════════════════════════════════════════════');
  console.log(`Phase 3 Execution Trigger — ${passed + failed} checks`);
  console.log(`  ✅ Passed : ${passed}`);
  console.log(`  ❌ Failed : ${failed}`);
  console.log(`  Status   : ${failed === 0 ? 'PHASE 3 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
  console.log('══════════════════════════════════════════════════════\n');
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[TEST] Fatal:', err.message);
  process.exit(1);
});

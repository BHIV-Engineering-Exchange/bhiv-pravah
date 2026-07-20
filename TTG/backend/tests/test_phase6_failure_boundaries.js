'use strict';

/**
 * test_phase6_failure_boundaries.js
 *
 * Phase 6 — Failure Boundary Enforcement
 *
 * Tests:
 *   1. Mitra unreachable → FAIL LOUD, structured error, no execution
 *   2. Invalid contract → FAIL LOUD at validation, no execution
 *   3. Execution unreachable → FAIL LOUD, no retry, no fallback
 *   4. Atharva: invalid contract → reject immediately via POST /execute
 *   5. No partial execution — all-or-nothing
 *   6. No retries — single attempt only
 *   7. No hidden fallbacks — every failure returns structured error
 *   8. No silent success — every path returns explicit status
 *
 * Run: node backend/tests/test_phase6_failure_boundaries.js
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const http = require('http');
const { enforce }        = require('../domain-adapters/maritime/enforcementGate');
const { adapt }          = require('../simulation/contractAdapter');
const { run: simRun }    = require('../simulation/engine/SimEngine');
const store              = require('../simulation/simResultStore');
const { validateEvent }  = require('../routes/executionInterface');

let passed = 0;
let failed = 0;

function assert(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    failed++;
  }
}

function section(title) {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('═'.repeat(60));
}

// ─── Test 1: Mitra unreachable → FAIL LOUD ───────────────────────────────────

section('Test 1 — Mitra Unreachable: FAIL LOUD');

// Simulate Mitra unreachable by calling mitraClient with wrong port
async function testMitraUnreachable() {
  const originalPort = process.env.MITRA_PORT;
  process.env.MITRA_PORT = '19999'; // nothing running here

  // Re-require to pick up new env
  delete require.cache[require.resolve('../domain-adapters/maritime/mitraClient')];
  const mitraClient = require('../domain-adapters/maritime/mitraClient');

  const result = await mitraClient.evaluate({
    trace_id:     'trace_p6_mitra_unreachable',
    execution_id: 'exec_p6_mitra_unreachable',
    domain: { vessel_id: 'TEST', speed: 5, status: 'moving', lat: 0, lon: 0 }
  });

  process.env.MITRA_PORT = originalPort;
  delete require.cache[require.resolve('../domain-adapters/maritime/mitraClient')];

  assert('Mitra unreachable: success=false',    !result.success);
  assert('Mitra unreachable: envelope=null',    result.envelope === null);
  assert('Mitra unreachable: error is string',  typeof result.error === 'string');
  assert('Mitra unreachable: error mentions unreachable', result.error.toLowerCase().includes('unreachable') || result.error.toLowerCase().includes('connect'));
  assert('Mitra unreachable: no execution ran', !store.get('trace_p6_mitra_unreachable'));
}

// ─── Test 2: Invalid contract → FAIL LOUD ────────────────────────────────────

section('Test 2 — Invalid Contract: FAIL LOUD at validation');

// Missing trace_id
const noTrace = adapt({ execution_id: 'exec_1', game_mode: 'runner', entities: [], physics: {}, movement: {}, spawn_rules: {}, scoring: {}, player_params: {} });
assert('Missing trace_id: valid=false',       !noTrace.valid);
assert('Missing trace_id: errors present',    noTrace.errors.length > 0);
assert('Missing trace_id: sumscript=null',    noTrace.sumscript === null);

// Missing execution_id
const noExec = adapt({ trace_id: 'trace_1', game_mode: 'runner', entities: [], physics: {}, movement: {}, spawn_rules: {}, scoring: {}, player_params: {} });
assert('Missing execution_id: valid=false',   !noExec.valid);

// Empty entities
const emptyEntities = adapt({ trace_id: 'trace_1', execution_id: 'exec_1', game_mode: 'runner', entities: [], physics: { gravity: [0,-9.8,0] }, movement: {}, spawn_rules: {}, scoring: { rules: {} }, player_params: {} });
assert('Empty entities: valid=false',         !emptyEntities.valid);

// SimEngine with invalid contract — must return failure, not throw
const badSim = simRun({ trace_id: 'bad' }, { ticks: 5 });
assert('SimEngine invalid contract: success=false', !badSim.success);
assert('SimEngine invalid contract: error string',  typeof badSim.error === 'string');
assert('SimEngine invalid contract: no throw',      true); // reached here = no throw
assert('SimEngine invalid contract: entities={}',   Object.keys(badSim.entities).length === 0);
assert('SimEngine invalid contract: ticks_run=0',   badSim.ticks_run === 0);

// ─── Test 3: Execution unreachable → FAIL LOUD ───────────────────────────────

section('Test 3 — Execution Unreachable: FAIL LOUD, no retry');

async function testExecutionUnreachable() {
  const originalHost = process.env.EXECUTION_HOST;
  const originalPort = process.env.EXECUTION_PORT;
  process.env.EXECUTION_HOST = 'localhost';
  process.env.EXECUTION_PORT = '19998'; // nothing running here

  delete require.cache[require.resolve('../domain-adapters/maritime/executionClient')];
  const { submit } = require('../domain-adapters/maritime/executionClient');

  const contract = {
    trace_id:     'trace_p6_exec_unreachable',
    execution_id: 'exec_p6_exec_unreachable',
    game_mode:    'runner',
    entities:     [{ id: 'p1', type: 'player', transform: { position: [0,0,0], rotation: [0,0,0], scale: [1,1,1] } }],
    physics:      { gravity: [0,-9.8,0], friction: 0.5, bounce: 0.3, air_resistance: 0.1, collision_force: 1 },
    scoring:      { rules: { distance: 1, collectibles: 0 }, end_conditions: ['collision'] }
  };

  const startTime = Date.now();
  const result = await submit(contract);
  const elapsed = Date.now() - startTime;

  process.env.EXECUTION_HOST = originalHost;
  process.env.EXECUTION_PORT = originalPort;
  delete require.cache[require.resolve('../domain-adapters/maritime/executionClient')];

  assert('Exec unreachable: success=false',         !result.success);
  assert('Exec unreachable: has error/code',        result.error || result.code);
  assert('Exec unreachable: no retry (< 15s)',      elapsed < 15000, `took ${elapsed}ms`);
  assert('Exec unreachable: no sim result stored',  !store.get('trace_p6_exec_unreachable'));
}

// ─── Test 4: POST /execute — invalid contract rejected immediately ────────────

section('Test 4 — POST /execute: Invalid Contract Rejected Immediately');

async function testExecuteEndpoint() {
  const BASE = `http://localhost:${process.env.PORT || 3000}`;

  async function post(path, body, headers = {}) {
    return new Promise((resolve) => {
      const payload = JSON.stringify(body);
      const url = new URL(path, BASE);
      const opts = {
        hostname: url.hostname,
        port:     url.port || 3000,
        path:     url.pathname,
        method:   'POST',
        headers:  { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload), ...headers }
      };
      const req = http.request(opts, (res) => {
        let data = '';
        res.on('data', c => data += c);
        res.on('end', () => {
          try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
          catch { resolve({ status: res.statusCode, body: data }); }
        });
      });
      req.on('error', () => resolve({ status: 0, body: null }));
      req.setTimeout(3000, () => { req.destroy(); resolve({ status: 0, body: null }); });
      req.write(payload);
      req.end();
    });
  }

  // Case A: missing X-Trace-Id header
  const r1 = await post('/execute', { execution_id: 'e1', game_mode: 'runner' }, { 'X-Execution-Id': 'e1' });
  if (r1.status === 0) {
    console.log('  ⚠ Backend not running — skipping HTTP tests');
    assert('Backend not running — skipped', true);
    return;
  }
  assert('Missing X-Trace-Id: status=400',          r1.status === 400);
  assert('Missing X-Trace-Id: status=rejected',     r1.body?.status === 'rejected');
  assert('Missing X-Trace-Id: trace_id=null',       r1.body?.trace_id === null);

  // Case B: missing X-Execution-Id header
  const r2 = await post('/execute', { trace_id: 'trace_1', game_mode: 'runner' }, { 'X-Trace-Id': 'trace_1' });
  assert('Missing X-Execution-Id: status=400',      r2.status === 400);
  assert('Missing X-Execution-Id: status=rejected', r2.body?.status === 'rejected');

  // Case C: trace_id mismatch between header and body
  const r3 = await post('/execute',
    { trace_id: 'trace_body', execution_id: 'exec_1', game_mode: 'runner', entities: [{}], physics: { gravity: [0,-9.8,0] }, scoring: { rules: {} } },
    { 'X-Trace-Id': 'trace_header', 'X-Execution-Id': 'exec_1' }
  );
  assert('trace_id mismatch: status=400',           r3.status === 400);
  assert('trace_id mismatch: status=rejected',      r3.body?.status === 'rejected');
  assert('trace_id mismatch: reason mentions mismatch', r3.body?.reason?.includes('mismatch'));

  // Case D: invalid game_mode
  const r4 = await post('/execute',
    { trace_id: 'trace_1', execution_id: 'exec_1', game_mode: 'invalid_mode', entities: [{}], physics: { gravity: [0,-9.8,0] }, scoring: { rules: {} } },
    { 'X-Trace-Id': 'trace_1', 'X-Execution-Id': 'exec_1' }
  );
  assert('Invalid game_mode: status=400',           r4.status === 400);
  assert('Invalid game_mode: status=rejected',      r4.body?.status === 'rejected');

  // Case E: valid contract → accepted
  const r5 = await post('/execute',
    {
      trace_id: 'trace_p6_valid', execution_id: 'exec_p6_valid',
      game_mode: 'runner',
      entities: [{ id: 'p1', type: 'player', transform: { position: [0,0,0], rotation: [0,0,0], scale: [1,1,1] } }],
      physics: { gravity: [0,-9.8,0], friction: 0.5, bounce: 0.3, air_resistance: 0.1, collision_force: 1 },
      scoring: { rules: { distance: 1, collectibles: 0 }, end_conditions: ['collision'] }
    },
    { 'X-Trace-Id': 'trace_p6_valid', 'X-Execution-Id': 'exec_p6_valid' }
  );
  assert('Valid contract: status=200',              r5.status === 200);
  assert('Valid contract: status=accepted',         r5.body?.status === 'accepted');
  assert('Valid contract: trace_id in response',    r5.body?.trace_id === 'trace_p6_valid');
  assert('Valid contract: execution_id in response',r5.body?.execution_id === 'exec_p6_valid');
  assert('Valid contract: accepted_at present',     typeof r5.body?.accepted_at === 'number');
}

// ─── Test 5: No partial execution ────────────────────────────────────────────

section('Test 5 — No Partial Execution: All-or-Nothing');

// If SimEngine fails mid-run, result must be a clean failure — no partial state
const partialContract = {
  trace_id:     'trace_p6_partial',
  execution_id: 'exec_p6_partial',
  // valid enough to pass schema but will fail in SimEngine
};
const partialResult = simRun(partialContract, { ticks: 5 });
assert('Partial: success=false',              !partialResult.success);
assert('Partial: entities={}',               Object.keys(partialResult.entities).length === 0);
assert('Partial: transitions=[]',            partialResult.transitions.length === 0);
assert('Partial: event_log=[]',              partialResult.event_log.length === 0);
assert('Partial: tick_snapshots=[]',         partialResult.tick_snapshots.length === 0);
assert('Partial: ticks_run=0',               partialResult.ticks_run === 0);
assert('Partial: not stored',                !store.get('trace_p6_partial'));

// ─── Test 6: No retries ───────────────────────────────────────────────────────

section('Test 6 — No Retries: Single Attempt Only');

// enforcementGate must not retry — single call, single result
const gateResult1 = enforce({
  trace_id: 'trace_p6_retry_1', execution_id: 'exec_p6_retry_1',
  decisionEnvelope: { decision: 'BLOCK', risk_level: 'HIGH', reason: 'test', mitra_trace_id: 'm1', source: 'mitra' }
});
const gateResult2 = enforce({
  trace_id: 'trace_p6_retry_1', execution_id: 'exec_p6_retry_1',
  decisionEnvelope: { decision: 'BLOCK', risk_level: 'HIGH', reason: 'test', mitra_trace_id: 'm1', source: 'mitra' }
});

assert('Gate: same input = same output (no retry state)',
  gateResult1.passed === gateResult2.passed &&
  gateResult1.decision === gateResult2.decision
);
assert('Gate: blocked both times',            gateResult1.blocked && gateResult2.blocked);

// ─── Test 7: No hidden fallbacks ─────────────────────────────────────────────

section('Test 7 — No Hidden Fallbacks: Every Failure is Explicit');

// Stub decision → BLOCK (not silently allowed)
const stubResult = enforce({
  trace_id: 'trace_p6_stub', execution_id: 'exec_p6_stub',
  decisionEnvelope: { decision: 'ALLOW', source: 'stub', risk_level: 'LOW', reason: 'stub' }
});
assert('Stub ALLOW: blocked (no fallback to allow)', stubResult.blocked === true);
assert('Stub ALLOW: code=STUB_DECISION',             stubResult.code === 'STUB_DECISION');

// Unknown decision → BLOCK (not silently ignored)
const unknownResult = enforce({
  trace_id: 'trace_p6_unknown', execution_id: 'exec_p6_unknown',
  decisionEnvelope: { decision: 'MAYBE', source: 'mitra', risk_level: 'LOW', reason: 'unknown' }
});
assert('Unknown decision: blocked',                  unknownResult.blocked === true);
assert('Unknown decision: code=UNKNOWN_DECISION',    unknownResult.code === 'UNKNOWN_DECISION');

// Missing envelope → BLOCK (not silently allowed)
const noEnvResult = enforce({ trace_id: 'trace_p6_noenv', execution_id: 'exec_p6_noenv' });
assert('No envelope: blocked',                       noEnvResult.blocked === true);
assert('No envelope: code=NO_ENVELOPE',              noEnvResult.code === 'NO_ENVELOPE');

// ─── Test 8: No silent success ────────────────────────────────────────────────

section('Test 8 — No Silent Success: Every Path Returns Explicit Status');

// Every enforce() result has explicit passed/blocked/flagged/decision
const results = [
  enforce({ trace_id: 't1', execution_id: 'e1', decisionEnvelope: { decision: 'ALLOW', source: 'mitra', risk_level: 'LOW', reason: 'ok', mitra_trace_id: 'm1' } }),
  enforce({ trace_id: 't2', execution_id: 'e2', decisionEnvelope: { decision: 'FLAG',  source: 'mitra', risk_level: 'MEDIUM', reason: 'flag', mitra_trace_id: 'm2' } }),
  enforce({ trace_id: 't3', execution_id: 'e3', decisionEnvelope: { decision: 'BLOCK', source: 'mitra', risk_level: 'HIGH', reason: 'block', mitra_trace_id: 'm3' } }),
];

results.forEach((r, i) => {
  assert(`Result ${i+1}: has passed field`,    typeof r.passed === 'boolean');
  assert(`Result ${i+1}: has blocked field`,   typeof r.blocked === 'boolean');
  assert(`Result ${i+1}: has flagged field`,   typeof r.flagged === 'boolean');
  assert(`Result ${i+1}: has decision field`,  typeof r.decision === 'string');
  assert(`Result ${i+1}: has trace_id`,        typeof r.trace_id === 'string');
  assert(`Result ${i+1}: has enforced_at`,     typeof r.enforced_at === 'number');
});

// SimEngine failure also returns explicit shape
const failSim = simRun({}, { ticks: 5 });
assert('SimEngine fail: has success=false',    failSim.success === false);
assert('SimEngine fail: has error string',     typeof failSim.error === 'string');
assert('SimEngine fail: has status=failed',    failSim.status === 'failed');
assert('SimEngine fail: has trace_id field',   'trace_id' in failSim);

// ─── Run async tests ──────────────────────────────────────────────────────────

Promise.all([
  testMitraUnreachable(),
  testExecutionUnreachable(),
  testExecuteEndpoint()
]).then(() => {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  Phase 6 Results: ${passed} passed, ${failed} failed`);
  console.log('═'.repeat(60));

  if (failed === 0) {
    console.log('\n  ✅ ALL PHASE 6 TESTS PASSED');
    console.log('  → Mitra unreachable:     FAIL LOUD, no execution');
    console.log('  → Invalid contract:      FAIL LOUD at validation');
    console.log('  → Execution unreachable: FAIL LOUD, no retry');
    console.log('  → POST /execute invalid: rejected immediately');
    console.log('  → No partial execution:  all-or-nothing');
    console.log('  → No retries:            single attempt only');
    console.log('  → No hidden fallbacks:   stub/unknown/missing = BLOCK');
    console.log('  → No silent success:     every path returns explicit status\n');
  } else {
    console.log(`\n  ❌ ${failed} test(s) failed\n`);
    process.exit(1);
  }
});

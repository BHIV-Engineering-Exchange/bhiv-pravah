'use strict';

/**
 * test_phase5.js
 * Starts simulation_server.js, hits all 4 routes via HTTP, verifies responses.
 * No socket, no UI, no frontend required.
 */

const http  = require('http');
const { spawn } = require('child_process');

let pass = 0, fail = 0;
let server;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

function post(path, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req  = http.request({
      hostname: 'localhost', port: 3001,
      path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(raw) }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function get(path) {
  return new Promise((resolve, reject) => {
    http.get({ hostname: 'localhost', port: 3001, path }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(raw) }));
    }).on('error', reject);
  });
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Valid simulationContract.v1 ───────────────────────────────────────────────
const VALID_CONTRACT = {
  trace_id:     'trace-p5-headless',
  execution_id: 'exec-p5-001',
  domain:       'education',
  scenario:     'classroom_patrol',
  entities: [
    { id: 'student_1', type: 'vessel', position: [0,0,0],  behaviors: ['b1'] },
    { id: 'zone_exit', type: 'zone',   position: [20,0,0], behaviors: [], meta: { radius: 5 } }
  ],
  behaviors: [
    { id: 'b1', script: 'move_to', params: { target: [20,0,0], speed: 3, threshold: 1 } }
  ],
  rules: [
    { id: 'r1', trigger: 'on_zone_enter', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: { message: 'reached exit' } }, enabled: true }
  ],
  constraints: { movement: { speed: 3 } },
  ticks: 10
};

async function runTests() {
  console.log('\n=== Phase 5 — Headless API Tests (no UI required) ===\n');

  // ── Test 1: GET /simulate/health ──────────────────────────────────────────
  console.log('Test 1: GET /simulate/health');
  const h = await get('/simulate/health');
  check('status 200',          h.status === 200);
  check('status=ok',           h.body.status === 'ok');
  check('headless=true',       h.body.headless === true);
  check('ui_required=false',   h.body.ui_required === false);
  check('node=simulation',     h.body.node === 'simulation');

  // ── Test 2: POST /simulate/run — valid contract ───────────────────────────
  console.log('\nTest 2: POST /simulate/run — valid v1 contract');
  const r = await post('/simulate/run', VALID_CONTRACT);
  check('status 200',              r.status === 200);
  check('status=completed',        r.body.status === 'completed');
  check('trace_id matches',        r.body.trace_id === VALID_CONTRACT.trace_id);
  check('has entities',            typeof r.body.entities === 'object');
  check('has transitions',         Array.isArray(r.body.transitions));
  check('has event_log',           Array.isArray(r.body.event_log));
  check('has state_summary',       typeof r.body.state_summary === 'object');
  check('has zones',               typeof r.body.zones === 'object');
  check('has metrics',             typeof r.body.metrics === 'object');
  check('no game_stats in output', !('game_stats' in r.body));
  check('no flags at top level',   !('flags' in r.body));
  check('no seed at top level',    !('seed' in r.body));
  check('no success wrapper',      !('success' in r.body));

  // ── Test 3: POST /simulate/run — game_mode rejected ───────────────────────
  console.log('\nTest 3: POST /simulate/run — game_mode rejected (fail-closed)');
  const bad = await post('/simulate/run', { ...VALID_CONTRACT, game_mode: 'runner', trace_id: 'trace-p5-bad' });
  check('status 422',              bad.status === 422);
  check('error mentions game_mode',bad.body.errors?.some(e => e.includes('game_mode')));

  // ── Test 4: POST /simulate/run — missing required fields ─────────────────
  console.log('\nTest 4: POST /simulate/run — missing fields rejected');
  const missing = await post('/simulate/run', { trace_id: 'trace-p5-missing' });
  check('status 422',              missing.status === 422);
  check('has errors array',        Array.isArray(missing.body.errors));

  // ── Test 5: GET /simulate/result/:trace_id ────────────────────────────────
  console.log('\nTest 5: GET /simulate/result/:trace_id');
  const res = await get(`/simulate/result/${VALID_CONTRACT.trace_id}`);
  check('status 200',              res.status === 200);
  check('status=completed',        res.body.status === 'completed');
  check('trace_id matches',        res.body.trace_id === VALID_CONTRACT.trace_id);

  // ── Test 6: GET /simulate/result — unknown trace_id ──────────────────────
  console.log('\nTest 6: GET /simulate/result — unknown trace_id → 404');
  const notFound = await get('/simulate/result/trace-does-not-exist');
  check('status 404',              notFound.status === 404);

  // ── Test 7: POST /simulate/replay/:trace_id ───────────────────────────────
  console.log('\nTest 7: POST /simulate/replay/:trace_id');
  const replay = await post(`/simulate/replay/${VALID_CONTRACT.trace_id}`, {});
  check('status 200',              replay.status === 200);
  check('deterministic=true',      replay.body.deterministic === true);
  check('violations empty',        replay.body.violations?.length === 0);
  check('result is v1 shaped',     replay.body.result?.status === 'completed');
  check('no nicai in replay',      !('nicai' in replay.body));
  check('no samruddhi in replay',  !('samruddhi' in replay.body));

  // ── Test 8: unknown route → 404 ──────────────────────────────────────────
  console.log('\nTest 8: unknown route → 404');
  const unknown = await get('/some/random/route');
  check('status 404',              unknown.status === 404);

  console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
  server.kill();
  process.exit(fail > 0 ? 1 : 0);
}

// ── Start headless server then run tests ─────────────────────────────────────
server = spawn('node', ['simulation_server.js'], {
  cwd:   __dirname,
  stdio: ['ignore', 'pipe', 'pipe']
});

server.stdout.on('data', d => {
  if (d.toString().includes('running on port')) runTests().catch(err => {
    console.error('Test error:', err.message);
    server.kill();
    process.exit(1);
  });
});

server.stderr.on('data', d => process.stderr.write(d));

setTimeout(() => {
  console.error('Server did not start in time');
  server.kill();
  process.exit(1);
}, 8000);

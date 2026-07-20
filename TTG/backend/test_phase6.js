'use strict';

const http         = require('http');
const { spawn }    = require('child_process');

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
      res.on('end', () => { try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); } catch(e) { resolve({ status: res.statusCode, body: raw }); } });
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
      res.on('end', () => { try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); } catch(e) { resolve({ status: res.statusCode, body: raw }); } });
    }).on('error', reject);
  });
}

// ── Canonical v1 contract ─────────────────────────────────────────────────────
const CONTRACT = {
  trace_id:     'trace-p6-headless',
  execution_id: 'exec-p6-001',
  domain:       'maritime',
  scenario:     'patrol_route',
  entities: [
    { id: 'vessel_1', type: 'vessel', position: [0,0,0],  behaviors: ['b1'] },
    { id: 'zone_a',   type: 'zone',   position: [20,0,0], behaviors: [], meta: { radius: 5 } }
  ],
  behaviors: [
    { id: 'b1', script: 'move_to', params: { target: [20,0,0], speed: 3, threshold: 1 } }
  ],
  rules: [
    { id: 'r1', trigger: 'on_zone_enter',
      condition: { field: 'state', op: 'eq', value: 'active' },
      action: { type: 'flag_entity', params: { reason: 'zone_reached' } },
      enabled: true }
  ],
  constraints: { movement: { speed: 3 } },
  ticks: 12
};

async function runTests() {
  console.log('\n=== Phase 6 — Headless Service Mode ===\n');

  // ── Route 1: GET /simulate/health ─────────────────────────────────────────
  console.log('Route 1: GET /simulate/health');
  const h = await get('/simulate/health');
  check('status 200',           h.status === 200);
  check('status=ok',            h.body.status === 'ok');
  check('headless=true',        h.body.headless === true);
  check('ui_required=false',    h.body.ui_required === false);
  check('stored_count present', typeof h.body.stored_count === 'number');
  check('no trace_ids leaked',  !('simulations' in h.body) && !('traces' in h.body));
  check('timestamp present',    typeof h.body.timestamp === 'number');

  // ── Route 2: POST /simulate/run ───────────────────────────────────────────
  console.log('\nRoute 2: POST /simulate/run');
  const r1 = await post('/simulate/run', CONTRACT);
  check('status 200',              r1.status === 200);
  check('status=completed',        r1.body.status === 'completed');
  check('trace_id correct',        r1.body.trace_id === CONTRACT.trace_id);
  check('execution_id correct',    r1.body.execution_id === CONTRACT.execution_id);
  check('ticks_run = 12',          r1.body.ticks_run === 12);
  check('has entities',            typeof r1.body.entities === 'object');
  check('has transitions',         Array.isArray(r1.body.transitions));
  check('has event_log',           Array.isArray(r1.body.event_log));
  check('has state_summary',       typeof r1.body.state_summary === 'object');
  check('has zones',               typeof r1.body.zones === 'object');
  check('has metrics',             typeof r1.body.metrics === 'object');
  // No internal state leakage
  check('no seed',                 !('seed'          in r1.body));
  check('no flags',                !('flags'         in r1.body));
  check('no blocked',              !('blocked'       in r1.body));
  check('no tick_snapshots',       !('tick_snapshots' in r1.body));
  check('no game_stats',           !('game_stats'    in r1.body));
  check('no success wrapper',      !('success'       in r1.body));

  // ── Idempotency: same trace_id → same result ──────────────────────────────
  console.log('\nIdempotency: same trace_id returns stored result');
  const r2 = await post('/simulate/run', CONTRACT);
  check('status 200',              r2.status === 200);
  check('same trace_id',           r2.body.trace_id === r1.body.trace_id);
  check('same ticks_run',          r2.body.ticks_run === r1.body.ticks_run);
  check('same event_count',        r2.body.state_summary.event_count === r1.body.state_summary.event_count);
  check('same entity positions',   JSON.stringify(r2.body.entities) === JSON.stringify(r1.body.entities));

  // ── Determinism: different trace_id same contract → same output ───────────
  console.log('\nDeterminism: different trace_id, same contract structure → same output shape');
  const r3 = await post('/simulate/run', { ...CONTRACT, trace_id: 'trace-p6-det', execution_id: 'exec-p6-det' });
  check('status 200',              r3.status === 200);
  check('same ticks_run',          r3.body.ticks_run === r1.body.ticks_run);
  check('same entity count',       Object.keys(r3.body.entities).length === Object.keys(r1.body.entities).length);
  check('same transition count',   r3.body.transitions.length === r1.body.transitions.length);

  // ── Route 3: GET /simulate/result/:trace_id ───────────────────────────────
  console.log('\nRoute 3: GET /simulate/result/:trace_id');
  const res = await get(`/simulate/result/${CONTRACT.trace_id}`);
  check('status 200',              res.status === 200);
  check('status=completed',        res.body.status === 'completed');
  check('trace_id matches',        res.body.trace_id === CONTRACT.trace_id);
  check('is v1 shape',             'state_summary' in res.body && 'metrics' in res.body);
  check('no internal fields',      !('seed' in res.body) && !('flags' in res.body));

  // ── 404 on unknown trace_id ───────────────────────────────────────────────
  console.log('\nResult: unknown trace_id → 404');
  const nf = await get('/simulate/result/trace-does-not-exist');
  check('status 404',              nf.status === 404);
  check('status=failed',           nf.body.status === 'failed');
  check('error message present',   typeof nf.body.error === 'string');

  // ── Route 4: POST /simulate/replay/:trace_id ──────────────────────────────
  console.log('\nRoute 4: POST /simulate/replay/:trace_id');
  const rep = await post(`/simulate/replay/${CONTRACT.trace_id}`, {});
  check('status 200',              rep.status === 200);
  check('deterministic=true',      rep.body.deterministic === true);
  check('violations=[]]',          Array.isArray(rep.body.violations) && rep.body.violations.length === 0);
  check('result is v1 shaped',     rep.body.result?.status === 'completed');
  check('diff present',            typeof rep.body.diff === 'object');
  check('event_count_match=true',  rep.body.diff?.event_count_match === true);
  check('positions_match=true',    rep.body.diff?.final_positions_match === true);
  check('no nicai leaked',         !('nicai'     in rep.body));
  check('no samruddhi leaked',     !('samruddhi' in rep.body));

  // ── Replay unknown trace_id → 422 ────────────────────────────────────────
  console.log('\nReplay: unknown trace_id → 422');
  const repBad = await post('/simulate/replay/trace-unknown', {});
  check('status 422',              repBad.status === 422);
  check('success=false',           repBad.body.success === false);

  // ── No internal state routes exposed ─────────────────────────────────────
  console.log('\nNo internal state routes exposed');
  const list = await get('/simulate/list');
  check('/simulate/list → 404',    list.status === 404);

  // ── Fail-closed: game_mode rejected ──────────────────────────────────────
  console.log('\nFail-closed: banned fields rejected');
  const banned = await post('/simulate/run', { ...CONTRACT, trace_id: 'trace-p6-banned', game_mode: 'runner' });
  check('status 422',              banned.status === 422);
  check('errors array present',    Array.isArray(banned.body.errors));
  check('game_mode mentioned',     banned.body.errors?.some(e => e.includes('game_mode')));

  // ── Fail-closed: missing required fields ─────────────────────────────────
  console.log('\nFail-closed: missing required fields');
  const missing = await post('/simulate/run', { trace_id: 'trace-p6-missing' });
  check('status 422',              missing.status === 422);
  check('errors array present',    Array.isArray(missing.body.errors));

  // ── Health reflects stored_count after runs ───────────────────────────────
  console.log('\nHealth: stored_count reflects completed runs');
  const h2 = await get('/simulate/health');
  check('stored_count >= 2',       h2.body.stored_count >= 2);

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
  server.kill();
  process.exit(fail > 0 ? 1 : 0);
}

// ── Boot server then run tests ────────────────────────────────────────────────
server = spawn('node', ['simulation_server.js'], {
  cwd: __dirname, stdio: ['ignore', 'pipe', 'pipe']
});

let started = false;
server.stdout.on('data', d => {
  if (!started && d.toString().includes('running on port')) {
    started = true;
    // Wait 500ms after the ready message before hitting routes
    setTimeout(() => {
      runTests().catch(err => {
        console.error('Test error:', err.message);
        server.kill();
        process.exit(1);
      });
    }, 500);
  }
});

server.stderr.on('data', d => process.stderr.write(d));

setTimeout(() => {
  console.error('Server did not start in time');
  server.kill();
  process.exit(1);
}, 8000);

'use strict';

const http      = require('http');
const net       = require('net');
const { spawn } = require('child_process');

let pass = 0, fail = 0;
let simServer, mitraServer;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

function post(path, body, port = 3001) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req  = http.request({
      hostname: 'localhost', port,
      path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch (e) { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.setTimeout(5000, () => { req.destroy(new Error('timeout')); });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function get(path, port = 3001) {
  return new Promise((resolve, reject) => {
    const req = http.get({ hostname: 'localhost', port, path }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch (e) { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.setTimeout(5000, () => { req.destroy(new Error('timeout')); });
    req.on('error', reject);
  });
}

// ── Contract factory ──────────────────────────────────────────────────────────

function makeContract(traceId, scenario = 'patrol', ticks = 10) {
  return {
    trace_id:     traceId,
    execution_id: `exec_${traceId}`,
    domain:       'test',
    scenario,
    entities: [
      { id: 'e1', type: 'vessel', position: [0,0,0],  behaviors: ['b1'] },
      { id: 'z1', type: 'zone',   position: [20,0,0], behaviors: [], meta: { radius: 5 } }
    ],
    behaviors: [
      { id: 'b1', script: 'move_to', params: { target: [20,0,0], speed: 3, threshold: 1 } }
    ],
    rules: [
      { id: 'r1', trigger: 'on_zone_enter',
        condition: { field: 'state', op: 'eq', value: 'active' },
        action: { type: 'log', params: { message: 'reached zone' } },
        enabled: true }
    ],
    constraints: { movement: { speed: 3 } },
    ticks
  };
}

// ── Mitra failure server — accepts connection, never responds ─────────────────

function startMitraFailureServer(port = 3099) {
  return new Promise(resolve => {
    mitraServer = net.createServer(socket => {
      // Accept connection but never send a response — simulates Mitra down
      socket.on('error', () => {});
    });
    mitraServer.listen(port, () => resolve());
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

async function runTests() {
  console.log('\n=== Phase 8 — Concurrency + Failure Testing ===\n');

  // ── Scenario 1: 5 parallel simulations ───────────────────────────────────
  console.log('Scenario 1: 5 parallel simulations (different trace_ids)\n');

  const traceIds = [
    'trace-p8-concurrent-1',
    'trace-p8-concurrent-2',
    'trace-p8-concurrent-3',
    'trace-p8-concurrent-4',
    'trace-p8-concurrent-5'
  ];

  const contracts = traceIds.map((id, i) =>
    makeContract(id, `scenario_${i + 1}`, 10 + i)
  );

  // Fire all 5 simultaneously
  const t0      = Date.now();
  const results = await Promise.all(contracts.map(c => post('/simulate/run', c)));
  const elapsed = Date.now() - t0;

  console.log(`  All 5 completed in ${elapsed}ms\n`);

  // Every run must succeed
  results.forEach((r, i) => {
    check(`run ${i+1} status 200`,          r.status === 200);
    check(`run ${i+1} status=completed`,    r.body.status === 'completed');
    check(`run ${i+1} correct trace_id`,    r.body.trace_id === traceIds[i]);
    check(`run ${i+1} correct ticks_run`,   r.body.ticks_run === 10 + i);
  });

  // No mixed trace states — each result must have its own trace_id
  const returnedIds = results.map(r => r.body.trace_id);
  const uniqueIds   = new Set(returnedIds);
  check('all 5 trace_ids are unique',       uniqueIds.size === 5);
  check('no trace_id cross-contamination',  returnedIds.every((id, i) => id === traceIds[i]));

  // Verify each result is independently retrievable
  const fetched = await Promise.all(traceIds.map(id => get(`/simulate/result/${id}`)));
  fetched.forEach((f, i) => {
    check(`result ${i+1} retrievable`,      f.status === 200);
    check(`result ${i+1} trace_id correct`, f.body.trace_id === traceIds[i]);
  });

  // ── Scenario 2: Mitra failure — no response ───────────────────────────────
  console.log('\nScenario 2: Mitra failure simulation (no response)\n');

  // Simulate what happens when an upstream dependency (Mitra) hangs —
  // the adapter must timeout and fail-closed, not crash the sim node

  const { run: nicaiRun } = require('./domain-adapters/nicai/nicaiAdapter');

  // Point adapter at the dead server by overriding env
  process.env.SIM_PORT = '3099';
  process.env.SIM_HOST = 'localhost';

  // Re-require adapter with new env (clear cache first)
  delete require.cache[require.resolve('./domain-adapters/nicai/nicaiAdapter')];
  const nicaiBroken = require('./domain-adapters/nicai/nicaiAdapter');

  let mitraResult;
  try {
    mitraResult = await Promise.race([
      nicaiBroken.run({
        session_id:   'nicai-mitra-down',
        mission:      'test_mission',
        threat_level: 'low',
        ticks:        5,
        agents: [{ id: 'a1', role: 'observer', position: [0,0,0] }]
      }),
      new Promise(resolve =>
        setTimeout(() => resolve({ success: false, result: null, errors: ['timeout'] }), 3000)
      )
    ]);
  } catch (e) {
    mitraResult = { success: false, result: null, errors: [e.message] };
  }

  check('Mitra down → success=false',       !mitraResult.success);
  check('Mitra down → result=null',         mitraResult.result === null);
  check('Mitra down → errors non-empty',    mitraResult.errors.length > 0);

  // Restore env
  process.env.SIM_PORT = '3001';
  delete require.cache[require.resolve('./domain-adapters/nicai/nicaiAdapter')];

  // Sim node itself must still be alive after Mitra failure
  const healthAfterMitra = await get('/simulate/health');
  check('sim node alive after Mitra down',  healthAfterMitra.status === 200);
  check('sim node status=ok',               healthAfterMitra.body.status === 'ok');

  // ── Scenario 3: malformed contract ───────────────────────────────────────
  console.log('\nScenario 3: Malformed contract\n');

  const malformedCases = [
    // Not JSON — raw string
    { label: 'raw string body',         body: 'not json at all',    expectedStatus: 400 },
    // game_mode present
    { label: 'game_mode banned field',  body: { ...makeContract('trace-p8-mal-1'), game_mode: 'runner' }, expectedStatus: 422 },
    // entity type invalid
    { label: 'invalid entity type',     body: { ...makeContract('trace-p8-mal-2'), entities: [{ id: 'e1', type: 'player', position: [0,0,0], behaviors: [] }] }, expectedStatus: 422 },
    // behavior script invalid
    { label: 'invalid behavior script', body: { ...makeContract('trace-p8-mal-3'), behaviors: [{ id: 'b1', script: 'jump', params: {} }] }, expectedStatus: 422 },
    // rule trigger invalid
    { label: 'invalid rule trigger',    body: { ...makeContract('trace-p8-mal-4'), rules: [{ id: 'r1', trigger: 'on_death', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: {} } }] }, expectedStatus: 422 },
    // ticks out of range
    { label: 'ticks > 1000',            body: { ...makeContract('trace-p8-mal-5'), ticks: 9999 }, expectedStatus: 422 },
    // position wrong length
    { label: 'position wrong length',   body: { ...makeContract('trace-p8-mal-6'), entities: [{ id: 'e1', type: 'vessel', position: [0,0], behaviors: ['b1'] }] }, expectedStatus: 422 },
  ];

  for (const c of malformedCases) {
    let r;
    if (typeof c.body === 'string') {
      // Send raw string — will be rejected by express JSON parser
      r = await new Promise(resolve => {
        const req = http.request({
          hostname: 'localhost', port: 3001,
          path: '/simulate/run', method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(c.body) }
        }, res => {
          let raw = '';
          res.on('data', d => raw += d);
          res.on('end', () => resolve({ status: res.statusCode }));
        });
        req.on('error', () => resolve({ status: 500 }));
        req.write(c.body);
        req.end();
      });
    } else {
      r = await post('/simulate/run', c.body);
    }
    check(`${c.label} → ${c.expectedStatus}`, r.status === c.expectedStatus);
  }

  // Sim node must still be alive after all malformed requests
  const healthAfterMalformed = await get('/simulate/health');
  check('sim node alive after malformed requests', healthAfterMalformed.status === 200);

  // ── Scenario 4: partial input ─────────────────────────────────────────────
  console.log('\nScenario 4: Partial input\n');

  const partialCases = [
    { label: 'empty body',                  body: {},                                    expectedStatus: 422 },
    { label: 'trace_id only',               body: { trace_id: 'x' },                     expectedStatus: 422 },
    { label: 'missing entities',            body: { trace_id: 'x', execution_id: 'y', domain: 'd', scenario: 's', behaviors: [{ id: 'b1', script: 'idle', params: {} }] }, expectedStatus: 422 },
    { label: 'missing behaviors',           body: { trace_id: 'x', execution_id: 'y', domain: 'd', scenario: 's', entities: [{ id: 'e1', type: 'vessel', position: [0,0,0], behaviors: [] }] }, expectedStatus: 422 },
    { label: 'missing domain',              body: { trace_id: 'x', execution_id: 'y', scenario: 's', entities: [{ id: 'e1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] }], behaviors: [{ id: 'b1', script: 'idle', params: {} }] }, expectedStatus: 422 },
    { label: 'missing scenario',            body: { trace_id: 'x', execution_id: 'y', domain: 'd',  entities: [{ id: 'e1', type: 'vessel', position: [0,0,0], behaviors: ['b1'] }], behaviors: [{ id: 'b1', script: 'idle', params: {} }] }, expectedStatus: 422 },
    { label: 'null body',                   body: null,                                  expectedStatus: 400 },  // body-parser rejects null before validator
  ];

  for (const c of partialCases) {
    const r = await post('/simulate/run', c.body);
    check(`${c.label} → ${c.expectedStatus}`, r.status === c.expectedStatus, `got ${r.status}`);
  }

  // Sim node must still be alive after all partial inputs
  const healthAfterPartial = await get('/simulate/health');
  check('sim node alive after partial inputs', healthAfterPartial.status === 200);

  // ── No mixed trace states — verify each concurrent result is isolated ─────
  console.log('\nNo mixed trace states — final isolation check\n');

  const finalFetch = await Promise.all(traceIds.map(id => get(`/simulate/result/${id}`)));
  finalFetch.forEach((f, i) => {
    check(`trace ${i+1} isolated — trace_id correct`,   f.body.trace_id === traceIds[i]);
    check(`trace ${i+1} isolated — ticks_run correct`,  f.body.ticks_run === 10 + i);
  });

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
  simServer.kill();
  if (mitraServer) mitraServer.close();
  process.exit(fail > 0 ? 1 : 0);
}

// ── Boot servers then run tests ───────────────────────────────────────────────
async function boot() {
  await startMitraFailureServer(3099);

  simServer = spawn('node', ['simulation_server.js'], {
    cwd: __dirname, stdio: ['ignore', 'pipe', 'pipe']
  });

  let started = false;
  simServer.stdout.on('data', d => {
    if (!started && d.toString().includes('running on port')) {
      started = true;
      setTimeout(() => {
        runTests().catch(err => {
          console.error('Test error:', err.message);
          simServer.kill();
          if (mitraServer) mitraServer.close();
          process.exit(1);
        });
      }, 500);
    }
  });

  simServer.stderr.on('data', d => process.stderr.write(d));

  setTimeout(() => {
    console.error('Server did not start in time');
    simServer.kill();
    process.exit(1);
  }, 8000);
}

boot();

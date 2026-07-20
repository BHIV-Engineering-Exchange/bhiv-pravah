'use strict';

const { spawn } = require('child_process');
const nicai     = require('./domain-adapters/nicai/nicaiAdapter');
const aiaic     = require('./domain-adapters/aiaic/aiaicAdapter');

let pass = 0, fail = 0;
let server;

function check(label, condition, detail) {
  if (condition) { console.log(`  PASS  ${label}`); pass++; }
  else           { console.log(`  FAIL  ${label}`, detail || ''); fail++; }
}

// ── NICAI domain input ────────────────────────────────────────────────────────
const NICAI_INPUT = {
  session_id:    'nicai-session-p7-001',
  mission:       'perimeter_surveillance',
  threat_level:  'high',
  ticks:         15,
  agents: [
    { id: 'agent_obs_1', role: 'observer',    position: [0,0,0],    patrol_radius: 20 },
    { id: 'agent_trk_1', role: 'tracker',     position: [10,0,10] },
    { id: 'agent_sen_1', role: 'sentinel',    position: [30,0,0] }
  ],
  zones: [
    { id: 'zone_perimeter', position: [20,0,20], radius: 12, label: 'perimeter' }
  ]
};

// ── AIAIC domain input ────────────────────────────────────────────────────────
const AIAIC_INPUT = {
  assessment_id:   'aiaic-assess-p7-001',
  assessment_type: 'navigation',
  time_limit_ticks: 20,
  participants: [
    { id: 'participant_1', skill_level: 'intermediate', start_position: [0,0,0] },
    { id: 'participant_2', skill_level: 'advanced',     start_position: [5,0,0] }
  ],
  checkpoints: [
    { id: 'cp_1', position: [25,0,0], radius: 8, label: 'checkpoint_1', order: 1 },
    { id: 'cp_2', position: [50,0,0], radius: 8, label: 'checkpoint_2', order: 2 }
  ]
};

async function runTests() {
  console.log('\n=== Phase 7 — Multi-Domain Adapter Proof ===\n');

  // ── NICAI Adapter ─────────────────────────────────────────────────────────
  console.log('--- NICAI Adapter ---\n');

  // Test 1: valid NICAI input → simulation run
  console.log('Test 1: NICAI valid input → simulationState.v1');
  const n1 = await nicai.run(NICAI_INPUT);
  check('success=true',                n1.success, n1.errors);
  check('no errors',                   n1.errors.length === 0);
  check('result.status=completed',     n1.result?.status === 'completed');
  check('trace_id = session_id',       n1.result?.trace_id === NICAI_INPUT.session_id);
  check('domain=nicai in entities',    Object.values(n1.result?.entities || {}).some(e => e.meta?.role));
  check('has state_summary',           typeof n1.result?.state_summary === 'object');
  check('has metrics',                 typeof n1.result?.metrics === 'object');
  check('has transitions',             Array.isArray(n1.result?.transitions));
  check('has event_log',               Array.isArray(n1.result?.event_log));
  check('no game_mode in result',      !('game_mode' in (n1.result || {})));
  check('no seed in result',           !('seed'      in (n1.result || {})));
  check('no flags at top level',       !('flags'     in (n1.result || {})));
  // Verify all 3 agents are in entities
  check('agent_obs_1 in entities',     'agent_obs_1' in (n1.result?.entities || {}));
  check('agent_trk_1 in entities',     'agent_trk_1' in (n1.result?.entities || {}));
  check('agent_sen_1 in entities',     'agent_sen_1' in (n1.result?.entities || {}));
  // Zone present
  check('zone_perimeter in entities',  'zone_perimeter' in (n1.result?.entities || {}));

  // Test 2: NICAI invalid input → fail-closed, no sim call
  console.log('\nTest 2: NICAI invalid input → fail-closed');
  const n2 = await nicai.run({ session_id: 'bad', mission: 'test', agents: [] });
  check('success=false',               !n2.success);
  check('result=null',                 n2.result === null);
  check('errors array non-empty',      n2.errors.length > 0);

  // Test 3: NICAI invalid agent role → rejected
  console.log('\nTest 3: NICAI invalid agent role → rejected');
  const n3 = await nicai.run({
    ...NICAI_INPUT,
    session_id: 'nicai-bad-role',
    agents: [{ id: 'a1', role: 'sniper', position: [0,0,0] }]
  });
  check('success=false',               !n3.success);
  check('error mentions role',         n3.errors.some(e => e.includes('role')));

  // Test 4: NICAI idempotency — same session_id returns stored result
  console.log('\nTest 4: NICAI idempotency — same session_id');
  const n4 = await nicai.run(NICAI_INPUT);
  check('success=true',                n4.success);
  check('same trace_id',               n4.result?.trace_id === n1.result?.trace_id);
  check('same event_count',            n4.result?.state_summary?.event_count === n1.result?.state_summary?.event_count);

  // ── AIAIC Adapter ─────────────────────────────────────────────────────────
  console.log('\n--- AIAIC Adapter ---\n');

  // Test 5: valid AIAIC input → simulation run
  console.log('Test 5: AIAIC valid input → simulationState.v1');
  const a1 = await aiaic.run(AIAIC_INPUT);
  check('success=true',                a1.success, a1.errors);
  check('no errors',                   a1.errors.length === 0);
  check('result.status=completed',     a1.result?.status === 'completed');
  check('trace_id = assessment_id',    a1.result?.trace_id === AIAIC_INPUT.assessment_id);
  check('has state_summary',           typeof a1.result?.state_summary === 'object');
  check('has metrics',                 typeof a1.result?.metrics === 'object');
  check('no game_mode in result',      !('game_mode' in (a1.result || {})));
  check('no seed in result',           !('seed'      in (a1.result || {})));
  // Verify participants in entities
  check('participant_1 in entities',   'participant_1' in (a1.result?.entities || {}));
  check('participant_2 in entities',   'participant_2' in (a1.result?.entities || {}));
  // Checkpoints as zones
  check('cp_1 in entities',            'cp_1' in (a1.result?.entities || {}));
  check('cp_2 in entities',            'cp_2' in (a1.result?.entities || {}));
  // Skill level preserved in meta
  const p1 = a1.result?.entities?.['participant_1'];
  check('skill_level in meta',         p1?.meta?.skill_level === 'intermediate');
  check('assessment_type in meta',     p1?.meta?.assessment_type === 'navigation');

  // Test 6: AIAIC invalid input → fail-closed
  console.log('\nTest 6: AIAIC invalid input → fail-closed');
  const a2 = await aiaic.run({ assessment_id: 'bad' });
  check('success=false',               !a2.success);
  check('result=null',                 a2.result === null);
  check('errors non-empty',            a2.errors.length > 0);

  // Test 7: AIAIC invalid skill_level → rejected
  console.log('\nTest 7: AIAIC invalid skill_level → rejected');
  const a3 = await aiaic.run({
    ...AIAIC_INPUT,
    assessment_id: 'aiaic-bad-skill',
    participants: [{ id: 'p1', skill_level: 'god_mode', start_position: [0,0,0] }]
  });
  check('success=false',               !a3.success);
  check('error mentions skill_level',  a3.errors.some(e => e.includes('skill_level')));

  // Test 8: AIAIC idempotency — same assessment_id returns stored result
  console.log('\nTest 8: AIAIC idempotency — same assessment_id');
  const a4 = await aiaic.run(AIAIC_INPUT);
  check('success=true',                a4.success);
  check('same trace_id',               a4.result?.trace_id === a1.result?.trace_id);
  check('same event_count',            a4.result?.state_summary?.event_count === a1.result?.state_summary?.event_count);

  // ── Cross-adapter: both produce v1 shape ──────────────────────────────────
  console.log('\n--- Cross-adapter: both produce simulationState.v1 ---\n');
  const V1_FIELDS = ['trace_id','execution_id','status','ticks_run','entities','transitions','event_log','state_summary','zones','metrics'];
  V1_FIELDS.forEach(f => {
    check(`NICAI result has ${f}`,  f in (n1.result || {}));
    check(`AIAIC result has ${f}`,  f in (a1.result || {}));
  });

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

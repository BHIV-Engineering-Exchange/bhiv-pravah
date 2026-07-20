'use strict';

/**
 * test_phase1_contract.js
 *
 * Phase 1 — Contract Lock Validation
 *
 * Runs 4 cases:
 *   1. ALLOW vessel  → valid contract produced
 *   2. Missing trace_id → fail loud
 *   3. Missing required field (entities) → fail loud
 *   4. Schema drift check — contract output vs engineExecutionContract.json required fields
 *
 * Run: node backend/domain-adapters/maritime/test_phase1_contract.js
 */

const { adaptVessel }  = require('./maritimeAdapter');
const { build }        = require('./contractBuilder');
const engineSchema     = require('../../engineExecutionContract.json');

const REQUIRED_BY_ENGINE = engineSchema.required; // ['execution_id','trace_id','game_mode','entities','physics','scoring']

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

// ─── Case 1: Valid vessel → contract produced ─────────────────────────────────
console.log('\n── Case 1: Valid vessel → contract produced ──────────────────');
{
  const vessel = { vessel_id: 'VESSEL_ALPHA', lat: 25.1, lon: 55.2, speed: 8, heading: 45, status: 'moving' };
  const adapted = adaptVessel(vessel, { trace_id: 'trace-phase1-test', execution_id: 'exec_phase1_001' });

  check('Adapter succeeded',        adapted.success, JSON.stringify(adapted.errors));

  const result = build(adapted.schema);

  check('Contract build succeeded', result.success, JSON.stringify(result.errors));

  if (result.success) {
    const c = result.contract;
    check('execution_id present',   !!c.execution_id);
    check('trace_id present',       !!c.trace_id);
    check('trace_id matches input', c.trace_id === 'trace-phase1-test');
    check('game_mode is open_scene',c.game_mode === 'open_scene');
    check('entities is array',      Array.isArray(c.entities) && c.entities.length > 0);
    check('physics.gravity is vec3',Array.isArray(c.physics.gravity) && c.physics.gravity.length === 3);
    check('scoring.rules present',  !!c.scoring && !!c.scoring.rules);
    check('scoring.end_conditions', Array.isArray(c.scoring.end_conditions));
    check('domain NOT in contract', c.domain === undefined, 'domain must be stripped from contract');
    check('decisionEnvelope NOT in contract', c.decisionEnvelope === undefined);

    // ── Schema drift check — every required engine field must be present ──
    console.log('\n── Schema Drift Check (contract vs engineExecutionContract.json) ──');
    REQUIRED_BY_ENGINE.forEach(field => {
      check(`Required field present: ${field}`, c[field] !== undefined && c[field] !== null);
    });

    console.log('\n── Contract Sample Output ────────────────────────────────────');
    console.log(JSON.stringify(c, null, 2));
  }
}

// ─── Case 2: Missing trace_id → fail loud ─────────────────────────────────────
console.log('\n── Case 2: Missing trace_id → fail loud ──────────────────────');
{
  const vessel = { vessel_id: 'VESSEL_BRAVO', lat: 25.3, lon: 55.4, speed: 5, heading: 90, status: 'moving' };
  const adapted = adaptVessel(vessel, { execution_id: 'exec_phase1_002' }); // no trace_id
  // Force remove trace_id to simulate missing
  adapted.schema.trace_id = null;

  const result = build(adapted.schema);
  check('Build correctly failed',   !result.success);
  check('Error mentions trace_id',  result.errors.some(e => e.includes('trace_id')), result.errors.join(', '));
  check('Contract is null',         result.contract === null);
}

// ─── Case 3: Missing entities → fail loud ─────────────────────────────────────
console.log('\n── Case 3: Missing entities → fail loud ──────────────────────');
{
  const vessel = { vessel_id: 'VESSEL_CHARLIE', lat: 25.5, lon: 55.1, speed: 3, heading: 180, status: 'moving' };
  const adapted = adaptVessel(vessel, { trace_id: 'trace-phase1-c3', execution_id: 'exec_phase1_003' });
  adapted.schema.entities = null; // simulate missing

  const result = build(adapted.schema);
  check('Build correctly failed',   !result.success);
  check('Error mentions entities',  result.errors.some(e => e.includes('entities')), result.errors.join(', '));
  check('Contract is null',         result.contract === null);
}

// ─── Case 4: Anchored vessel → health=0, speed clamped to 1 ──────────────────
console.log('\n── Case 4: Anchored vessel → player_params.health=0, speed=1 ─');
{
  const vessel = { vessel_id: 'VESSEL_DELTA', lat: 25.2, lon: 55.5, speed: 0, heading: 0, status: 'anchored' };
  const adapted = adaptVessel(vessel, { trace_id: 'trace-phase1-c4', execution_id: 'exec_phase1_004' });
  const result  = build(adapted.schema);

  check('Build succeeded',          result.success, JSON.stringify(result.errors));
  if (result.success) {
    check('player_params.health=0', result.contract.player_params.health === 0);
    check('movement.speed >= 1',    result.contract.movement.speed >= 1, `got ${result.contract.movement.speed}`);
  }
}

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log('\n══════════════════════════════════════════════');
console.log(`Phase 1 Contract Lock — ${passed + failed} checks`);
console.log(`  ✅ Passed : ${passed}`);
console.log(`  ❌ Failed : ${failed}`);
console.log(`  Status   : ${failed === 0 ? 'PHASE 1 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
console.log('══════════════════════════════════════════════\n');

process.exit(failed > 0 ? 1 : 0);

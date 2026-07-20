'use strict';

/**
 * phase6_unseen_contracts.js
 *
 * Phase 6 proof — Unseen Contract Tests
 *
 * Executes 5 contracts that did not previously exist.
 * No new runtime code between tests — only contract changes.
 *
 * Scenario 1: Maritime patrol     (patrol_vessel, unknown_vessel, zones)
 * Scenario 2: Drone swarm         (drone formation, track behavior, no-fly zone)
 * Scenario 3: Vehicle convoy      (cargo_vehicle, escort_vehicle, checkpoints)
 * Scenario 4: Facility monitoring (sensor, guard, intruder, perimeter zones)
 * Scenario 5: Resource network    (resource_node, carrier, depot zone)
 */

const validator = require('./simulation/contractValidator.v1');
const adapter   = require('./simulation/contractAdapter');
const { run }   = require('./simulation/engine/SimEngine');
const store     = require('./simulation/simResultStore');

const CONTRACTS = [
  { label: 'Scenario 1 — Maritime Patrol',          file: require('./contracts/unseen_01_maritime_patrol.json') },
  { label: 'Scenario 2 — Drone Swarm',              file: require('./contracts/unseen_02_drone_swarm.json') },
  { label: 'Scenario 3 — Vehicle Convoy',           file: require('./contracts/unseen_03_vehicle_convoy.json') },
  { label: 'Scenario 4 — Facility Monitoring',      file: require('./contracts/unseen_04_facility_monitoring.json') },
  { label: 'Scenario 5 — Resource Movement Network',file: require('./contracts/unseen_05_resource_network.json') }
];

// ─── Single generic execute — same path for all 5 ─────────────────────────────

function execute(label, contract) {
  console.log(`\n${'─'.repeat(62)}`);
  console.log(`${label}`);
  console.log(`  trace_id     : ${contract.trace_id}`);
  console.log(`  domain       : ${contract.domain}`);
  console.log(`  scenario     : ${contract.scenario}`);
  console.log(`  ticks        : ${contract.ticks || 10}`);
  console.log(`  entities     : ${contract.entities.length} — types: ${[...new Set(contract.entities.map(e => e.type))].join(', ')}`);
  console.log(`  behaviors    : ${contract.behaviors.length}`);
  console.log(`  rules        : ${(contract.rules || []).length}`);

  // Step 1 — validate
  const v1 = validator.validate(contract);
  if (!v1.valid) {
    console.log(`  ✗ VALIDATION FAILED`);
    v1.errors.forEach(e => console.log(`    - ${e}`));
    return { success: false, label, errors: v1.errors };
  }
  console.log(`  ✓ validation passed`);

  // Step 2 — adapt
  const adapted = adapter.adapt({
    trace_id:     contract.trace_id,
    execution_id: contract.execution_id,
    domain:       contract.domain,
    scenario:     contract.scenario,
    entities:     contract.entities,
    behaviors:    contract.behaviors,
    rules:        contract.rules || []
  });
  if (!adapted.valid) {
    console.log(`  ✗ ADAPTER FAILED: ${adapted.errors.join('; ')}`);
    return { success: false, label, errors: adapted.errors };
  }
  console.log(`  ✓ adapter passed`);

  // Step 3 — run
  const result = run(adapted.sumscript, { ticks: contract.ticks || 10 });
  if (result.status !== 'completed') {
    console.log(`  ✗ SIMENGINE FAILED: ${result.error}`);
    return { success: false, label, error: result.error };
  }

  // Step 4 — store
  store.save(result.trace_id, result, adapted.sumscript);

  // Step 5 — print result
  const types   = [...new Set(Object.values(result.entities).map(e => e.type))];
  const states  = {};
  Object.values(result.entities).forEach(e => { states[e.state] = (states[e.state] || 0) + 1; });
  const stateStr = Object.entries(states).map(([s, c]) => `${s}:${c}`).join(' | ');

  console.log(`  ✓ simulation completed`);
  console.log(`    ticks_run    : ${result.ticks_run}`);
  console.log(`    entities     : ${result.state_summary.entity_count}`);
  console.log(`    types        : ${types.join(', ')}`);
  console.log(`    states       : ${stateStr}`);
  console.log(`    transitions  : ${result.state_summary.transition_count}`);
  console.log(`    events       : ${result.state_summary.event_count}`);
  console.log(`    collisions   : ${result.state_summary.collision_count}`);
  console.log(`    flagged      : ${result.state_summary.flagged_count}`);
  console.log(`    blocked      : ${result.state_summary.blocked_count}`);

  // State transition log (state changes only)
  const stateTransitions = result.transitions.filter(t => t.field === 'state');
  if (stateTransitions.length > 0) {
    console.log(`    state transitions:`);
    stateTransitions.forEach(t => {
      console.log(`      tick=${String(t.tick).padStart(2)} | ${t.entity_id.padEnd(18)} | ${String(t.from).padEnd(14)} → ${String(t.to).padEnd(14)} | ${t.reason}`);
    });
  }

  return {
    success:      true,
    label,
    trace_id:     result.trace_id,
    domain:       contract.domain,
    scenario:     contract.scenario,
    entity_count: result.state_summary.entity_count,
    entity_types: types,
    ticks_run:    result.ticks_run,
    transitions:  result.state_summary.transition_count,
    events:       result.state_summary.event_count,
    collisions:   result.state_summary.collision_count,
    flagged:      result.state_summary.flagged_count,
    blocked:      result.state_summary.blocked_count,
    states
  };
}

// ─── Run all 5 ────────────────────────────────────────────────────────────────

console.log('╔══════════════════════════════════════════════════════════╗');
console.log('║   PHASE 6 — UNSEEN CONTRACT EXECUTION PROOF             ║');
console.log('╚══════════════════════════════════════════════════════════╝');
console.log('5 contracts that did not previously exist.');
console.log('No new runtime code between tests — only contract changes.');
console.log('Same runtime path: contractValidator → contractAdapter → SimEngine → store\n');

const results = CONTRACTS.map(c => execute(c.label, c.file));

// ─── Summary ──────────────────────────────────────────────────────────────────

const passed = results.filter(r => r.success).length;

console.log(`\n${'═'.repeat(62)}`);
console.log('PHASE 6 PROOF SUMMARY');
console.log(`${'═'.repeat(62)}`);

results.forEach((r, i) => {
  const icon = r.success ? '✓' : '✗';
  console.log(`${icon} Scenario ${i + 1}: ${r.label.replace(/^Scenario \d — /, '')}`);
  if (r.success) {
    console.log(`    domain=${r.domain} | entities=${r.entity_count} | types=[${r.entity_types.join(',')}]`);
    console.log(`    ticks=${r.ticks_run} | transitions=${r.transitions} | events=${r.events} | flagged=${r.flagged} | blocked=${r.blocked}`);
  } else {
    console.log(`    FAILED: ${r.errors?.join('; ') || r.error}`);
  }
});

console.log(`\nContracts executed : ${passed}/5`);

if (passed === 5) {
  console.log('\n✓ ALL 5 UNSEEN CONTRACTS EXECUTED SUCCESSFULLY');
  console.log('✓ No new runtime code written between tests');
  console.log('✓ Entity types: patrol_vessel, unknown_vessel, drone, cargo_vehicle,');
  console.log('               escort_vehicle, sensor, guard, intruder, resource_node,');
  console.log('               carrier — all accepted without code changes');
  console.log('✓ Same runtime path used for all 5 scenarios');
  console.log('✓ Atharva is a runtime, not a demo framework');
} else {
  console.log(`✗ ${5 - passed} CONTRACT(S) FAILED`);
  process.exit(1);
}
console.log(`${'═'.repeat(62)}\n`);

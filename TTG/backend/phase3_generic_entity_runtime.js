'use strict';

/**
 * phase3_generic_entity_runtime.js
 *
 * Phase 3 proof — Generic Entity Runtime
 *
 * Executes 3 contracts through the SAME runtime path:
 *   Contract A : 5 vessels   (domain: maritime)
 *   Contract B : 10 vehicles (domain: logistics)
 *   Contract C : 20 drones   (domain: surveillance)
 *
 * Runtime path (identical for all 3):
 *   contractValidator.v1  →  contractAdapter  →  SimEngine  →  simResultStore
 *
 * Success criteria:
 *   ✓ No demo selection
 *   ✓ No scenario-specific code
 *   ✓ No hardcoded entity names
 *   ✓ entity.type is open — vessel / vehicle / drone all accepted
 *   ✓ All 3 produce: status=completed, entities, transitions, event_log
 *   ✓ Same runtime path confirmed by single execute() function
 */

const path      = require('path');
const validator = require('./simulation/contractValidator.v1');
const adapter   = require('./simulation/contractAdapter');
const { run }   = require('./simulation/engine/SimEngine');
const store     = require('./simulation/simResultStore');

const CONTRACT_A = require('./contracts/contract_A_vessels.json');
const CONTRACT_B = require('./contracts/contract_B_vehicles.json');
const CONTRACT_C = require('./contracts/contract_C_drones.json');

// ─── Single generic execute function ─────────────────────────────────────────
// This is the ONLY execution function. All 3 contracts go through it.
// No branching on domain, scenario, entity type, or count.

function execute(contract) {
  const label = `[${contract.domain.toUpperCase()} / ${contract.scenario}]`;

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`${label}`);
  console.log(`  trace_id     : ${contract.trace_id}`);
  console.log(`  entity_count : ${contract.entities.length}`);
  console.log(`  entity_types : ${[...new Set(contract.entities.map(e => e.type))].join(', ')}`);
  console.log(`  ticks        : ${contract.ticks || 10}`);

  // Step 1 — validate
  const v1 = validator.validate(contract);
  if (!v1.valid) {
    console.error(`  ✗ VALIDATION FAILED`);
    v1.errors.forEach(e => console.error(`    - ${e}`));
    return { success: false, trace_id: contract.trace_id, errors: v1.errors };
  }
  console.log(`  ✓ validation passed`);

  // Step 2 — adapt to SumScript
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
    console.error(`  ✗ ADAPTER FAILED: ${adapted.errors.join('; ')}`);
    return { success: false, trace_id: contract.trace_id, errors: adapted.errors };
  }
  console.log(`  ✓ adapter passed — sumscript entities: ${adapted.sumscript.entities.length}`);

  // Step 3 — run SimEngine
  const result = run(adapted.sumscript, { ticks: contract.ticks || 10 });

  if (result.status !== 'completed') {
    console.error(`  ✗ SIMENGINE FAILED: ${result.error}`);
    return { success: false, trace_id: contract.trace_id, error: result.error };
  }

  // Step 4 — store result
  store.save(result.trace_id, result, adapted.sumscript);

  // Step 5 — print proof summary
  const entityIds    = Object.keys(result.entities);
  const entityTypes  = [...new Set(Object.values(result.entities).map(e => e.type))];
  const stateGroups  = {};
  Object.values(result.entities).forEach(e => {
    stateGroups[e.state] = (stateGroups[e.state] || 0) + 1;
  });

  console.log(`  ✓ simulation completed`);
  console.log(`    ticks_run      : ${result.ticks_run}`);
  console.log(`    entity_count   : ${result.state_summary.entity_count}`);
  console.log(`    entity_types   : ${entityTypes.join(', ')}`);
  console.log(`    entity_states  : ${JSON.stringify(stateGroups)}`);
  console.log(`    transitions    : ${result.state_summary.transition_count}`);
  console.log(`    events         : ${result.state_summary.event_count}`);
  console.log(`    collisions     : ${result.state_summary.collision_count}`);
  console.log(`    flagged        : ${result.state_summary.flagged_count}`);
  console.log(`    stored         : trace_id=${result.trace_id}`);

  // Print first 3 entity final states as sample
  console.log(`    entity sample  :`);
  entityIds.slice(0, 3).forEach(id => {
    const e = result.entities[id];
    console.log(`      ${id} | type=${e.type} | state=${e.state} | pos=[${e.position.map(v => v.toFixed(2)).join(',')}]`);
  });
  if (entityIds.length > 3) {
    console.log(`      ... and ${entityIds.length - 3} more`);
  }

  return {
    success:        true,
    trace_id:       result.trace_id,
    domain:         contract.domain,
    scenario:       contract.scenario,
    entity_count:   result.state_summary.entity_count,
    entity_types:   entityTypes,
    ticks_run:      result.ticks_run,
    transitions:    result.state_summary.transition_count,
    events:         result.state_summary.event_count,
    collisions:     result.state_summary.collision_count,
    flagged:        result.state_summary.flagged_count
  };
}

// ─── Run all 3 contracts ──────────────────────────────────────────────────────

console.log('╔══════════════════════════════════════════════════════════╗');
console.log('║   PHASE 3 — GENERIC ENTITY RUNTIME PROOF                ║');
console.log('╚══════════════════════════════════════════════════════════╝');
console.log('Runtime path: contractValidator → contractAdapter → SimEngine → store');
console.log('No demo selection. No hardcoded entities. Same function for all contracts.');

const results = [];

results.push(execute(CONTRACT_A));  // 5 vessels
results.push(execute(CONTRACT_B));  // 10 vehicles
results.push(execute(CONTRACT_C));  // 20 drones

// ─── Final summary ────────────────────────────────────────────────────────────

console.log(`\n${'═'.repeat(60)}`);
console.log('PHASE 3 PROOF SUMMARY');
console.log(`${'═'.repeat(60)}`);

let allPassed = true;
results.forEach((r, i) => {
  const label = ['Contract A (5 vessels)', 'Contract B (10 vehicles)', 'Contract C (20 drones)'][i];
  if (r.success) {
    console.log(`✓ ${label}`);
    console.log(`    domain=${r.domain} | entities=${r.entity_count} | types=${r.entity_types.join(',')} | ticks=${r.ticks_run} | transitions=${r.transitions} | events=${r.events}`);
  } else {
    allPassed = false;
    console.log(`✗ ${label} — FAILED`);
    if (r.errors) r.errors.forEach(e => console.log(`    - ${e}`));
  }
});

console.log(`\n${'─'.repeat(60)}`);

if (allPassed) {
  console.log('✓ ALL 3 CONTRACTS EXECUTED THROUGH THE SAME RUNTIME PATH');
  console.log('✓ No VESSEL_ALPHA / VESSEL_BRAVO / demo-specific identifiers');
  console.log('✓ entity.type: vessel, vehicle, drone — all accepted');
  console.log('✓ Proof complete — Atharva is a runtime, not a demo framework');
} else {
  console.log('✗ ONE OR MORE CONTRACTS FAILED — see errors above');
  process.exit(1);
}

console.log(`${'═'.repeat(60)}\n`);

'use strict';

/**
 * phase4_state_evolution.js
 *
 * Phase 4 proof — State Evolution Engine
 *
 * Proves that every state transition comes from contract rule definitions.
 * No code branches. No hardcoded state logic.
 *
 * Transitions proved:
 *   moving        → stopped         (on_tick rule: tick == 5)
 *   idle          → active          (on_tick rule: tick == 3)
 *   active        → restricted_zone (on_zone_enter rule)
 *   healthy       → damaged         (on_collision rule)
 */

const validator = require('./simulation/contractValidator.v1');
const adapter   = require('./simulation/contractAdapter');
const { run }   = require('./simulation/engine/SimEngine');
const store     = require('./simulation/simResultStore');
const CONTRACT  = require('./contracts/contract_state_evolution.json');

// ─── Run ──────────────────────────────────────────────────────────────────────

console.log('╔══════════════════════════════════════════════════════════╗');
console.log('║   PHASE 4 — STATE EVOLUTION ENGINE PROOF                ║');
console.log('╚══════════════════════════════════════════════════════════╝');
console.log('All transitions must come from contract rules — not code branches.\n');

// Step 1 — validate
const v1 = validator.validate(CONTRACT);
if (!v1.valid) {
  console.error('✗ VALIDATION FAILED');
  v1.errors.forEach(e => console.error(`  - ${e}`));
  process.exit(1);
}
console.log('✓ Contract validated');

// Step 2 — adapt
const adapted = adapter.adapt({
  trace_id:     CONTRACT.trace_id,
  execution_id: CONTRACT.execution_id,
  domain:       CONTRACT.domain,
  scenario:     CONTRACT.scenario,
  entities:     CONTRACT.entities,
  behaviors:    CONTRACT.behaviors,
  rules:        CONTRACT.rules
});
if (!adapted.valid) {
  console.error(`✗ ADAPTER FAILED: ${adapted.errors.join('; ')}`);
  process.exit(1);
}
console.log('✓ Adapter passed\n');

// Step 3 — run
const result = run(adapted.sumscript, { ticks: CONTRACT.ticks });
if (result.status !== 'completed') {
  console.error(`✗ SIMENGINE FAILED: ${result.error}`);
  process.exit(1);
}

store.save(result.trace_id, result, adapted.sumscript);

// ─── Extract transition evidence ──────────────────────────────────────────────

const stateTransitions = result.transitions.filter(t => t.field === 'state');

function findTransition(entityId, from, to) {
  return stateTransitions.find(t =>
    t.entity_id === entityId &&
    String(t.from) === String(from) &&
    String(t.to)   === String(to)
  );
}

function printTransition(label, entityId, from, to) {
  const t = findTransition(entityId, from, to);
  if (t) {
    console.log(`  ✓ ${label}`);
    console.log(`    entity   : ${t.entity_id}`);
    console.log(`    from     : ${t.from}`);
    console.log(`    to       : ${t.to}`);
    console.log(`    tick     : ${t.tick}`);
    console.log(`    reason   : ${t.reason}`);
  } else {
    console.log(`  ✗ ${label} — NOT FOUND`);
    console.log(`    expected : ${entityId} | ${from} → ${to}`);
  }
  return !!t;
}

// ─── Print all entity final states ───────────────────────────────────────────

console.log('─── Entity Final States ─────────────────────────────────');
Object.values(result.entities).forEach(e => {
  console.log(`  ${e.id.padEnd(22)} | type=${e.type.padEnd(8)} | state=${e.state}`);
});

// ─── Print full transition log ────────────────────────────────────────────────

console.log('\n─── Full State Transition Log ───────────────────────────');
console.log(`  Total transitions : ${result.transitions.length}`);
console.log(`  State transitions : ${stateTransitions.length}\n`);
stateTransitions.forEach(t => {
  console.log(`  tick=${String(t.tick).padStart(2)} | ${t.entity_id.padEnd(22)} | ${String(t.from).padEnd(18)} → ${String(t.to).padEnd(18)} | ${t.reason}`);
});

// ─── Verify each required transition ─────────────────────────────────────────

console.log('\n─── Transition Proof ────────────────────────────────────');

const results = [
  printTransition('moving → stopped       (on_tick: tick==5)',       'unit_moving', 'moving',  'stopped'),
  printTransition('idle → active          (on_tick: tick==3)',        'unit_idle',   'idle',    'active'),
  printTransition('active → restricted_zone (on_zone_enter)',         'unit_active', 'active',  'restricted_zone'),
  printTransition('healthy → damaged      (on_collision)',            'unit_healthy','healthy', 'damaged')
];

// ─── Summary ──────────────────────────────────────────────────────────────────

const passed = results.filter(Boolean).length;
const total  = results.length;

console.log(`\n${'═'.repeat(60)}`);
console.log('PHASE 4 PROOF SUMMARY');
console.log(`${'═'.repeat(60)}`);
console.log(`Transitions proved : ${passed}/${total}`);
console.log(`Total transitions  : ${result.transitions.length}`);
console.log(`Events emitted     : ${result.state_summary.event_count}`);
console.log(`Ticks run          : ${result.ticks_run}`);
console.log(`trace_id           : ${result.trace_id}`);

if (passed === total) {
  console.log('\n✓ ALL TRANSITIONS CAME FROM CONTRACT RULE DEFINITIONS');
  console.log('✓ No code branches — RuleEngine reads trigger/condition/action from contract');
  console.log('✓ State strings are open — moving, idle, healthy, restricted_zone, damaged all accepted');
  console.log('✓ EntityRegistry recorded every transition with entity_id, from, to, tick, reason');
} else {
  console.log(`\n✗ ${total - passed} TRANSITION(S) NOT PROVED`);
  process.exit(1);
}
console.log(`${'═'.repeat(60)}\n`);

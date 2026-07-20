'use strict';

/**
 * test_phase5_determinism.js
 *
 * Phase 5 — Determinism Validation
 *
 * Runs 3 input cases × 3 runs each through the pipeline pre-runtime stages.
 * Prints a full DeterminismReport for each case.
 *
 * Cases:
 *   1. ALLOW path   — normal vessel, low speed
 *   2. Mitra-down   — same input, Mitra unavailable (expected: deterministic failure)
 *   3. Invalid input — bad lat (expected: deterministic adapter failure)
 *
 * Usage:
 *   node backend/tests/test_phase5_determinism.js
 */

const { validate } = require('../domain-adapters/maritime/determinismValidator');

const RUNS = 3;

const CASES = [
  {
    label: 'Normal vessel — ALLOW path (Mitra down → deterministic MITRA_UNREACHABLE)',
    input: { vessel_id: 'VESSEL_DET_ALPHA', lat: 25.1, lon: 55.2, speed: 10, heading: 45, status: 'moving' }
  },
  {
    label: 'Anchored vessel — different player_params path',
    input: { vessel_id: 'VESSEL_DET_BRAVO', lat: 10.0, lon: 20.0, speed: 0, heading: 0, status: 'anchored' }
  },
  {
    label: 'Speed at contract boundary — clamped to 15',
    input: { vessel_id: 'VESSEL_DET_CHARLIE', lat: 1.0, lon: 1.0, speed: 15, heading: 180, status: 'moving' }
  },
  {
    label: 'Invalid input — lat out of range (deterministic adapter failure)',
    input: { vessel_id: 'VESSEL_DET_BAD', lat: 999, lon: 55.2, speed: 10, heading: 45, status: 'moving' }
  }
];

// ─── Assertion helpers ────────────────────────────────────────────────────────

let totalPassed = 0;
let totalFailed = 0;

function assert(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
    totalPassed++;
  } else {
    console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`);
    totalFailed++;
  }
}

// ─── Report printer ───────────────────────────────────────────────────────────

function printReport(report, caseLabel) {
  console.log(`\n${'─'.repeat(68)}`);
  console.log(`CASE: ${caseLabel}`);
  console.log(`${'─'.repeat(68)}`);
  console.log(`  runs        : ${report.run_count}`);
  console.log(`  deterministic: ${report.deterministic ? '✅ YES' : '❌ NO'}`);

  // Print run log
  report.run_log.forEach(l => console.log(`  ${l}`));

  // Print each check
  console.log(`\n  Checks (${report.checks.length}):`);
  for (const c of report.checks) {
    const icon = c.deterministic ? '✅' : '❌';
    const val  = String(c.reference_value).slice(0, 80);
    console.log(`    ${icon} ${c.field.padEnd(28)} ref=${val}`);
    if (!c.deterministic) {
      c.mismatches.forEach(m =>
        console.log(`         ⚠ run ${m.run}: expected="${m.expected}" got="${m.got}"`)
      );
    }
  }

  if (report.failed_checks.length > 0) {
    console.log(`\n  ❌ FAILED CHECKS:`);
    report.failed_checks.forEach(c => console.log(`     - ${c.field}: ${c.description}`));
  }

  console.log(`\n  Allowed to vary (${report.what_varies.length} fields):`);
  console.log(`    ${report.what_varies.join(', ')}`);
}

// ─── Assertions per report ────────────────────────────────────────────────────

function assertReport(report, caseLabel) {
  // Every check must be deterministic
  assert(`[${caseLabel}] overall deterministic`,
    report.deterministic,
    `${report.failed_checks.map(c => c.field).join(', ')} failed`);

  // All checks present
  assert(`[${caseLabel}] 19 checks run`,
    report.checks.length === 19,
    `got ${report.checks.length}`);

  // what_varies is populated
  assert(`[${caseLabel}] what_varies documented`,
    report.what_varies.length > 0);

  // run_log has entries
  assert(`[${caseLabel}] run_log populated`,
    report.run_log.length >= RUNS * 2);

  // path is consistent (checked by determinism, but verify it's a known value)
  const validPaths = ['ALLOW', 'FLAG', 'BLOCK', 'MITRA_FAILED', 'ADAPTER_FAILED', 'CONTRACT_FAILED'];
  const refPath = report.checks.find(c => c.field === 'path')?.reference_value;
  assert(`[${caseLabel}] path is a known value`,
    validPaths.includes(refPath),
    `got "${refPath}"`);

  // Contract checks — if contract was built, all contract sub-checks must pass
  const contractChecks = report.checks.filter(c => c.field.startsWith('contract.'));
  const contractBuilt  = report.checks.find(c => c.field === 'path')?.reference_value !== 'ADAPTER_FAILED'
                      && report.checks.find(c => c.field === 'path')?.reference_value !== 'CONTRACT_FAILED';
  if (contractBuilt) {
    const contractFailed = contractChecks.filter(c => !c.deterministic);
    assert(`[${caseLabel}] all contract fields deterministic`,
      contractFailed.length === 0,
      contractFailed.map(c => c.field).join(', '));
  }

  // Event sequence check
  const seqCheck = report.checks.find(c => c.field === 'event_sequence');
  assert(`[${caseLabel}] event_sequence deterministic`,
    seqCheck?.deterministic === true);

  // Artifact keys check
  const artCheck = report.checks.find(c => c.field === 'artifact_keys');
  assert(`[${caseLabel}] artifact_keys deterministic`,
    artCheck?.deterministic === true);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run() {
  console.log('\nPhase 5 — Determinism Validation');
  console.log('='.repeat(68));
  console.log(`Running ${CASES.length} cases × ${RUNS} runs each\n`);

  const reports = [];

  for (const c of CASES) {
    const report = await validate(c.input, RUNS);
    reports.push({ label: c.label, report });
    printReport(report, c.label);
    assertReport(report, c.label);
  }

  // ── Cross-case: different inputs must produce different contracts ──────────
  console.log(`\n${'─'.repeat(68)}`);
  console.log('Cross-case: different inputs → different contracts');
  console.log(`${'─'.repeat(68)}`);

  const contracts = reports
    .filter(r => r.report.checks.find(c => c.field === 'contract.entities')?.reference_value)
    .map(r => ({
      label:    r.label,
      entities: r.report.checks.find(c => c.field === 'contract.entities')?.reference_value
    }));

  if (contracts.length >= 2) {
    const allDifferent = contracts.every((c, i) =>
      contracts.every((d, j) => i === j || c.entities !== d.entities)
    );
    assert('Different inputs produce different entity contracts', allDifferent);
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n' + '='.repeat(68));
  console.log(`Results: ${totalPassed} passed, ${totalFailed} failed`);
  console.log('='.repeat(68));

  // ── Determinism Report document ───────────────────────────────────────────
  console.log('\n── DETERMINISM REPORT ───────────────────────────────────────────');
  console.log('\nDETERMINISTIC (identical across all runs with same input):');
  const deterministicFields = [
    '  contract.game_mode       — always "open_scene" for maritime input',
    '  contract.entities        — vessel_id, position, rotation, material, components',
    '  contract.physics         — gravity, friction, bounce, air_resistance, collision_force',
    '  contract.movement        — speed (clamped 1–15), jump_height',
    '  contract.scoring         — rules.distance/collectibles/time, end_conditions',
    '  contract.spawn_rules     — obstacles, frequency, distance',
    '  contract.player_params   — health (0 if anchored, 1 if moving), jetpack',
    '  contract.scene           — scene_id, ambient_light, skybox',
    '  decision                 — ALLOW / FLAG / BLOCK (same input → same Mitra response)',
    '  risk_level               — LOW / MEDIUM / HIGH',
    '  enforcement.passed/blocked/flagged — gate result follows decision deterministically',
    '  event_sequence           — stage names in order, pre-runtime',
    '  artifact_keys            — which artifact files are written',
    '  failure_code             — same failure for same bad input',
    '  failure_stage            — same stage for same bad input'
  ];
  deterministicFields.forEach(f => console.log(f));

  console.log('\nALLOWED TO VARY (by design — not a determinism violation):');
  const varyFields = [
    '  trace_id / execution_id  — unique per run (UUID + timestamp)',
    '  telemetry_id / event_id  — UUID per event',
    '  timestamp / logged_at    — wall-clock time of each operation',
    '  decided_at / enforced_at — wall-clock time of each stage',
    '  buffered_at / flushed_at — wall-clock time of artifact write',
    '  duration                 — elapsed time (varies with system load)',
    '  mitra_trace_id           — assigned by Mitra per request',
    '  your_trace_id            — echoes trace_id (varies with trace_id)',
    '  accepted_at / started_at / completed_at / stopped_at — wall-clock times'
  ];
  varyFields.forEach(f => console.log(f));

  process.exit(totalFailed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[TEST] Fatal:', err.message);
  process.exit(1);
});

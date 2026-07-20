'use strict';

/**
 * test_phase2_enforcement.js
 *
 * Phase 2 — Decision + Enforcement Verification
 *
 * Tests every enforcement path:
 *   1. ALLOW  → passed=true, execution may proceed
 *   2. FLAG   → passed=false, execution STOPS
 *   3. BLOCK  → passed=false, execution STOPS
 *   4. No decisionEnvelope → BLOCK (fail-closed)
 *   5. Stub source → BLOCK (stub never reaches execution)
 *   6. Unknown decision value → BLOCK (fail-closed)
 *   7. Mitra unreachable + STUB_ALLOWED=false → evaluate() fails, no envelope
 *   8. trace_id missing → mitraClient.evaluate() fails immediately
 *
 * Run: node backend/domain-adapters/maritime/test_phase2_enforcement.js
 */

const { enforce, getFlagLog, _clearFlagLog } = require('./enforcementGate');
const mitraClient = require('./mitraClient');

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

// Helper — build a minimal schema with a given decisionEnvelope
function _schema(decision, source = 'mitra', extra = {}) {
  return {
    trace_id:     'trace-p2-test',
    execution_id: 'exec_p2_001',
    decisionEnvelope: decision ? {
      decision,
      risk_level:     decision === 'ALLOW' ? 'LOW' : decision === 'FLAG' ? 'MEDIUM' : 'HIGH',
      confidence:     0.95,
      reason:         `Test decision: ${decision}`,
      mitra_trace_id: 'mitra-trace-001',
      your_trace_id:  'trace-p2-test',
      decided_at:     Date.now(),
      source
    } : null,
    ...extra
  };
}

// ─── Case 1: ALLOW → passed=true ─────────────────────────────────────────────
console.log('\n── Case 1: ALLOW → passed=true, execution proceeds ───────────');
{
  const result = enforce(_schema('ALLOW'));
  check('passed=true',          result.passed === true);
  check('blocked=false',        result.blocked === false);
  check('flagged=false',        result.flagged === false);
  check('decision=ALLOW',       result.decision === 'ALLOW');
  check('source preserved',     result.source === 'mitra');
  check('enforced_at present',  typeof result.enforced_at === 'number');
  check('trace_id preserved',   result.trace_id === 'trace-p2-test');
}

// ─── Case 2: FLAG → passed=false, execution STOPS ────────────────────────────
console.log('\n── Case 2: FLAG → passed=false, execution STOPS ──────────────');
{
  _clearFlagLog();
  const result = enforce(_schema('FLAG'));
  check('passed=false',         result.passed === false);
  check('blocked=false',        result.blocked === false);
  check('flagged=true',         result.flagged === true);
  check('decision=FLAG',        result.decision === 'FLAG');
  check('enforced_at present',  typeof result.enforced_at === 'number');
  check('flag logged',          getFlagLog().length === 1);
  check('flag log has trace_id',getFlagLog()[0].trace_id === 'trace-p2-test');
}

// ─── Case 3: BLOCK → passed=false, execution STOPS ───────────────────────────
console.log('\n── Case 3: BLOCK → passed=false, execution STOPS ─────────────');
{
  const result = enforce(_schema('BLOCK'));
  check('passed=false',         result.passed === false);
  check('blocked=true',         result.blocked === true);
  check('flagged=false',        result.flagged === false);
  check('decision=BLOCK',       result.decision === 'BLOCK');
  check('code=POLICY_VIOLATION',result.code === 'POLICY_VIOLATION');
  check('enforced_at present',  typeof result.enforced_at === 'number');
}

// ─── Case 4: No decisionEnvelope → BLOCK (fail-closed) ───────────────────────
console.log('\n── Case 4: No decisionEnvelope → BLOCK (fail-closed) ─────────');
{
  const result = enforce({ trace_id: 'trace-p2-c4', execution_id: 'exec_p2_004' });
  check('passed=false',         result.passed === false);
  check('blocked=true',         result.blocked === true);
  check('code=NO_ENVELOPE',     result.code === 'NO_ENVELOPE');
}

// ─── Case 5: source=stub → BLOCK (stub never reaches execution) ──────────────
console.log('\n── Case 5: source=stub → BLOCK (stub never reaches execution) ');
{
  const result = enforce(_schema('ALLOW', 'stub')); // even ALLOW from stub is blocked
  check('passed=false',         result.passed === false);
  check('blocked=true',         result.blocked === true);
  check('code=STUB_DECISION',   result.code === 'STUB_DECISION');
}

// ─── Case 6: Unknown decision value → BLOCK (fail-closed) ────────────────────
console.log('\n── Case 6: Unknown decision value → BLOCK (fail-closed) ───────');
{
  const schema = _schema('ALLOW'); // start valid then corrupt
  schema.decisionEnvelope.decision = 'MAYBE';
  const result = enforce(schema);
  check('passed=false',           result.passed === false);
  check('blocked=true',           result.blocked === true);
  check('code=UNKNOWN_DECISION',  result.code === 'UNKNOWN_DECISION');
}

// ─── Case 7: Mitra unreachable + STUB_ALLOWED=false → evaluate() fails ───────
console.log('\n── Case 7: Mitra unreachable + STUB_ALLOWED=false → fail loud ─');
{
  // Ensure stub is off (default)
  delete process.env.MITRA_STUB_ALLOWED;

  mitraClient.evaluate({
    trace_id:     'trace-p2-c7',
    execution_id: 'exec_p2_007',
    domain: { vessel_id: 'V007', speed: 5, status: 'moving', lat: 25.1, lon: 55.2 }
  }).then(result => {
    check('evaluate failed (no silent fallback)', result.success === false);
    check('error message present',               typeof result.error === 'string' && result.error.length > 0);
    check('envelope is null',                    result.envelope === null);

    // ─── Case 8: Missing trace_id → evaluate() fails immediately ─────────────
    console.log('\n── Case 8: Missing trace_id → evaluate() fails immediately ───');
    return mitraClient.evaluate({ execution_id: 'exec_p2_008' }); // no trace_id
  }).then(result => {
    check('evaluate failed',        result.success === false);
    check('error mentions trace_id',result.error.includes('trace_id'));
    check('envelope is null',       result.envelope === null);

    // ─── Summary ──────────────────────────────────────────────────────────────
    console.log('\n══════════════════════════════════════════════════════');
    console.log(`Phase 2 Enforcement — ${passed + failed} checks`);
    console.log(`  ✅ Passed : ${passed}`);
    console.log(`  ❌ Failed : ${failed}`);
    console.log(`  Status   : ${failed === 0 ? 'PHASE 2 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
    console.log('══════════════════════════════════════════════════════\n');
    process.exit(failed > 0 ? 1 : 0);
  }).catch(err => {
    console.error('[TEST] Unexpected error:', err.message);
    process.exit(1);
  });
}

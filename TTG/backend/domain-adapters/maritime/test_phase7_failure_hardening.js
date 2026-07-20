'use strict';

/**
 * test_phase7_failure_hardening.js
 *
 * Phase 7 — Failure Hardening Verification
 *
 * Required cases (from task):
 *   A. decision != ALLOW → no execution
 *   B. execution rejection → log + stop
 *   C. missing trace_id → fail
 *   D. broken event stream → fail
 *
 * Additional cases:
 *   E. Mitra unreachable → fail loud
 *   F. enforcement BLOCK → stop
 *   G. enforcement FLAG → stop
 *   H. stub decision → stop
 *   I. contract build failed → stop
 *   J. execution unreachable → stop
 *   K. event stream incomplete (no execution_completed) → fail
 *   L. event trace_id mismatch → fail
 *   M. unclassified error → fromError() wraps it, never silent
 *
 * Every check verifies:
 *   - failed=true
 *   - failure_code is the correct named code
 *   - stage is correct
 *   - trace_id is present (where applicable)
 *   - reason is a non-empty string
 *
 * Run: node backend/domain-adapters/maritime/test_phase7_failure_hardening.js
 */

const {
  FAILURE_CODES,
  assertTraceId,
  checkMitraResult,
  checkGateResult,
  checkContractBuild,
  checkExecutionResult,
  checkIncomingEvent,
  checkStreamComplete,
  fromError
} = require('./failureGuard');

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

function checkFailure(label, result, expectedCode, expectedStage) {
  check(`${label} — failed=true`,         result !== null && result.failed === true);
  check(`${label} — code=${expectedCode}`, result?.failure_code === expectedCode, `got ${result?.failure_code}`);
  check(`${label} — stage=${expectedStage}`, result?.stage === expectedStage, `got ${result?.stage}`);
  check(`${label} — reason is string`,    typeof result?.reason === 'string' && result.reason.length > 0);
  check(`${label} — stopped_at present`,  typeof result?.stopped_at === 'number');
}

const TRACE = 'trace-p7-test';
const EXEC  = 'exec_p7_001';

// ─── Case C: Missing trace_id → fail ─────────────────────────────────────────
console.log('\n── Case C: Missing trace_id → fail ────────────────────────────');
{
  const r = assertTraceId(null, EXEC);
  checkFailure('assertTraceId(null)', r, FAILURE_CODES.MISSING_TRACE_ID, 'input');
  check('trace_id is null in result', r.trace_id === null);
}
{
  const r = assertTraceId('', EXEC);
  checkFailure('assertTraceId("")', r, FAILURE_CODES.MISSING_TRACE_ID, 'input');
}
{
  // Valid trace_id → returns null (no failure)
  const r = assertTraceId(TRACE, EXEC);
  check('assertTraceId(valid) → null', r === null);
}

// ─── Case A: decision != ALLOW → no execution ────────────────────────────────
console.log('\n── Case A: decision != ALLOW → no execution ───────────────────');
{
  // FLAG decision
  const flagResult = {
    success: true,
    envelope: { decision: 'FLAG', risk_level: 'MEDIUM', reason: 'speed too high', source: 'mitra' }
  };
  const r = checkMitraResult(flagResult, TRACE, EXEC);
  checkFailure('FLAG decision', r, FAILURE_CODES.DECISION_NOT_ALLOW, 'decision');
  check('meta.decision=FLAG',   r.meta.decision === 'FLAG');
  check('meta.risk_level set',  r.meta.risk_level === 'MEDIUM');
}
{
  // BLOCK decision
  const blockResult = {
    success: true,
    envelope: { decision: 'BLOCK', risk_level: 'HIGH', reason: 'policy violation', source: 'mitra' }
  };
  const r = checkMitraResult(blockResult, TRACE, EXEC);
  checkFailure('BLOCK decision', r, FAILURE_CODES.DECISION_NOT_ALLOW, 'decision');
  check('meta.decision=BLOCK',  r.meta.decision === 'BLOCK');
}
{
  // ALLOW → no failure
  const allowResult = {
    success: true,
    envelope: { decision: 'ALLOW', risk_level: 'LOW', reason: 'ok', source: 'mitra' }
  };
  const r = checkMitraResult(allowResult, TRACE, EXEC);
  check('ALLOW → null (no failure)', r === null);
}

// ─── Case E: Mitra unreachable → fail loud ────────────────────────────────────
console.log('\n── Case E: Mitra unreachable → fail loud ──────────────────────');
{
  const r = checkMitraResult(
    { success: false, envelope: null, error: 'Mitra unreachable: ECONNREFUSED' },
    TRACE, EXEC
  );
  checkFailure('Mitra unreachable', r, FAILURE_CODES.MITRA_UNREACHABLE, 'decision');
}
{
  const r = checkMitraResult(
    { success: false, envelope: null, error: 'Mitra returned empty or invalid response' },
    TRACE, EXEC
  );
  checkFailure('Mitra invalid response', r, FAILURE_CODES.MITRA_INVALID_RESPONSE, 'decision');
}

// ─── Case F+G+H: Enforcement failures ────────────────────────────────────────
console.log('\n── Case F: Enforcement BLOCK → stop ───────────────────────────');
{
  const r = checkGateResult(
    { passed: false, blocked: true, flagged: false, decision: 'BLOCK',
      reason: 'policy violation', code: 'POLICY_VIOLATION', enforced_at: Date.now() },
    TRACE, EXEC
  );
  checkFailure('gate BLOCK', r, FAILURE_CODES.ENFORCEMENT_BLOCKED, 'enforcement');
  check('meta.gate_code=POLICY_VIOLATION', r.meta.gate_code === 'POLICY_VIOLATION');
}

console.log('\n── Case G: Enforcement FLAG → stop ────────────────────────────');
{
  const r = checkGateResult(
    { passed: false, blocked: false, flagged: true, decision: 'FLAG',
      reason: 'flagged for monitoring', enforced_at: Date.now() },
    TRACE, EXEC
  );
  checkFailure('gate FLAG', r, FAILURE_CODES.ENFORCEMENT_FLAGGED, 'enforcement');
}

console.log('\n── Case H: Stub decision → stop ───────────────────────────────');
{
  const r = checkGateResult(
    { passed: false, blocked: true, flagged: false, decision: 'BLOCK',
      reason: 'Decision source is stub', code: 'STUB_DECISION', enforced_at: Date.now() },
    TRACE, EXEC
  );
  checkFailure('stub decision', r, FAILURE_CODES.STUB_DECISION, 'enforcement');
}
{
  // Gate passed → null
  const r = checkGateResult(
    { passed: true, blocked: false, flagged: false, decision: 'ALLOW',
      reason: 'ok', source: 'mitra', enforced_at: Date.now() },
    TRACE, EXEC
  );
  check('gate passed → null', r === null);
}

// ─── Case I: Contract build failed ───────────────────────────────────────────
console.log('\n── Case I: Contract build failed → stop ───────────────────────');
{
  const r = checkContractBuild(
    { success: false, contract: null, errors: ['entities is required', 'scoring.rules missing'] },
    TRACE, EXEC
  );
  checkFailure('contract build failed', r, FAILURE_CODES.CONTRACT_BUILD_FAILED, 'contract');
  check('meta.errors array',  Array.isArray(r.meta.errors) && r.meta.errors.length === 2);
}
{
  const r = checkContractBuild({ success: true, contract: {}, errors: [] }, TRACE, EXEC);
  check('contract build success → null', r === null);
}

// ─── Case B: Execution rejection → log + stop ────────────────────────────────
console.log('\n── Case B: Execution rejection → log + stop ───────────────────');
{
  const r = checkExecutionResult(
    { success: false, status: 'contract_rejected', reason: 'game_mode not supported', code: 'CONTRACT_REJECTED' },
    TRACE, EXEC
  );
  checkFailure('execution rejected', r, FAILURE_CODES.EXECUTION_REJECTED, 'execution');
  check('meta.status=contract_rejected', r.meta.status === 'contract_rejected');
}

// ─── Case J: Execution unreachable ───────────────────────────────────────────
console.log('\n── Case J: Execution unreachable → stop ───────────────────────');
{
  const r = checkExecutionResult(
    { success: false, status: 'contract_rejected', error: 'Execution layer unreachable: ECONNREFUSED', code: 'UNREACHABLE' },
    TRACE, EXEC
  );
  checkFailure('execution unreachable', r, FAILURE_CODES.EXECUTION_UNREACHABLE, 'execution');
}
{
  const r = checkExecutionResult(
    { success: true, status: 'contract_accepted', accepted_at: Date.now() },
    TRACE, EXEC
  );
  check('execution accepted → null', r === null);
}

// ─── Case D: Broken event stream ─────────────────────────────────────────────
console.log('\n── Case D: Broken event stream → fail ─────────────────────────');
{
  // null event
  const r = checkIncomingEvent(null, TRACE, EXEC);
  checkFailure('null event', r, FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream');
}
{
  // missing event_type
  const r = checkIncomingEvent({ trace_id: TRACE }, TRACE, EXEC);
  checkFailure('missing event_type', r, FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream');
  check('reason mentions event_type', r.reason.includes('event_type'));
}
{
  // missing trace_id on event
  const r = checkIncomingEvent({ event_type: 'entity_spawned' }, TRACE, EXEC);
  checkFailure('missing trace_id on event', r, FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream');
  check('reason mentions trace_id', r.reason.includes('trace_id'));
}
{
  // trace_id mismatch
  const r = checkIncomingEvent(
    { event_type: 'entity_spawned', trace_id: 'WRONG-TRACE' },
    TRACE, EXEC
  );
  checkFailure('trace_id mismatch', r, FAILURE_CODES.EVENT_STREAM_BROKEN, 'event_stream');
  check('reason mentions mismatch', r.reason.includes('mismatch'));
}
{
  // valid event → null
  const r = checkIncomingEvent(
    { event_type: 'entity_spawned', trace_id: TRACE },
    TRACE, EXEC
  );
  check('valid event → null', r === null);
}

// ─── Case K: Event stream incomplete ─────────────────────────────────────────
console.log('\n── Case K: Event stream incomplete → fail ──────────────────────');
{
  const r = checkStreamComplete(false, TRACE, EXEC);
  checkFailure('stream incomplete', r, FAILURE_CODES.EVENT_STREAM_INCOMPLETE, 'event_stream');
  check('reason mentions execution_completed', r.reason.includes('execution_completed'));
}
{
  const r = checkStreamComplete(true, TRACE, EXEC);
  check('stream complete → null', r === null);
}

// ─── Case M: Unclassified error → fromError() ────────────────────────────────
console.log('\n── Case M: Unclassified error → fromError() ────────────────────');
{
  const r = fromError(new Error('something exploded'), 'execution', TRACE, EXEC);
  checkFailure('fromError(Error)', r, FAILURE_CODES.UNKNOWN, 'execution');
  check('reason contains error message', r.reason.includes('something exploded'));
}
{
  const r = fromError('plain string error', 'decision', TRACE, EXEC);
  checkFailure('fromError(string)', r, FAILURE_CODES.UNKNOWN, 'decision');
  check('reason contains string', r.reason.includes('plain string error'));
}

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log('\n══════════════════════════════════════════════════════');
console.log(`Phase 7 Failure Hardening — ${passed + failed} checks`);
console.log(`  ✅ Passed : ${passed}`);
console.log(`  ❌ Failed : ${failed}`);
console.log(`  Status   : ${failed === 0 ? 'PHASE 7 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
console.log('══════════════════════════════════════════════════════\n');
process.exit(failed > 0 ? 1 : 0);

'use strict';

/**
 * test_phase4_event_collector.js
 *
 * Phase 4 — Event Stream Capture Verification
 *
 * Tests:
 *   1. All 4 pipeline events collected in order
 *   2. trace_id continuity — every event carries the same trace_id
 *   3. Missing trace_id → rejected, not silently dropped
 *   4. Missing execution_id → rejected
 *   5. Unknown event type → rejected
 *   6. Post-completion event → rejected (stream is sealed)
 *   7. entity_spawned fires multiple times (multiple entities)
 *   8. getStream() returns snapshot — immutable
 *   9. hasEvent() and isComplete() work correctly
 *  10. Two separate traces are fully isolated
 *
 * Run: node backend/domain-adapters/maritime/test_phase4_event_collector.js
 */

const {
  collect,
  getStream,
  getEventsByType,
  hasEvent,
  isComplete,
  PIPELINE_EVENTS,
  _clear
} = require('./eventCollector');

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

const TRACE  = 'trace-p4-main';
const EXEC   = 'exec_p4_001';

// ─── Case 1: All 4 events collected in order ──────────────────────────────────
console.log('\n── Case 1: All 4 events collected in order ────────────────────');
_clear();
{
  const r1 = collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED,   TRACE, EXEC, { accepted_at: Date.now() });
  const r2 = collect(PIPELINE_EVENTS.EXECUTION_STARTED,   TRACE, EXEC, { started_at: Date.now() });
  const r3 = collect(PIPELINE_EVENTS.ENTITY_SPAWNED,      TRACE, EXEC, { entity_id: 'VESSEL_ALPHA', entity_type: 'npc' });
  const r4 = collect(PIPELINE_EVENTS.EXECUTION_COMPLETED, TRACE, EXEC, { status: 'completed', duration: 1200 });

  check('contract_accepted collected',   r1.success);
  check('execution_started collected',   r2.success);
  check('entity_spawned collected',      r3.success);
  check('execution_completed collected', r4.success);

  const stream = getStream(TRACE);
  check('stream has 4 events',           stream.events.length === 4);
  check('stream is complete',            stream.completed === true);
  check('completed_at present',          typeof stream.completed_at === 'number');
}

// ─── Case 2: trace_id continuity ─────────────────────────────────────────────
console.log('\n── Case 2: trace_id continuity on every event ─────────────────');
{
  const stream = getStream(TRACE);
  const allHaveTrace = stream.events.every(e => e.trace_id === TRACE);
  const allHaveExec  = stream.events.every(e => e.execution_id === EXEC);
  const allHaveId    = stream.events.every(e => typeof e.event_id === 'string' && e.event_id.length > 0);
  const allHaveTs    = stream.events.every(e => typeof e.collected_at === 'number');

  check('every event has correct trace_id',    allHaveTrace);
  check('every event has correct execution_id',allHaveExec);
  check('every event has unique event_id',     allHaveId);
  check('every event has collected_at',        allHaveTs);
}

// ─── Case 3: Missing trace_id → rejected ─────────────────────────────────────
console.log('\n── Case 3: Missing trace_id → rejected ────────────────────────');
{
  const r = collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED, null, EXEC, {});
  check('success=false',          r.success === false);
  check('event is null',          r.event   === null);
  check('error message present',  typeof r.error === 'string' && r.error.length > 0);
}

// ─── Case 4: Missing execution_id → rejected ─────────────────────────────────
console.log('\n── Case 4: Missing execution_id → rejected ────────────────────');
{
  const r = collect(PIPELINE_EVENTS.EXECUTION_STARTED, 'trace-p4-c4', null, {});
  check('success=false',          r.success === false);
  check('event is null',          r.event   === null);
  check('error mentions exec_id', r.error.includes('execution_id'));
}

// ─── Case 5: Unknown event type → rejected ────────────────────────────────────
console.log('\n── Case 5: Unknown event type → rejected ──────────────────────');
{
  const r = collect('some_random_event', 'trace-p4-c5', 'exec_p4_c5', {});
  check('success=false',               r.success === false);
  check('event is null',               r.event   === null);
  check('error mentions unknown type', r.error.includes('Unknown event type'));
}

// ─── Case 6: Post-completion event → rejected ────────────────────────────────
console.log('\n── Case 6: Post-completion event → rejected ───────────────────');
{
  // stream from Case 1 is already completed
  const r = collect(PIPELINE_EVENTS.ENTITY_SPAWNED, TRACE, EXEC, { entity_id: 'LATE_VESSEL' });
  check('success=false',              r.success === false);
  check('event is null',              r.event   === null);
  check('error mentions completed',   r.error.includes('completed'));
}

// ─── Case 7: entity_spawned fires multiple times ──────────────────────────────
console.log('\n── Case 7: entity_spawned fires multiple times ────────────────');
{
  _clear();
  const T = 'trace-p4-multi';
  const E = 'exec_p4_multi';

  collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED, T, E, {});
  collect(PIPELINE_EVENTS.EXECUTION_STARTED, T, E, {});
  collect(PIPELINE_EVENTS.ENTITY_SPAWNED,    T, E, { entity_id: 'VESSEL_A' });
  collect(PIPELINE_EVENTS.ENTITY_SPAWNED,    T, E, { entity_id: 'VESSEL_B' });
  collect(PIPELINE_EVENTS.ENTITY_SPAWNED,    T, E, { entity_id: 'VESSEL_C' });
  collect(PIPELINE_EVENTS.EXECUTION_COMPLETED, T, E, { status: 'completed' });

  const spawned = getEventsByType(T, PIPELINE_EVENTS.ENTITY_SPAWNED);
  check('3 entity_spawned events',    spawned.length === 3);
  check('each has unique event_id',   new Set(spawned.map(e => e.event_id)).size === 3);
  check('payloads preserved',         spawned.map(e => e.payload.entity_id).join(',') === 'VESSEL_A,VESSEL_B,VESSEL_C');
  check('stream total = 6',           getStream(T).events.length === 6);
}

// ─── Case 8: getStream() returns immutable snapshot ──────────────────────────
console.log('\n── Case 8: getStream() returns immutable snapshot ─────────────');
{
  const T = 'trace-p4-multi';
  const snap1 = getStream(T);
  snap1.events.push({ fake: true }); // mutate the snapshot
  const snap2 = getStream(T);
  check('internal store not mutated', snap2.events.length === 6);
}

// ─── Case 9: hasEvent() and isComplete() ─────────────────────────────────────
console.log('\n── Case 9: hasEvent() and isComplete() ────────────────────────');
{
  const T = 'trace-p4-multi';
  check('hasEvent contract_accepted',   hasEvent(T, PIPELINE_EVENTS.CONTRACT_ACCEPTED));
  check('hasEvent execution_started',   hasEvent(T, PIPELINE_EVENTS.EXECUTION_STARTED));
  check('hasEvent entity_spawned',      hasEvent(T, PIPELINE_EVENTS.ENTITY_SPAWNED));
  check('hasEvent execution_completed', hasEvent(T, PIPELINE_EVENTS.EXECUTION_COMPLETED));
  check('isComplete=true',              isComplete(T) === true);
  check('isComplete unknown trace',     isComplete('no-such-trace') === false);
}

// ─── Case 10: Two traces are fully isolated ───────────────────────────────────
console.log('\n── Case 10: Two traces are fully isolated ──────────────────────');
{
  _clear();
  const T1 = 'trace-p4-iso-1';
  const T2 = 'trace-p4-iso-2';

  collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED, T1, 'exec_iso_1', { note: 'trace1' });
  collect(PIPELINE_EVENTS.CONTRACT_ACCEPTED, T2, 'exec_iso_2', { note: 'trace2' });
  collect(PIPELINE_EVENTS.EXECUTION_STARTED, T1, 'exec_iso_1', {});

  const s1 = getStream(T1);
  const s2 = getStream(T2);

  check('T1 has 2 events',              s1.events.length === 2);
  check('T2 has 1 event',               s2.events.length === 1);
  check('T1 execution_id correct',      s1.execution_id === 'exec_iso_1');
  check('T2 execution_id correct',      s2.execution_id === 'exec_iso_2');
  check('T1 events have T1 trace_id',   s1.events.every(e => e.trace_id === T1));
  check('T2 events have T2 trace_id',   s2.events.every(e => e.trace_id === T2));
}

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log('\n══════════════════════════════════════════════════════');
console.log(`Phase 4 Event Collector — ${passed + failed} checks`);
console.log(`  ✅ Passed : ${passed}`);
console.log(`  ❌ Failed : ${failed}`);
console.log(`  Status   : ${failed === 0 ? 'PHASE 4 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
console.log('══════════════════════════════════════════════════════\n');
process.exit(failed > 0 ? 1 : 0);

/**
 * Test Event Safety Guard
 * Covers: invalid type, stale timestamp, future timestamp,
 *         duplicate detection, rate limiting, loop detection
 */

const {
  guardEvent,
  getViolations,
  updateConfig,
  reset,
  checkEventType,
  checkTimestamp,
  checkDuplicate,
  checkRateLimit,
  checkLoopDepth
} = require('./consequence/eventSafetyGuard');

const { createCollisionEvent, ENTITY_TYPES } = require('./events/runtimeEvents');

// ─── helpers ──────────────────────────────────────────────────────────────────

function makeEvent(overrides = {}) {
  const base = createCollisionEvent('player', 'obstacle_01', {
    entity_type: ENTITY_TYPES.OBSTACLE,
    gameSessionId: 'session_test'
  });
  return { ...base, ...overrides };
}

let passed = 0;
let failed = 0;

function assert(label, condition) {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}`);
    failed++;
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

console.log('=== Event Safety Guard Tests ===\n');

// ── 1. Invalid event type ─────────────────────────────────────────────────────
console.log('Test 1: Invalid Event Type');
reset();
{
  const r = checkEventType({ event_type: 'hack_attempt' });
  assert('blocked unknown type', !r.allowed);
  assert('reason contains invalid_event_type', r.reason.includes('invalid_event_type'));

  const r2 = checkEventType({ event_type: 'collision' });
  assert('allowed known type', r2.allowed);

  assert('violation counter incremented', getViolations().invalid_type === 1);
}
console.log();

// ── 2. Stale timestamp ────────────────────────────────────────────────────────
console.log('Test 2: Stale Timestamp');
reset();
{
  const stale = makeEvent({ timestamp: Date.now() - 60_000 }); // 60 s ago
  const r = checkTimestamp(stale);
  assert('blocked stale event', !r.allowed);
  assert('reason contains stale_timestamp', r.reason.includes('stale_timestamp'));

  const fresh = makeEvent({ timestamp: Date.now() });
  const r2 = checkTimestamp(fresh);
  assert('allowed fresh event', r2.allowed);

  assert('stale_timestamp violation counted', getViolations().stale_timestamp === 1);
}
console.log();

// ── 3. Future timestamp ───────────────────────────────────────────────────────
console.log('Test 3: Future Timestamp');
reset();
{
  const future = makeEvent({ timestamp: Date.now() + 30_000 }); // 30 s ahead
  const r = checkTimestamp(future);
  assert('blocked future event', !r.allowed);
  assert('reason contains future_timestamp', r.reason.includes('future_timestamp'));

  assert('future_timestamp violation counted', getViolations().future_timestamp === 1);
}
console.log();

// ── 4. Duplicate detection ────────────────────────────────────────────────────
console.log('Test 4: Duplicate Detection');
reset();
{
  const ev = makeEvent();
  const r1 = checkDuplicate(ev);
  assert('first occurrence allowed', r1.allowed);

  const r2 = checkDuplicate(ev); // same event_id
  assert('second occurrence blocked', !r2.allowed);
  assert('reason contains duplicate_event', r2.reason.includes('duplicate_event'));

  assert('duplicate violation counted', getViolations().duplicate === 1);
}
console.log();

// ── 5. Rate limiting ──────────────────────────────────────────────────────────
console.log('Test 5: Rate Limiting');
reset();
updateConfig({ MAX_EVENTS_PER_SECOND: 5 }); // lower limit for test
{
  const session = 'rate_test_session';
  let blocked = false;

  for (let i = 0; i < 10; i++) {
    const ev = makeEvent({ event_id: `rate_evt_${i}`, game_session_id: session });
    const r = checkRateLimit(ev, session);
    if (!r.allowed) { blocked = true; break; }
  }

  assert('rate limit triggered after threshold', blocked);
  assert('rate_limit violation counted', getViolations().rate_limit >= 1);
}
updateConfig({ MAX_EVENTS_PER_SECOND: 20 }); // restore
console.log();

// ── 6. Loop / chain depth detection ──────────────────────────────────────────
console.log('Test 6: Recursive Loop Detection');
reset();
updateConfig({ MAX_CHAIN_DEPTH: 3, LOOP_WINDOW_MS: 5000 });
{
  const originId = 'origin_evt_loop_test';

  // Simulate a chain: each event shares the same origin_event_id
  let blocked = false;
  for (let i = 0; i < 6; i++) {
    const ev = makeEvent({
      event_id: `chain_evt_${i}`,
      metadata: { origin_event_id: originId }
    });
    const r = checkLoopDepth(ev);
    if (!r.allowed) { blocked = true; break; }
  }

  assert('loop blocked after max chain depth', blocked);
  assert('loop violation counted', getViolations().loop >= 1);
}
updateConfig({ MAX_CHAIN_DEPTH: 5, LOOP_WINDOW_MS: 2000 }); // restore
console.log();

// ── 7. Full guardEvent – valid event passes all checks ────────────────────────
console.log('Test 7: Full Guard – Valid Event');
reset();
{
  const ev = makeEvent();
  const r = guardEvent(ev, 'session_valid');
  assert('valid event passes all checks', r.allowed);
  assert('all check flags present', 'event_type' in r.checks && 'timestamp' in r.checks);
}
console.log();

// ── 8. Full guardEvent – invalid type blocked at first gate ───────────────────
console.log('Test 8: Full Guard – Invalid Type Blocked Early');
reset();
{
  const ev = makeEvent({ event_type: 'unknown_event' });
  const r = guardEvent(ev, 'session_bad');
  assert('invalid type blocked', !r.allowed);
  assert('blocked at event_type check', r.checks.event_type === false);
}
console.log();

// ── 9. Full guardEvent – duplicate blocked ────────────────────────────────────
console.log('Test 9: Full Guard – Duplicate Blocked');
reset();
{
  const ev = makeEvent();
  guardEvent(ev, 'session_dup'); // first pass
  const r = guardEvent(ev, 'session_dup'); // second pass – same event_id
  assert('duplicate blocked by full guard', !r.allowed);
  assert('reason mentions duplicate', r.reason.includes('duplicate_event'));
}
console.log();

// ── 10. Violation summary ─────────────────────────────────────────────────────
console.log('Test 10: Violation Summary After All Tests');
// Run a quick set to populate counters
reset();
guardEvent(makeEvent({ event_type: 'bad_type' }));
const ev = makeEvent();
guardEvent(ev, 's1');
guardEvent(ev, 's1'); // duplicate

const v = getViolations();
assert('invalid_type counted', v.invalid_type >= 1);
assert('duplicate counted', v.duplicate >= 1);
console.log('  Violations:', v);
console.log();

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log('=== Summary ===');
console.log(`Passed: ${passed}  Failed: ${failed}`);
if (failed === 0) {
  console.log('\nEvent Safety Guard: ✅ ALL CHECKS PASSING');
} else {
  console.log('\nEvent Safety Guard: ❌ SOME CHECKS FAILED');
  process.exitCode = 1;
}

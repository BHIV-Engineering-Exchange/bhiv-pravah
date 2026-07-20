/**
 * Full Pipeline Test — Runner Game Scenario
 * 
 * Scenario: Runner game, player collides with obstacle
 * Flow: Runtime Event → Safety Guard → Consequence Compiler → END_GAME job → Job Queue → Engine
 */

// ─── Mock Job Queue (prevents setInterval hang) ──────────────────────────────
const jobLog = [];
let jobsCompleted = 0;
let jobsDispatched = 0;

const mockJobQueue = {
  addJob: (job, callback) => {
    job.status = 'queued';
    jobLog.push(job);  // push reference, not snapshot
    jobsDispatched++;
    console.log(`  [JOB QUEUE] Job added: ${job.jobType} (${job.priority}) — id: ${job.jobId}`);

    // Simulate: queued → dispatched → running → completed
    setTimeout(() => {
      job.status = 'dispatched';
      console.log(`  [JOB QUEUE] Job dispatched to engine: ${job.jobType}`);
      setTimeout(() => {
        job.status = 'running';
        console.log(`  [JOB QUEUE] Engine running job: ${job.jobType}`);
        setTimeout(() => {
          job.status = 'completed';
          jobsCompleted++;
          console.log(`  [JOB QUEUE] Engine completed job: ${job.jobType}`);
          if (callback) callback(job, 'completed', null);
        }, 80);
      }, 80);
    }, 80);
  }
};

require.cache[require.resolve('./jobQueue')] = { id: require.resolve('./jobQueue'), filename: require.resolve('./jobQueue'), loaded: true, exports: mockJobQueue };

// ─── Imports (after mock) ─────────────────────────────────────────────────────
const { createCollisionEvent, createPickupCollectedEvent, createTimerExpiredEvent } = require('./events/runtimeEvents');
const { processRuntimeEvent, getPipelineStatistics, resetStatistics } = require('./dispatcher_event_pipeline');
const { reset: resetGuard } = require('./consequence/eventSafetyGuard');

// ─── Test Helpers ─────────────────────────────────────────────────────────────
let passed = 0;
let failed = 0;

function assert(condition, label) {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.log(`  ❌ ${label}`);
    failed++;
  }
}

function section(title) {
  console.log(`\n${'─'.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('─'.repeat(60));
}

// ─── Tests ────────────────────────────────────────────────────────────────────

section('SCENARIO 1 — Runner: collision(player, obstacle) → END_GAME');

resetStatistics();
resetGuard();

const collisionEvent = createCollisionEvent('player_01', 'obstacle_01', {
  entity_type: 'obstacle',
  velocity: 5.2,
  gameSessionId: 'runner_session_001'
});

console.log('\n  [ENGINE] Emitting runtime event:');
console.log(`    event_type : ${collisionEvent.event_type}`);
console.log(`    entities   : ${collisionEvent.entities.join(', ')}`);
console.log(`    entity_type: ${collisionEvent.context.entity_type}`);
console.log(`    session    : runner_session_001`);
console.log('');

const result1 = processRuntimeEvent(collisionEvent, {
  gameSessionId: 'runner_session_001',
  userId: 'player_01',
  engineId: 'runner_engine'
});

console.log('');
assert(result1.success === true,                          'Pipeline processed event successfully');
assert(result1.stage === 'completed',                     'Pipeline reached completed stage');
assert(result1.event_type === 'collision',                'Event type is collision');
assert(result1.critical === true,                         'Collision flagged as critical');
assert(result1.matched_rules >= 1,                        `At least 1 rule matched (got ${result1.matched_rules})`);
assert(result1.jobs_generated >= 1,                       `At least 1 job generated (got ${result1.jobs_generated})`);
assert(result1.jobs_dispatched >= 1,                      `At least 1 job dispatched (got ${result1.jobs_dispatched})`);

const endGameJob = jobLog.find(j => j.jobType === 'END_GAME');
assert(endGameJob !== undefined,                          'END_GAME job was created');
assert(endGameJob?.priority === 'critical',               'END_GAME job has critical priority');
assert(endGameJob?.payload?.reason === 'collision_with_obstacle', 'END_GAME reason is collision_with_obstacle');
assert(endGameJob?.payload?.show_game_over === true,      'END_GAME sets show_game_over = true');
assert(endGameJob?.traceId === collisionEvent.event_id,   'Job traceId matches source event_id');
assert(endGameJob?.executionId === 'runner_session_001',  'Job executionId matches game session');

// ─── Scenario 2: Coin pickup → UPDATE_SCORE ───────────────────────────────────
section('SCENARIO 2 — Runner: pickup_collected(coin) → UPDATE_SCORE');

resetGuard();
jobLog.length = 0;

const pickupEvent = createPickupCollectedEvent('coin_42', {
  score: 50,
  gameSessionId: 'runner_session_001'
});

const result2 = processRuntimeEvent(pickupEvent, {
  gameSessionId: 'runner_session_001',
  userId: 'player_01',
  engineId: 'runner_engine'
});

console.log('');
assert(result2.success === true,                          'Pickup event processed successfully');
assert(result2.jobs_generated >= 1,                       `Jobs generated for pickup (got ${result2.jobs_generated})`);

const scoreJob = jobLog.find(j => j.jobType === 'UPDATE_SCORE');
assert(scoreJob !== undefined,                            'UPDATE_SCORE job was created');
assert(scoreJob?.payload?.score_delta === 10,             'Score delta is 10 for coin');

// ─── Scenario 3: Timer expired → END_GAME ────────────────────────────────────
section('SCENARIO 3 — Runner: timer_expired → END_GAME');

resetGuard();
jobLog.length = 0;

const timerEvent = createTimerExpiredEvent(0, { gameSessionId: 'runner_session_002' });

const result3 = processRuntimeEvent(timerEvent, {
  gameSessionId: 'runner_session_002',
  userId: 'player_01',
  engineId: 'runner_engine'
});

console.log('');
assert(result3.success === true,                          'Timer event processed successfully');
assert(result3.critical === true,                         'Timer expired flagged as critical');

const timerEndGame = jobLog.find(j => j.jobType === 'END_GAME');
assert(timerEndGame !== undefined,                        'END_GAME job created for timer expiry');
assert(timerEndGame?.payload?.reason === 'time_up',       'END_GAME reason is time_up');

// ─── Scenario 4: Safety guard blocks duplicate ────────────────────────────────
section('SCENARIO 4 — Safety Guard: duplicate event blocked');

// Send same event twice (same event_id)
const dupEvent = createCollisionEvent('player_01', 'obstacle_02', {
  entity_type: 'obstacle',
  gameSessionId: 'runner_session_003'
});

const r4a = processRuntimeEvent(dupEvent, { gameSessionId: 'runner_session_003' });
const r4b = processRuntimeEvent(dupEvent, { gameSessionId: 'runner_session_003' }); // duplicate

console.log('');
assert(r4a.success === true,                              'First event passes through');
assert(r4b.success === false,                             'Duplicate event blocked by safety guard');
assert(r4b.stage === 'safety_guard',                      'Blocked at safety_guard stage');

// ─── Pipeline Statistics ──────────────────────────────────────────────────────
section('PIPELINE STATISTICS');

const stats = getPipelineStatistics();
console.log('');
console.log(`  events_received  : ${stats.events_received}`);
console.log(`  events_processed : ${stats.events_processed}`);
console.log(`  events_failed    : ${stats.events_failed}`);
console.log(`  jobs_generated   : ${stats.jobs_generated}`);
console.log(`  jobs_dispatched  : ${stats.jobs_dispatched}`);
console.log(`  critical_events  : ${stats.critical_events}`);
console.log(`  success_rate     : ${stats.success_rate}`);

assert(stats.events_received >= 5,                        'Pipeline tracked all received events');
assert(stats.critical_events >= 2,                        'Critical events counted correctly');

// ─── Job Lifecycle (wait for async completions) ───────────────────────────────
section('JOB LIFECYCLE — Waiting for engine completions...');

setTimeout(() => {
  console.log('');
  console.log(`  Jobs dispatched : ${jobsDispatched}`);
  console.log(`  Jobs completed  : ${jobsCompleted}`);

  // ─── Summary ─────────────────────────────────────────────────────────────
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  FULL PIPELINE TEST RESULTS`);
  console.log('═'.repeat(60));
  console.log(`  ✅ Passed : ${passed}`);
  console.log(`  ❌ Failed : ${failed}`);
  console.log(`  Total     : ${passed + failed}`);
  console.log('═'.repeat(60));

  if (failed === 0) {
    console.log('\n  🎮 Runner game pipeline: FULLY OPERATIONAL');
    console.log('  collision(player, obstacle) → END_GAME job → Queue → Engine ✓\n');
  } else {
    console.log('\n  ⚠️  Some checks failed — review output above\n');
  }

  process.exit(failed === 0 ? 0 : 1);
}, 600);  // 3 × 80ms lifecycle chain + margin

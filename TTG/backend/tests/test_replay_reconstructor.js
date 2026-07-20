// test_replay_reconstructor.js - Phase 8: Replay Reconstruction Test
// Run: node tests/test_replay_reconstructor.js

const { v4: uuidv4 }       = require('uuid');
const gsm                  = require('../state/gameStateManager');
const bucketWriter         = require('../state/stateBucketWriter');
const { reconstruct,
        reconstructAt,
        loadArtifacts }    = require('../state/replayReconstructor');

function pass(msg) { console.log(`  ✅ ${msg}`); }
function fail(msg) { console.log(`  ❌ ${msg}`); process.exitCode = 1; }

// ─── Build a real session with known events ───────────────────────────────────

const SESSION_ID   = `replay_test_${Date.now()}`;
const EXECUTION_ID = `exec_replay_${Date.now()}`;
const TRACE_ID     = `trace_replay_${Date.now()}`;

const MOCK_SCHEMA = { game_mode: 'arena', player_params: { health: 100 }, spawn_rules: { obstacles: 5 } };

// Ordered events we will apply and then replay
const EVENTS = [
  { event_type: 'entity_spawned',   entities: ['enemy_001'], context: { entity_type: 'enemy' } },
  { event_type: 'entity_spawned',   entities: ['enemy_002'], context: { entity_type: 'enemy' } },
  { event_type: 'score_update',     entities: ['player'],    context: { score_delta: 100 } },
  { event_type: 'health_changed',   entities: ['player'],    context: { delta: -1 } },
  { event_type: 'entity_destroyed', entities: ['enemy_001'], context: { entity_type: 'enemy' } },
  { event_type: 'pickup_collected', entities: ['player', 'coin_001'], context: { entity_type: 'collectible', score_delta: 10 } },
  { event_type: 'score_update',     entities: ['player'],    context: { score_delta: 50 } }
];

async function buildSession() {
  // Create state
  gsm.createGameState(SESSION_ID, { template_id: 'arena_v1', defaults: { player_health: 100, enemy_count: 0 } }, {
    execution_id: EXECUTION_ID, trace_id: TRACE_ID
  });
  const { _sessions } = gsm.__internals();
  _sessions.get(SESSION_ID).status = 'running';

  // Write initial snapshot (v0) BEFORE any events
  await bucketWriter.writeStateSnapshot(SESSION_ID);

  // Apply events and trace each one
  for (const e of EVENTS) {
    const event = {
      event_type:      e.event_type,
      event_id:        uuidv4(),
      timestamp:       Date.now(),
      game_session_id: SESSION_ID,
      entities:        e.entities,
      context:         e.context,
      metadata:        {}
    };
    const result = gsm.applyEventToState(SESSION_ID, event);
    await bucketWriter.appendEventTrace(SESSION_ID, event, result.changes);
    await new Promise(r => setTimeout(r, 2)); // ensure unique timestamps
  }

  // Write execution schema
  await bucketWriter.writeExecutionSchema(SESSION_ID, EXECUTION_ID, TRACE_ID, MOCK_SCHEMA);

  return gsm.getCurrentState(SESSION_ID);
}

// ─── Tests ────────────────────────────────────────────────────────────────────

async function test1_loadArtifacts() {
  console.log('\n=== Test 1: loadArtifacts ===');
  const result = await loadArtifacts(SESSION_ID);

  if (result.success)                    pass('loadArtifacts succeeded');
  else { fail(`loadArtifacts failed: ${result.error}`); return false; }

  if (result.snapshot)                   pass(`snapshot loaded (mode: ${result.snapshot.game_mode})`);
  else                                   fail('snapshot missing');

  if (result.events.length === EVENTS.length)
    pass(`event trace loaded: ${result.events.length} events`);
  else
    fail(`expected ${EVENTS.length} events, got ${result.events.length}`);

  if (result.schema)                     pass('execution schema loaded');
  else                                   fail('execution schema missing');

  return true;
}

async function test2_fullReconstruct(liveState) {
  console.log('\n=== Test 2: Full Reconstruction ===');
  const result = await reconstruct(SESSION_ID);

  if (!result.success) { fail(`reconstruct failed: ${result.error}`); return false; }
  pass('reconstruct succeeded');

  if (result.frames.length === EVENTS.length)
    pass(`correct frame count: ${result.frames.length}`);
  else
    fail(`expected ${EVENTS.length} frames, got ${result.frames.length}`);

  // Every frame must have applied=true
  const allApplied = result.frames.every(f => f.applied);
  if (allApplied) pass('all frames applied successfully');
  else            fail('some frames failed to apply');

  // Final state must match live state exactly
  const replayScore  = result.finalState.player.score;
  const liveScore    = liveState.player.score;
  if (replayScore === liveScore)
    pass(`final score matches live: ${replayScore}`);
  else
    fail(`score mismatch — replay: ${replayScore}, live: ${liveScore}`);

  const replayHealth = result.finalState.player.health;
  const liveHealth   = liveState.player.health;
  if (replayHealth === liveHealth)
    pass(`final health matches live: ${replayHealth}`);
  else
    fail(`health mismatch — replay: ${replayHealth}, live: ${liveHealth}`);

  const replayEnemies = result.finalState.entities.enemy_count;
  const liveEnemies   = liveState.entities.enemy_count;
  if (replayEnemies === liveEnemies)
    pass(`final enemy_count matches live: ${replayEnemies}`);
  else
    fail(`enemy_count mismatch — replay: ${replayEnemies}, live: ${liveEnemies}`);

  return result;
}

async function test3_frameInspection(replayResult) {
  console.log('\n=== Test 3: Frame Inspection ===');

  // Frame 0: entity_spawned enemy_001 → enemy_count should go from 0 to 1
  const f0 = replayResult.frames[0];
  if (f0.event_type === 'entity_spawned') pass(`frame[0] event_type: ${f0.event_type}`);
  else fail(`frame[0] wrong event_type: ${f0.event_type}`);

  const enemyBefore = f0.stateBefore.entities.enemy_count;
  const enemyAfter  = f0.stateAfter.entities.enemy_count;
  if (enemyAfter === enemyBefore + 1)
    pass(`frame[0] enemy_count: ${enemyBefore} → ${enemyAfter}`);
  else
    fail(`frame[0] enemy_count wrong: ${enemyBefore} → ${enemyAfter}`);

  // Frame 3: health_changed delta=-1 → health drops by 1
  const f3 = replayResult.frames[3];
  if (f3.event_type === 'health_changed') pass(`frame[3] event_type: ${f3.event_type}`);
  else fail(`frame[3] wrong event_type: ${f3.event_type}`);

  const hBefore = f3.stateBefore.player.health;
  const hAfter  = f3.stateAfter.player.health;
  if (hAfter === hBefore - 1)
    pass(`frame[3] health: ${hBefore} → ${hAfter}`);
  else
    fail(`frame[3] health wrong: ${hBefore} → ${hAfter}`);

  return true;
}

async function test4_seekReplay() {
  console.log('\n=== Test 4: Seek Replay (reconstructAt) ===');

  // Seek to frame 2 (after 3 events: spawn, spawn, score+100)
  const result = await reconstructAt(SESSION_ID, 2);
  if (!result.success) { fail(`reconstructAt failed: ${result.error}`); return false; }
  pass('reconstructAt succeeded');

  // After 3 events: 2 spawns + score+100 → score should be 100
  if (result.state.player.score === 100)
    pass(`state at frame[2] score: ${result.state.player.score}`);
  else
    fail(`expected score 100 at frame[2], got ${result.state.player.score}`);

  // enemy_count should be 2 (two spawns)
  if (result.state.entities.enemy_count === 2)
    pass(`state at frame[2] enemy_count: ${result.state.entities.enemy_count}`);
  else
    fail(`expected enemy_count 2 at frame[2], got ${result.state.entities.enemy_count}`);

  return true;
}

async function test5_determinism() {
  console.log('\n=== Test 5: Determinism (two replays produce identical final state) ===');

  const r1 = await reconstruct(SESSION_ID);
  const r2 = await reconstruct(SESSION_ID);

  if (!r1.success || !r2.success) { fail('one of the replays failed'); return false; }

  const match =
    r1.finalState.player.score         === r2.finalState.player.score  &&
    r1.finalState.player.health        === r2.finalState.player.health &&
    r1.finalState.entities.enemy_count === r2.finalState.entities.enemy_count &&
    r1.frames.length                   === r2.frames.length;

  if (match) pass(`two replays identical — score: ${r1.finalState.player.score}, health: ${r1.finalState.player.health}, enemies: ${r1.finalState.entities.enemy_count}`);
  else       fail('replays produced different results — NOT deterministic');

  return match;
}

async function test6_summary() {
  console.log('\n=== Test 6: Summary ===');
  const result = await reconstruct(SESSION_ID);
  const s = result.summary;

  if (s.total_events === EVENTS.length) pass(`summary.total_events: ${s.total_events}`);
  else fail(`summary.total_events wrong: ${s.total_events}`);

  if (typeof s.final_score === 'number') pass(`summary.final_score: ${s.final_score}`);
  else fail('summary.final_score missing');

  if (s.events_by_type) pass(`summary.events_by_type: ${JSON.stringify(s.events_by_type)}`);
  else fail('summary.events_by_type missing');

  return true;
}

// ─── Run all ──────────────────────────────────────────────────────────────────

async function runAll() {
  console.log('🧪 Phase 8: Replay Reconstruction Tests');
  console.log(`   Session ID: ${SESSION_ID}\n`);

  console.log('--- Building session with live events ---');
  const liveState = await buildSession();
  console.log(`    Live final state — score: ${liveState.player.score}, health: ${liveState.player.health}, enemies: ${liveState.entities.enemy_count}`);

  const results = [];
  results.push(await test1_loadArtifacts());
  const replayResult = await test2_fullReconstruct(liveState);
  results.push(!!replayResult);
  results.push(replayResult ? await test3_frameInspection(replayResult) : false);
  results.push(await test4_seekReplay());
  results.push(await test5_determinism());
  results.push(await test6_summary());

  const passed = results.filter(Boolean).length;
  console.log(`\n${'─'.repeat(50)}`);
  console.log(`Results: ${passed}/${results.length} tests passed`);
  if (passed === results.length) {
    console.log('✅ Phase 8 complete — deterministic replay verified');
  } else {
    console.log('❌ Some tests failed');
    process.exit(1);
  }
}

runAll().catch(err => { console.error('Fatal:', err); process.exit(1); });

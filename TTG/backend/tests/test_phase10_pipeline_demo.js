'use strict';

/**
 * Phase 10 — Full Pipeline Demonstration
 *
 * Stages:
 *   1. Prompt          → simulate Prompt Runner output
 *   2. Game Generation → stateInitializer.initializeFromExecutionSchema()
 *   3. Game State      → GSM creates session, state printed
 *   4. Engine Runs     → setRunning(), game_start event
 *   5. Runtime Events  → stateEventProcessor processes 6 events
 *   6. State Updates   → state snapshot printed after each event
 *   7. Consequence Jobs→ consequenceCompiler generates jobs per event
 *
 * Run: node tests/test_phase10_pipeline_demo.js
 */

const { v4: uuidv4 } = require('uuid');

const stateInitializer   = require('../state/stateInitializer');
const gsm                = require('../state/gameStateManager');
const sep                = require('../state/stateEventProcessor');
const compiler           = require('../consequence/consequenceCompiler');
const guard              = require('../state/stateIntegrityGuard');
const bucketWriter       = require('../state/stateBucketWriter');

// ─── Helpers ──────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function banner(title) {
  const line = '═'.repeat(60);
  console.log(`\n${line}`);
  console.log(`  ${title}`);
  console.log(line);
}

function step(label) {
  console.log(`\n  ▶  ${label}`);
}

function ok(label) {
  passed++;
  console.log(`     ✔  ${label}`);
}

function fail(label, detail) {
  failed++;
  console.error(`     ✘  ${label}${detail ? ' — ' + detail : ''}`);
}

function printState(state, label = 'State Snapshot') {
  console.log(`\n  ┌─ ${label}`);
  console.log(`  │  status        : ${state.status}`);
  console.log(`  │  player.health : ${state.player.health}/${state.player.max_health}`);
  console.log(`  │  player.score  : ${state.player.score}`);
  console.log(`  │  player.lives  : ${state.player.lives}`);
  console.log(`  │  player.alive  : ${state.player.is_alive}`);
  console.log(`  │  enemies       : ${state.entities.enemy_count}`);
  console.log(`  │  obstacles     : ${state.entities.obstacle_count}`);
  console.log(`  │  collectibles  : ${state.entities.collectible_count}`);
  console.log(`  │  world.level   : ${state.world.level}`);
  console.log(`  │  difficulty    : ${state.world.difficulty}`);
  console.log(`  │  event_count   : ${state.meta.event_count}`);
  console.log(`  └─────────────────────────────────────────────────`);
}

function makeEvent(type, entities = [], context = {}) {
  return {
    event_type:      type,
    event_id:        `evt_${uuidv4().slice(0, 8)}`,
    timestamp:       Date.now(),
    game_session_id: null,
    entities,
    context,
    metadata:        {}
  };
}

// ─── Stage 1: Prompt ──────────────────────────────────────────────────────────

async function stage1_prompt() {
  banner('STAGE 1 — Prompt Runner Output');

  // Simulate what prompt_runner/adapter.js convertToExecutionSchema() produces
  const now = Date.now();
  const executionData = {
    execution_id: `exec_demo_${now}`,
    trace_id:     `trace_demo_${now}`,
    user_id:      'demo_user',
    intent:       { prompt: 'create a hard arena game with 3 enemies' },
    executionSchema: {
      game_mode:     'open_scene',          // → maps to 'arena' in stateInitializer
      module:        'game_generation',
      intent:        'create_game',
      movement:      { speed: 5 },
      physics:       { gravity: -9.8, friction: 0.5, bounce: 0.3, air_resistance: 0.1, collision_force: 1 },
      spawn_rules:   { obstacles: 3, frequency: 1.5 },
      score_rules:   { distance: 1, collectibles: 10 },
      end_conditions:['collision'],
      player_params: { health: 5, jetpack: false },
      world_params:  { theme: 'volcano' },
      data:          { topic: 'arena combat', parameters: {}, original_prompt: 'create a hard arena game' },
      tasks:         ['spawn_enemies', 'track_score', 'handle_death'],
      output_format: 'game_world',
      context:       { source: 'prompt_runner' }
    },
    timestamp: now
  };

  step('Prompt: "create a hard arena game with 3 enemies"');
  console.log(`     execution_id : ${executionData.execution_id}`);
  console.log(`     game_mode    : ${executionData.executionSchema.game_mode} → arena`);
  console.log(`     health       : ${executionData.executionSchema.player_params.health}`);
  console.log(`     enemies      : ${executionData.executionSchema.spawn_rules.obstacles}`);
  console.log(`     theme        : ${executionData.executionSchema.world_params.theme}`);

  ok('Prompt Runner output constructed');
  return executionData;
}

// ─── Stage 2 & 3: Game Generation + State Created ────────────────────────────

async function stage2_3_gameGeneration(executionData) {
  banner('STAGE 2 — Game Generation  →  STAGE 3 — Game State Created');

  step('Calling stateInitializer.initializeFromExecutionSchema()');

  const result = await stateInitializer.initializeFromExecutionSchema(executionData);

  if (!result.success) {
    fail('State initialization', result.error);
    return null;
  }

  ok(`Session created: ${result.sessionId}`);
  ok(`Game mode resolved: ${result.state.game_mode}`);
  ok(`Player health: ${result.state.player.health}/${result.state.player.max_health}`);
  ok(`Enemies: ${result.state.entities.enemy_count}`);
  ok(`Theme: ${result.state.world.theme}`);

  printState(result.state, 'Initial State (status: initializing)');

  // Integrity check on initial state
  const integrityCheck = guard.validateState(result.state);
  if (integrityCheck.valid) {
    ok('Integrity guard: initial state is valid');
  } else {
    fail('Integrity guard: initial state invalid', integrityCheck.violations.join('; '));
  }

  return result.sessionId;
}

// ─── Stage 4: Engine Runs ─────────────────────────────────────────────────────

async function stage4_engineRuns(sessionId) {
  banner('STAGE 4 — Engine Runs');

  step('Registering 3 enemies in active_entities');

  // Spawn 3 enemies so entity_destroyed events are valid
  const spawnEvents = [
    makeEvent('entity_spawned', ['enemy_001'], { entity_type: 'enemy', position: { x: 5, y: 0, z: 0 } }),
    makeEvent('entity_spawned', ['enemy_002'], { entity_type: 'enemy', position: { x: 10, y: 0, z: 0 } }),
    makeEvent('entity_spawned', ['enemy_003'], { entity_type: 'enemy', position: { x: 15, y: 0, z: 0 } })
  ];

  for (const ev of spawnEvents) {
    const r = sep.processEvent(sessionId, ev);
    if (!r.success) { fail(`Spawn ${ev.entities[0]}`, r.error); return false; }
  }
  ok('3 enemies registered in active_entities');

  step('Sending game_start event');
  const startEvent = makeEvent('game_start', [], {});
  const startResult = sep.processEvent(sessionId, startEvent);

  if (!startResult.success) {
    fail('game_start event', startResult.error);
    return false;
  }

  ok(`Status → ${startResult.state.status}`);
  printState(startResult.state, 'State after game_start');
  return true;
}

// ─── Stage 5 & 6 & 7: Runtime Events + State Updates + Consequence Jobs ───────

async function stage5_6_7_eventsAndConsequences(sessionId, executionData) {
  banner('STAGE 5 — Runtime Events  →  STAGE 6 — State Updates  →  STAGE 7 — Consequence Jobs');

  const events = [
    // Event 1: enemy_001 killed → score +100, enemy_count -1
    {
      label: 'Enemy killed (enemy_001)',
      event: makeEvent('entity_destroyed', ['enemy_001'], { entity_type: 'enemy', score_delta: 100 })
    },
    // Event 2: pickup coin → score +10, collectible_count -1
    {
      label: 'Coin collected',
      event: makeEvent('pickup_collected', ['player', 'coin_001'], { entity_type: 'collectible', pickup_type: 'coin' })
    },
    // Event 3: score_update → triggers high_score_difficulty_boost if score >= 500
    {
      label: 'Score update (direct +400)',
      event: makeEvent('score_update', ['player'], { score_delta: 400 })
    },
    // Event 4: health_changed -2 → triggers low_health_warning (health drops to <=1 for arena mode health=5 → 3 → 1)
    {
      label: 'Health changed (-4 damage)',
      event: makeEvent('health_changed', ['player'], { delta: -4 })
    },
    // Event 5: enemy_002 killed → enemy_count -1
    {
      label: 'Enemy killed (enemy_002)',
      event: makeEvent('entity_destroyed', ['enemy_002'], { entity_type: 'enemy', score_delta: 100 })
    },
    // Event 6: enemy_003 killed → enemy_count = 0 → triggers enemy_killed_wave_clear
    {
      label: 'Enemy killed (enemy_003) — last enemy → wave clear',
      event: makeEvent('entity_destroyed', ['enemy_003'], { entity_type: 'enemy', score_delta: 100 })
    }
  ];

  let eventIndex = 0;
  for (const { label, event } of events) {
    eventIndex++;
    console.log(`\n  ── Event ${eventIndex}: ${label}`);

    const stateBefore = gsm.getCurrentState(sessionId);

    // Guard check
    const guardCheck = guard.validateEvent(event, stateBefore);
    if (!guardCheck.valid) {
      fail(`Guard blocked event: ${label}`, guardCheck.violations.join('; '));
      continue;
    }

    // Apply event via SEP
    const sepResult = sep.processEvent(sessionId, event);
    if (!sepResult.success) {
      fail(`SEP failed: ${label}`, sepResult.error);
      continue;
    }

    ok(`State updated — changes: ${JSON.stringify(sepResult.changes)}`);

    // Transition integrity
    const transCheck = guard.validateTransition(stateBefore, event, sepResult.state);
    if (transCheck.valid) {
      ok('Transition integrity: valid');
    } else {
      fail('Transition integrity violation', transCheck.violations.join('; '));
    }

    printState(sepResult.state, `State after event ${eventIndex}`);

    // Append to event trace
    await bucketWriter.appendEventTrace(sessionId, sepResult.event || event, sepResult.changes)
      .catch(() => {});

    // Consequence jobs (state-aware)
    const compResult = compiler.processEventWithState(event, { sessionId });
    if (compResult.success && compResult.jobs.length > 0) {
      ok(`Consequence jobs generated: ${compResult.jobs.length}`);
      compResult.jobs.forEach(job => {
        console.log(`     → [${job.priority.toUpperCase()}] ${job.jobType}`);
        if (job.payload.reason)       console.log(`          reason      : ${job.payload.reason}`);
        if (job.payload.score_delta)  console.log(`          score_delta : ${job.payload.score_delta}`);
        if (job.payload.sound_id)     console.log(`          sound_id    : ${job.payload.sound_id}`);
        if (job.payload.wave_size)    console.log(`          wave_size   : ${job.payload.wave_size}`);
      });
    } else if (compResult.success) {
      console.log('     → No consequence jobs (no matching rules)');
    } else {
      fail('Consequence compiler error', compResult.error);
    }
  }

  return true;
}

// ─── Stage: Session End + Bucket Artifacts ────────────────────────────────────

async function stage_sessionEnd(sessionId, executionData) {
  banner('SESSION END — Bucket Artifacts');

  step('Writing final snapshot + execution schema to bucket');

  const endResult = await bucketWriter.writeSessionEnd(
    sessionId,
    executionData.execution_id,
    executionData.trace_id,
    executionData.executionSchema
  );

  if (endResult.success) {
    ok('Final snapshot written');
    ok('Execution schema written');
  } else {
    fail('Session end write', JSON.stringify(endResult));
  }

  const finalState = gsm.getCurrentState(sessionId);
  printState(finalState, 'FINAL STATE');

  // Final integrity check
  const finalCheck = guard.validateState(finalState);
  if (finalCheck.valid) {
    ok('Final state integrity: valid');
  } else {
    fail('Final state integrity', finalCheck.violations.join('; '));
  }

  gsm.destroySession(sessionId);
  ok(`Session ${sessionId} destroyed from memory`);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n╔══════════════════════════════════════════════════════════════╗');
  console.log('║   PHASE 10 — FULL PIPELINE DEMONSTRATION                     ║');
  console.log('║   Prompt → Generation → State → Engine → Events → Jobs       ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');

  try {
    // Stage 1
    const executionData = await stage1_prompt();

    // Stages 2 & 3
    const sessionId = await stage2_3_gameGeneration(executionData);
    if (!sessionId) throw new Error('Session creation failed — aborting demo');

    // Stage 4
    const engineOk = await stage4_engineRuns(sessionId);
    if (!engineOk) throw new Error('Engine start failed — aborting demo');

    // Stages 5, 6, 7
    await stage5_6_7_eventsAndConsequences(sessionId, executionData);

    // Session end
    await stage_sessionEnd(sessionId, executionData);

  } catch (err) {
    failed++;
    console.error(`\n  FATAL: ${err.message}`);
  }

  // ─── Summary ────────────────────────────────────────────────────────────────
  banner('DEMO SUMMARY');
  console.log(`  Checks passed : ${passed}`);
  console.log(`  Checks failed : ${failed}`);
  console.log(`  Result        : ${failed === 0 ? '✔  ALL CHECKS PASSED' : '✘  SOME CHECKS FAILED'}\n`);

  process.exit(failed === 0 ? 0 : 1);
}

main();

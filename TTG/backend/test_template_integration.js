/**
 * End-to-End Test: Game Template → Dispatcher → Job Queue
 *
 * Tests the full chain:
 * Intent text → selectTemplate → validateTemplate → injectParameters
 *             → mapSchemaToJobs → addJob → job lifecycle
 *
 * Covers: runner, platformer, arena + parameter overrides
 */

// ─── Mock Job Queue ───────────────────────────────────────────────────────────
const jobsAdded = [];
const mockJobQueue = {
  addJob: (job, callback) => {
    job.status = 'queued';
    jobsAdded.push(job);
    setTimeout(() => { job.status = 'dispatched';
      setTimeout(() => { job.status = 'running';
        setTimeout(() => { job.status = 'completed'; if (callback) callback(job, 'completed', null); }, 60);
      }, 60);
    }, 60);
  },
  clearAllJobs: () => {},
  setEngineConnected: () => {},
  findJobById: (id) => jobsAdded.find(j => j.jobId === id) || null
};
require.cache[require.resolve('./jobQueue')] = {
  id: require.resolve('./jobQueue'), filename: require.resolve('./jobQueue'),
  loaded: true, exports: mockJobQueue
};

// ─── Mock side-effect modules ─────────────────────────────────────────────────
const mockNoop = { appendExecutionLog: async () => {} };
require.cache[require.resolve('./bucketWriter')] = {
  id: require.resolve('./bucketWriter'), filename: require.resolve('./bucketWriter'),
  loaded: true, exports: mockNoop
};
const mockTelemetry = { recordJobStarted: () => {}, recordJobCompleted: () => {}, recordExecutionDuration: () => {} };
require.cache[require.resolve('./telemetry/behaviourRecorder')] = {
  id: require.resolve('./telemetry/behaviourRecorder'), filename: require.resolve('./telemetry/behaviourRecorder'),
  loaded: true, exports: mockTelemetry
};

// ─── Imports ──────────────────────────────────────────────────────────────────
const { selectTemplate } = require('./game-templates/templateSelector');
const { injectParameters, extractParameters } = require('./game-templates/parameterInjector');
const { validateTemplate } = require('./game-templates/templateValidator');
const { mapSchemaToJobs, dispatchExecution } = require('./executionDispatcher');
const { storeExecution } = require('./executionRegistry');

// ─── Helpers ──────────────────────────────────────────────────────────────────
let passed = 0, failed = 0;

function assert(condition, label) {
  if (condition) { console.log(`  ✅ ${label}`); passed++; }
  else           { console.log(`  ❌ ${label}`); failed++; }
}
function section(title) {
  console.log(`\n${'─'.repeat(62)}`);
  console.log(`  ${title}`);
  console.log('─'.repeat(62));
}

// ─── 1. Template Selection ────────────────────────────────────────────────────
section('1 — Template Selection (keyword matching)');

const runnerT    = selectTemplate('make a fast runner with obstacles');
const platformerT = selectTemplate('create a platform jump game');
const arenaT     = selectTemplate('survival arena with enemies');
const defaultT   = selectTemplate('some unknown game type');

assert(runnerT.template_id    === 'runner_v1',    `Runner template selected (got ${runnerT.template_id})`);
assert(platformerT.template_id === 'platformer_v1', `Platformer template selected (got ${platformerT.template_id})`);
assert(arenaT.template_id     === 'arena_v1',     `Arena template selected (got ${arenaT.template_id})`);
assert(defaultT.template_id   === 'runner_v1',    `Default falls back to runner (got ${defaultT.template_id})`);

// ─── 2. Template Validation ───────────────────────────────────────────────────
section('2 — Template Validation against engineCapabilities.json');

const rv = validateTemplate(runnerT);
const pv = validateTemplate(platformerT);
const av = validateTemplate(arenaT);

assert(rv.valid, `Runner template valid (errors: ${rv.errors.join(', ') || 'none'})`);
assert(pv.valid, `Platformer template valid (errors: ${pv.errors.join(', ') || 'none'})`);
assert(av.valid, `Arena template valid (errors: ${av.errors.join(', ') || 'none'})`);

// ─── 3. Parameter Injection ───────────────────────────────────────────────────
section('3 — Parameter Injection (defaults + intent overrides)');

// 3a: defaults only
const defaultConfig = injectParameters(runnerT, {});
assert(defaultConfig.parameters.movement_speed === 5,  `Runner default speed = 5 (got ${defaultConfig.parameters.movement_speed})`);
assert(defaultConfig.parameters.spawn_frequency === 3, `Runner default spawn_frequency = 3 (got ${defaultConfig.parameters.spawn_frequency})`);
assert(defaultConfig.parameters.lane_count === 3,      `Runner default lane_count = 3 (got ${defaultConfig.parameters.lane_count})`);

// 3b: intent overrides
const fastParams = extractParameters('make a fast runner with hard difficulty');
assert(fastParams.movement_speed === 8,    `extractParameters: fast → speed 8 (got ${fastParams.movement_speed})`);
assert(fastParams.spawn_frequency === 1.5, `extractParameters: hard → spawn_frequency 1.5 (got ${fastParams.spawn_frequency})`);

const fastConfig = injectParameters(runnerT, fastParams);
assert(fastConfig.parameters.movement_speed === 8,    `Injected fast speed = 8 (got ${fastConfig.parameters.movement_speed})`);
assert(fastConfig.parameters.spawn_frequency === 1.5, `Injected hard spawn_frequency = 1.5 (got ${fastConfig.parameters.spawn_frequency})`);

// 3c: schema value overrides template param
const schemaOverride = injectParameters(runnerT, { movement_speed: 12 });
assert(schemaOverride.parameters.movement_speed === 12, `Schema override: speed 12 wins (got ${schemaOverride.parameters.movement_speed})`);

// 3d: arena defaults
const arenaConfig = injectParameters(arenaT, {});
assert(arenaConfig.parameters.enemy_count === 5,   `Arena default enemy_count = 5 (got ${arenaConfig.parameters.enemy_count})`);
assert(arenaConfig.parameters.arena_size === 20,   `Arena default arena_size = 20 (got ${arenaConfig.parameters.arena_size})`);

// ─── 4. Job Generation (mapSchemaToJobs) ──────────────────────────────────────
section('4 — Job Generation from Template + Schema');

const runnerSchema = {
  game_mode: 'runner', movement: { speed: 6 },
  physics: { gravity: -9.8 }, spawn_rules: { frequency: 2.5 },
  score_rules: { distance: 1, collectibles: 10 },
  end_conditions: ['collision'], player_params: { health: 3 }
};
const runnerConfig = injectParameters(runnerT, extractParameters('fast runner'));
const runnerJobs = mapSchemaToJobs(
  runnerSchema, 'exec_runner_001', 'trace_001', 'user_01',
  runnerConfig.jobs, { ...runnerConfig.parameters, _template_id: runnerT.template_id }
);

assert(runnerJobs.length === 4, `Runner: 4 jobs generated (got ${runnerJobs.length})`);
assert(runnerJobs[0].jobType === 'BUILD_SCENE',   `Job 0: BUILD_SCENE`);
assert(runnerJobs[1].jobType === 'SPAWN_ENTITY',  `Job 1: SPAWN_ENTITY (player)`);
assert(runnerJobs[2].jobType === 'SPAWN_ENTITY',  `Job 2: SPAWN_ENTITY (obstacle_spawner)`);
assert(runnerJobs[3].jobType === 'START_LOOP',    `Job 3: START_LOOP`);

const startLoop = runnerJobs[3];
assert(startLoop.payload.template_id === 'runner_v1',  `START_LOOP carries template_id`);
assert(startLoop.payload.params.movement_speed === 6,  `START_LOOP uses schema speed 6 (schema wins over template)`);
assert(startLoop.payload.params.spawn_rules.interval === 2.5, `START_LOOP spawn interval = 2.5 from schema`);

const obstacleJob = runnerJobs[2];
assert(obstacleJob.payload.spawn_rules?.lane_count === 3, `Obstacle spawner has lane_count from template`);

// Arena jobs
const arenaSchema = {
  game_mode: 'open_scene', movement: { speed: 5 },
  physics: { gravity: -9.8 }, spawn_rules: { frequency: 4, obstacles: 8 },
  score_rules: { distance: 0, collectibles: 50 },
  end_conditions: ['collision'], player_params: { health: 100 }
};
const arenaConfigFull = injectParameters(arenaT, {});
const arenaJobs = mapSchemaToJobs(
  arenaSchema, 'exec_arena_001', 'trace_002', 'user_01',
  arenaConfigFull.jobs, { ...arenaConfigFull.parameters, _template_id: arenaT.template_id }
);

assert(arenaJobs.length === 5, `Arena: 5 jobs generated (got ${arenaJobs.length})`);
const enemyJob = arenaJobs.find(j => j.payload?.id === 'enemy_spawner');
assert(enemyJob !== undefined,          `Arena: enemy_spawner job exists`);
assert(enemyJob.payload.count === 8,    `Arena: enemy count = 8 from schema (got ${enemyJob.payload.count})`);
assert(enemyJob.payload.health === 50,  `Arena: enemy health = 50 from template (got ${enemyJob.payload.health})`);

// ─── 5. Full dispatchExecution flow ──────────────────────────────────────────
section('5 — Full dispatchExecution (intent text → jobs in queue)');

jobsAdded.length = 0;

const execution = storeExecution({
  execution_id: 'exec_e2e_001',
  trace_id: 'trace_e2e_001',
  user_id: 'test_user',
  executionSchema: {
    game_mode: 'runner', movement: { speed: 7 },
    physics: { gravity: -9.8 }, spawn_rules: { frequency: 2.0 },
    score_rules: { distance: 1, collectibles: 10 },
    end_conditions: ['collision'], player_params: { health: 3 }
  },
  intent: { prompt: 'make a fast runner with obstacles and hard difficulty' }
});

dispatchExecution(execution).then(result => {
  assert(result.success === true,   `dispatchExecution succeeded`);
  assert(result.jobCount === 4,     `4 jobs dispatched (got ${result.jobCount})`);

  const loopJob = jobsAdded.find(j => j.jobType === 'START_LOOP');
  assert(loopJob !== undefined,                          `START_LOOP job in queue`);
  assert(loopJob.payload.template_id === 'runner_v1',   `START_LOOP has template_id = runner_v1`);
  assert(loopJob.payload.params.movement_speed === 7,   `Speed = 7 from schema (got ${loopJob.payload.params.movement_speed})`);
  assert(loopJob.payload.params.spawn_rules.interval === 1.5, `Hard difficulty → spawn interval 1.5 (got ${loopJob.payload.params.spawn_rules.interval})`);

  // ─── 6. Job lifecycle ──────────────────────────────────────────────────────
  section('6 — Job Lifecycle (queued → dispatched → running → completed)');

  setTimeout(() => {
    const completed = jobsAdded.filter(j => j.status === 'completed');
    assert(completed.length === jobsAdded.length, `All ${jobsAdded.length} jobs completed`);

    const jobTypes = jobsAdded.map(j => j.jobType);
    assert(jobTypes.includes('BUILD_SCENE'),  `BUILD_SCENE completed`);
    assert(jobTypes.includes('SPAWN_ENTITY'), `SPAWN_ENTITY completed`);
    assert(jobTypes.includes('START_LOOP'),   `START_LOOP completed`);

    // ─── Summary ──────────────────────────────────────────────────────────────
    console.log(`\n${'═'.repeat(62)}`);
    console.log('  END-TO-END TEST RESULTS');
    console.log('═'.repeat(62));
    console.log(`  ✅ Passed : ${passed}`);
    console.log(`  ❌ Failed : ${failed}`);
    console.log(`  Total     : ${passed + failed}`);
    console.log('═'.repeat(62));

    if (failed === 0) {
      console.log('\n  🎮 Game Template → Dispatcher → Job Queue: FULLY WIRED\n');
    } else {
      console.log('\n  ⚠️  Some checks failed — review output above\n');
    }

    process.exit(failed === 0 ? 0 : 1);
  }, 400);
});

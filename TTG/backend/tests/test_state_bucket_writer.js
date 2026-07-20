// test_state_bucket_writer.js - Test Phase 5: State Bucket Writer
// Run: node tests/test_state_bucket_writer.js

const path = require('path');
const fs   = require('fs').promises;

const gsm              = require('../state/gameStateManager');
const snapshot         = require('../state/stateSnapshot');
const stateBucketWriter = require('../state/stateBucketWriter');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function pass(msg) { console.log(`  ✅ ${msg}`); }
function fail(msg) { console.log(`  ❌ ${msg}`); }

async function fileExists(filepath) {
  try { await fs.access(filepath); return true; }
  catch { return false; }
}

async function readJson(filepath) {
  const raw = await fs.readFile(filepath, 'utf8');
  return JSON.parse(raw);
}

async function readJsonl(filepath) {
  const raw   = await fs.readFile(filepath, 'utf8');
  const lines = raw.trim().split('\n').filter(Boolean);
  return lines.map(l => JSON.parse(l));
}

// ─── Setup: create a live session ────────────────────────────────────────────

const SESSION_ID   = `test_session_${Date.now()}`;
const EXECUTION_ID = `exec_test_${Date.now()}`;
const TRACE_ID     = `trace_test_${Date.now()}`;

const MOCK_TEMPLATE = {
  template_id: 'runner_v1',
  defaults: { player_health: 3, obstacle_count: 3 }
};

const MOCK_SCHEMA = {
  module: 'game_generation',
  intent: 'create runner game',
  game_mode: 'runner',
  movement: { speed: 5 },
  physics: { gravity: -9.8 }
};

const MOCK_EVENT = {
  event_id:        `evt_${Date.now()}`,
  event_type:      'pickup_collected',
  timestamp:       Date.now(),
  game_session_id: SESSION_ID,
  entities:        ['player', 'coin_001'],
  context:         { entity_type: 'collectible', score_delta: 10 }
};

// ─── Tests ────────────────────────────────────────────────────────────────────

async function test1_writeStateSnapshot() {
  console.log('\n=== Test 1: writeStateSnapshot ===');

  const state = gsm.createGameState(SESSION_ID, MOCK_TEMPLATE, {
    execution_id: EXECUTION_ID,
    trace_id:     TRACE_ID
  });

  if (!state) { fail('GSM did not create state'); return false; }
  pass(`Session created — mode: ${state.game_mode}, health: ${state.player.health}`);

  const result = await stateBucketWriter.writeStateSnapshot(SESSION_ID);

  if (!result.success) { fail(`writeStateSnapshot failed: ${result.error}`); return false; }
  pass(`writeStateSnapshot returned success, version: ${result.version}`);

  // Check versioned file exists
  const versionedFile = path.join(BUCKET_DIR, `state_snapshot_${SESSION_ID}_v0.json`);
  if (await fileExists(versionedFile)) {
    pass(`Versioned file written: state_snapshot_${SESSION_ID}_v0.json`);
  } else {
    fail('Versioned snapshot file not found on disk');
    return false;
  }

  // Check latest file exists
  const latestFile = path.join(BUCKET_DIR, `state_snapshot_${SESSION_ID}.json`);
  if (await fileExists(latestFile)) {
    pass(`Latest file written: state_snapshot_${SESSION_ID}.json`);
  } else {
    fail('Latest snapshot file not found on disk');
    return false;
  }

  // Validate content
  const artifact = await readJson(latestFile);
  if (artifact.artifact_type === 'state_snapshot') {
    pass(`artifact_type correct: ${artifact.artifact_type}`);
  } else {
    fail(`Wrong artifact_type: ${artifact.artifact_type}`);
  }

  if (artifact.state.session_id === SESSION_ID) {
    pass(`session_id matches: ${artifact.state.session_id}`);
  } else {
    fail(`session_id mismatch: ${artifact.state.session_id}`);
  }

  if (artifact.state.player.health === 3) {
    pass(`player.health correct: ${artifact.state.player.health}`);
  } else {
    fail(`player.health wrong: ${artifact.state.player.health}`);
  }

  return true;
}

async function test2_writeExecutionSchema() {
  console.log('\n=== Test 2: writeExecutionSchema ===');

  const result = await stateBucketWriter.writeExecutionSchema(
    SESSION_ID, EXECUTION_ID, TRACE_ID, MOCK_SCHEMA
  );

  if (!result.success) { fail(`writeExecutionSchema failed: ${result.error}`); return false; }
  pass('writeExecutionSchema returned success');

  const schemaFile = path.join(BUCKET_DIR, `state_exec_schema_${SESSION_ID}.json`);
  if (await fileExists(schemaFile)) {
    pass(`Schema file written: state_exec_schema_${SESSION_ID}.json`);
  } else {
    fail('Schema file not found on disk');
    return false;
  }

  const artifact = await readJson(schemaFile);
  if (artifact.artifact_type === 'state_execution_schema') {
    pass(`artifact_type correct: ${artifact.artifact_type}`);
  } else {
    fail(`Wrong artifact_type: ${artifact.artifact_type}`);
  }

  if (artifact.execution_id === EXECUTION_ID) {
    pass(`execution_id matches: ${artifact.execution_id}`);
  } else {
    fail(`execution_id mismatch: ${artifact.execution_id}`);
  }

  if (artifact.trace_id === TRACE_ID) {
    pass(`trace_id matches: ${artifact.trace_id}`);
  } else {
    fail(`trace_id mismatch: ${artifact.trace_id}`);
  }

  if (artifact.source === 'game_state_engine') {
    pass(`source correct: ${artifact.source}`);
  } else {
    fail(`source wrong: ${artifact.source}`);
  }

  return true;
}

async function test3_appendEventTrace() {
  console.log('\n=== Test 3: appendEventTrace ===');

  const mockChanges = { field: 'entities.collectible_count', from: 5, to: 4 };

  // Append 3 events to verify JSONL accumulation
  for (let i = 0; i < 3; i++) {
    const event = { ...MOCK_EVENT, event_id: `evt_${Date.now()}_${i}`, timestamp: Date.now() };
    const result = await stateBucketWriter.appendEventTrace(SESSION_ID, event, mockChanges);
    if (!result.success) { fail(`appendEventTrace failed on entry ${i}: ${result.error}`); return false; }
  }
  pass('3 event trace entries appended');

  const traceFile = path.join(BUCKET_DIR, `state_event_trace_${SESSION_ID}.jsonl`);
  if (await fileExists(traceFile)) {
    pass(`Trace file written: state_event_trace_${SESSION_ID}.jsonl`);
  } else {
    fail('Trace file not found on disk');
    return false;
  }

  const entries = await readJsonl(traceFile);
  if (entries.length === 3) {
    pass(`JSONL has 3 entries (append-only confirmed)`);
  } else {
    fail(`Expected 3 entries, got ${entries.length}`);
    return false;
  }

  const entry = entries[0];
  if (entry.session_id === SESSION_ID)  pass(`entry.session_id correct`);
  else fail(`entry.session_id wrong: ${entry.session_id}`);

  if (entry.event_type === 'pickup_collected') pass(`entry.event_type correct`);
  else fail(`entry.event_type wrong: ${entry.event_type}`);

  if (entry.changes && entry.changes.field === 'entities.collectible_count') {
    pass(`entry.changes correct: ${JSON.stringify(entry.changes)}`);
  } else {
    fail(`entry.changes wrong: ${JSON.stringify(entry.changes)}`);
  }

  return true;
}

async function test4_writeSessionEnd() {
  console.log('\n=== Test 4: writeSessionEnd ===');

  // Use a fresh session so snapshot_version starts at 0
  const endSessionId = `test_end_${Date.now()}`;
  gsm.createGameState(endSessionId, MOCK_TEMPLATE, {
    execution_id: EXECUTION_ID,
    trace_id:     TRACE_ID
  });

  const result = await stateBucketWriter.writeSessionEnd(
    endSessionId, EXECUTION_ID, TRACE_ID, MOCK_SCHEMA
  );

  if (!result.success) { fail(`writeSessionEnd failed`); return false; }
  pass('writeSessionEnd returned success');

  if (result.snapshot.success) pass('snapshot written');
  else fail(`snapshot failed: ${result.snapshot.error}`);

  if (result.schema.success) pass('schema written');
  else fail(`schema failed: ${result.schema.error}`);

  // Verify both files exist
  const snapFile   = path.join(BUCKET_DIR, `state_snapshot_${endSessionId}.json`);
  const schemaFile = path.join(BUCKET_DIR, `state_exec_schema_${endSessionId}.json`);

  if (await fileExists(snapFile))   pass('snapshot file on disk');
  else fail('snapshot file missing');

  if (await fileExists(schemaFile)) pass('schema file on disk');
  else fail('schema file missing');

  return true;
}

async function test5_snapshotVersionIncrement() {
  console.log('\n=== Test 5: Snapshot version increments on each write ===');

  // Write a second snapshot for the original session — should be v1 now
  const result = await stateBucketWriter.writeStateSnapshot(SESSION_ID);
  if (!result.success) { fail(`Second snapshot failed: ${result.error}`); return false; }

  if (result.version === 1) {
    pass(`Version incremented correctly: v${result.version}`);
  } else {
    fail(`Expected version 1, got ${result.version}`);
    return false;
  }

  const v1File = path.join(BUCKET_DIR, `state_snapshot_${SESSION_ID}_v1.json`);
  if (await fileExists(v1File)) pass('v1 file exists on disk');
  else fail('v1 file not found');

  return true;
}

// ─── Run all tests ────────────────────────────────────────────────────────────

async function runAll() {
  console.log('🧪 Phase 5: State Bucket Writer Tests');
  console.log(`   Session ID : ${SESSION_ID}`);
  console.log(`   Bucket Dir : ${BUCKET_DIR}\n`);

  const results = [];
  results.push(await test1_writeStateSnapshot());
  results.push(await test2_writeExecutionSchema());
  results.push(await test3_appendEventTrace());
  results.push(await test4_writeSessionEnd());
  results.push(await test5_snapshotVersionIncrement());

  const passed = results.filter(Boolean).length;
  const total  = results.length;

  console.log(`\n${'─'.repeat(50)}`);
  console.log(`Results: ${passed}/${total} tests passed`);

  if (passed === total) {
    console.log('✅ Phase 5 complete — all bucket artifacts verified on disk');
  } else {
    console.log('❌ Some tests failed — check output above');
    process.exit(1);
  }
}

runAll().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

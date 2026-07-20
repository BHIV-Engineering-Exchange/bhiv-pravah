'use strict';

/**
 * test_replay_engine.js
 *
 * Runs replayEngine.replay() against real bucket artifacts.
 * Prints full ReplayResult — no mocking, no stubs.
 *
 * Usage:
 *   node backend/domain-adapters/maritime/test_replay_engine.js
 */

const { replay } = require('./replayEngine');

const TRACES = [
  'maritime_c9e761c9-2f30-4d29-9e00-5875ae6c6f0c',  // ALLOW — full 5-artifact set
  'maritime_86e9faac-a6b8-4692-909d-875507bc7ee8',   // partial set (no decision) — expect ARTIFACT_LOAD_FAILED
  'nonexistent_trace_000'                             // missing — expect ARTIFACT_LOAD_FAILED
];

async function run() {
  for (const trace_id of TRACES) {
    console.log('\n' + '═'.repeat(72));
    console.log(`REPLAY: ${trace_id}`);
    console.log('═'.repeat(72));

    const result = await replay(trace_id);

    if (result.success) {
      console.log(`✅ SUCCESS`);
      console.log(`   path         : ${result.path}`);
      console.log(`   decision     : ${result.decision}`);
      console.log(`   risk_level   : ${result.risk_level}`);
      console.log(`   execution_id : ${result.execution_id}`);
      console.log(`   event_count  : ${result.event_count}`);
      console.log(`   sequence     : ${result.sequence.join(' → ')}`);
      console.log(`   state        :`, result.state_summary);
    } else {
      console.log(`❌ FAILED`);
      console.log(`   code   : ${result.failure.failure_code}`);
      console.log(`   reason : ${result.failure.reason}`);
      if (Object.keys(result.failure.meta).length > 0) {
        console.log(`   meta   :`, JSON.stringify(result.failure.meta, null, 2));
      }
    }

    console.log(`\n   replay_log (${result.replay_log.length} entries):`);
    result.replay_log.forEach(e => console.log(`     [${e.stage}] ${e.message}`));
  }
}

run().catch(err => {
  console.error('[TEST] Unhandled error:', err);
  process.exit(1);
});

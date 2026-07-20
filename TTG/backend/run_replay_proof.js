'use strict';

/**
 * run_replay_proof.js
 *
 * Executes replayEngine.replay() against two real artifact sets:
 *   1. maritime_c9e761c9  — maritime pipeline ALLOW path (5 artifacts)
 *   2. p8-allow-test      — BHIV pipeline ALLOW path    (5 artifacts)
 *
 * For each trace:
 *   - Loads original execution artifacts from bucket_artifacts/
 *   - Runs the replay engine (trace retrieval → event reconstruction
 *     → state reconstruction → replay execution → validation)
 *   - Compares replay result against original artifacts
 *   - Writes REPLAY_RESULT.json with full match analysis
 *
 * Run:
 *   cd backend
 *   node run_replay_proof.js
 */

const path = require('path');
const fs   = require('fs');
const { replay } = require('./domain-adapters/maritime/replayEngine');

const BUCKET_DIR   = path.join(__dirname, 'bucket_artifacts');
const OUTPUT_FILE  = path.join(__dirname, '..', 'REPLAY_RESULT.json');

// ── Load original artifacts for comparison ────────────────────────────────────

function loadOriginal(trace_id) {
  const base = path.join(BUCKET_DIR, `execution_${trace_id}`);
  const result = {};

  // schema
  try {
    result.schema = JSON.parse(fs.readFileSync(`${base}_schema.json`, 'utf8'));
  } catch { result.schema = null; }

  // decision
  try {
    result.decision = JSON.parse(fs.readFileSync(`${base}_decision.json`, 'utf8'));
  } catch { result.decision = null; }

  // events
  try {
    const raw = fs.readFileSync(`${base}_events.jsonl`, 'utf8');
    result.events = raw.split('\n').map(l => l.trim()).filter(Boolean).map(JSON.parse.bind(JSON));
  } catch { result.events = []; }

  // state
  try {
    result.state = JSON.parse(fs.readFileSync(`${base}_state.json`, 'utf8'));
  } catch { result.state = null; }

  // log
  try {
    const raw = fs.readFileSync(`${base}_log.jsonl`, 'utf8');
    result.log = raw.split('\n').map(l => l.trim()).filter(Boolean).map(JSON.parse.bind(JSON));
  } catch { result.log = []; }

  return result;
}

// ── Match analysis ─────────────────────────────────────────────────────────────

function analyseMatch(trace_id, original, replayResult) {
  const checks = [];

  function check(field, expected, got, pass) {
    checks.push({ field, expected, got, pass });
  }

  // 1. Replay succeeded
  check('replay_success', true, replayResult.success, replayResult.success === true);

  // 2. trace_id preserved
  check('trace_id', trace_id, replayResult.trace_id, replayResult.trace_id === trace_id);

  // 3. execution_id preserved
  const orig_exec = original.schema?.execution_id;
  check('execution_id', orig_exec, replayResult.execution_id, replayResult.execution_id === orig_exec);

  // 4. Decision matches
  const orig_decision = original.decision?.decision_envelope?.decision
                     || original.schema?.governance?.decision
                     || original.schema?.mitra_decision;
  check('decision', orig_decision, replayResult.decision, replayResult.decision === orig_decision);

  // 5. Risk level matches
  const orig_risk = original.decision?.decision_envelope?.risk_level
                 || original.schema?.governance?.risk_level;
  check('risk_level', orig_risk, replayResult.risk_level, replayResult.risk_level === orig_risk);

  // 6. Event count matches
  check('event_count', original.events.length, replayResult.event_count,
        replayResult.event_count === original.events.length);

  // 7. Required stage sequence present
  const required = ['decision_received','enforcement_applied','execution_started','execution_completed'];
  const seqOk = required.every(s => replayResult.sequence?.includes(s));
  check('stage_sequence', required.join('→'), replayResult.sequence?.join('→'), seqOk);

  // 8. Path matches enforcement result
  const orig_path = original.decision?.enforcement_result?.passed === true ? 'ALLOW' : 'BLOCK';
  check('execution_path', orig_path, replayResult.path, replayResult.path === orig_path);

  // 9. State execution_id matches
  const orig_state_exec = original.state?.execution_id;
  check('state.execution_id', orig_state_exec, replayResult.state_summary?.execution_id,
        replayResult.state_summary?.execution_id === orig_state_exec);

  const passed = checks.filter(c => c.pass).length;
  const total  = checks.length;

  return {
    trace_id,
    passed,
    total,
    all_passed: passed === total,
    checks
  };
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main() {
  const TRACES = [
    'maritime_c9e761c9-2f30-4d29-9e00-5875ae6c6f0c',
    'p8-allow-test'
  ];

  const proof = {
    generated_at: new Date().toISOString(),
    replay_engine: 'backend/domain-adapters/maritime/replayEngine.js',
    endpoint: 'POST /pipeline/replay/:trace_id',
    traces: []
  };

  let allPassed = true;

  for (const trace_id of TRACES) {
    console.log('\n' + '═'.repeat(70));
    console.log(`REPLAY: ${trace_id}`);
    console.log('═'.repeat(70));

    // Load original
    const original = loadOriginal(trace_id);
    const orig_artifacts = Object.entries(original)
      .filter(([, v]) => v !== null && (Array.isArray(v) ? v.length > 0 : true))
      .map(([k]) => k);
    console.log(`[ORIGINAL] Artifacts loaded: ${orig_artifacts.join(', ')}`);

    // Run replay
    const started_at = Date.now();
    const replayResult = await replay(trace_id);
    const elapsed_ms   = Date.now() - started_at;

    // Print replay log
    replayResult.replay_log.forEach(e =>
      console.log(`  [REPLAY:${e.stage.padEnd(12)}] ${e.message}`)
    );

    // Match analysis
    const match = analyseMatch(trace_id, original, replayResult);

    console.log('\n  Match Analysis:');
    match.checks.forEach(c => {
      const icon = c.pass ? '✓' : '✗';
      console.log(`    ${icon} ${c.field.padEnd(22)} expected=${JSON.stringify(c.expected)}  got=${JSON.stringify(c.got)}`);
    });
    console.log(`\n  Result: ${match.passed}/${match.total} checks passed — ${match.all_passed ? 'FULL MATCH ✓' : 'PARTIAL MATCH ✗'}`);

    if (!match.all_passed) allPassed = false;

    proof.traces.push({
      trace_id,
      original: {
        execution_id:  original.schema?.execution_id,
        decision:      original.decision?.decision_envelope?.decision || original.schema?.governance?.decision || original.schema?.mitra_decision,
        risk_level:    original.decision?.decision_envelope?.risk_level || original.schema?.governance?.risk_level,
        event_count:   original.events.length,
        artifacts_present: orig_artifacts
      },
      replay: {
        success:       replayResult.success,
        trace_id:      replayResult.trace_id,
        execution_id:  replayResult.execution_id,
        path:          replayResult.path,
        decision:      replayResult.decision,
        risk_level:    replayResult.risk_level,
        event_count:   replayResult.event_count,
        sequence:      replayResult.sequence,
        state_summary: replayResult.state_summary,
        failure:       replayResult.failure,
        elapsed_ms
      },
      match
    });
  }

  proof.overall_passed = allPassed;
  proof.summary = {
    traces_tested:  proof.traces.length,
    traces_passed:  proof.traces.filter(t => t.match.all_passed).length,
    traces_failed:  proof.traces.filter(t => !t.match.all_passed).length
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(proof, null, 2), 'utf8');
  console.log('\n' + '═'.repeat(70));
  console.log(`REPLAY PROOF written to: REPLAY_RESULT.json`);
  console.log(`Overall: ${proof.summary.traces_passed}/${proof.summary.traces_tested} traces fully matched`);
  console.log('═'.repeat(70));

  process.exit(allPassed ? 0 : 1);
}

main().catch(err => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

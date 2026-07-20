'use strict';

/**
 * test_phase5_telemetry.js
 *
 * Phase 5 — Telemetry Emission Verification
 *
 * Tests:
 *   1. All 4 stages emit correctly (in-memory)
 *   2. Every event is trace-linked (trace_id + execution_id + telemetry_id)
 *   3. File transport — telemetry_<trace_id>.jsonl written and readable
 *   4. File content is valid JSONL — every line parses correctly
 *   5. File events match in-memory stream exactly
 *   6. Missing trace_id → not emitted, returns null
 *   7. Missing execution_id → not emitted, returns null
 *   8. HTTP transport fires when TELEMETRY_HTTP_ENDPOINT is set
 *   9. HTTP transport failure is non-fatal — pipeline continues
 *  10. Two traces produce two separate telemetry files
 *
 * Run: node backend/domain-adapters/maritime/test_phase5_telemetry.js
 */

const fs   = require('fs');
const path = require('path');
const http = require('http');

const ib = require('./insightBridge');

const BUCKET_DIR = path.join(__dirname, '../../bucket_artifacts');

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

// Clean up test telemetry files before run
function cleanFile(trace_id) {
  const f = path.join(BUCKET_DIR, `telemetry_${trace_id}.jsonl`);
  if (fs.existsSync(f)) fs.unlinkSync(f);
}

// Read and parse a .jsonl file
function readJsonl(trace_id) {
  const f = path.join(BUCKET_DIR, `telemetry_${trace_id}.jsonl`);
  if (!fs.existsSync(f)) return null;
  return fs.readFileSync(f, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

async function run() {

  // ── Case 1 & 2: All 4 stages emit, every event trace-linked ──────────────
  console.log('\n── Case 1+2: All 4 stages emit, every event trace-linked ──────');
  {
    const TRACE = 'trace-p5-main';
    const EXEC  = 'exec_p5_001';
    cleanFile(TRACE);
    ib._clearStream(TRACE);

    const e1 = ib.emitDecisionReceived(TRACE, EXEC, {
      decision: 'ALLOW', risk_level: 'LOW', confidence: 0.95,
      reason: 'passed', mitra_trace_id: 'mitra-001', signal_type: 'implicit_positive',
      source: 'mitra', decided_at: Date.now()
    });
    const e2 = ib.emitEnforcementApplied(TRACE, EXEC, {
      passed: true, blocked: false, flagged: false,
      decision: 'ALLOW', reason: 'gate passed', source: 'mitra', enforced_at: Date.now()
    });
    const e3 = ib.emitExecutionStarted(TRACE, EXEC, { vessel_count: 3, game_mode: 'open_scene' });
    const e4 = ib.emitExecutionCompleted(TRACE, EXEC, { status: 'completed', duration: 850 });

    check('decision_received emitted',   e1 !== null);
    check('enforcement_applied emitted', e2 !== null);
    check('execution_started emitted',   e3 !== null);
    check('execution_completed emitted', e4 !== null);

    // trace-linked checks
    for (const [label, ev] of [['e1', e1], ['e2', e2], ['e3', e3], ['e4', e4]]) {
      check(`${label} has trace_id`,     ev.trace_id     === TRACE);
      check(`${label} has execution_id`, ev.execution_id === EXEC);
      check(`${label} has telemetry_id`, typeof ev.telemetry_id === 'string' && ev.telemetry_id.length > 0);
      check(`${label} has timestamp`,    typeof ev.timestamp === 'number');
      check(`${label} has stage`,        typeof ev.stage === 'string');
    }

    // in-memory stream
    const stream = ib.getStream(TRACE);
    check('in-memory stream has 4 events', stream.length === 4);
    check('stages in order', stream.map(e => e.stage).join(',') ===
      'decision_received,enforcement_applied,execution_started,execution_completed');
  }

  // ── Case 3 & 4 & 5: File transport ───────────────────────────────────────
  console.log('\n── Case 3+4+5: File transport — JSONL written and valid ────────');
  {
    const TRACE = 'trace-p5-main';
    const EXEC  = 'exec_p5_001';

    // small delay to ensure sync writes are flushed
    await new Promise(r => setTimeout(r, 50));

    const lines = readJsonl(TRACE);
    check('telemetry file exists',         lines !== null, `expected at ${BUCKET_DIR}`);

    if (lines) {
      check('file has 4 lines',            lines.length === 4);
      check('all lines parse as JSON',     lines.every(l => typeof l === 'object'));
      check('all lines have trace_id',     lines.every(l => l.trace_id === TRACE));
      check('all lines have execution_id', lines.every(l => l.execution_id === EXEC));
      check('all lines have telemetry_id', lines.every(l => typeof l.telemetry_id === 'string'));
      check('all lines have stage',        lines.every(l => typeof l.stage === 'string'));

      // file matches in-memory
      const stream = ib.getStream(TRACE);
      const fileIds   = lines.map(l => l.telemetry_id).sort();
      const memIds    = stream.map(e => e.telemetry_id).sort();
      check('file telemetry_ids match memory', JSON.stringify(fileIds) === JSON.stringify(memIds));

      // stages in file
      check('stages in file correct', lines.map(l => l.stage).join(',') ===
        'decision_received,enforcement_applied,execution_started,execution_completed');
    }
  }

  // ── Case 6: Missing trace_id → not emitted ────────────────────────────────
  console.log('\n── Case 6: Missing trace_id → not emitted ──────────────────────');
  {
    const r = ib.emitDecisionReceived(null, 'exec_p5_c6', {
      decision: 'ALLOW', risk_level: 'LOW', confidence: 0.9,
      reason: 'test', mitra_trace_id: 'x', source: 'mitra', decided_at: Date.now()
    });
    check('returns null',              r === null);
    check('no file created for null',  !fs.existsSync(path.join(BUCKET_DIR, 'telemetry_null.jsonl')));
  }

  // ── Case 7: Missing execution_id → not emitted ───────────────────────────
  console.log('\n── Case 7: Missing execution_id → not emitted ──────────────────');
  {
    const r = ib.emitExecutionStarted('trace-p5-c7', null, { vessel_count: 1 });
    check('returns null',              r === null);
  }

  // ── Case 8: HTTP transport fires when endpoint is set ────────────────────
  console.log('\n── Case 8: HTTP transport fires when endpoint is set ───────────');
  {
    await new Promise((resolve) => {
      const received = [];

      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', c => { body += c; });
        req.on('end', () => {
          try { received.push(JSON.parse(body)); } catch {}
          res.writeHead(200);
          res.end();
        });
      });

      server.listen(19876, () => {
        process.env.TELEMETRY_HTTP_ENDPOINT = 'http://localhost:19876/telemetry';

        const TRACE = 'trace-p5-http';
        ib._clearStream(TRACE);
        cleanFile(TRACE);

        ib.emitExecutionStarted(TRACE, 'exec_p5_http', { test: true });

        // wait for async HTTP call
        setTimeout(() => {
          check('HTTP transport received 1 event', received.length === 1);
          if (received.length > 0) {
            check('HTTP event has trace_id',     received[0].trace_id     === TRACE);
            check('HTTP event has execution_id', received[0].execution_id === 'exec_p5_http');
            check('HTTP event has stage',        received[0].stage        === 'execution_started');
            check('HTTP event has telemetry_id', typeof received[0].telemetry_id === 'string');
          }
          delete process.env.TELEMETRY_HTTP_ENDPOINT;
          server.close(resolve);
        }, 200);
      });
    });
  }

  // ── Case 9: HTTP transport failure is non-fatal ───────────────────────────
  console.log('\n── Case 9: HTTP transport failure is non-fatal ─────────────────');
  {
    process.env.TELEMETRY_HTTP_ENDPOINT = 'http://localhost:19999/telemetry'; // nothing here
    const TRACE = 'trace-p5-nonfatal';
    ib._clearStream(TRACE);
    cleanFile(TRACE);

    let threw = false;
    try {
      ib.emitExecutionCompleted(TRACE, 'exec_p5_nonfatal', { status: 'completed' });
    } catch {
      threw = true;
    }

    check('no exception thrown',       threw === false);
    check('in-memory event still written', ib.getStream(TRACE).length === 1);

    await new Promise(r => setTimeout(r, 200)); // let HTTP attempt fail
    check('file still written despite HTTP failure',
      fs.existsSync(path.join(BUCKET_DIR, `telemetry_${TRACE}.jsonl`)));

    delete process.env.TELEMETRY_HTTP_ENDPOINT;
  }

  // ── Case 10: Two traces → two separate files ──────────────────────────────
  console.log('\n── Case 10: Two traces → two separate telemetry files ──────────');
  {
    const T1 = 'trace-p5-iso-1';
    const T2 = 'trace-p5-iso-2';
    cleanFile(T1); cleanFile(T2);
    ib._clearStream(T1); ib._clearStream(T2);

    ib.emitDecisionReceived(T1, 'exec_iso_1', {
      decision: 'ALLOW', risk_level: 'LOW', confidence: 0.9,
      reason: 'ok', mitra_trace_id: 'mt1', source: 'mitra', decided_at: Date.now()
    });
    ib.emitDecisionReceived(T2, 'exec_iso_2', {
      decision: 'BLOCK', risk_level: 'HIGH', confidence: 0.99,
      reason: 'blocked', mitra_trace_id: 'mt2', source: 'mitra', decided_at: Date.now()
    });
    ib.emitEnforcementApplied(T1, 'exec_iso_1', {
      passed: true, blocked: false, flagged: false, decision: 'ALLOW', reason: 'ok'
    });

    await new Promise(r => setTimeout(r, 50));

    const f1 = readJsonl(T1);
    const f2 = readJsonl(T2);

    check('T1 file has 2 events',      f1 && f1.length === 2);
    check('T2 file has 1 event',       f2 && f2.length === 1);
    check('T1 file only has T1 trace', f1 && f1.every(e => e.trace_id === T1));
    check('T2 file only has T2 trace', f2 && f2.every(e => e.trace_id === T2));
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n══════════════════════════════════════════════════════');
  console.log(`Phase 5 Telemetry Emission — ${passed + failed} checks`);
  console.log(`  ✅ Passed : ${passed}`);
  console.log(`  ❌ Failed : ${failed}`);
  console.log(`  Status   : ${failed === 0 ? 'PHASE 5 COMPLETE ✅' : 'NEEDS FIXES ❌'}`);
  console.log('══════════════════════════════════════════════════════\n');
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('[TEST] Fatal:', err.message);
  process.exit(1);
});

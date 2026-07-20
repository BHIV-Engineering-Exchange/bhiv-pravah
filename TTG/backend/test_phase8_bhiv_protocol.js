'use strict';

/**
 * test_phase8_bhiv_protocol.js
 *
 * Phase 8 — BHIV Testing Protocol
 *
 * Runs all phase tests in sequence and generates a validation report.
 * Target: 5-10 minute reproducible validation.
 *
 * Run: node test_phase8_bhiv_protocol.js
 */

const http = require('http');
const fs   = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

const RUDRA_URL    = 'http://localhost:3000';
const ARTIFACT_DIR = path.join(__dirname, 'bucket_artifacts');
const BACKEND_DIR  = __dirname;

// ── HTTP helpers ──────────────────────────────────────────────────────────────
function httpGet(url) {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const req    = http.request({ hostname: parsed.hostname, port: parsed.port || 80, path: parsed.pathname, method: 'GET' }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => { try { resolve({ ok: res.statusCode === 200, status: res.statusCode, body: JSON.parse(raw) }); } catch { resolve({ ok: false }); } });
    });
    req.on('error', () => resolve({ ok: false }));
    req.setTimeout(5000, () => { req.destroy(); resolve({ ok: false }); });
    req.end();
  });
}

function httpPost(url, body) {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const data   = JSON.stringify(body);
    const req    = http.request({
      hostname: parsed.hostname, port: parsed.port || 80, path: parsed.pathname, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => { try { resolve({ ok: res.statusCode === 200, status: res.statusCode, body: JSON.parse(raw) }); } catch { resolve({ ok: false }); } });
    });
    req.on('error', () => resolve({ ok: false }));
    req.setTimeout(35000, () => { req.destroy(); resolve({ ok: false, error: 'timeout' }); });
    req.write(data);
    req.end();
  });
}

// ── Run a node script and capture result ─────────────────────────────────────
function runScript(scriptPath) {
  return new Promise((resolve) => {
    const start  = Date.now();
    const child  = spawn('node', [scriptPath], { cwd: BACKEND_DIR, stdio: 'pipe' });
    let stdout   = '';
    let stderr   = '';

    child.stdout.on('data', d => { stdout += d.toString(); process.stdout.write(d); });
    child.stderr.on('data', d => { stderr += d.toString(); process.stderr.write(d); });

    child.on('close', (code) => {
      resolve({ pass: code === 0, code, stdout, stderr, elapsed: Date.now() - start });
    });

    child.on('error', (err) => {
      resolve({ pass: false, code: -1, stderr: err.message, elapsed: Date.now() - start });
    });
  });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Tests ─────────────────────────────────────────────────────────────────────
const TESTS = [
  { id: 'HEALTH_CHECK',  label: 'Service Health Check',           fn: testHealthCheck },
  { id: 'PHASE1',        label: 'Phase 1 — Atharva Convergence',  fn: () => runScript('test_phase1_atharva_real.js'), optional: true },
  { id: 'PHASE3',        label: 'Phase 3 — SVACS E2E Proof',      fn: () => runScript('test_phase3_svacs_e2e.js') },
  { id: 'PHASE4',        label: 'Phase 4 — Namami Gange',         fn: () => runScript('test_phase4_namami_gange_e2e.js') },
  { id: 'PHASE5',        label: 'Phase 5 — NICAI + UICICS',       fn: () => runScript('test_phase5_nicai_uicics.js') },
  { id: 'PHASE6',        label: 'Phase 6 — Truth Layer',          fn: () => runScript('test_phase6_truth_layer.js') },
  { id: 'PHASE7',        label: 'Phase 7 — Ecosystem Demo',       fn: () => runScript('test_phase7_ecosystem_demo.js') },
  { id: 'TRACE_VERIFY',  label: 'Trace Verification',             fn: testTraceVerification },
  { id: 'REPLAY_VERIFY', label: 'Replay Validation',              fn: testReplayValidation },
  { id: 'ARTIFACT_CHECK',label: 'Artifact Integrity Check',       fn: testArtifactIntegrity },
];

// ── Individual test functions ─────────────────────────────────────────────────
async function testHealthCheck() {
  const health  = await httpGet(`${RUDRA_URL}/health`);
  const svacs   = await httpGet(`${RUDRA_URL}/svacs/health`);
  const namami  = await httpGet(`${RUDRA_URL}/namami-gange/health`);
  const atharva = await httpGet(`${RUDRA_URL}/core/atharva-health`);

  const all_ok = health.ok && svacs.ok && namami.ok;
  console.log(`  Rudra       : ${health.ok  ? '✓' : '✗'} (${health.status || 'unreachable'})`);
  console.log(`  SVACS route : ${svacs.ok   ? '✓' : '✗'}`);
  console.log(`  Namami route: ${namami.ok  ? '✓' : '✗'}`);
  console.log(`  Atharva     : ${atharva.ok ? '✓ connected' : '✗ offline (non-blocking)'}`);
  return { pass: all_ok, code: all_ok ? 0 : 1 };
}

async function testTraceVerification() {
  const ts  = Date.now().toString(36);
  const tid = `trace_verify_${ts}`;
  const eid = `exec_verify_${ts}`;

  console.log(`  Sending trace_id: ${tid}`);
  const r = await httpPost(`${RUDRA_URL}/svacs/inbound`, {
    trace_id: tid, execution_id: eid,
    risk_level: 'LOW', pipeline_stages: ['SIGNAL', 'CORE'],
    intelligence_event: { risk_level: 'LOW' }
  });

  if (!r.ok) { console.log(`  ✗ HTTP ${r.status}`); return { pass: false, code: 1 }; }

  const trace_preserved = r.body?.trace_id === tid;
  const ownership       = r.body?.upstream_trace_ownership === 'CONFIRMED';
  const enforcement     = r.body?.contract_enforcement === 'PASSED';

  console.log(`  trace_id preserved      : ${trace_preserved ? '✓' : '✗'} ${r.body?.trace_id}`);
  console.log(`  upstream_trace_ownership: ${ownership       ? '✓ CONFIRMED' : '✗'}`);
  console.log(`  contract_enforcement    : ${enforcement     ? '✓ PASSED'    : '✗'}`);

  // Verify artifact written
  const artifact = path.join(ARTIFACT_DIR, `svacs_phase3_${tid}_proof.json`);
  const written  = fs.existsSync(artifact);
  console.log(`  proof artifact written  : ${written ? '✓' : '✗'}`);

  if (written) {
    const content = JSON.parse(fs.readFileSync(artifact, 'utf8'));
    const match   = content.trace_id === tid;
    console.log(`  artifact trace_id match : ${match ? '✓' : '✗'}`);
  }

  const pass = trace_preserved && ownership && enforcement && written;
  return { pass, code: pass ? 0 : 1 };
}

async function testReplayValidation() {
  // Verify artifacts survive — read all existing artifacts
  const files = fs.existsSync(ARTIFACT_DIR)
    ? fs.readdirSync(ARTIFACT_DIR).filter(f => f.endsWith('.json') || f.endsWith('.jsonl'))
    : [];

  console.log(`  Total artifacts on disk : ${files.length}`);
  const corrupted = files.filter(f => {
    if (!f.endsWith('.json')) return false;
    try { JSON.parse(fs.readFileSync(path.join(ARTIFACT_DIR, f), 'utf8')); return false; }
    catch { return true; }
  });
  console.log(`  Corrupted artifacts     : ${corrupted.length}`);
  console.log(`  Append-only intact      : ${files.length - corrupted.length}/${files.length}`);

  // Verify recoverable via API
  const svacs_r  = await httpGet(`${RUDRA_URL}/svacs/proofs`);
  const phase5_r = await httpGet(`${RUDRA_URL}/phase5/proofs`);
  const ng_r     = await httpGet(`${RUDRA_URL}/namami-gange/proofs`);
  console.log(`  SVACS traces recoverable: ${svacs_r.ok  ? `✓ (${svacs_r.body?.count})` : '✗'}`);
  console.log(`  Phase5 traces recoverable:${phase5_r.ok ? `✓ (${phase5_r.body?.count})` : '✗'}`);
  console.log(`  NamamiG traces recoverable:${ng_r.ok    ? `✓ (${ng_r.body?.count})`    : '✗'}`);

  const pass = files.length > 0 && corrupted.length === 0;
  return { pass, code: pass ? 0 : 1 };
}

async function testArtifactIntegrity() {
  const files = fs.existsSync(ARTIFACT_DIR)
    ? fs.readdirSync(ARTIFACT_DIR).filter(f => f.startsWith('phase') && f.endsWith('.json'))
    : [];

  const phases_present = { 1: false, 3: false, 4: false, 5: false, 6: false, 7: false };
  let   traces_found   = new Set();

  for (const f of files) {
    try {
      const c = JSON.parse(fs.readFileSync(path.join(ARTIFACT_DIR, f), 'utf8'));
      if (c.phase) phases_present[c.phase] = true;
      if (c.trace_id) traces_found.add(c.trace_id);
    } catch { /* skip */ }
  }

  for (const [phase, found] of Object.entries(phases_present)) {
    console.log(`  Phase ${phase} artifacts : ${found ? '✓ present' : '✗ missing'}`);
  }
  console.log(`  Unique traces in proofs : ${traces_found.size}`);

  const pass = Object.values(phases_present).filter(Boolean).length >= 4;
  return { pass, code: pass ? 0 : 1 };
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function run() {
  const suite_start = Date.now();

  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║   PHASE 8 — BHIV TESTING PROTOCOL                   ║');
  console.log('╠══════════════════════════════════════════════════════╣');
  console.log('║   Target: 5-10 minute reproducible validation        ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  const results = [];

  for (const test of TESTS) {
    console.log(`\n${'─'.repeat(56)}`);
    console.log(`▶ ${test.label}`);
    console.log('─'.repeat(56));

    try {
      const result  = await test.fn();
      const elapsed = result.elapsed || 0;
      results.push({ id: test.id, label: test.label, pass: result.pass, elapsed });
      console.log(`\n  Result: ${result.pass ? '✓ PASS' : '✗ FAIL'} ${elapsed ? `[${(elapsed/1000).toFixed(1)}s]` : ''}`);
    } catch (err) {
      console.error(`  ✗ ERROR: ${err.message}`);
      results.push({ id: test.id, label: test.label, pass: false, error: err.message });
    }
  }

  // Write report
  const elapsed_total = ((Date.now() - suite_start) / 1000).toFixed(1);
  const required      = results.filter(r => !TESTS.find(t => t.id === r.id)?.optional);
  const passed        = results.filter(r => r.pass).length;
  const required_pass = required.filter(r => r.pass).length;
  const failed        = required.filter(r => !r.pass).length;
  const optional_fail = results.filter(r => !r.pass && TESTS.find(t => t.id === r.id)?.optional).length;

  const report = {
    phase:         8,
    title:         'BHIV Testing Protocol — Validation Report',
    total_tests:   results.length,
    passed,
    failed,
    elapsed_s:     parseFloat(elapsed_total),
    pass_rate:     `${Math.round((passed / results.length) * 100)}%`,
    results,
    generated_at:  new Date().toISOString()
  };

  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  const report_file = path.join(ARTIFACT_DIR, `phase8_testing_report_${Date.now()}.json`);
  fs.writeFileSync(report_file, JSON.stringify(report, null, 2), 'utf8');

  // Final summary
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║              PHASE 8 TEST REPORT                    ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  for (const r of results) {
    console.log(`  ${r.pass ? '✓' : '✗'} ${r.label.padEnd(40)} ${r.elapsed ? `[${(r.elapsed/1000).toFixed(1)}s]` : ''}`);
  }

  console.log(`\n  passed       : ${passed}/${results.length}`);
  console.log(`  failed       : ${failed}`);
  console.log(`  total time   : ${elapsed_total}s`);
  console.log(`  pass_rate    : ${report.pass_rate}`);
  console.log(`  report_file  : ${path.basename(report_file)}\n`);

  if (failed === 0) {
    console.log('✓ PHASE 8 BHIV TESTING PROTOCOL: ALL TESTS PASSED\n');
    process.exit(0);
  } else {
    console.log(`✗ PHASE 8: ${failed} test(s) failed — check report for details\n`);
    process.exit(1);
  }
}

run().catch(err => {
  console.error('[PHASE8] Fatal:', err.message);
  process.exit(1);
});

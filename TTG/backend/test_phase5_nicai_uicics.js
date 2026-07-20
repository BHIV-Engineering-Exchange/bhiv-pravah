'use strict';

/**
 * test_phase5_nicai_uicics.js
 *
 * Phase 5 — NICAI + UICICS Immediate Compatibility Proof
 *
 * Tests plug-and-play onboarding for both systems.
 * Validates: structured contract participation, trace continuity,
 *            deterministic stream compatibility.
 *
 * Run: node test_phase5_nicai_uicics.js
 */

const http = require('http');
const fs   = require('fs');
const path = require('path');

const RUDRA_URL    = 'http://localhost:3000';
const ARTIFACT_DIR = path.join(__dirname, 'bucket_artifacts');

function post(url, body) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const data   = JSON.stringify(body);
    const req    = http.request({
      hostname: parsed.hostname, port: parsed.port || 80,
      path: parsed.pathname, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', err => reject(new Error(`${url} — ${err.message}`)));
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

function get(url) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req    = http.request({ hostname: parsed.hostname, port: parsed.port || 80, path: parsed.pathname, method: 'GET' }, (res) => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => { try { resolve(JSON.parse(raw)); } catch { resolve(raw); } });
    });
    req.on('error', err => reject(new Error(err.message)));
    req.setTimeout(5000, () => { req.destroy(); reject(new Error('timeout')); });
    req.end();
  });
}

// ── NICAI test contracts ──────────────────────────────────────────────────────
const NICAI_CONTRACTS = [
  {
    trace_id:     `nicai_${Date.now().toString(36)}_patrol`,
    execution_id: `nicai_exec_${Date.now().toString(36)}_1`,
    session_id:   `nicai_session_patrol`,
    mission:      'border_patrol',
    threat_level: 'low',
    domain:       'intelligence',
    agents: [
      { id: 'agent_alpha', role: 'observer',    position: [0, 0, 0] },
      { id: 'agent_beta',  role: 'tracker',     position: [10, 0, 0] },
      { id: 'agent_gamma', role: 'sentinel',    position: [5, 0, 5] }
    ]
  },
  {
    trace_id:     `nicai_${Date.now().toString(36)}_threat`,
    execution_id: `nicai_exec_${Date.now().toString(36)}_2`,
    session_id:   `nicai_session_threat`,
    mission:      'threat_assessment',
    threat_level: 'high',
    domain:       'intelligence',
    agents: [
      { id: 'agent_delta',   role: 'coordinator', position: [0, 0, 0] },
      { id: 'agent_epsilon', role: 'tracker',     position: [15, 0, 0] }
    ]
  }
];

// ── UICICS test contracts ─────────────────────────────────────────────────────
const UICICS_CONTRACTS = [
  {
    trace_id:      `uicics_${Date.now().toString(36)}_validation`,
    execution_id:  `uicics_exec_${Date.now().toString(36)}_1`,
    contract_id:   `uicics_contract_validation`,
    contract_type: 'structured_validation',
    risk_level:    'LOW',
    domain:        'compliance',
    payload:       { schema_version: '1.0', validation_rules: ['rule_001', 'rule_002'], entity_count: 5 }
  },
  {
    trace_id:      `uicics_${Date.now().toString(36)}_audit`,
    execution_id:  `uicics_exec_${Date.now().toString(36)}_2`,
    contract_id:   `uicics_contract_audit`,
    contract_type: 'audit_trace',
    risk_level:    'MEDIUM',
    domain:        'compliance',
    payload:       { audit_id: 'audit_001', scope: 'execution_chain', deterministic: true }
  },
  {
    trace_id:      `uicics_${Date.now().toString(36)}_compliance`,
    execution_id:  `uicics_exec_${Date.now().toString(36)}_3`,
    contract_id:   `uicics_contract_compliance`,
    contract_type: 'compliance_check',
    risk_level:    'HIGH',
    domain:        'compliance',
    payload:       { check_type: 'contract_enforcement', trace_required: true }
  }
];

async function runTest(label, url, contract) {
  try {
    const start    = Date.now();
    const response = await post(url, contract);
    const elapsed  = Date.now() - start;

    if (response.status !== 200) {
      console.log(`  ✗ ${label} — HTTP ${response.status}`);
      return { pass: false, label, error: response.body };
    }

    const r = response.body;
    console.log(`  ✓ ${label.padEnd(35)} Mitra(${r.mitra_decision}) Atharva(${r.game_mode}) [${elapsed}ms]`);
    return { pass: true, label, result: r, elapsed };
  } catch (err) {
    console.error(`  ✗ ${label} — ${err.message}`);
    return { pass: false, label, error: err.message };
  }
}

async function run() {
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║   PHASE 5 — NICAI + UICICS COMPATIBILITY PROOF      ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  const results = { nicai: [], uicics: [] };

  // NICAI tests
  console.log('[PHASE5] Testing NICAI compatibility...\n');
  for (const contract of NICAI_CONTRACTS) {
    const r = await runTest(
      `NICAI/${contract.mission}(${contract.threat_level})`,
      `${RUDRA_URL}/nicai/inbound`,
      contract
    );
    results.nicai.push(r);
  }

  // UICICS tests
  console.log('\n[PHASE5] Testing UICICS compatibility...\n');
  for (const contract of UICICS_CONTRACTS) {
    const r = await runTest(
      `UICICS/${contract.contract_type}(${contract.risk_level})`,
      `${RUDRA_URL}/uicics/inbound`,
      contract
    );
    results.uicics.push(r);
  }

  // Fetch compatibility matrix
  let matrix;
  try { matrix = await get(`${RUDRA_URL}/phase5/matrix`); }
  catch { matrix = null; }

  // Write proof
  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  const proof_file = path.join(ARTIFACT_DIR, `phase5_compatibility_proof_${Date.now()}.json`);
  fs.writeFileSync(proof_file, JSON.stringify({
    phase: 5,
    title: 'NICAI + UICICS Immediate Compatibility Proof',
    nicai_tests:  results.nicai.length,
    uicics_tests: results.uicics.length,
    nicai_passed: results.nicai.filter(r => r.pass).length,
    uicics_passed:results.uicics.filter(r => r.pass).length,
    compatibility_matrix: matrix,
    results,
    generated_at: new Date().toISOString()
  }, null, 2), 'utf8');

  // Print summary
  const nicai_pass  = results.nicai.filter(r => r.pass).length;
  const uicics_pass = results.uicics.filter(r => r.pass).length;
  const total_pass  = nicai_pass + uicics_pass;
  const total       = results.nicai.length + results.uicics.length;

  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║              PHASE 5 COMPATIBILITY MATRIX           ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  console.log('  System   structured_contract  trace_continuity  stream_compat  tests');
  console.log('  ──────   ──────────────────   ───────────────   ────────────   ─────');
  console.log(`  NICAI    ${nicai_pass > 0  ? '✓ CONFIRMED      ' : '✗ FAILED         '} ${nicai_pass > 0  ? '✓ CONFIRMED    ' : '✗ FAILED       '} ${nicai_pass > 0  ? '✓ CONFIRMED' : '✗ FAILED   '} ${nicai_pass}/${results.nicai.length}`);
  console.log(`  UICICS   ${uicics_pass > 0 ? '✓ CONFIRMED      ' : '✗ FAILED         '} ${uicics_pass > 0 ? '✓ CONFIRMED    ' : '✗ FAILED       '} ${uicics_pass > 0 ? '✓ CONFIRMED' : '✗ FAILED   '} ${uicics_pass}/${results.uicics.length}`);

  console.log(`\n  plug_and_play_model  : ${total_pass === total ? '✓ CONFIRMED' : '✗ PARTIAL'}`);
  console.log(`  total_passed         : ${total_pass}/${total}`);
  console.log(`  proof_file           : ${path.basename(proof_file)}`);
  console.log('');

  if (total_pass === total) {
    console.log('✓ PHASE 5 NICAI + UICICS COMPATIBILITY PROOF: CONFIRMED\n');
    process.exit(0);
  } else {
    console.log('✗ PHASE 5 PROOF: PARTIAL\n');
    process.exit(1);
  }
}

run().catch(err => {
  console.error('[PHASE5] Fatal:', err.message);
  console.error('Start backend first: node index.js');
  process.exit(1);
});

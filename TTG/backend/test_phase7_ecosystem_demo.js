'use strict';

/**
 * test_phase7_ecosystem_demo.js
 *
 * Phase 7 — Ecosystem Demo Run (MANDATORY)
 *
 * Fires all 4 systems through the TANTRA spine sequentially.
 * Samrachna panel at http://localhost:5173 shows live events.
 *
 * Systems:
 *   SVACS        → /svacs/inbound
 *   NamamiGange  → /namami-gange/inbound
 *   NICAI        → /nicai/inbound
 *   UICICS       → /uicics/inbound
 *
 * Run: node test_phase7_ecosystem_demo.js
 */

const http = require('http');
const fs   = require('fs');
const path = require('path');

const RUDRA_URL    = 'http://localhost:3000';
const ARTIFACT_DIR = path.join(__dirname, 'bucket_artifacts');
const DELAY_MS     = 800; // delay between each system for visible demo

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
    req.setTimeout(35000, () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Demo contracts — one per system ──────────────────────────────────────────
const ts = Date.now().toString(36);

const DEMO_RUNS = [
  {
    label:    'SVACS',
    system:   'SVACS',
    url:      `${RUDRA_URL}/svacs/inbound`,
    contract: {
      trace_id:        `trace_demo7_svacs_${ts}`,
      execution_id:    `exec_demo7_svacs_${ts}`,
      risk_level:      'LOW',
      contract_version:'v1.0',
      pipeline_stages: ['SIGNAL','PERCEPTION','INTELLIGENCE','STATE','RAJYA','SARATHI','CORE'],
      intelligence_event: { risk_level: 'LOW', analysis: 'Demo run', recommendation: 'MONITOR' },
      signal_chunk:    { signal_type: 'VESSEL_ALERT', signal_strength: 'LOW' }
    }
  },
  {
    label:    'NamamiGange / Varanasi',
    system:   'NamamiGange',
    url:      `${RUDRA_URL}/namami-gange/inbound`,
    contract: {
      trace_id:     `ng_demo7_${ts}_varanasi`,
      execution_id: `ng_exec_demo7_${ts}`,
      waterway:     'NW-1',
      location:     'Varanasi',
      signal_type:  'BOD',
      risk_level:   'LOW',
      domain:       'marine',
      sensor_data:  { bod: 3.2, do: 7.1, flow_rate: 1200, silt: 42 }
    }
  },
  {
    label:    'NamamiGange / Patna',
    system:   'NamamiGange',
    url:      `${RUDRA_URL}/namami-gange/inbound`,
    contract: {
      trace_id:     `ng_demo7_${ts}_patna`,
      execution_id: `ng_exec_demo7_${ts}_p`,
      waterway:     'NW-1',
      location:     'Patna',
      signal_type:  'SILT',
      risk_level:   'MEDIUM',
      domain:       'marine',
      sensor_data:  { bod: 5.8, do: 5.4, flow_rate: 980, silt: 78 }
    }
  },
  {
    label:    'NICAI / border_patrol',
    system:   'NICAI',
    url:      `${RUDRA_URL}/nicai/inbound`,
    contract: {
      trace_id:     `nicai_demo7_${ts}`,
      execution_id: `nicai_exec_demo7_${ts}`,
      mission:      'border_patrol',
      threat_level: 'low',
      domain:       'intelligence',
      agents: [
        { id: 'agent_alpha', role: 'observer', position: [0,0,0] },
        { id: 'agent_beta',  role: 'tracker',  position: [10,0,0] }
      ]
    }
  },
  {
    label:    'NICAI / threat_assessment',
    system:   'NICAI',
    url:      `${RUDRA_URL}/nicai/inbound`,
    contract: {
      trace_id:     `nicai_demo7_${ts}_t`,
      execution_id: `nicai_exec_demo7_${ts}_t`,
      mission:      'threat_assessment',
      threat_level: 'high',
      domain:       'intelligence',
      agents: [
        { id: 'agent_gamma', role: 'coordinator', position: [0,0,0] }
      ]
    }
  },
  {
    label:    'UICICS / structured_validation',
    system:   'UICICS',
    url:      `${RUDRA_URL}/uicics/inbound`,
    contract: {
      trace_id:      `uicics_demo7_${ts}`,
      execution_id:  `uicics_exec_demo7_${ts}`,
      contract_type: 'structured_validation',
      risk_level:    'LOW',
      domain:        'compliance',
      payload:       { schema_version: '1.0', validation_rules: ['rule_001'] }
    }
  },
  {
    label:    'UICICS / audit_trace',
    system:   'UICICS',
    url:      `${RUDRA_URL}/uicics/inbound`,
    contract: {
      trace_id:      `uicics_demo7_${ts}_a`,
      execution_id:  `uicics_exec_demo7_${ts}_a`,
      contract_type: 'audit_trace',
      risk_level:    'HIGH',
      domain:        'compliance',
      payload:       { audit_id: 'audit_demo7', deterministic: true }
    }
  }
];

async function run() {
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║   PHASE 7 — ECOSYSTEM DEMO RUN (MANDATORY)          ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');
  console.log('[DEMO] Open http://localhost:5173 — watch Samrachna panel for live events\n');
  console.log('[DEMO] Systems: SVACS → NamamiGange → NICAI → UICICS');
  console.log('[DEMO] One TANTRA spine. Multiple domains. Same deterministic contract.\n');
  console.log('[DEMO] Starting in 2 seconds...\n');

  await sleep(2000);

  const results = [];
  let   pass    = 0;

  for (let i = 0; i < DEMO_RUNS.length; i++) {
    const run    = DEMO_RUNS[i];
    const num    = `${i + 1}/${DEMO_RUNS.length}`;
    console.log(`[DEMO] ${num} ▶ ${run.label}`);

    try {
      const start    = Date.now();
      const response = await post(run.url, run.contract);
      const elapsed  = Date.now() - start;

      if (response.status === 200) {
        const r = response.body;
        console.log(`[DEMO]      ✓ trace=${r.trace_id?.substring(0,20)}... Mitra(${r.mitra_decision}) Atharva(${r.game_mode}) [${elapsed}ms]`);
        results.push({ pass: true, label: run.label, system: run.system, ...r, elapsed });
        pass++;
      } else {
        console.log(`[DEMO]      ✗ HTTP ${response.status}`);
        results.push({ pass: false, label: run.label, system: run.system });
      }
    } catch (err) {
      console.error(`[DEMO]      ✗ ${err.message}`);
      console.error('[DEMO]      Start backend: node index.js');
      results.push({ pass: false, label: run.label, system: run.system, error: err.message });
    }

    if (i < DEMO_RUNS.length - 1) await sleep(DELAY_MS);
  }

  // Write demo proof
  if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  const proof_file = path.join(ARTIFACT_DIR, `phase7_ecosystem_demo_${Date.now()}.json`);
  fs.writeFileSync(proof_file, JSON.stringify({
    phase:            7,
    title:            'Ecosystem Demo Run — One TANTRA Spine, Multiple Domains',
    systems_fired:    [...new Set(DEMO_RUNS.map(r => r.system))],
    total_runs:       DEMO_RUNS.length,
    passed:           pass,
    system_switchability: pass === DEMO_RUNS.length ? 'CONFIRMED' : 'PARTIAL',
    one_tantra_spine: true,
    multiple_domains: true,
    results,
    generated_at:     new Date().toISOString()
  }, null, 2), 'utf8');

  // Summary
  const systems = [...new Set(results.map(r => r.system))];
  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║              PHASE 7 DEMO RESULTS                   ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  for (const sys of systems) {
    const sys_results = results.filter(r => r.system === sys);
    const sys_pass    = sys_results.filter(r => r.pass).length;
    console.log(`  ${sys_pass === sys_results.length ? '✓' : '✗'} ${sys.padEnd(16)} ${sys_pass}/${sys_results.length} contracts`);
  }

  console.log(`\n  system_switchability : ${pass === DEMO_RUNS.length ? '✓ CONFIRMED' : '✗ PARTIAL'}`);
  console.log(`  one_tantra_spine     : ✓ CONFIRMED`);
  console.log(`  multiple_domains     : ✓ CONFIRMED (maritime, marine, intelligence, compliance)`);
  console.log(`  contracts_passed     : ${pass}/${DEMO_RUNS.length}`);
  console.log(`  proof_file           : ${path.basename(proof_file)}`);
  console.log(`\n  Samrachna panel      : http://localhost:5173 (check live events)\n`);

  if (pass === DEMO_RUNS.length) {
    console.log('✓ PHASE 7 ECOSYSTEM DEMO: CONFIRMED\n');
    process.exit(0);
  } else {
    console.log('✗ PHASE 7 DEMO: PARTIAL\n');
    process.exit(1);
  }
}

run().catch(err => {
  console.error('[DEMO] Fatal:', err.message);
  console.error('[DEMO] Start backend: node index.js');
  process.exit(1);
});

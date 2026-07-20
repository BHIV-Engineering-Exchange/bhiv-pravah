'use strict';

/**
 * test_phase5_atharva_integration.js
 *
 * Phase 5 — Atharva Integration Proof
 *
 * Runs mock_atharva_renderer.js as a subprocess, captures its full output,
 * validates the convergence proof, and writes the evidence log.
 *
 * Validates:
 *   1. Renderer connected to /simulate/stream
 *   2. stream:start sent with upstream trace_id
 *   3. All ticks consumed (stream:tick events)
 *   4. render:entity_update emitted per changed entity
 *   5. render:tick_complete emitted per tick
 *   6. execution:complete emitted on stream:done
 *   7. trace_id intact across all events
 *   8. No stream:error received
 *
 * Run:
 *   cd backend
 *   node test_phase5_atharva_integration.js
 */

const { spawn }  = require('child_process');
const fs         = require('fs');
const path       = require('path');

const LOG_PATH   = path.join(__dirname, 'phase5_integration_proof.log');

let passed = 0;
let failed = 0;
function pass(msg) { console.log(`  ✓ ${msg}`); passed++; }
function fail(msg) { console.error(`  ✗ ${msg}`); failed++; }

// ─── Run renderer subprocess ──────────────────────────────────────────────────

function runRenderer() {
  return new Promise((resolve, reject) => {
    const chunks = [];

    const proc = spawn('node', ['mock_atharva_renderer.js'], {
      cwd:   __dirname,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    proc.stdout.on('data', (d) => {
      process.stdout.write(d);   // live output
      chunks.push(d.toString());
    });

    proc.stderr.on('data', (d) => {
      process.stderr.write(d);
      chunks.push(d.toString());
    });

    proc.on('close', (code) => {
      const output = chunks.join('');
      resolve({ code, output });
    });

    proc.on('error', reject);

    // 15s timeout guard
    setTimeout(() => {
      proc.kill();
      reject(new Error('Renderer timed out after 15s'));
    }, 15000);
  });
}

// ─── Validate output ──────────────────────────────────────────────────────────

function validate(output) {
  console.log('\n── Validating convergence proof ─────────────────────');

  // 1. Connected
  if (output.includes('✓ Connected')) pass('Renderer connected to /simulate/stream');
  else                                 fail('Renderer did not connect');

  // 2. stream:start sent with trace_id
  if (output.includes('Sending stream:start with trace_id=')) pass('stream:start sent with upstream trace_id');
  else                                                          fail('stream:start not sent');

  // 3. stream:tick received
  const tick_matches = output.match(/← stream:tick received/g) || [];
  if (tick_matches.length === 8) pass(`All 8 stream:tick payloads consumed by renderer`);
  else                            fail(`Expected 8 stream:tick, got ${tick_matches.length}`);

  // 5. render:tick_complete emitted — count only the console summary lines
  const tick_completes = output.match(/→ render:tick_complete \|/g) || [];
  if (tick_completes.length === 8) pass(`render:tick_complete emitted for all 8 ticks`);
  else                              fail(`Expected 8 render:tick_complete, got ${tick_completes.length}`);

  // 4. render:entity_update emitted — count only the console summary lines
  const entity_updates = output.match(/→ render:entity_update \|/g) || [];
  if (entity_updates.length > 0) pass(`render:entity_update emitted (${entity_updates.length} total)`);
  else                            fail('No render:entity_update events emitted');

  // 6. execution:complete emitted
  if (output.includes('execution:complete')) pass('execution:complete emitted on stream:done');
  else                                        fail('execution:complete not emitted');

  // 7. trace_id intact
  if (output.includes('trace continuity: ✓ INTACT')) pass('trace_id intact across all events');
  else                                                  fail('trace_id continuity broken');

  // 8. No stream:error
  if (!output.includes('stream:error')) pass('No stream:error received');
  else                                   fail('stream:error was received');

  // 9. Convergence proof confirmed
  if (output.includes('PHASE 5 CONVERGENCE PROOF: LIVE INTEGRATION CONFIRMED')) {
    pass('CONVERGENCE PROOF: LIVE INTEGRATION CONFIRMED');
  } else {
    fail('Convergence proof not confirmed');
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n[PHASE 5 ATHARVA INTEGRATION TEST]');
  console.log('Running mock_atharva_renderer.js...\n');
  console.log('─'.repeat(54));

  let output;
  try {
    const result = await runRenderer();
    output = result.output;

    // Write evidence log
    fs.writeFileSync(LOG_PATH, output);
    console.log(`\n[PROOF LOG] Written to: ${LOG_PATH}`);
  } catch (err) {
    console.error(`\n[FATAL] Renderer failed: ${err.message}`);
    console.error('Make sure the server is running: node index.js\n');
    process.exit(1);
  }

  validate(output);

  console.log('\n' + '─'.repeat(54));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  if (failed === 0) {
    console.log('✓ Phase 5 Atharva integration test PASSED\n');
    console.log(`Evidence log: ${LOG_PATH}\n`);
  } else {
    console.log('✗ Phase 5 Atharva integration test FAILED\n');
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});

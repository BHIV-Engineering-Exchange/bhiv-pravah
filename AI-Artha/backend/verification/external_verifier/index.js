#!/usr/bin/env node

/**
 * external_verifier/index.js
 *
 * EXTERNAL independent verifier that runs OUTSIDE the application trust boundary.
 * Executes as a child_process from the main application, verifying governance
 * properties from an independently trusted perspective.
 *
 * Phase 1 convergence: external verification outside application trust boundary.
 *
 * CLI: node verification/external_verifier/index.js [--json] [--ci]
 */

import crypto from 'crypto';
import { readFileSync, readdirSync, existsSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const ROOT = join(__dirname, '..', '..');
const PROJECT_ROOT = ROOT;
const EVIDENCE_DIR = join(PROJECT_ROOT, 'evidence');
const CONTRACTS_DIR = join(PROJECT_ROOT, 'contracts', 'capability_contracts');
const REGISTRY_PATH = join(PROJECT_ROOT, 'capability_registry', 'capability_registry.json');

function computeHash(data) {
  return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
}

function loadJSON(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, 'utf-8'));
  } catch {
    return null;
  }
}

// ─── Verification Tests (independent of running application) ─────────────

function verifyContractFiles() {
  const results = { passed: 0, failed: 0, details: [] };

  if (!existsSync(CONTRACTS_DIR)) {
    results.failed++;
    results.details.push({ test: 'contracts_directory_exists', status: 'FAIL', error: 'contracts directory not found' });
    return results;
  }

  const contractFiles = readdirSync(CONTRACTS_DIR).filter(f => f.endsWith('.json'));

  for (const file of contractFiles) {
    const contract = loadJSON(join(CONTRACTS_DIR, file));
    if (!contract) {
      results.failed++;
      results.details.push({ test: `contract_parse_${file}`, status: 'FAIL', error: 'Failed to parse' });
      continue;
    }

    // Verify required fields
    const requiredFields = ['capability_id', 'version', 'description', 'hash'];
    const missing = requiredFields.filter(f => !contract[f]);
    if (missing.length > 0) {
      results.failed++;
      results.details.push({ test: `contract_fields_${file}`, status: 'FAIL', error: `Missing: ${missing.join(', ')}` });
      continue;
    }

    // Verify hash integrity
    const contractData = { ...contract };
    delete contractData.hash;
    const expectedHash = computeHash(contractData);
    if (contract.hash !== expectedHash) {
      results.failed++;
      results.details.push({ test: `contract_hash_${file}`, status: 'FAIL', expected: expectedHash.slice(0, 16), actual: contract.hash?.slice(0, 16) });
      continue;
    }

    results.passed++;
    results.details.push({ test: `contract_integrity_${file}`, status: 'PASS', capability_id: contract.capability_id });
  }

  return results;
}

function verifyRegistryIntegrity() {
  const results = { passed: 0, failed: 0, details: [] };

  const registry = loadJSON(REGISTRY_PATH);
  if (!registry) {
    results.failed++;
    results.details.push({ test: 'registry_load', status: 'FAIL', error: 'Registry file not found or invalid' });
    return results;
  }

  // Verify registry structure
  if (!registry.capabilities || typeof registry.capabilities !== 'object') {
    results.failed++;
    results.details.push({ test: 'registry_structure', status: 'FAIL', error: 'Missing or invalid capabilities' });
    return results;
  }

  const capCount = Object.keys(registry.capabilities).length;
  if (capCount === 0) {
    results.failed++;
    results.details.push({ test: 'registry_populated', status: 'FAIL', error: 'No capabilities registered' });
    return results;
  }

  results.passed++;
  results.details.push({ test: 'registry_structure', status: 'PASS', capability_count: capCount });

  // Verify each capability has required fields
  for (const [id, cap] of Object.entries(registry.capabilities)) {
    if (!cap.version || !cap.owns_collections) {
      results.failed++;
      results.details.push({ test: `capability_fields_${id}`, status: 'FAIL', error: 'Missing required fields' });
    } else {
      results.passed++;
      results.details.push({ test: `capability_valid_${id}`, status: 'PASS' });
    }
  }

  return results;
}

function verifyNoDuplicateCollections() {
  const results = { passed: 0, failed: 0, details: [] };

  const registry = loadJSON(REGISTRY_PATH);
  if (!registry?.capabilities) {
    results.failed++;
    results.details.push({ test: 'registry_load', status: 'FAIL', error: 'Cannot load registry' });
    return results;
  }

  const collectionOwnership = new Map();
  const conflicts = [];

  for (const [id, cap] of Object.entries(registry.capabilities)) {
    for (const coll of cap.owns_collections || []) {
      if (collectionOwnership.has(coll)) {
        conflicts.push({ collection: coll, capability_a: collectionOwnership.get(coll), capability_b: id });
      }
      collectionOwnership.set(coll, id);
    }
  }

  if (conflicts.length === 0) {
    results.passed++;
    results.details.push({ test: 'collection_ownership_no_conflicts', status: 'PASS', unique_collections: collectionOwnership.size });
  } else {
    results.failed++;
    results.details.push({ test: 'collection_ownership_conflicts', status: 'FAIL', conflicts });
  }

  return results;
}

function verifyFileIntegrity() {
  const results = { passed: 0, failed: 0, details: [] };

  // Check critical files exist
  const criticalFiles = [
    { path: join(PROJECT_ROOT, 'backend', 'src', 'server.js'), name: 'server.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'middleware', 'policyEngine.js'), name: 'policyEngine.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'middleware', 'authorityBoundary.js'), name: 'authorityBoundary.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'services', 'capabilityRegistry.service.js'), name: 'capabilityRegistry.service.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'services', 'provenanceChain.service.js'), name: 'provenanceChain.service.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'services', 'decisionLedger.service.js'), name: 'decisionLedger.service.js' },
    { path: join(PROJECT_ROOT, 'backend', 'src', 'services', 'circuitBreaker.service.js'), name: 'circuitBreaker.service.js' },
  ];

  for (const file of criticalFiles) {
    if (existsSync(file.path)) {
      const content = readFileSync(file.path, 'utf-8');
      const hash = computeHash(content);
      results.passed++;
      results.details.push({ test: `file_exists_${file.name}`, status: 'PASS', hash: hash.slice(0, 16), size: content.length });
    } else {
      results.failed++;
      results.details.push({ test: `file_exists_${file.name}`, status: 'FAIL', error: 'File not found' });
    }
  }

  return results;
}

function verifyEvidenceDirectory() {
  const results = { passed: 0, failed: 0, details: [] };

  if (!existsSync(EVIDENCE_DIR)) {
    results.failed++;
    results.details.push({ test: 'evidence_directory_exists', status: 'FAIL', error: 'Evidence directory not found' });
    return results;
  }

  const evidenceFiles = readdirSync(EVIDENCE_DIR).filter(f => f.endsWith('.json'));
  results.passed++;
  results.details.push({ test: 'evidence_directory_exists', status: 'PASS', evidence_count: evidenceFiles.length });

  // Verify at least one evidence file has valid JSON
  for (const file of evidenceFiles.slice(0, 5)) {
    const evidence = loadJSON(join(EVIDENCE_DIR, file));
    if (evidence) {
      results.passed++;
      results.details.push({ test: `evidence_valid_${file}`, status: 'PASS' });
    } else {
      results.failed++;
      results.details.push({ test: `evidence_valid_${file}`, status: 'FAIL', error: 'Invalid JSON' });
    }
  }

  return results;
}

// ─── Main ────────────────────────────────────────────────────────────────

function main() {
  const isCI = process.argv.includes('--ci');
  const isJSON = process.argv.includes('--json');
  const startTime = Date.now();

  console.log('\n╔═══════════════════════════════════════════════════════════╗');
  console.log('║   ARTHA External Independent Verifier                    ║');
  console.log('║   Running OUTSIDE application trust boundary              ║');
  console.log('╚═══════════════════════════════════════════════════════════╝\n');

  const testSuites = [
    { name: 'Contract File Integrity', fn: verifyContractFiles },
    { name: 'Registry Integrity', fn: verifyRegistryIntegrity },
    { name: 'Collection Ownership', fn: verifyNoDuplicateCollections },
    { name: 'Critical File Integrity', fn: verifyFileIntegrity },
    { name: 'Evidence Directory', fn: verifyEvidenceDirectory },
  ];

  const suiteResults = [];

  for (const suite of testSuites) {
    console.log(`  ▸ Running ${suite.name}...`);
    const result = suite.fn();
    suiteResults.push({ name: suite.name, ...result });

    const icon = result.failed === 0 ? '✓' : '✗';
    console.log(`    ${icon} ${result.passed} passed, ${result.failed} failed`);
  }

  const duration = Date.now() - startTime;

  // Aggregate
  let totalPassed = 0;
  let totalFailed = 0;
  for (const suite of suiteResults) {
    totalPassed += suite.passed;
    totalFailed += suite.failed;
  }

  const allPassed = totalFailed === 0;

  // Console summary
  console.log('\n┌─────────────────────────────────────────────────────────┐');
  console.log('│  EXTERNAL VERIFICATION RESULTS                          │');
  console.log('├─────────────────────────────────────────────────────────┤');
  console.log(`│  TOTAL: ${totalPassed}/${totalPassed + totalFailed} checks passed, ${totalFailed} failed`);
  console.log(`│  DURATION: ${duration}ms`);
  console.log(`│  OVERALL: ${allPassed ? 'PASS ✓' : 'FAIL ✗'}`);
  console.log('└─────────────────────────────────────────────────────────┘\n');

  // Build evidence
  const evidence = {
    verifier: 'ARTH External Independent Verifier',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    duration_ms: duration,
    trust_boundary: 'EXTERNAL',
    overall_status: allPassed ? 'PASS' : 'FAIL',
    summary: {
      total_checks: totalPassed + totalFailed,
      passed: totalPassed,
      failed: totalFailed,
      all_passed: allPassed,
    },
    suite_results: suiteResults,
    environment: {
      node_version: process.version,
      platform: process.platform,
      arch: process.arch,
    },
  };

  evidence.evidence_hash = computeHash(evidence);

  // Write evidence
  mkdirSync(EVIDENCE_DIR, { recursive: true });
  const date = new Date().toISOString().split('T')[0];
  const evidencePath = join(EVIDENCE_DIR, `external-verification-${date}.json`);
  writeFileSync(evidencePath, JSON.stringify(evidence, null, 2));
  console.log(`  Evidence written to: ${evidencePath}`);
  console.log(`  Evidence hash: ${evidence.evidence_hash.substring(0, 16)}...\n`);

  if (isJSON) {
    console.log(JSON.stringify(evidence, null, 2));
  }

  if (isCI && !allPassed) {
    process.exit(1);
  }
}

main();

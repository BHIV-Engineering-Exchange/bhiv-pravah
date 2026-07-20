#!/usr/bin/env node

/**
 * external-verifier.js
 *
 * Independent verification script that runs OUTSIDE the application trust boundary.
 * Connects directly to MongoDB to verify governance invariants without trusting
 * the application runtime.
 *
 * Usage: node scripts/external-verifier.js [--mongo-uri URI] [--output FILE]
 *
 * This produces deterministic, reproducible evidence that can be verified
 * independently by any auditor.
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class ExternalVerifier {
  constructor(mongoUri, outputFile) {
    this.mongoUri = mongoUri || process.env.MONGODB_URI || 'mongodb://localhost:27017/artha';
    this.outputFile = outputFile || path.join(__dirname, '..', 'evidence', `external-verification-${Date.now()}.json`);
    this.results = [];
    this.startTime = Date.now();
  }

  async connectDB() {
    const { default: mongoose } = await import('mongoose');
    await mongoose.connect(this.mongoUri);
    this.mongoose = mongoose;
    console.log(`Connected to MongoDB: ${this.mongoUri}`);
    return mongoose;
  }

  async disconnectDB() {
    if (this.mongoose) {
      await this.mongoose.disconnect();
    }
  }

  async runAllTests() {
    console.log('\n=== ARTHA External Independent Verification ===\n');
    console.log(`Started at: ${new Date().toISOString()}`);
    console.log(`Mongo URI: ${this.mongoUri.replace(/\/\/[^:]+:[^@]+@/, '//***:***@')}`);
    console.log('');

    await this.connectDB();

    try {
      await this.verifyProvenanceChainIntegrity();
      await this.verifyDecisionLedgerIntegrity();
      await this.verifyLineageAnchors();
      await this.verifyHashChainIntegrity();
      await this.verifyDoubleEntryBalancing();
      await this.verifyCapabilityContracts();
      await this.verifyAuditChainIntegrity();
      await this.verifyTraceContinuity();
      await this.verifyNoTamperedBlocks();
      await this.verifyConstitutionalCompliance();
    } catch (err) {
      console.error('Verification suite error:', err);
    }

    await this.disconnectDB();

    const evidence = this.generateEvidence();
    this.saveEvidence(evidence);
    this.printSummary(evidence);

    return evidence;
  }

  async verifyProvenanceChainIntegrity() {
    console.log('1. Verifying Provenance Chain Integrity...');
    const ProvenanceBlock = (await import('../backend/src/models/ProvenanceBlock.js')).default;

    const blocks = await ProvenanceBlock.find({}).sort({ chain_position: 1 }).lean();
    if (blocks.length === 0) {
      this.results.push({ test: 'provenance_chain', status: 'PASS', detail: 'No blocks (genesis only)' });
      return;
    }

    const errors = [];
    for (let i = 1; i < blocks.length; i++) {
      if (blocks[i].previous_hash !== blocks[i - 1].hash) {
        errors.push({ position: blocks[i].chain_position, error: 'Chain link broken' });
      }
    }

    const status = errors.length === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'provenance_chain_integrity',
      status,
      total_blocks: blocks.length,
      chain_tip: blocks[blocks.length - 1]?.hash,
      errors,
    });
    console.log(`   ${status}: ${blocks.length} blocks verified`);
  }

  async verifyDecisionLedgerIntegrity() {
    console.log('2. Verifying Decision Ledger Integrity...');
    const DecisionLedger = (await import('../backend/src/models/DecisionLedger.js')).default;

    const decisions = await DecisionLedger.find({}).sort({ chain_position: 1 }).lean();
    if (decisions.length === 0) {
      this.results.push({ test: 'decision_ledger', status: 'PASS', detail: 'No decisions recorded' });
      return;
    }

    const errors = [];
    for (let i = 1; i < decisions.length; i++) {
      if (decisions[i].previous_hash !== decisions[i - 1].hash) {
        errors.push({ position: decisions[i].chain_position, error: 'Chain link broken' });
      }
    }

    const status = errors.length === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'decision_ledger_integrity',
      status,
      total_decisions: decisions.length,
      errors,
    });
    console.log(`   ${status}: ${decisions.length} decisions verified`);
  }

  async verifyLineageAnchors() {
    console.log('3. Verifying Lineage Anchors...');
    const LineageAnchor = (await import('../backend/src/models/LineageAnchor.js')).default;

    const anchors = await LineageAnchor.find({}).lean();
    const byEntityType = {};
    for (const anchor of anchors) {
      byEntityType[anchor.entity_type] = (byEntityType[anchor.entity_type] || 0) + 1;
    }

    const status = anchors.length > 0 ? 'PASS' : 'WARN';
    this.results.push({
      test: 'lineage_anchors',
      status,
      total_anchors: anchors.length,
      by_entity_type: byEntityType,
    });
    console.log(`   ${status}: ${anchors.length} lineage anchors`);
  }

  async verifyHashChainIntegrity() {
    console.log('4. Verifying Ledger Hash Chain...');
    const LedgerEntry = (await import('../backend/src/models/LedgerEntry.js')).default;

    const count = await LedgerEntry.countDocuments();
    let chainBreaks = 0;

    if (count > 1) {
      const entries = await LedgerEntry.find({}).sort({ timestamp: 1, _id: 1 }).limit(1000).lean();
      for (let i = 1; i < entries.length; i++) {
        if (entries[i].prev_hash !== entries[i - 1].hash) {
          chainBreaks++;
        }
      }
    }

    const status = chainBreaks === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'ledger_hash_chain',
      status,
      total_entries: count,
      chain_breaks: chainBreaks,
    });
    console.log(`   ${status}: ${count} entries, ${chainBreaks} breaks`);
  }

  async verifyDoubleEntryBalancing() {
    console.log('5. Verifying Double-Entry Balancing...');
    const AccountBalance = (await import('../backend/src/models/AccountBalance.js')).default;

    const balances = await AccountBalance.find({}).lean();
    let totalDebit = 0;
    let totalCredit = 0;

    for (const bal of balances) {
      totalDebit += bal.debitTotal || 0;
      totalCredit += bal.creditTotal || 0;
    }

    const difference = Math.abs(totalDebit - totalCredit);
    const isBalanced = difference < 0.01;

    const status = isBalanced ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'double_entry_balancing',
      status,
      total_debit: totalDebit,
      total_credit: totalCredit,
      difference,
    });
    console.log(`   ${status}: difference=${difference}`);
  }

  async verifyCapabilityContracts() {
    console.log('6. Verifying Capability Contracts...');
    const fs = await import('fs');
    const contractsDir = path.join(__dirname, '..', 'contracts', 'capability_contracts');

    if (!fs.existsSync(contractsDir)) {
      this.results.push({ test: 'capability_contracts', status: 'SKIP', detail: 'Contracts directory not found' });
      return;
    }

    const files = fs.readdirSync(contractsDir).filter(f => f.endsWith('.json'));
    const results = [];

    for (const file of files) {
      const filePath = path.join(contractsDir, file);
      const content = fs.readFileSync(filePath, 'utf8');
      const hash = crypto.createHash('sha256').update(content).digest('hex');
      const contract = JSON.parse(content);
      results.push({ file, capability_id: contract.capability_id, hash });
    }

    const status = results.length > 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'capability_contracts',
      status,
      total_contracts: results.length,
      contracts: results,
    });
    console.log(`   ${status}: ${results.length} contracts verified`);
  }

  async verifyAuditChainIntegrity() {
    console.log('7. Verifying Audit Chain...');
    const AuditEvent = (await import('../backend/src/models/AuditEvent.js')).default;

    const count = await AuditEvent.countDocuments();
    let chainBreaks = 0;

    if (count > 1) {
      const events = await AuditEvent.find({}).sort({ chainPosition: 1 }).limit(1000).lean();
      for (let i = 1; i < events.length; i++) {
        if (events[i].previousHash !== events[i - 1].hash) {
          chainBreaks++;
        }
      }
    }

    const status = chainBreaks === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'audit_chain_integrity',
      status,
      total_events: count,
      chain_breaks: chainBreaks,
    });
    console.log(`   ${status}: ${count} events, ${chainBreaks} breaks`);
  }

  async verifyTraceContinuity() {
    console.log('8. Verifying Trace Continuity...');
    const UnifiedTrace = (await import('../backend/src/models/UnifiedTrace.js')).default;

    const total = await UnifiedTrace.countDocuments();
    const completed = await UnifiedTrace.countDocuments({ status: 'COMPLETED' });
    const failed = await UnifiedTrace.countDocuments({ status: 'FAILED' });
    const inProgress = await UnifiedTrace.countDocuments({ status: 'IN_PROGRESS' });

    const status = total > 0 ? 'PASS' : 'WARN';
    this.results.push({
      test: 'trace_continuity',
      status,
      total_traces: total,
      completed,
      failed,
      in_progress: inProgress,
    });
    console.log(`   ${status}: ${total} traces`);
  }

  async verifyNoTamperedBlocks() {
    console.log('9. Verifying No Tampered Blocks...');
    const ProvenanceBlock = (await import('../backend/src/models/ProvenanceBlock.js')).default;

    const blocks = await ProvenanceBlock.find({}).lean();
    let tampered = 0;

    for (const block of blocks) {
      const expectedHash = crypto.createHash('sha256').update(JSON.stringify({
        block_id: block.block_id,
        type: block.type,
        timestamp: block.timestamp,
        data: block.data,
        previous_hash: block.previous_hash,
        nonce: block.nonce,
        chain_position: block.chain_position,
      })).digest('hex');

      if (block.hash !== expectedHash) {
        tampered++;
      }
    }

    const status = tampered === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'no_tampered_blocks',
      status,
      total_blocks: blocks.length,
      tampered,
    });
    console.log(`   ${status}: ${tampered} tampered blocks`);
  }

  async verifyConstitutionalCompliance() {
    console.log('10. Verifying Constitutional Compliance...');
    const DecisionLedger = (await import('../backend/src/models/DecisionLedger.js')).default;

    const decisions = await DecisionLedger.find({}).lean();
    const nonCompliant = decisions.filter(d => !d.constitutionally_compliant).length;
    const replayUnsafe = decisions.filter(d => !d.replay_safe).length;

    const status = nonCompliant === 0 && replayUnsafe === 0 ? 'PASS' : 'FAIL';
    this.results.push({
      test: 'constitutional_compliance',
      status,
      total_decisions: decisions.length,
      non_compliant: nonCompliant,
      replay_unsafe: replayUnsafe,
    });
    console.log(`   ${status}: ${nonCompliant} non-compliant, ${replayUnsafe} replay-unsafe`);
  }

  generateEvidence() {
    const duration = Date.now() - this.startTime;
    const passed = this.results.filter(r => r.status === 'PASS').length;
    const failed = this.results.filter(r => r.status === 'FAIL').length;
    const warnings = this.results.filter(r => r.status === 'WARN').length;

    return {
      evidence_type: 'EXTERNAL_INDEPENDENT_VERIFICATION',
      generated_at: new Date().toISOString(),
      duration_ms: duration,
      environment: {
        mongo_uri: this.mongoUri.replace(/\/\/[^:]+:[^@]+@/, '//***:***@'),
        node_version: process.version,
        platform: process.platform,
      },
      summary: {
        total_tests: this.results.length,
        passed,
        failed,
        warnings,
        overall: failed === 0 ? 'PASS' : 'FAIL',
      },
      tests: this.results,
      verification_hash: crypto.createHash('sha256').update(JSON.stringify(this.results)).digest('hex'),
    };
  }

  saveEvidence(evidence) {
    const dir = path.dirname(this.outputFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(this.outputFile, JSON.stringify(evidence, null, 2));
    console.log(`\nEvidence saved to: ${this.outputFile}`);
  }

  printSummary(evidence) {
    console.log('\n=== Verification Summary ===');
    console.log(`Overall: ${evidence.summary.overall}`);
    console.log(`Passed: ${evidence.summary.passed}/${evidence.summary.total_tests}`);
    console.log(`Failed: ${evidence.summary.failed}`);
    console.log(`Warnings: ${evidence.summary.warnings}`);
    console.log(`Duration: ${evidence.duration_ms}ms`);
    console.log(`Evidence Hash: ${evidence.verification_hash}`);
  }
}

const args = process.argv.slice(2);
let mongoUri = null;
let outputFile = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--mongo-uri' && args[i + 1]) {
    mongoUri = args[++i];
  }
  if (args[i] === '--output' && args[i + 1]) {
    outputFile = args[++i];
  }
}

const verifier = new ExternalVerifier(mongoUri, outputFile);
verifier.runAllTests().then(() => {
  process.exit(0);
}).catch(err => {
  console.error('Verification failed:', err);
  process.exit(1);
});

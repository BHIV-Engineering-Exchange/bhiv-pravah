import crypto from 'crypto';
import { randomUUID } from 'crypto';
import logger from '../config/logger.js';
import provenanceChain from './provenanceChain.service.js';
import decisionLedger from './decisionLedger.service.js';
import lineage from './lineage.service.js';

class IndependentVerifierService {
  constructor() {
    this.verificationResults = [];
    this.initialized = false;
  }

  initialize() {
    this.initialized = true;
    logger.info('[INDEPENDENT_VERIFIER] Verification engine initialized');
  }

  async runVerificationSuite(context = {}) {
    const suiteId = `VSUITE-${Date.now()}-${randomUUID().slice(0, 8)}`;
    const startTime = Date.now();

    logger.info(`[INDEPENDENT_VERIFIER] Starting verification suite: ${suiteId}`);

    const results = {
      suite_id: suiteId,
      started_at: new Date().toISOString(),
      environment: {
        node_version: process.version,
        platform: process.platform,
        arch: process.arch,
        memory_mb: Math.round(process.memoryUsage().rss / 1024 / 1024),
        pid: process.pid,
      },
      tests: [],
    };

    const tests = [
      () => this.verifyCapabilityContracts(context),
      () => this.verifyAuthorityBoundaries(context),
      () => this.verifyHashChainIntegrity(context),
      () => this.verifyDoubleEntryBalancing(context),
      () => this.verifyTraceContinuity(context),
      () => this.verifyCircuitBreakers(context),
      () => this.verifyContractIntegrity(context),
      () => this.verifyRouteMapping(context),
      () => this.verifyPolicyEnforcement(context),
      () => this.verifyProvenanceChain(context),
      () => this.verifyDecisionLedger(context),
      () => this.verifyLineageIntegrity(context),
    ];

    for (const testFn of tests) {
      try {
        const testResult = await testFn();
        results.tests.push(testResult);
      } catch (err) {
        results.tests.push({
          test: testFn.name,
          status: 'ERROR',
          error: err.message,
          timestamp: new Date().toISOString(),
        });
      }
    }

    results.completed_at = new Date().toISOString();
    results.duration_ms = Date.now() - startTime;
    results.total_tests = results.tests.length;
    results.passed = results.tests.filter(t => t.status === 'PASS').length;
    results.failed = results.tests.filter(t => t.status === 'FAIL').length;
    results.errors = results.tests.filter(t => t.status === 'ERROR').length;
    results.overall = results.failed === 0 && results.errors === 0 ? 'PASS' : 'FAIL';

    results.suite_hash = crypto
      .createHash('sha256')
      .update(JSON.stringify(results.tests))
      .digest('hex');

    await provenanceChain.recordReplayVerification({
      trace_id: suiteId,
      deterministic: results.overall === 'PASS',
      input_hash: results.suite_hash,
      output_hash: crypto.createHash('sha256').update(JSON.stringify(results)).digest('hex'),
      match: results.overall === 'PASS',
    });

    this.verificationResults.push(results);

    logger.info(
      `[INDEPENDENT_VERIFIER] Suite ${suiteId} complete: ${results.overall} ` +
      `(${results.passed}/${results.total_tests} passed, ${results.duration_ms}ms)`
    );

    return results;
  }

  async verifyCapabilityContracts(context) {
    const capabilityRegistry = (await import('./capabilityRegistry.service.js')).default;
    const allCaps = capabilityRegistry.getAllCapabilities();
    const contractHashes = capabilityRegistry.verifyAllContracts();

    const failures = Object.entries(contractHashes)
      .filter(([, r]) => !r.valid)
      .map(([id, r]) => ({ capability_id: id, error: r.error }));

    return {
      test: 'verifyCapabilityContracts',
      status: failures.length === 0 ? 'PASS' : 'FAIL',
      details: {
        total_capabilities: Object.keys(allCaps).length,
        contracts_verified: Object.keys(contractHashes).length,
        failures,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyAuthorityBoundaries(context) {
    const capabilityRegistry = (await import('./capabilityRegistry.service.js')).default;
    const caps = capabilityRegistry.getAllCapabilities();
    const conflicts = [];

    const allCollections = new Map();
    for (const [id, cap] of Object.entries(caps)) {
      for (const coll of cap.owns_collections || []) {
        if (allCollections.has(coll)) {
          conflicts.push({
            collection: coll,
            capability_a: allCollections.get(coll),
            capability_b: id,
          });
        }
        allCollections.set(coll, id);
      }
    }

    return {
      test: 'verifyAuthorityBoundaries',
      status: conflicts.length === 0 ? 'PASS' : 'FAIL',
      details: {
        total_capabilities: Object.keys(caps).length,
        unique_collections: allCollections.size,
        conflicts,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyHashChainIntegrity(context) {
    let totalEntries = 0;
    let chainBreaks = 0;

    try {
      const LedgerEntry = (await import('../models/LedgerEntry.js')).default;
      totalEntries = await LedgerEntry.countDocuments();

      if (totalEntries > 1) {
        const entries = await LedgerEntry.find({})
          .sort({ timestamp: 1, _id: 1 })
          .limit(1000)
          .lean();

        for (let i = 1; i < entries.length; i++) {
          if (entries[i].prev_hash !== entries[i - 1].hash) {
            chainBreaks++;
          }
        }
      }
    } catch (err) {
      return {
        test: 'verifyHashChainIntegrity',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }

    return {
      test: 'verifyHashChainIntegrity',
      status: chainBreaks === 0 ? 'PASS' : 'FAIL',
      details: {
        total_entries: totalEntries,
        chain_breaks: chainBreaks,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyDoubleEntryBalancing(context) {
    let isBalanced = false;
    let balanceDifference = '0';

    try {
      const ledgerService = (await import('./ledger.service.js')).default;
      const summary = await ledgerService.getLedgerSummary();
      isBalanced = summary.isBalanced;
      balanceDifference = summary.balanceDifference;
    } catch (err) {
      return {
        test: 'verifyDoubleEntryBalancing',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }

    return {
      test: 'verifyDoubleEntryBalancing',
      status: isBalanced ? 'PASS' : 'FAIL',
      details: { is_balanced: isBalanced, balance_difference: balanceDifference },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyTraceContinuity(context) {
    let totalTraces = 0;
    let brokenTraces = 0;

    try {
      const UnifiedTrace = (await import('../models/UnifiedTrace.js')).default;
      totalTraces = await UnifiedTrace.countDocuments();

      const traces = await UnifiedTrace.find({}).limit(100).lean();
      for (const trace of traces) {
        if (!trace.stages || trace.stages.length === 0) {
          brokenTraces++;
        }
      }
    } catch (err) {
      return {
        test: 'verifyTraceContinuity',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }

    return {
      test: 'verifyTraceContinuity',
      status: brokenTraces === 0 ? 'PASS' : 'FAIL',
      details: { total_traces: totalTraces, broken_traces: brokenTraces },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyCircuitBreakers(context) {
    const circuitBreaker = (await import('./circuitBreaker.service.js')).default;
    const status = circuitBreaker.getStatus();
    const openCircuits = circuitBreaker.getOpenCircuits();

    return {
      test: 'verifyCircuitBreakers',
      status: openCircuits.length === 0 ? 'PASS' : 'WARN',
      details: {
        total_breakers: Object.keys(status).length,
        open_circuits: openCircuits,
        all_status: status,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyContractIntegrity(context) {
    const capabilityRegistry = (await import('./capabilityRegistry.service.js')).default;
    const results = capabilityRegistry.verifyAllContracts();
    const allValid = Object.values(results).every(r => r.valid);

    return {
      test: 'verifyContractIntegrity',
      status: allValid ? 'PASS' : 'FAIL',
      details: {
        contracts_checked: Object.keys(results).length,
        all_valid: allValid,
        results,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyRouteMapping(context) {
    const capabilityRegistry = (await import('./capabilityRegistry.service.js')).default;
    const metadata = capabilityRegistry.getRegistryMetadata();

    return {
      test: 'verifyRouteMapping',
      status: metadata.route_count > 0 ? 'PASS' : 'FAIL',
      details: {
        route_count: metadata.route_count,
        capability_count: metadata.capability_count,
        registration_id: metadata.registration_id,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyPolicyEnforcement(context) {
    const capabilityRegistry = (await import('./capabilityRegistry.service.js')).default;
    const caps = capabilityRegistry.getAllCapabilities();
    let enforcedCount = 0;

    for (const [, cap] of Object.entries(caps)) {
      if (cap.owns_collections.length > 0 || cap.read_only) {
        enforcedCount++;
      }
    }

    return {
      test: 'verifyPolicyEnforcement',
      status: enforcedCount > 0 ? 'PASS' : 'FAIL',
      details: {
        total_capabilities: Object.keys(caps).length,
        enforced_capabilities: enforcedCount,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async verifyProvenanceChain(context) {
    try {
      const result = await provenanceChain.verifyIntegrity();
      return {
        test: 'verifyProvenanceChain',
        status: result.valid ? 'PASS' : 'FAIL',
        details: result,
        timestamp: new Date().toISOString(),
      };
    } catch (err) {
      return {
        test: 'verifyProvenanceChain',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }
  }

  async verifyDecisionLedger(context) {
    try {
      const result = await decisionLedger.verifyChainIntegrity();
      const stats = await decisionLedger.getDecisionStats();

      return {
        test: 'verifyDecisionLedger',
        status: result.valid ? 'PASS' : 'FAIL',
        details: {
          integrity: result,
          stats,
        },
        timestamp: new Date().toISOString(),
      };
    } catch (err) {
      return {
        test: 'verifyDecisionLedger',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }
  }

  async verifyLineageIntegrity(context) {
    try {
      const stats = await lineage.getLineageStats();
      return {
        test: 'verifyLineageIntegrity',
        status: stats.total > 0 ? 'PASS' : 'WARN',
        details: stats,
        timestamp: new Date().toISOString(),
      };
    } catch (err) {
      return {
        test: 'verifyLineageIntegrity',
        status: 'ERROR',
        details: { error: err.message },
        timestamp: new Date().toISOString(),
      };
    }
  }

  getVerificationHistory() {
    return this.verificationResults;
  }
}

const independentVerifier = new IndependentVerifierService();
export default independentVerifier;

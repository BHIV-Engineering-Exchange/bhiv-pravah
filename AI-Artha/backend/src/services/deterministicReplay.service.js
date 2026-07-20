/**
 * deterministicReplay.service.js
 *
 * Extended deterministic replay system for governance verification.
 * Records execution inputs, computes deterministic output hashes,
 * captures full execution state for distributed dependency replay,
 * and enables independent verification of execution outcomes.
 *
 * Phase 1 convergence: extended for distributed dependency replay.
 */

import crypto from 'crypto';
import { randomUUID } from 'crypto';
import logger from '../config/logger.js';
import provenanceChain from './provenanceChain.service.js';
import decisionLedger from './decisionLedger.service.js';
import lineage from './lineage.service.js';

class DeterministicReplayService {
  constructor() {
    this.replayRecords = new Map();
    this.executionStates = new Map();
    this.initialized = false;
  }

  initialize() {
    this.initialized = true;
    logger.info('[REPLAY] Deterministic replay system initialized');
  }

  /**
   * Record an execution with full state capture for distributed dependency replay.
   */
  recordExecution(execution) {
    if (!this.initialized) this.initialize();

    const record = {
      replay_id: `RPL-${Date.now()}-${randomUUID().slice(0, 8)}`,
      trace_id: execution.trace_id,
      operation: execution.operation,
      timestamp: new Date().toISOString(),
      input: {
        method: execution.method,
        path: execution.path,
        body_hash: this._hashData(execution.body || {}),
        query_hash: this._hashData(execution.query || {}),
        params_hash: this._hashData(execution.params || {}),
        user_id: execution.user_id,
        capability: execution.capability,
      },
      output: {
        status_code: execution.status_code,
        response_hash: this._hashData(execution.response || {}),
        error: execution.error || null,
      },
      metadata: {
        environment_hash: this._hashEnvironment(),
        node_version: process.version,
      },
      verification: {
        input_fingerprint: null,
        output_fingerprint: null,
        deterministic: true,
      },
    };

    record.verification.input_fingerprint = this._computeFingerprint(record.input);
    record.verification.output_fingerprint = this._computeFingerprint(record.output);
    this.replayRecords.set(record.replay_id, record);

    logger.debug(`[REPLAY] Recorded: ${record.replay_id} op=${execution.operation}`);
    return record;
  }

  /**
   * Record execution with full distributed dependency state.
   * Captures: database state, external API responses, cache state,
   * circuit breaker states, and environment snapshot.
   */
  recordDistributedExecution(execution) {
    if (!this.initialized) this.initialize();

    const replayId = `RPL-${Date.now()}-${randomUUID().slice(0, 8)}`;

    const executionState = {
      replay_id: replayId,
      trace_id: execution.trace_id,
      operation: execution.operation,
      timestamp: new Date().toISOString(),

      // Input state
      input: {
        method: execution.method,
        path: execution.path,
        body: execution.body || {},
        query: execution.query || {},
        params: execution.params || {},
        headers: execution.headers || {},
        user_id: execution.user_id,
        capability: execution.capability,
      },

      // Database state snapshot
      database_state: {
        collections_read: execution.db_reads || [],
        collections_written: execution.db_writes || [],
        documents_affected: execution.db_documents || [],
        transaction_id: execution.transaction_id || null,
      },

      // External dependency state
      external_dependencies: {
        api_calls: execution.external_calls || [],
        cache_reads: execution.cache_reads || [],
        cache_writes: execution.cache_writes || [],
      },

      // Circuit breaker state at execution time
      circuit_breaker_state: execution.circuit_breaker_state || {},

      // Environment snapshot
      environment: {
        node_version: process.version,
        platform: process.platform,
        arch: process.arch,
        env: process.env.NODE_ENV,
        timestamp: new Date().toISOString(),
      },

      // Output state
      output: {
        status_code: execution.status_code,
        response: execution.response || {},
        error: execution.error || null,
      },

      // Deterministic verification
      verification: {
        input_hash: null,
        output_hash: null,
        state_hash: null,
        deterministic: true,
      },
    };

    // Compute hashes
    executionState.verification.input_hash = this._hashData(executionState.input);
    executionState.verification.output_hash = this._hashData(executionState.output);
    executionState.verification.state_hash = this._hashData({
      db: executionState.database_state,
      external: executionState.external_dependencies,
      circuit: executionState.circuit_breaker_state,
    });

    this.executionStates.set(replayId, executionState);

    // Also record in basic replay records
    const basicRecord = this.recordExecution(execution);

    logger.debug(`[REPLAY] Recorded distributed execution: ${replayId} op=${execution.operation}`);
    return {
      replay_id: replayId,
      basic_record: basicRecord,
      execution_state: executionState,
    };
  }

  getReplayData(replayId) {
    const record = this.replayRecords.get(replayId);
    const executionState = this.executionStates.get(replayId);

    if (!record && !executionState) {
      return { found: false, error: `Replay ${replayId} not found` };
    }

    return {
      found: true,
      record: record || null,
      execution_state: executionState || null,
      replay_instructions: record ? {
        method: record.input.method,
        path: record.input.path,
        body_hash: record.input.body_hash,
        expected_output_hash: record.output.response_hash,
        expected_status: record.output.status_code,
        capability: record.input.capability,
      } : null,
      distributed_replay_instructions: executionState ? {
        method: executionState.input.method,
        path: executionState.input.path,
        body: executionState.input.body,
        expected_status: executionState.output.status_code,
        expected_response: executionState.output.response,
        database_state: executionState.database_state,
        external_dependencies: executionState.external_dependencies,
        circuit_breaker_state: executionState.circuit_breaker_state,
      } : null,
    };
  }

  verifyReplay(replayId, actualOutput) {
    const record = this.replayRecords.get(replayId);
    if (!record) return { valid: false, error: `Replay ${replayId} not found` };

    const actualHash = this._hashData(actualOutput);
    const deterministic = actualHash === record.verification.output_fingerprint;

    return {
      replay_id: replayId,
      trace_id: record.trace_id,
      operation: record.operation,
      deterministic,
      expected_hash: record.verification.output_fingerprint,
      actual_hash: actualHash,
      match: deterministic,
      verified_at: new Date().toISOString(),
    };
  }

  /**
   * Verify distributed execution replay.
   * Compares full state: input, output, database, external deps.
   */
  verifyDistributedReplay(replayId, actualState) {
    const executionState = this.executionStates.get(replayId);
    if (!executionState) return { valid: false, error: `Replay ${replayId} not found` };

    const results = {
      replay_id: replayId,
      trace_id: executionState.trace_id,
      operation: executionState.operation,
      checks: {},
      overall_deterministic: true,
      verified_at: new Date().toISOString(),
    };

    // Check input hash
    if (actualState.input) {
      const actualInputHash = this._hashData(actualState.input);
      results.checks.input = {
        match: actualInputHash === executionState.verification.input_hash,
        expected: executionState.verification.input_hash,
        actual: actualInputHash,
      };
      if (!results.checks.input.match) results.overall_deterministic = false;
    }

    // Check output hash
    if (actualState.output) {
      const actualOutputHash = this._hashData(actualState.output);
      results.checks.output = {
        match: actualOutputHash === executionState.verification.output_hash,
        expected: executionState.verification.output_hash,
        actual: actualOutputHash,
      };
      if (!results.checks.output.match) results.overall_deterministic = false;
    }

    // Check database state
    if (actualState.database_state) {
      const actualDbHash = this._hashData(actualState.database_state);
      const expectedDbHash = this._hashData(executionState.database_state);
      results.checks.database = {
        match: actualDbHash === expectedDbHash,
        expected: expectedDbHash,
        actual: actualDbHash,
      };
      if (!results.checks.database.match) results.overall_deterministic = false;
    }

    // Check external dependencies
    if (actualState.external_dependencies) {
      const actualExtHash = this._hashData(actualState.external_dependencies);
      const expectedExtHash = this._hashData(executionState.external_dependencies);
      results.checks.external_dependencies = {
        match: actualExtHash === expectedExtHash,
        expected: expectedExtHash,
        actual: actualExtHash,
      };
      if (!results.checks.external_dependencies.match) results.overall_deterministic = false;
    }

    // Record verification result
    decisionLedger.recordReplayVerification({
      trace_id: executionState.trace_id,
      replay_id: replayId,
      input_hash: executionState.verification.input_hash,
      output_hash: executionState.verification.output_hash,
      deterministic: results.overall_deterministic,
    }).catch(() => {});

    return results;
  }

  getReplaysByTrace(traceId) {
    const basic = Array.from(this.replayRecords.values()).filter(r => r.trace_id === traceId);
    const distributed = Array.from(this.executionStates.values()).filter(r => r.trace_id === traceId);
    return { basic, distributed };
  }

  getStatistics() {
    const records = Array.from(this.replayRecords.values());
    const states = Array.from(this.executionStates.values());
    return {
      total_replays: records.length,
      distributed_replays: states.length,
      deterministic_count: records.filter(r => r.verification.deterministic).length,
      operations: [...new Set(records.map(r => r.operation))],
      traces: [...new Set(records.map(r => r.trace_id).filter(Boolean))],
    };
  }

  generateReplayProof(replayId) {
    const record = this.replayRecords.get(replayId);
    const executionState = this.executionStates.get(replayId);
    if (!record && !executionState) return { valid: false, error: `Replay ${replayId} not found` };

    const source = record || executionState;

    return {
      proof_id: `RPF-${Date.now()}-${randomUUID().slice(0, 8)}`,
      replay_id: replayId,
      trace_id: source.trace_id,
      operation: source.operation,
      timestamp: source.timestamp,
      input_fingerprint: record?.verification.input_fingerprint || executionState?.verification.input_hash,
      output_fingerprint: record?.verification.output_fingerprint || executionState?.verification.output_hash,
      deterministic: source.verification.deterministic,
      environment: { node_version: process.version, environment_hash: source.metadata?.environment_hash },
      verification: {
        method: 'SHA-256 hash comparison',
        input_hash: record?.input.body_hash || executionState?.verification.input_hash,
        output_hash: record?.output.response_hash || executionState?.verification.output_hash,
        status_code: record?.output.status_code || executionState?.output.status_code,
      },
      distributed: !!executionState,
      distributed_details: executionState ? {
        database_state_captured: !!executionState.database_state,
        external_dependencies_captured: !!executionState.external_dependencies,
        circuit_breaker_state_captured: !!executionState.circuit_breaker_state,
        state_hash: executionState.verification.state_hash,
      } : null,
      generated_at: new Date().toISOString(),
    };
  }

  _hashData(data) {
    const sorted = JSON.stringify(data, Object.keys(data).sort());
    return crypto.createHash('sha256').update(sorted || '').digest('hex');
  }

  _hashEnvironment() {
    const envStr = JSON.stringify({
      node_version: process.version,
      platform: process.platform,
      arch: process.arch,
    });
    return crypto.createHash('sha256').update(envStr).digest('hex');
  }

  _computeFingerprint(data) {
    const payload = JSON.stringify(data, Object.keys(data).sort());
    return crypto.createHash('sha256').update(payload).digest('hex');
  }
}

const deterministicReplay = new DeterministicReplayService();
export default deterministicReplay;

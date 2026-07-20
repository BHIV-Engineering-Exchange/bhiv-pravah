import crypto from 'crypto';
import { randomUUID } from 'crypto';
import ProvenanceBlock from '../models/ProvenanceBlock.js';
import logger from '../config/logger.js';

class ProvenanceChainService {
  constructor() {
    this.chainTip = null;
    this.chainPosition = 0;
    this.initialized = false;
  }

  async initialize(existingState = null) {
    try {
      const lastBlock = await ProvenanceBlock.findOne({}).sort({ chain_position: -1 }).lean();
      if (lastBlock) {
        this.chainTip = lastBlock.hash;
        this.chainPosition = lastBlock.chain_position;
        this.initialized = true;
        logger.info(`[PROVENANCE] Restored chain from tip: ${this.chainTip} at position ${this.chainPosition}`);
        return;
      }

      const genesis = await this._createGenesisBlock();
      this.chainTip = genesis.hash;
      this.chainPosition = genesis.chain_position;
      this.initialized = true;

      logger.info(`[PROVENANCE] Initialized with genesis block: ${genesis.hash}`);
    } catch (error) {
      logger.error('[PROVENANCE] Initialization failed:', error);
      throw error;
    }
  }

  async _createGenesisBlock() {
    const block = {
      block_id: `PRV-${Date.now()}-GENESIS`,
      type: 'GENESIS',
      timestamp: new Date(),
      data: {
        message: 'Provenance chain initialized',
        version: '1.0.0',
        system: 'ARTHA',
      },
      previous_hash: '0'.repeat(64),
      nonce: 0,
      chain_position: 0,
    };

    block.hash = this._computeHash(block);
    const saved = await ProvenanceBlock.create(block);
    return saved;
  }

  async append(event) {
    if (!this.initialized) {
      throw new Error('[PROVENANCE] Chain not initialized. Call initialize() first.');
    }

    this.chainPosition++;
    const block = {
      block_id: `PRV-${Date.now()}-${randomUUID().slice(0, 8)}`,
      type: event.type || 'GOVERNANCE_EVENT',
      timestamp: new Date(),
      data: {
        ...event,
        recorded_at: new Date().toISOString(),
      },
      previous_hash: this.chainTip,
      nonce: 0,
      chain_position: this.chainPosition,
      lineage_anchor: event.lineage_anchor || null,
    };

    block.hash = this._computeHash(block);
    const saved = await ProvenanceBlock.create(block);
    this.chainTip = block.hash;

    logger.debug(`[PROVENANCE] Appended block: ${block.block_id} type=${block.type} position=${block.chain_position}`);
    return saved;
  }

  async recordCapabilityDecision(decision) {
    return this.append({
      type: 'CAPABILITY_DECISION',
      capability_id: decision.capability_id,
      method: decision.method,
      path: decision.path,
      outcome: decision.outcome,
      user_id: decision.user_id,
      reason: decision.reason,
      lineage_anchor: decision.lineage_anchor || null,
    });
  }

  async recordPolicyEvent(event) {
    return this.append({
      type: 'POLICY_EVENT',
      policy: event.policy,
      action: event.action,
      target: event.target,
      outcome: event.outcome,
      details: event.details,
      lineage_anchor: event.lineage_anchor || null,
    });
  }

  async recordContractVerification(verification) {
    return this.append({
      type: 'CONTRACT_VERIFICATION',
      capability_id: verification.capability_id,
      expected_hash: verification.expected_hash,
      actual_hash: verification.actual_hash,
      valid: verification.valid,
      verified_by: verification.verified_by || 'system',
      lineage_anchor: verification.lineage_anchor || null,
    });
  }

  async recordDeployment(event) {
    return this.append({
      type: 'DEPLOYMENT_EVENT',
      action: event.action,
      version: event.version,
      environment: event.environment,
      details: event.details,
    });
  }

  async recordAdversarialAttempt(attempt) {
    return this.append({
      type: 'ADVERSARIAL_ATTEMPT',
      attack_type: attempt.attack_type,
      source: attempt.source,
      blocked: attempt.blocked,
      evidence: attempt.evidence,
    });
  }

  async recordReplayVerification(verification) {
    return this.append({
      type: 'REPLAY_VERIFICATION',
      trace_id: verification.trace_id,
      deterministic: verification.deterministic,
      input_hash: verification.input_hash,
      output_hash: verification.output_hash,
      match: verification.match,
      lineage_anchor: verification.lineage_anchor || null,
    });
  }

  async recordDecisionLedger(decision) {
    return this.append({
      type: 'DECISION_LEDGER',
      decision_id: decision.decision_id,
      outcome: decision.outcome,
      reason: decision.reason,
      lineage_anchor: decision.lineage_anchor || null,
    });
  }

  async recordLineageAnchor(anchor) {
    return this.append({
      type: 'LINEAGE_ANCHOR',
      trace_id: anchor.trace_id,
      entity_type: anchor.entity_type,
      entity_id: anchor.entity_id,
      lineage_anchor: {
        trace_id: anchor.trace_id,
        entity_type: anchor.entity_type,
        entity_id: anchor.entity_id,
      },
    });
  }

  async verifyIntegrity() {
    try {
      const blocks = await ProvenanceBlock.find({}).sort({ chain_position: 1 }).lean();
      if (blocks.length === 0) return { valid: true, block_count: 0 };

      const errors = [];
      for (let i = 1; i < blocks.length; i++) {
        if (blocks[i].previous_hash !== blocks[i - 1].hash) {
          errors.push({
            block_id: blocks[i].block_id,
            position: blocks[i].chain_position,
            error: 'Chain link broken',
            expected_prev: blocks[i - 1].hash,
            actual_prev: blocks[i].previous_hash,
          });
        }

        const expectedHash = this._computeHash({
          ...blocks[i],
          hash: undefined,
        });
        if (blocks[i].hash !== expectedHash) {
          errors.push({
            block_id: blocks[i].block_id,
            position: blocks[i].chain_position,
            error: 'Hash mismatch',
            expected: expectedHash,
            actual: blocks[i].hash,
          });
        }
      }

      return {
        valid: errors.length === 0,
        block_count: blocks.length,
        chain_tip: blocks[blocks.length - 1].hash,
        errors,
      };
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }

  async getChain(options = {}) {
    const { limit = 100, offset = 0, type = null } = options;
    const query = {};
    if (type) query.type = type;

    const blocks = await ProvenanceBlock.find(query)
      .sort({ chain_position: -1 })
      .skip(offset)
      .limit(limit)
      .lean();

    const total = await ProvenanceBlock.countDocuments(query);

    return {
      blocks,
      total,
      chain_tip: this.chainTip,
      chain_position: this.chainPosition,
      initialized: this.initialized,
    };
  }

  async getCapabilityProvenance(capabilityId) {
    return ProvenanceBlock.find({
      'data.capability_id': capabilityId,
    }).sort({ chain_position: -1 }).lean();
  }

  async getLineageProvenance(traceId) {
    return ProvenanceBlock.find({
      'lineage_anchor.trace_id': traceId,
    }).sort({ chain_position: -1 }).lean();
  }

  async getRecentBlocks(count = 10) {
    return ProvenanceBlock.find({}).sort({ chain_position: -1 }).limit(count).lean();
  }

  _computeHash(block) {
    const payload = JSON.stringify({
      block_id: block.block_id,
      type: block.type,
      timestamp: block.timestamp,
      data: block.data,
      previous_hash: block.previous_hash,
      nonce: block.nonce,
      chain_position: block.chain_position,
    });

    return crypto.createHash('sha256').update(payload).digest('hex');
  }
}

const provenanceChain = new ProvenanceChainService();
export default provenanceChain;

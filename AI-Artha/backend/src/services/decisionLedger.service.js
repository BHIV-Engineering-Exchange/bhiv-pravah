import crypto from 'crypto';
import { randomUUID } from 'crypto';
import DecisionLedger from '../models/DecisionLedger.js';
import logger from '../config/logger.js';

class DecisionLedgerService {
  constructor() {
    this.chainTip = null;
    this.chainPosition = 0;
    this.initialized = false;
  }

  async initialize() {
    try {
      const lastDecision = await DecisionLedger.findOne({}).sort({ chainPosition: -1 }).lean();
      if (lastDecision) {
        this.chainTip = lastDecision.hash;
        this.chainPosition = lastDecision.chain_position;
      } else {
        const genesis = await this._createGenesis();
        this.chainTip = genesis.hash;
        this.chainPosition = genesis.chain_position;
      }
      this.initialized = true;
      logger.info(`[DECISION_LEDGER] Initialized at position ${this.chainPosition}`);
    } catch (error) {
      logger.error('[DECISION_LEDGER] Initialization failed:', error);
      throw error;
    }
  }

  async _createGenesis() {
    const block = {
      decision_id: `DLG-GENESIS-${Date.now()}`,
      decision_type: 'GOVERNANCE_ACTION',
      timestamp: new Date(),
      outcome: 'ALLOW',
      reason: 'Decision Ledger genesis block - constitutional governance initialized',
      evidence: { message: 'Decision Ledger initialized', version: '1.0.0', system: 'ARTHA' },
      chain_position: 0,
      previous_hash: '0'.repeat(64),
      hash: null,
    };
    block.hash = this._computeHash(block);
    const saved = await DecisionLedger.create(block);
    logger.info('[DECISION_LEDGER] Genesis block created');
    return saved;
  }

  async recordDecision(decision) {
    if (!this.initialized) await this.initialize();

    this.chainPosition++;
    const record = {
      decision_id: `DLG-${Date.now()}-${randomUUID().slice(0, 8)}`,
      decision_type: decision.decision_type,
      timestamp: new Date(),
      capability_id: decision.capability_id,
      method: decision.method,
      path: decision.path,
      outcome: decision.outcome,
      reason: decision.reason,
      evidence: decision.evidence || {},
      user_id: decision.user_id,
      request_context: decision.request_context || {},
      policy_context: decision.policy_context || {},
      chain_position: this.chainPosition,
      previous_hash: this.chainTip,
      replay_safe: decision.replay_safe !== false,
      constitutionally_compliant: decision.constitutionally_compliant !== false,
    };

    record.hash = this._computeHash(record);
    const saved = await DecisionLedger.create(record);
    this.chainTip = record.hash;

    logger.debug(`[DECISION_LEDGER] Recorded: ${record.decision_id} outcome=${record.outcome}`);
    return saved;
  }

  async recordCapabilityEnforcement(enforcement) {
    return this.recordDecision({
      decision_type: 'CAPABILITY_ENFORCEMENT',
      capability_id: enforcement.capability_id,
      method: enforcement.method,
      path: enforcement.path,
      outcome: enforcement.outcome,
      reason: enforcement.reason,
      evidence: enforcement.evidence,
      user_id: enforcement.user_id,
      request_context: enforcement.request_context,
      policy_context: {
        policy_name: 'capability-boundary',
        policy_version: '1.0.0',
        enforcement_point: 'middleware',
      },
    });
  }

  async recordPolicyDecision(policy) {
    return this.recordDecision({
      decision_type: 'POLICY_DECISION',
      capability_id: policy.capability_id,
      method: policy.method,
      path: policy.path,
      outcome: policy.outcome,
      reason: policy.reason,
      evidence: policy.evidence,
      user_id: policy.user_id,
      policy_context: {
        policy_name: policy.policy_name,
        policy_version: policy.policy_version || '1.0.0',
        enforcement_point: policy.enforcement_point || 'policy-engine',
      },
    });
  }

  async recordAdversarialBlock(attempt) {
    return this.recordDecision({
      decision_type: 'ADVERSARIAL_BLOCK',
      outcome: 'BLOCK',
      reason: `Adversarial attack blocked: ${attempt.attack_type}`,
      evidence: {
        attack_type: attempt.attack_type,
        source: attempt.source,
        payload: attempt.payload,
        blocked_at: new Date().toISOString(),
      },
    });
  }

  async recordReplayVerification(verification) {
    return this.recordDecision({
      decision_type: 'REPLAY_VERIFICATION',
      outcome: verification.deterministic ? 'ALLOW' : 'DENY',
      reason: verification.deterministic
        ? `Replay verified: deterministic execution confirmed`
        : `Replay failed: execution non-deterministic`,
      evidence: {
        trace_id: verification.trace_id,
        replay_id: verification.replay_id,
        input_hash: verification.input_hash,
        output_hash: verification.output_hash,
        deterministic: verification.deterministic,
      },
    });
  }

  async verifyChainIntegrity() {
    try {
      const blocks = await DecisionLedger.find({}).sort({ chain_position: 1 }).lean();
      if (blocks.length === 0) return { valid: true, block_count: 0 };

      const errors = [];
      for (let i = 1; i < blocks.length; i++) {
        if (blocks[i].previous_hash !== blocks[i - 1].hash) {
          errors.push({
            block_id: blocks[i].decision_id,
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
            block_id: blocks[i].decision_id,
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

  async getDecisionHistory(filters = {}) {
    const query = {};
    if (filters.decision_type) query.decision_type = filters.decision_type;
    if (filters.outcome) query.outcome = filters.outcome;
    if (filters.capability_id) query.capability_id = filters.capability_id;
    if (filters.from_date) query.timestamp = { $gte: new Date(filters.from_date) };
    if (filters.to_date) {
      query.timestamp = query.timestamp || {};
      query.timestamp.$lte = new Date(filters.to_date);
    }

    return DecisionLedger.find(query).sort({ chain_position: -1 }).limit(filters.limit || 100).lean();
  }

  async getDecisionStats() {
    const stats = await DecisionLedger.aggregate([
      {
        $group: {
          _id: { decision_type: '$decision_type', outcome: '$outcome' },
          count: { $sum: 1 },
          latest: { $max: '$timestamp' },
        },
      },
      { $sort: { '_id.decision_type': 1, '_id.outcome': 1 } },
    ]);

    const total = await DecisionLedger.countDocuments();
    const byType = await DecisionLedger.aggregate([
      { $group: { _id: '$decision_type', count: { $sum: 1 } } },
      { $sort: { count: -1 } },
    ]);

    return { total, by_type: byType, breakdown: stats };
  }

  _computeHash(block) {
    const payload = JSON.stringify({
      decision_id: block.decision_id,
      decision_type: block.decision_type,
      timestamp: block.timestamp,
      capability_id: block.capability_id,
      method: block.method,
      path: block.path,
      outcome: block.outcome,
      reason: block.reason,
      evidence: block.evidence,
      chain_position: block.chain_position,
      previous_hash: block.previous_hash,
    });
    return crypto.createHash('sha256').update(payload).digest('hex');
  }
}

const decisionLedger = new DecisionLedgerService();
export default decisionLedger;

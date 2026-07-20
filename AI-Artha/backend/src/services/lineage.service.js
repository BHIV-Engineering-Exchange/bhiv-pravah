import crypto from 'crypto';
import LineageAnchor from '../models/LineageAnchor.js';
import provenanceChain from './provenanceChain.service.js';
import decisionLedger from './decisionLedger.service.js';
import logger from '../config/logger.js';

class LineageService {
  constructor() {
    this.initialized = false;
  }

  async initialize() {
    this.initialized = true;
    logger.info('[LINEAGE] Service initialized');
  }

  async anchorEntity(anchorData) {
    if (!this.initialized) await this.initialize();

    const contentHash = this._computeContentHash(anchorData.entity_data || {});

    const anchor = {
      trace_id: anchorData.trace_id,
      entity_type: anchorData.entity_type,
      entity_id: String(anchorData.entity_id),
      anchor_type: anchorData.anchor_type,
      anchor_data: anchorData.anchor_data || {},
      content_hash: contentHash,
      bucket_reference: anchorData.bucket_reference || {},
      mdu_reference: anchorData.mdu_reference || {},
      parent_lineage_id: anchorData.parent_lineage_id || null,
    };

    const saved = await LineageAnchor.create(anchor);

    await provenanceChain.recordLineageAnchor({
      trace_id: anchorData.trace_id,
      entity_type: anchorData.entity_type,
      entity_id: String(anchorData.entity_id),
    });

    logger.debug(`[LINEAGE] Anchored: ${saved.lineage_id} ${anchorData.entity_type}:${anchorData.entity_id}`);
    return saved;
  }

  async anchorToBucket(traceId, entityType, entityId, bucketData) {
    return this.anchorEntity({
      trace_id: traceId,
      entity_type: entityType,
      entity_id: entityId,
      anchor_type: 'BUCKET_STORAGE',
      anchor_data: {
        operation: 'STORE',
        immutable: true,
        timestamp: new Date().toISOString(),
      },
      bucket_reference: {
        bucket_id: bucketData.bucket_id,
        bucket_path: bucketData.bucket_path,
        immutable_ref: bucketData.immutable_ref,
      },
    });
  }

  async anchorToMDU(traceId, entityType, entityId, mduData) {
    return this.anchorEntity({
      trace_id: traceId,
      entity_type: entityType,
      entity_id: entityId,
      anchor_type: 'MDU_LINEAGE',
      anchor_data: {
        operation: 'LINK',
        semantic_continuity: true,
        timestamp: new Date().toISOString(),
      },
      mdu_reference: {
        lineage_path: mduData.lineage_path,
        semantic_version: mduData.semantic_version,
        schema_version: mduData.schema_version,
      },
    });
  }

  async anchorDecision(decisionId, traceId, entityType, entityId) {
    return this.anchorEntity({
      trace_id: traceId,
      entity_type: entityType,
      entity_id: entityId,
      anchor_type: 'DECISION_LEDGER',
      anchor_data: {
        decision_id: decisionId,
        operation: 'RECORD',
        timestamp: new Date().toISOString(),
      },
    });
  }

  async getEntityLineage(entityType, entityId) {
    const anchors = await LineageAnchor.find({
      entity_type: entityType,
      entity_id: String(entityId),
    }).sort({ created_at: 1 }).lean();

    const lineage = [];
    for (const anchor of anchors) {
      lineage.push({
        lineage_id: anchor.lineage_id,
        anchor_type: anchor.anchor_type,
        content_hash: anchor.content_hash,
        timestamp: anchor.created_at,
        verified: anchor.verified,
        bucket_reference: anchor.bucket_reference,
        mdu_reference: anchor.mdu_reference,
      });
    }

    return {
      entity_type: entityType,
      entity_id: entityId,
      lineage_count: lineage.length,
      lineage,
      complete: lineage.length > 0,
    };
  }

  async getTraceLineage(traceId) {
    const anchors = await LineageAnchor.find({
      trace_id: traceId,
    }).sort({ created_at: 1 }).lean();

    const byEntityType = {};
    for (const anchor of anchors) {
      if (!byEntityType[anchor.entity_type]) {
        byEntityType[anchor.entity_type] = [];
      }
      byEntityType[anchor.entity_type].push({
        lineage_id: anchor.lineage_id,
        entity_id: anchor.entity_id,
        anchor_type: anchor.anchor_type,
        timestamp: anchor.created_at,
      });
    }

    return {
      trace_id: traceId,
      total_anchors: anchors.length,
      by_entity_type: byEntityType,
      anchors: anchors.map(a => ({
        lineage_id: a.lineage_id,
        entity_type: a.entity_type,
        entity_id: a.entity_id,
        anchor_type: a.anchor_type,
        timestamp: a.created_at,
      })),
    };
  }

  async verifyEntityIntegrity(entityType, entityId) {
    const anchors = await LineageAnchor.find({
      entity_type: entityType,
      entity_id: String(entityId),
    }).lean();

    const results = [];
    for (const anchor of anchors) {
      const expectedHash = this._computeContentHash(anchor.anchor_data);
      results.push({
        lineage_id: anchor.lineage_id,
        anchor_type: anchor.anchor_type,
        content_hash_match: anchor.content_hash === expectedHash,
        verified: anchor.verified,
      });
    }

    return {
      entity_type: entityType,
      entity_id: entityId,
      total_anchors: results.length,
      all_verified: results.every(r => r.content_hash_match),
      results,
    };
  }

  async verifyTraceLineageIntegrity(traceId) {
    const anchors = await LineageAnchor.find({ trace_id: traceId }).lean();
    if (anchors.length === 0) {
      return { valid: true, message: 'No lineage anchors found', count: 0 };
    }

    const errors = [];
    for (const anchor of anchors) {
      const expectedHash = this._computeContentHash(anchor.anchor_data);
      if (anchor.content_hash !== expectedHash) {
        errors.push({
          lineage_id: anchor.lineage_id,
          error: 'Content hash mismatch',
          expected: expectedHash,
          actual: anchor.content_hash,
        });
      }
    }

    return {
      valid: errors.length === 0,
      trace_id: traceId,
      total_anchors: anchors.length,
      errors,
    };
  }

  async getLineageStats() {
    const total = await LineageAnchor.countDocuments();
    const byEntityType = await LineageAnchor.aggregate([
      { $group: { _id: '$entity_type', count: { $sum: 1 } } },
      { $sort: { count: -1 } },
    ]);
    const byAnchorType = await LineageAnchor.aggregate([
      { $group: { _id: '$anchor_type', count: { $sum: 1 } } },
      { $sort: { count: -1 } },
    ]);
    const verifiedCount = await LineageAnchor.countDocuments({ verified: true });

    return {
      total,
      verified: verifiedCount,
      unverified: total - verifiedCount,
      by_entity_type: byEntityType,
      by_anchor_type: byAnchorType,
    };
  }

  _computeContentHash(data) {
    const payload = JSON.stringify(data, Object.keys(data).sort());
    return crypto.createHash('sha256').update(payload).digest('hex');
  }
}

const lineage = new LineageService();
export default lineage;

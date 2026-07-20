import mongoose from 'mongoose';

const provenanceBlockSchema = new mongoose.Schema({
  block_id: {
    type: String,
    required: true,
    unique: true,
    immutable: true,
    index: true,
  },
  type: {
    type: String,
    required: true,
    enum: [
      'GENESIS',
      'CAPABILITY_DECISION',
      'POLICY_EVENT',
      'CONTRACT_VERIFICATION',
      'DEPLOYMENT_EVENT',
      'ADVERSARIAL_ATTEMPT',
      'REPLAY_VERIFICATION',
      'DECISION_LEDGER',
      'LINEAGE_ANCHOR',
      'VERIFICATION_RESULT',
    ],
    index: true,
  },
  timestamp: {
    type: Date,
    required: true,
    immutable: true,
    index: true,
  },
  data: {
    type: mongoose.Schema.Types.Mixed,
    required: true,
  },
  previous_hash: {
    type: String,
    required: true,
    immutable: true,
  },
  nonce: {
    type: Number,
    default: 0,
  },
  hash: {
    type: String,
    required: true,
    unique: true,
    immutable: true,
    index: true,
  },
  chain_position: {
    type: Number,
    required: true,
    index: true,
  },
  lineage_anchor: {
    trace_id: String,
    entity_type: String,
    entity_id: String,
  },
}, {
  timestamps: false,
});

provenanceBlockSchema.index({ type: 1, timestamp: -1 });
provenanceBlockSchema.index({ 'lineage_anchor.trace_id': 1 });
provenanceBlockSchema.index({ 'lineage_anchor.entity_type': 1, 'lineage_anchor.entity_id': 1 });

export default mongoose.model('ProvenanceBlock', provenanceBlockSchema);

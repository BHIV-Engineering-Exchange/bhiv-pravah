import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

const reconcileRecordSchema = new mongoose.Schema({
  reconcileId: {
    type: String,
    unique: true,
    default: () => `REC-${randomUUID()}`,
    immutable: true,
    index: true,
  },
  reconcileType: {
    type: String,
    enum: ['bank', 'gst', 'tds', 'intercompany', 'vendor', 'customer'],
    required: true,
    index: true,
  },
  companyId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Company',
    index: true,
  },
  period: {
    financialYear: String,
    quarter: String,
    month: String,
  },
  status: {
    type: String,
    enum: ['in_progress', 'completed', 'discrepancy', 'resolved'],
    default: 'in_progress',
    index: true,
  },
  summary: {
    totalItems: { type: Number, default: 0 },
    matched: { type: Number, default: 0 },
    unmatched: { type: Number, default: 0 },
    discrepancyCount: { type: Number, default: 0 },
    totalDiscrepancyAmount: { type: String, default: '0' },
  },
  items: [{
    sourceType: String,
    sourceId: String,
    sourceAmount: String,
    targetType: String,
    targetId: String,
    targetAmount: String,
    difference: String,
    status: {
      type: String,
      enum: ['matched', 'unmatched', 'partial', 'discrepancy'],
    },
    notes: String,
  }],
  reconciledBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  verifiedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
  },
  verifiedAt: Date,
  journalEntryIds: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'JournalEntry',
  }],
  traceId: String,
}, {
  timestamps: true,
});

reconcileRecordSchema.index({ reconcileType: 1, companyId: 1 });
reconcileRecordSchema.index({ status: 1, createdAt: -1 });
reconcileRecordSchema.index({ 'period.financialYear': 1, 'period.quarter': 1 });

export default mongoose.model('ReconcileRecord', reconcileRecordSchema);

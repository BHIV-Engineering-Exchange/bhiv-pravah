import mongoose from 'mongoose';

const auditLogSchema = new mongoose.Schema({
  action: {
    type: String,
    required: true,
    // e.g., 'journal_entry.created', 'invoice.paid', 'user.login'
  },
  entityType: {
    type: String,
    required: true,
    // e.g., 'JournalEntry', 'Invoice', 'User'
  },
  entityId: {
    type: String,
    required: true,
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
  },
  ipAddress: String,
  userAgent: String,
  changes: {
    type: mongoose.Schema.Types.Mixed,
    // Store before/after for modifications
  },
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    // Additional context
  },
  timestamp: {
    type: Date,
    default: Date.now,
    immutable: true,
  },
}, {
  timestamps: false, // Use custom timestamp field
});

// Additional indexes for performance
auditLogSchema.index({ entityType: 1, entityId: 1 });
auditLogSchema.index({ userId: 1 });
auditLogSchema.index({ timestamp: -1 });
auditLogSchema.index({ action: 1 });
auditLogSchema.index({ entityType: 1, timestamp: -1 });
auditLogSchema.index({ userId: 1, timestamp: -1 });
auditLogSchema.index({ ipAddress: 1 });

// Make immutable
auditLogSchema.pre('save', function(next) {
  if (!this.isNew) {
    return next(new Error('Audit logs cannot be modified'));
  }
  next();
});

export default mongoose.model('AuditLog', auditLogSchema);
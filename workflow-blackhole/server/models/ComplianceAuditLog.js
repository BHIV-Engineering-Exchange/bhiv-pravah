const mongoose = require('mongoose');

const complianceAuditLogSchema = new mongoose.Schema({
  eventId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  timestamp: {
    type: Date,
    default: Date.now,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  action: {
    type: String,
    required: true,
    enum: [
      'set_consent', 'get_consent', 'access_consent', 'delete_consent',
      'api_set_consent', 'api_get_consent', 'api_list_consents', 'api_get_audit_logs',
      'apply_retention_policy', 'ems_forward', 'access', 'modify', 'delete', 'read',
      'procurement_analysis', 'procurement_report_generated'
    ],
    index: true
  },
  resource: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['success', 'failure', 'pending'],
    default: 'success'
  },
  details: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  ipAddress: {
    type: String
  },
  userAgent: {
    type: String
  },
  reason: {
    type: String
  },
  purpose: {
    type: String
  },
  viaEndpoint: {
    type: String
  },
  emsTraceId: {
    type: String
  },
  emsSource: {
    type: String
  },
  prevHash: {
    type: String
  },
  hash: {
    type: String,
    required: true
  }
}, {
  timestamps: false // We use our own timestamp field
});

// Indexes for efficient querying
complianceAuditLogSchema.index({ timestamp: -1 });
complianceAuditLogSchema.index({ userId: 1, timestamp: -1 });
complianceAuditLogSchema.index({ action: 1, timestamp: -1 });
complianceAuditLogSchema.index({ resource: 1, timestamp: -1 });

module.exports = mongoose.model('ComplianceAuditLog', complianceAuditLogSchema);
const mongoose = require('mongoose');

const consentSchema = new mongoose.Schema({
  employeeId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  monitoringEnabled: {
    type: Boolean,
    required: true,
    default: false
  },
  retentionDays: {
    type: Number,
    default: 90
  },
  dataCategories: [{
    type: String,
    enum: ['analytics', 'security', 'performance', 'all'],
    default: ['all']
  }],
  expirationDate: {
    type: Date,
    required: true
  },
  lastUpdated: {
    type: Date,
    default: Date.now
  },
  lastUpdatedBy: {
    type: String,
    default: 'system'
  },
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

// Index for efficient queries
consentSchema.index({ employeeId: 1, isActive: 1 });
consentSchema.index({ expirationDate: 1 });

module.exports = mongoose.model('Consent', consentSchema);
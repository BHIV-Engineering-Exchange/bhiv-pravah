const mongoose = require('mongoose');

// Model for storing individual biometric punches
const biometricPunchSchema = new mongoose.Schema({
  employeeId: {
    type: String,
    required: true,
    index: true
  },
  biometricId: {
    type: String,
    index: true
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    index: true
  },
  punchTime: {
    type: Date,
    required: true,
    index: true
  },
  date: {
    type: Date,
    required: true,
    index: true
  },
  punchType: {
    type: String,
    enum: ['In', 'Out', 'Unknown'],
    default: 'Unknown'
  },
  deviceId: {
    type: String
  },
  location: {
    type: String
  },
  uploadBatch: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'BiometricUpload',
    index: true
  },
  isProcessed: {
    type: Boolean,
    default: false,
    index: true
  },
  processedIntoAttendance: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'DailyAttendance'
  },
  rawData: {
    type: mongoose.Schema.Types.Mixed // Store original CSV row data
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Compound indexes for efficient queries
biometricPunchSchema.index({ employeeId: 1, date: 1, punchTime: 1 });
biometricPunchSchema.index({ user: 1, date: 1, punchTime: 1 });
biometricPunchSchema.index({ uploadBatch: 1, isProcessed: 1 });

module.exports = mongoose.model('BiometricPunch', biometricPunchSchema);

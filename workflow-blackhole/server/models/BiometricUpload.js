const mongoose = require('mongoose');

const biometricUploadSchema = new mongoose.Schema({
  uploadDate: { 
    type: Date, 
    default: Date.now,
    index: true
  },
  fileName: { 
    type: String, 
    required: true 
  },
  originalFileName: {
    type: String,
    required: true
  },
  filePath: {
    type: String,
    required: true
  },
  fileSize: {
    type: Number,
    required: true
  },
  processedBy: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', 
    required: true,
    index: true
  },
  totalRecords: { 
    type: Number, 
    default: 0 
  },
  successfulMatches: { 
    type: Number, 
    default: 0 
  },
  discrepancies: { 
    type: Number, 
    default: 0 
  },
  newRecords: {
    type: Number,
    default: 0
  },
  updatedRecords: {
    type: Number,
    default: 0
  },
  status: { 
    type: String, 
    enum: ['Processing', 'Completed', 'Failed', 'Pending Review'], 
    default: 'Processing',
    index: true
  },
  processingStartTime: {
    type: Date,
    default: Date.now
  },
  processingEndTime: {
    type: Date
  },
  errorLog: [{
    row: Number,
    error: String,
    data: mongoose.Schema.Types.Mixed,
    timestamp: { type: Date, default: Date.now }
  }],
  warningLog: [{
    row: Number,
    warning: String,
    data: mongoose.Schema.Types.Mixed,
    timestamp: { type: Date, default: Date.now }
  }],
  summary: {
    dateRange: {
      start: Date,
      end: Date
    },
    employeesProcessed: [String], // Employee IDs or names
    departmentsAffected: [String],
    averageWorkingHours: Number,
    totalWorkingDays: Number,
    attendanceRate: Number
  },
  preview: {
    headers: [String],
    sampleRows: [mongoose.Schema.Types.Mixed],
    totalRows: Number,
    detectedFormat: String // 'Standard', 'Custom', 'Unknown'
  },
  mappingConfig: {
    employeeIdColumn: String,
    employeeNameColumn: String,
    dateColumn: String,
    timeInColumn: String,
    timeOutColumn: String,
    deviceIdColumn: String,
    locationColumn: String,
    customMappings: mongoose.Schema.Types.Mixed
  },
  validationRules: {
    requireEmployeeMatch: { type: Boolean, default: true },
    allowFutureDate: { type: Boolean, default: false },
    maxWorkingHours: { type: Number, default: 16 },
    minWorkingHours: { type: Number, default: 0.5 },
    allowWeekendWork: { type: Boolean, default: false }
  },
  comparisonResults: [{
    date: Date,
    employee: {
      id: String,
      name: String,
      email: String
    },
    biometric: {
      timeIn: Date,
      timeOut: Date,
      deviceId: String,
      location: String
    },
    startDay: {
      timeIn: Date,
      timeOut: Date,
      location: {
        latitude: Number,
        longitude: Number,
        address: String
      }
    },
    discrepancy: {
      hasDiscrepancy: { type: Boolean, default: false },
      timeInDiff: Number, // minutes
      timeOutDiff: Number, // minutes
      locationMismatch: { type: Boolean, default: false },
      notes: String
    },
    recommendation: {
      action: {
        type: String,
        enum: ['Accept Biometric', 'Accept Start Day', 'Manual Review', 'Reject Both'],
        default: 'Manual Review'
      },
      confidence: { type: Number, min: 0, max: 1 },
      reason: String
    }
  }],
  approvalStatus: {
    type: String,
    enum: ['Pending', 'Approved', 'Rejected', 'Partially Approved'],
    default: 'Pending',
    index: true
  },
  approvedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  approvedAt: Date,
  rejectionReason: String,
  notes: {
    type: String,
    maxlength: 1000
  },
  isActive: {
    type: Boolean,
    default: true,
    index: true
  },
  createdAt: { 
    type: Date, 
    default: Date.now,
    index: true
  },
  updatedAt: { 
    type: Date, 
    default: Date.now 
  }
}, {
  timestamps: true
});

// Update the updatedAt field before saving
biometricUploadSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// Indexes for efficient queries
biometricUploadSchema.index({ uploadDate: -1, status: 1 });
biometricUploadSchema.index({ processedBy: 1, status: 1 });
biometricUploadSchema.index({ 'summary.dateRange.start': 1, 'summary.dateRange.end': 1 });

// Virtual for processing duration
biometricUploadSchema.virtual('processingDuration').get(function() {
  if (!this.processingStartTime) return 0;
  const endTime = this.processingEndTime || new Date();
  return Math.round((endTime - this.processingStartTime) / 1000); // seconds
});

// Virtual for success rate
biometricUploadSchema.virtual('successRate').get(function() {
  if (this.totalRecords === 0) return 0;
  return Math.round((this.successfulMatches / this.totalRecords) * 100);
});

// Virtual for error rate
biometricUploadSchema.virtual('errorRate').get(function() {
  if (this.totalRecords === 0) return 0;
  return Math.round((this.errorLog.length / this.totalRecords) * 100);
});

// Static method to get upload statistics
biometricUploadSchema.statics.getUploadStats = async function(startDate, endDate) {
  const matchCondition = {
    uploadDate: { $gte: startDate, $lte: endDate },
    isActive: true
  };
  
  const stats = await this.aggregate([
    { $match: matchCondition },
    {
      $group: {
        _id: null,
        totalUploads: { $sum: 1 },
        totalRecords: { $sum: '$totalRecords' },
        totalMatches: { $sum: '$successfulMatches' },
        totalDiscrepancies: { $sum: '$discrepancies' },
        avgProcessingTime: { $avg: '$processingDuration' },
        statusBreakdown: {
          $push: {
            status: '$status',
            count: 1
          }
        }
      }
    }
  ]);
  
  return stats[0] || {
    totalUploads: 0,
    totalRecords: 0,
    totalMatches: 0,
    totalDiscrepancies: 0,
    avgProcessingTime: 0,
    statusBreakdown: []
  };
};

// Method to add error log entry
biometricUploadSchema.methods.addError = function(row, error, data = null) {
  this.errorLog.push({
    row,
    error,
    data,
    timestamp: new Date()
  });
};

// Method to add warning log entry
biometricUploadSchema.methods.addWarning = function(row, warning, data = null) {
  this.warningLog.push({
    row,
    warning,
    data,
    timestamp: new Date()
  });
};

// Method to update processing status
biometricUploadSchema.methods.updateStatus = function(status, additionalData = {}) {
  this.status = status;
  
  if (status === 'Completed' || status === 'Failed') {
    this.processingEndTime = new Date();
  }
  
  Object.assign(this, additionalData);
  return this.save();
};

module.exports = mongoose.model('BiometricUpload', biometricUploadSchema);

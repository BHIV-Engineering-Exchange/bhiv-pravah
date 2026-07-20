const mongoose = require('mongoose');

/**
 * New Salary Record Model
 * Stores calculated salary records with date ranges, holidays, and hourly rates
 */
const newSalaryRecordSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  
  // Date Range
  startDate: {
    type: Date,
    required: true,
    index: true
  },
  endDate: {
    type: Date,
    required: true,
    index: true
  },
  
  // Holiday Management
  holidays: [{
    date: {
      type: Date,
      required: true
    },
    hours: {
      type: Number,
      default: 8 // Fixed 8 hours per holiday
    }
  }],
  
  // Hours Calculation
  workingHours: {
    type: Number,
    default: 0,
    min: 0
  },
  holidayHours: {
    type: Number,
    default: 0,
    min: 0
  },
  totalCumulativeHours: {
    type: Number,
    required: true,
    min: 0
  },
  
  // Salary Calculation
  perHourRate: {
    type: Number,
    required: true,
    min: 0
  },
  calculatedSalary: {
    type: Number,
    required: true,
    min: 0
  },
  
  // Metadata
  calculatedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  calculatedAt: {
    type: Date,
    default: Date.now
  },
  notes: {
    type: String,
    maxlength: 500
  },
  
  // Status
  status: {
    type: String,
    enum: ['Draft', 'Calculated', 'Confirmed', 'Approved', 'Paid'],
    default: 'Calculated'
  },
  
  // Confirmed Salary (Admin can set final confirmed amount)
  confirmedSalary: {
    type: Number,
    default: null
  },
  isConfirmed: {
    type: Boolean,
    default: false
  },
  confirmedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  confirmedAt: {
    type: Date
  },
  confirmationNotes: {
    type: String,
    maxlength: 500
  },
  
  // Bucket Management (for history)
  isBucketed: {
    type: Boolean,
    default: false
  },
  bucketedAt: {
    type: Date
  },
  bucketedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  
  // For payslip generation
  payslipGenerated: {
    type: Boolean,
    default: false
  },
  payslipGeneratedAt: Date
}, {
  timestamps: true
});

// Indexes for efficient queries
newSalaryRecordSchema.index({ user: 1, startDate: 1, endDate: 1 });
newSalaryRecordSchema.index({ calculatedAt: -1 });
newSalaryRecordSchema.index({ status: 1 });

// Virtual for holiday count
newSalaryRecordSchema.virtual('holidayCount').get(function() {
  return this.holidays ? this.holidays.length : 0;
});

module.exports = mongoose.model('NewSalaryRecord', newSalaryRecordSchema);


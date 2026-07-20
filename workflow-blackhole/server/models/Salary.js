const mongoose = require('mongoose');

const salarySchema = new mongoose.Schema({
  user: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', 
    required: true, 
    unique: true,
    index: true
  },
  baseSalary: { 
    type: Number, 
    required: true,
    min: 0
  },
  currency: {
    type: String,
    default: 'USD',
    enum: ['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD']
  },
  salaryType: {
    type: String,
    enum: ['Monthly', 'Annual', 'Hourly', 'Daily'],
    default: 'Monthly'
  },
  payGrade: {
    type: String,
    enum: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2', 'E1', 'E2'],
    index: true
  },
  adjustments: [{
    type: {
      type: String,
      enum: ['Bonus', 'Increment', 'Deduction', 'Allowance', 'Overtime', 'Commission'],
      required: true
    },
    amount: { 
      type: Number, 
      required: true 
    },
    percentage: Number, // For percentage-based adjustments
    reason: { 
      type: String, 
      required: true,
      maxlength: 200
    },
    isRecurring: {
      type: Boolean,
      default: false
    },
    frequency: {
      type: String,
      enum: ['Monthly', 'Quarterly', 'Annually', 'One-time'],
      default: 'One-time'
    },
    effectiveDate: {
      type: Date,
      default: Date.now
    },
    expiryDate: Date,
    approvedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    date: { 
      type: Date, 
      default: Date.now 
    },
    isActive: {
      type: Boolean,
      default: true
    }
  }],
  allowances: {
    housing: { type: Number, default: 0 },
    transport: { type: Number, default: 0 },
    medical: { type: Number, default: 0 },
    food: { type: Number, default: 0 },
    communication: { type: Number, default: 0 },
    other: { type: Number, default: 0 }
  },
  deductions: {
    tax: { type: Number, default: 0 },
    insurance: { type: Number, default: 0 },
    providentFund: { type: Number, default: 0 },
    loan: { type: Number, default: 0 },
    other: { type: Number, default: 0 }
  },
  joiningDate: { 
    type: Date, 
    required: true,
    index: true
  },
  probationPeriod: {
    duration: { type: Number, default: 3 }, // months
    endDate: Date,
    isCompleted: { type: Boolean, default: false },
    confirmationDate: Date
  },
  salaryHistory: [{
    previousSalary: Number,
    newSalary: Number,
    effectiveDate: Date,
    reason: String,
    approvedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    changePercentage: Number
  }],
  bankDetails: {
    accountNumber: String,
    bankName: String,
    branchCode: String,
    ifscCode: String,
    accountHolderName: String
  },
  taxInformation: {
    taxId: String,
    taxBracket: String,
    exemptions: [{
      type: String,
      amount: Number,
      description: String
    }]
  },
  performanceIncentives: {
    targetBased: { type: Boolean, default: false },
    kpiMultiplier: { type: Number, default: 1.0 },
    bonusEligible: { type: Boolean, default: true }
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
  },
  lastCalculated: Date,
  nextReviewDate: Date
}, {
  timestamps: true
});

// Update the updatedAt field before saving
salarySchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  
  // Calculate probation end date if not set
  if (this.joiningDate && !this.probationPeriod.endDate) {
    const endDate = new Date(this.joiningDate);
    endDate.setMonth(endDate.getMonth() + this.probationPeriod.duration);
    this.probationPeriod.endDate = endDate;
  }
  
  next();
});

// Virtual for total allowances
salarySchema.virtual('totalAllowances').get(function() {
  return Object.values(this.allowances).reduce((sum, amount) => sum + (amount || 0), 0);
});

// Virtual for total deductions
salarySchema.virtual('totalDeductions').get(function() {
  return Object.values(this.deductions).reduce((sum, amount) => sum + (amount || 0), 0);
});

// Virtual for gross salary (base + allowances)
salarySchema.virtual('grossSalary').get(function() {
  return this.baseSalary + this.totalAllowances;
});

// Virtual for net salary (gross - deductions)
salarySchema.virtual('netSalary').get(function() {
  return this.grossSalary - this.totalDeductions;
});

// Method to calculate monthly salary with attendance
salarySchema.methods.calculateMonthlySalary = function(workingDays, attendedDays, adjustments = []) {
  const dailyRate = this.baseSalary / workingDays;
  const basePay = dailyRate * attendedDays;
  
  // Add allowances
  const totalAllowances = this.totalAllowances;
  
  // Calculate active adjustments
  const activeAdjustments = this.adjustments.filter(adj => adj.isActive);
  const adjustmentAmount = activeAdjustments.reduce((sum, adj) => {
    if (adj.percentage) {
      return sum + (basePay * adj.percentage / 100);
    }
    return sum + adj.amount;
  }, 0);
  
  // Add external adjustments (overtime, bonuses, etc.)
  const externalAdjustments = adjustments.reduce((sum, adj) => sum + adj.amount, 0);
  
  const grossPay = basePay + totalAllowances + adjustmentAmount + externalAdjustments;
  const netPay = grossPay - this.totalDeductions;
  
  return {
    basePay: Math.round(basePay * 100) / 100,
    allowances: totalAllowances,
    adjustments: adjustmentAmount + externalAdjustments,
    grossPay: Math.round(grossPay * 100) / 100,
    deductions: this.totalDeductions,
    netPay: Math.round(netPay * 100) / 100,
    workingDays,
    attendedDays,
    attendancePercentage: Math.round((attendedDays / workingDays) * 100)
  };
};

// Static method to get salary statistics
salarySchema.statics.getSalaryStats = async function() {
  const stats = await this.aggregate([
    { $match: { isActive: true } },
    {
      $group: {
        _id: null,
        avgSalary: { $avg: '$baseSalary' },
        minSalary: { $min: '$baseSalary' },
        maxSalary: { $max: '$baseSalary' },
        totalEmployees: { $sum: 1 }
      }
    }
  ]);
  
  return stats[0] || {};
};

// Compound indexes for efficient queries
salarySchema.index({ payGrade: 1, isActive: 1 });
salarySchema.index({ joiningDate: -1, isActive: 1 });

module.exports = mongoose.model('Salary', salarySchema);

const mongoose = require('mongoose');

// Enhanced Employee Master for salary calculations
const employeeMasterSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true,
    index: true
  },
  employeeId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  biometricId: {
    type: String,
    index: true,
    sparse: true
  },
  name: {
    type: String,
    required: true
  },
  department: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Department'
  },
  designation: {
    type: String
  },
  joiningDate: {
    type: Date,
    required: true
  },
  
  // Salary Configuration
  salaryType: {
    type: String,
    enum: ['Monthly', 'Hourly', 'Daily'],
    default: 'Monthly',
    required: true
  },
  monthlySalary: {
    type: Number,
    default: 0
  },
  hourlyRate: {
    type: Number,
    default: 0
  },
  dailyRate: {
    type: Number,
    default: 0
  },
  
  // Working Hours Configuration
  standardShiftHours: {
    type: Number,
    default: 8
  },
  standardWorkingDays: {
    type: Number,
    default: 26
  },
  halfDayThreshold: {
    type: Number,
    default: 4 // Hours worked to consider half-day
  },
  
  // Overtime Configuration
  overtimeEnabled: {
    type: Boolean,
    default: true
  },
  overtimeRate: {
    type: Number,
    default: 1.5 // 1.5x multiplier
  },
  
  // Allowances
  allowances: {
    housing: { type: Number, default: 0 },
    transport: { type: Number, default: 0 },
    medical: { type: Number, default: 0 },
    food: { type: Number, default: 0 },
    other: { type: Number, default: 0 }
  },
  
  // Deductions
  deductions: {
    tax: { type: Number, default: 0 },
    insurance: { type: Number, default: 0 },
    providentFund: { type: Number, default: 0 },
    loan: { type: Number, default: 0 },
    other: { type: Number, default: 0 }
  },
  
  // Status
  isActive: {
    type: Boolean,
    default: true,
    index: true
  },
  exitDate: {
    type: Date
  },
  
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Virtual for calculated rates
employeeMasterSchema.virtual('calculatedHourlyRate').get(function() {
  if (this.hourlyRate > 0) return this.hourlyRate;
  if (this.dailyRate > 0) return this.dailyRate / this.standardShiftHours;
  if (this.monthlySalary > 0) {
    const totalMonthlyHours = this.standardWorkingDays * this.standardShiftHours;
    return this.monthlySalary / totalMonthlyHours;
  }
  return 0;
});

employeeMasterSchema.virtual('calculatedDailyRate').get(function() {
  if (this.dailyRate > 0) return this.dailyRate;
  if (this.monthlySalary > 0) return this.monthlySalary / this.standardWorkingDays;
  if (this.hourlyRate > 0) return this.hourlyRate * this.standardShiftHours;
  return 0;
});

employeeMasterSchema.set('toJSON', { virtuals: true });
employeeMasterSchema.set('toObject', { virtuals: true });

module.exports = mongoose.model('EmployeeMaster', employeeMasterSchema);

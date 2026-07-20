import mongoose from 'mongoose';
import Decimal from 'decimal.js';

const tdsEntrySchema = new mongoose.Schema({
  entryNumber: {
    type: String,
    unique: true,
    // Format: TDS-YYYYMMDD-XXXX (auto-generated)
  },
  
  transactionDate: {
    type: Date,
    required: true,
    default: Date.now,
  },
  
  // Party details
  deductee: {
    name: {
      type: String,
      required: true,
    },
    pan: {
      type: String,
      required: true,
      match: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
    },
    address: String,
  },

  employeeDetails: {
    employeeId: String,
    department: String,
    designation: String,
  },

  salaryDetails: {
    basic: String,
    hra: String,
    perquisites: String,
    otherAllowances: String,
    deductions: String,
    employerDeductions: String,
    taxableSalary: String,
  },
  
  // Transaction details
  section: {
    type: String,
    required: true,
    enum: [
      '194A', // Interest other than on securities
      '194C', // Contractor payments
      '194H', // Commission/brokerage
      '194I', // Rent
      '194J', // Professional/technical services
      '192',  // Salary
      '194Q', // Purchase of goods
      'other',
    ],
  },
  
  nature: {
    type: String,
    required: true,
    // e.g., 'Professional Fees', 'Rent', 'Interest', etc.
  },
  
  paymentAmount: {
    type: String,
    required: true,
  },
  
  tdsRate: {
    type: Number,
    required: true,
    // e.g., 10 for 10%
  },
  
  tdsAmount: {
    type: String,
    required: true,
  },
  
  netPayable: {
    type: String,
    // paymentAmount - tdsAmount (calculated automatically)
  },
  
  // Payment details
  challanNumber: String,
  challanDate: Date,
  bankBSR: String,
  
  // Accounting
  expenseAccount: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'ChartOfAccounts',
  },
  
  tdsPayableAccount: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'ChartOfAccounts',
  },
  
  journalEntryId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'JournalEntry',
  },
  
  // Status
  status: {
    type: String,
    enum: ['pending', 'deducted', 'deposited', 'filed'],
    default: 'pending',
  },
  
  // Form 26AS reconciliation
  form26ASMatched: {
    type: Boolean,
    default: false,
  },
  
  // Metadata
  quarter: {
    type: String,
    enum: ['Q1', 'Q2', 'Q3', 'Q4'],
  },
  financialYear: String,
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  notes: String,
}, {
  timestamps: true,
});

// Generate entry number and calculate net payable
tdsEntrySchema.pre('save', async function(next) {
  // Generate entry number if new
  if (this.isNew && !this.entryNumber) {
    const date = new Date();
    const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
    const count = await mongoose.model('TDSEntry').countDocuments({
      entryNumber: new RegExp(`^TDS-${dateStr}`)
    });
    this.entryNumber = `TDS-${dateStr}-${String(count + 1).padStart(4, '0')}`;
  }
  
  // Calculate net payable
  if (this.paymentAmount && this.tdsAmount) {
    const payment = new Decimal(this.paymentAmount);
    const tds = new Decimal(this.tdsAmount);
    this.netPayable = payment.minus(tds).toString();
  }
  
  next();
});

// Additional indexes for performance
tdsEntrySchema.index({ 'deductee.pan': 1 });
tdsEntrySchema.index({ status: 1 });
tdsEntrySchema.index({ quarter: 1, financialYear: 1 });
tdsEntrySchema.index({ transactionDate: -1 });
tdsEntrySchema.index({ section: 1 });
tdsEntrySchema.index({ createdBy: 1 });
tdsEntrySchema.index({ status: 1, transactionDate: -1 });
tdsEntrySchema.index({ form26ASMatched: 1 });

export default mongoose.model('TDSEntry', tdsEntrySchema);
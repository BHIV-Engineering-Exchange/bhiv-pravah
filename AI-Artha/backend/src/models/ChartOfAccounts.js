import mongoose from 'mongoose';

const chartOfAccountsSchema = new mongoose.Schema({
  code: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    // Format: 1000, 2000, etc.
  },
  name: {
    type: String,
    required: true,
    trim: true,
  },
  type: {
    type: String,
    required: true,
    enum: ['Asset', 'Liability', 'Equity', 'Income', 'Expense'],
  },
  subtype: {
    type: String,
    // e.g., 'Current Asset', 'Fixed Asset', 'Operating Expense', etc.
  },
  normalBalance: {
    type: String,
    enum: ['debit', 'credit'],
    required: true,
    // Asset/Expense = debit, Liability/Equity/Income = credit
  },
  parentAccount: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'ChartOfAccounts',
    default: null,
  },
  isActive: {
    type: Boolean,
    default: true,
  },
  description: String,
}, {
  timestamps: true,
});

// Additional indexes for performance
chartOfAccountsSchema.index({ type: 1 });
chartOfAccountsSchema.index({ isActive: 1 });
chartOfAccountsSchema.index({ type: 1, isActive: 1 });
chartOfAccountsSchema.index({ parentAccount: 1 });

// Validation: Ensure normalBalance matches type
chartOfAccountsSchema.pre('save', function(next) {
  const debitTypes = ['Asset', 'Expense'];
  const creditTypes = ['Liability', 'Equity', 'Income'];
  
  if (debitTypes.includes(this.type) && this.normalBalance !== 'debit') {
    return next(new Error(`${this.type} accounts must have debit normal balance`));
  }
  
  if (creditTypes.includes(this.type) && this.normalBalance !== 'credit') {
    return next(new Error(`${this.type} accounts must have credit normal balance`));
  }
  
  next();
});

export default mongoose.model('ChartOfAccounts', chartOfAccountsSchema);
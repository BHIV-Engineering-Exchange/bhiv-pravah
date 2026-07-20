import mongoose from 'mongoose';

const accountBalanceSchema = new mongoose.Schema({
  account: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'ChartOfAccounts',
    required: true,
    unique: true,
  },
  balance: {
    type: String,
    default: '0',
    // Stored as string for precision, represents net balance
  },
  debitTotal: {
    type: String,
    default: '0',
  },
  creditTotal: {
    type: String,
    default: '0',
  },
  lastUpdated: {
    type: Date,
    default: Date.now,
  },
}, {
  timestamps: true,
});

// Additional indexes for performance
accountBalanceSchema.index({ lastUpdated: -1 });

export default mongoose.model('AccountBalance', accountBalanceSchema);
import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

const costCentreSchema = new mongoose.Schema({
  centreId: {
    type: String,
    unique: true,
    default: () => `CC-${randomUUID()}`,
    immutable: true,
    index: true,
  },
  code: {
    type: String,
    required: true,
    unique: true,
    trim: true,
  },
  name: {
    type: String,
    required: true,
    trim: true,
  },
  type: {
    type: String,
    enum: ['cost_centre', 'profit_centre', 'branch', 'department'],
    required: true,
    index: true,
  },
  companyId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Company',
    index: true,
  },
  parentCentre: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'CostCentre',
    default: null,
  },
  manager: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
  },
  description: String,
  isActive: {
    type: Boolean,
    default: true,
  },
  budget: {
    allocated: String,
    spent: String,
    variance: String,
  },
  // Link to accounts
  linkedAccounts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'ChartOfAccounts',
  }],
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
}, {
  timestamps: true,
});

costCentreSchema.index({ companyId: 1, type: 1 });
costCentreSchema.index({ code: 1, companyId: 1 });

export default mongoose.model('CostCentre', costCentreSchema);

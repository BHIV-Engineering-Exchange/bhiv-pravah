import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

const companySchema = new mongoose.Schema({
  companyId: {
    type: String,
    unique: true,
    default: () => `CO-${randomUUID()}`,
    immutable: true,
    index: true,
  },
  name: {
    type: String,
    required: true,
    trim: true,
  },
  legalName: {
    type: String,
    trim: true,
  },
  registrationNumber: String,
  gstin: {
    type: String,
    match: /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/,
  },
  pan: {
    type: String,
    match: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
  },
  tan: String,
  cin: String,

  address: {
    line1: String,
    line2: String,
    city: String,
    state: String,
    pincode: String,
    country: { type: String, default: 'India' },
  },
  phone: String,
  email: String,
  website: String,

  // Financial year
  financialYearStart: {
    type: String,
    default: '04-01', // April 1
  },
  financialYearEnd: {
    type: String,
    default: '03-31', // March 31
  },
  baseCurrency: {
    type: String,
    default: 'INR',
  },

  // GST settings
  gstSettings: {
    registrationType: {
      type: String,
      enum: ['regular', 'composition', 'unregistered', 'consumer'],
      default: 'regular',
    },
    compositionScheme: { type: Boolean, default: false },
    hsnCode: String,
    stateCode: String,
  },

  // TDS settings
  tdsSettings: {
    tan: String,
    defaultTDSRate: { type: Number, default: 10 },
    applicableSections: [String],
  },

  // Invoice settings
  invoiceSettings: {
    prefix: { type: String, default: 'INV' },
    nextNumber: { type: Number, default: 1 },
    termsAndConditions: String,
    logo: String,
  },

  // Parent company (for consolidation)
  parentCompany: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Company',
    default: null,
  },
  isSubsidiary: {
    type: Boolean,
    default: false,
  },

  // Branch support
  branchCode: String,
  branchName: String,
  isHeadquarters: {
    type: Boolean,
    default: true,
  },

  // Cost centre / Profit centre
  costCentre: String,
  profitCentre: String,

  status: {
    type: String,
    enum: ['active', 'inactive', 'archived'],
    default: 'active',
  },

  // Consolidation settings
  consolidation: {
    enableConsolidation: { type: Boolean, default: false },
    eliminateIntercompany: { type: Boolean, default: true },
    minorityInterest: { type: Boolean, default: false },
  },

  // Owners
  owners: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
  }],
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
}, {
  timestamps: true,
});

companySchema.index({ gstin: 1 });
companySchema.index({ pan: 1 });
companySchema.index({ parentCompany: 1 });
companySchema.index({ status: 1 });
companySchema.index({ branchCode: 1 });

export default mongoose.model('Company', companySchema);

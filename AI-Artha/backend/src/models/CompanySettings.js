import mongoose from 'mongoose';

const companySettingsSchema = new mongoose.Schema({
  // Basic Info
  companyName: {
    type: String,
    required: true,
  },
  legalName: String,
  
  // Address
  address: {
    street: String,
    city: String,
    state: String,
    postalCode: String,
    country: {
      type: String,
      default: 'India',
    },
  },
  
  // Contact
  phone: String,
  email: String,
  website: String,
  
  // India Statutory IDs
  gstin: {
    type: String,
    match: /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/,
  },
  gstinRegistrations: [{
    gstin: {
      type: String,
      match: /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/,
    },
    state: String,
    branchCode: String,
    isPrimary: {
      type: Boolean,
      default: false,
    },
  }],
  pan: {
    type: String,
    match: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
  },
  tan: {
    type: String,
    match: /^[A-Z]{4}[0-9]{5}[A-Z]{1}$/,
  },
  cin: String, // Corporate Identification Number
  
  // Bank Details
  bankAccounts: [{
    bankName: String,
    accountNumber: String,
    ifscCode: String,
    accountType: {
      type: String,
      enum: ['savings', 'current'],
    },
    isPrimary: Boolean,
  }],
  
  // GST Settings
  gstSettings: {
    isRegistered: {
      type: Boolean,
      default: true,
    },
    filingFrequency: {
      type: String,
      enum: ['monthly', 'quarterly'],
      default: 'monthly',
    },
    compositionScheme: {
      type: Boolean,
      default: false,
    },
    reverseChargeMechanism: {
      type: Boolean,
      default: false,
    },
  },
  
  // TDS Settings
  tdsSettings: {
    isTANActive: {
      type: Boolean,
      default: true,
    },
    defaultTDSRate: Number,
    autoCalculateTDS: {
      type: Boolean,
      default: true,
    },
  },
  
  // Accounting Settings
  accountingSettings: {
    financialYearStart: {
      month: {
        type: Number,
        default: 4, // April
      },
      day: {
        type: Number,
        default: 1,
      },
    },
    baseCurrency: {
      type: String,
      default: 'INR',
    },
    decimalPlaces: {
      type: Number,
      default: 2,
    },
  },
  
  // Logo
  logo: {
    filename: String,
    path: String,
  },
  
  // Singleton pattern - only one settings document
  _id: {
    type: String,
    default: 'company_settings',
  },
}, {
  timestamps: true,
});

// Additional indexes for performance
companySettingsSchema.index({ gstin: 1 });
companySettingsSchema.index({ pan: 1 });
companySettingsSchema.index({ tan: 1 });
companySettingsSchema.index({ 'gstSettings.isRegistered': 1 });
companySettingsSchema.index({ 'tdsSettings.isTANActive': 1 });

export default mongoose.model('CompanySettings', companySettingsSchema);
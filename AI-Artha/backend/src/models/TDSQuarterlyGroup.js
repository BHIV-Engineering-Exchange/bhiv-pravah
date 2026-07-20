import mongoose from 'mongoose';

const tdsQuarterlyGroupSchema = new mongoose.Schema({
  quarter: {
    type: String,
    enum: ['Q1', 'Q2', 'Q3', 'Q4'],
    required: true,
  },
  financialYear: {
    type: String,
    required: true,
  },
  tan: String,
  totalDeducted: String,
  totalDeposited: String,
  sectionSummary: mongoose.Schema.Types.Mixed,
  entries: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'TDSEntry',
  }],
  challans: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'TDSChallan',
  }],
  status: {
    type: String,
    enum: ['grouped', 'validated', 'filed'],
    default: 'grouped',
  },
}, {
  timestamps: true,
});

tdsQuarterlyGroupSchema.index({ quarter: 1, financialYear: 1 });

tdsQuarterlyGroupSchema.index({ status: 1 });

export default mongoose.model('TDSQuarterlyGroup', tdsQuarterlyGroupSchema);

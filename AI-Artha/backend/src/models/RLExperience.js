import mongoose from 'mongoose';

const rlExperienceSchema = new mongoose.Schema({
  sessionId: {
    type: String,
    required: true,
    index: true,
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  
  // State
  state: {
    type: mongoose.Schema.Types.Mixed,
    required: true,
    // Example: { screen: 'invoice_create', fields_filled: ['customer', 'amount'], ... }
  },
  
  // Action
  action: {
    type: String,
    required: true,
    // Example: 'click_save', 'navigate_to_ledger', 'apply_filter', etc.
  },
  
  // Reward
  reward: {
    type: Number,
    required: true,
    // Positive for successful actions, negative for errors/inefficiencies
  },
  
  // Next state
  nextState: {
    type: mongoose.Schema.Types.Mixed,
    required: true,
  },
  
  // Terminal flag
  isTerminal: {
    type: Boolean,
    default: false,
  },
  
  // Metadata
  metadata: {
    duration: Number, // Action duration in ms
    errorOccurred: Boolean,
    errorType: String,
    userRole: String,
    timestamp: {
      type: Date,
      default: Date.now,
    },
  },
}, {
  timestamps: true,
});

// Additional indexes for performance
rlExperienceSchema.index({ sessionId: 1, createdAt: -1 });
rlExperienceSchema.index({ userId: 1, createdAt: -1 });
rlExperienceSchema.index({ 'metadata.timestamp': -1 });
rlExperienceSchema.index({ action: 1 });
rlExperienceSchema.index({ isTerminal: 1 });
rlExperienceSchema.index({ 'metadata.userRole': 1 });
rlExperienceSchema.index({ reward: -1 });

export default mongoose.model('RLExperience', rlExperienceSchema);
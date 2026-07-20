const mongoose = require('mongoose');

const aiReviewSchema = new mongoose.Schema({
  taskId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Task',
    required: true,
    index: true
  },
  submissionId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'TaskSubmission',
    required: true
  },
  repositoryUrl: {
    type: String,
    required: true
  },
  reviewStatus: {
    type: String,
    enum: ['pending', 'analyzing', 'completed', 'failed'],
    default: 'pending',
    index: true
  },
  aiProvider: {
    type: String,
    enum: ['openai', 'gemini', 'groq'],
    default: 'openai'
  },
  overallScore: {
    type: Number,
    min: 0,
    max: 100
  },
  completionPercentage: {
    type: Number,
    min: 0,
    max: 100
  },
  codeQualityScore: {
    type: Number,
    min: 0,
    max: 100
  },
  requirementsFulfillment: {
    type: Number,
    min: 0,
    max: 100
  },
  aiSummary: {
    type: String
  },
  strengths: [{
    type: String
  }],
  weaknesses: [{
    type: String
  }],
  missingRequirements: [{
    requirement: String,
    severity: {
      type: String,
      enum: ['low', 'medium', 'high', 'critical']
    },
    suggestion: String
  }],
  recommendations: [{
    type: String
  }],
  codeAnalysis: {
    filesAnalyzed: Number,
    linesOfCode: Number,
    complexity: String,
    testCoverage: String,
    documentation: String
  },
  reviewedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  reviewedAt: {
    type: Date,
    default: Date.now
  },
  errorMessage: {
    type: String
  }
}, {
  timestamps: true
});

aiReviewSchema.index({ taskId: 1, reviewStatus: 1 });
aiReviewSchema.index({ reviewedAt: -1 });

module.exports = mongoose.model('AIReview', aiReviewSchema);
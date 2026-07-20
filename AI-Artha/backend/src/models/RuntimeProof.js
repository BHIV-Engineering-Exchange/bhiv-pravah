import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

/**
 * RuntimeProof — Verifiable evidence of system execution
 * Captures actual outputs, screenshots, logs, database states
 * 
 * Purpose: Transform "claimed proof" into "verified proof"
 */
const runtimeProofSchema = new mongoose.Schema({
  proof_id: {
    type: String,
    unique: true,
    default: () => `PROOF-${randomUUID()}`,
    immutable: true,
    index: true,
  },
  trace_id: {
    type: String,
    required: true,
    index: true,
    ref: 'UnifiedTrace',
  },
  
  // Proof metadata
  proof_type: {
    type: String,
    required: true,
    enum: ['API_RESPONSE', 'DATABASE_STATE', 'TERMINAL_LOG', 'CURL_OUTPUT', 
           'SCREENSHOT', 'CHAIN_VERIFICATION', 'BALANCE_SHEET', 'INTEGRATION_TEST',
           'SETU_DISPATCH_ATTEMPT', 'SETU_ACKNOWLEDGMENT', 'SETU_REJECTION',
           'SETU_RETRY', 'DELIVERY_RECEIPT'],
  },
  endpoint: String,
  method: String, // GET, POST, etc.
  
  // Captured evidence
  request: {
    headers: mongoose.Schema.Types.Mixed,
    body: mongoose.Schema.Types.Mixed,
    query: mongoose.Schema.Types.Mixed,
    timestamp: Date,
  },
  response: {
    status: Number,
    headers: mongoose.Schema.Types.Mixed,
    body: mongoose.Schema.Types.Mixed,
    latency_ms: Number,
    timestamp: Date,
  },
  
  // Database state capture
  db_state: {
    before: mongoose.Schema.Types.Mixed,
    after: mongoose.Schema.Types.Mixed,
    queries: [String],
  },
  
  // Terminal/console output
  console_output: String,
  
  // File attachments (screenshots, curl outputs, etc.)
  attachments: [{
    filename: String,
    path: String,
    mimetype: String,
    size: Number,
    uploaded_at: Date,
  }],
  
  // Verification status
  verified: {
    type: Boolean,
    default: false,
  },
  verified_by: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
  },
  verified_at: Date,
  
  // Assertions
  assertions: [{
    description: String,
    expected: mongoose.Schema.Types.Mixed,
    actual: mongoose.Schema.Types.Mixed,
    passed: Boolean,
    message: String,
  }],
  
  // Environment context
  environment: {
    node_env: String,
    node_version: String,
    mongodb_version: String,
    redis_available: Boolean,
    timestamp: Date,
  },
  
  // Reproducibility
  reproducible: {
    type: Boolean,
    default: true,
  },
  reproduction_steps: [String],

  // SETU delivery tracking
  attempt_number: Number,
  dispatch_id: String,
  is_retry: { type: Boolean, default: false },
  retry_of: String,
  setu_reference: String,
  delivery_status: {
    type: String,
    enum: ['INITIATED', 'SENT', 'ACCEPTED', 'REJECTED', 'TIMEOUT', 'NETWORK_ERROR', 'DEAD_LETTER'],
  },
  content_hash: String,
  webhook_signature: String,
  original_proof_id: String,
  pipeline_version: { type: String, default: '1.0.0' },
  
  created_at: {
    type: Date,
    default: Date.now,
    immutable: true,
  },
}, {
  timestamps: false, // Use created_at instead
});

// Indexes
runtimeProofSchema.index({ proof_type: 1, created_at: -1 });
runtimeProofSchema.index({ endpoint: 1, method: 1 });
runtimeProofSchema.index({ verified: 1 });
runtimeProofSchema.index({ 'environment.node_env': 1 });
runtimeProofSchema.index({ dispatch_id: 1 });
runtimeProofSchema.index({ attempt_number: 1, trace_id: 1 });
runtimeProofSchema.index({ delivery_status: 1 });

// Add assertion
runtimeProofSchema.methods.addAssertion = function(description, expected, actual) {
  const passed = JSON.stringify(expected) === JSON.stringify(actual);
  this.assertions.push({
    description,
    expected,
    actual,
    passed,
    message: passed ? 'Assertion passed' : `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
  });
  return passed;
};

// Verify proof
runtimeProofSchema.methods.verify = async function(userId) {
  const allAssertionsPassed = this.assertions.every(a => a.passed);
  this.verified = allAssertionsPassed;
  this.verified_by = userId;
  this.verified_at = new Date();
  await this.save();
  return this.verified;
};

// Generate proof summary
runtimeProofSchema.methods.getSummary = function() {
  const totalAssertions = this.assertions.length;
  const passedAssertions = this.assertions.filter(a => a.passed).length;
  
  return {
    proof_id: this.proof_id,
    trace_id: this.trace_id,
    proof_type: this.proof_type,
    endpoint: this.endpoint,
    method: this.method,
    verified: this.verified,
    assertions: {
      total: totalAssertions,
      passed: passedAssertions,
      failed: totalAssertions - passedAssertions,
      pass_rate: totalAssertions > 0 ? (passedAssertions / totalAssertions * 100).toFixed(2) + '%' : 'N/A',
    },
    response_status: this.response?.status,
    latency_ms: this.response?.latency_ms,
    created_at: this.created_at,
  };
};

export default mongoose.model('RuntimeProof', runtimeProofSchema);

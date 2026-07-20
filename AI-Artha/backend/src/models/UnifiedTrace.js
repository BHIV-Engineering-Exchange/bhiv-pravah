import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

/**
 * UnifiedTrace — Single trace system for end-to-end continuity
 * Replaces fragmented trace systems with unified correlation
 * 
 * Design: Every transaction gets ONE trace_id that flows through:
 * - Journal Entry creation
 * - Signal generation
 * - Filing generation
 * - SETU dispatch
 */
const unifiedTraceSchema = new mongoose.Schema({
  trace_id: {
    type: String,
    unique: true,
    required: true,
    immutable: true,
    index: true,
    // Format: TRC-YYYYMMDD-UUID (unified format)
  },
  source: {
    type: String,
    required: true,
    enum: ['INVOICE', 'EXPENSE', 'TDS', 'MANUAL_JOURNAL', 'GST_FILING', 'TDS_FILING'],
  },
  source_id: {
    type: String,
    required: true,
    // MongoDB ObjectId as string (invoice._id, expense._id, etc.)
  },
  initiated_by: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  initiated_at: {
    type: Date,
    default: Date.now,
    immutable: true,
  },
  
  // Lifecycle tracking
  stages: [{
    stage: {
      type: String,
      enum: ['TRANSACTION_CREATED', 'JOURNAL_CREATED', 'JOURNAL_VALIDATED', 'JOURNAL_POSTED', 
             'SIGNAL_GENERATED', 'FILING_CREATED', 'FILING_VALIDATED', 'SETU_DISPATCHED',
             'SETU_ACKNOWLEDGED', 'SETU_REJECTED', 'RETRY_SCHEDULED', 'RETRY_IN_PROGRESS',
             'RETRY_EXHAUSTED', 'DEAD_LETTER', 'CONFIRMED'],
      required: true,
    },
    entity_type: {
      type: String,
      enum: ['Invoice', 'Expense', 'TDSEntry', 'JournalEntry', 'ComplianceSignal', 
             'ComplianceFiling', 'ComplianceValidationLog', 'SetuDispatch', 'Payment'],
    },
    entity_id: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      enum: ['SUCCESS', 'FAILED', 'PENDING', 'SKIPPED'],
      required: true,
    },
    timestamp: {
      type: Date,
      default: Date.now,
    },
    metadata: mongoose.Schema.Types.Mixed,
    error: String,
    attempt_number: Number,
  }],
  
  // Current state
  current_stage: {
    type: String,
    enum: ['TRANSACTION_CREATED', 'JOURNAL_CREATED', 'JOURNAL_VALIDATED', 'JOURNAL_POSTED', 
           'SIGNAL_GENERATED', 'FILING_CREATED', 'FILING_VALIDATED', 'SETU_DISPATCHED',
           'SETU_ACKNOWLEDGED', 'SETU_REJECTED', 'RETRY_SCHEDULED', 'RETRY_IN_PROGRESS',
           'RETRY_EXHAUSTED', 'DEAD_LETTER', 'CONFIRMED', 'FAILED'],
    default: 'TRANSACTION_CREATED',
  },
  status: {
    type: String,
    enum: ['IN_PROGRESS', 'COMPLETED', 'FAILED'],
    default: 'IN_PROGRESS',
  },
  
  // Linked entities (denormalized for fast lookup)
  linked_entities: {
    journal_entries: [{ type: mongoose.Schema.Types.ObjectId, ref: 'JournalEntry' }],
    signals: [{ type: mongoose.Schema.Types.ObjectId, ref: 'ComplianceSignal' }],
    filings: [{ type: mongoose.Schema.Types.ObjectId, ref: 'ComplianceFiling' }],
    validation_logs: [{ type: mongoose.Schema.Types.ObjectId, ref: 'ComplianceValidationLog' }],
    setu_dispatches: [String], // SETU dispatch IDs
  },
  
  // Replay capability
  replay_available: {
    type: Boolean,
    default: true,
  },
  replay_count: {
    type: Number,
    default: 0,
  },
  last_replayed_at: Date,
  
  // SETU dispatch tracking
  setu: {
    ack_status: {
      type: String,
      enum: ['PENDING', 'ACCEPTED', 'REJECTED', 'TIMEOUT', 'UNKNOWN'],
      default: 'PENDING',
    },
    setu_reference: String,
    callback_received_at: Date,
    callback_payload: mongoose.Schema.Types.Mixed,
    dispatch_id: String,
    last_dispatched_at: Date,
    first_dispatched_at: Date,
  },
  
  // Retry tracking
  retry: {
    count: { type: Number, default: 0 },
    max_retries: { type: Number, default: 3 },
    next_retry_at: Date,
    last_retry_at: Date,
    failure_reason: String,
  },
  
  // Dispatch attempts
  dispatch_attempts: [{
    attempt_id: String,
    attempt_number: Number,
    dispatched_at: Date,
    request_body_hash: String,
    response_status: Number,
    response_body: mongoose.Schema.Types.Mixed,
    response_latency_ms: Number,
    ack_status: String,
  }],
  
  // Pipeline metadata
  pipeline_version: { type: String, default: '1.0.0' },
  environment: { type: String, default: process.env.NODE_ENV },
  input_snapshot: mongoose.Schema.Types.Mixed,
  
  // Causality chain
  caused_by: {
    type: String,
    ref: 'UnifiedTrace',
    // Reference to parent trace_id if this trace was triggered by another
  },
  triggers: [{
    type: String,
    ref: 'UnifiedTrace',
    // Child trace_ids triggered by this trace
  }],
  
}, {
  timestamps: true,
});

// Indexes for performance
unifiedTraceSchema.index({ source: 1, source_id: 1 });
unifiedTraceSchema.index({ initiated_by: 1, initiated_at: -1 });
unifiedTraceSchema.index({ current_stage: 1, status: 1 });
unifiedTraceSchema.index({ 'stages.stage': 1, 'stages.timestamp': -1 });
unifiedTraceSchema.index({ 'linked_entities.journal_entries': 1 });
unifiedTraceSchema.index({ 'linked_entities.signals': 1 });
unifiedTraceSchema.index({ 'setu.ack_status': 1 });
unifiedTraceSchema.index({ 'retry.count': 1, 'retry.next_retry_at': 1 });
unifiedTraceSchema.index({ 'dispatch_attempts.attempt_id': 1 });

// Generate unified trace_id
unifiedTraceSchema.statics.generateTraceId = function() {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const uuid = randomUUID().slice(0, 8);
  return `TRC-${date}-${uuid}`;
};

// Add stage to trace
unifiedTraceSchema.methods.addStage = async function(stageData) {
  this.stages.push({
    stage: stageData.stage,
    entity_type: stageData.entity_type,
    entity_id: stageData.entity_id,
    status: stageData.status || 'SUCCESS',
    timestamp: new Date(),
    metadata: stageData.metadata,
    error: stageData.error,
    attempt_number: stageData.attempt_number,
  });
  
  if (stageData.status === 'SUCCESS') {
    this.current_stage = stageData.stage;
  } else if (stageData.status === 'FAILED') {
    this.status = 'FAILED';
    this.current_stage = 'FAILED';
  }
  
  // Update linked entities
  if (stageData.entity_type && stageData.entity_id) {
    const entityMap = {
      'JournalEntry': 'journal_entries',
      'ComplianceSignal': 'signals',
      'ComplianceFiling': 'filings',
      'ComplianceValidationLog': 'validation_logs',
      'SetuDispatch': 'setu_dispatches',
    };
    
    const field = entityMap[stageData.entity_type];
    if (field && this.linked_entities[field]) {
      if (!this.linked_entities[field].includes(stageData.entity_id)) {
        this.linked_entities[field].push(stageData.entity_id);
      }
    }
  }
  
  // Update SETU ack status from stage metadata
  if (stageData.stage === 'SETU_ACKNOWLEDGED' && stageData.metadata) {
    this.setu.ack_status = 'ACCEPTED';
    this.setu.setu_reference = stageData.metadata.setu_reference;
    this.setu.callback_received_at = new Date();
  } else if (stageData.stage === 'SETU_REJECTED') {
    this.setu.ack_status = 'REJECTED';
  } else if (stageData.stage === 'SETU_DISPATCHED' && stageData.metadata) {
    this.setu.last_dispatched_at = new Date();
    if (!this.setu.first_dispatched_at) this.setu.first_dispatched_at = new Date();
    this.setu.dispatch_id = stageData.metadata.dispatch_id;
    this.dispatch_attempts.push({
      attempt_id: stageData.metadata.dispatch_id,
      attempt_number: stageData.attempt_number || 1,
      dispatched_at: new Date(),
      request_body_hash: stageData.metadata.body_hash,
      response_status: stageData.metadata.response_status,
      response_body: stageData.metadata.response_body,
      response_latency_ms: stageData.metadata.latency_ms,
      ack_status: 'PENDING',
    });
  } else if (stageData.stage === 'RETRY_SCHEDULED' && stageData.metadata) {
    this.retry.count += 1;
    this.retry.next_retry_at = stageData.metadata.next_retry_at;
    this.retry.failure_reason = stageData.metadata.failure_reason;
  } else if (stageData.stage === 'DEAD_LETTER') {
    this.status = 'FAILED';
    this.current_stage = 'DEAD_LETTER';
    this.retry.failure_reason = stageData.metadata?.failure_reason || 'Max retries exceeded';
  }
  
  await this.save();
  return this;
};

// Record SETU acknowledgement
unifiedTraceSchema.methods.recordSetuAck = async function(ackPayload) {
  this.setu.ack_status = ackPayload.status || 'ACCEPTED';
  this.setu.setu_reference = ackPayload.setu_reference;
  this.setu.callback_received_at = new Date();
  this.setu.callback_payload = ackPayload;
  
  // Update last dispatch attempt
  if (this.dispatch_attempts.length > 0) {
    const lastAttempt = this.dispatch_attempts[this.dispatch_attempts.length - 1];
    lastAttempt.ack_status = this.setu.ack_status;
  }
  
  await this.addStage({
    stage: ackPayload.status === 'ACCEPTED' ? 'SETU_ACKNOWLEDGED' : 'SETU_REJECTED',
    entity_type: 'SetuDispatch',
    entity_id: this.setu.dispatch_id || 'unknown',
    status: ackPayload.status === 'ACCEPTED' ? 'SUCCESS' : 'FAILED',
    metadata: ackPayload,
  });
  
  return this;
};

// Get full trace chain with all linked entities
unifiedTraceSchema.methods.getFullChain = async function() {
  await this.populate([
    { path: 'linked_entities.journal_entries', select: 'entryNumber date status hash chainPosition' },
    { path: 'linked_entities.signals', select: 'signal_id type severity created_at' },
    { path: 'linked_entities.filings', select: 'filingId filingType created_at' },
    { path: 'linked_entities.validation_logs', select: 'filingId filing_ready errors' },
    { path: 'initiated_by', select: 'name email' },
  ]);
  
  return this;
};

export default mongoose.model('UnifiedTrace', unifiedTraceSchema);

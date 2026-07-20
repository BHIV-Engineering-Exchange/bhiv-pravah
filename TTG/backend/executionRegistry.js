// executionRegistry.js - Track execution schemas and their lifecycle
const EventEmitter = require('events');
const { writeExecutionSchema, writeExecutionStart, writeExecutionCompletion, appendExecutionLog } = require('./bucketWriter');

const registry = new Map();
const registryEvents = new EventEmitter();

function storeExecution(executionData) {
  const { execution_id, trace_id, executionSchema, user_id, timestamp } = executionData;
  
  if (!execution_id || !trace_id || !executionSchema) {
    throw new Error('Missing required fields: execution_id, trace_id, executionSchema');
  }

  const execution = {
    execution_id,
    trace_id,
    user_id,
    executionSchema,
    status: 'received',
    jobs: [],
    receivedAt: timestamp || Date.now(),
    startedAt: null,
    completedAt: null,
    error: null
  };

  registry.set(execution_id, execution);
  registryEvents.emit('execution_stored', execution);
  
  console.log(`[REGISTRY] Stored execution: ${execution_id}`);
  
  // Write to Bucket (async, non-blocking)
  writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp)
    .catch(err => console.error('[REGISTRY] Bucket write failed:', err.message));
  
  appendExecutionLog(execution_id, trace_id, 'execution_received', { status: 'received' })
    .catch(err => console.error('[REGISTRY] Log append failed:', err.message));
  
  return execution;
}

function getExecution(execution_id) {
  return registry.get(execution_id);
}

function updateExecutionStatus(execution_id, status, data = {}) {
  const execution = registry.get(execution_id);
  if (!execution) {
    console.warn(`[REGISTRY] Execution not found: ${execution_id}`);
    return null;
  }

  execution.status = status;
  Object.assign(execution, data);

  if (status === 'running' && !execution.startedAt) {
    execution.startedAt = Date.now();
    // Write start timestamp to Bucket
    writeExecutionStart(execution_id, execution.trace_id, execution.startedAt)
      .catch(err => console.error('[REGISTRY] Bucket write failed:', err.message));
    appendExecutionLog(execution_id, execution.trace_id, 'execution_started', { status: 'running' })
      .catch(err => console.error('[REGISTRY] Log append failed:', err.message));
  }
  
  if (status === 'completed' || status === 'failed') {
    execution.completedAt = Date.now();
    const duration = execution.completedAt - execution.startedAt;
    // Write completion timestamp to Bucket
    writeExecutionCompletion(execution_id, execution.trace_id, execution.completedAt, status, duration)
      .catch(err => console.error('[REGISTRY] Bucket write failed:', err.message));
    appendExecutionLog(execution_id, execution.trace_id, 'execution_completed', { status, duration })
      .catch(err => console.error('[REGISTRY] Log append failed:', err.message));
  }

  registryEvents.emit('execution_updated', execution);
  console.log(`[REGISTRY] Updated execution ${execution_id}: ${status}`);
  return execution;
}

function addJobToExecution(execution_id, jobId) {
  const execution = registry.get(execution_id);
  if (execution) {
    execution.jobs.push(jobId);
  }
}

function getAllExecutions() {
  return Array.from(registry.values());
}

function clearRegistry() {
  registry.clear();
  console.log('[REGISTRY] Cleared all executions');
}

module.exports = {
  storeExecution,
  getExecution,
  updateExecutionStatus,
  addJobToExecution,
  getAllExecutions,
  clearRegistry,
  registryEvents
};

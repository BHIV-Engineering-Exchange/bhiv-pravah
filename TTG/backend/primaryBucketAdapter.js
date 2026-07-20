// primaryBucketAdapter.js - Adapter to send execution artifacts to Primary Bucket Owner
const axios = require('axios');

const PRIMARY_BUCKET_URL = process.env.PRIMARY_BUCKET_URL || 'http://localhost:8000';

// Send execution schema to Primary Bucket
async function sendExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
  try {
    const artifact = {
      artifact_class: 'execution_metadata',
      execution_id,
      trace_id,
      executionSchema,
      timestamp: timestamp || Date.now(),
      source: 'real_time_micro_bridge'
    };

    const response = await axios.post(`${PRIMARY_BUCKET_URL}/governance/validate-artifact-admission`, 
      artifact,
      { params: { artifact_class: 'execution_metadata' } }
    );

    if (response.data.admitted) {
      console.log(`[PRIMARY_BUCKET] Execution schema admitted: ${execution_id}`);
      return { success: true, response: response.data };
    } else {
      console.warn(`[PRIMARY_BUCKET] Execution schema rejected: ${response.data.reason}`);
      return { success: false, error: response.data.reason };
    }
  } catch (error) {
    console.error(`[PRIMARY_BUCKET] Failed to send execution schema: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Send execution start timestamp
async function sendExecutionStart(execution_id, trace_id, startTimestamp) {
  try {
    const artifact = {
      artifact_class: 'execution_metadata',
      execution_id,
      trace_id,
      start_timestamp: startTimestamp || Date.now(),
      event: 'execution_started',
      source: 'real_time_micro_bridge'
    };

    await axios.post(`${PRIMARY_BUCKET_URL}/governance/validate-artifact-admission`, 
      artifact,
      { params: { artifact_class: 'execution_metadata' } }
    );

    console.log(`[PRIMARY_BUCKET] Execution start sent: ${execution_id}`);
    return { success: true };
  } catch (error) {
    console.error(`[PRIMARY_BUCKET] Failed to send execution start: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Send execution completion timestamp
async function sendExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
  try {
    const artifact = {
      artifact_class: 'execution_metadata',
      execution_id,
      trace_id,
      completion_timestamp: completionTimestamp || Date.now(),
      status: status || 'completed',
      duration: duration || null,
      event: 'execution_completed',
      source: 'real_time_micro_bridge'
    };

    await axios.post(`${PRIMARY_BUCKET_URL}/governance/validate-artifact-admission`, 
      artifact,
      { params: { artifact_class: 'execution_metadata' } }
    );

    console.log(`[PRIMARY_BUCKET] Execution completion sent: ${execution_id}`);
    return { success: true };
  } catch (error) {
    console.error(`[PRIMARY_BUCKET] Failed to send execution completion: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Send execution log entry
async function sendExecutionLog(execution_id, trace_id, event, data) {
  try {
    const artifact = {
      artifact_class: 'logs',
      execution_id,
      trace_id,
      event,
      data,
      timestamp: Date.now(),
      source: 'real_time_micro_bridge'
    };

    await axios.post(`${PRIMARY_BUCKET_URL}/governance/validate-artifact-admission`, 
      artifact,
      { params: { artifact_class: 'logs' } }
    );

    return { success: true };
  } catch (error) {
    console.error(`[PRIMARY_BUCKET] Failed to send execution log: ${error.message}`);
    return { success: false, error: error.message };
  }
}

module.exports = {
  sendExecutionSchema,
  sendExecutionStart,
  sendExecutionCompletion,
  sendExecutionLog
};

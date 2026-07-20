// executionState.js - Track execution states and job progress
const { getExecution } = require('./executionRegistry');
const { findJobById } = require('./jobQueue');

// Get detailed execution state
function getExecutionState(execution_id) {
  const execution = getExecution(execution_id);
  
  if (!execution) {
    return null;
  }
  
  // Get job states
  const jobStates = execution.jobs.map(jobId => {
    const job = findJobById(jobId);
    return {
      jobId,
      jobType: job?.jobType || 'unknown',
      status: job?.status || 'unknown',
      queuedAt: job?.queuedAt || null,
      startedAt: job?.startedAt || null,
      completedAt: job?.completedAt || null,
      duration: job?.duration || null,
      error: job?.error || null
    };
  });
  
  // Calculate overall progress
  const totalJobs = execution.jobs.length;
  const completedJobs = jobStates.filter(j => j.status === 'completed').length;
  const failedJobs = jobStates.filter(j => j.status === 'failed').length;
  const runningJobs = jobStates.filter(j => j.status === 'running').length;
  const queuedJobs = jobStates.filter(j => j.status === 'queued' || j.status === 'dispatched').length;
  
  const progress = totalJobs > 0 ? (completedJobs / totalJobs) * 100 : 0;
  
  return {
    execution_id: execution.execution_id,
    trace_id: execution.trace_id,
    user_id: execution.user_id,
    status: execution.status,
    
    // Timestamps
    receivedAt: execution.receivedAt,
    startedAt: execution.startedAt,
    completedAt: execution.completedAt,
    duration: execution.completedAt && execution.startedAt 
      ? execution.completedAt - execution.startedAt 
      : null,
    
    // Progress
    progress: Math.round(progress),
    
    // Job summary
    jobs: {
      total: totalJobs,
      completed: completedJobs,
      failed: failedJobs,
      running: runningJobs,
      queued: queuedJobs
    },
    
    // Detailed job states
    jobDetails: jobStates,
    
    // Error info
    error: execution.error
  };
}

// Get execution summary (lightweight)
function getExecutionSummary(execution_id) {
  const execution = getExecution(execution_id);
  
  if (!execution) {
    return null;
  }
  
  return {
    execution_id: execution.execution_id,
    trace_id: execution.trace_id,
    status: execution.status,
    receivedAt: execution.receivedAt,
    startedAt: execution.startedAt,
    completedAt: execution.completedAt,
    duration: execution.completedAt && execution.startedAt 
      ? execution.completedAt - execution.startedAt 
      : null,
    jobCount: execution.jobs.length
  };
}

// Get all executions with states
function getAllExecutionStates() {
  const { getAllExecutions } = require('./executionRegistry');
  const executions = getAllExecutions();
  
  return executions.map(exec => getExecutionSummary(exec.execution_id));
}

// Get executions by status
function getExecutionsByStatus(status) {
  const { getAllExecutions } = require('./executionRegistry');
  const executions = getAllExecutions();
  
  return executions
    .filter(exec => exec.status === status)
    .map(exec => getExecutionSummary(exec.execution_id));
}

module.exports = {
  getExecutionState,
  getExecutionSummary,
  getAllExecutionStates,
  getExecutionsByStatus
};

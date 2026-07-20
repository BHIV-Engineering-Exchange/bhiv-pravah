// jobQueue.js - Strict Lifecycle State Machine
const { recordTelemetry } = require("./engine/engine_telemetry");
const EventEmitter = require('events');
const { startJobTimeout, clearJobTimeout } = require('./engine/job_timeout');

const MAX_RETRIES = 2;

const queue = [];
const activeJobs = new Map();
const jobRegistry = new Map();
let processing = false;

const ENGINE_ID = "engine_local_01";
let engineConnected = false;

const jobDispatcher = new EventEmitter();

const VALID_TRANSITIONS = {
  queued: ["dispatched", "failed"],
  dispatched: ["running", "failed", "queued"],
  running: ["completed", "failed", "queued"],
  completed: [],
  failed: []
};

function validateTransition(currentState, newState) {
  const allowed = VALID_TRANSITIONS[currentState] || [];
  if (!allowed.includes(newState)) {
    throw new Error(`Invalid transition: ${currentState} → ${newState}`);
  }
}

function addJob(job, onStatus, gameplayContract) {
  console.log("[QUEUE RECEIVED]", job.jobType);

  job.status = "queued";
  job.queuedAt = Date.now();
  job.retryCount = 0;
  job.engineId = ENGINE_ID;

  jobRegistry.set(job.jobId, { job, onStatus, gameplayContract });

  queue.push(job);
  onStatus(job, "queued");

  recordTelemetry({
    event: "JOB_QUEUED",
    jobId: job.jobId,
    engineId: ENGINE_ID,
    payload: { jobType: job.jobType, userId: job.userId }
  });

  processQueue();
}

function processQueue() {
  if (processing || queue.length === 0) return;
  processing = true;

  const job = queue.shift();
  const entry = jobRegistry.get(job.jobId);
  
  if (!entry) {
    console.error(`[QUEUE] Job ${job.jobId} not in registry`);
    processing = false;
    processQueue();
    return;
  }

  const { onStatus, gameplayContract } = entry;
  
  try {
    validateTransition(job.status, "dispatched");
    job.status = "dispatched";
    job.dispatchedAt = Date.now();
    onStatus(job, "dispatched");

    recordTelemetry({
      event: "JOB_DISPATCHED",
      jobId: job.jobId,
      engineId: ENGINE_ID,
      payload: { jobType: job.jobType }
    });

    jobDispatcher.emit('dispatch_to_engine', { job, gameplayContract });

    setTimeout(() => {
      const currentJob = findJobById(job.jobId);
      if (currentJob && currentJob.status === 'dispatched') {
        updateJobStatus(job.jobId, 'running', { startedAt: Date.now() });
      }
    }, 1000);

  } catch (err) {
    console.error(`[JOB TRANSITION ERROR] ${err.message}`);
    failJob(job, onStatus, err.message);
    processing = false;
    processQueue();
  }
}

function completeJob(job, onStatus) {
  try {
    validateTransition(job.status, "completed");
    job.status = "completed";
    job.completedAt = Date.now();
    job.duration = job.completedAt - job.startedAt;

    onStatus(job, "completed");

    if (job.jobType === "BUILD_SCENE") {
      recordTelemetry({
        event: "SCENE_LOADED",
        jobId: job.jobId,
        engineId: ENGINE_ID,
        payload: job.payload
      });
    } else if (job.jobType === "SPAWN_ENTITY") {
      recordTelemetry({
        event: "ENTITY_SPAWNED",
        jobId: job.jobId,
        engineId: ENGINE_ID,
        payload: job.payload
      });
    } else if (job.jobType === "LOAD_ASSETS") {
      recordTelemetry({
        event: "ASSETS_LOADED",
        jobId: job.jobId,
        engineId: ENGINE_ID,
        payload: job.payload
      });
    }

    recordTelemetry({
      event: "JOB_COMPLETED",
      jobId: job.jobId,
      engineId: ENGINE_ID,
      payload: { jobType: job.jobType, duration: job.duration }
    });
  } catch (err) {
    console.error(`[JOB COMPLETION ERROR] ${err.message}`);
    failJob(job, onStatus, err.message);
  }
}

function failJob(job, onStatus, error) {
  try {
    validateTransition(job.status, "failed");
  } catch (err) {
    console.error(`[JOB ALREADY TERMINAL] ${job.jobId} in ${job.status}`);
    return;
  }

  job.status = "failed";
  job.failedAt = Date.now();
  job.error = error;
  job.duration = job.failedAt - (job.startedAt || job.dispatchedAt || job.queuedAt);

  onStatus(job, "failed", error);

  recordTelemetry({
    event: "JOB_FAILED",
    jobId: job.jobId,
    engineId: ENGINE_ID,
    payload: { jobType: job.jobType, error, duration: job.duration }
  });

  console.error(`[JOB FAILED] ${job.jobId}: ${error}`);
}

function getPendingEngineJobs() {
  return [...queue, ...Array.from(activeJobs.values())];
}

function findJobById(jobId) {
  const entry = jobRegistry.get(jobId);
  return entry ? entry.job : null;
}

function updateJobStatus(jobId, status, data = {}) {
  const entry = jobRegistry.get(jobId);
  if (!entry) {
    console.warn(`[QUEUE] Job ${jobId} not found in registry`);
    return;
  }
  
  const { job, onStatus } = entry;
  
  try {
    validateTransition(job.status, status);
  } catch (err) {
    console.error(`[QUEUE] Invalid transition for ${jobId}: ${err.message}`);
    return;
  }

  job.status = status;
  Object.assign(job, data);
  
  onStatus(job, status, data.error);
  
  if (status === 'running') {
    activeJobs.set(jobId, job);
    
    startJobTimeout(jobId, (timeoutJobId) => {
      const entry = jobRegistry.get(timeoutJobId);
      if (entry && entry.job.status === 'running') {
        console.error(`[TIMEOUT] Job ${timeoutJobId} timed out`);
        
        clearJobTimeout(timeoutJobId);
        
        if (entry.job.retryCount < MAX_RETRIES) {
          entry.job.retryCount++;
          entry.job.status = 'queued';
          queue.unshift(entry.job);
          console.log(`[RETRY] Job ${timeoutJobId} retry ${entry.job.retryCount}/${MAX_RETRIES}`);
          activeJobs.delete(timeoutJobId);
          processing = false;
          processQueue();
        } else {
          failJob(entry.job, entry.onStatus, `TIMEOUT after ${MAX_RETRIES} retries`);
          activeJobs.delete(timeoutJobId);
          processing = false;
          processQueue();
        }
      }
    });
  } else if (status === 'completed' || status === 'failed') {
    clearJobTimeout(jobId);
    activeJobs.delete(jobId);
    
    processing = false;
    processQueue();
    
    setTimeout(() => jobRegistry.delete(jobId), 60000);
  } else if (status === 'queued') {
    clearJobTimeout(jobId);
    activeJobs.delete(jobId);
  }
}

function setEngineConnected(connected) {
  engineConnected = connected;
  
  if (!connected) {
    activeJobs.forEach((job) => {
      const entry = jobRegistry.get(job.jobId);
      if (entry) {
        console.error(`[ENGINE DISCONNECT] Failing job ${job.jobId}`);
        failJob(job, entry.onStatus, "ENGINE_DISCONNECTED");
      }
    });
    activeJobs.clear();
    processing = false;
  } else {
    queue.length = 0;
    
    const requeuedJobs = [];
    jobRegistry.forEach((entry, jobId) => {
      const { job, onStatus } = entry;
      
      if (job.status === 'dispatched' || job.status === 'queued') {
        console.log(`[QUEUE] Re-queuing job ${jobId} (was ${job.status})`);
        
        if (job.status === 'dispatched') {
          try {
            validateTransition(job.status, 'queued');
            job.status = 'queued';
            onStatus(job, 'queued');
          } catch (err) {
            console.error(`[QUEUE] Failed to re-queue ${jobId}: ${err.message}`);
          }
        }
        requeuedJobs.push(job);
      }
    });
    
    requeuedJobs.forEach(job => queue.push(job));
    
    console.log(`[QUEUE] Engine connected - ${queue.length} jobs ready to process`);
    
    if (activeJobs.size === 0 && queue.length > 0) {
      processing = false;
      processQueue();
    }
  }
}

function clearAllJobs() {
  queue.length = 0;
  activeJobs.clear();
  jobRegistry.clear();
  processing = false;
  console.log('[QUEUE] All jobs cleared');
}

function clearStaleJobs() {
  const now = Date.now();
  const staleThreshold = 2 * 60 * 1000; // 2 minutes
  
  let cleared = 0;
  jobRegistry.forEach((entry, jobId) => {
    const { job } = entry;
    if (job.status !== 'completed' && job.status !== 'failed') {
      if (now - job.queuedAt > staleThreshold) {
        console.log(`[CLEANUP] Removing stale job ${jobId} (${job.status})`);
        jobRegistry.delete(jobId);
        const queueIndex = queue.indexOf(job);
        if (queueIndex > -1) queue.splice(queueIndex, 1);
        activeJobs.delete(jobId);
        clearJobTimeout(jobId);
        cleared++;
      }
    }
  });
  
  if (cleared > 0) {
    console.log(`[CLEANUP] Cleared ${cleared} stale jobs`);
  }
}

// Auto-cleanup stale jobs every minute
setInterval(clearStaleJobs, 60000);

module.exports = { 
  addJob, 
  getPendingEngineJobs, 
  setEngineConnected,
  jobDispatcher,
  findJobById,
  updateJobStatus,
  clearAllJobs
};

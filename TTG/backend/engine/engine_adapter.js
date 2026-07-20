const { buildEngineJobs } = require("./engine_job_queue");

/**
 * Convert intent-layer output to engine-ready format
 * Input: TG Engine Gameplay Contract from intent-layer
 * Output: Same format (already compatible)
 */
function convertToEngineSchema(input) {
  if (!input || typeof input !== 'object') {
    throw new Error("Invalid input: expected object");
  }

  // If already in TG Engine format, return as-is
  if (input.meta && input.gameplay && input.camera && input.player) {
    return input;
  }

  throw new Error("Unknown input format - expected TG Engine Gameplay Contract");
}

/**
 * Prepare job for engine dispatch
 * Converts internal job format to engine-compatible format
 */
function prepareEngineJob(internalJob, gameplayContract) {
  if (!internalJob || typeof internalJob !== 'object') {
    throw new Error("Invalid job: must be object");
  }
  
  if (!internalJob.jobId || typeof internalJob.jobId !== 'string') {
    throw new Error("Invalid job: missing or invalid jobId");
  }

  if (!internalJob.jobType || typeof internalJob.jobType !== 'string') {
    throw new Error("Invalid job: missing or invalid jobType");
  }

  if (!gameplayContract || typeof gameplayContract !== 'object') {
    throw new Error("Invalid job: missing or invalid gameplayContract");
  }

  // Validate jobType
  const ALLOWED_JOB_TYPES = ['START_GAME', 'STOP_GAME', 'UPDATE_CONFIG'];
  if (!ALLOWED_JOB_TYPES.includes(internalJob.jobType)) {
    throw new Error(`Invalid job: unauthorized jobType '${internalJob.jobType}'`);
  }

  // Build engine job
  const engineJob = {
    job_id: internalJob.jobId,
    job_type: internalJob.jobType,
    gameplay_contract: gameplayContract,
    payload: internalJob.payload || {},
    execution_params: {
      priority: "normal",
      timeout_ms: 300000
    },
    submitted_at: internalJob.submittedAt || Date.now(),
    user_id: internalJob.userId || "unknown"
  };

  return engineJob;
}

module.exports = {
  convertToEngineSchema,
  prepareEngineJob
};

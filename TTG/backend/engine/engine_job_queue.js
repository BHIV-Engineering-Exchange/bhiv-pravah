// Engine Job Builder for TG Engine Gameplay Contract

const { randomUUID } = require("crypto");

/**
 * Build jobs for TG Engine (gameplay-focused)
 * @param {Object} gameplayContract - TG Engine Gameplay Contract
 * @returns {Array} Array of jobs
 */
function buildEngineJobs(gameplayContract) {
  if (!gameplayContract || !gameplayContract.game_mode) {
    throw new Error("Invalid gameplayContract passed to buildEngineJobs");
  }

  const jobs = [];

  // Single job: START_GAME with full contract
  jobs.push({
    jobId: randomUUID(),
    jobType: "START_GAME",
    payload: gameplayContract
  });

  console.log(
    "[ENGINE JOBS GENERATED]",
    jobs.map(j => `${j.jobType}:${j.jobId}`)
  );

  return jobs;
}

function createEndGameJob(reason, finalScore, duration) {
  return {
    jobId: randomUUID(),
    jobType: "STOP_GAME",
    payload: {
      reason: reason || "manual_stop",
      final_score: finalScore || 0,
      duration: duration || 0
    }
  };
}

module.exports = { buildEngineJobs, createEndGameJob };

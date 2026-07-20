const JOB_TIMEOUT_MS = 15000; // 15 seconds
const activeTimeouts = new Map();

function startJobTimeout(jobId, onTimeout) {
  if (activeTimeouts.has(jobId)) {
    clearTimeout(activeTimeouts.get(jobId));
  }
  
  const timer = setTimeout(() => {
    console.error(`[JOB TIMEOUT] Job ${jobId} exceeded ${JOB_TIMEOUT_MS}ms`);
    activeTimeouts.delete(jobId);
    onTimeout(jobId);
  }, JOB_TIMEOUT_MS);
  
  activeTimeouts.set(jobId, timer);
}

function clearJobTimeout(jobId) {
  if (activeTimeouts.has(jobId)) {
    clearTimeout(activeTimeouts.get(jobId));
    activeTimeouts.delete(jobId);
  }
}

function clearAllTimeouts() {
  activeTimeouts.forEach(timer => clearTimeout(timer));
  activeTimeouts.clear();
}

module.exports = { startJobTimeout, clearJobTimeout, clearAllTimeouts, JOB_TIMEOUT_MS };

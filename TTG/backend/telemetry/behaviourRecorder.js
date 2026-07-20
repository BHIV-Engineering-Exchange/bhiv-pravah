const behaviourStore = new Map(); // sessionId → array
const executionTelemetry = new Map(); // execution_id → telemetry
const SESSION_CLEANUP_INTERVAL = 30 * 60 * 1000; // 30 minutes
const SESSION_MAX_AGE = 2 * 60 * 60 * 1000; // 2 hours

// Auto-cleanup old sessions
setInterval(() => {
  const now = Date.now();
  const sessionsToDelete = [];
  
  for (const [sessionId, behaviours] of behaviourStore.entries()) {
    if (behaviours.length === 0) {
      sessionsToDelete.push(sessionId);
      continue;
    }
    
    const lastActivity = Math.max(...behaviours.map(b => b.ts));
    if (now - lastActivity > SESSION_MAX_AGE) {
      sessionsToDelete.push(sessionId);
    }
  }
  
  sessionsToDelete.forEach(sessionId => {
    behaviourStore.delete(sessionId);
  });
  
  if (sessionsToDelete.length > 0) {
    console.log(`[TELEMETRY] Cleaned up ${sessionsToDelete.length} old sessions`);
  }
}, SESSION_CLEANUP_INTERVAL);

function recordBehaviour({
  sessionId,
  userId,
  role,
  device,
  actionType,
  category,
  context,
  ts
}) {
  if (!behaviourStore.has(sessionId)) {
    behaviourStore.set(sessionId, []);
  }

  behaviourStore.get(sessionId).push({
    sessionId,
    userId,
    role,
    device,
    behaviour: {
      type: actionType,
      category
    },
    context,
    ts
  });
}

function getSessionBehaviours(sessionId) {
  return behaviourStore.get(sessionId) || [];
}

function clearOldSessions() {
  const now = Date.now();
  let cleared = 0;
  
  for (const [sessionId, behaviours] of behaviourStore.entries()) {
    if (behaviours.length === 0) {
      behaviourStore.delete(sessionId);
      cleared++;
      continue;
    }
    
    const lastActivity = Math.max(...behaviours.map(b => b.ts));
    if (now - lastActivity > SESSION_MAX_AGE) {
      behaviourStore.delete(sessionId);
      cleared++;
    }
  }
  
  return cleared;
}

// Record execution telemetry
function recordExecutionTelemetry(execution_id, event, data) {
  if (!executionTelemetry.has(execution_id)) {
    executionTelemetry.set(execution_id, []);
  }
  
  const telemetryEvent = {
    execution_id,
    event,
    data,
    timestamp: Date.now()
  };
  
  executionTelemetry.get(execution_id).push(telemetryEvent);
  console.log(`[TELEMETRY] ${event}: ${execution_id}`);
  
  return telemetryEvent;
}

// Record job started
function recordJobStarted(execution_id, trace_id, jobId, jobType) {
  return recordExecutionTelemetry(execution_id, 'job_started', {
    trace_id,
    jobId,
    jobType,
    startedAt: Date.now()
  });
}

// Record job completed
function recordJobCompleted(execution_id, trace_id, jobId, jobType, duration) {
  return recordExecutionTelemetry(execution_id, 'job_completed', {
    trace_id,
    jobId,
    jobType,
    duration,
    completedAt: Date.now()
  });
}

// Record execution duration
function recordExecutionDuration(execution_id, trace_id, duration, status) {
  return recordExecutionTelemetry(execution_id, 'execution_duration', {
    trace_id,
    duration,
    status,
    completedAt: Date.now()
  });
}

// Get execution telemetry
function getExecutionTelemetry(execution_id) {
  return executionTelemetry.get(execution_id) || [];
}

// Get all execution telemetry
function getAllExecutionTelemetry() {
  const all = [];
  for (const [execution_id, events] of executionTelemetry.entries()) {
    all.push({ execution_id, events });
  }
  return all;
}

module.exports = {
  recordBehaviour,
  getSessionBehaviours,
  clearOldSessions,
  recordExecutionTelemetry,
  recordJobStarted,
  recordJobCompleted,
  recordExecutionDuration,
  getExecutionTelemetry,
  getAllExecutionTelemetry
};

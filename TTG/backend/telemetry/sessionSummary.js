const { getSessionBehaviours } = require("./behaviourRecorder");

function buildSessionSummary(sessionId, meta) {
  const logs = getSessionBehaviours(sessionId);

  const actionCount = {};
  logs.forEach(l => {
    const type = l.behaviour.type;
    actionCount[type] = (actionCount[type] || 0) + 1;
  });

  return {
    sessionId,
    userId: meta.userId,
    role: meta.role,
    startTime: meta.startTime,
    endTime: Date.now(),
    durationSec: Math.floor((Date.now() - meta.startTime) / 1000),
    actions: {
      total: logs.length,
      breakdown: actionCount
    },
    anomalies: [],
    integrity: {
      nonceReplayDetected: false,
      invalidSignatureCount: 0
    }
  };
}

module.exports = { buildSessionSummary };

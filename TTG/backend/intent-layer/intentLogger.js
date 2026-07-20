const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, '../logs/intent_telemetry.log');

function ensureLogDir() {
  const dir = path.dirname(LOG_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function log(event, data) {
  ensureLogDir();
  const entry = {
    timestamp: new Date().toISOString(),
    event,
    ...data
  };
  fs.appendFileSync(LOG_FILE, JSON.stringify(entry) + '\n');
  console.log(`[INTENT_LOG] ${event}:`, data);
}

function logIntentReceived(text, userId) {
  log('intent_received', { text, userId, length: text.length });
}

function logSchemaGenerated(gameMode, intent, userId) {
  log('schema_generated', { gameMode, intent, userId });
}

function logJobDispatched(jobId, jobType, gameMode, userId) {
  log('job_dispatched', { jobId, jobType, gameMode, userId });
}

function logError(stage, error, userId) {
  log('error', { stage, error: error.message, userId });
}

module.exports = {
  logIntentReceived,
  logSchemaGenerated,
  logJobDispatched,
  logError
};

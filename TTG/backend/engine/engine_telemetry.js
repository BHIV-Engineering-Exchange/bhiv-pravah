const fs = require("fs");
const path = require("path");

const TELEMETRY_PATH = path.join(__dirname, "..", "telemetry_samples.json");
const TELEMETRY_CLEANUP_INTERVAL = 60 * 60 * 1000; // 1 hour
const TELEMETRY_MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours
const MAX_TELEMETRY_ENTRIES = 10000; // Max entries before cleanup

let sequenceNumber = 0;
const eventBuffer = [];

// Auto-cleanup telemetry file
setInterval(() => {
  cleanupTelemetryFile();
}, TELEMETRY_CLEANUP_INTERVAL);

function cleanupTelemetryFile() {
  if (!fs.existsSync(TELEMETRY_PATH)) return;
  
  try {
    const lines = fs.readFileSync(TELEMETRY_PATH, "utf-8").split("\n").filter(Boolean);
    const events = lines.map(line => JSON.parse(line));
    
    const now = Date.now();
    const recentEvents = events.filter(event => 
      (now - event.ts) < TELEMETRY_MAX_AGE
    ).slice(-MAX_TELEMETRY_ENTRIES); // Keep only recent entries, max limit
    
    if (recentEvents.length < events.length) {
      const newContent = recentEvents.map(event => JSON.stringify(event)).join("\n") + "\n";
      fs.writeFileSync(TELEMETRY_PATH, newContent);
      console.log(`[TELEMETRY] Cleaned up ${events.length - recentEvents.length} old entries`);
    }
  } catch (err) {
    console.error("[TELEMETRY] Cleanup failed:", err.message);
  }
}


function recordTelemetry(event) {
  const entry = {
    seq: ++sequenceNumber,
    ts: Date.now(),
    event: event.event,
    jobId: event.jobId || null,
    engineId: event.engineId || null,
    userId: event.userId || null,
    payload: event.payload || {},
    _replay: true
  };

  eventBuffer.push(entry);
  try {
    fs.appendFileSync(TELEMETRY_PATH, JSON.stringify(entry) + "\n");
  } catch (err) {
    console.error("[TELEMETRY] Failed to write telemetry:", err.message);
  }
}


function loadTelemetry() {
  if (!fs.existsSync(TELEMETRY_PATH)) return [];
  
  try {
    const lines = fs.readFileSync(TELEMETRY_PATH, "utf-8").split("\n").filter(Boolean);
    return lines.map(line => JSON.parse(line)).sort((a, b) => a.seq - b.seq);
  } catch (err) {
    console.error("[TELEMETRY] Failed to load telemetry:", err.message);
    return [];
  }
}


function replayTelemetry(events, handlers) {
  events.forEach(event => {
    const handler = handlers[event.event];
    if (handler) handler(event);
  });
}


function clearTelemetry() {
  if (fs.existsSync(TELEMETRY_PATH)) fs.unlinkSync(TELEMETRY_PATH);
  sequenceNumber = 0;
  eventBuffer.length = 0;
}

function forceTelemetryCleanup() {
  return cleanupTelemetryFile();
}

module.exports = { recordTelemetry, loadTelemetry, replayTelemetry, clearTelemetry, forceTelemetryCleanup };

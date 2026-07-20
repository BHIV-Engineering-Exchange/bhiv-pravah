// bucketWriter.js - Storage adapter using pluggable storage contract
const { createStorage } = require('./storage');
const primaryBucket = require('./primaryBucketAdapter');
const fs   = require('fs');
const path = require('path');

// Initialize storage provider based on environment
const storage = createStorage();
const USE_PRIMARY_BUCKET = process.env.USE_PRIMARY_BUCKET === 'true';

const BUCKET_DIR = path.join(__dirname, 'bucket_artifacts');

function _ensureBucketDir() {
  if (!fs.existsSync(BUCKET_DIR)) fs.mkdirSync(BUCKET_DIR, { recursive: true });
}

// ── Stream tick persistence (append-only, no overwrite) ───────────────────────
// Each tick is appended as a single JSON line to:
//   bucket_artifacts/stream_<trace_id>_ticks.jsonl
// Rule: append-only. Never truncate. Never overwrite.
function appendStreamTick(trace_id, delta) {
  _ensureBucketDir();
  const file = path.join(BUCKET_DIR, `stream_${trace_id}_ticks.jsonl`);
  fs.appendFileSync(file, JSON.stringify(delta) + '\n');
}

// Write the contract once on stream completion.
// No-op if file already exists (idempotent, no overwrite).
function writeStreamContract(trace_id, contract) {
  _ensureBucketDir();
  const file = path.join(BUCKET_DIR, `stream_${trace_id}_contract.json`);
  if (fs.existsSync(file)) return;  // no overwrite
  fs.writeFileSync(file, JSON.stringify(contract, null, 2));
}

// Load persisted stream ticks from disk.
// Returns { contract, stream_ticks } or null if not found.
function loadStreamTicks(trace_id) {
  _ensureBucketDir();
  const ticks_file    = path.join(BUCKET_DIR, `stream_${trace_id}_ticks.jsonl`);
  const contract_file = path.join(BUCKET_DIR, `stream_${trace_id}_contract.json`);

  if (!fs.existsSync(ticks_file) || !fs.existsSync(contract_file)) return null;

  try {
    const lines    = fs.readFileSync(ticks_file, 'utf8').trim().split('\n').filter(Boolean);
    const ticks    = lines.map(l => JSON.parse(l));
    const contract = JSON.parse(fs.readFileSync(contract_file, 'utf8'));
    return { contract, stream_ticks: ticks };
  } catch (err) {
    console.error(`[BUCKET_WRITER] Failed to load stream ticks for ${trace_id}:`, err.message);
    return null;
  }
}

// Wrapper functions that write to both local storage and Primary Bucket
async function writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp) {
  const localResult = await storage.writeExecutionSchema(execution_id, trace_id, executionSchema, timestamp);
  
  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionSchema(execution_id, trace_id, executionSchema, timestamp)
      .catch(err => console.error('[BUCKET_WRITER] Primary Bucket sync failed:', err.message));
  }
  
  return localResult;
}

async function writeExecutionStart(execution_id, trace_id, startTimestamp) {
  const localResult = await storage.writeExecutionStart(execution_id, trace_id, startTimestamp);
  
  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionStart(execution_id, trace_id, startTimestamp)
      .catch(err => console.error('[BUCKET_WRITER] Primary Bucket sync failed:', err.message));
  }
  
  return localResult;
}

async function writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration) {
  const localResult = await storage.writeExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration);
  
  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionCompletion(execution_id, trace_id, completionTimestamp, status, duration)
      .catch(err => console.error('[BUCKET_WRITER] Primary Bucket sync failed:', err.message));
  }
  
  return localResult;
}

async function appendExecutionLog(execution_id, trace_id, event, data) {
  const localResult = await storage.appendExecutionLog(execution_id, trace_id, event, data);
  
  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionLog(execution_id, trace_id, event, data)
      .catch(err => console.error('[BUCKET_WRITER] Primary Bucket sync failed:', err.message));
  }
  
  return localResult;
}

module.exports = {
  writeExecutionSchema,
  writeExecutionStart,
  writeExecutionCompletion,
  appendExecutionLog,
  appendStreamTick,
  writeStreamContract,
  loadStreamTicks,
  writeExecutionArtifact: (...args) => storage.writeExecutionArtifact(...args),
  readExecutionArtifacts: (...args) => storage.readExecutionArtifacts(...args),
  listExecutions: (...args) => storage.listExecutions(...args),
  storage
};
